from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

from prometheus_client import make_asgi_app
import redis
import os

from src.orchastrator.config.database import get_db, Orchestration, Agent, create_tables
from src.orchastrator.workers.tasks import orchestrate_workflow
from config import settings

from orchestrator.core import orchestrate_workflow, generate_workflow_visualization_data
from orchestrator.metrics import TASK_COUNTER, TASK_DURATION

# Create FastAPI app
app = FastAPI(
    title="AI Agent Marketplace Orchestrator",
    description="Enhanced orchestration with monitoring and caching",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
if os.getenv("ENABLE_METRICS", "true").lower() == "true":
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/1"))

# Pydantic models for API
class UserRequest(BaseModel):
    user_input: str
    workflow_type: Optional[str] = None

class OrchestrationResponse(BaseModel):
    id: str
    user_input: str
    current_status: str
    workflow_type: Optional[str]
    subtasks: Optional[List[str]]
    results: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

class AgentCreate(BaseModel):
    name: str
    description: str
    endpoint_url: str
    capabilities: List[str]
    reputation_score: Optional[int] = 100

class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    endpoint_url: str
    capabilities: List[str]
    reputation_score: int
    is_active: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AI Agent Orchestrator"}

# Request Layer - User inputs via natural language or APIs
@app.post("/orchestrate", response_model=OrchestrationResponse)
async def create_orchestration(
    request: UserRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new orchestration request
    Step 1: Parse intent and create orchestration record
    """
    try:
        # Create orchestration record
        orchestration = Orchestration(
            user_input=request.user_input,
            workflow_type=request.workflow_type,
            current_status="PARSING"
        )
        
        db.add(orchestration)
        db.commit()
        db.refresh(orchestration)
        
        # Start background orchestration task
        background_tasks.add_task(orchestrate_workflow, orchestration.id)
        
        return OrchestrationResponse(
            id=orchestration.id,
            user_input=orchestration.user_input,
            current_status=orchestration.current_status,
            workflow_type=orchestration.workflow_type,
            subtasks=orchestration.subtasks,
            results=orchestration.results,
            created_at=orchestration.created_at.isoformat(),
            updated_at=orchestration.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create orchestration: {str(e)}")

# Get orchestration status and results
@app.get("/orchestrate/{orchestration_id}", response_model=OrchestrationResponse)
async def get_orchestration(
    orchestration_id: str,
    db: Session = Depends(get_db)
):
    """Get orchestration status and results"""
    orchestration = db.query(Orchestration).filter(Orchestration.id == orchestration_id).first()
    
    if not orchestration:
        raise HTTPException(status_code=404, detail="Orchestration not found")
    
    return OrchestrationResponse(
        id=orchestration.id,
        user_input=orchestration.user_input,
        current_status=orchestration.current_status,
        workflow_type=orchestration.workflow_type,
        subtasks=orchestration.subtasks,
        results=orchestration.results,
        created_at=orchestration.created_at.isoformat(),
        updated_at=orchestration.updated_at.isoformat()
    )

# List all orchestrations
@app.get("/orchestrate", response_model=List[OrchestrationResponse])
async def list_orchestrations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all orchestrations"""
    orchestrations = db.query(Orchestration).offset(skip).limit(limit).all()
    
    return [
        OrchestrationResponse(
            id=o.id,
            user_input=o.user_input,
            current_status=o.current_status,
            workflow_type=o.workflow_type,
            subtasks=o.subtasks,
            results=o.results,
            created_at=o.created_at.isoformat(),
            updated_at=o.updated_at.isoformat()
        )
        for o in orchestrations
    ]

# Agent Services Layer - Manage AI agents
@app.post("/agents", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db)
):
    """Create a new AI agent"""
    try:
        db_agent = Agent(
            name=agent.name,
            description=agent.description,
            endpoint_url=agent.endpoint_url,
            capabilities=agent.capabilities,
            reputation_score=agent.reputation_score
        )
        
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        
        return AgentResponse(
            id=db_agent.id,
            name=db_agent.name,
            description=db_agent.description,
            endpoint_url=db_agent.endpoint_url,
            capabilities=db_agent.capabilities,
            reputation_score=db_agent.reputation_score,
            is_active=db_agent.is_active
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    capability: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all agents, optionally filtered by capability"""
    query = db.query(Agent)
    
    if capability:
        query = query.filter(Agent.capabilities.contains([capability]))
    
    agents = query.all()
    
    return [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            endpoint_url=agent.endpoint_url,
            capabilities=agent.capabilities,
            reputation_score=agent.reputation_score,
            is_active=agent.is_active
        )
        for agent in agents
    ]

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific agent by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        endpoint_url=agent.endpoint_url,
        capabilities=agent.capabilities,
        reputation_score=agent.reputation_score,
        is_active=agent.is_active
    )

# Workflow definitions endpoint
@app.get("/workflows")
async def get_workflow_definitions():
    """Get available workflow definitions"""
    from src.orchastrator.workers.tasks import WORKFLOW_DEFINITIONS
    return WORKFLOW_DEFINITIONS

# Demo endpoint for testing
@app.post("/demo/ecommerce-onboarding")
async def demo_ecommerce_onboarding(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Demo endpoint for e-commerce product onboarding workflow"""
    
    # Create sample agents if they don't exist
    sample_agents = [
        {
            "name": "Data Extractor",
            "description": "Extracts product information from various sources",
            "endpoint_url": "http://localhost:8001/extract",
            "capabilities": ["extract"]
        },
        {
            "name": "Copywriter",
            "description": "Creates compelling product descriptions",
            "endpoint_url": "http://localhost:8002/copywrite",
            "capabilities": ["copywrite"]
        },
        {
            "name": "SEO Optimizer",
            "description": "Optimizes content for search engines",
            "endpoint_url": "http://localhost:8003/seo",
            "capabilities": ["seo"]
        }
    ]
    
    for agent_data in sample_agents:
        existing = db.query(Agent).filter(Agent.name == agent_data["name"]).first()
        if not existing:
            agent = Agent(**agent_data)
            db.add(agent)
    
    db.commit()
    
    # Create demo orchestration
    demo_input = "Create a new product onboarding workflow for an e-commerce store"
    orchestration = Orchestration(
        user_input=demo_input,
        workflow_type="ecommerce_onboarding",
        current_status="PARSING"
    )
    
    db.add(orchestration)
    db.commit()
    db.refresh(orchestration)
    
    # Start orchestration
    background_tasks.add_task(orchestrate_workflow, orchestration.id)
    
    return {
        "message": "Demo e-commerce onboarding workflow started",
        "orchestration_id": orchestration.id,
        "workflow_type": "ecommerce_onboarding"
    }

# NEW: Add workflow visualization endpoint
@app.get("/workflow/{orchestration_id}/visualization")
async def get_workflow_visualization(orchestration_id: str):
    """Get workflow data for frontend visualization"""
    result = generate_workflow_visualization_data.delay(orchestration_id)
    return result.get(timeout=30)

# NEW: Add cache statistics endpoint
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    info = redis_client.info()
    return {
        "cache_hits": info.get("keyspace_hits", 0),
        "cache_misses": info.get("keyspace_misses", 0),
        "memory_usage": info.get("used_memory_human", "0B"),
        "connected_clients": info.get("connected_clients", 0)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )



