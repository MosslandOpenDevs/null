import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import KnowledgeEdgeOut, WikiPageOut
from null_engine.models.tables import KnowledgeEdge, WikiPage
from null_engine.services.storage import search_wiki_pages

router = APIRouter(tags=["wiki"])


@router.get("/worlds/{world_id}/wiki", response_model=list[WikiPageOut])
async def list_wiki_pages(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WikiPage).where(WikiPage.world_id == world_id))
    return result.scalars().all()


@router.get("/worlds/{world_id}/wiki/search", response_model=list[WikiPageOut])
async def search_wiki(
    world_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    pages = await search_wiki_pages(db, world_id, q)
    return pages


@router.get("/worlds/{world_id}/knowledge-graph", response_model=list[KnowledgeEdgeOut])
async def get_knowledge_graph(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEdge).where(KnowledgeEdge.world_id == world_id))
    return result.scalars().all()
