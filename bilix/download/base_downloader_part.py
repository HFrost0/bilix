import asyncio
import re
from typing import Union, List, Iterable
import aiofiles
import httpx
import random
import os

from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader import BaseDownloader
from bilix.utils import req_retry, merge_files
from bilix.log import logger


class BaseDownloaderPart(BaseDownloader):
    def __init__(self, client: httpx.AsyncClient, videos_dir: str = 'videos', part_concurrency=10,
                 speed_limit: Union[float, int] = None, progress=None):
        """
        Base Async http Content-Range Downloader

        :param client:
        :param videos_dir:
        :param part_concurrency:
        :param speed_limit:
        :param progress:
        """
        super(BaseDownloaderPart, self).__init__(client, videos_dir, speed_limit=speed_limit, progress=progress)
        self.part_concurrency = part_concurrency

    async def _content_length(self, urls: List[Union[str, httpx.URL]]) -> int:
        # use GET instead of HEAD due to 404 bug https://github.com/HFrost0/bilix/issues/16
        res = await req_retry(self.client, urls[0], follow_redirects=True, headers={'Range': 'bytes=0-1'})
        total = int(res.headers['Content-Range'].split('/')[-1])
        # change origin url to redirected position to avoid twice redirect
        if res.history:
            urls[0] = res.url
        return total

    async def get_media(self, url_or_urls: Union[str, Iterable[str]],
                        media_name: str, task_id=None, hierarchy: str = '', retry: int = 5) -> str:
        """

        :param url_or_urls: media url or urls with backups
        :param media_name:
        :param task_id: if not provided, a new progress task will be created
        :param hierarchy:
        :param retry: retry times
        :return: downloaded file path
        """
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        file_path = f'{file_dir}/{media_name}'
        urls = [url_or_urls] if isinstance(url_or_urls, str) else [url for url in url_or_urls]
        if os.path.exists(file_path):
            logger.info(f'[green]已存在[/green] {media_name}')
            return file_path
        total = await self._content_length(urls)
        if task_id is not None:
            await self.progress.update(task_id, total=self.progress.tasks[task_id].total + total, visible=True)
        else:
            task_id = await self.progress.add_task(description=media_name[:30], total=total, visible=True)
        part_length = total // self.part_concurrency
        cors = []
        part_names = []
        for i in range(self.part_concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < self.part_concurrency - 1 else total - 1
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cors.append(self._get_media_part(urls, part_name, task_id, hierarchy=hierarchy, retry=retry))
        file_list = await asyncio.gather(*cors)
        await merge_files(file_list, new_name=file_path)
        if self.progress.tasks[task_id].finished:
            await self.progress.update(task_id, visible=False)
            logger.info(f"[cyan]已完成[/cyan] {media_name}")
        return file_path

    async def _get_media_part(self, urls: List[Union[str, httpx.URL]],
                              part_name, task_id, times=0, hierarchy: str = '', retry: int = 5):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if times > retry:
            raise Exception(f'STREAM 超过重试次数 {part_name}')
        start, end = map(int, part_name.split('-')[-2:])
        file_path = f'{file_dir}/{part_name}'
        if os.path.exists(file_path):
            downloaded = os.path.getsize(file_path)
            start += downloaded
            if times == 0:
                await self.progress.update(task_id, advance=downloaded)
        if start > end:
            return file_path  # skip already finished
        url_idx = random.randint(0, len(urls) - 1)
        try:
            async with self.client.stream("GET", urls[url_idx], follow_redirects=True,
                                          headers={'Range': f'bytes={start}-{end}'}) as r, self._stream_context(times):
                r.raise_for_status()
                if r.history:  # avoid twice redirect
                    urls[url_idx] = r.url
                async with aiofiles.open(file_path, 'ab') as f:
                    async for chunk in r.aiter_bytes(chunk_size=self.chunk_size):
                        await f.write(chunk)
                        await self.progress.update(task_id, advance=len(chunk))
        except (httpx.TransportError, httpx.HTTPStatusError):
            await self._get_media_part(urls, part_name, task_id, times=times + 1, hierarchy=hierarchy)
        return file_path


@Handler(name="Part")
def handle(**kwargs):
    key = kwargs['key']
    if m := re.fullmatch(r'http.+(?P<suffix>mp4|m4s|m4a)(\?.*)?', key):
        videos_dir = kwargs['videos_dir']
        part_concurrency = kwargs['part_concurrency']
        speed_limit = kwargs['speed_limit']
        method = kwargs['method']
        d = BaseDownloaderPart(httpx.AsyncClient(http2=True), videos_dir=videos_dir, part_concurrency=part_concurrency,
                               speed_limit=speed_limit)
        if method == 'get_video' or method == 'v':
            cor = d.get_media(key, f"unnamed.{m.group('suffix')}")
            return d, cor
        raise HandleMethodError(d, method)
