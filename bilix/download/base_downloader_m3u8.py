import asyncio
import re
import anyio
import httpx
import os
import m3u8
from Crypto.Cipher import AES
from m3u8 import Segment
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn

from bilix.download.base_downloader import BaseDownloader
from bilix.log import logger
from bilix.utils import req_retry


class BaseDownLoaderM3u8(BaseDownloader):
    # todo no two live progress
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
        TextColumn("ETA"),
        TimeRemainingColumn(),
        transient=True)

    def __init__(self, client: httpx.AsyncClient, videos_dir="videos", video_concurrency=3, part_concurrency=20):
        super(BaseDownLoaderM3u8, self).__init__(client, videos_dir)
        self.v_sema = asyncio.Semaphore(video_concurrency)
        self.part_con = part_concurrency
        self.decrypt_cache = {}

    async def _decrypt(self, key: m3u8.Key, content: bytes):
        async def get_key():
            key_bytes = (await req_retry(self.client, uri)).content
            iv = bytes.fromhex(key.iv.replace('0x', ''))
            return AES.new(key_bytes, AES.MODE_CBC, iv)

        uri = key.absolute_uri
        if uri not in self.decrypt_cache:
            self.decrypt_cache[uri] = asyncio.ensure_future(get_key())
            self.decrypt_cache[uri] = await self.decrypt_cache[uri]
        elif asyncio.isfuture(self.decrypt_cache[uri]):
            await self.decrypt_cache[uri]
        cipher = self.decrypt_cache[uri]
        return cipher.decrypt(content)

    async def get_m3u8_video(self, m3u8_url: str, name: str, hierarchy: str = ''):
        base_path = f"{self.videos_dir}/{hierarchy}" if hierarchy else self.videos_dir
        if os.path.exists(f"{base_path}/{name}.ts"):
            logger.info(f"[green]已存在[/green] {name}.ts")
            return f"{base_path}/{name}.ts"
        await self.v_sema.acquire()
        res = await req_retry(self.client, m3u8_url)
        m3u8_info = m3u8.loads(res.text)
        if not m3u8_info.base_uri:
            base_uri = re.search(r"(.*)/[^/]+m3u8", m3u8_url).groups()[0]
            m3u8_info.base_uri = base_uri
        cors = []
        p_sema = asyncio.Semaphore(self.part_con)
        task_id = self.progress.add_task(
            description=name if len(name) < 33 else f'{name[:15]}...{name[-15:]}', visible=False)
        total_time = 0
        for idx, seg in enumerate(m3u8_info.segments):
            total_time += seg.duration
            cors.append(self._get_ts(seg, f"{name}-{idx}.ts", task_id, p_sema, hierarchy))
        self.progress.update(task_id, total=total_time, visible=True)
        await asyncio.gather(*cors)
        self.v_sema.release()
        # merge
        async with await anyio.open_file(f"{base_path}/{name}-0.ts", 'ab') as f:
            for idx in range(1, len(m3u8_info.segments)):
                async with await anyio.open_file(f"{base_path}/{name}-{idx}.ts", 'rb') as fa:
                    await f.write(await fa.read())
                    os.remove(f"{base_path}/{name}-{idx}.ts")
        os.rename(f"{base_path}/{name}-0.ts", f"{base_path}/{name}.ts")
        logger.info(f"[cyan]已完成[/cyan] {name}.ts")
        self.progress.update(task_id, visible=False)
        return f"{base_path}/{name}.ts"

    async def _get_ts(self, seg: Segment, name, task_id, p_sema: asyncio.Semaphore, hierarchy: str = ''):
        ts_url = seg.absolute_uri
        base_path = f"{self.videos_dir}/{hierarchy}" if hierarchy else self.videos_dir
        file_path = f"{base_path}/{name}"
        if not os.path.exists(file_path):
            async with p_sema:
                res = await req_retry(self.client, ts_url)
            content = res.content
            # in case .png
            if not ts_url.endswith('.ts'):
                content = content[content.find(b'\x47\x40'):]
            # in case encrypted
            if seg.key:
                content = await self._decrypt(seg.key, content)
            async with await anyio.open_file(file_path, 'wb') as f:
                await f.write(content)
        self.progress.update(task_id, advance=seg.duration)
        return file_path
