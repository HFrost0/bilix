import re
from pydantic import BaseModel
from typing import Union, List
import httpx
from bs4 import BeautifulSoup
from bilix.download.utils import req_retry, raise_api_error

BASE_URL = "http://www.yinghuacd.com"
dft_client_settings = {
    'headers': {'user-agent': 'PostmanRuntime/7.29.0'},
    'http2': False
}


class VideoInfo(BaseModel):
    title: str
    sub_title: str
    play_info: List[Union[List[str], List]]  # may be empty
    m3u8_url: str


@raise_api_error
async def get_video_info(client: httpx.AsyncClient, url: str) -> VideoInfo:
    # request
    res = await req_retry(client, url)
    m3u8_url = re.search(r'http.*m3u8', res.text)[0]
    soup = BeautifulSoup(res.text, 'html.parser')
    h1 = soup.find('h1')
    title, sub_title = h1.a.text, h1.span.text[1:]

    # extract
    play_info = [[a.text, f"{BASE_URL}{a['href']}"] for a in soup.find('div', class_="movurls").find_all('a')]
    video_info = VideoInfo(title=title, sub_title=sub_title, play_info=play_info, m3u8_url=m3u8_url)
    return video_info
