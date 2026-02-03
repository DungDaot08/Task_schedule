import time
import logging
from datetime import datetime

from app.task_queue.redis_queue import pop_job
from app.ai.llm_grok import parse_message
from app.database import SessionLocal
from app.crud import create_task
from app.models import Message

# ========================
# LOGGING CONFIG
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("ai-worker")


def run_once():
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    logger.info(f"🚀 Worker triggered | run_id={run_id}")

    try:
        logger.info("⏳ Checking Redis queue...")
        job = pop_job()  # NON-BLOCKING

        if not job:
            logger.info("📭 No job found in queue")
            return {
                "status": "empty",
                "run_id": run_id
            }

        message_id = job.get("message_id")
        logger.info(f"📩 Job received | message_id={message_id}")

        db = SessionLocal()
        try:
            logger.info(f"🔍 Fetching message | message_id={message_id}")
            msg = db.get(Message, message_id)

            if not msg:
                logger.warning(
                    f"⚠️ Message not found | message_id={message_id}"
                )
                return {
                    "status": "message_not_found",
                    "message_id": message_id,
                    "run_id": run_id
                }

            logger.info(
                f"🧠 Calling LLM | message_id={message_id}"
            )
            start = time.time()

            result = parse_message(msg.content)

            elapsed = round(time.time() - start, 2)
            logger.info(
                f"⏱️ LLM done in {elapsed}s | message_id={message_id}"
            )

            if result.get("is_task"):
                logger.info(
                    f"✅ Task detected | title='{result.get('title')}' | message_id={message_id}"
                )

                create_task(
                    db,
                    result,
                    msg.sender_id,
                    msg.id
                )

                logger.info(
                    f"📝 Task created successfully | message_id={message_id}"
                )

                return {
                    "status": "task_created",
                    "message_id": message_id,
                    "elapsed": elapsed,
                    "run_id": run_id
                }

            logger.info(
                f"❌ Message is not a task | message_id={message_id}"
            )

            return {
                "status": "not_a_task",
                "message_id": message_id,
                "elapsed": elapsed,
                "run_id": run_id
            }

        finally:
            db.close()
            logger.info(
                f"🔒 DB session closed | message_id={message_id}"
            )

    except Exception as e:
        logger.exception(
            f"🔥 Worker crashed | run_id={run_id} | error={e}"
        )
        return {
            "status": "error",
            "error": str(e),
            "run_id": run_id
        }
