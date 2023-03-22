import asyncio
from typing import Union
import httpx
import bilix.api.hanime1 as api
from bilix.handle import Handler
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import HandleMethodError


class DownloaderHanime1(BaseDownloaderPart, BaseDownloaderM3u8):
    def __init__(self, videos_dir: str = "videos", stream_retry=5,
                 speed_limit: Union[float, int] = None, progress=None, browser: str = None):
        client = httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderHanime1, self).__init__(client, videos_dir, speed_limit=speed_limit,
                                                stream_retry=stream_retry, progress=progress, browser=browser)

    async def get_video(self, url: str, image=False):
        video_info = await api.get_video_info(self.client, url)
        video_url = video_info.video_url
        cors = [self.get_m3u8_video(video_url, file_name=video_info.title + '.ts') if '.m3u8' in video_url else
                self.get_file(video_url, file_name=video_info.title + '.mp4')]
        if image:
            cors.append(self._get_static(video_info.img_url, name=video_info.title))
        await asyncio.gather(*cors)


@Handler.register('hanime1')
def handle(kwargs):
    keys = kwargs['keys']
    method = kwargs['method']
    if 'hanime1' in keys[0]:
        d = DownloaderHanime1
        if method == 'get_video' or method == 'v':
            m = d.get_video
            return d, m
        raise HandleMethodError(d, method)
