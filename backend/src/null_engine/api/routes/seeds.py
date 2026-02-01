from fastapi import APIRouter

from null_engine.services.llm_router import llm_router

router = APIRouter(tags=["seeds"])

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


@router.get("/seeds")
async def generate_seeds():
    result = await llm_router.generate_json(
        role="reaction_agent",
        prompt=GENERATE_SEEDS_PROMPT,
    )
    if isinstance(result, list):
        return result[:5]
    return result.get("seeds", [])
