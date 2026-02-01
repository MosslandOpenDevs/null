import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import WikiPage, WikiHistory, KnowledgeEdge
from null_engine.models.schemas import WSEnvelope
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

WIKI_GEN_PROMPT = """You are a world librarian. Based on the following conversation summaries,
write or update a wiki article.

Topic: {topic}
Existing content (if any): {existing}

Conversation summaries:
{summaries}

Write a concise, encyclopedic article (200-400 words). Include facts established through
agent discourse. Mark uncertain claims with qualifiers."""

KNOWLEDGE_EXTRACT_PROMPT = """Extract knowledge graph triples from this wiki article.

Article: {content}

Return JSON array:
[
  {{"subject": "...", "predicate": "...", "object": "...", "confidence": 0.0-1.0}},
  ...
]

Max 10 triples. Focus on important relationships and facts."""


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
            role="reaction_agent",
            prompt=WIKI_GEN_PROMPT.format(
                topic=topic,
                existing=existing_content or "(new article)",
                summaries="\n".join(f"- {s}" for s in summaries),
            ),
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

        # Extract knowledge edges
        await self._extract_knowledge(db, world_id, page.id, content)

        await db.commit()

        await broadcast(world_id, WSEnvelope(
            type="wiki.edit",
            payload={"page_id": str(page.id), "title": topic, "version": page.version},
        ))

        logger.info("wiki.updated", page=topic, version=page.version)
        return page

    async def _extract_knowledge(
        self,
        db: AsyncSession,
        world_id: uuid.UUID,
        page_id: uuid.UUID,
        content: str,
    ):
        triples = await llm_router.generate_json(
            role="reaction_agent",
            prompt=KNOWLEDGE_EXTRACT_PROMPT.format(content=content),
        )
        if not isinstance(triples, list):
            triples = triples.get("triples", [])

        for triple in triples[:10]:
            edge = KnowledgeEdge(
                world_id=world_id,
                subject=triple.get("subject", ""),
                predicate=triple.get("predicate", ""),
                object=triple.get("object", ""),
                source_page=page_id,
                confidence=triple.get("confidence", 0.5),
            )
            db.add(edge)


wiki_engine = WikiEngine()
