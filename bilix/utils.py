import asyncio
import html
import os
import re
import random
from typing import Union, Sequence, Coroutine, List, Tuple
import aiofiles
import httpx

from bilix.log import logger


def cors_slice(cors: Sequence[Coroutine], p_range: Sequence[int]):
    h, t = p_range[0] - 1, p_range[1]
    assert 0 <= h <= t
    [cor.close() for idx, cor in enumerate(cors) if idx < h or idx >= t]  # avoid runtime warning
    cors = cors[h:t]
    return cors


async def req_retry(client: httpx.AsyncClient, url_or_urls: Union[str, Sequence[str]], method='GET',
                    follow_redirects=False, retry=3, **kwargs) -> httpx.Response:
    """Client request with multiple backup urls and retry"""
    pre_exc = Exception(f"{method} 超过重复次数")  # predefine to avoid warning
    for _ in range(1 + retry):
        url = url_or_urls if type(url_or_urls) is str else random.choice(url_or_urls)
        try:
            res = await client.request(method, url, follow_redirects=follow_redirects, **kwargs)
            res.raise_for_status()
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            logger.warning(f'{method} {e.__class__.__name__} url: {url}')
            pre_exc = e
            await asyncio.sleep(0.1)
        except httpx.HTTPStatusError as e:
            logger.warning(f'{method} {e.response.status_code} {url}')
            pre_exc = e
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f'{method} {e.__class__.__name__} 未知异常 url: {url}')
            pre_exc = e
            await asyncio.sleep(0.5)
        else:
            return res
    logger.error(f"{method} 超过重复次数 {url_or_urls}")
    raise pre_exc


async def merge_files(file_list: Sequence[str], new_name: str):
    first_file = file_list[0]
    async with aiofiles.open(first_file, 'ab') as f:
        for idx in range(1, len(file_list)):
            async with aiofiles.open(file_list[idx], 'rb') as fa:
                await f.write(await fa.read())
            os.remove(file_list[idx])
    os.rename(first_file, new_name)


def legal_title(title, add_name=''):
    """

    :param title: 主标题
    :param add_name: 分P名
    :return:
    """
    title, add_name = _replace(title), _replace(add_name)
    title = _truncate(title)  # avoid OSError caused by title too long
    return f'{title}-{add_name}' if add_name else title


def _replace(s: str):
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n]", '', s)  # replace illegal filename character
    return s


def _truncate(s: str, target=150):
    while len(s.encode('utf8')) > target - 3:
        s = s[:-1]
    return s


def parse_bilibili_url(url: str):
    if re.match(r'https://space\.bilibili\.com/\d+/favlist\?fid=\d+', url):
        return 'fav'
    elif re.match(r'https://space\.bilibili\.com/\d+/channel/seriesdetail\?sid=\d+', url):
        return 'list'
    elif re.match(r'https://space\.bilibili\.com/\d+/channel/collectiondetail\?sid=\d+', url):
        return 'col'
    elif re.match(r'https://space\.bilibili\.com/\d+', url):  # up space url
        return 'up'
    elif re.search(r'www\.bilibili\.com', url):
        return 'video'
    raise ValueError(f'{url} no match for bilibili')


def convert_size(total_bytes: int) -> str:
    unit, suffix = pick_unit_and_suffix(
        total_bytes, ["bytes", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"], 1000
    )
    return f"{total_bytes / unit:,.2f}{suffix}"


def pick_unit_and_suffix(size: int, suffixes: List[str], base: int) -> Tuple[int, str]:
    """Borrowed from rich.filesize. Pick a suffix and base for the given size."""
    for i, suffix in enumerate(suffixes):
        unit = base ** i
        if size < unit * base:
            break
    else:
        raise ValueError('Invalid input')
    return unit, suffix


def parse_bytes_str(s: str) -> float:
    """"Parse a string byte quantity into an integer"""
    units_map = {unit: i for i, unit in enumerate(['', *'KMGTPEZY'])}
    units_re = '|'.join(units_map.keys())
    m = re.fullmatch(rf'(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>{units_re})B?', s)
    if not m:
        raise ValueError(f"Invalid bytes str {s} to parse to number")
    num = float(m.group('num'))
    mult = 1000 ** units_map[m.group('unit')]
    return num * mult
