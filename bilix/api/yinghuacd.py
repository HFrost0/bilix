import asyncio
import re
from dataclasses import dataclass
from typing import Union, Sequence
import httpx
from bs4 import BeautifulSoup
from bilix.log import logger
from bilix.utils import req_retry

BASE_URL = "http://www.yinghuacd.com"
_dft_headers = {'user-agent': 'PostmanRuntime/7.29.0'}


@dataclass
class VideoInfo:
    title: str
    sub_title: str
    play_info: Sequence[Union[Sequence[str], Sequence]]  # may be empty
    m3u8_url: str


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


async def main():
    _dft_client = httpx.AsyncClient(headers=_dft_headers, http2=True)

    return await asyncio.gather(
        get_video_info(_dft_client, "http://www.yinghuacd.com/v/5606-7.html"),
    )


if __name__ == '__main__':
    logger.setLevel("DEBUG")
    result = asyncio.run(main())
    print(result)
