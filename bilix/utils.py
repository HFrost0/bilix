import asyncio
import html
import re
import random
from typing import Union, Sequence
import httpx

from bilix.log import log


async def req_retry(client: httpx.AsyncClient, url_or_urls: Union[str, Sequence[str]], method='GET', follow_redirects=False,
                    **kwargs) -> httpx.Response:
    """Client request with multiple backup urls and retry"""
    pre_exc = Exception("超过重复次数")  # predefine to avoid warning
    for _ in range(3):  # repeat 3 times to handle Exception
        url = url_or_urls if type(url_or_urls) is str else random.choice(url_or_urls)
        try:
            res = await client.request(method, url, follow_redirects=follow_redirects, **kwargs)
            res.raise_for_status()
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            log.warning(f'{method} {e.__class__.__name__} url: {url}')
            pre_exc = e
            await asyncio.sleep(0.1)
        except httpx.HTTPStatusError as e:
            log.warning(f'{method} {e.response.status_code} {url}')
            pre_exc = e
        except Exception as e:
            log.warning(f'{method} {e.__class__.__name__} 未知异常 url: {url}')
            pre_exc = e
            await asyncio.sleep(0.5)
        else:
            return res
    raise pre_exc


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
    s = re.sub(r"[/\\:*?\"<>|]", '', s)  # replace illegal filename character
    return s


def _truncate(s: str, target=150):
    while len(s.encode('utf8')) > target - 3:
        s = s[:-1]
    return s
