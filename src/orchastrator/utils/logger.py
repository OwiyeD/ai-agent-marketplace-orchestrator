# src/orchastrator/utils/logger.py

import structlog
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from typing import Optional
from .settings import settings


def _ensure_dir(path: str) -> None:
    """Ensure the directory for a given file path exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _build_rotating_file_handler(path: str) -> RotatingFileHandler:
    """Create a rotating file handler."""
    _ensure_dir(path)
    handler = RotatingFileHandler(
        filename=path,
        maxBytes=10 * 1024 * 1024,  # 10 MB rotation
        backupCount=5,
        encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def _get_global_handlers() -> list[logging.Handler]:
    """Build global log handlers based on settings."""
    handlers: list[logging.Handler] = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    handlers.append(console_handler)

    # Global sandbox log file
    if settings.sandbox_log_file_enabled:
        handlers.append(_build_rotating_file_handler(settings.sandbox_log_file_path))

    return handlers


def configure_logging() -> None:
    """Configure structured logging with correlation IDs and sinks."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        handlers=_get_global_handlers(),
        force=True  # override defaults
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured logger instance (global)."""
    return structlog.get_logger(name)


def get_agent_logger(agent_id: str, run_id: Optional[str] = None) -> structlog.BoundLogger:
    """
    Create a dedicated logger for a specific agent run.
    Logs to logs/agents/{agent_id}_{run_id}.log in addition to global sinks.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())

    logger_name = f"agent.{agent_id}.{run_id}"
    logger = logging.getLogger(logger_name)

    if not logger.handlers:  # Prevent duplicate handlers
        agent_log_path = os.path.join("logs", "agents", f"{agent_id}_{run_id}.log")
        agent_handler = _build_rotating_file_handler(agent_log_path)
        logger.addHandler(agent_handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = True  # Also send logs to global sinks

    bound = structlog.wrap_logger(logger).bind(agent_id=agent_id, run_id=run_id)
    return bound
