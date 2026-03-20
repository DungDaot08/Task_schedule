from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)

    try:
        while True:
            await websocket.receive_text()  # giữ connection
    except WebSocketDisconnect:
        manager.disconnect(user_id)
