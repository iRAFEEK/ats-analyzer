#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting ATS Analyzer Development Environment${NC}"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

echo "🔍 Checking port availability..."
PORTS_OK=true

if ! check_port 3000; then
    echo -e "${RED}   Frontend port 3000 is occupied${NC}"
    PORTS_OK=false
fi

if ! check_port 8000; then
    echo -e "${RED}   Backend port 8000 is occupied${NC}"
    PORTS_OK=false
fi

if ! check_port 5432; then
    echo -e "${RED}   PostgreSQL port 5432 is occupied${NC}"
    PORTS_OK=false
fi

if ! check_port 6379; then
    echo -e "${RED}   Redis port 6379 is occupied${NC}"
    PORTS_OK=false
fi

if [ "$PORTS_OK" = false ]; then
    echo -e "${RED}❌ Some required ports are in use. Please free them and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All ports are available${NC}"

# Navigate to infrastructure directory
cd infra

# Pull latest images
echo "📦 Pulling Docker images..."
docker compose -f docker-compose.dev.yml pull

# Start services
echo "🏗️  Building and starting services..."
docker compose -f docker-compose.dev.yml up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL
echo "   Waiting for PostgreSQL..."
timeout 60s bash -c 'until docker exec ats_postgres pg_isready -U ats_user -d ats_db; do sleep 2; done'

# Wait for Redis
echo "   Waiting for Redis..."
timeout 30s bash -c 'until docker exec ats_redis redis-cli ping; do sleep 2; done'

# Wait for backend
echo "   Waiting for Backend..."
timeout 120s bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 3; done'

# Wait for frontend
echo "   Waiting for Frontend..."
timeout 60s bash -c 'until curl -f http://localhost:3000 > /dev/null 2>&1; do sleep 3; done'

echo ""
echo -e "${GREEN}🎉 ATS Analyzer is now running!${NC}"
echo "=================================="
echo ""
echo -e "${GREEN}📱 Frontend:${NC}     http://localhost:3000"
echo -e "${GREEN}🔧 Backend API:${NC}  http://localhost:8000"
echo -e "${GREEN}📚 API Docs:${NC}     http://localhost:8000/docs"
echo -e "${GREEN}🗄️  Database:${NC}    localhost:5432 (ats_db/ats_user/ats_pass)"
echo -e "${GREEN}🚀 Redis:${NC}        localhost:6379"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo "   View logs:           docker compose -f infra/docker-compose.dev.yml logs -f"
echo "   Stop services:       docker compose -f infra/docker-compose.dev.yml down"
echo "   Restart backend:     docker compose -f infra/docker-compose.dev.yml restart backend"
echo "   Run backend tests:   cd backend && pytest -v"
echo "   Run frontend tests:  cd frontend && npm test"
echo "   Generate API types:  cd frontend && npm run generate-types"
echo ""
echo -e "${GREEN}✨ Happy coding!${NC}"
