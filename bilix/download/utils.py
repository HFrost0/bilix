import asyncio
import errno
import os
import random
import re
from functools import wraps
from pathlib import Path

import aiofiles
import httpx
from typing import Union, Sequence, Tuple, List
from bilix.exception import APIError, APIParseError
from bilix.log import logger
from bilix.utils import s2t


async def merge_files(file_list: List[Path], new_path: Path):
    first_file = file_list[0]
    async with aiofiles.open(first_file, 'ab') as f:
        for idx in range(1, len(file_list)):
            async with aiofiles.open(file_list[idx], 'rb') as fa:
                await f.write(await fa.read())
            os.remove(file_list[idx])
    os.rename(first_file, new_path)


async def req_retry(client: httpx.AsyncClient, url_or_urls: Union[str, Sequence[str]], method='GET',
                    follow_redirects=False, retry=5, **kwargs) -> httpx.Response:
    """Client request with multiple backup urls and retry"""
    pre_exc = None  # predefine to avoid warning
    for times in range(1 + retry):
        url = url_or_urls if type(url_or_urls) is str else random.choice(url_or_urls)
        try:
            res = await client.request(method, url, follow_redirects=follow_redirects, **kwargs)
            res.raise_for_status()
        except httpx.TransportError as e:
            msg = f'{method} {e.__class__.__name__} url: {url}'
            logger.warning(msg) if times > 0 else logger.debug(msg)
            pre_exc = e
            await asyncio.sleep(.1 * (times + 1))
        except httpx.HTTPStatusError as e:
            logger.warning(f'{method} {e.response.status_code} {url}')
            pre_exc = e
            await asyncio.sleep(1. * (times + 1))
        except Exception as e:
            logger.warning(f'{method} Unknown Exception {e.__class__.__name__} url: {url}')
            raise e
        else:
            return res
    logger.error(f"{method} max retry {url_or_urls}")
    raise pre_exc


def eclipse_str(s: str, max_len: int = 100):
    if len(s) <= max_len:
        return s
    else:
        half_len = (max_len - 1) // 2
        return f"{s[:half_len]}…{s[-half_len:]}"


def path_check(path: Path, retry: int = 100) -> Tuple[bool, Path]:
    """
    check whether path exist, if filename too long, truncate and return valid path

    :param path: path to check
    :param retry: max retry times
    :return: exist, path
    """
    for times in range(retry):
        try:
            exist = path.exists()
            return exist, path
        except OSError as e:
            if e.errno == errno.ENAMETOOLONG:  # filename too long for os
                if times == 0:
                    logger.warning(f"filename too long for os, truncate will be applied. filename: {path.name}")
                else:
                    logger.debug(f"filename too long for os {path.name}")
                path = path.with_stem(eclipse_str(path.stem, int(len(path.stem) * .8)))
            else:
                raise e
    raise OSError(f"filename too long for os {path.name}")


def raise_api_error(func):
    """Decorator to catch exceptions except APIError and HTTPError and raise APIParseError"""

    @wraps(func)
    async def wrapped(client: httpx.AsyncClient, *args, **kwargs):
        try:
            return await func(client, *args, **kwargs)
        except (APIError, httpx.HTTPError):
            raise
        except Exception as e:
            raise APIParseError(e, func) from e

    return wrapped


def parse_speed_str(value: str) -> float:
    """Parse a string byte quantity into float"""
    units_map = {unit: i for i, unit in enumerate(['', *'KMGTPEZY'])}
    units_re = '|'.join(units_map.keys())
    m = re.fullmatch(rf'(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>{units_re})B?', value)
    if not m:
        raise ValueError(f"Invalid bytes str {value} to parse to number")
    num = float(m.group('num'))
    mult = 1000 ** units_map[m.group('unit')]
    return num * mult


def parse_time_range(value: str) -> Tuple[int, int]:
    """Parse a time range string into start and end time"""
    start_time, end_time = map(s2t, value.split('-'))
    return start_time, end_time


def str2path(value: str) -> Path:
    """convert str to Path, but with type hint"""
    return Path(value)
