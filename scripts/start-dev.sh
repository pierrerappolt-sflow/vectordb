#!/bin/bash
# Start all development services with Docker Compose

set -e

echo "🚀 Starting VectorDB development environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please review and update .env with your configuration"
fi

# Build and start services
echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  - API:          http://localhost:8000"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - Temporal UI:  http://localhost:8080"
echo "  - Postgres:     localhost:5432 (user: vdbuser, db: vectordb)"
echo ""
echo "📝 Useful commands:"
echo "  - View logs:         docker-compose logs -f"
echo "  - Stop services:     docker-compose down"
echo "  - Reset databases:   docker-compose down -v"
echo "  - Restart API:       docker-compose restart api"
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Health check
echo "🔍 Checking service health..."
curl -f http://localhost:8000/docs > /dev/null 2>&1 && echo "✅ API is healthy" || echo "❌ API not ready yet"
curl -f http://localhost:8080 > /dev/null 2>&1 && echo "✅ Temporal UI is healthy" || echo "❌ Temporal UI not ready yet"

echo ""
echo "🎉 Development environment is ready!"
