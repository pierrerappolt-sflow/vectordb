-- Migration 011: Add IVF vectorization config
-- This migration adds one vectorization config using IVF indexing strategy
-- IVF (Inverted File Index) provides faster search at scale with acceptable accuracy tradeoff

BEGIN;

-- Insert vectorization config with IVF indexing for Cohere English v3
-- Uses same embedding/chunking strategies as the FLAT version
INSERT INTO vectorization_configs (
    id,
    description,
    version,
    vector_indexing_strategy,
    vector_similarity_metric,
    embedding_strategy_ids,
    chunking_strategy_ids,
    status,
    created_at,
    updated_at
) VALUES (
    '3f7a8b4c-9d2e-4e5f-a1b6-c8d9e0f12345',
    'Cohere English v3 (1024d) - IVF Index',
    1,
    'ivf',
    'cosine',
    ARRAY['e6580cfc-4b31-5c2f-a486-f41cf344f67e'::uuid],  -- Cohere English v3 embedding
    ARRAY['28d6aaca-302e-5ad9-8517-e0fa90543684'::uuid],  -- Cohere Token Chunking
    'active',
    NOW(),
    NOW()
);

COMMIT;
