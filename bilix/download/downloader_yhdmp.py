import asyncio
import httpx
from typing import Sequence, Union

import bilix.api.yhdmp as api
from bilix.handle import Handler, HandleMethodError
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderYhdmp(BaseDownloaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10,
                 speed_limit: Union[float, int] = None, progress=None):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "Referer": "https://www.yhdmp.cc"}, http2=False)
        super(DownloaderYhdmp, self).__init__(client, videos_dir, video_concurrency, part_concurrency,
                                              speed_limit=speed_limit, progress=progress)

    async def get_series(self, url: str, p_range: Sequence[int] = None, hierarchy=True):
        video_info = await api.get_video_info(self.client, url)
        ep_idx = video_info.ep_idx
        play_idx = video_info.play_idx
        title = video_info.title
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, video_info.title)

        # no need to reuse get_video since we only need m3u8_url
        async def get_video(page_url, name):
            m3u8_url = await api.get_m3u8_url(self.client, page_url)
            await self.get_m3u8_video(m3u8_url=m3u8_url, name=name, hierarchy=hierarchy if hierarchy else '')

        cors = []
        for idx, (sub_title, url) in enumerate(video_info.play_info[play_idx]):
            if ep_idx == idx:
                cors.append(self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=legal_title(title, sub_title),
                                                hierarchy=hierarchy if hierarchy else ''))
            else:
                cors.append(get_video(url, legal_title(title, sub_title)))
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, hierarchy: str = ''):
        video_info = await api.get_video_info(self.client, url)
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=name, hierarchy=hierarchy)


@Handler(name='樱花动漫P')
def handle(**kwargs):
    method = kwargs['method']
    key = kwargs['key']
    videos_dir = kwargs['videos_dir']
    video_concurrency = kwargs['video_concurrency']
    part_concurrency = kwargs['part_concurrency']
    speed_limit = kwargs['speed_limit']
    hierarchy = kwargs['hierarchy']
    p_range = kwargs['p_range']
    if 'yhdmp' in key:
        d = DownloaderYhdmp(videos_dir=videos_dir, video_concurrency=video_concurrency,
                            part_concurrency=part_concurrency, speed_limit=speed_limit)
        if method == 'get_series' or method == 's':
            cor = d.get_series(key, p_range=p_range, hierarchy=hierarchy)
            return d, cor
        elif method == 'get_video' or method == 'v':
            cor = d.get_video(key)
            return d, cor
        raise HandleMethodError(d, method)
