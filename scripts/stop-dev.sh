#!/bin/bash
# Stop all development services

set -e

echo "🛑 Stopping VectorDB development environment..."

docker-compose down

echo "✅ All services stopped"
echo ""
echo "💡 To remove volumes (databases): docker-compose down -v"
