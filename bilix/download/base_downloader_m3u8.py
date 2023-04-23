import asyncio
import re
from pathlib import Path
from typing import Union, Tuple
import aiofiles
import httpx
import os
import m3u8
from Crypto.Cipher import AES
from m3u8 import Segment
from bilix.download.base_downloader import BaseDownloader
from bilix.download.utils import path_check, merge_files
from .utils import req_retry

__all__ = ['BaseDownloaderM3u8']


class BaseDownloaderM3u8(BaseDownloader):
    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            # unique params
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            **kwargs
    ):
        """Base async m3u8 Downloader"""
        super(BaseDownloaderM3u8, self).__init__(
            client=client,
            browser=browser,
            stream_retry=stream_retry,
            speed_limit=speed_limit,
            progress=progress,
            logger=logger
        )
        self.v_sema = asyncio.Semaphore(video_concurrency) if isinstance(video_concurrency, int) else video_concurrency
        self.part_concurrency = part_concurrency
        self.decrypt_cache = {}

    async def _decrypt(self, seg: m3u8.Segment, content: bytearray):
        async def get_key():
            key_bytes = (await req_retry(self.client, uri)).content
            iv = bytes.fromhex(seg.key.iv.replace('0x', '')) if seg.key.iv is not None else \
                seg.custom_parser_values['iv']
            return AES.new(key_bytes, AES.MODE_CBC, iv)

        uri = seg.key.absolute_uri
        if uri not in self.decrypt_cache:
            self.decrypt_cache[uri] = asyncio.ensure_future(get_key())
            self.decrypt_cache[uri] = await self.decrypt_cache[uri]
        elif asyncio.isfuture(self.decrypt_cache[uri]):
            await self.decrypt_cache[uri]
        cipher = self.decrypt_cache[uri]
        return cipher.decrypt(content)

    async def get_m3u8_video(self, m3u8_url: str, path: Path = Path("./test.ts")) -> Path:
        """
        download

        :param m3u8_url:
        :param path: file path
        :return: downloaded file path
        """
        exist, path = path_check(path)
        if exist:
            self.logger.info(f"[green]已存在[/green] {path.name}")
            return path
        async with self.v_sema:
            task_id = await self.progress.add_task(total=None, description=path.name)
            res = await req_retry(self.client, m3u8_url, follow_redirects=True)
            m3u8_info = m3u8.loads(res.text)
            if not m3u8_info.base_uri:
                base_uri = re.search(r"(.*)/[^/]*m3u8", m3u8_url).groups()[0]
                m3u8_info.base_uri = base_uri
            cors = []
            p_sema = asyncio.Semaphore(self.part_concurrency)
            total_time = 0
            for idx, seg in enumerate(m3u8_info.segments):
                total_time += seg.duration
                # https://stackoverflow.com/questions/50628791/decrypt-m3u8-playlist-encrypted-with-aes-128-without-iv
                if seg.key and seg.key.iv is None:
                    seg.custom_parser_values['iv'] = idx.to_bytes(16, 'big')
                cors.append(self._get_seg(seg, path.with_name(f"{path.stem}-{idx}.ts"), task_id, p_sema))
            await self.progress.update(task_id, total_time=total_time)
            file_list = await asyncio.gather(*cors)
        # todo ffmpeg merge
        await merge_files(file_list, new_path=path)
        self.logger.info(f"[cyan]已完成[/cyan] {path.name}")
        await self.progress.update(task_id, visible=False)
        return path

    async def _update_task_total(self, task_id, time_part: float, update_size: int):
        task = self.progress.tasks[task_id]
        if task.total is None:
            confirmed_t = time_part
            confirmed_b = update_size
        else:
            confirmed_t = time_part + task.fields['confirmed_t']
            confirmed_b = update_size + task.fields['confirmed_b']
        predicted_total = task.fields['total_time'] * confirmed_b / confirmed_t
        await self.progress.update(task_id, total=predicted_total, confirmed_t=confirmed_t, confirmed_b=confirmed_b)

    async def _get_seg(self, seg: Segment, path: Path, task_id, p_sema: asyncio.Semaphore) -> Path:
        exists, path = path_check(path)
        if exists:
            downloaded = os.path.getsize(path)
            await self._update_task_total(task_id, time_part=seg.duration, update_size=downloaded)
            await self.progress.update(task_id, advance=downloaded)
            return path
        seg_url = seg.absolute_uri
        async with p_sema:
            content = None
            for times in range(1 + self.stream_retry):
                content = bytearray()
                try:
                    async with self.client.stream("GET", seg_url,
                                                  follow_redirects=True) as r, self._stream_context(times):
                        r.raise_for_status()
                        await self._update_task_total(
                            task_id, time_part=seg.duration, update_size=int(r.headers['content-length']))
                        async for chunk in r.aiter_bytes(chunk_size=self.chunk_size):
                            content.extend(chunk)
                            await self.progress.update(task_id, advance=len(chunk))
                            await self._check_speed(len(chunk))
                    break
                except (httpx.HTTPStatusError, httpx.TransportError):
                    continue
            else:
                raise Exception(f"STREAM 超过重复次数 {seg_url}")
        # in case .png
        if re.fullmatch(r'.*\.png', seg_url):
            _, _, content = content.partition(b'\x47\x40')
        # in case encrypted
        if seg.key:
            content = await self._decrypt(seg, content)
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
        return path

    @classmethod
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        if method == 'm3u8':
            d = cls(**options)
            cors = []
            for i, key in enumerate(keys):
                cors.append(d.get_m3u8_video(key, options['path'] / f"{i}.ts"))
            return d, asyncio.gather(*cors)
