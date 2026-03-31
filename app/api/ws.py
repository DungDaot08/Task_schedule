import asyncio
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
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                print("📩", data)
            except asyncio.TimeoutError:
                # 👇 không có message → vẫn giữ connection
                pass
    except WebSocketDisconnect:
        manager.disconnect(str(user_id))
        print(f"❌ WS disconnected: user_id={user_id}")
