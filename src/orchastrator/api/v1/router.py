# from fastapi import APIRouter

# # Import routers from modules
# from . import agents, orchestration, health, subtasks

# # Create a versioned API router
# api_router = APIRouter(prefix="/v1")

# # Register all route groups
# api_router.include_router(agents.router)
# api_router.include_router(orchestration.router)
# api_router.include_router(health.router)
# api_router.include_router(subtasks.router)

# from fastapi import APIRouter
# from . import router as v1_router

# api_router = APIRouter()
# api_router.include_router(v1_router.api_router, prefix="/api")

from fastapi import APIRouter
from src.orchastrator.api import monitoring  # 👈 import new health endpoints
from src.orchastrator.api import orchestrations, agents  # your other routers

router = APIRouter()

# Include routers with tags
router.include_router(orchestrations.router, prefix="/orchestrations", tags=["Orchestrations"])
router.include_router(agents.router, prefix="/agents", tags=["Agents"])
router.include_router(monitoring.router, prefix="", tags=["Monitoring"])  # 👈 healthz
