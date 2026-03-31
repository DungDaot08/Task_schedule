import threading
from app.task_queue.redis_queue import subscribe_events
from app.ws.manager import manager
import asyncio


def handle_event(data):
    try:
        user_id = data.get("user_id")

        if user_id:
            asyncio.run(manager.send_to_user(user_id, data))
        else:
            asyncio.run(manager.broadcast(data))

    except Exception as e:
        print("❌ WS send error:", e)


def start_ws_listener():
    thread = threading.Thread(
        target=subscribe_events,
        args=(handle_event,),
        daemon=True
    )
    thread.start()
