import asyncio
import re
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
from bilix.log import logger
from bilix.utils import legal_title, req_retry

BASE_URL = "https://jable.tv"
_dft_headers = {'user-agent': 'PostmanRuntime/7.29.0', "Referer": BASE_URL}


@dataclass
class VideoInfo:
    url: str
    avid: str
    title: str
    model_name: str
    m3u8_url: str
    img_url: str


async def get_video_info(client: httpx.AsyncClient, url_or_avid: str) -> VideoInfo:
    if url_or_avid.startswith('http'):
        url = url_or_avid
        avid = url.split('/')[-2]
    else:
        url = f'{BASE_URL}/videos/{url_or_avid}/'
        avid = url_or_avid
    avid = avid.upper()
    res = await req_retry(client, url)  # proxies default global in httpx
    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.find('meta', property="og:title")['content']
    title = legal_title(title)
    model_name = soup.find("span", class_="placeholder rounded-circle")['title']
    img_url = soup.find('meta', property="og:image")['content']
    m3u8_url = re.findall(r'http.*m3u8', res.text)[0]
    video_info = VideoInfo(url=url, avid=avid, title=title, img_url=img_url, m3u8_url=m3u8_url, model_name=model_name)
    return video_info


if __name__ == '__main__':
    async def main():
        _dft_client = httpx.AsyncClient(headers=_dft_headers, http2=True)
        return await asyncio.gather(
            get_video_info(_dft_client, "MIAA-650"),
        )


    logger.setLevel("DEBUG")
    result = asyncio.run(main())
    print(result)
