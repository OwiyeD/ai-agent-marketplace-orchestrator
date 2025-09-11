# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.orchastrator.settings import settings
from src.orchastrator.api.router import router
from src.orchastrator.logger import configure_logging

# Configure logging on startup
configure_logging(settings.log_level)

# Initialize app
app = FastAPI(
    title="AI Agent Marketplace Orchestrator",
    description="An orchestrator service for managing AI agents, workflows, and sandboxed execution.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Orchestrations", "description": "Manage orchestrations and their sub-tasks."},
        {"name": "Agents", "description": "Register, update, and query AI agents."},
        {"name": "Monitoring", "description": "Check orchestrator health and performance metrics."}
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)

# Entrypoint for local dev
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers
    )
