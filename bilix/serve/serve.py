import logging

from starlette.websockets import WebSocketDisconnect, WebSocketClose

from .app import app
from . import auth
from fastapi import WebSocket, Depends


@app.get('/t')
async def t(user: auth.User = Depends(auth.get_current_user)):
    return user.username


@app.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str,
):
    try:
        auth.decode_token(token)
    except:
        await websocket.close(reason="invalid token")
        return
    # connect to client
    try:
        await websocket.accept()
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"echo: {text}")
    except WebSocketDisconnect:
        logging.info(f"bye {websocket.client.host}:{websocket.client.port}")
        return
