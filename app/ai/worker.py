import time
import logging

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
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ai-worker")


def run():
    logger.info("🤖 AI Worker started, waiting for jobs...")

    while True:
        try:
            logger.info("⏳ Waiting for job from Redis...")
            job = pop_job()  # BLOCKING

            message_id = job["message_id"]
            logger.info(f"📩 Received job | message_id={message_id}")

            db = SessionLocal()

            msg = db.get(Message, message_id)
            if not msg:
                logger.warning(
                    f"⚠️ Message not found | message_id={message_id}")
                db.close()
                continue

            logger.info(f"🧠 Calling LLM | message_id={message_id}")
            start = time.time()

            result = parse_message(msg.content)

            elapsed = round(time.time() - start, 2)
            logger.info(f"⏱️ LLM done in {elapsed}s | message_id={message_id}")

            if result.get("is_task"):
                logger.info(
                    f"✅ Task detected | title='{result.get('title')}' | message_id={message_id}"
                )
                create_task(db, result, msg.sender_id, msg.id)
                logger.info(f"📝 Task created | message_id={message_id}")
            else:
                logger.info(f"❌ Not a task | message_id={message_id}")

            db.close()

        except Exception as e:
            logger.exception(f"🔥 Worker error: {e}")
            time.sleep(2)  # tránh crash loop


if __name__ == "__main__":
    run()
