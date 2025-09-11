# scripts/setup.sh - Complete development environment setup
#!/bin/bash
set -e

echo "🚀 Setting up AI Agent Marketplace Orchestrator development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is required but not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
poetry install

# Install pre-commit hooks
echo -e "${YELLOW}🔧 Setting up pre-commit hooks...${NC}"
poetry run pre-commit install

# Copy environment files
echo -e "${YELLOW}📋 Setting up environment configuration...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration${NC}"
fi

if [ ! -f .env.development ]; then
    cp .env.example .env.development
fi

# Start infrastructure services
echo -e "${YELLOW}🐳 Starting infrastructure services...${NC}"
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Run database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
./scripts/migrate.sh

# Seed database with sample data
echo -e "${YELLOW}🌱 Seeding database with sample data...${NC}"
poetry run python scripts/seed_data.py

# Run tests to verify setup
echo -e "${YELLOW}🧪 Running tests to verify setup...${NC}"
poetry run pytest tests/ -v

echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${GREEN}🌐 API: http://localhost:8000${NC}"
echo -e "${GREEN}📊 Grafana: http://localhost:3000 (admin/admin)${NC}"
echo -e "${GREEN}📈 Prometheus: http://localhost:9090${NC}"
echo -e "${GREEN}📖 API Docs: http://localhost:8000/docs${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Run 'make test' to run tests"
echo "3. Run 'make docker-up' to start services"
echo "4. Visit http://localhost:8000/docs for API documentation"