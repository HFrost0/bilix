import asyncio
import re
import logging
from pathlib import Path
from typing import Union, Tuple, Annotated
import httpx
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.download.utils import parse_speed_str, str2path, parse_time_range
from bilix.progress.abc import Progress
from . import api


class DownloaderCctv(BaseDownloaderM3u8):
    pattern = re.compile(r'https?://(?:tv\.cctv\.com|tv\.cctv\.cn)/?[?/](?:pid=)?(\d+)(?:&vid=(\d+))?(?:&v=(\d+))?')

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: logging.Logger = None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            # unique params
            hierarchy: bool = True,
    ):
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderCctv, self).__init__(
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

    async def get_series(self, url: str, path: Annotated[Path, str2path] = Path('.'), quality: int = 0):
        """
        :cli short: s
        :param url:
        :param path:
        :param quality: 画面质量，越大画面质量越低，超过可选范围时自动选择最低画质
        :return:
        """
        pid, vide, vida = await api.get_id(self.client, url)
        if vida is None:  # 单个视频
            await self.get_video(pid, quality=quality)
        else:  # 剧集
            title, pids = await api.get_series_info(self.client, vide, vida)
            if self.hierarchy:
                path /= title
                path.mkdir(parents=True, exist_ok=True)
            await asyncio.gather(*[self.get_video(pid, path, quality) for pid in pids])

    async def get_video(self, url_or_pid: str, path: Annotated[Path, str2path] = Path('.'),
                        quality: int = 0, time_range: Annotated[Tuple[int, int], parse_time_range] = None):
        """
        :cli short: v
        :param url_or_pid:
        :param path:
        :param quality: 画面质量，越大画面质量越低，超过可选范围时自动选择最低画质
        :param time_range: 切片的时间范围，例如(10, 20)：从第10秒到第20秒，或字符串如'00:00:10-00:00:20' (hour:minute:second)
        :return:
        """
        if url_or_pid.startswith('http'):
            pid, _, _ = await api.get_id(self.client, url_or_pid)
        else:
            pid = url_or_pid
        title, m3u8_urls = await api.get_media_info(self.client, pid)
        m3u8_url = m3u8_urls[min(quality, len(m3u8_urls) - 1)]
        file_path = await self.get_m3u8_video(m3u8_url, path / f"{title}.mp4", time_range=time_range)
        return file_path
