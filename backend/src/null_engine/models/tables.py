import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from null_engine.models.base import Base


def new_uuid():
    return uuid.uuid4()


class World(Base):
    __tablename__ = "worlds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    seed_prompt = Column(Text, nullable=False)
    config = Column(JSONB, default=dict)
    status = Column(String(20), default="created")
    current_epoch = Column(Integer, default=0)
    current_tick = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    factions = relationship("Faction", back_populates="world", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="world", cascade="all, delete-orphan")


class Faction(Base):
    __tablename__ = "factions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    color = Column(String(7), default="#FFFFFF")

    world = relationship("World", back_populates="factions")
    agents = relationship("Agent", back_populates="faction")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    faction_id = Column(UUID(as_uuid=True), ForeignKey("factions.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    persona = Column(JSONB, default=dict)
    beliefs = Column(JSONB, default=list)
    status = Column(String(20), default="idle")
    embedding = Column(Vector(1536), nullable=True)

    world = relationship("World", back_populates="agents")
    faction = relationship("Faction", back_populates="agents")


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    agent_a = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    agent_b = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), default="neutral")
    strength = Column(Float, default=0.5)


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    status = Column(Enum("draft", "canon", "legend", "disputed", name="wiki_status"), default="draft")
    version = Column(Integer, default=1)
    embedding = Column(Vector(1536), nullable=True)
    created_by_agent = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WikiHistory(Base):
    __tablename__ = "wiki_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    page_id = Column(UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, default="")
    version = Column(Integer, nullable=False)
    edited_by_agent = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(500), nullable=False)
    predicate = Column(String(200), nullable=False)
    object = Column(String(500), nullable=False)
    source_page = Column(UUID(as_uuid=True), ForeignKey("wiki_pages.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, default=0.5)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    epoch = Column(Integer, nullable=False)
    tick = Column(Integer, nullable=False, default=0)
    topic = Column(String(500), default="")
    participants = Column(JSONB, default=list)  # list[str(UUID)]
    messages = Column(JSONB, default=list)  # list[{agent_id, agent_name, content}]
    summary = Column(Text, default="")
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorldTag(Base):
    __tablename__ = "world_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)


class ConceptCluster(Base):
    __tablename__ = "concept_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    label = Column(String(200), nullable=False)
    description = Column(Text, default="")
    centroid = Column(Vector(1536), nullable=True)
    member_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConceptMembership(Base):
    __tablename__ = "concept_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("concept_clusters.id", ondelete="CASCADE"), nullable=False)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(50), nullable=False)  # "wiki_page" | "conversation" | "agent"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    similarity = Column(Float, default=0.0)


class ResonanceLink(Base):
    __tablename__ = "resonance_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("concept_clusters.id", ondelete="CASCADE"), nullable=True)
    world_a = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    world_b = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    entity_a = Column(UUID(as_uuid=True), nullable=False)
    entity_b = Column(UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), default="wiki_page")
    strength = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # "conversation" | "wiki" | "event"
    source_id = Column(UUID(as_uuid=True), nullable=False)
    mention_text = Column(String(500), nullable=False)
    target_type = Column(String(50), nullable=False)  # "agent" | "wiki_page" | "faction" | "location"
    target_id = Column(UUID(as_uuid=True), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SemanticNeighbor(Base):
    __tablename__ = "semantic_neighbors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    entity_a_type = Column(String(50), nullable=False)
    entity_a_id = Column(UUID(as_uuid=True), nullable=False)
    entity_b_type = Column(String(50), nullable=False)
    entity_b_id = Column(UUID(as_uuid=True), nullable=False)
    similarity = Column(Float, default=0.0)
    is_cross_world = Column(String(5), default="false")  # "true" | "false"


class TaxonomyNode(Base):
    __tablename__ = "taxonomy_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("taxonomy_nodes.id", ondelete="SET NULL"), nullable=True)
    label = Column(String(200), nullable=False)
    description = Column(Text, default="")
    depth = Column(Integer, default=0)
    path = Column(String(1000), default="")
    centroid = Column(Vector(1536), nullable=True)
    member_count = Column(Integer, default=0)

    children = relationship("TaxonomyNode", back_populates="parent_node", foreign_keys="[TaxonomyNode.parent_id]")
    parent_node = relationship("TaxonomyNode", remote_side="[TaxonomyNode.id]", foreign_keys="[TaxonomyNode.parent_id]")


class TaxonomyMembership(Base):
    __tablename__ = "taxonomy_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    node_id = Column(UUID(as_uuid=True), ForeignKey("taxonomy_nodes.id", ondelete="CASCADE"), nullable=False)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    similarity = Column(Float, default=0.0)


class Stratum(Base):
    __tablename__ = "strata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    epoch = Column(Integer, nullable=False)
    summary = Column(Text, default="")
    emerged_concepts = Column(JSONB, default=list)
    faded_concepts = Column(JSONB, default=list)
    dominant_themes = Column(JSONB, default=list)
    embedding = Column(Vector(1536), nullable=True)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_session = Column(String(200), nullable=False)
    label = Column(String(500), default="")
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    world_id = Column(UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
