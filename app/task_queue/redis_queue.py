import redis
import json
import logging
from urllib.parse import urlparse

# ========================
# CONFIG
# ========================
REDIS_URL = "redis://default:AfSTAAIncDE2NTdmOGQ4YmM3YmQ0ZjQ1YWMxYmZlODZkMWMwM2E0YXAxNjI2MTE@smooth-rodent-62611.upstash.io:6379"
QUEUE = "task_nlp"

logger = logging.getLogger("redis-queue")

# ========================
# REDIS CLIENT (Upstash-safe)
# ========================
parsed = urlparse(REDIS_URL)

r = redis.Redis(
    host=parsed.hostname,
    port=parsed.port,
    username=parsed.username,   # Upstash cần
    password=parsed.password,
    ssl=True,
    decode_responses=True,
    socket_connect_timeout=5,   # ⬅️ RẤT QUAN TRỌNG
    socket_timeout=5            # ⬅️ tránh treo worker
)

# ========================
# QUEUE FUNCTIONS
# ========================


def push_job(message_id: int):
    """
    Push message_id vào queue AI
    """
    payload = json.dumps({"message_id": message_id})
    r.lpush(QUEUE, payload)
    logger.info(f"[REDIS] PUSH job | message_id={message_id}")


def pop_job():
    """
    NON-BLOCKING pop (Render / Cron safe)
    """
    try:
        logger.info("[REDIS] POP attempt...")
        data = r.rpop(QUEUE)   # ❗ NON-BLOCKING

        if not data:
            logger.info("[REDIS] QUEUE EMPTY")
            return None

        logger.info("[REDIS] POP success")
        return json.loads(data)

    except Exception as e:
        logger.exception(f"[REDIS] POP error: {e}")
        return None
