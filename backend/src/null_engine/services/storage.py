import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import WikiPage


async def search_wiki_pages(
    db: AsyncSession,
    world_id: uuid.UUID,
    query: str,
    limit: int = 20,
) -> list[WikiPage]:
    """Search wiki pages by title or content (text match).
    For vector search, use pgvector similarity when embeddings are available."""
    q = f"%{query}%"
    result = await db.execute(
        select(WikiPage)
        .where(
            WikiPage.world_id == world_id,
            or_(
                WikiPage.title.ilike(q),
                WikiPage.content.ilike(q),
            ),
        )
        .limit(limit)
    )
    return list(result.scalars().all())
