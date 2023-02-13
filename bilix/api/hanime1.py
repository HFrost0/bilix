import asyncio
from bilix.log import logger
from pydantic import BaseModel
import httpx
from bilix.utils import legal_title, req_retry
from bs4 import BeautifulSoup

BASE_URL = "https://hanime1.me"
dft_client_settings = {
    'headers': {'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile'
                              ' Safari/537.36 Edg/87.0.664.66', "Referer": BASE_URL},
    'http2': False
}


class VideoInfo(BaseModel):
    url: str
    avid: str
    title: str
    mp4_url: str
    img_url: str


async def get_video_info(client: httpx.AsyncClient, url_or_avid: str) -> VideoInfo:
    if url_or_avid.startswith('http'):
        url = url_or_avid
        avid = url.split('=')[-1]
    else:
        url = f'{BASE_URL}/watch?v={url_or_avid}'
        avid = url_or_avid
    res = await req_retry(client, url)
    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.find('meta', property="og:title")['content']
    title = legal_title(title)
    img_url = soup.find('meta', property="og:image")['content']
    mp4_url = soup.find('input', {'id': 'video-sd'})['value']
    video_info = VideoInfo(url=url, avid=avid, title=title, img_url=img_url, mp4_url=mp4_url)
    return video_info


if __name__ == '__main__':
    async def main():
        _dft_client = httpx.AsyncClient(**dft_client_settings)
        return await asyncio.gather(
            get_video_info(_dft_client, "39466"),
        )


    logger.setLevel("DEBUG")
    result = asyncio.run(main())
    print(result)
