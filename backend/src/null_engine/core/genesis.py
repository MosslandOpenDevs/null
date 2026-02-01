import uuid
from typing import Any

import structlog
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
    logger.info("genesis: creating world", seed=seed_prompt[:80])

    # Generate world config via LLM
    world_config = await llm_router.generate_json(
        role="genesis_architect",
        prompt=WORLD_GEN_PROMPT.format(
            seed_prompt=seed_prompt,
            num_factions=settings.default_factions,
        ),
    )

    if extra_config:
        world_config.update(extra_config)

    world = World(seed_prompt=seed_prompt, config=world_config, status="created")
    db.add(world)
    await db.flush()

    # Create factions
    faction_specs = world_config.get("factions", [])
    factions: list[Faction] = []
    for spec in faction_specs:
        faction = Faction(
            world_id=world.id,
            name=spec["name"],
            description=spec.get("description", ""),
            color=spec.get("color", "#FFFFFF"),
        )
        db.add(faction)
        factions.append(faction)
    await db.flush()

    # Generate agents per faction
    all_agents: list[Agent] = []
    for faction, spec in zip(factions, faction_specs):
        count = spec.get("agent_count", settings.default_agents_per_faction)
        personas = await _generate_personas(
            faction.name,
            faction.description,
            world_config.get("description", seed_prompt),
            count,
        )
        for persona in personas:
            agent = Agent(
                world_id=world.id,
                faction_id=faction.id,
                name=persona.get("name", f"Agent-{uuid.uuid4().hex[:6]}"),
                persona=persona,
                beliefs=[],
                status="idle",
            )
            db.add(agent)
            all_agents.append(agent)
    await db.flush()

    # Generate initial relationships
    await _generate_relationships(db, world.id, all_agents)

    # Auto-generate world tags
    await _generate_world_tags(db, world.id, world_config)

    await db.commit()
    await db.refresh(world)
    logger.info("genesis: world created", world_id=str(world.id), agents=len(all_agents))
    return world


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
