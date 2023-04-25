import asyncio
import inspect
import logging
import time
from functools import wraps
from typing import Union, Optional, Tuple
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import aiofiles
import httpx
from bilix.log import logger as dft_logger
from bilix.download.utils import req_retry, path_check
from bilix.progress.abc import Progress
from bilix.progress.cli_progress import CLIProgress
from pathlib import Path, PurePath

__all__ = ['BaseDownloader']


class BaseDownloaderMeta(type):
    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            # check if attr is a non-private coroutine function
            if not attr_name.startswith('__') and asyncio.iscoroutinefunction(attr_value):
                # function has path argument
                if 'path' in (sig := inspect.signature(attr_value)).parameters:
                    dct[attr_name] = cls.ensure_path(attr_value, sig)
        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def ensure_path(func, sig):
        path_index = next(i for i, name in enumerate(sig.parameters) if name == 'path')

        @wraps(func)
        async def wrapper(*args, **kwargs):
            new_args = list(args)
            if path_index < len(args) and isinstance(args[path_index], str):
                new_args[path_index] = Path(args[path_index])
            elif 'path' in kwargs and isinstance(kwargs['path'], str):
                kwargs['path'] = Path(kwargs['path'])

            return await func(*new_args, **kwargs)

        wrapper.__annotations__['path'] = Union[Path, str]
        return wrapper


class BaseDownloader(metaclass=BaseDownloaderMeta):
    COOKIE_DOMAIN: str = ""

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: logging.Logger = None,
    ):
        """

        :param client: client used for http request
        :param browser: load cookies from which browser
        :param speed_limit: global download rate for the downloader, should be a number (Byte/s unit)
        :param progress: progress obj
        """
        # use cli progress by default
        self.progress = progress or CLIProgress()
        self.logger = logger or dft_logger
        self.client = client if client else httpx.AsyncClient(headers={'user-agent': 'PostmanRuntime/7.29.0'})
        if browser:  # load cookies from browser, may need auth
            self.update_cookies_from_browser(browser)
        assert speed_limit is None or speed_limit > 0
        self.speed_limit = speed_limit
        self.stream_retry = stream_retry
        # active stream number
        self._stream_num = 0

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        """Close transport and proxies for httpx client"""
        await self.client.aclose()

    async def get_static(self, url: str, path: Union[str, Path], convert_func=None) -> Path:
        """

        :param url:
        :param path: file path without suffix
        :param convert_func: function used to convert http bytes content, must be named like ...2...
        :return: downloaded file path
        """
        # use suffix from convert_func's name
        if convert_func:
            suffix = '.' + convert_func.__name__.split('2')[-1]
        # try to find suffix from url
        else:
            suffix = PurePath(urlparse(url).path).suffix
        path = path.with_name(path.name + suffix)
        exist, path = path_check(path)
        if exist:
            self.logger.info(f'[green]已存在[/green] {path.name}')
            return path
        res = await req_retry(self.client, url)
        content = convert_func(res.content) if convert_func else res.content
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
        self.logger.info(f'[cyan]已完成[/cyan] {path.name}')
        return path

    @asynccontextmanager
    async def _stream_context(self, times: int):
        """
        contextmanager to print log, slow down streaming and count active stream number

        :param times: error occur times which is related to sleep time
        :return:
        """
        self._stream_num += 1
        try:
            yield
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                self.logger.warning(f"STREAM slowing down since 403 forbidden {e}")
                await asyncio.sleep(10. * (times + 1))
            else:
                self.logger.warning(f"STREAM {e}")
                await asyncio.sleep(.5 * (times + 1))
            raise
        except httpx.TransportError as e:
            msg = f'STREAM {e.__class__.__name__} 异常可能由于网络条件不佳或并发数过大导致，若重复出现请考虑降低并发数'
            self.logger.warning(msg) if times > 2 else self.logger.debug(msg)
            await asyncio.sleep(.1 * (times + 1))
            raise
        except Exception as e:
            self.logger.warning(f'STREAM Unexpected Exception class:{e.__class__.__name__} {e}')
            raise
        finally:
            self._stream_num -= 1

    @property
    def stream_num(self):
        """current activate network stream number"""
        return self._stream_num

    LIMIT_BOUND: float = 1e5
    DELAY_SLOPE: float = 0.1

    @property
    def chunk_size(self) -> Optional[int]:
        if self.speed_limit and self.speed_limit < self.LIMIT_BOUND:
            # only restrict chunk_size when speed_limit is too low
            return int(self.speed_limit * self.DELAY_SLOPE)
        # default to None setup
        return None

    async def _check_speed(self, content_size):
        if self.speed_limit and (cur_speed := self.progress.active_speed) > self.speed_limit:
            t_tgt = content_size / self.speed_limit * self.stream_num
            t_real = content_size / cur_speed
            t = t_tgt - t_real
            await asyncio.sleep(t)

    def update_cookies_from_browser(self, browser: str):
        try:
            a = time.time()
            import browser_cookie3
            f = getattr(browser_cookie3, browser.lower())
            self.logger.debug(f"trying to load cookies from {browser}: {self.COOKIE_DOMAIN}, may need auth")
            self.client.cookies.update(f(domain_name=self.COOKIE_DOMAIN))
            self.logger.debug(f"load complete, consumed time: {time.time() - a} s")
        except AttributeError:
            raise AttributeError(f"Invalid Browser {browser}")

    @classmethod
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        return NotImplemented
