import redis
import json
from urllib.parse import urlparse

REDIS_URL = "redis://default:AfSTAAIncDE2NTdmOGQ4YmM3YmQ0ZjQ1YWMxYmZlODZkMWMwM2E0YXAxNjI2MTE@smooth-rodent-62611.upstash.io:6379"
QUEUE = "task_nlp"

# Parse URL
parsed = urlparse(REDIS_URL)

r = redis.Redis(
    host=parsed.hostname,
    port=parsed.port,
    username=parsed.username,   # Upstash cần
    password=parsed.password,
    ssl=True,
    decode_responses=True
)


def push_job(message_id: int):
    """
    Push message_id vào queue AI
    """
    payload = json.dumps({"message_id": message_id})
    r.lpush(QUEUE, payload)
    print(f"[REDIS] PUSH job message_id={message_id}")


def pop_job(timeout: int = 0):
    """
    Blocking pop (BRPOP)
    timeout = 0 => chờ vô hạn
    """
    result = r.brpop(QUEUE, timeout=timeout)
    if not result:
        return None

    _, data = result
    return json.loads(data)
