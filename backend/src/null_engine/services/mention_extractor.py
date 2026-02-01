"""MentionExtractor — detects entity mentions in conversations and wiki pages.

Uses fuzzy string matching against known entities (agents, wiki pages, factions)
to create bidirectional entity_mentions links.
"""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import (
    Agent, WikiPage, Faction, EntityMention, Conversation,
)

logger = structlog.get_logger()

# Minimum ratio for fuzzy match (0-100)
FUZZY_THRESHOLD = 75


def _normalize(text: str) -> str:
    return text.lower().strip()


def _fuzzy_match(needle: str, haystack: str) -> bool:
    """Simple substring-based fuzzy match."""
    n = _normalize(needle)
    h = _normalize(haystack)
    if len(n) < 2:
        return False
    return n in h


async def extract_mentions_from_conversation(
    db: AsyncSession,
    world_id: uuid.UUID,
    conversation_id: uuid.UUID,
    messages: list[dict],
):
    """Extract entity mentions from conversation messages."""
    full_text = " ".join(m.get("content", "") for m in messages)
    if not full_text.strip():
        return

    await _extract_mentions(
        db, world_id, "conversation", conversation_id, full_text,
    )


async def extract_mentions_from_wiki(
    db: AsyncSession,
    world_id: uuid.UUID,
    page_id: uuid.UUID,
    content: str,
):
    """Extract entity mentions from wiki page content."""
    if not content.strip():
        return

    await _extract_mentions(
        db, world_id, "wiki", page_id, content,
    )


async def _extract_mentions(
    db: AsyncSession,
    world_id: uuid.UUID,
    source_type: str,
    source_id: uuid.UUID,
    text: str,
):
    """Core extraction: match known entities against text."""
    # Load all known entities for this world
    agents = (await db.execute(
        select(Agent).where(Agent.world_id == world_id)
    )).scalars().all()

    wiki_pages = (await db.execute(
        select(WikiPage).where(WikiPage.world_id == world_id)
    )).scalars().all()

    factions = (await db.execute(
        select(Faction).where(Faction.world_id == world_id)
    )).scalars().all()

    # Already existing mentions for this source
    existing = (await db.execute(
        select(EntityMention).where(
            EntityMention.source_type == source_type,
            EntityMention.source_id == source_id,
        )
    )).scalars().all()
    existing_targets = {(m.target_type, m.target_id) for m in existing}

    mentions_to_add = []

    # Match agents
    for agent in agents:
        if _fuzzy_match(agent.name, text):
            key = ("agent", agent.id)
            if key not in existing_targets:
                mentions_to_add.append(EntityMention(
                    world_id=world_id,
                    source_type=source_type,
                    source_id=source_id,
                    mention_text=agent.name,
                    target_type="agent",
                    target_id=agent.id,
                    confidence=0.9,
                ))

    # Match wiki pages
    for page in wiki_pages:
        if source_type == "wiki" and page.id == source_id:
            continue  # Skip self-reference
        if _fuzzy_match(page.title, text):
            key = ("wiki_page", page.id)
            if key not in existing_targets:
                mentions_to_add.append(EntityMention(
                    world_id=world_id,
                    source_type=source_type,
                    source_id=source_id,
                    mention_text=page.title,
                    target_type="wiki_page",
                    target_id=page.id,
                    confidence=0.85,
                ))

    # Match factions
    for faction in factions:
        if _fuzzy_match(faction.name, text):
            key = ("faction", faction.id)
            if key not in existing_targets:
                mentions_to_add.append(EntityMention(
                    world_id=world_id,
                    source_type=source_type,
                    source_id=source_id,
                    mention_text=faction.name,
                    target_type="faction",
                    target_id=faction.id,
                    confidence=0.85,
                ))

    for mention in mentions_to_add:
        db.add(mention)

    if mentions_to_add:
        await db.flush()
        logger.info(
            "mention_extractor.extracted",
            source_type=source_type,
            count=len(mentions_to_add),
        )
