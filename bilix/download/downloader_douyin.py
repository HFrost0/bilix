import asyncio
from pathlib import Path
from typing import Union
import httpx

import bilix.api.douyin as api
from bilix._handle import Handler
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.utils import legal_title
from bilix.exception import HandleMethodError


class DownloaderDouyin(BaseDownloaderPart):
    def __init__(
            self,
            browser: str = None,
            speed_limit: Union[float, int, None] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
    ):
        client = httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderDouyin, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
        )

    async def get_video(self, url: str, path: Path = Path('.'), image=False):
        video_info = await api.get_video_info(self.client, url)
        title = legal_title(video_info.author_name, video_info.title)
        cors = [self.get_file(video_info.nwm_urls, path=path / f"{title}.mp4", url_name=False)]
        if image:
            cors.append(self.get_static(video_info.cover, path / title))
        await asyncio.gather(*cors)


@Handler.register(name='抖音')
def handle(kwargs):
    keys = kwargs['keys']
    if 'douyin' in keys[0]:
        method = kwargs['method']
        d = DownloaderDouyin
        if method == 'v' or method == 'get_video':
            m = d.get_video
        else:
            raise HandleMethodError(d, method)
        return d, m
