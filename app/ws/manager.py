from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id (string) -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # self.active_connections: Dict[str, List[WebSocket]]

    async def connect(self, user_id, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[str(user_id)] = websocket

    def disconnect(self, user_id):
        user_id = str(user_id)
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    # async def send_to_user(self, user_id, data: dict):
    #    ws = self.active_connections.get(str(user_id))
    #    if ws:
    #        await ws.send_json(data)

    async def send_to_user(self, user_id, data: dict):
        user_id = str(user_id)
        ws = self.active_connections.get(str(user_id))

        if not ws:
            print(f"❌ No WS connection for user {user_id}")
            return

        try:
            await ws.send_json(data)
            print(f"✅ Sent WS to {user_id}: {data}")
        except Exception as e:
            print(f"🔥 WS send error for {user_id}: {e}")
            self.disconnect(user_id)

    async def broadcast(self, data: dict):
        for user_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(data)
            except:
                self.disconnect(user_id)


manager = ConnectionManager()
