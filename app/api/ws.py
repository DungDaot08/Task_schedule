from fastapi import WebSocket

connections = set()


async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        pass
    finally:
        connections.remove(ws)
