# AI Agent Marketplace Orchestrator - MVP

A walking skeleton implementation of an AI agent marketplace that facilitates AI agent interoperability through intelligent orchestration.

## 🏗️ Architecture Overview

The orchestrator follows a layered architecture pattern:

```
User Request → Orchestrator → Agents → Results
     ↓              ↓           ↓        ↓
Request Layer → Orchestrator Core → Agent Services → Aggregation → Delivery
```

### Framework Layers

1. **Request Layer** - User inputs via natural language or APIs
2. **Orchestrator Core** - Parses intent, decomposes tasks, routes requests
3. **Agent Services Layer** - Executes subtasks across specialized agents
4. **Aggregation Layer** - Combines results into coherent responses
5. **Delivery Layer** - Returns results to end-user applications

## 🚀 Key Features (V0 Implementation)

- **Monolithic Architecture**: Single FastAPI application for simplicity
- **State Machine**: Database-driven orchestration state tracking
- **Agent Discovery**: PostgreSQL-based agent matching using capabilities
- **Workflow Orchestration**: Hardcoded DAGs for common workflows
- **Background Processing**: Celery + Redis for asynchronous task execution
- **Failover Handling**: Simple retry logic with fallback agents

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis broker
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- pip

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/OwiyeD/ai-agent-marketplace-orchestrator.git
cd orchestrator_v1
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/orchestrator_db
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb orchestrator_db

# The application will create tables automatically on startup
```

### 4. Start Services

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery worker
celery -A celery_app worker --loglevel=info

# Terminal 3: Start FastAPI application
python main.py
```

### 5. Access the Application

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Orchestration

- `POST /orchestrate` - Create new orchestration request
- `GET /orchestrate/{id}` - Get orchestration status and results
- `GET /orchestrate` - List all orchestrations

### Agents

- `POST /agents` - Create new AI agent
- `GET /agents` - List all agents (with optional capability filtering)
- `GET /agents/{id}` - Get specific agent details

### Workflows

- `GET /workflows` - Get available workflow definitions
- `POST /demo/ecommerce-onboarding` - Demo e-commerce workflow

## 🔄 Workflow Example: E-commerce Product Onboarding

The MVP includes a hardcoded workflow for e-commerce product onboarding:

```
[Data Extractor] → [Copywriter, SEO Optimizer]
```

**Steps:**
1. **Extract**: Gather product information from various sources
2. **Copywrite**: Create compelling product descriptions
3. **SEO**: Optimize content for search engines

**Dependencies:**
- Copywriter and SEO tasks depend on extracted data
- All tasks can run in parallel after extraction

## 🧪 Testing the MVP

### 1. Create Sample Agents

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Extractor",
    "description": "Extracts product information",
    "endpoint_url": "http://localhost:8001/extract",
    "capabilities": ["extract"]
  }'
```

### 2. Start Demo Workflow

```bash
curl -X POST "http://localhost:8000/demo/ecommerce-onboarding"
```

### 3. Monitor Progress

```bash
# Get the orchestration ID from the demo response
curl "http://localhost:8000/orchestrate/{orchestration_id}"
```

## 🔧 Development Notes

### V0 Simplifications

- **Agent Discovery**: Simple PostgreSQL full-text search instead of Pinecone
- **Scoring**: Hardcoded reputation scores (all agents = 100)
- **Workflows**: Hardcoded DAGs instead of dynamic planning
- **Failover**: Basic try/except with fallback agents

### Future Enhancements

- **Microservices**: Split into separate services
- **Temporal**: Replace database state machine with Temporal
- **Vector Search**: Integrate Pinecone for semantic agent matching
- **Dynamic Workflows**: AI-powered workflow generation
- **Parallel Execution**: Enhanced task parallelism and dependency management

## 📊 Database Schema

### Orchestrations Table

```sql
CREATE TABLE orchestrations (
    id UUID PRIMARY KEY,
    user_input TEXT NOT NULL,
    current_status VARCHAR NOT NULL DEFAULT 'PARSING',
    results JSON,
    workflow_type VARCHAR,
    subtasks JSON,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Agents Table

```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    endpoint_url VARCHAR NOT NULL,
    capabilities TEXT[] NOT NULL,
    reputation_score INTEGER DEFAULT 100,
    is_active VARCHAR DEFAULT 'active'
);
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
2. **Redis Connection**: Verify Redis server is running on the configured port
3. **Celery Worker**: Check that the Celery worker is running and connected to Redis
4. **Port Conflicts**: Ensure ports 8000 (FastAPI) and 6379 (Redis) are available

### Logs

- **FastAPI**: Check terminal output for API logs
- **Celery**: Monitor Celery worker terminal for task execution logs
- **Database**: Check PostgreSQL logs for database-related issues

## 🤝 Contributing

This is an MVP implementation. For production use, consider:

- Adding authentication and authorization
- Implementing proper error handling and logging
- Adding comprehensive testing
- Enhancing security measures
- Optimizing database queries and performance

## 📄 License

[Add your license information here]



