import uuid
from collections import defaultdict

import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.schemas import AgentMessage
from null_engine.models.tables import AgentMemory

logger = structlog.get_logger()


class MemoryManager:
    """Three-tier memory system for agents with DB persistence."""

    def __init__(self):
        # In-memory hot cache
        self._short_term: dict[uuid.UUID, list[dict]] = defaultdict(list)
        self._mid_term: dict[uuid.UUID, list[str]] = defaultdict(list)
        self._long_term: dict[uuid.UUID, list[str]] = defaultdict(list)

    async def add_short_term(self, agent_id: uuid.UUID, messages: list[AgentMessage], db: AsyncSession | None = None):
        entries = [{"agent_id": str(m.agent_id), "content": m.content, "type": m.type} for m in messages]
        self._short_term[agent_id].extend(entries)
        self._short_term[agent_id] = self._short_term[agent_id][-20:]

        # Write-through to DB
        if db:
            try:
                for entry in entries:
                    mem = AgentMemory(
                        agent_id=agent_id,
                        world_id=uuid.UUID(entry.get("world_id", "00000000-0000-0000-0000-000000000000")) if "world_id" in entry else agent_id,
                        tier="short",
                        content=entry,
                    )
                    db.add(mem)
                await db.flush()
            except Exception:
                logger.exception("memory.short_term_persist_failed", agent_id=str(agent_id))

    async def add_mid_term(self, agent_id: uuid.UUID, summary: str, db: AsyncSession | None = None, world_id: uuid.UUID | None = None):
        self._mid_term[agent_id].append(summary)
        self._mid_term[agent_id] = self._mid_term[agent_id][-50:]

        if db and world_id:
            try:
                mem = AgentMemory(
                    agent_id=agent_id,
                    world_id=world_id,
                    tier="mid",
                    content={"summary": summary},
                )
                db.add(mem)
                await db.flush()
            except Exception:
                logger.exception("memory.mid_term_persist_failed", agent_id=str(agent_id))

    async def add_long_term(self, agent_id: uuid.UUID, fact: str, db: AsyncSession | None = None, world_id: uuid.UUID | None = None):
        self._long_term[agent_id].append(fact)

        if db and world_id:
            try:
                mem = AgentMemory(
                    agent_id=agent_id,
                    world_id=world_id,
                    tier="long",
                    content={"fact": fact},
                )
                db.add(mem)
                await db.flush()
            except Exception:
                logger.exception("memory.long_term_persist_failed", agent_id=str(agent_id))

    async def load_from_db(self, agent_id: uuid.UUID, db: AsyncSession):
        """Load agent memory from DB into hot cache on startup."""
        try:
            result = await db.execute(
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id)
                .order_by(AgentMemory.created_at.desc())
            )
            memories = result.scalars().all()

            for mem in memories:
                if mem.tier == "short":
                    if len(self._short_term[agent_id]) < 20:
                        self._short_term[agent_id].insert(0, mem.content)
                elif mem.tier == "mid":
                    if len(self._mid_term[agent_id]) < 50:
                        self._mid_term[agent_id].insert(0, mem.content.get("summary", ""))
                elif mem.tier == "long":
                    self._long_term[agent_id].insert(0, mem.content.get("fact", ""))

            logger.info("memory.loaded_from_db", agent_id=str(agent_id), count=len(memories))
        except Exception:
            logger.exception("memory.load_from_db_failed", agent_id=str(agent_id))

    async def build_context(self, agent_id: uuid.UUID, topic: str, max_tokens: int = 8000) -> str:
        parts: list[str] = []

        # Short-term (most recent messages)
        short = self._short_term.get(agent_id, [])
        if short:
            recent = short[-10:]
            parts.append("Recent messages:")
            for m in recent:
                parts.append(f"  {m['content'][:200]}")

        # Mid-term (summaries)
        mid = self._mid_term.get(agent_id, [])
        if mid:
            parts.append("\nPast conversation summaries:")
            for s in mid[-5:]:
                parts.append(f"  - {s[:150]}")

        # Long-term (facts)
        long = self._long_term.get(agent_id, [])
        if long:
            parts.append("\nKnown facts:")
            for f in long[-5:]:
                parts.append(f"  - {f[:150]}")

        context = "\n".join(parts)

        # Rough token estimation (4 chars ≈ 1 token)
        estimated_tokens = len(context) // 4
        if estimated_tokens > max_tokens:
            context = context[-(max_tokens * 4):]

        return context if context else "(no prior context)"
