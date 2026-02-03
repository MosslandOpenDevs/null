import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import WikiPage, WikiHistory
from null_engine.models.schemas import WSEnvelope
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

WIKI_GEN_PROMPT = """You are a world librarian writing a comprehensive Wikipedia-style article.

Topic: {topic}
Existing content (if any): {existing}

Recent conversation summaries:
{summaries}

Write a well-structured encyclopedic article (800-1500 words) with the following sections:

## Overview
A comprehensive introduction explaining what/who this topic is, its significance, and key characteristics.

## Background & History
How this entity came to be, its origins, evolution over time, and important historical events.

## Characteristics
Key traits, beliefs, behaviors, relationships with other entities, and defining features.

## Notable Events
Significant incidents, conflicts, achievements, or turning points involving this topic.

## Relationships & Connections
How this topic relates to other agents, factions, locations, or concepts in the world.

## Current Status
The present state and ongoing developments.

Guidelines:
- Write in formal, encyclopedic tone (third person)
- Include specific details, quotes, and references to conversations
- Mark uncertain information with phrases like "reportedly", "according to sources"
- Create internal links using [[Page Title]] format for related topics
- Be comprehensive but avoid speculation beyond established facts"""


class WikiEngine:
    async def generate_or_update_page(
        self,
        db: AsyncSession,
        world_id: uuid.UUID,
        topic: str,
        summaries: list[str],
    ) -> WikiPage:
        # Check for existing page
        result = await db.execute(
            select(WikiPage).where(WikiPage.world_id == world_id, WikiPage.title == topic)
        )
        existing_page = result.scalar_one_or_none()
        existing_content = existing_page.content if existing_page else ""

        content = await llm_router.generate_text(
            role="wiki_writer",
            prompt=WIKI_GEN_PROMPT.format(
                topic=topic,
                existing=existing_content or "(new article)",
                summaries="\n".join(f"- {s}" for s in summaries),
            ),
            max_tokens=4096,
        )

        if existing_page:
            # Save history
            history = WikiHistory(
                page_id=existing_page.id,
                content=existing_page.content,
                version=existing_page.version,
            )
            db.add(history)

            existing_page.content = content
            existing_page.version += 1
            page = existing_page
        else:
            page = WikiPage(
                world_id=world_id,
                title=topic,
                content=content,
                status="draft",
            )
            db.add(page)
            await db.flush()

        # Extract entity mentions
        try:
            from null_engine.services.mention_extractor import extract_mentions_from_wiki
            await extract_mentions_from_wiki(db, world_id, page.id, content)
        except Exception:
            logger.exception("wiki.mention_extraction_failed")

        await db.commit()

        await broadcast(world_id, WSEnvelope(
            type="wiki.edit",
            payload={"page_id": str(page.id), "title": topic, "version": page.version},
        ))

        logger.info("wiki.updated", page=topic, version=page.version)
        return page


wiki_engine = WikiEngine()
