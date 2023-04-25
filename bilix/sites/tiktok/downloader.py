import asyncio
from pathlib import Path
from typing import Union, Tuple
import httpx
from . import api
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.utils import legal_title
from bilix.exception import HandleMethodError


class DownloaderTiktok(BaseDownloaderPart):
    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int, None] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
    ):
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderTiktok, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
        )

    async def get_video(self, url: str, path=Path('.'), image=False):
        video_info = await api.get_video_info(self.client, url)
        title = legal_title(video_info.author_name, video_info.title)
        # since TikTok backup not fast enough some time, use the first one
        cors = [self.get_file(video_info.nwm_urls[0], path / f'{title}.mp4')]
        if image:
            cors.append(self.get_static(video_info.cover, path=path / title, ))
        await asyncio.gather(*cors)

    @classmethod
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        if 'tiktok' in keys[0]:
            if method == 'v' or method == 'get_video':
                m = cls.get_video
                return cls, m
            raise HandleMethodError(cls, method)
