import asyncio
import inspect
import logging
import time
from functools import wraps
from typing import Union, Optional, Callable, Dict
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import aiofiles
import httpx

from bilix.cli_new.handler import Handler, HandlerMeta
from bilix.log import logger as dft_logger
from bilix.download.utils import req_retry, path_check
from bilix.utils import parse_bytes_str
from bilix.progress.abc import Progress
from bilix.progress.cli_progress import CLIProgress
from pathlib import Path, PurePath

try:
    from typing import Annotated, get_origin, get_args, get_type_hints
except ImportError:  # lower than python 3.9
    from typing_extensions import Annotated, get_origin, get_args, get_type_hints

__all__ = ['BaseDownloader']


def check_annotated(annotated_type) -> Callable:
    assert get_origin(annotated_type) is Annotated
    args = get_args(annotated_type)
    assert len(args) == 2
    target_type, convertor = args
    assert inspect.isfunction(convertor), f"{convertor} is not a function"
    type_hints = get_type_hints(convertor)
    assert len(type_hints) == (1 if 'return' not in type_hints else 2)
    return convertor


class BaseDownloaderMeta(HandlerMeta):
    def __new__(cls, name, bases, dct):
        for method_name, method in dct.items():
            if inspect.isfunction(method):
                dct[method_name] = cls.ensure_path(method)
        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def ensure_path(func: Callable) -> Callable:
        def convert(*args, **kwargs):
            # todo check type hint of convertor
            new_args = list(args)
            for i, arg in enumerate(args):
                if i in convertors:
                    new_args[i] = convertors[i](arg)
            for k, v in kwargs.items():
                if k in convertors:
                    kwargs[k] = convertors[k](v)
            return new_args, kwargs

        sig = inspect.signature(func)
        convertors: Dict[Union[int, str], Callable] = {}
        for idx, p in enumerate(sig.parameters.values()):
            if get_origin(p.annotation) is Annotated:
                convertor = check_annotated(p.annotation)
                convertors[idx] = convertor  # for args
                convertors[p.name] = convertor  # for kwargs
        if len(convertors) == 0:  # if no Annotated, return original func
            return func

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                new_args, kwargs = convert(*args, **kwargs)
                return await func(*new_args, **kwargs)
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                new_args, kwargs = convert(*args, **kwargs)
                return func(*new_args, **kwargs)
        return wrapper


def str2path(value: str) -> Path:
    """convert str to Path, but with type hint"""
    return Path(value)


class BaseDownloader(Handler, metaclass=BaseDownloaderMeta):
    cookie_domain: str = ""  # cookie domain used to accelerate cookie load

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_bytes_str] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: logging.Logger = None,
    ):
        """
        :param client: client used for http request
        :param browser: load cookies from which browser
        :param stream_retry: retry times for http stream
        :param speed_limit: global download rate for the downloader, should be a number (Byte/s unit) or speed str
        :param progress: progress obj used to output download progress
        :param logger: logger obj used to output log
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

    async def get_static(self, url: str, path: Annotated[Path, str2path], convert_func=None) -> Path:
        """
        download static file from url
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

    @property
    def chunk_size(self) -> Optional[int]:
        if self.speed_limit and self.speed_limit < 1e5:  # 1e5 limit bound
            # only restrict chunk_size when speed_limit is too low
            return int(self.speed_limit * 0.1)  # 0.1 delay slope
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
            self.logger.debug(f"trying to load cookies from {browser}: {self.cookie_domain}, may need auth")
            self.client.cookies.update(f(domain_name=self.cookie_domain))
            self.logger.debug(f"load complete, consumed time: {time.time() - a} s")
        except AttributeError:
            raise AttributeError(f"Invalid Browser {browser}")
