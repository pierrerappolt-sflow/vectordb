"""Integration tests for SQL schema integrity.

Tests that all SQL queries in the codebase work against the actual migrated schema.
This prevents runtime errors from schema mismatches.

These tests require a running PostgreSQL instance. Set TEST_DATABASE_BASE_URL environment
variable or use docker-compose to start the postgres service.
"""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio

# Mark all tests in this module as requiring database
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_BASE_URL") and os.getenv("CI") != "true",
    reason="PostgreSQL database not available (set TEST_DATABASE_BASE_URL or run docker-compose up postgres)"
)


async def run_all_migrations(conn: asyncpg.Connection) -> None:
    """Run all migration files in order to build the complete schema.

    Args:
        conn: Database connection

    """
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent.parent.parent.parent / "scripts" / "migrations"

    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    # Get all migration files in order
    migration_files = sorted(migrations_dir.glob("*.sql"))
    migration_files = [f for f in migration_files if f.is_file()]

    print(f"\n📦 Running {len(migration_files)} migrations...")

    for migration_file in migration_files:
        print(f"  ▶ {migration_file.name}")
        migration_sql = migration_file.read_text()
        try:
            await conn.execute(migration_sql)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            raise
        print("  ✓ Success")

    print("✅ All migrations completed\n")


@pytest_asyncio.fixture
async def migrated_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Create a test database with all migrations applied.

    This fixture:
    1. Creates a fresh test database
    2. Runs all migrations in order
    3. Provides a connection for tests
    4. Cleans up after all tests

    Yields:
        Database connection with migrated schema

    """
    import os

    # Get base connection URL (to postgres database)
    base_url = os.getenv(
        "TEST_DATABASE_BASE_URL",
        "postgresql://vdbuser:vdbpass@localhost:5432/postgres",
    )

    test_db_name = "vectordb_schema_test"

    # Connect to postgres database to create test database
    conn = await asyncpg.connect(base_url)

    try:
        # Drop test database if it exists
        await conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")

        # Create test database
        await conn.execute(f"CREATE DATABASE {test_db_name}")
    finally:
        await conn.close()

    # Connect to test database
    test_db_url = base_url.replace("/postgres", f"/{test_db_name}")
    test_conn = await asyncpg.connect(test_db_url)

    try:
        # Enable pgvector extension
        await test_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Run all migrations
        await run_all_migrations(test_conn)

        yield test_conn
    finally:
        # Clean up
        await test_conn.close()

        # Drop test database
        cleanup_conn = await asyncpg.connect(base_url)
        try:
            await cleanup_conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        finally:
            await cleanup_conn.close()


@pytest.mark.asyncio
class TestExtractedContentsSchema:
    """Test extracted_contents table schema matches domain entity and queries."""

    async def test_extracted_contents_table_exists(self, migrated_db: asyncpg.Connection) -> None:
        """Test that extracted_contents table exists after migrations."""
        result = await migrated_db.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'extracted_contents'
            )
        """)

        assert result is True, "extracted_contents table should exist after migrations"

    async def test_extracted_contents_has_all_required_columns(
        self, migrated_db: asyncpg.Connection
    ) -> None:
        """Test that extracted_contents has all columns required by domain entity."""
        # Get all columns from table
        rows = await migrated_db.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'extracted_contents'
            ORDER BY ordinal_position
        """)

        columns = {row["column_name"]: (row["data_type"], row["is_nullable"]) for row in rows}

        # Required columns based on ExtractedContent entity and activity queries
        required_columns = {
            "id": ("uuid", "NO"),
            "document_id": ("uuid", "NO"),
            "document_fragment_id": ("uuid", "YES"),  # Can be NULL during migration
            "content": ("text", "NO"),  # Or bytea
            "modality_type": ("character varying", "NO"),
            "modality_sequence_number": ("integer", "YES"),  # Can be NULL initially
            "is_last_of_modality": ("boolean", "NO"),
            "status": ("character varying", "NO"),
            "metadata": ("jsonb", "YES"),
            "created_at": ("timestamp with time zone", "NO"),
            "updated_at": ("timestamp with time zone", "NO"),
        }

        # Check each required column exists
        for col_name, (expected_type, _) in required_columns.items():
            assert col_name in columns, f"Column '{col_name}' should exist in extracted_contents"

            actual_type = columns[col_name][0]
            # Allow text or bytea for content (both work)
            if col_name == "content":
                assert actual_type in ("text", "bytea"), \
                    f"Column 'content' should be text or bytea, got {actual_type}"
            else:
                assert actual_type == expected_type, \
                    f"Column '{col_name}' should be {expected_type}, got {actual_type}"

    async def test_extracted_contents_indexes_exist(
        self, migrated_db: asyncpg.Connection
    ) -> None:
        """Test that all required indexes exist on extracted_contents."""
        # Get all indexes on extracted_contents
        rows = await migrated_db.fetch("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'extracted_contents'
            AND schemaname = 'public'
        """)

        indexes = {row["indexname"]: row["indexdef"] for row in rows}

        # Required indexes
        required_indexes = [
            "idx_extracted_contents_document_id",
            "idx_extracted_contents_modality_type",
            "idx_extracted_contents_document_fragment_id",
            "idx_extracted_contents_status",
        ]

        for index_name in required_indexes:
            assert index_name in indexes, \
                f"Index '{index_name}' should exist on extracted_contents"

    async def test_load_extracted_content_query_works(
        self, migrated_db: asyncpg.Connection
    ) -> None:
        """Test that the load_extracted_content_activity query works against schema."""
        from uuid import uuid4

        # Insert test data
        doc_id = uuid4()
        fragment_id = uuid4()
        ec_id = uuid4()

        # First insert a library
        library_id = uuid4()
        await migrated_db.execute("""
            INSERT INTO libraries (id, name, status)
            VALUES ($1, $2, $3)
        """, library_id, "Test Library", "active")

        # Insert a document
        await migrated_db.execute("""
            INSERT INTO documents (id, library_id, name, status)
            VALUES ($1, $2, $3, $4)
        """, doc_id, library_id, "Test Doc", "pending")

        # Insert a document fragment
        await migrated_db.execute("""
            INSERT INTO document_fragments (id, document_id, sequence_number, content, content_hash, is_final)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, fragment_id, doc_id, 1, b"test content", "hash123", False)

        # Insert extracted content with all required fields
        await migrated_db.execute("""
            INSERT INTO extracted_contents (
                id, document_id, document_fragment_id, content, modality_type,
                modality_sequence_number, is_last_of_modality, status, metadata,
                created_at, updated_at, content_hash
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), $10)
        """, ec_id, doc_id, fragment_id, "Test content", "TEXT", 1, False, "pending", "{}", "hash123")

        # Run the actual query from load_extracted_content_activity
        query = """
            SELECT id, document_id, document_fragment_id, content, modality_type,
                   modality_sequence_number, is_last_of_modality, metadata,
                   status, created_at, updated_at
            FROM extracted_contents
            WHERE id = ANY($1::uuid[])
            ORDER BY modality_sequence_number
        """

        result = await migrated_db.fetch(query, [ec_id])

        assert len(result) == 1, "Should find 1 extracted content"
        row = result[0]

        assert row["id"] == ec_id
        assert row["document_id"] == doc_id
        assert row["document_fragment_id"] == fragment_id
        assert row["content"] == "Test content"
        assert row["modality_type"] == "TEXT"
        assert row["modality_sequence_number"] == 1
        assert row["is_last_of_modality"] is False
        assert row["status"] == "pending"
        assert row["metadata"] == {}

    async def test_extracted_content_foreign_keys_exist(
        self, migrated_db: asyncpg.Connection
    ) -> None:
        """Test that foreign key constraints exist."""
        # Get foreign keys
        rows = await migrated_db.fetch("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = 'extracted_contents'
        """)

        fks = {row["column_name"]: row["foreign_table_name"] for row in rows}

        # Required foreign keys
        assert "document_id" in fks, "Should have FK on document_id"
        assert fks["document_id"] == "documents", "document_id should reference documents"

        # document_fragment_id FK is optional but should exist if column is present
        if "document_fragment_id" in fks:
            assert fks["document_fragment_id"] == "document_fragments", \
                "document_fragment_id should reference document_fragments"


@pytest.mark.asyncio
class TestAllRepositoryQueries:
    """Test that all repository SQL queries work against migrated schema."""

    async def test_can_insert_and_query_extracted_content(
        self, migrated_db: asyncpg.Connection
    ) -> None:
        """Test full lifecycle: insert -> query -> update."""
        from uuid import uuid4

        # Setup test data
        library_id = uuid4()
        doc_id = uuid4()
        fragment_id = uuid4()
        ec_id = uuid4()

        # Insert library
        await migrated_db.execute("""
            INSERT INTO libraries (id, name, status)
            VALUES ($1, $2, $3)
        """, library_id, "Test Library", "active")

        # Insert document
        await migrated_db.execute("""
            INSERT INTO documents (id, library_id, name, status)
            VALUES ($1, $2, $3, $4)
        """, doc_id, library_id, "Test Doc", "pending")

        # Insert fragment
        await migrated_db.execute("""
            INSERT INTO document_fragments (id, document_id, sequence_number, content, content_hash, is_final)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, fragment_id, doc_id, 1, b"test", "hash", False)

        # Insert extracted content
        await migrated_db.execute("""
            INSERT INTO extracted_contents (
                id, document_id, document_fragment_id, content, modality_type,
                modality_sequence_number, is_last_of_modality, status, metadata,
                created_at, updated_at, content_hash
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), $10)
        """, ec_id, doc_id, fragment_id, "Test", "TEXT", 1, True, "pending", '{"key": "value"}', "hash")

        # Query by document_id (common pattern)
        result = await migrated_db.fetch("""
            SELECT id FROM extracted_contents
            WHERE document_id = $1
            ORDER BY modality_sequence_number
        """, doc_id)

        assert len(result) == 1
        assert result[0]["id"] == ec_id

        # Update status
        await migrated_db.execute("""
            UPDATE extracted_contents
            SET status = $1, updated_at = NOW()
            WHERE id = $2
        """, "chunked", ec_id)

        # Verify update
        status = await migrated_db.fetchval("""
            SELECT status FROM extracted_contents WHERE id = $1
        """, ec_id)

        assert status == "chunked"


@pytest.mark.asyncio
class TestMigrationCompleteness:
    """Test that migrations create the complete expected schema."""

    async def test_all_core_tables_exist(self, migrated_db: asyncpg.Connection) -> None:
        """Test that all core domain tables exist."""
        required_tables = [
            "libraries",
            "documents",
            "document_fragments",
            "extracted_contents",
            "chunks",
            "chunking_strategies",
            "embedding_strategies",
            "vectorization_configs",
            "library_vectorization_configs",
            "event_logs",
        ]

        for table_name in required_tables:
            result = await migrated_db.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = $1
                )
            """, table_name)

            assert result is True, f"Table '{table_name}' should exist after migrations"

    async def test_migrations_are_idempotent(self, migrated_db: asyncpg.Connection) -> None:
        """Test that migrations can be run multiple times safely."""
        # Re-run all migrations
        await run_all_migrations(migrated_db)

        # Verify schema is still valid
        result = await migrated_db.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'extracted_contents'
            )
        """)

        assert result is True, "Schema should still be valid after re-running migrations"
