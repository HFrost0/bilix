import re
import asyncio
from pathlib import Path
from typing import Union
import httpx
from . import api
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix import ffmpeg


class DownloaderYoutube(BaseDownloaderPart):
    pattern = re.compile(r"^https?://([A-Za-z0-9-]+\.)*(youtube\.com)")

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            # unique params
            video_concurrency: Union[int, asyncio.Semaphore] = 3
    ):
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderYoutube, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency
        )
        self.video_sema = asyncio.Semaphore(video_concurrency) if type(video_concurrency) is int else video_concurrency

    async def get_video(self, url: str, path=Path('.')):
        """
        :cli: short: v
        :param url
        :param path:
        :return:
        """
        async with self.video_sema:
            video_info = await api.get_video_info(self.client, url)
            video_path = path / (video_info.title + '.mp4')
            if video_path.exists():
                return self.logger.info(f'[green]已存在[/green] {video_path.name}')
            task_id = await self.progress.add_task(description=video_info.title, upper=True)
            path_lst = await asyncio.gather(
                self.get_file(url_or_urls=video_info.video_url, path=path / (video_info.title + '-v'), task_id=task_id),
                self.get_file(url_or_urls=video_info.audio_url, path=path / (video_info.title + '-a'), task_id=task_id)
            )
        await ffmpeg.combine(path_lst, output_path=path / (video_info.title + '.mp4'))
        self.logger.info(f'[cyan]已完成[/cyan] {video_path.name}')
        await self.progress.update(task_id=task_id, visible=False)
