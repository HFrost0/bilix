import asyncio
from pathlib import Path
import httpx
from typing import Sequence, Union

import bilix.api.yinghuacd as api
from bilix._handle import Handler
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import HandleMethodError, APIError


class DownloaderYinghuacd(BaseDownloaderM3u8):
    def __init__(
            self,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            hierarchy: bool = True,
    ):
        stream_client = httpx.AsyncClient()
        super(DownloaderYinghuacd, self).__init__(
            client=stream_client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )
        self.api_client = httpx.AsyncClient(**api.dft_client_settings)
        self.hierarchy = hierarchy

    async def get_series(self, url: str, path: Path = Path("."), p_range: Sequence[int] = None):
        video_info = await api.get_video_info(self.api_client, url)
        if self.hierarchy:
            path /= video_info.title
            path.mkdir(parents=True, exist_ok=True)
        cors = [self.get_video(u, path=path, video_info=video_info if u == url else None)
                for _, u in video_info.play_info]
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, path: Path = Path('.'), video_info=None):
        if video_info is None:
            try:
                video_info = await api.get_video_info(self.api_client, url)
            except APIError as e:
                return self.logger.error(e)
        else:
            video_info = video_info
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, path=path / f'{name}.ts')


@Handler.register(name='樱花动漫')
def handle(kwargs):
    method = kwargs['method']
    keys = kwargs['keys']
    if 'yinghuacd' in keys[0]:
        d = DownloaderYinghuacd
        if method == 'get_series' or method == 's':
            m = d.get_series
        elif method == 'get_video' or method == 'v':
            m = d.get_video
        else:
            raise HandleMethodError(d, method)
        return d, m
