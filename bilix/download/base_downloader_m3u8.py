import asyncio
import logging
import uuid
from pathlib import Path, PurePath
from typing import Tuple, Union, Annotated
from urllib.parse import urlparse
import aiofiles
import httpx
import os
import m3u8
from Crypto.Cipher import AES
from m3u8 import Segment
from bilix.download.base_downloader import BaseDownloader
from bilix.download.utils import path_check, parse_speed_str, str2path, parse_time_range, merge_files
from bilix.progress.abc import Progress
from bilix import ffmpeg
from .utils import req_retry

__all__ = ['BaseDownloaderM3u8']


class BaseDownloaderM3u8(BaseDownloader):
    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: logging.Logger = None,
            # unique params
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
    ):
        """Base Async http m3u8 Downloader
        :param part_concurrency: max concurrency of seg download
        :param video_concurrency: max concurrency of video download
        """
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

    async def to_invariant_m3u8(self, m3u8_url: str) -> m3u8.M3U8:
        res = await req_retry(self.client, m3u8_url, follow_redirects=True)
        m3u8_info = m3u8.loads(res.text)
        if not m3u8_info.base_uri:
            m3u8_info.base_uri = m3u8_url
        if m3u8_info.is_variant:
            self.logger.debug(f"m3u8 is variant, use first playlist: {m3u8_info.playlists[0].absolute_uri}")
            return await self.to_invariant_m3u8(m3u8_info.playlists[0].absolute_uri)
        return m3u8_info

    async def get_m3u8_video(self, m3u8_url: str, path: Annotated[Path, str2path] = Path('.'),
                             time_range: Annotated[Tuple[int, int], parse_time_range] = None) -> Path:
        """
        download video from m3u8 url
        :cli short: m3u8
        :param m3u8_url: m3u8 url, can be invariant or variant
        :param path: file path or file dir, if dir, filename will be set according to m3u8_url
        :param time_range: tuple (start_time, end_time) or str like 00:01:00-00:01:05 (hour:minute:second)
        :return: downloaded file path
        """
        if path.is_dir():
            path = (path / PurePath(urlparse(m3u8_url).path).stem).with_suffix('.mp4')
        if time_range:
            path = path.with_stem(f"{path.stem}-{time_range[0]}-{time_range[1]}")
        exist, path = path_check(path)
        if exist:
            self.logger.exist(path.name)
            return path
        async with self.v_sema:
            task_id = await self.progress.add_task(total=None, description=path.name)
            m3u8_info = await self.to_invariant_m3u8(m3u8_url)
            cors = []
            p_sema = asyncio.Semaphore(self.part_concurrency)
            total_time = 0
            if time_range:
                current_time = 0
                start_time, end_time = time_range
                inside = False
            else:
                inside = True
            for idx, seg in enumerate(m3u8_info.segments):
                if time_range:
                    current_time += seg.duration
                    if not inside and current_time > start_time:
                        inside = True
                        s = seg.duration - (current_time - start_time)
                    elif current_time > end_time:
                        break
                if inside:
                    total_time += seg.duration
                    # https://stackoverflow.com/questions/50628791/decrypt-m3u8-playlist-encrypted-with-aes-128-without-iv
                    if seg.key and seg.key.iv is None:
                        seg.custom_parser_values['iv'] = idx.to_bytes(16, 'big')
                    cors.append(self._get_seg(seg, path.with_name(f"{path.stem}-{idx}.ts"), task_id, p_sema))
            if len(cors) == 0 and time_range:
                raise Exception(f"time range <{start_time}-{end_time}> invalid for <{path.name}>")
            if init_sec := m3u8_info.segments[0].init_section:
                async def _get_init():
                    r = await req_retry(self.client, init_sec.absolute_uri)
                    async with aiofiles.open(fn := path.with_name(f"{path.stem}-init"), 'wb') as f:
                        await f.write(r.content)
                        return fn

                cors.insert(0, _get_init())
                merge_fn = merge_files
            else:
                merge_fn = ffmpeg.concat
            await self.progress.update(task_id, total_time=total_time)
            file_list = await asyncio.gather(*cors)

        await merge_fn(file_list, path)
        if time_range:
            path_tmp = path.with_stem(str(uuid.uuid4()))
            # to save key frame, use 0 as start time instead of s, clip will be a little longer than expected
            await ffmpeg.time_range_clip(path, 0, end_time - start_time + s, path_tmp)
            os.rename(path_tmp, path)
        self.logger.done(path.name)
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
            for times in range(1 + self.stream_retry):
                content = bytearray()
                try:
                    async with self.client.stream("GET", seg_url,
                                                  follow_redirects=True) as r, self._stream_context(times):
                        r.raise_for_status()
                        # pre-update total if content-length is provided and first time to get content
                        if 'content-length' in r.headers and not content:
                            await self._update_task_total(
                                task_id, time_part=seg.duration, update_size=int(r.headers['content-length']))
                        async for chunk in r.aiter_bytes(chunk_size=self._chunk_size):
                            content.extend(chunk)
                            await self.progress.update(task_id, advance=len(chunk))
                            await self._check_speed(len(chunk))
                    if 'content-length' not in r.headers:  # after-update total if content-length is not provided
                        await self._update_task_total(task_id, time_part=seg.duration, update_size=len(content))
                    break
                except (httpx.HTTPStatusError, httpx.TransportError):
                    continue
            else:
                raise Exception(f"STREAM max retry {seg_url}")
        content = self._after_seg(seg, content)
        # in case encrypted
        if seg.key:
            content = await self._decrypt(seg, content)
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
        return path

    def _after_seg(self, seg: Segment, content: bytearray) -> bytearray:
        """hook for subclass to modify segment content, happened before decrypt"""
        return content
