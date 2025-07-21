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

# Apply SSL settings only if using a secure 'rediss://' URL
if redis_url.startswith("rediss://"):
    celery_app.conf.update(
        broker_connection_options={
            'ssl_cert_reqs': ssl.CERT_NONE
        },
        result_backend_transport_options={
            'ssl_cert_reqs': ssl.CERT_NONE
        }
    )

if __name__ == '__main__':
    celery_app.start()
