from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# --- World ---
class WorldCreate(BaseModel):
    seed_prompt: str
    config: dict[str, Any] = Field(default_factory=dict)


class WorldConfig(BaseModel):
    era: str = ""
    tech_level: str = ""
    factions: list[FactionSpec] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    description: str = ""


class FactionSpec(BaseModel):
    name: str
    description: str = ""
    color: str = "#FFFFFF"
    agent_count: int = 25


class WorldOut(BaseModel):
    id: uuid.UUID
    seed_prompt: str
    config: dict[str, Any]
    status: str
    current_epoch: int
    current_tick: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Faction ---
class FactionOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    name: str
    description: str
    color: str

    model_config = {"from_attributes": True}


# --- Agent ---
class AgentOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    faction_id: uuid.UUID | None
    name: str
    persona: dict[str, Any]
    beliefs: list[Any]
    status: str

    model_config = {"from_attributes": True}


class AgentMessage(BaseModel):
    agent_id: uuid.UUID
    content: str
    type: str = "speech"
    targets: list[uuid.UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationTurn(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    world_id: uuid.UUID
    epoch: int
    messages: list[AgentMessage] = Field(default_factory=list)
    topic: str = ""
    participants: list[uuid.UUID] = Field(default_factory=list)


# --- Events ---
class EventCreate(BaseModel):
    type: str = "divine_intervention"
    description: str
    target_agents: list[uuid.UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventOut(BaseModel):
    type: str
    description: str
    epoch: int
    tick: int


# --- Wiki ---
class WikiPageOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    title: str
    content: str
    status: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeEdgeOut(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float

    model_config = {"from_attributes": True}


# --- Conversation ---
class ConversationOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    epoch: int
    tick: int
    topic: str
    participants: list[str]
    messages: list[dict[str, Any]]
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- WorldTag ---
class WorldTagOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    tag: str
    weight: float

    model_config = {"from_attributes": True}


# --- WorldOut with tags ---
class WorldWithTagsOut(BaseModel):
    id: uuid.UUID
    seed_prompt: str
    config: dict[str, Any]
    status: str
    current_epoch: int
    current_tick: int
    created_at: datetime
    tags: list[WorldTagOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Concept Cluster ---
class ClusterOut(BaseModel):
    id: uuid.UUID
    label: str
    description: str
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ClusterMemberOut(BaseModel):
    id: uuid.UUID
    cluster_id: uuid.UUID
    world_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    similarity: float

    model_config = {"from_attributes": True}


class ClusterDetailOut(BaseModel):
    cluster: ClusterOut
    members: list[ClusterMemberOut] = Field(default_factory=list)


# --- Resonance ---
class ResonanceLinkOut(BaseModel):
    id: uuid.UUID
    cluster_id: uuid.UUID | None
    world_a: uuid.UUID
    world_b: uuid.UUID
    entity_a: uuid.UUID
    entity_b: uuid.UUID
    entity_type: str
    strength: float

    model_config = {"from_attributes": True}


# --- Global Search ---
class GlobalSearchResult(BaseModel):
    entity_type: str  # "wiki_page" | "agent" | "conversation"
    entity_id: uuid.UUID
    world_id: uuid.UUID
    title: str
    snippet: str
    score: float


# --- WebSocket ---
class WSEnvelope(BaseModel):
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    epoch: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


# --- Entity Mention ---
class EntityMentionOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    mention_text: str
    target_type: str
    target_id: uuid.UUID
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Semantic Neighbor ---
class SemanticNeighborOut(BaseModel):
    id: uuid.UUID
    entity_a_type: str
    entity_a_id: uuid.UUID
    entity_b_type: str
    entity_b_id: uuid.UUID
    similarity: float
    is_cross_world: str

    model_config = {"from_attributes": True}


# --- Taxonomy ---
class TaxonomyNodeOut(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None
    label: str
    description: str
    depth: int
    path: str
    member_count: int

    model_config = {"from_attributes": True}


class TaxonomyMembershipOut(BaseModel):
    id: uuid.UUID
    node_id: uuid.UUID
    world_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    similarity: float

    model_config = {"from_attributes": True}


class TaxonomyNodeDetail(BaseModel):
    node: TaxonomyNodeOut
    children: list[TaxonomyNodeOut] = Field(default_factory=list)
    members: list[TaxonomyMembershipOut] = Field(default_factory=list)


# --- Stratum ---
class StratumOut(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    epoch: int
    summary: str
    emerged_concepts: list[Any]
    faded_concepts: list[Any]
    dominant_themes: list[Any]
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Bookmark ---
class BookmarkCreate(BaseModel):
    user_session: str
    label: str = ""
    entity_type: str
    entity_id: uuid.UUID
    world_id: uuid.UUID
    note: str = ""


class BookmarkOut(BaseModel):
    id: uuid.UUID
    user_session: str
    label: str
    entity_type: str
    entity_id: uuid.UUID
    world_id: uuid.UUID
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Entity Graph ---
class EntityGraphNode(BaseModel):
    id: uuid.UUID
    type: str
    label: str


class EntityGraphEdge(BaseModel):
    source_id: uuid.UUID
    target_id: uuid.UUID
    type: str  # "mention" | "knowledge"
    weight: float


class EntityGraphOut(BaseModel):
    nodes: list[EntityGraphNode] = Field(default_factory=list)
    edges: list[EntityGraphEdge] = Field(default_factory=list)


# Resolve forward references
WorldConfig.model_rebuild()
