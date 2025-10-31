#!/bin/bash
# Apply database migrations manually
# Usage: ./scripts/apply-migrations.sh [migration_number]
# Examples:
#   ./scripts/apply-migrations.sh        # Run all pending migrations
#   ./scripts/apply-migrations.sh 002    # Run specific migration

set -e

# Database connection parameters
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-vectordb}"
DB_USER="${DB_USER:-vdbuser}"
DB_PASSWORD="${DB_PASSWORD:-vdbpass}"

MIGRATIONS_DIR="$(dirname "$0")/migrations"

# Export password for psql
export PGPASSWORD="$DB_PASSWORD"

echo "🔍 Checking database connection..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database"
    exit 1
fi

echo "✅ Connected to database: $DB_NAME"

# Create migrations tracking table if it doesn't exist
echo "📋 Creating schema_migrations table if not exists..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(10) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);
EOF

# Function to check if migration is already applied
is_migration_applied() {
    local version=$1
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
        "SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version = '$version');"
}

# Function to apply a single migration
apply_migration() {
    local migration_file=$1
    local version=$(basename "$migration_file" | cut -d'_' -f1)
    local description=$(head -n1 "$migration_file" | sed 's/^--[[:space:]]*//')

    echo ""
    echo "🔄 Processing migration $version..."

    # Check if already applied
    if [ "$(is_migration_applied "$version")" = "t" ]; then
        echo "⏭️  Migration $version already applied, skipping"
        return 0
    fi

    echo "📝 Applying: $description"

    # Apply migration
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file"; then
        # Record migration
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
INSERT INTO schema_migrations (version, description)
VALUES ('$version', '$description')
ON CONFLICT (version) DO NOTHING;
EOF
        echo "✅ Migration $version applied successfully"
    else
        echo "❌ Migration $version failed"
        exit 1
    fi
}

# Main execution
if [ -n "$1" ]; then
    # Apply specific migration
    MIGRATION_FILE="$MIGRATIONS_DIR/${1}_*.sql"
    if [ -f $MIGRATION_FILE ]; then
        apply_migration "$MIGRATION_FILE"
    else
        echo "❌ Migration $1 not found in $MIGRATIONS_DIR"
        exit 1
    fi
else
    # Apply all pending migrations in order
    echo "🚀 Applying all pending migrations..."

    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [ -f "$migration_file" ]; then
            apply_migration "$migration_file"
        fi
    done
fi

echo ""
echo "🎉 All migrations completed successfully!"

# Show migration history
echo ""
echo "📊 Migration history:"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
SELECT version, description, applied_at
FROM schema_migrations
ORDER BY version;
EOF
