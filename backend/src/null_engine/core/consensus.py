import uuid

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.schemas import WSEnvelope
from null_engine.models.tables import Claim, ClaimVote, WikiPage
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
        # In-memory cache for fast lookup
        self._proposed: dict[uuid.UUID, list[dict]] = {}  # world_id -> claims

    async def extract_claims(self, conversation_text: str) -> list[dict]:
        result = await llm_router.generate_json(
            role="reaction_agent",
            prompt=CLAIM_EXTRACTION_PROMPT.format(text=conversation_text),
        )
        if isinstance(result, list):
            return result
        return result.get("claims", [])

    async def propose_claim(
        self,
        db: AsyncSession,
        world_id: uuid.UUID,
        claim: dict,
        proposer_id: uuid.UUID,
        faction_id: uuid.UUID,
    ):
        # Persist to DB
        db_claim = Claim(
            world_id=world_id,
            claim_text=claim.get("claim", ""),
            category=claim.get("category", "general"),
            confidence=claim.get("confidence", 0.5),
            status="proposed",
            proposer_id=proposer_id,
            faction_id=faction_id,
        )
        db.add(db_claim)
        await db.flush()

        # Add initial vote from proposer
        vote = ClaimVote(
            claim_id=db_claim.id,
            agent_id=proposer_id,
            faction_id=faction_id,
        )
        db.add(vote)
        await db.flush()

        # Update cache
        if world_id not in self._proposed:
            self._proposed[world_id] = []

        self._proposed[world_id].append({
            "db_id": db_claim.id,
            **claim,
            "proposer": str(proposer_id),
            "faction": str(faction_id),
            "votes": [{"agent": str(proposer_id), "faction": str(faction_id)}],
            "status": "proposed",
        })

    async def vote(
        self,
        db: AsyncSession,
        world_id: uuid.UUID,
        claim_text: str,
        voter_id: uuid.UUID,
        faction_id: uuid.UUID,
    ) -> str | None:
        claims = self._proposed.get(world_id, [])
        for claim in claims:
            if claim.get("claim") == claim_text and claim["status"] == "proposed":
                # Check if this agent already voted
                voter_ids = {v["agent"] for v in claim["votes"]}
                if str(voter_id) not in voter_ids:
                    claim["votes"].append({"agent": str(voter_id), "faction": str(faction_id)})

                    # Persist vote
                    vote = ClaimVote(
                        claim_id=claim["db_id"],
                        agent_id=voter_id,
                        faction_id=faction_id,
                    )
                    db.add(vote)
                    await db.flush()

                # Check consensus: 3+ agents from 2+ factions
                factions = {v["faction"] for v in claim["votes"]}
                if len(claim["votes"]) >= 3 and len(factions) >= 2:
                    claim["status"] = "canon"

                    # Update DB
                    result = await db.execute(
                        select(Claim).where(Claim.id == claim["db_id"])
                    )
                    db_claim = result.scalar_one_or_none()
                    if db_claim:
                        db_claim.status = "canon"
                        await db.flush()

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
                    payload={"claim": claim.get("claim", ""), "votes": len(claim["votes"])},
                ))

                # Auto-create wiki page for canon claims
                await self._create_wiki_from_claim(db, world_id, claim)

        # Remove canon claims from proposed
        self._proposed[world_id] = [c for c in claims if c["status"] != "canon"]
        return canon_claims

    async def _create_wiki_from_claim(self, db: AsyncSession, world_id: uuid.UUID, claim: dict):
        """Auto-create or update wiki page from canon claim."""
        claim_text = claim.get("claim", "")
        category = claim.get("category", "general")

        # Check if a related wiki page exists
        result = await db.execute(
            select(WikiPage).where(
                WikiPage.world_id == world_id,
                WikiPage.title.ilike(f"%{category}%"),
            ).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Append to existing page
            existing.content += f"\n\n- {claim_text} (established by consensus)"
            existing.version += 1
            existing.status = "canon"
        else:
            # Create new wiki page
            page = WikiPage(
                world_id=world_id,
                title=f"Established {category.title()} Facts",
                content=f"- {claim_text} (established by consensus)",
                status="canon",
                version=1,
            )
            db.add(page)

        try:
            await db.flush()
        except Exception:
            logger.exception("consensus.wiki_creation_failed")

    async def load_from_db(self, db: AsyncSession, world_id: uuid.UUID):
        """Load proposed claims from DB into cache."""
        try:
            result = await db.execute(
                select(Claim).where(
                    Claim.world_id == world_id,
                    Claim.status == "proposed",
                )
            )
            claims = result.scalars().all()

            self._proposed[world_id] = []
            for c in claims:
                # Load votes
                vote_result = await db.execute(
                    select(ClaimVote).where(ClaimVote.claim_id == c.id)
                )
                votes = vote_result.scalars().all()

                self._proposed[world_id].append({
                    "db_id": c.id,
                    "claim": c.claim_text,
                    "category": c.category,
                    "confidence": c.confidence,
                    "proposer": str(c.proposer_id),
                    "faction": str(c.faction_id),
                    "votes": [
                        {"agent": str(v.agent_id), "faction": str(v.faction_id)}
                        for v in votes
                    ],
                    "status": c.status,
                })

            logger.info("consensus.loaded_from_db", world_id=str(world_id), count=len(claims))
        except Exception:
            logger.exception("consensus.load_from_db_failed")


consensus_engine = ConsensusEngine()
