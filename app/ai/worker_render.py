import logging
import time

from app.task_queue.redis_queue import pop_job
from app.ai.llm_grok import parse_message
from app.database import SessionLocal
from app.crud import create_task
from app.models import Message

logger = logging.getLogger("worker")


def run_once():
    job = pop_job()
    if not job:
        return {"status": "empty"}

    message_id = job["message_id"]

    db = SessionLocal()
    try:
        msg = db.get(Message, message_id)
        if not msg:
            return {"status": "message_not_found"}

        start = time.time()
        result = parse_message(msg.content)
        elapsed = round(time.time() - start, 2)

        if result.get("is_task"):
            create_task(db, result, msg.sender_id, msg.id)
            return {
                "status": "task_created",
                "elapsed": elapsed
            }

        return {"status": "not_a_task", "elapsed": elapsed}

    finally:
        db.close()
