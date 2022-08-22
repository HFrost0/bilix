import asyncio
import re

import httpx
import bilix.api.jable as api
from bilix.assign import Handler
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderJable(BaseDownloaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "referer": "https://jable.tv"}, http2=False)
        super(DownloaderJable, self).__init__(client, videos_dir, video_concurrency, part_concurrency)

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
def handle(
        method: str,
        key: str,
        videos_dir: str,
        video_concurrency: int,
        part_concurrency: int,
        cookie: str,
        quality: int,
        days: int,
        num: int,
        order: str,
        keyword: str,
        no_series: bool,
        hierarchy: bool,
        image: bool,
        subtitle: bool,
        dm: bool,
        only_audio: bool,
        p_range,
):
    if 'jable' in key or re.match(r"[A-Za-z]+-\d+", key):
        d = DownloaderJable(videos_dir=videos_dir, video_concurrency=video_concurrency,
                            part_concurrency=part_concurrency)
        if method == 'get_video' or method == 'v':
            cor = d.get_video(key, image=image, hierarchy=hierarchy)
            return d, cor
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
