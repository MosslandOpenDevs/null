"""Baseline schema — full NULL engine schema at embedding dim 1024.

The previous chain was broken: its root revision was empty (created no
tables) and the next revision referenced worlds/agents/factions that no
migration created, so `alembic upgrade head` failed on any fresh database.

Existing databases created via metadata.create_all() are stamped
automatically at startup (see null_engine.db.run_migrations). If such a
database still has 1536-dim vector columns, run
backend/migrations/reconcile_embedding_dim_1024.sql once.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-14
"""

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


DDL_STATEMENTS = [
    """CREATE TYPE wiki_status AS ENUM ('draft', 'canon', 'legend', 'disputed')""",
    """CREATE TABLE worlds (
	id UUID NOT NULL, 
	seed_prompt TEXT NOT NULL, 
	config JSONB, 
	status VARCHAR(20), 
	current_epoch INTEGER, 
	current_tick INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)""",
    """CREATE TABLE concept_clusters (
	id UUID NOT NULL, 
	label VARCHAR(200) NOT NULL, 
	description TEXT, 
	centroid VECTOR(1024), 
	member_count INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
)""",
    """CREATE TABLE semantic_neighbors (
	id UUID NOT NULL, 
	entity_a_type VARCHAR(50) NOT NULL, 
	entity_a_id UUID NOT NULL, 
	entity_b_type VARCHAR(50) NOT NULL, 
	entity_b_id UUID NOT NULL, 
	similarity FLOAT, 
	is_cross_world VARCHAR(5), 
	PRIMARY KEY (id)
)""",
    """CREATE TABLE taxonomy_nodes (
	id UUID NOT NULL, 
	parent_id UUID, 
	label VARCHAR(200) NOT NULL, 
	description TEXT, 
	depth INTEGER, 
	path VARCHAR(1000), 
	centroid VECTOR(1024), 
	member_count INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES taxonomy_nodes (id) ON DELETE SET NULL
)""",
    """CREATE TABLE factions (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	color VARCHAR(7), 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE conversations (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	epoch INTEGER NOT NULL, 
	tick INTEGER NOT NULL, 
	topic VARCHAR(500), 
	participants JSONB, 
	messages JSONB, 
	summary TEXT, 
	embedding VECTOR(1024), 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	topic_ko VARCHAR(500), 
	messages_ko JSONB, 
	summary_ko TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE world_tags (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	tag VARCHAR(100) NOT NULL, 
	weight FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE concept_memberships (
	id UUID NOT NULL, 
	cluster_id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	entity_type VARCHAR(50) NOT NULL, 
	entity_id UUID NOT NULL, 
	similarity FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cluster_id) REFERENCES concept_clusters (id) ON DELETE CASCADE, 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE resonance_links (
	id UUID NOT NULL, 
	cluster_id UUID, 
	world_a UUID NOT NULL, 
	world_b UUID NOT NULL, 
	entity_a UUID NOT NULL, 
	entity_b UUID NOT NULL, 
	entity_type VARCHAR(50), 
	strength FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cluster_id) REFERENCES concept_clusters (id) ON DELETE CASCADE, 
	FOREIGN KEY(world_a) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(world_b) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE entity_mentions (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	source_type VARCHAR(50) NOT NULL, 
	source_id UUID NOT NULL, 
	mention_text VARCHAR(500) NOT NULL, 
	target_type VARCHAR(50) NOT NULL, 
	target_id UUID NOT NULL, 
	confidence FLOAT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE taxonomy_memberships (
	id UUID NOT NULL, 
	node_id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	entity_type VARCHAR(50) NOT NULL, 
	entity_id UUID NOT NULL, 
	similarity FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(node_id) REFERENCES taxonomy_nodes (id) ON DELETE CASCADE, 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE strata (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	epoch INTEGER NOT NULL, 
	summary TEXT, 
	summary_ko TEXT, 
	emerged_concepts JSONB, 
	faded_concepts JSONB, 
	dominant_themes JSONB, 
	embedding VECTOR(1024), 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE bookmarks (
	id UUID NOT NULL, 
	user_session VARCHAR(200) NOT NULL, 
	label VARCHAR(500), 
	entity_type VARCHAR(50) NOT NULL, 
	entity_id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	note TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE TABLE agents (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	faction_id UUID, 
	name VARCHAR(200) NOT NULL, 
	persona JSONB, 
	beliefs JSONB, 
	status VARCHAR(20), 
	embedding VECTOR(1024), 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(faction_id) REFERENCES factions (id) ON DELETE SET NULL
)""",
    """CREATE TABLE relationships (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	agent_a UUID NOT NULL, 
	agent_b UUID NOT NULL, 
	type VARCHAR(50), 
	strength FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(agent_a) REFERENCES agents (id) ON DELETE CASCADE, 
	FOREIGN KEY(agent_b) REFERENCES agents (id) ON DELETE CASCADE
)""",
    """CREATE TABLE wiki_pages (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	content TEXT, 
	title_ko VARCHAR(500), 
	content_ko TEXT, 
	status wiki_status, 
	version INTEGER, 
	embedding VECTOR(1024), 
	created_by_agent UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by_agent) REFERENCES agents (id) ON DELETE SET NULL
)""",
    """CREATE TABLE agent_memories (
	id UUID NOT NULL, 
	agent_id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	tier VARCHAR(10) NOT NULL, 
	content JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(agent_id) REFERENCES agents (id) ON DELETE CASCADE, 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE
)""",
    """CREATE INDEX ix_agent_memories_world_id ON agent_memories (world_id)""",
    """CREATE INDEX ix_agent_memories_agent_id ON agent_memories (agent_id)""",
    """CREATE TABLE claims (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	claim_text TEXT NOT NULL, 
	category VARCHAR(50), 
	confidence FLOAT, 
	status VARCHAR(20), 
	proposer_id UUID, 
	faction_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(proposer_id) REFERENCES agents (id) ON DELETE SET NULL, 
	FOREIGN KEY(faction_id) REFERENCES factions (id) ON DELETE SET NULL
)""",
    """CREATE INDEX ix_claims_status ON claims (status)""",
    """CREATE INDEX ix_claims_world_id ON claims (world_id)""",
    """CREATE TABLE agent_posts (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	agent_id UUID NOT NULL, 
	epoch INTEGER NOT NULL, 
	tick INTEGER NOT NULL, 
	title VARCHAR(500), 
	content TEXT NOT NULL, 
	title_ko VARCHAR(500), 
	content_ko TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(agent_id) REFERENCES agents (id) ON DELETE CASCADE
)""",
    """CREATE TABLE wiki_history (
	id UUID NOT NULL, 
	page_id UUID NOT NULL, 
	content TEXT, 
	version INTEGER NOT NULL, 
	edited_by_agent UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(page_id) REFERENCES wiki_pages (id) ON DELETE CASCADE, 
	FOREIGN KEY(edited_by_agent) REFERENCES agents (id) ON DELETE SET NULL
)""",
    """CREATE TABLE knowledge_edges (
	id UUID NOT NULL, 
	world_id UUID NOT NULL, 
	subject VARCHAR(500) NOT NULL, 
	predicate VARCHAR(200) NOT NULL, 
	object VARCHAR(500) NOT NULL, 
	source_page UUID, 
	confidence FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(world_id) REFERENCES worlds (id) ON DELETE CASCADE, 
	FOREIGN KEY(source_page) REFERENCES wiki_pages (id) ON DELETE SET NULL
)""",
    """CREATE TABLE claim_votes (
	id UUID NOT NULL, 
	claim_id UUID NOT NULL, 
	agent_id UUID NOT NULL, 
	faction_id UUID, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(claim_id) REFERENCES claims (id) ON DELETE CASCADE, 
	FOREIGN KEY(agent_id) REFERENCES agents (id) ON DELETE CASCADE, 
	FOREIGN KEY(faction_id) REFERENCES factions (id) ON DELETE SET NULL
)""",
    """CREATE INDEX ix_claim_votes_claim_id ON claim_votes (claim_id)""",
]

TABLES_REVERSE_ORDER = ['claim_votes', 'knowledge_edges', 'wiki_history', 'agent_posts', 'claims', 'agent_memories', 'wiki_pages', 'relationships', 'agents', 'bookmarks', 'strata', 'taxonomy_memberships', 'entity_mentions', 'resonance_links', 'concept_memberships', 'world_tags', 'conversations', 'factions', 'taxonomy_nodes', 'semantic_neighbors', 'concept_clusters', 'worlds']


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    for statement in DDL_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    for table in TABLES_REVERSE_ORDER:
        op.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
    op.execute("DROP TYPE IF EXISTS wiki_status")
