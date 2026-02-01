import uuid
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import Agent, WikiPage
from null_engine.models.schemas import WSEnvelope
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

CLAIM_EXTRACTION_PROMPT = """Extract factual claims from this conversation excerpt.

Conversation:
{text}

Return a JSON array of claims:
[
  {{"claim": "statement of fact", "confidence": 0.0-1.0, "category": "history|science|politics|culture|geography"}},
  ...
]

Only extract concrete, verifiable claims. Max 5 claims."""


class ConsensusEngine:
    def __init__(self):
        self._proposed: dict[uuid.UUID, list[dict]] = {}  # world_id -> claims
        self._votes: dict[str, list[dict]] = {}  # claim_hash -> votes

    async def extract_claims(self, conversation_text: str) -> list[dict]:
        result = await llm_router.generate_json(
            role="reaction_agent",
            prompt=CLAIM_EXTRACTION_PROMPT.format(text=conversation_text),
        )
        if isinstance(result, list):
            return result
        return result.get("claims", [])

    async def propose_claim(self, world_id: uuid.UUID, claim: dict, proposer_id: uuid.UUID, faction_id: uuid.UUID):
        if world_id not in self._proposed:
            self._proposed[world_id] = []

        claim_entry = {
            **claim,
            "proposer": str(proposer_id),
            "faction": str(faction_id),
            "votes": [{"agent": str(proposer_id), "faction": str(faction_id)}],
            "status": "proposed",
        }
        self._proposed[world_id].append(claim_entry)

    async def vote(self, world_id: uuid.UUID, claim_text: str, voter_id: uuid.UUID, faction_id: uuid.UUID) -> str | None:
        claims = self._proposed.get(world_id, [])
        for claim in claims:
            if claim["claim"] == claim_text and claim["status"] == "proposed":
                # Check if this agent already voted
                voter_ids = {v["agent"] for v in claim["votes"]}
                if str(voter_id) not in voter_ids:
                    claim["votes"].append({"agent": str(voter_id), "faction": str(faction_id)})

                # Check consensus: 3+ agents from 2+ factions
                factions = {v["faction"] for v in claim["votes"]}
                if len(claim["votes"]) >= 3 and len(factions) >= 2:
                    claim["status"] = "canon"
                    return "canon"
                return "proposed"
        return None

    async def check_consensus(self, db: AsyncSession, world_id: uuid.UUID) -> list[dict]:
        canon_claims = []
        claims = self._proposed.get(world_id, [])
        for claim in claims:
            if claim["status"] == "canon":
                canon_claims.append(claim)
                await broadcast(world_id, WSEnvelope(
                    type="consensus.reached",
                    payload={"claim": claim["claim"], "votes": len(claim["votes"])},
                ))
        # Remove canon claims from proposed
        self._proposed[world_id] = [c for c in claims if c["status"] != "canon"]
        return canon_claims


consensus_engine = ConsensusEngine()
