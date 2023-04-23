import asyncio
import re
from pathlib import Path
from typing import Union, Tuple
import httpx
from . import api
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import HandleMethodError


class DownloaderHanime1:
    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
    ):
        self.client = client or httpx.AsyncClient(**api.dft_client_settings)
        self.m3u8_dl = BaseDownloaderM3u8(
            client=self.client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )
        self.file_dl = BaseDownloaderPart(
            client=self.client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
        )

    async def get_video(self, url: str, path: Path = Path('.'), image=False):
        video_info = await api.get_video_info(self.client, url)
        video_url = video_info.video_url
        cors = [
            self.m3u8_dl.get_m3u8_video(video_url, path=path / f'{video_info.title}.ts') if '.m3u8' in video_url else
            self.file_dl.get_file(video_url, path=path / f'{video_info.title}.mp4', url_name=False)]
        if image:
            cors.append(self.file_dl.get_static(video_info.img_url, path=path / video_info.title))
        await asyncio.gather(*cors)

    @classmethod
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        if 'hanime1' in keys[0]:
            if method == 'get_video' or method == 'v':
                m = cls.get_video
                return cls, m
            raise HandleMethodError(cls, method)
