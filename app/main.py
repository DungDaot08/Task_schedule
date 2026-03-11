from fastapi import FastAPI, WebSocket
from app.api.message import router as message_router
from app.api.user_api import router as user_router
from app.api.task_api import router as task_router
from app.api.auth import router as auth_router
from app.api.ws import websocket_endpoint

app = FastAPI()

app.include_router(message_router)
app.include_router(user_router)
app.include_router(task_router)
app.include_router(auth_router)


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await websocket_endpoint(ws)
