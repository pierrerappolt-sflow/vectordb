-- Migration 010: Insert default vectorization configs
-- This migration removes all existing configs and inserts exactly 4 default Cohere configs
-- Replaces the runtime bootstrap code with a one-time migration

BEGIN;

-- Delete all existing vectorization configs (CASCADE will handle references)
DELETE FROM vectorization_configs;

-- Delete all existing strategies to start fresh
DELETE FROM chunking_strategies;
DELETE FROM embedding_strategies;

-- Insert 1 shared chunking strategy (deterministic UUID based on model_key)
INSERT INTO chunking_strategies (
    id,
    name,
    model_key,
    status,
    modality,
    behavior,
    chunk_size_tokens,
    chunk_overlap_tokens,
    min_chunk_size_tokens,
    max_chunk_size_tokens,
    config,
    created_at,
    updated_at
) VALUES (
    '28d6aaca-302e-5ad9-8517-e0fa90543684',
    'Cohere Token Chunking (256 tokens)',
    'cohere-token-256',
    'active',
    'TEXT',
    'split',
    256,
    25,
    50,
    512,
    '{"max_tokens": 512}'::jsonb,
    NOW(),
    NOW()
);

-- Insert 4 embedding strategies (deterministic UUIDs based on model_key)
INSERT INTO embedding_strategies (
    id,
    name,
    model_key,
    status,
    modality,
    dimensions,
    provider,
    model_name,
    max_tokens,
    config,
    created_at,
    updated_at
) VALUES
    (
        'e6580cfc-4b31-5c2f-a486-f41cf344f67e',
        'Cohere English v3 (1024d)',
        'embed-english-v3.0',
        'active',
        'TEXT',
        1024,
        'cohere',
        'embed-english-v3.0',
        512,
        '{}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        'fa8dbc02-ba62-5c81-aa1e-d47f0a381245',
        'Cohere Multilingual v3 (1024d)',
        'embed-multilingual-v3.0',
        'active',
        'TEXT',
        1024,
        'cohere',
        'embed-multilingual-v3.0',
        512,
        '{}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        '644ec044-84b2-57ac-8a45-ee8f5491a04d',
        'Cohere English Light v3 (384d)',
        'embed-english-light-v3.0',
        'active',
        'TEXT',
        384,
        'cohere',
        'embed-english-light-v3.0',
        512,
        '{}'::jsonb,
        NOW(),
        NOW()
    ),
    (
        '9c89ca76-7acc-53d5-b5f6-4898363501f7',
        'Cohere Multilingual Light v3 (384d)',
        'embed-multilingual-light-v3.0',
        'active',
        'TEXT',
        384,
        'cohere',
        'embed-multilingual-light-v3.0',
        512,
        '{}'::jsonb,
        NOW(),
        NOW()
    );

-- Insert 4 vectorization configs (one per embedding model, all with FLAT indexing and COSINE similarity)
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
) VALUES
    (
        'dbdebef7-b6a0-46de-9fd5-79ee7657ae86',
        'Cohere English v3 (1024d)',
        1,
        'flat',
        'cosine',
        ARRAY['e6580cfc-4b31-5c2f-a486-f41cf344f67e'::uuid],
        ARRAY['28d6aaca-302e-5ad9-8517-e0fa90543684'::uuid],
        'active',
        NOW(),
        NOW()
    ),
    (
        'e26e5bea-774c-4d58-ba9b-0521b5b8ade7',
        'Cohere Multilingual v3 (1024d)',
        1,
        'flat',
        'cosine',
        ARRAY['fa8dbc02-ba62-5c81-aa1e-d47f0a381245'::uuid],
        ARRAY['28d6aaca-302e-5ad9-8517-e0fa90543684'::uuid],
        'active',
        NOW(),
        NOW()
    ),
    (
        '4039d402-f6e3-42c2-856b-54c8d86e98e0',
        'Cohere English Light v3 (384d)',
        1,
        'flat',
        'cosine',
        ARRAY['644ec044-84b2-57ac-8a45-ee8f5491a04d'::uuid],
        ARRAY['28d6aaca-302e-5ad9-8517-e0fa90543684'::uuid],
        'active',
        NOW(),
        NOW()
    ),
    (
        '92d25646-caba-4cbd-bf93-b98cdea31b38',
        'Cohere Multilingual Light v3 (384d)',
        1,
        'flat',
        'cosine',
        ARRAY['9c89ca76-7acc-53d5-b5f6-4898363501f7'::uuid],
        ARRAY['28d6aaca-302e-5ad9-8517-e0fa90543684'::uuid],
        'active',
        NOW(),
        NOW()
    );

COMMIT;
