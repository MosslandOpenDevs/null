"""Background translation worker — translates agent-generated content to Korean."""

import asyncio
import copy
import time

import structlog
from sqlalchemy import func, select

from null_engine.db import async_session
from null_engine.models.tables import Conversation, Stratum, WikiPage
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()

BATCH_SIZE = 5
INTERVAL_SECONDS = 60

TRANSLATE_PROMPT = (
    "Translate the following English text to Korean. "
    "Output ONLY the Korean translation, nothing else.\n\n{text}"
)


async def translate_to_korean(text: str) -> str | None:
    """Translate a single text string to Korean via LLM."""
    if not text or not text.strip():
        return None
    try:
        result = await llm_router.generate_text(
            "translator",
            TRANSLATE_PROMPT.format(text=text),
            temperature=0.3,
            max_tokens=2048,
        )
        if result and not result.startswith("(LLM error"):
            return result.strip()
        return None
    except Exception:
        logger.exception("translator.translate_failed")
        return None


async def translate_messages(messages: list[dict]) -> list[dict] | None:
    """Translate the content field of each message in a conversation messages list."""
    if not messages:
        return None
    translated = []
    for msg in messages:
        msg_copy = copy.copy(msg)
        content = msg.get("content", "")
        if content:
            ko = await translate_to_korean(content)
            if ko:
                msg_copy["content"] = ko
            # If translation fails, keep original
        translated.append(msg_copy)
    return translated


async def _translate_conversations():
    """Find conversations with NULL _ko fields and translate them."""
    async with async_session() as db:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.topic_ko.is_(None))
            .where(Conversation.topic != "")
            .order_by(Conversation.created_at.desc())
            .limit(BATCH_SIZE)
        )
        rows = result.scalars().all()

        for conv in rows:
            topic_ko = await translate_to_korean(conv.topic) if conv.topic else None
            summary_ko = await translate_to_korean(conv.summary) if conv.summary else None
            messages_ko = await translate_messages(conv.messages) if conv.messages else None

            if topic_ko is not None:
                conv.topic_ko = topic_ko
            if summary_ko is not None:
                conv.summary_ko = summary_ko
            if messages_ko is not None:
                conv.messages_ko = messages_ko

            # Mark as processed even if translation partially failed
            if conv.topic_ko is None:
                conv.topic_ko = conv.topic or ""

            logger.info("translator.conversation_done", id=str(conv.id))

        await db.commit()
        return len(rows)


async def _translate_wiki_pages():
    """Find wiki pages with NULL _ko fields and translate them."""
    async with async_session() as db:
        result = await db.execute(
            select(WikiPage)
            .where(WikiPage.title_ko.is_(None))
            .where(WikiPage.title != "")
            .order_by(WikiPage.created_at.desc())
            .limit(BATCH_SIZE)
        )
        rows = result.scalars().all()

        for page in rows:
            title_ko = await translate_to_korean(page.title) if page.title else None
            content_ko = await translate_to_korean(page.content) if page.content else None

            if title_ko is not None:
                page.title_ko = title_ko
            if content_ko is not None:
                page.content_ko = content_ko

            # Mark as processed
            if page.title_ko is None:
                page.title_ko = page.title or ""

            logger.info("translator.wiki_page_done", id=str(page.id))

        await db.commit()
        return len(rows)


async def _translate_strata():
    """Find strata with NULL summary_ko and translate them."""
    async with async_session() as db:
        result = await db.execute(
            select(Stratum)
            .where(Stratum.summary_ko.is_(None))
            .where(Stratum.summary != "")
            .limit(BATCH_SIZE)
        )
        rows = result.scalars().all()

        for s in rows:
            summary_ko = await translate_to_korean(s.summary) if s.summary else None

            if summary_ko is not None:
                s.summary_ko = summary_ko
            else:
                s.summary_ko = s.summary or ""

            logger.info("translator.stratum_done", id=str(s.id))

        await db.commit()
        return len(rows)


async def _count_pending() -> dict[str, int]:
    """Count untranslated rows by entity type for queue observability."""
    async with async_session() as db:
        conv_result = await db.execute(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.topic_ko.is_(None))
            .where(Conversation.topic != "")
        )
        wiki_result = await db.execute(
            select(func.count())
            .select_from(WikiPage)
            .where(WikiPage.title_ko.is_(None))
            .where(WikiPage.title != "")
        )
        strata_result = await db.execute(
            select(func.count())
            .select_from(Stratum)
            .where(Stratum.summary_ko.is_(None))
            .where(Stratum.summary != "")
        )

        return {
            "conversations_pending": conv_result.scalar() or 0,
            "wiki_pages_pending": wiki_result.scalar() or 0,
            "strata_pending": strata_result.scalar() or 0,
        }


async def translation_worker_loop():
    """Background loop that periodically translates untranslated content."""
    logger.info("translator.worker_started")
    while True:
        try:
            await asyncio.sleep(INTERVAL_SECONDS)
            cycle_started = time.monotonic()

            pending = await _count_pending()
            logger.info("translator.queue", **pending)

            conv_count = await _translate_conversations()
            wiki_count = await _translate_wiki_pages()
            strata_count = await _translate_strata()

            duration_ms = int((time.monotonic() - cycle_started) * 1000)
            logger.info(
                "translator.batch_done",
                conversations=conv_count,
                wiki_pages=wiki_count,
                strata=strata_count,
                translated_total=conv_count + wiki_count + strata_count,
                duration_ms=duration_ms,
                **pending,
            )
        except asyncio.CancelledError:
            logger.info("translator.worker_stopped")
            break
        except Exception:
            logger.exception("translator.worker_error")
            await asyncio.sleep(10)
