import asyncio
from pathlib import Path
from typing import Union, Tuple
import httpx

from . import api
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import HandleMethodError


class DownloaderCctv(BaseDownloaderM3u8):
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
            # unique params
            hierarchy: bool = True,
    ):
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderCctv, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )
        self.hierarchy = hierarchy

    async def get_series(self, url: str, path=Path('.'), quality=0):
        pid, vide, vida = await api.get_id(self.client, url)
        if vida is None:  # 单个视频
            await self.get_video(pid, quality=quality)
        else:  # 剧集
            title, pids = await api.get_series_info(self.client, vide, vida)
            if self.hierarchy:
                path /= title
                path.mkdir(parents=True, exist_ok=True)
            await asyncio.gather(*[self.get_video(pid, path, quality) for pid in pids])

    async def get_video(self, url_or_pid: str, path=Path('.'), quality=0, time_range: Tuple[int, int] = None):
        if url_or_pid.startswith('http'):
            pid, _, _ = await api.get_id(self.client, url_or_pid)
        else:
            pid = url_or_pid
        title, m3u8_urls = await api.get_media_info(self.client, pid)
        m3u8_url = m3u8_urls[min(quality, len(m3u8_urls) - 1)]
        file_path = await self.get_m3u8_video(m3u8_url, path / f"{title}.mp4", time_range=time_range)
        return file_path

    @classmethod
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        if 'cctv' in keys[0]:
            if method == 's' or method == 'get_series':
                m = cls.get_series
            elif method == 'v' or method == 'get_video':
                m = cls.get_video
            else:
                raise HandleMethodError(cls, method)
            return cls, m
