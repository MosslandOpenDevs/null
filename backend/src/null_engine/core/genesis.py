import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.config import settings
from null_engine.models.tables import World, Faction, Agent, Relationship, WorldTag
from null_engine.services.llm_router import llm_router

logger = structlog.get_logger()

WORLD_GEN_PROMPT = """You are a world architect. Given the seed prompt below, generate a detailed world configuration.

Seed: {seed_prompt}

Respond with JSON:
{{
  "era": "time period",
  "tech_level": "technology description",
  "description": "2-3 sentence world description",
  "factions": [
    {{"name": "...", "description": "...", "color": "#hex", "agent_count": 25}},
    ...
  ],
  "constraints": ["rule1", "rule2", ...]
}}

Generate exactly {num_factions} factions. Be creative and ensure factions have conflicting interests.
"""

PERSONA_GEN_PROMPT = """Generate {count} unique character personas for the "{faction_name}" faction in this world:

World: {world_desc}
Faction: {faction_desc}

For each character, respond with a JSON array:
[
  {{
    "name": "unique name fitting the world",
    "role": "their role/occupation",
    "personality": "2-3 key personality traits",
    "motivation": "primary motivation",
    "secret": "a hidden agenda or secret",
    "speech_style": "how they talk"
  }},
  ...
]
"""


async def create_world(db: AsyncSession, seed_prompt: str, extra_config: dict[str, Any] | None = None) -> World:
    """Synchronous full creation (used by auto_genesis and tests)."""
    world = World(seed_prompt=seed_prompt, config=extra_config or {}, status="generating")
    db.add(world)
    await db.flush()

    await populate_world(db, world.id, seed_prompt, extra_config or {})

    world.status = "created"
    await db.commit()
    await db.refresh(world)
    logger.info("genesis: world created", world_id=str(world.id))
    return world


async def _update_progress(db: AsyncSession, world_id: uuid.UUID, step: str, step_num: int, total_steps: int, detail: str = ""):
    """Update genesis progress in the world's config JSONB."""
    result = await db.execute(select(World).where(World.id == world_id))
    world = result.scalar_one_or_none()
    if not world:
        return
    config = dict(world.config or {})
    config["_genesis_progress"] = {
        "step": step,
        "step_num": step_num,
        "total_steps": total_steps,
        "detail": detail,
        "percent": round(step_num / total_steps * 100),
    }
    world.config = config
    await db.flush()
    await db.commit()


async def populate_world(db: AsyncSession, world_id: uuid.UUID, seed_prompt: str, extra_config: dict[str, Any]) -> None:
    """Generate factions, agents, relationships, and tags for an existing world row."""
    import asyncio as _asyncio

    num_factions = settings.default_factions
    # Total steps: 1 (world config) + 1 (factions) + num_factions (agents) + 1 (relationships) + 1 (tags) = num_factions + 4
    total_steps = num_factions + 4

    logger.info("genesis: populating world", world_id=str(world_id), seed=seed_prompt[:80])

    # Step 1: Generate world config via LLM
    await _update_progress(db, world_id, "world_config", 1, total_steps, "Designing world architecture...")

    world_config = await llm_router.generate_json(
        role="genesis_architect",
        prompt=WORLD_GEN_PROMPT.format(
            seed_prompt=seed_prompt,
            num_factions=num_factions,
        ),
    )

    if extra_config:
        world_config.update(extra_config)

    # Update world config
    result = await db.execute(
        select(World).where(World.id == world_id)
    )
    world = result.scalar_one_or_none()
    if not world:
        return
    world.config = world_config
    await db.flush()

    # Step 2: Create factions
    await _update_progress(db, world_id, "factions", 2, total_steps, "Establishing factions...")

    faction_specs = world_config.get("factions", [])
    factions: list[Faction] = []
    for spec in faction_specs:
        faction = Faction(
            world_id=world_id,
            name=spec["name"],
            description=spec.get("description", ""),
            color=spec.get("color", "#FFFFFF"),
        )
        db.add(faction)
        factions.append(faction)
    await db.flush()
    await db.commit()

    # Steps 3..N: Generate agents per faction — sequential with progress updates
    world_desc = world_config.get("description", seed_prompt)
    all_agents: list[Agent] = []

    for idx, (faction, spec) in enumerate(zip(factions, faction_specs)):
        step_num = 3 + idx
        await _update_progress(
            db, world_id, "agents", step_num, total_steps,
            f"Summoning agents for {faction.name}..."
        )

        count = spec.get("agent_count", settings.default_agents_per_faction)
        personas = await _generate_personas(
            faction.name, faction.description, world_desc, count,
        )
        for persona in personas:
            agent = Agent(
                world_id=world_id,
                faction_id=faction.id,
                name=persona.get("name", f"Agent-{uuid.uuid4().hex[:6]}"),
                persona=persona,
                beliefs=[],
                status="idle",
            )
            db.add(agent)
            all_agents.append(agent)
        await db.flush()
        await db.commit()

    # Step N+1: Relationships
    await _update_progress(
        db, world_id, "relationships", total_steps - 1, total_steps,
        "Weaving relationships..."
    )
    await _generate_relationships(db, world_id, all_agents)
    await db.flush()
    await db.commit()

    # Step N+2: Tags
    await _update_progress(
        db, world_id, "tags", total_steps, total_steps,
        "Classifying world tags..."
    )
    await _generate_world_tags(db, world_id, world_config)

    await db.flush()
    logger.info("genesis: world populated", world_id=str(world_id), agents=len(all_agents))


async def _generate_personas(faction_name: str, faction_desc: str, world_desc: str, count: int) -> list[dict]:
    BATCH_SIZE = 5
    all_personas: list[dict] = []

    for batch_start in range(0, count, BATCH_SIZE):
        batch_count = min(BATCH_SIZE, count - batch_start)

        for attempt in range(3):
            result = await llm_router.generate_json(
                role="genesis_architect",
                prompt=PERSONA_GEN_PROMPT.format(
                    count=batch_count,
                    faction_name=faction_name,
                    faction_desc=faction_desc,
                    world_desc=world_desc,
                ),
                max_tokens=4096,
            )
            personas = result if isinstance(result, list) else result.get("personas", [])
            if personas:
                all_personas.extend(personas[:batch_count])
                break
            logger.warning("genesis.persona_retry", faction=faction_name, attempt=attempt)

    return all_personas[:count]


TAG_GEN_PROMPT = """Analyze this world and generate 5-8 descriptive tags.

World description: {description}
Era: {era}
Factions: {factions}

Return a JSON array of objects: [{{"tag": "tag_name", "weight": 0.0-1.0}}]
Tags should capture: genre, themes, setting, mood, key mechanics.
Keep tags short (1-3 words), lowercase."""


async def _generate_world_tags(db: AsyncSession, world_id: uuid.UUID, config: dict):
    try:
        faction_names = ", ".join(f.get("name", "") for f in config.get("factions", []))
        result = await llm_router.generate_json(
            role="reaction_agent",
            prompt=TAG_GEN_PROMPT.format(
                description=config.get("description", ""),
                era=config.get("era", ""),
                factions=faction_names,
            ),
            max_tokens=512,
        )
        tags = result if isinstance(result, list) else result.get("tags", [])
        for item in tags[:8]:
            if isinstance(item, dict) and item.get("tag"):
                tag = WorldTag(
                    world_id=world_id,
                    tag=str(item["tag"]).lower().strip()[:100],
                    weight=float(item.get("weight", 1.0)),
                )
                db.add(tag)
    except Exception:
        logger.exception("genesis.tag_generation_failed")


async def _generate_relationships(db: AsyncSession, world_id: uuid.UUID, agents: list[Agent]):
    import random

    for i, agent_a in enumerate(agents):
        num_relations = random.randint(2, min(5, len(agents) - 1))
        others = [a for j, a in enumerate(agents) if j != i]
        targets = random.sample(others, min(num_relations, len(others)))
        for agent_b in targets:
            rel_type = random.choice(["ally", "rival", "neutral", "trade", "mentor"])
            rel = Relationship(
                world_id=world_id,
                agent_a=agent_a.id,
                agent_b=agent_b.id,
                type=rel_type,
                strength=round(random.uniform(0.1, 1.0), 2),
            )
            db.add(rel)
