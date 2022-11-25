import asyncio
from typing import Union
import httpx

import bilix.api.cctv as api
from bilix.api.cctv import _dft_headers
from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8


class DownloaderCctv(BaseDownloaderM3u8):
    def __init__(self, videos_dir='videos', video_concurrency=3, part_concurrency=10,
                 speed_limit: Union[float, int] = None, progress=None):
        client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        super(DownloaderCctv, self).__init__(client, videos_dir, video_concurrency, part_concurrency,
                                             speed_limit=speed_limit, progress=progress)

    async def get_series(self, url: str, quality=0, hierarchy=True):
        pid, vide, vida = await api.get_id(self.client, url)
        if vida is None:  # 单个视频
            await self.get_video(pid, quality=quality)
        else:  # 剧集
            title, pids = await api.get_series_info(self.client, vide, vida)
            if hierarchy:
                hierarchy = self._make_hierarchy_dir(hierarchy, title)
            await asyncio.gather(*[self.get_video(pid, quality, hierarchy if hierarchy else '') for pid in pids])

    async def get_video(self, url_or_pid: str, quality=0, hierarchy=''):
        if url_or_pid.startswith('http'):
            pid, _, _ = await api.get_id(self.client, url_or_pid)
        else:
            pid = url_or_pid
        title, m3u8_urls = await api.get_media_info(self.client, pid)
        m3u8_url = m3u8_urls[min(quality, len(m3u8_urls) - 1)]
        file_path = await self.get_m3u8_video(m3u8_url, title, hierarchy)
        return file_path


@Handler(name='CCTV')
def handle(**kwargs):
    key = kwargs['key']
    if 'cctv' in key:
        video_con = kwargs['video_concurrency']
        part_con = kwargs['part_concurrency']
        speed_limit = kwargs['speed_limit']
        videos_dir = kwargs['videos_dir']
        quality = kwargs['quality']
        method = kwargs['method']
        d = DownloaderCctv(videos_dir=videos_dir, video_concurrency=video_con, part_concurrency=part_con,
                           speed_limit=speed_limit)
        if method == 's' or method == 'get_series':
            cor = d.get_series(key, quality=quality)
        elif method == 'v' or method == 'get_video':
            cor = d.get_video(key, quality=quality)
        else:
            raise HandleMethodError(d, method)
        return d, cor


if __name__ == '__main__':
    async def main():
        async with DownloaderCctv() as d:
            await d.get_series(
                'https://tv.cctv.com/2012/05/02/VIDE1355968282695723.shtml?spm=C55853485115.P6UrzpiudtDc.0.0'
            )


    asyncio.run(main())
