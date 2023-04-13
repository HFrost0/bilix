import asyncio
from pathlib import Path
from typing import Union
import httpx

import bilix.api.cctv as api
from bilix._handle import Handler
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import HandleMethodError


class DownloaderCctv(BaseDownloaderM3u8):
    def __init__(
            self,
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

    async def get_series(self, url: str, path: Path = Path('.'), quality=0):
        pid, vide, vida = await api.get_id(self.client, url)
        if vida is None:  # 单个视频
            await self.get_video(pid, quality=quality)
        else:  # 剧集
            title, pids = await api.get_series_info(self.client, vide, vida)
            if self.hierarchy:
                path /= title
                path.mkdir(parents=True, exist_ok=True)
            await asyncio.gather(*[self.get_video(pid, path, quality) for pid in pids])

    async def get_video(self, url_or_pid: str, path: Path = Path('.'), quality=0):
        if url_or_pid.startswith('http'):
            pid, _, _ = await api.get_id(self.client, url_or_pid)
        else:
            pid = url_or_pid
        title, m3u8_urls = await api.get_media_info(self.client, pid)
        m3u8_url = m3u8_urls[min(quality, len(m3u8_urls) - 1)]
        file_path = await self.get_m3u8_video(m3u8_url,  path / f"{title}.ts")
        return file_path


@Handler.register(name='CCTV')
def handle(kwargs):
    keys = kwargs['keys']
    method = kwargs['method']
    if 'cctv' in keys[0]:
        d = DownloaderCctv
        if method == 's' or method == 'get_series':
            m = d.get_series
        elif method == 'v' or method == 'get_video':
            m = d.get_video
        else:
            raise HandleMethodError(d, method)
        return d, m
