import asyncio
import httpx

import bilix.api.cctv as api
from bilix.api.cctv import _dft_headers
from bilix.assign import Handler
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderCctv(BaseDownloaderM3u8):
    def __init__(self, videos_dir='videos', video_concurrency=3, part_concurrency=10):
        client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        super(DownloaderCctv, self).__init__(client, videos_dir, video_concurrency, part_concurrency)

    async def get_series(self, url: str, quality=0):
        pid, vida = await api.get_id(url, self.client)
        if vida is None:  # 单个视频
            await self.get_video(pid, quality=quality)
        else:  # 剧集
            pids = await api.get_list_info(vida, self.client)
            await asyncio.gather(*[self.get_video(pid, quality=quality) for pid in pids])

    async def get_video(self, url_or_pid: str, quality=0):
        if url_or_pid.startswith('http'):
            pid, _ = await api.get_id(url_or_pid)
        else:
            pid = url_or_pid
        title, m3u8_urls = await api.get_media_info(pid, self.client)
        m3u8_url = m3u8_urls[min(quality, len(m3u8_urls) - 1)]
        await self.get_m3u8_video(m3u8_url, title)


@Handler(name='CCTV')
def handle(**kwargs):
    key = kwargs['key']
    if 'cctv' in key:
        video_con = kwargs['video_concurrency']
        part_con = kwargs['part_concurrency']
        videos_dir = kwargs['videos_dir']
        quality = kwargs['quality']
        method = kwargs['method']
        d = DownloaderCctv(videos_dir=videos_dir, video_concurrency=video_con, part_concurrency=part_con)
        if method == 's' or method == 'get_series':
            cor = d.get_series(key, quality=quality)
        elif method == 'v' or method == 'get_video':
            cor = d.get_video(key, quality=quality)
        else:
            raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
        return d, cor


if __name__ == '__main__':
    async def main():
        async with DownloaderCctv() as d:
            await d.get_video(
                'https://tv.cctv.com/2022/07/04/VIDEnMUCprEHmwTAt8RTT8Bo220704.shtml'
            )


    asyncio.run(main())
