import asyncio
import re
from pathlib import Path
from typing import Union, Tuple, Annotated
import httpx
from . import api
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.download.utils import str2path, parse_speed_str, parse_time_range


class DownloaderHanime1(BaseDownloaderM3u8, BaseDownloaderPart):
    pattern = re.compile(r"^https?://([A-Za-z0-9-]+\.)*(hanime1\.me)")

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
    ):
        self.client = client or httpx.AsyncClient(**api.dft_client_settings)
        super().__init__(
            client=self.client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )

    async def get_video(self, url: str, path: Annotated[Path, str2path] = Path('.'),
                        image=False, time_range: Annotated[Tuple[int, int], parse_time_range] = None):
        """
        :cli short: v
        :param url:
        :param path:
        :param image:
        :param time_range:
        :return:
        """
        video_info = await api.get_video_info(self.client, url)
        video_url = video_info.video_url
        cors = [
            self.get_m3u8_video(
                video_url, path=path / f'{video_info.title}.mp4', time_range=time_range) if '.m3u8' in video_url else
            self.get_file(video_url, path=path / f'{video_info.title}.mp4')]
        if image:
            cors.append(self.get_static(video_info.img_url, path=path / video_info.title))
        await asyncio.gather(*cors)
