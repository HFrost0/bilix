import re
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
from bilix.utils import legal_title
from bilix.download.utils import raise_api_error, req_retry

BASE_URL = "https://jable.tv"
dft_client_settings = {
    'headers': {'user-agent': 'PostmanRuntime/7.29.0', "Referer": BASE_URL},
    'http2': False
}


class VideoInfo(BaseModel):
    url: str
    avid: str
    title: str
    actor_name: str
    m3u8_url: str
    img_url: str


@raise_api_error
async def get_actor_info(client: httpx.AsyncClient, url: str):
    res = await req_retry(client, url)
    soup = BeautifulSoup(res.text, "html.parser")
    actor_name = soup.find('h2', class_='h3-md mb-1').text
    urls = [h6.a['href'] for h6 in soup.find('section', class_='pb-3 pb-e-lg-40').find_all('h6')]
    return {'actor_name': actor_name, 'urls': urls}


@raise_api_error
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
    if span := soup.find("span", class_="placeholder rounded-circle"):
        actor_name = span['title']
    else:  # https://github.com/HFrost0/bilix/issues/45  for some video actor name in different place
        actor_name = soup.find("img", class_="avatar rounded-circle")['title']
    img_url = soup.find('meta', property="og:image")['content']
    m3u8_url = re.findall(r'http.*m3u8', res.text)[0]
    video_info = VideoInfo(url=url, avid=avid, title=title, img_url=img_url, m3u8_url=m3u8_url, actor_name=actor_name)
    return video_info
