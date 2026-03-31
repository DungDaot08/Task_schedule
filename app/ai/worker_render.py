import time
import logging
from datetime import datetime
from uuid import UUID
from app.task_queue.redis_queue import pop_job
from app.ai.llm_grok import parse_message
from app.database import SessionLocal
from app.crud import create_task
from app.models import Message
from app.ws.manager import manager
import asyncio

# ========================
# LOGGING CONFIG
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("ai-worker")


def to_str(x):
    return str(x) if x else None


async def run_once():
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    logger.info(f"🚀 Worker triggered | run_id={run_id}")

    try:
        logger.info("⏳ Checking Redis queue...")
        job = pop_job()

        if not job:
            logger.info("📭 No job found in queue")
            return {"status": "empty", "run_id": run_id}

        message_id = job.get("message_id")

        if isinstance(message_id, str):
            message_id = UUID(message_id)

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
                    f"✅ Task detected | title='{result.get('title')}'"
                )

                task, assignee_ids = create_task(
                    db,
                    result,
                    msg.sender_id,
                    msg.id
                )

                try:
                    await manager.send_to_user(
                        msg.sender_id,
                        {
                            "type": "task_created",
                            "data": {
                                    "message_id": to_str(msg.id),
                                    "task_id": to_str(task.id),
                                    "title": task.title
                            }
                        }
                    )
                    logger.info(f"📡 WebSocket sent | user_id={msg.sender_id}")

                except Exception as ws_err:
                    logger.error(f"❌ WebSocket error: {ws_err}")

                recipients = set([msg.sender_id] + assignee_ids)

                payload = {
                    "message_id": to_str(msg.id),
                    "task_id": to_str(task.id),
                    "title": task.title
                }

                for user_id in recipients:
                    try:
                        await manager.send_to_user(
                            user_id,
                            {
                                "type": "task_created" if user_id == msg.sender_id else "task_assigned",
                                "data": payload
                            }
                        )
                        logger.info(f"📡 WS sent | user_id={user_id}")

                    except Exception as ws_err:
                        logger.error(
                            f"❌ WS error | user_id={user_id} | err={ws_err}"
                        )
                # logger.info(
                #    f"📝 Task created | task_id={task.id}"
                # )

                # ⭐ QUAN TRỌNG: link message -> task
                msg.generated_task_id = task.id
                db.commit()

                logger.info(
                    f"🔗 Message linked to task | message_id={msg.id} | task_id={task.id}"
                )

                return {
                    "status": "task_created",
                    "message_id": message_id,
                    "task_id": task.id,
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
