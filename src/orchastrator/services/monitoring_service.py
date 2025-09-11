"""src/orchastrator/services/monitoring_service.py

Simple Prometheus metrics HTTP endpoint runner. Run as a background thread or separate process.
"""
import threading
import logging
from wsgiref.simple_server import make_server
from prometheus_client import make_wsgi_app

from ..utils.logger import get_logger
from ..config.settings import settings

logger = get_logger("monitoring_service")


class MonitoringService:
    """Expose prometheus metrics via HTTP.

    Example:
        svc = MonitoringService(host='0.0.0.0', port=8000)
        svc.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self._thread: threading.Thread | None = None

    def _run(self):
        app = make_wsgi_app()
        logger.info("Starting Prometheus metrics server on %s:%s", self.host, self.port)
        httpd = make_server(self.host, self.port, app)
        httpd.serve_forever()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Monitoring service started")

    def stop(self):
        # graceful stop would require more complex server management
        logger.info("Monitoring service stop requested (not implemented)")