from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/ws", tags=["ws"])


@router.get("/ping")
async def ws_ping():
    """
    Простейший HTTP endpoint-заглушка для маршрута /api/v1/ws/ping.
    """
    return {"status": "ok", "message": "ws stub is alive"}


@router.websocket("/echo")
async def websocket_echo(websocket: WebSocket):
    """
    Простейший WebSocket-заглушка.
    При подключении читает сообщения и отправляет их обратно.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
    except Exception:
        await websocket.close()
