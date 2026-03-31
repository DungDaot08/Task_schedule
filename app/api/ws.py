from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    await manager.connect(str(user_id), websocket)

    print(f"🔌 WS connected: user_id={user_id}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(str(user_id))
        print(f"❌ WS disconnected: user_id={user_id}")
