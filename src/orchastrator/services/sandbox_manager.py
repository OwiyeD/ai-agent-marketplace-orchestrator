# src/orchastrator/services/sandbox_manager.py

import docker
import time
import threading
import io
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
from src.orchastrator.config.settings import settings
from src.orchastrator.config.logger import get_logger, get_agent_logger
from src.orchastrator.services.monitoring_service import ResourceMonitor


class DockerSandboxManager:
    """Manages sandboxed Docker containers for agent execution."""

    def __init__(self):
        self.client = docker.from_env()
        self.log = get_logger(__name__)

    @contextmanager
    def resource_monitor(
        self,
        container_id: str,
        agent_logger,
        tick_interval: int = settings.monitoring_tick_interval
    ) -> Generator[ResourceMonitor, None, None]:
        """Attach a resource monitor to a running container."""
        monitor = ResourceMonitor(
            container_id=container_id,
            tick_interval=tick_interval,
            logger=agent_logger
        )
        thread = threading.Thread(target=monitor.start, daemon=True)
        thread.start()
        try:
            yield monitor
        finally:
            monitor.stop()
            thread.join()

    def run_agent(
        self,
        agent_id: str,
        image: str,
        command: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout: int = settings.docker_timeout,
        memory_limit: str = settings.docker_memory_limit
    ) -> Dict[str, Any]:
        """
        Run an agent inside a sandboxed Docker container and capture logs/resources.
        Each run gets its own dedicated agent log file with UUID correlation ID.
        """
        run_id = str(uuid.uuid4())
        agent_logger = get_agent_logger(agent_id, run_id=run_id)
        agent_logger.info("sandbox_start", image=image, command=command)

        container = self.client.containers.run(
            image=image,
            command=command,
            environment=environment,
            detach=True,
            mem_limit=memory_limit,
            stdout=True,
            stderr=True
        )

        logs_buffer = io.StringIO()
        start_time = time.time()

        try:
            with self.resource_monitor(container.id, agent_logger) as monitor:
                # Stream logs in real time
                for log in container.logs(stream=True, follow=True):
                    decoded = log.decode("utf-8", errors="replace").rstrip()
                    logs_buffer.write(decoded + "\n")
                    agent_logger.info("sandbox_log", line=decoded)

                    if logs_buffer.tell() > settings.sandbox_log_buffer_limit:
                        agent_logger.warning(
                            "sandbox_log_buffer_truncated",
                            limit=settings.sandbox_log_buffer_limit
                        )
                        break

                exit_status = container.wait(timeout=timeout)
                runtime = time.time() - start_time

                metrics = monitor.get_metrics()
                result = {
                    "agent_id": agent_id,
                    "run_id": run_id,
                    "exit_status": exit_status,
                    "logs": logs_buffer.getvalue(),
                    "runtime": runtime,
                    "metrics": metrics,
                }

                agent_logger.info("sandbox_finished", result=result)
                return result

        except Exception as e:
            agent_logger.error("sandbox_error", error=str(e))
            raise
        finally:
            container.remove(force=True)
            agent_logger.info("sandbox_cleanup")
