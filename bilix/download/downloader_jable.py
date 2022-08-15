import asyncio
import httpx
import bilix.api.jable as api
from bilix.download.base_downloader_m3u8 import BaseDownLoaderM3u8


class DownloaderJable(BaseDownLoaderM3u8):
    def __init__(self, videos_dir: str = "videos", video_concurrency: int = 3, part_concurrency: int = 10):
        client = httpx.AsyncClient(
            headers={'user-agent': 'PostmanRuntime/7.29.0', "referer": "https://jable.tv"}, http2=False)
        super(DownloaderJable, self).__init__(client, videos_dir, video_concurrency, part_concurrency)

    async def get_video(self, url: str, image=True, hierarchy=True):
        video_info = await api.get_video_info(url, self.client)
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, f"{video_info.avid} {video_info.model_name}")
        cors = [self.get_m3u8_video(m3u8_url=video_info.m3u8_url, name=video_info.title,
                                    hierarchy=hierarchy if hierarchy else '')]
        if image:
            cors.append(self._get_static(video_info.img_url, name=video_info.title,
                                         hierarchy=hierarchy if hierarchy else ''))
        await asyncio.gather(*cors)


if __name__ == '__main__':
    async def main():
        d = DownloaderJable()
        await d.get_video("MIAA-650")
        await d.aclose()


    asyncio.run(main())
