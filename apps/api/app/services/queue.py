from redis import Redis
from rq import Queue

from app.config import get_settings


def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def get_queue() -> Queue:
    settings = get_settings()
    return Queue(settings.queue_name, connection=get_redis())


def enqueue_chapter_job(job_id: str) -> str:
    queue = get_queue()
    job = queue.enqueue(
        "app.workers.translate_chapter.process_chapter",
        job_id,
        job_timeout="2h",
        result_ttl=86400,
        failure_ttl=86400,
    )
    return job.id


def enqueue_cleanup_job() -> str:
    queue = get_queue()
    job = queue.enqueue(
        "app.workers.cleanup.cleanup_expired_jobs",
        job_timeout="30m",
        result_ttl=3600,
        failure_ttl=3600,
    )
    return job.id
