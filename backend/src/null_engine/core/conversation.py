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

    # Build world context for topic generation
    world_context = ""
    try:
        from null_engine.models.tables import Conversation as ConvTable
        recent = await db.execute(
            select(ConvTable)
            .where(ConvTable.world_id == world_id)
            .order_by(ConvTable.created_at.desc())
            .limit(3)
        )
        recent_convs = recent.scalars().all()
        if recent_convs:
            world_context = "Recent discussions: " + "; ".join(
                c.summary[:100] for c in recent_convs if c.summary
            )
    except Exception:
        pass

    topic = await _generate_topic(participants, world_context)

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

    # Update relationships based on conversation (with sentiment analysis)
    await _update_relationships(db, world_id, participants, turn.messages)

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


TOPIC_GENERATION_PROMPT = """Generate a single conversation topic for a group of agents in a simulated civilization.

Participants: {participant_names}
Their factions: {faction_info}
World context: {world_context}

The topic should be:
- Relevant to current world events or tensions
- Likely to provoke interesting debate or negotiation
- Specific enough to drive meaningful discussion

Respond with ONLY the topic (a short phrase, 3-8 words). No explanation."""

FALLBACK_TOPICS = [
    "resource distribution", "territorial boundaries", "trade agreements",
    "recent mysterious events", "leadership disputes", "ancient prophecies",
    "technological discoveries", "cultural traditions", "military strategy",
    "diplomatic relations", "spiritual beliefs", "economic reforms",
]


async def _generate_topic(participants: list[Agent], world_context: str = "") -> str:
    try:
        participant_names = ", ".join(p.name for p in participants)
        faction_info = ", ".join(
            f"{p.name} ({p.persona.get('role', 'member')})"
            for p in participants
        )

        prompt = TOPIC_GENERATION_PROMPT.format(
            participant_names=participant_names,
            faction_info=faction_info,
            world_context=world_context or "A diverse civilization with competing factions",
        )

        topic = await llm_router.generate_text(role="reaction_agent", prompt=prompt)
        topic = topic.strip().strip('"').strip("'")

        if topic and len(topic) < 200:
            return topic
    except Exception:
        logger.exception("topic_generation.llm_failed")

    return random.choice(FALLBACK_TOPICS)


SENTIMENT_PROMPT = """Analyze the relationship dynamics from this conversation between {agent_a} and {agent_b}.

Conversation excerpt:
{conversation}

Rate the overall sentiment on a scale from -1.0 (very hostile) to +1.0 (very friendly).
Consider: agreement/disagreement, cooperation/conflict, respect/disrespect, trust/distrust.

Respond with ONLY a number between -1.0 and 1.0. Nothing else."""


async def _update_relationships(db: AsyncSession, world_id: uuid.UUID, participants: list[Agent], messages: list[AgentMessage] | None = None):
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
            if not rel:
                continue

            drift = random.uniform(-0.02, 0.02)  # Base random drift (smaller)

            # Same faction bias: slight positive tendency
            if a.faction_id and a.faction_id == b.faction_id:
                drift += 0.01
            # Different factions: slight negative tendency
            elif a.faction_id and b.faction_id and a.faction_id != b.faction_id:
                drift -= 0.005

            # LLM sentiment analysis if messages are available
            if messages:
                try:
                    # Filter messages involving these two agents
                    relevant = [
                        m for m in messages
                        if m.agent_id in (a.id, b.id)
                    ]
                    if relevant:
                        conversation_text = "\n".join(
                            f"{m.agent_id}: {m.content[:100]}" for m in relevant[:6]
                        )
                        sentiment_str = await llm_router.generate_text(
                            role="reaction_agent",
                            prompt=SENTIMENT_PROMPT.format(
                                agent_a=a.name,
                                agent_b=b.name,
                                conversation=conversation_text,
                            ),
                        )
                        sentiment = float(sentiment_str.strip())
                        sentiment = max(-1.0, min(1.0, sentiment))
                        # Scale sentiment to drift range
                        drift += sentiment * 0.08
                except (ValueError, Exception):
                    pass  # Fall back to random drift

            rel.strength = max(0.0, min(1.0, rel.strength + drift))
