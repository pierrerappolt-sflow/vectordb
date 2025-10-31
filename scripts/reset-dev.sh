#!/bin/bash
# Reset the development environment (removes all data)

set -e

echo "⚠️  WARNING: This will delete all databases and volumes!"
read -p "Are you sure you want to continue? (yes/no) " -n 3 -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "🗑️  Stopping and removing all containers and volumes..."
docker-compose down -v

echo "🧹 Removing Docker images..."
docker-compose rm -f

echo "✅ Development environment reset complete"
echo ""
echo "To start fresh: ./scripts/start-dev.sh"
