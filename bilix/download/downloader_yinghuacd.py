import asyncio
import httpx
from typing import Sequence, Union

import bilix.api.yinghuacd as api
from bilix.handle import Handler, HandleMethodError
from bilix.log import logger
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderYinghuacd(BaseDownloaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10,
                 speed_limit: Union[int, float] = None, progress=None):
        stream_client = httpx.AsyncClient()
        super(DownloaderYinghuacd, self).__init__(stream_client, videos_dir, video_concurrency, part_concurrency,
                                                  speed_limit=speed_limit, progress=progress)
        self.api_client = httpx.AsyncClient(**api.dft_client_settings)

    async def get_series(self, url: str, p_range: Sequence[int] = None, hierarchy=True):
        video_info = await api.get_video_info(self.api_client, url)
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, video_info.title)
        cors = [self.get_video(u, hierarchy=hierarchy if hierarchy else '', extra=video_info if u == url else None)
                for _, u in video_info.play_info]
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, hierarchy: str = '', extra=None):
        if extra is None:
            try:
                video_info = await api.get_video_info(self.api_client, url)
            except Exception as e:
                logger.error(f"{url} 解析失败 {e}")
                return
        else:
            video_info = extra
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=name, hierarchy=hierarchy)


@Handler.register(name='樱花动漫')
def handle(kwargs):
    method = kwargs['method']
    key = kwargs['key']
    if 'yinghuacd' in key:
        d = DownloaderYinghuacd
        if method == 'get_series' or method == 's':
            m = d.get_series
        elif method == 'get_video' or method == 'v':
            m = d.get_video
        else:
            raise HandleMethodError(d, method)
        return d, m
