from typing import Dict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id (string) -> websocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[str(user_id)] = websocket

    def disconnect(self, user_id):
        user_id = str(user_id)
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_to_user(self, user_id, data: dict):
        ws = self.active_connections.get(str(user_id))
        if ws:
            await ws.send_json(data)

    async def broadcast(self, data: dict):
        for user_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(data)
            except:
                self.disconnect(user_id)


manager = ConnectionManager()
