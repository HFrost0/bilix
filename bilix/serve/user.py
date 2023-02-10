import asyncio
from typing import List, Dict
from bilix.download.base_downloader import BaseDownloader
from fastapi.websockets import WebSocket
from pydantic import BaseModel


class User(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    username: str
    password: str
    active_sockets: List[WebSocket] = []
    downloaders: Dict[str, BaseDownloader] = {}
    tasks: Dict[str, asyncio.Task] = {}
