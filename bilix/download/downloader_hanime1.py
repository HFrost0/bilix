import asyncio
import re

import httpx
import bilix.api.hanime1 as api
from bilix.assign import Handler
from bilix.download.base_downloader import BaseDownloader


class DownloaderHanime1(BaseDownloader):
    def __init__(self, videos_dir: str = "videos"):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "referer": "https://hanime1.me/"}, http2=False)
        super(DownloaderHanime1, self).__init__(client, videos_dir)

    async def get_video(self, url: str, image=True):
        video_info = await api.get_video_info(self.client, url)
        cors = [self._get_static(video_info.mp4_url, name=video_info.title)]
        if image:
            cors.append(self._get_static(video_info.img_url, name=video_info.title))
        await asyncio.gather(*cors)


@Handler('hanime1')
def handle(**kwargs):
    method = kwargs['method']
    key = kwargs['key']
    videos_dir = kwargs['videos_dir']
    image = kwargs['image']
    if 'hanime1' in key or re.match(r"^[1-9]\d*$", key):
        d = DownloaderHanime1(videos_dir=videos_dir)
        if method == 'get_video' or method == 'v':
            cor = d.get_video(key, image=image)
            return d, cor
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')