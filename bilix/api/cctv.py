import asyncio
import re
import json
from typing import Sequence, Tuple

import httpx
import m3u8
from bilix.log import logger
from bilix.utils import legal_title, req_retry

_dft_headers = {'user-agent': 'PostmanRuntime/7.29.0'}
_dft_client = httpx.AsyncClient(headers=_dft_headers, http2=True)

vida_pattern = re.compile(r'videotvCodes ?= ?"(\w+)"')
pid_pattern = re.compile(r'guid ?= ?"(\w+)"')


async def get_id(url: str, client: httpx.AsyncClient = _dft_client) -> Tuple[str, str]:
    res_web = await req_retry(client, url)
    try:
        vida = vida_pattern.findall(res_web.text)[0]
    except IndexError:
        vida = None
    pid = pid_pattern.findall(res_web.text)[0]
    return pid, vida


async def get_media_info(pid: str, client=_dft_client) -> Tuple[str, Sequence[str]]:
    """

    :param pid:
    :param client:
    :return: title and m3u8_info (play list)
    """
    res = await req_retry(client, f'https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={pid}')
    info_data = json.loads(res.text)
    # extract
    title = legal_title(info_data['title'])
    m3u8_main_url = info_data['hls_url']
    res = await req_retry(client, m3u8_main_url)
    m3u8_info = m3u8.loads(res.text)
    if m3u8_info.base_uri is None:
        m3u8_info.base_uri = re.match(r'(https?://[^/]*)/', m3u8_main_url).groups()[0]
    m3u8_urls = list(sorted((i.absolute_uri for i in m3u8_info.playlists), reverse=True,
                            key=lambda s: int(re.findall(r'/(\d+).m3u8', s)[0])))
    return title, m3u8_urls


async def get_list_info(vida: str, client=_dft_client) -> Sequence[str]:
    """

    :param vida:
    :param client:
    :return: list of guid(pid)
    """
    # todo page number
    params = {'mode': 0, 'id': vida, 'serviceId': 'tvcctv'}
    res = await req_retry(client, f'https://api.cntv.cn/NewVideo/getVideoListByAlbumIdNew', params=params)
    info_data = json.loads(res.text)
    # extract
    return [i['guid'] for i in info_data['data']['list']]


if __name__ == '__main__':
    async def main():
        return await asyncio.gather(
            get_list_info(
                # "https://sports.cctv.com/2022/07/09/VIDEk31WNUm1wWfBRNVCp1YG220709.shtml",
                "VIDAvNhIUgppFT0adfBhvj0M220704"
            ), )


    logger.setLevel("DEBUG")
    result = asyncio.run(main())
    print(result)
