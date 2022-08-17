import asyncio
import httpx
from typing import Sequence

import bilix.api.yhdmp as api
from bilix.utils import legal_title, cors_slice
from bilix.download.base_downloader_m3u8 import BaseDownLoaderM3u8


class DownloaderYhdmp(BaseDownLoaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "Referer": "https://www.yhdmp.cc"}, http2=True)
        super(DownloaderYhdmp, self).__init__(client, videos_dir, video_concurrency, part_concurrency)

    async def get_series(self, url: str, p_range: Sequence[int] = None, hierarchy=True):
        video_info = await api.get_video_info(url)
        ep_idx = video_info.ep_idx
        play_idx = video_info.play_idx
        title = video_info.title
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, video_info.title)

        # no need to reuse get_video since we only need m3u8_url
        async def get_video(name):
            m3u8_url = await api.get_m3u8_url(url)
            await self.get_m3u8_video(m3u8_url=m3u8_url, name=name, hierarchy=hierarchy if hierarchy else '')

        cors = []
        for idx, (sub_title, url) in enumerate(video_info.play_info[play_idx]):
            if ep_idx == idx:
                cors.append(self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=legal_title(title, sub_title),
                                                hierarchy=hierarchy if hierarchy else ''))
            else:
                cors.append(get_video(legal_title(title, sub_title)))
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, hierarchy: str = ''):
        video_info = await api.get_video_info(url, self.client)
        name = legal_title(video_info.title, video_info.sub_title)
        await self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=name, hierarchy=hierarchy)


if __name__ == '__main__':
    async def main():
        d = DownloaderYhdmp(video_concurrency=1)
        await d.get_series("https://www.yhdmp.cc/vp/22224-1-0.html", p_range=[1, 1])
        await d.aclose()


    asyncio.run(main())
