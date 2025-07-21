import os
from celery import Celery
from dotenv import load_dotenv
import ssl

load_dotenv()

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("FATAL: REDIS_URL environment variable is not set. Celery cannot start.")

celery_app = Celery(
    'auravoice',
    broker=redis_url,
    backend=redis_url,
    include=['celery_worker.tasks']
)

# Basic Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Idempotently apply SSL settings to the URL for maximum compatibility.
# This prevents duplicate parameters if the env var already has them.
if redis_url.startswith("rediss://") and "ssl_cert_reqs" not in redis_url:
    redis_url = f"{redis_url}?ssl_cert_reqs=none"

# Update the broker and backend URLs with the correctly formatted URL
celery_app.conf.broker_url = redis_url
celery_app.conf.result_backend = redis_url

if __name__ == '__main__':
    celery_app.start()
