import time

from fastapi import APIRouter

from null_engine.services.llm_router import LLMGenerationError, llm_router

router = APIRouter(tags=["seeds"])

# /seeds triggers an LLM generation; cache results so anonymous traffic
# cannot turn every page load into model spend.
_SEED_CACHE_TTL_SECONDS = 300.0
_seed_cache: dict[str, object] = {"expires_at": 0.0, "seeds": []}

FALLBACK_SEEDS = [
    "A drowned archipelago where salvager guilds and cloister-scholars fight over pre-flood machines that still dream.",
    "정전이 100년째 이어지는 지하 도시. 빛을 배급하는 관료들과 어둠 속에서 새 언어를 만든 아이들이 공존한다.",
    "A generation ship whose navigation AI vanished; the deck-castes now argue whether the stars outside are real.",
    "모든 기억이 화폐가 된 사막 도시국가. 기억 채굴꾼과 망각 수도회가 마지막 원본 기억을 두고 대립한다.",
    "A fungal forest parliament where spore-linked delegates vote by dreaming, and one faction has learned to lie in dreams.",
]

GENERATE_SEEDS_PROMPT = """Generate 5 unique, creative seed prompts for an autonomous agent civilization simulator.

Each prompt should describe a compelling fictional world with:
- A vivid setting (alternate history, sci-fi, fantasy, surreal, etc.)
- Clear factions or groups in conflict
- An interesting core tension or mystery

Mix languages: write some in English, some in Korean (한국어).
Each should be 1-2 sentences, 30-80 words.
Make them wildly diverse — no two should feel similar.

Return a JSON array of strings:
["prompt 1", "prompt 2", "prompt 3", "prompt 4", "prompt 5"]
"""


@router.get("/seeds", response_model=list[str])
async def generate_seeds():
    now = time.monotonic()
    if now < float(_seed_cache["expires_at"]) and _seed_cache["seeds"]:
        return _seed_cache["seeds"]

    try:
        result = await llm_router.generate_json(
            role="reaction_agent",
            prompt=GENERATE_SEEDS_PROMPT,
        )
    except LLMGenerationError:
        result = []
    seeds: list[str] = []
    if isinstance(result, list):
        seeds = [s for s in result if isinstance(s, str)][:5]
    elif isinstance(result, dict):
        seeds = [s for s in result.get("seeds", []) if isinstance(s, str)][:5]
    if not seeds:
        seeds = FALLBACK_SEEDS

    _seed_cache["seeds"] = seeds
    _seed_cache["expires_at"] = now + _SEED_CACHE_TTL_SECONDS
    return seeds
