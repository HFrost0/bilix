import re
import json
from pydantic import BaseModel
import httpx
from bilix.download.utils import req_retry
from bilix.utils import legal_title

dft_client_settings = {
    'headers': {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
        'referer': 'https://www.youtube.com/'
    },
}


class VideoInfo(BaseModel):
    # url: str
    title: str
    video_url: str
    audio_url: str
    # img_url: str


async def get_video_info(client: httpx.AsyncClient, url: str):
    response = await req_retry(client=client, url_or_urls=url)
    # 解析
    json_str = re.findall('var ytInitialPlayerResponse = (.*?);var', response.text)[0]
    json_data = json.loads(json_str)
    video_url = json_data['streamingData']['adaptiveFormats'][0]['url']
    audio_url = json_data['streamingData']['adaptiveFormats'][-2]['url']
    title = legal_title(json_data['videoDetails']['title'])
    video_info = VideoInfo(video_url=video_url, audio_url=audio_url, title=title)
    return video_info
