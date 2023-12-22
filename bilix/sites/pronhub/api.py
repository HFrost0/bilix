from dataclasses import dataclass
import json
import re
from typing import Union

import httpx
from bs4 import BeautifulSoup
from bilix.utils import legal_title
from bilix.download.utils import raise_api_error, req_retry

BASE_URL = "https://cn.pornhub.com/"
dft_client_settings = {
    'headers': {'user-agent': 'PostmanRuntime/7.29.0', "Referer": BASE_URL},
    'http2': True
}


@dataclass
class VideoInfo:
    url: str
    title: str
    uploader: str
    qualities: dict[str, str]
    img_url: str

    def choose_quality(self, quality: Union[str, int]) -> str:
        if isinstance(quality, str):
            if quality in {'1080', '720', '480', '360'}:
                return self.qualities[quality]
        key = list(self.qualities.keys())[min(int(quality), len(self.qualities) - 1)]
        return self.qualities[key]


@raise_api_error
async def get_video_info(client: httpx.AsyncClient, url: str) -> VideoInfo:
    res = await req_retry(client, url, follow_redirects=True)
    soup = BeautifulSoup(res.text, "html.parser")
    script = soup.find("div", id="player").script.text
    flash_var = re.findall(r'flashvars_\d+ = ({.*?});', script)[0]
    uploader = re.search(r"'video_uploader_name'\s?:\s?'(\S+)'", res.text).group(1)
    video_data = json.loads(flash_var)
    title = legal_title(video_data['video_title'])
    qualities = {str(q): None for q in sorted(video_data['defaultQuality'], reverse=True)}
    for media in video_data['mediaDefinitions']:
        if type(media['quality']) is str and media['quality'] in qualities:
            qualities[media['quality']] = media['videoUrl']

    img_url = video_data['image_url']
    video_info = VideoInfo(url=url, title=title, img_url=img_url, qualities=qualities, uploader=uploader)
    return video_info


@raise_api_error
async def get_uploader_urls(client: httpx.AsyncClient, url: str) -> list[str]:
    res = await req_retry(client, url, follow_redirects=True)
    soup = BeautifulSoup(res.text, "html.parser")
    ul = soup.find("ul", id="mostRecentVideosSection")
    urls = []
    for li in ul.find_all("li"):
        video_key = li['data-video-vkey']
        urls.append(f"{BASE_URL}view_video.php?viewkey={video_key}")
    return urls
