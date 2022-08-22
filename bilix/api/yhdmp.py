import asyncio
import json
import os
import random
import re
from dataclasses import dataclass
from typing import Union, Sequence
import httpx
import execjs
from bs4 import BeautifulSoup
from bilix.log import logger
import bilix.utils
from bilix.utils import legal_title

BASE_URL = "https://www.yhdmp.cc"
_dft_headers = {'user-agent': 'PostmanRuntime/7.29.0', "Referer": BASE_URL}

with open(f'{os.path.dirname(bilix.__file__)}/js/yhdmp.js', 'r') as f:
    js = execjs.compile(f.read())


def _get_t2_k2(t1: str, k1: str) -> dict:
    new_cookies = js.call("get_t2_k2", t1, k1)
    return new_cookies


def _decode(data: str) -> str:
    return js.call('__getplay_rev_data', data)


async def req_retry(client: httpx.AsyncClient, url_or_urls: Union[str, Sequence[str]],
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

    res = await bilix.utils.req_retry(client, url_or_urls, method, follow_redirects, **kwargs)
    return res


@dataclass
class VideoInfo:
    aid: Union[str, int]
    play_idx: int
    ep_idx: int
    title: str
    sub_title: str
    play_info: Sequence[Union[Sequence[str], Sequence]]  # may be empty
    m3u8_url: str


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


async def main():
    _dft_client = httpx.AsyncClient(headers=_dft_headers, http2=True)

    return await asyncio.gather(
        get_video_info(_dft_client, "https://www.yhdmp.cc/vp/22224-1-0.html"),
        get_m3u8_url(_dft_client, "https://www.yhdmp.cc/vp/18261-2-0.html"),
    )


if __name__ == '__main__':
    logger.setLevel("DEBUG")
    result = asyncio.run(main())
    print(result)
