from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis
import time

from src.orchastrator.models.database import get_db
from src.orchastrator.config.settings import settings

router = APIRouter()

# Record app start time
START_TIME = time.time()


@router.get("/healthz", tags=["Monitoring"], summary="Service health check")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check for orchestrator service."""

    health_status = {"status": "ok", "checks": {}}

    # ✅ Uptime
    uptime_seconds = int(time.time() - START_TIME)
    health_status["checks"]["uptime"] = f"{uptime_seconds}s"

    # ✅ Database check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # ✅ Redis check
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"error: {str(e)}"

    return health_status
