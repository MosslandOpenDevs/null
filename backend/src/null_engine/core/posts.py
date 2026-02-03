import random
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.models.tables import Agent, AgentPost, World
from null_engine.models.schemas import WSEnvelope
from null_engine.services.llm_router import llm_router
from null_engine.ws.handler import broadcast

logger = structlog.get_logger()

# Probability of post generation per tick (same as EVENT_PROBABILITY)
POST_PROBABILITY = 0.15


async def generate_agent_posts(
    db: AsyncSession, world_id: uuid.UUID, epoch: int, tick: int
) -> list[AgentPost]:
    """Generate agent posts with a random probability."""
    posts: list[AgentPost] = []

    if random.random() >= POST_PROBABILITY:
        return posts

    # Fetch world and agents
    world_result = await db.execute(select(World).where(World.id == world_id))
    world = world_result.scalar_one_or_none()
    if not world:
        return posts

    agents_result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    agents = agents_result.scalars().all()
    if not agents:
        return posts

    # Select a random agent
    agent = random.choice(agents)
    persona = agent.persona or {}

    # Build prompt
    agent_name = agent.name
    agent_role = persona.get("role", "a member of this world")
    personality = persona.get("personality", "thoughtful and observant")
    motivation = persona.get("motivation", "to understand the world")

    prompt = f"""You are {agent_name}, {agent_role}.
Personality: {personality}
Motivation: {motivation}

Write a short social media post (1-3 paragraphs) sharing your thoughts.
You might:
- React to recent events or conversations
- Share an opinion on current happenings
- Reflect on your goals or experiences
- Make an announcement

Write in character. Be authentic to your personality.
Keep it concise and engaging, like a real social media post.

Respond with ONLY the post content, no additional commentary."""

    try:
        content = await llm_router.generate_text("post_writer", prompt, temperature=0.9, max_tokens=500)
        content = content.strip()

        if not content or content.startswith("(LLM error"):
            logger.warning("post.generation_failed", agent=agent_name)
            return posts

        # Create the post
        post = AgentPost(
            id=uuid.uuid4(),
            world_id=world_id,
            agent_id=agent.id,
            epoch=epoch,
            tick=tick,
            title=None,
            content=content,
            title_ko=None,
            content_ko=None,
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)

        posts.append(post)

        logger.info("post.created", agent=agent_name, post_id=str(post.id))

        # Broadcast via WebSocket
        await broadcast(
            world_id,
            WSEnvelope(
                type="post.created",
                epoch=epoch,
                payload={
                    "id": str(post.id),
                    "agent_id": str(agent.id),
                    "agent_name": agent_name,
                    "content": content[:200],
                    "tick": tick,
                },
            ),
        )

    except Exception:
        logger.exception("post.error", agent=agent_name)

    return posts
