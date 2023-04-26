import asyncio
from pathlib import Path
import httpx
from typing import Sequence, Union, Tuple
from . import api
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderYhdmp(BaseDownloaderM3u8):
    def __init__(
            self,
            *,
            api_client: httpx.AsyncClient = None,
            stream_client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            hierarchy: bool = True,
    ):
        stream_client = stream_client or httpx.AsyncClient()
        super(DownloaderYhdmp, self).__init__(
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

    async def get_series(self, url: str, path=Path('.'), p_range: Sequence[int] = None):
        """
        :cli: short: s
        :param url:
        :param path:
        :param p_range:
        :return:
        """
        video_info = await api.get_video_info(self.api_client, url)
        ep_idx = video_info.ep_idx
        play_idx = video_info.play_idx
        title = video_info.title
        if self.hierarchy:
            path = path / title
            path.mkdir(parents=True, exist_ok=True)

        # no need to reuse get_video since we only need m3u8_url
        async def get_video(page_url, name):
            m3u8_url = await api.get_m3u8_url(self.api_client, page_url)
            await self.get_m3u8_video(m3u8_url=m3u8_url, path=path / name)

        cors = []
        for idx, (sub_title, url) in enumerate(video_info.play_info[play_idx]):
            if ep_idx == idx:
                cors.append(self.get_m3u8_video(m3u8_url=video_info.m3u8_url,
                                                path=path / f'{legal_title(title, sub_title)}.mp4'))
            else:
                cors.append(get_video(url, legal_title(title, sub_title)))
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, path=Path('.'), time_range=None):
        """
        :cli: short: v
        :param url:
        :param path:
        :param time_range:
        :return:
        """
        video_info = await api.get_video_info(self.api_client, url)
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, path=path / f'{name}.mp4', time_range=time_range)

    @classmethod
    def _decide_handle(cls, method: str, keys: Tuple[str, ...], options: dict) -> bool:
        return 'yhdmp' in keys[0]
