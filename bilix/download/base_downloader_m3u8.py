import asyncio
import re
from typing import Union
import aiofiles
import httpx
import os
import m3u8
from Crypto.Cipher import AES
from m3u8 import Segment

from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader import BaseDownloader
from bilix.log import logger
from bilix.utils import req_retry, merge_files


class BaseDownloaderM3u8(BaseDownloader):
    def __init__(self, client: httpx.AsyncClient, videos_dir="videos", video_concurrency=3, part_concurrency=10,
                 speed_limit: Union[float, int] = None, progress=None):
        """
        Base async m3u8 Downloader

        :param client:
        :param videos_dir:
        :param video_concurrency:
        :param part_concurrency:
        :param speed_limit:
        :param progress:
        """
        super(BaseDownloaderM3u8, self).__init__(client, videos_dir, speed_limit=speed_limit, progress=progress)
        self.v_sema = asyncio.Semaphore(video_concurrency)
        self.part_con = part_concurrency
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

    async def get_m3u8_video(self, m3u8_url: str, name: str, hierarchy: str = '', retry: int = 5) -> str:
        """
        download

        :param m3u8_url:
        :param name:
        :param hierarchy:
        :param retry:
        :return: downloaded file path
        """
        base_path = f"{self.videos_dir}/{hierarchy}" if hierarchy else self.videos_dir
        file_path = f"{base_path}/{name}.ts"
        if os.path.exists(file_path):
            logger.info(f"[green]已存在[/green] {name}.ts")
            return file_path
        await self.v_sema.acquire()
        res = await req_retry(self.client, m3u8_url)
        m3u8_info = m3u8.loads(res.text)
        if not m3u8_info.base_uri:
            base_uri = re.search(r"(.*)/[^/]*m3u8", m3u8_url).groups()[0]
            m3u8_info.base_uri = base_uri
        cors = []
        p_sema = asyncio.Semaphore(self.part_con)
        task_id = await self.progress.add_task(  # invisible at first and create task id for _get_ts
            description=name if len(name) < 33 else f'{name[:15]}...{name[-15:]}', visible=False)
        total_time = 0
        for idx, seg in enumerate(m3u8_info.segments):
            total_time += seg.duration
            # https://stackoverflow.com/questions/50628791/decrypt-m3u8-playlist-encrypted-with-aes-128-without-iv
            if seg.key and seg.key.iv is None:
                seg.custom_parser_values['iv'] = idx.to_bytes(16, 'big')
            cors.append(self._get_ts(seg, f"{name}-{idx}.ts", task_id, p_sema, hierarchy, retry=retry))
        await self.progress.update(task_id, total=0, total_time=total_time)
        file_list = await asyncio.gather(*cors)
        self.v_sema.release()
        await merge_files(file_list, new_name=file_path)
        logger.info(f"[cyan]已完成[/cyan] {name}.ts")
        await self.progress.update(task_id, visible=False)
        return file_path

    async def _update_task_total(self, task_id, time_part: float, update_size: int):
        task = self.progress.tasks[task_id]
        if not self.progress.tasks[task_id].visible:
            confirmed_t = time_part
            confirmed_b = update_size
            await self.progress.update(task_id, visible=True)
        else:
            confirmed_t = time_part + task.fields['confirmed_t']
            confirmed_b = update_size + task.fields['confirmed_b']
        predicted_total = confirmed_b / confirmed_t * task.fields['total_time']
        await self.progress.update(task_id, total=predicted_total, confirmed_t=confirmed_t, confirmed_b=confirmed_b)

    async def _get_ts(self, seg: Segment, name, task_id, p_sema: asyncio.Semaphore, hierarchy: str = '',
                      retry: int = 5) -> str:
        ts_url = seg.absolute_uri
        base_path = f"{self.videos_dir}/{hierarchy}" if hierarchy else self.videos_dir
        file_path = f"{base_path}/{name}"
        if os.path.exists(file_path):
            downloaded = os.path.getsize(file_path)
            await self._update_task_total(task_id, time_part=seg.duration, update_size=downloaded)
            await self.progress.update(task_id, advance=downloaded)
            return file_path

        async with p_sema:
            content = None
            for times in range(1 + retry):
                content = bytearray()
                try:
                    async with self.client.stream("GET", ts_url) as r, self._stream_context(times):
                        r.raise_for_status()
                        await self._update_task_total(
                            task_id, time_part=seg.duration, update_size=int(r.headers['content-length']))
                        async for chunk in r.aiter_bytes(chunk_size=self.chunk_size):
                            content.extend(chunk)
                            await self.progress.update(task_id, advance=len(chunk))
                    break
                except (httpx.HTTPStatusError, httpx.TransportError) as e:
                    continue
            else:
                raise Exception(f"STREAM 超过重复次数 {ts_url}")
        # in case .png
        if re.fullmatch(r'.*\.png', ts_url):
            _, _, content = content.partition(b'\x47\x40')
        # in case encrypted
        if seg.key:
            content = await self._decrypt(seg, content)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        return file_path


@Handler(name="m3u8")
def handle(**kwargs):
    key = kwargs['key']
    if re.fullmatch(r"http.+m3u8(\?.*)?", key):
        videos_dir = kwargs['videos_dir']
        part_concurrency = kwargs['part_concurrency']
        speed_limit = kwargs['speed_limit']
        method = kwargs['method']
        d = BaseDownloaderM3u8(httpx.AsyncClient(), videos_dir=videos_dir, part_concurrency=part_concurrency,
                               speed_limit=speed_limit)
        if method == 'get_video' or method == 'v':
            cor = d.get_m3u8_video(key, "unnamed")
            return d, cor
        raise HandleMethodError(d, method)
