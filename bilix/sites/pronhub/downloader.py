import asyncio
import re
from pathlib import Path
from typing import Union, Tuple, Annotated
import httpx
from . import api
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.download.utils import str2path, parse_speed_str


class DownloaderPornhub(BaseDownloaderM3u8):
    cookie_domain = "pornhub.com"
    pattern = re.compile(r"^https?://([A-Za-z0-9-]+\.)*(pornhub\.com)")

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            # unique params
            hierarchy: bool = True,

    ):
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderPornhub, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )
        self.hierarchy = hierarchy

    async def get_uploader(self, url: str, path: Annotated[Path, str2path] = Path("."),
                           quality: Union[str, int] = 0, image=False):
        """
        get a page of videos from uploader
        :cli short: up
        :param url: uploader video page url
        :param path:
        :param quality:
        :param image:
        :return:
        """
        urls = await api.get_uploader_urls(self.client, url)
        cors = [self.get_video(url, path=path, quality=quality, image=image) for url in urls]
        await asyncio.gather(*cors)

    async def get_video(self, url: str, path: Annotated[Path, str2path] = Path("."),
                        quality: Union[str, int] = 0, image=False, time_range: Tuple[int, int] = None):
        """
        :cli short: v
        :param url:
        :param path:
        :param quality:
        :param image:
        :param time_range:
        :return:
        """
        async with self.v_sema:
            video_info = await api.get_video_info(self.client, url)
        if self.hierarchy:
            path /= f"{video_info.uploader}"
            path.mkdir(parents=True, exist_ok=True)
        m3u8_url = video_info.choose_quality(quality)
        cors = [self.get_m3u8_video(m3u8_url=m3u8_url, path=path / f"{video_info.title}.mp4", time_range=time_range)]
        if image:
            cors.append(self.get_static(video_info.img_url, path=path / video_info.title, ))
        await asyncio.gather(*cors)
