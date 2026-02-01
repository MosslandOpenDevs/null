import uuid
from collections import defaultdict

import structlog

from null_engine.models.schemas import AgentMessage
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()


class MemoryManager:
    """Three-tier memory system for agents."""

    def __init__(self):
        # Short-term: last N raw messages per agent
        self._short_term: dict[uuid.UUID, list[dict]] = defaultdict(list)
        # Mid-term: conversation summaries per agent
        self._mid_term: dict[uuid.UUID, list[str]] = defaultdict(list)
        # Long-term: vector-indexed facts (simplified; full impl uses pgvector)
        self._long_term: dict[uuid.UUID, list[str]] = defaultdict(list)

    async def add_short_term(self, agent_id: uuid.UUID, messages: list[AgentMessage]):
        entries = [{"agent_id": str(m.agent_id), "content": m.content, "type": m.type} for m in messages]
        self._short_term[agent_id].extend(entries)
        # Keep only last 20
        self._short_term[agent_id] = self._short_term[agent_id][-20:]

    async def add_mid_term(self, agent_id: uuid.UUID, summary: str):
        self._mid_term[agent_id].append(summary)
        # Keep last 50 summaries
        self._mid_term[agent_id] = self._mid_term[agent_id][-50:]

    async def add_long_term(self, agent_id: uuid.UUID, fact: str):
        self._long_term[agent_id].append(fact)

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
            # Truncate from the beginning
            context = context[-(max_tokens * 4):]

        return context if context else "(no prior context)"
