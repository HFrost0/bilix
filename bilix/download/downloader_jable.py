import asyncio
import re
from typing import Union
import httpx
import bilix.api.jable as api
from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderJable(BaseDownloaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10,
                 speed_limit: Union[float, int] = None, progress=None):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "referer": "https://jable.tv"}, http2=False)
        super(DownloaderJable, self).__init__(client, videos_dir, video_concurrency, part_concurrency,
                                              speed_limit=speed_limit, progress=progress)

    async def get_model(self, url: str, image=True, hierarchy=True):
        data = await api.get_model_info(self.client, url)
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, data['model_name'])
        await asyncio.gather(*[self.get_video(url, image, hierarchy) for url in data['urls']])

    async def get_video(self, url: str, image=True, hierarchy=True):
        video_info = await api.get_video_info(self.client, url)
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, f"{video_info.avid} {video_info.model_name}")
        cors = [self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=video_info.title,
                                    hierarchy=hierarchy if hierarchy else '')]
        if image:
            cors.append(self._get_static(video_info.img_url, name=video_info.title,
                                         hierarchy=hierarchy if hierarchy else ''))
        await asyncio.gather(*cors)


@Handler('jable')
def handle(**kwargs):
    method = kwargs['method']
    key = kwargs['key']
    videos_dir = kwargs['videos_dir']
    video_concurrency = kwargs['video_concurrency']
    part_concurrency = kwargs['part_concurrency']
    speed_limit = kwargs['speed_limit']
    hierarchy = kwargs['hierarchy']
    image = kwargs['image']
    if 'jable' in key or re.match(r"[A-Za-z]+-\d+", key):
        d = DownloaderJable(videos_dir=videos_dir, video_concurrency=video_concurrency,
                            part_concurrency=part_concurrency, speed_limit=speed_limit)
        if method == 'get_video' or method == 'v':
            cor = d.get_video(key, image=image, hierarchy=hierarchy)
            return d, cor
        if method == 'get_model' or method == 'm':
            cor = d.get_model(key, image=image, hierarchy=hierarchy)
            return d, cor
        raise HandleMethodError(d, method)
