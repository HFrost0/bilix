"""
Originally From
@Author: https://github.com/Evil0ctal/
https://github.com/Evil0ctal/Douyin_TikTok_Download_API

Modified by
@Author: https://github.com/HFrost0/
"""
import asyncio
import re
import json
from typing import Sequence
import httpx
from dataclasses import dataclass
from bilix.utils import req_retry, legal_title

_dft_headers = {'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile'
                              ' Safari/537.36 Edg/87.0.664.66'}


@dataclass
class VideoInfo:
    title: str
    author_name: str
    wm_urls: Sequence[str]
    nwm_urls: Sequence[str]
    cover: str
    dynamic_cover: str
    origin_cover: str


async def get_video_info(client: httpx.AsyncClient, url: str) -> VideoInfo:
    if short_url := re.findall(r'https://v.douyin.com/\w+/', url):
        res = await req_retry(client, short_url[0], follow_redirects=True)
        url = str(res.url)
    if key := re.search(r'/video/(\d+)', url):
        key = key.groups()[0]
    else:
        key = re.search(r"modal_id=(\d+)", url).groups()[0]
    res = await req_retry(client, f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={key}')
    data = json.loads(res.text)
    data = data['item_list'][0]
    # 视频标题
    title = legal_title(data['desc'])
    # 视频作者昵称
    author_name = data['author']['nickname']
    # 有水印视频链接
    wm_urls = data['video']['play_addr']['url_list']
    # 无水印视频链接 (在回执JSON中将关键字'playwm'替换为'play'即可获得无水印地址)
    nwm_urls = list(map(lambda x: x.replace('playwm', 'play'), wm_urls))
    # 视频封面
    cover = data['video']['cover']['url_list'][0]
    # 视频动态封面
    dynamic_cover = data['video']['dynamic_cover']['url_list'][0]
    # 视频原始封面
    origin_cover = data['video']['origin_cover']['url_list'][0]
    video_info = VideoInfo(title=title, author_name=author_name, wm_urls=wm_urls, nwm_urls=nwm_urls, cover=cover,
                           dynamic_cover=dynamic_cover, origin_cover=origin_cover)
    return video_info


if __name__ == '__main__':
    async def main():
        _dft_client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        data = await get_video_info(_dft_client, 'https://www.douyin.com/video/7132430286415252773')
        print(data)


    asyncio.run(main())
