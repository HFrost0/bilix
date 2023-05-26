import asyncio
from pathlib import Path
import httpx
import re
from m3u8 import Segment
from typing import Union, Tuple, Annotated
from . import api
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.exception import APIError
from bilix.download.utils import parse_speed_str, str2path


class DownloaderYinghuacd(BaseDownloaderM3u8):
    def __init__(
            self,
            *,
            stream_client: httpx.AsyncClient = None,
            api_client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            hierarchy: bool = True,
    ):
        stream_client = stream_client or httpx.AsyncClient()
        super(DownloaderYinghuacd, self).__init__(
            client=stream_client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )
        self.api_client = api_client or httpx.AsyncClient(**api.dft_client_settings)
        self.hierarchy = hierarchy

    def _after_seg(self, seg: Segment, content: bytearray) -> bytearray:
        # in case .png
        if re.fullmatch(r'.*\.png', seg.absolute_uri):
            _, _, content = content.partition(b'\x47\x40')
        return content

    async def get_series(self, url: str, path: Annotated[Path, str2path] = Path("."),
                         p_range: Tuple[int, int] = None):
        """
        :cli short: s
        :param url:
        :param path:
        :param p_range:
        :return:
        """
        video_info = await api.get_video_info(self.api_client, url)
        if self.hierarchy:
            path /= video_info.title
            path.mkdir(parents=True, exist_ok=True)
        cors = [self.get_video(u, path=path, video_info=video_info if u == url else None)
                for _, u in video_info.play_info]
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, path: Annotated[Path, str2path] = Path('.'),
                        time_range: Tuple[int, int] = None, video_info=None):
        """
        :cli short: v
        :param url:
        :param path:
        :param time_range:
        :param video_info:
        :return:
        """
        if video_info is None:
            try:
                video_info = await api.get_video_info(self.api_client, url)
            except APIError as e:
                return self.logger.error(e)
        else:
            video_info = video_info
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, path=path / f'{name}.mp4', time_range=time_range)

    @classmethod
    def decide_handle(cls, method: str, keys: Tuple[str, ...]):
        return 'yinghuacd.' in keys[0]
