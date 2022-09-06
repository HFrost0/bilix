import asyncio
import re
from typing import Union, Sequence
import aiofiles
import httpx
import random
import os

from bilix.assign import Handler
from bilix.download.base_downloader import BaseDownloader
from bilix.utils import req_retry, merge_files
from bilix.log import logger


class BaseDownloaderPart(BaseDownloader):
    def __init__(self, client: httpx.AsyncClient, videos_dir: str = 'videos', part_concurrency=10):
        """
        Base Async http Content-Range Downloader

        :param client:
        :param videos_dir:
        :param part_concurrency:
        """
        super(BaseDownloaderPart, self).__init__(client, videos_dir)
        self.part_concurrency = part_concurrency

    async def _content_length(self, url_or_urls: Union[str, Sequence[str]]) -> int:
        try:
            res = await req_retry(self.client, url_or_urls, method='HEAD')
            total = int(res.headers['Content-Length'])
        except httpx.HTTPStatusError:
            # deal with HEAD 404 bug https://github.com/HFrost0/bilix/issues/16
            res = await req_retry(self.client, url_or_urls, method='GET', headers={'Range': 'bytes=0-1'})
            total = int(res.headers['Content-Range'].split('/')[-1])
        return total

    async def get_media(self, url_or_urls: Union[str, Sequence[str]],
                        media_name, task_id=None, hierarchy: str = '') -> str:
        """

        :param url_or_urls: media url or urls with backups
        :param media_name:
        :param task_id: if not provided, a new progress task will be created
        :param hierarchy:
        :return: downloaded file path
        """
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        file_path = f'{file_dir}/{media_name}'
        if os.path.exists(file_path):
            logger.info(f'[green]已存在[/green] {media_name}')
            return file_path
        total = await self._content_length(url_or_urls)
        if task_id is not None:
            self.progress.update(task_id, total=self.progress.tasks[task_id].total + total, visible=True)
        else:
            task_id = self.progress.add_task(description=media_name[:30], total=total, visible=True)
        part_length = total // self.part_concurrency
        cors = []
        part_names = []
        for i in range(self.part_concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < self.part_concurrency - 1 else total - 1
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cors.append(self._get_media_part(url_or_urls, part_name, task_id, hierarchy=hierarchy))
        file_list = await asyncio.gather(*cors)
        await merge_files(file_list, new_name=file_path)
        if self.progress.tasks[task_id].finished:
            self.progress.update(task_id, visible=False)
            logger.info(f"[cyan]已完成[/cyan] {media_name}")
        return file_path

    async def _get_media_part(self, url_or_urls: Union[str, Sequence[str]],
                              part_name, task_id, exception=0, hierarchy: str = ''):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if exception > 5:
            logger.error(f'超过重试次数 {part_name}')
            raise Exception('超过重试次数')
        start, end = map(int, part_name.split('-')[-2:])
        file_path = f'{file_dir}/{part_name}'
        if os.path.exists(file_path):
            downloaded = os.path.getsize(file_path)
            start += downloaded
            if exception == 0:
                self.progress.update(task_id, advance=downloaded)
        if start > end:
            return file_path  # skip already finished
        try:
            url = url_or_urls if type(url_or_urls) is str else random.choice(url_or_urls)
            async with self.client.stream("GET", url,
                                          headers={'Range': f'bytes={start}-{end}'}) as r:
                r.raise_for_status()
                async with aiofiles.open(file_path, 'ab') as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
                        self.progress.update(task_id, advance=len(chunk))
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            if exception > 1:
                logger.warning(f'STREAM {e.__class__.__name__} 异常可能由于网络条件不佳或并发数过大导致，若重复出现请考虑降低并发数')
            await asyncio.sleep(.1 * exception)
            await self._get_media_part(url_or_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
        except Exception as e:
            logger.warning(f'STREAM {e.__class__.__name__} 未知异常')
            await asyncio.sleep(.5 * exception)
            await self._get_media_part(url_or_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
        return file_path


@Handler(name="Part")
def handle(**kwargs):
    key = kwargs['key']
    if key.endswith('.mp4'):
        videos_dir = kwargs['videos_dir']
        part_concurrency = kwargs['part_concurrency']
        method = kwargs['method']
        d = BaseDownloaderPart(httpx.AsyncClient(http2=True), videos_dir=videos_dir, part_concurrency=part_concurrency)
        if method == 'get_video' or method == 'v':
            cor = d.get_media(key, "unnamed.mp4")
            return d, cor
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
