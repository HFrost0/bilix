"""
Originally From
@Author: https://github.com/Evil0ctal/
https://github.com/Evil0ctal/Douyin_TikTok_Download_API
"""

import re
import json
import random
from typing import List
import httpx
from pydantic import BaseModel
from bilix.utils import legal_title
from bilix.download.utils import req_retry, raise_api_error

dft_client_settings = {
    'headers': {'user-agent': 'com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;'
                              '+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+'
                              '(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36'},
    'http2': True
}


class VideoInfo(BaseModel):
    title: str
    author_name: str
    wm_urls: List[str]
    nwm_urls: List[str]
    cover: str
    dynamic_cover: str
    origin_cover: str


@raise_api_error
async def get_video_info(client: httpx.AsyncClient, url: str) -> VideoInfo:
    if short_url := re.findall(r'https://www.tiktok.com/t/\w+/', url):
        res = await req_retry(client, short_url[0], follow_redirects=True)
        url = str(res.url)
    if key := re.search(r'/video/(\d+)', url):
        key = key.groups()[0]
    else:
        key = re.search(r"/v/(\d+)", url).groups()[0]
    params = {'aweme_id': key, 'aid': 1180, 'iid': 6165993682518218889,
              'device_id': random.randint(10 * 10 * 10, 9 * 10 ** 10)}
    res = await req_retry(client, 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/', params=params)
    data = json.loads(res.text)
    data = data['aweme_list'][0]
    # 视频标题 (如果为空则使用分享标题)
    title = legal_title(data['desc'] if data['desc'] != '' else data['share_info']['share_title'])
    # 视频作者昵称
    author_name = data['author']['nickname']
    # 有水印视频链接
    wm_urls = data['video']['download_addr']['url_list']
    # 无水印视频链接
    nwm_urls = data['video']['bit_rate'][0]['play_addr']['url_list']
    # 视频封面
    cover = data['video']['cover']['url_list'][0]
    # 视频动态封面
    dynamic_cover = data['video']['dynamic_cover']['url_list'][0]
    # 视频原始封面
    origin_cover = data['video']['origin_cover']['url_list'][0]
    video_info = VideoInfo(title=title, author_name=author_name, wm_urls=wm_urls, nwm_urls=nwm_urls, cover=cover,
                           dynamic_cover=dynamic_cover, origin_cover=origin_cover)
    return video_info
