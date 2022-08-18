import asyncio

import httpx

import bilix.api.douyin as api
from bilix.api.douyin import _dft_headers
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.utils import legal_title, req_retry


class DownLoaderDouyin(BaseDownloaderPart):
    def __init__(self, videos_dir='videos', part_concurrency=10):
        client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        super(DownLoaderDouyin, self).__init__(client, videos_dir, part_concurrency)

    async def get_video(self, url: str, image=False):
        video_info = await api.get_video_info(url, self.client)
        title = legal_title(video_info.author_name, video_info.title)
        # redirect to real video location
        res = await req_retry(self.client, video_info.nwm_urls[0], follow_redirects=True)
        media_urls = [str(res.url)]
        cors = [self.get_media(media_urls, media_name=title + ".mp4")]
        if image:
            cors.append(self._get_static(video_info.cover, title))
        await asyncio.gather(*cors)


def handle(**kwargs):
    key = kwargs['key']
    if 'douyin' in key:
        part_con = kwargs['part_concurrency']
        videos_dir = kwargs['videos_dir']
        image = kwargs['image']
        method = kwargs['method']
        if method == 'v' or method == 'get_video':
            d = DownLoaderDouyin(videos_dir=videos_dir, part_concurrency=part_con)
            cor = d.get_video(key, image)
            return d, cor


if __name__ == '__main__':
    async def main():
        async with DownLoaderDouyin() as d:
            await d.get_video("https://www.douyin.com/video/6781355292451015948")


    asyncio.run(main())
