# from celery import Celery
# from config import settings
# import os
# # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproj.settings')
# os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

# # Celery configuration
# celery_app = Celery(
#     "orchestrator",
#     broker=settings.redis_url,
#     backend=settings.redis_url
# )

# celery_app.conf.update(
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_time_limit=30 * 60,  # 30 minutes
#     # Windows-specific fixes
#     worker_disable_rate_limits=True,
#     task_always_eager=False,
#     task_eager_propagates=True,
#     # Fix for Windows task location issue
#     worker_send_task_events=False,
#     task_send_sent_event=False,
# )

# # Import tasks after celery_app is defined to avoid circular imports
# # This ensures the task decorator works properly
# celery_app.autodiscover_tasks(['tasks'])

# # Force import of tasks module to register the task
# import tasks

import os
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')  # Windows/Py3.13 fix

from celery import Celery
from config import settings

celery_app = Celery(
    "orchestrator",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_disable_rate_limits=True,
    task_always_eager=False,
    task_eager_propagates=True,
)

celery_app.autodiscover_tasks(['tasks'])

try:
    import tasks
except ImportError:
    pass
