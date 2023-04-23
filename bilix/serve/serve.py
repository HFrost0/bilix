import asyncio
import logging
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect

from bilix.sites.bilibili import DownloaderBilibili
from bilix.sites.jable import DownloaderJable
from bilix.download.base_downloader import BaseDownloader
from bilix.progress.ws_progress import WebSocketProgress
from .app import app
from . import auth
from fastapi import WebSocket, Depends
from typing import List, Coroutine, Dict

site_map: Dict[str, type[BaseDownloader]] = {
    'bilibili': DownloaderBilibili,
    'jable': DownloaderJable
}


class AddForm(BaseModel):
    site: str
    method: str
    key: str


def get_coroutine(user: auth.User, form: AddForm) -> Coroutine:
    # 1. find or create downloader by user
    if form.site not in user.downloaders:
        progress = WebSocketProgress(sockets=user.active_sockets)
        downloader = site_map[form.site](speed_limit=3000 * 1e3, progress=progress)
        user.downloaders[form.site] = downloader
    else:
        downloader = user.downloaders[form.site]
    # 2. create cor
    cor = downloader.__getattribute__(form.method)(form.key)
    return cor


@app.post('/add_task')
async def add_task(form: AddForm, user: auth.User = Depends(auth.get_current_user)):
    cor = get_coroutine(user, form)
    t = asyncio.create_task(cor)
    t_name = t.get_name()
    user.tasks[t_name] = t
    return {"task_name": t_name}


@app.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str,
):
    # verify user
    try:
        user = auth.decode_token(token)
    except:
        await websocket.close(reason="invalid token")
        return
    # connect to client
    await websocket.accept()
    # add socket
    user.active_sockets.append(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            # todo
            await websocket.send_text(f"echo: {text}")
    except WebSocketDisconnect:
        logging.info(f"bye {websocket.client.host}:{websocket.client.port}")
    finally:
        user.active_sockets.remove(websocket)
