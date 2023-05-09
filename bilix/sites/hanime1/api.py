from pydantic import BaseModel
import httpx
from bilix.utils import legal_title
from bilix.download.utils import req_retry, raise_api_error
from bs4 import BeautifulSoup

BASE_URL = "https://hanime1.me"
dft_client_settings = {
    'headers': {'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012)'
                              ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Mobile'
                              ' Safari/537.36 Edg/87.0.664.66',
                "Referer": BASE_URL},
    'http2': False
}


class VideoInfo(BaseModel):
    url: str
    avid: str
    title: str
    video_url: str
    img_url: str


@raise_api_error
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
    video_url = soup.find('input', {'id': 'video-sd'})['value']
    video_info = VideoInfo(url=url, avid=avid, title=title, img_url=img_url, video_url=video_url)
    return video_info
