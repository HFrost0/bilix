import asyncio
from typing import Union
import httpx
import bilix.api.hanime1 as api
from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader_part import BaseDownloaderPart


class DownloaderHanime1(BaseDownloaderPart):
    def __init__(self, videos_dir: str = "videos", stream_retry=5,
                 speed_limit: Union[float, int] = None, progress=None):
        client = httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderHanime1, self).__init__(client, videos_dir, speed_limit=speed_limit,
                                                stream_retry=stream_retry, progress=progress)

    async def get_video(self, url: str, image=False):
        video_info = await api.get_video_info(self.client, url)
        cors = [self.get_file(video_info.mp4_url, file_name=video_info.title + '.mp4')]
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
