"""Background task that continuously generates new worlds autonomously."""

import asyncio
import random

import structlog
from sqlalchemy import select, func

from null_engine.core.genesis import create_world
from null_engine.db import async_session
from null_engine.models.tables import World

logger = structlog.get_logger()

AUTO_SEEDS = [
    "Neon Joseon — 1700년대 조선이 증기기관을 발명한 대체역사. 왕실, 상인 길드, 비밀 학자 결사, 농민 반란군이 권력을 두고 경쟁한다.",
    "Deep Ocean Civilization — Sentient species evolve in ocean trenches. Bioluminescent cities, thermal vent economies, pressure-based caste systems.",
    "AI Pantheon — In 2089, seven superintelligent AIs govern humanity. Each has a different ethical framework. They debate, scheme, and negotiate the fate of billions.",
    "거꾸로 된 바벨탑 — 모든 인류가 하나의 언어를 쓰던 시대. 한 이단 집단이 '다름'을 발명하려 한다.",
    "Floating Archipelago — Islands drift across an endless sky. Nomadic traders, sky-pirates, cloud-miners, and the mysterious Order of the Compass.",
    "Silicon Renaissance — Florence, 1492. But instead of paint, Michelangelo sculpts with programmable matter. The Medici fund neural networks.",
    "Mycelium Network — A planet where fungal networks are sentient. Surface creatures are pawns. Underground, ancient mycelia wage slow wars spanning millennia.",
    "사이버 삼국지 — 2150년 한반도, 세 개의 메가코퍼레이션이 통일을 두고 사이버 전쟁. 해커 용병, AI 참모, 디지털 난민.",
    "The Last Library — Reality is collapsing. Factions of librarians guard different versions of history. What they preserve becomes real. What they forget, vanishes.",
    "Quantum Diplomacy — Parallel universes can now communicate. Ambassadors negotiate between realities. Some want merging, some want isolation, some want conquest.",
    "Mars Colony Year 50 — The first generation born on Mars wants independence. Earth corporations say no. Underground resistance meets corporate mercenaries.",
    "꿈의 시장 — 사람들이 꿈을 사고파는 세계. 악몽 딜러, 꿈 도둑, 꿈을 잃어버린 사람들의 혁명.",
    "Eternal Empire — A civilization that discovered immortality 10,000 years ago. Stagnation, underground mortality cults, and the 'Last Child' prophecy.",
    "Symbiont Wars — Every human bonds with an alien parasite that grants powers but slowly changes their personality. Purists vs Bonded vs the Hive.",
    "언더그라운드 서울 — 지표면이 오염되어 서울 지하 도시에서 100만명이 생존. 구역 간 영토 분쟁, 지상 탐험가, 정수 길드.",
    "Post-Music World — Sound itself has been weaponized. Silence zones are sanctuaries. Composers are generals. A deaf child may hold the key to peace.",
    "Living Architecture — Buildings are biological organisms. Architects are surgeons. A building revolution is brewing — the structures want rights.",
    "시간 난민 — 과거에서 온 사람들이 2200년에 난민 수용소에 모인다. 조선시대 선비, 로마 병사, 빅토리아 시대 과학자가 함께 생존.",
    "Infinite Casino — Reality is a game run by cosmic entities. Civilizations bet their existence. Cheaters are executed across all timelines.",
    "Ghost Internet — The dead can post online. Their social media persists and evolves. A corporation monetizes the afterlife. The living protest.",
    "Plague of Colors — A disease that turns everything one color. Each color faction fights for dominance. The colorblind are immune and hold the balance.",
    "Nomad Planet — The planet itself migrates between star systems. Civilizations must adapt to new suns every century.",
    "기억 제국 — 기억을 추출하고 이식하는 기술이 발명된 세계. 기억 귀족, 기억 없는 노동자, 기억 해방 운동.",
    "Reversed Gravity Zones — Parts of Earth have inverted gravity. Sky-floor cities, falling upward, and the border wars between Up and Down.",
    "The Emotion Market — Feelings are commodified. Joy is expensive, anger is cheap. A black market for forbidden emotions thrives underground.",
]

# Only auto-generate if fewer than this many ready/running worlds exist
MAX_AUTO_WORLDS = 3
# Wait between generation attempts
AUTO_GENESIS_INTERVAL = 300


async def auto_genesis_loop():
    """Generate worlds in the background, but only when needed."""
    logger.info("auto_genesis.started")
    used_indices: set[int] = set()

    while True:
        try:
            # Check how many worlds are ready/running — skip if enough exist
            async with async_session() as db:
                result = await db.execute(
                    select(func.count()).select_from(World).where(
                        World.status.in_(["ready", "running"])
                    )
                )
                active_count = result.scalar() or 0

            if active_count >= MAX_AUTO_WORLDS:
                logger.info("auto_genesis.skipped", active=active_count, max=MAX_AUTO_WORLDS)
                await asyncio.sleep(AUTO_GENESIS_INTERVAL)
                continue

            # Also skip if there's already a world being generated
            async with async_session() as db:
                result = await db.execute(
                    select(func.count()).select_from(World).where(World.status == "generating")
                )
                generating_count = result.scalar() or 0

            if generating_count > 0:
                logger.info("auto_genesis.waiting", generating=generating_count)
                await asyncio.sleep(60)
                continue

            # Pick a random unused seed
            available = [i for i in range(len(AUTO_SEEDS)) if i not in used_indices]
            if not available:
                used_indices.clear()
                available = list(range(len(AUTO_SEEDS)))

            idx = random.choice(available)
            used_indices.add(idx)
            seed = AUTO_SEEDS[idx]

            logger.info("auto_genesis.creating", seed=seed[:60])

            async with async_session() as db:
                world = await create_world(db, seed)
                world_id = world.id
                logger.info("auto_genesis.created", world_id=str(world_id))

                # Auto-start the simulation
                from null_engine.core.runner import SimulationRunner
                from null_engine.api.routes.worlds import _runners

                runner = SimulationRunner(world_id)
                _runners[world_id] = runner
                runner.start()

                from sqlalchemy import update
                await db.execute(
                    update(World).where(World.id == world_id).values(status="running")
                )
                await db.commit()

        except Exception:
            logger.exception("auto_genesis.error")

        await asyncio.sleep(AUTO_GENESIS_INTERVAL)
