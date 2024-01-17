import asyncio
from pathlib import Path, PurePath
from typing import Union, List, Iterable, Tuple
from urllib.parse import urlparse
import aiofiles
import httpx
import uuid
import random
import os
from email.message import Message
from pymp4.parser import Box
from bilix.download.base_downloader import BaseDownloader
from bilix.download.utils import path_check, merge_files
from bilix import ffmpeg
from .utils import req_retry

__all__ = ['BaseDownloaderPart']


class BaseDownloaderPart(BaseDownloader):
    """Base Async http Content-Range Downloader"""

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int, None] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            # unique params
            part_concurrency: int = 10,
    ):
        super(BaseDownloaderPart, self).__init__(
            client=client,
            browser=browser,
            stream_retry=stream_retry,
            speed_limit=speed_limit,
            progress=progress,
            logger=logger
        )
        self.part_concurrency = part_concurrency

    async def _pre_req(self, urls: List[str]) -> Tuple[int, str]:
        # use GET instead of HEAD due to 404 bug https://github.com/HFrost0/bilix/issues/16
        res = await req_retry(self.client, urls[0], follow_redirects=True, headers={'Range': 'bytes=0-1'})
        total = int(res.headers['Content-Range'].split('/')[-1])
        # get filename
        if content_disposition := res.headers.get('Content-Disposition', None):
            m = Message()
            m['content-type'] = content_disposition
            filename = m.get_param('filename', '')
        else:
            filename = ''
        # change origin url to redirected position to avoid twice redirect
        if res.history:
            urls[0] = str(res.url)
        return total, filename

    async def get_media_clip(
            self,
            url_or_urls: Union[str, Iterable[str]],
            path: Union[Path, str],
            time_range: Tuple[int, int],
            init_range: str,
            seg_range: str,
            get_s: asyncio.Future = None,
            set_s: asyncio.Future = None,
            task_id=None,
    ):
        """

        :param url_or_urls:
        :param path:
        :param time_range: (start_time, end_time)
        :param init_range: xxx-xxx
        :param seg_range: xxx-xxx
        :param get_s:
        :param set_s:
        :param task_id:
        :return:
        """
        upper = task_id is not None and self.progress.tasks[task_id].fields.get('upper', None)
        exist, path = path_check(path)
        if exist:
            if not upper:
                self.logger.info(f'[green]已存在[/green] {path.name}')
            return path

        urls = [url_or_urls] if isinstance(url_or_urls, str) else [url for url in url_or_urls]
        init_start, init_end = map(int, init_range.split('-'))
        seg_start, seg_end = map(int, seg_range.split('-'))
        res = await req_retry(self.client, urls[0], follow_redirects=True,
                              headers={'Range': f'bytes={seg_start}-{seg_end}'})
        container = Box.parse(res.content)
        assert container.type == b'sidx'
        if get_s:
            start_time = await get_s
            end_time = time_range[1]
        else:
            start_time, end_time = time_range
        pre_time, pre_byte = 0, seg_end + 1
        inside = False
        parts = [(init_start, init_end)]
        total = init_end - init_start + 1
        s = 0
        for idx, ref in enumerate(container.references):
            if ref.reference_type != "MEDIA":
                self.logger.debug("not a media", ref)
                continue
            seg_duration = ref.segment_duration / container.timescale
            if not inside and start_time < pre_time + seg_duration:
                s = start_time - pre_time
                inside = True
            if inside and end_time < pre_time:
                break
            if inside:
                total += ref.referenced_size
                parts.append((pre_byte, pre_byte + ref.referenced_size - 1))
            pre_time += seg_duration
            pre_byte += ref.referenced_size
        if len(parts) == 1:
            raise Exception(f"time range <{start_time}-{end_time}> invalid for <{path.name}>")
        if set_s:
            set_s.set_result(start_time - s)
        if task_id is not None:
            await self.progress.update(
                task_id,
                total=self.progress.tasks[task_id].total + total if self.progress.tasks[task_id].total else total)
        else:
            task_id = await self.progress.add_task(description=path.name, total=total)
        p_sema = asyncio.Semaphore(self.part_concurrency)

        async def get_seg(part_range: Tuple[int, int]):
            async with p_sema:
                return await self._get_file_part(urls, path=path, part_range=part_range, task_id=task_id)

        file_list = await asyncio.gather(*[get_seg(part_range) for part_range in parts])
        path_tmp = path.with_name(str(uuid.uuid4()))
        await merge_files(file_list, path_tmp)
        if set_s:
            await ffmpeg.time_range_clip(path_tmp, start=0, t=end_time - start_time + s, output_path=path)
        else:
            await ffmpeg.time_range_clip(path_tmp, start=s, t=end_time - start_time, output_path=path)
        if not upper:  # no upstream task
            await self.progress.update(task_id, visible=False)
            self.logger.info(f"[cyan]已完成[/cyan] {path.name}")
        return path

    async def get_file(self, url_or_urls: Union[str, Iterable[str]], path: Union[Path, str], task_id=None) -> Path:
        """
        download file by http content-range
        :cli: short: f
        :param url_or_urls: file url or urls with backups
        :param path: file path or dir path, if dir path, filename will be extracted from url
        :param task_id: if not provided, a new progress task will be created
        :return: downloaded file path
        """
        urls = [url_or_urls] if isinstance(url_or_urls, str) else [url for url in url_or_urls]
        upper = task_id is not None and self.progress.tasks[task_id].fields.get('upper', None)

        if not path.is_dir():
            exist, path = path_check(path)
            if exist:
                if not upper:
                    self.logger.info(f'[green]已存在[/green] {path.name}')
                return path

        total, req_filename = await self._pre_req(urls)

        if path.is_dir():
            file_name = req_filename if req_filename else PurePath(urlparse(urls[0]).path).name
            path /= file_name
            exist, path = path_check(path)
            if exist:
                if not upper:
                    self.logger.info(f'[green]已存在[/green] {path.name}')
                return path

        if task_id is not None:
            await self.progress.update(
                task_id,
                total=self.progress.tasks[task_id].total + total if self.progress.tasks[task_id].total else total)
        else:
            task_id = await self.progress.add_task(description=path.name, total=total)
        part_length = total // self.part_concurrency
        cors = []
        for i in range(self.part_concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < self.part_concurrency - 1 else total - 1
            cors.append(self._get_file_part(urls, path=path, part_range=(start, end), task_id=task_id))
        file_list = await asyncio.gather(*cors)
        await merge_files(file_list, new_path=path)
        if not upper:
            await self.progress.update(task_id, visible=False)
            self.logger.info(f"[cyan]已完成[/cyan] {path.name}")
        return path

    async def _get_file_part(self, urls: List[str], path: Path, part_range: Tuple[int, int],
                             task_id) -> Path:
        start, end = part_range
        part_path = path.with_name(f'{path.name}.{part_range[0]}-{part_range[1]}')
        exist, part_path = path_check(part_path)
        if exist:
            downloaded = os.path.getsize(part_path)
            start += downloaded
            await self.progress.update(task_id, advance=downloaded)
        if start > end:
            return part_path  # skip already finished
        url_idx = random.randint(0, len(urls) - 1)

        for times in range(1 + self.stream_retry):
            try:
                async with \
                        self.client.stream("GET", urls[url_idx], follow_redirects=True,
                                           headers={'Range': f'bytes={start}-{end}'}) as r, \
                        self._stream_context(times), \
                        aiofiles.open(part_path, 'ab') as f:
                    r.raise_for_status()
                    if r.history:  # avoid twice redirect
                        urls[url_idx] = r.url
                    async for chunk in r.aiter_bytes(chunk_size=self.chunk_size):
                        await f.write(chunk)
                        start += len(chunk)
                        await self.progress.update(task_id, advance=len(chunk))
                        await self._check_speed(len(chunk))
                break
            except (httpx.HTTPStatusError, httpx.TransportError):
                continue
        else:
            raise Exception(f"STREAM 超过重复次数 {part_path.name}")
        return part_path
