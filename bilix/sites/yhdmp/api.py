import asyncio
import json
import random
import re
from pathlib import Path
from pydantic import BaseModel
from typing import Union, List
import httpx
import execjs
from bs4 import BeautifulSoup
from bilix.utils import legal_title
from bilix.download.utils import req_retry as rr, raise_api_error

BASE_URL = "https://www.yhdmp.cc"
dft_client_settings = {
    'headers': {'user-agent': 'PostmanRuntime/7.29.0', "Referer": BASE_URL},
    'http2': False
}
_js = None


def _get_js():
    global _js
    if _js is None:
        with open(Path(__file__).parent / 'yhdmp.js', 'r') as f:
            _js = execjs.compile(f.read())
    return _js


def _get_t2_k2(t1: str, k1: str) -> dict:
    new_cookies = _get_js().call("get_t2_k2", t1, k1)
    return new_cookies


def _decode(data: str) -> str:
    return _get_js().call('__getplay_rev_data', data)


async def req_retry(client: httpx.AsyncClient, url_or_urls: Union[str, List[str]],
                    method: str = 'GET',
                    follow_redirects: bool = False,
                    **kwargs):
    if 't1' in client.cookies and 'k1' in client.cookies:
        new_cookies = _get_t2_k2(client.cookies['t1'], client.cookies['k1'])
        if 't2' in client.cookies:
            client.cookies.delete('t2')
        if 'k2' in client.cookies:
            client.cookies.delete('k2')
        client.cookies.update(new_cookies)

    res = await rr(client, url_or_urls, method, follow_redirects, **kwargs)
    return res


class VideoInfo(BaseModel):
    aid: Union[str, int]
    play_idx: int
    ep_idx: int
    title: str
    sub_title: str
    play_info: List[Union[List[str], List]]  # may be empty
    m3u8_url: str


@raise_api_error
async def get_video_info(client: httpx.AsyncClient, url: str) -> VideoInfo:
    aid, play_idx, ep_idx = url.split('/')[-1].split('.')[0].split('-')
    play_idx, ep_idx = int(play_idx), int(ep_idx)
    # request
    res_web = req_retry(client, url)
    m3u8_url = get_m3u8_url(url=url, client=client)
    if 't1' in client.cookies and 'k1' in client.cookies:
        res_web, m3u8_url = await asyncio.gather(res_web, m3u8_url)
    else:
        res_web, m3u8_url = await res_web, await m3u8_url
    # extract
    title, sub_title = map(legal_title,
                           re.search(r'target="_self">([^<]+)</a><span>:([^<]+)</span>', res_web.text).groups())
    soup = BeautifulSoup(res_web.text, 'html.parser')
    divs = soup.find_all('div', class_="movurl")
    play_info = []
    for div in divs:
        play_info.append([[legal_title(a["title"]), f"{BASE_URL}/{a['href']}"] for a in div.find_all("a")])
    video_info = VideoInfo(aid=aid, play_idx=play_idx, ep_idx=ep_idx, title=title, sub_title=sub_title,
                           play_info=play_info, m3u8_url=m3u8_url)
    return video_info


@raise_api_error
async def get_m3u8_url(client: httpx.AsyncClient, url):
    aid, play_idx, ep_idx = url.split('/')[-1].split('.')[0].split('-')
    params = {"aid": aid, "playindex": play_idx, "epindex": ep_idx, "r": random.random()}
    res_play = await req_retry(client, f"{BASE_URL}/_getplay", params=params)
    if res_play.text.startswith("err"):  # maybe first time
        res_play = await req_retry(client, f"{BASE_URL}/_getplay", params=params)
    data = json.loads(res_play.text)
    purl, vurl = _decode(data['purl']), _decode(data['vurl'])
    m3u8_url = purl.split("url=")[-1] + vurl
    return m3u8_url
