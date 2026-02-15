import random
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.agents.memory import MemoryManager
from null_engine.models.schemas import AgentMessage, ConversationTurn, WSEnvelope
from null_engine.models.tables import Agent, Conversation, Relationship
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

CONVERSATION_PROMPT = """You are {agent_name}, {agent_role} of the {faction_name} faction.

Personality: {personality}
Motivation: {motivation}
Speech style: {speech_style}

Context from memory:
{memory_context}

Current conversation topic: {topic}
Previous messages in this conversation:
{history}

Respond in character. Keep response under 150 words. You may:
- Share information, opinions, or rumors
- React to what others said
- Propose actions or alliances
- Reveal (or conceal) secrets

Respond ONLY with your character's dialogue/action. No meta-commentary."""


async def run_conversation(
    db: AsyncSession,
    world_id: uuid.UUID,
    epoch: int,
    tick: int,
    memory: MemoryManager,
) -> ConversationTurn:
    # Select participants
    participants = await _select_participants(db, world_id)
    if len(participants) < 2:
        return ConversationTurn(world_id=world_id, epoch=epoch, participants=[])

    topic = await _generate_topic(participants)

    turn = ConversationTurn(
        world_id=world_id,
        epoch=epoch,
        topic=topic,
        participants=[p.id for p in participants],
    )

    history_lines: list[str] = []

    # Multi-round conversation (3-6 rounds)
    num_rounds = random.randint(3, 6)
    for round_num in range(num_rounds):
        speaker = participants[round_num % len(participants)]

        # Build context
        memory_context = await memory.build_context(speaker.id, topic)

        prompt = CONVERSATION_PROMPT.format(
            agent_name=speaker.name,
            agent_role=speaker.persona.get("role", "member"),
            faction_name="Unknown",
            personality=speaker.persona.get("personality", ""),
            motivation=speaker.persona.get("motivation", ""),
            speech_style=speaker.persona.get("speech_style", "neutral"),
            memory_context=memory_context,
            topic=topic,
            history="\n".join(history_lines[-10:]),
        )

        response = await llm_router.generate_text(role="main_debater", prompt=prompt)

        msg = AgentMessage(
            agent_id=speaker.id,
            content=response,
            type="speech",
            targets=[p.id for p in participants if p.id != speaker.id],
        )
        turn.messages.append(msg)
        history_lines.append(f"{speaker.name}: {response}")

        # Broadcast via WebSocket
        await broadcast(world_id, WSEnvelope(
            type="agent.message",
            epoch=epoch,
            payload={
                "agent_id": str(speaker.id),
                "agent_name": speaker.name,
                "content": response,
                "tick": tick,
                "round": round_num,
            },
        ))

    # Post-conversation: update memories
    summary = f"Conversation about '{topic}': " + "; ".join(
        f"{m.content[:60]}..." for m in turn.messages[:3]
    )
    for p in participants:
        await memory.add_short_term(p.id, turn.messages)
        await memory.add_mid_term(p.id, summary)

    # Update relationships based on conversation
    await _update_relationships(db, world_id, participants)

    # Persist conversation to DB
    conv_id = await _save_conversation(db, turn, tick, summary)

    # Extract entity mentions
    if conv_id:
        try:
            from null_engine.services.mention_extractor import extract_mentions_from_conversation
            await extract_mentions_from_conversation(
                db, world_id, conv_id,
                [{"content": m.content} for m in turn.messages],
            )
        except Exception:
            logger.exception("conversation.mention_extraction_failed")

    return turn


async def _save_conversation(db: AsyncSession, turn: ConversationTurn, tick: int, summary: str) -> uuid.UUID | None:
    try:
        conv = Conversation(
            world_id=turn.world_id,
            epoch=turn.epoch,
            tick=tick,
            topic=turn.topic,
            participants=[str(p) for p in turn.participants],
            messages=[
                {
                    "agent_id": str(m.agent_id),
                    "content": m.content,
                }
                for m in turn.messages
            ],
            summary=summary,
        )
        db.add(conv)
        await db.flush()
        return conv.id
    except Exception:
        logger.exception("conversation.save_failed")
        return None


async def _select_participants(db: AsyncSession, world_id: uuid.UUID, count: int = 0) -> list[Agent]:
    if count == 0:
        count = random.randint(3, 8)
    result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    all_agents = list(result.scalars().all())
    if len(all_agents) <= count:
        return all_agents
    return random.sample(all_agents, count)


async def _generate_topic(participants: list[Agent]) -> str:
    topics = [
        "resource distribution", "territorial boundaries", "trade agreements",
        "recent mysterious events", "leadership disputes", "ancient prophecies",
        "technological discoveries", "cultural traditions", "military strategy",
        "diplomatic relations", "spiritual beliefs", "economic reforms",
    ]
    return random.choice(topics)


async def _update_relationships(db: AsyncSession, world_id: uuid.UUID, participants: list[Agent]):
    for i, a in enumerate(participants):
        for b in participants[i + 1:]:
            result = await db.execute(
                select(Relationship).where(
                    Relationship.world_id == world_id,
                    Relationship.agent_a == a.id,
                    Relationship.agent_b == b.id,
                )
            )
            rel = result.scalar_one_or_none()
            if rel:
                # Slight random drift
                drift = random.uniform(-0.05, 0.05)
                rel.strength = max(0.0, min(1.0, rel.strength + drift))
