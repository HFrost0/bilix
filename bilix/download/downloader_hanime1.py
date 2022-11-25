import asyncio
from typing import Union
import httpx
import bilix.api.hanime1 as api
from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader_part import BaseDownloaderPart


class DownloaderHanime1(BaseDownloaderPart):
    def __init__(self, videos_dir: str = "videos", speed_limit: Union[float, int] = None, progress=None):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "referer": "https://hanime1.me/"}, http2=False)
        super(DownloaderHanime1, self).__init__(client, videos_dir, speed_limit=speed_limit, progress=progress)

    async def get_video(self, url: str, image=False):
        video_info = await api.get_video_info(self.client, url)
        cors = [self.get_media(video_info.mp4_url, media_name=video_info.title + '.mp4')]
        if image:
            cors.append(self._get_static(video_info.img_url, name=video_info.title))
        await asyncio.gather(*cors)


@Handler('hanime1')
def handle(**kwargs):
    method = kwargs['method']
    key = kwargs['key']
    videos_dir = kwargs['videos_dir']
    image = kwargs['image']
    speed_limit = kwargs['speed_limit']
    if 'hanime1' in key:
        d = DownloaderHanime1(videos_dir=videos_dir, speed_limit=speed_limit)
        if method == 'get_video' or method == 'v':
            cor = d.get_video(key, image=image)
            return d, cor
        raise HandleMethodError(d, method)
