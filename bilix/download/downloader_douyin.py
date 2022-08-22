import asyncio
import httpx

import bilix.api.douyin as api
from bilix.api.douyin import _dft_headers
from bilix.assign import Handler
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.utils import legal_title, req_retry


class DownloaderDouyin(BaseDownloaderPart):
    def __init__(self, videos_dir='videos', part_concurrency=10):
        client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        super(DownloaderDouyin, self).__init__(client, videos_dir, part_concurrency)

    async def get_video(self, url: str, image=False):
        video_info = await api.get_video_info(self.client, url)
        title = legal_title(video_info.author_name, video_info.title)
        # redirect to real video location
        res = await req_retry(self.client, video_info.nwm_urls[0], follow_redirects=True)
        media_urls = [str(res.url)]
        cors = [self.get_media(media_urls, media_name=title + ".mp4")]
        if image:
            cors.append(self._get_static(video_info.cover, title))
        await asyncio.gather(*cors)


@Handler(name='抖音')
def handle(**kwargs):
    key = kwargs['key']
    if 'douyin' in key:
        part_con = kwargs['part_concurrency']
        videos_dir = kwargs['videos_dir']
        image = kwargs['image']
        method = kwargs['method']
        d = DownloaderDouyin(videos_dir=videos_dir, part_concurrency=part_con)
        if method == 'v' or method == 'get_video':
            cor = d.get_video(key, image)
            return d, cor
        raise ValueError(f'For {d.__class__.__name__} "{method}" is not available')
