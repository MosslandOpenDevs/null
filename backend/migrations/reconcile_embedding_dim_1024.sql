-- One-off reconcile for databases created before the 1024-dim baseline.
--
-- The old schema declared vector(1536) columns, sized for OpenAI
-- text-embedding-3-small, while the default Ollama model
-- (qwen3-embedding:0.6b) emits 1024 dims — so with default settings no
-- embedding was ever stored. Any 1536-dim data that does exist came from
-- a different model and cannot be compared against 1024-dim vectors,
-- so these columns are re-created empty and repopulated by the
-- semantic_indexer / convergence background loops.
--
-- Usage: psql "$DATABASE_URL" -f migrations/reconcile_embedding_dim_1024.sql

BEGIN;

ALTER TABLE agents            ALTER COLUMN embedding TYPE vector(1024) USING NULL;
ALTER TABLE wiki_pages        ALTER COLUMN embedding TYPE vector(1024) USING NULL;
ALTER TABLE conversations     ALTER COLUMN embedding TYPE vector(1024) USING NULL;
ALTER TABLE strata            ALTER COLUMN embedding TYPE vector(1024) USING NULL;
ALTER TABLE concept_clusters  ALTER COLUMN centroid  TYPE vector(1024) USING NULL;
ALTER TABLE taxonomy_nodes    ALTER COLUMN centroid  TYPE vector(1024) USING NULL;

-- Derived similarity data is stale once embeddings reset.
TRUNCATE semantic_neighbors;
DELETE FROM concept_memberships;
DELETE FROM resonance_links;
DELETE FROM taxonomy_memberships;

COMMIT;
