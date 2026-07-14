import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import BookmarkCreate, BookmarkOut, OkResponse
from null_engine.models.tables import Agent, Bookmark, Conversation, WikiPage, World

router = APIRouter(tags=["bookmarks"])


# Bookmarks stay anonymous (they are a viewer feature), so cap per-session
# volume to keep an abusive client from filling the table.
MAX_BOOKMARKS_PER_SESSION = 500


@router.post("/bookmarks", response_model=BookmarkOut)
async def create_bookmark(
    body: BookmarkCreate,
    db: AsyncSession = Depends(get_db),
):
    world = await db.execute(select(World.id).where(World.id == body.world_id))
    if world.scalar_one_or_none() is None:
        raise HTTPException(404, "World not found")

    count_result = await db.execute(
        select(func.count())
        .select_from(Bookmark)
        .where(Bookmark.user_session == body.user_session)
    )
    if (count_result.scalar() or 0) >= MAX_BOOKMARKS_PER_SESSION:
        raise HTTPException(429, "Bookmark limit reached for this session")

    bookmark = Bookmark(
        user_session=body.user_session,
        label=body.label,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        world_id=body.world_id,
        note=body.note,
    )
    db.add(bookmark)
    await db.flush()
    await db.commit()
    await db.refresh(bookmark)
    return bookmark


@router.get("/bookmarks", response_model=list[BookmarkOut])
async def list_bookmarks(
    session: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark)
        .where(Bookmark.user_session == session)
        .order_by(Bookmark.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/bookmarks/{bookmark_id}", response_model=OkResponse)
async def delete_bookmark(
    bookmark_id: uuid.UUID,
    session: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_session == session,
        )
    )
    bookmark = result.scalar_one_or_none()
    if not bookmark:
        raise HTTPException(404, "Bookmark not found")
    await db.delete(bookmark)
    await db.commit()
    return {"ok": True}


@router.post("/bookmarks/export", response_model=list[dict[str, object]])
async def export_bookmarks(
    session: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Export all bookmarked items with their full content."""
    result = await db.execute(
        select(Bookmark)
        .where(Bookmark.user_session == session)
        .order_by(Bookmark.created_at)
    )
    bookmarks = result.scalars().all()

    items = []
    for bm in bookmarks:
        item = {
            "label": bm.label,
            "entity_type": bm.entity_type,
            "entity_id": str(bm.entity_id),
            "world_id": str(bm.world_id),
            "note": bm.note,
        }

        if bm.entity_type == "wiki_page":
            page = (await db.execute(
                select(WikiPage).where(WikiPage.id == bm.entity_id)
            )).scalar_one_or_none()
            if page:
                item["title"] = page.title
                item["content"] = page.content

        elif bm.entity_type == "agent":
            agent = (await db.execute(
                select(Agent).where(Agent.id == bm.entity_id)
            )).scalar_one_or_none()
            if agent:
                item["name"] = agent.name
                item["persona"] = agent.persona

        elif bm.entity_type == "conversation":
            conv = (await db.execute(
                select(Conversation).where(Conversation.id == bm.entity_id)
            )).scalar_one_or_none()
            if conv:
                item["topic"] = conv.topic
                item["messages"] = conv.messages
                item["summary"] = conv.summary

        items.append(item)

    return JSONResponse(items)
