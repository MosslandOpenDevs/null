import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from null_engine.db import get_db
from null_engine.models.schemas import AgentOut, EventCreate, WhisperResponseOut
from null_engine.models.tables import Agent

router = APIRouter(tags=["agents"])


@router.get("/worlds/{world_id}/agents", response_model=list[AgentOut])
async def list_agents(world_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.world_id == world_id))
    return result.scalars().all()


@router.get("/worlds/{world_id}/agents/{agent_id}", response_model=AgentOut)
async def get_agent(world_id: uuid.UUID, agent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent).where(Agent.world_id == world_id, Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.post(
    "/worlds/{world_id}/agents/{agent_id}/whisper",
    response_model=WhisperResponseOut,
)
async def whisper_to_agent(
    world_id: uuid.UUID,
    agent_id: uuid.UUID,
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Agent).where(Agent.world_id == world_id, Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Inject whisper into agent's short-term memory via metadata
    if "whispers" not in agent.persona:
        agent.persona = {**agent.persona, "whispers": []}
    agent.persona = {**agent.persona, "whispers": agent.persona.get("whispers", []) + [body.description]}
    await db.commit()
    return {"status": "whispered", "agent_id": str(agent_id)}
