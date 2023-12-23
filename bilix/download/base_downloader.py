import asyncio
import inspect
import time
import random
from functools import wraps
from collections import OrderedDict
from typing import Union, Optional, Callable, Dict, Any, Tuple, List, Set, Annotated, get_origin, get_args
from contextlib import asynccontextmanager
from urllib.parse import urlparse
import aiofiles
import httpx

from bilix.cli.handler import Handler, HandlerMeta
from bilix.log import logger as dft_logger, CustomLogger
from bilix.download.utils import path_check, parse_speed_str, str2path
from bilix.progress.abc import Progress
from bilix.progress.cli_progress import CLIProgress
from pathlib import Path, PurePath


def is_instance_of_generic_type(value: Any, target_type: Any) -> bool:
    origin = get_origin(target_type)
    args = get_args(target_type)
    if origin is None and args == ():
        return isinstance(value, target_type)
    if origin == Union:
        return any(is_instance_of_generic_type(value, arg) for arg in args)
    return isinstance(value, origin)


def annotated_convertors(annotated_type) -> Tuple[Any, List[Callable], Set[Any]]:
    assert get_origin(annotated_type) is Annotated
    args = get_args(annotated_type)
    assert len(args) > 1
    target_type, *convertors = args
    types = set()
    for convertor in convertors:
        assert inspect.isfunction(convertor), f"{convertor} is not a function"
        sig = inspect.signature(convertor)
        assert len(sig.parameters) == 1, f"convertor {convertor} must have exactly one parameter"
        p = list(sig.parameters.values())[0]
        assert p.annotation != p.empty, f"convertor's parameter must have annotation"
        assert p.annotation not in types, f"convertor's parameter annotation must be unique"
        types.add(p.annotation)
    return target_type, convertors, types


def _convert(convertors_map: Dict[Union[int, str], Tuple[Any, List[Callable], Set[Any]]], *args, **kwargs):
    new_args = list(args)

    for key, (tgt_type, convertors, types) in convertors_map.items():
        if isinstance(key, str) and key in kwargs and not is_instance_of_generic_type(kwargs[key], tgt_type):
            source = kwargs
        elif isinstance(key, int) and key < len(args) and not is_instance_of_generic_type(args[key], tgt_type):
            source = new_args
        else:
            continue
        # find a convertor that can convert the source arg to target type
        for convertor, t in zip(convertors, types):
            if is_instance_of_generic_type(source[key], t):
                source[key] = convertor(source[key])
                break
        else:
            # no convertor is applied
            pass
    return new_args, kwargs


def annotated_decorator(func: Callable) -> Callable:
    sig = inspect.signature(func)

    convertors_map: Dict[Union[int, str], Tuple[Any, List[Callable], List[Any]]] = {}
    for idx, p in enumerate(sig.parameters.values()):
        if get_origin(p.annotation) is Annotated:
            try:
                target_type, convertors, types = annotated_convertors(p.annotation)
            except AssertionError:
                continue
            convertors_map[idx] = (target_type, convertors, types)  # for args
            convertors_map[p.name] = (target_type, convertors, types)  # for kwargs
    if len(convertors_map) == 0:  # if no Annotated, return original func
        return func

    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            new_args, kwargs = _convert(convertors_map, *args, **kwargs)
            return await func(*new_args, **kwargs)
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            new_args, kwargs = _convert(convertors_map, *args, **kwargs)
            return func(*new_args, **kwargs)
    return wrapper


class BaseDownloaderMeta(HandlerMeta):
    def __new__(cls, name, bases, dct):
        for method_name, method in dct.items():
            if inspect.isfunction(method):
                dct[method_name] = annotated_decorator(method)
        return super().__new__(cls, name, bases, dct)


class BaseDownloader(Handler, metaclass=BaseDownloaderMeta):
    cookie_domain: str = ""  # cookie domain used to accelerate cookie load

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: CustomLogger = None,
    ):
        """
        :param client: client used for http request
        :param browser: load cookies from which browser
        :param stream_retry: retry times for http stream
        :param speed_limit: global download rate for the downloader. should be a float (Byte/s unit) or str (e.g. 1.5MB)
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
        # url score
        self._url_scores = DefaultLRUCache(default_factory=lambda: self.stream_retry * 5, capacity=1000)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        """Close transport and proxies for httpx client"""
        await self.client.aclose()

    async def get_static(self, url: str, path: Annotated[Path, str2path], convert_func=None, task_id=None) -> Path:
        """
        download static file from url
        :param url:
        :param path: file path without suffix
        :param convert_func: function used to convert http bytes content, must be named like ...2...
        :param task_id: task id used to update progress, if None, progress will not be updated
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
            if task_id is None:
                self.logger.exist(path.name)
            return path

        async def update_progress_total(length):
            if (t := self.progress.tasks[task_id].total) is None:
                await self.progress.update(task_id, total=length, visible=True)
            else:
                await self.progress.update(task_id, total=length + t)

        for times in range(1 + self.stream_retry):
            content = bytearray()
            try:
                async with self.client.stream('GET', url) as r, self._stream_context(times):
                    r.raise_for_status()
                    if task_id is not None and 'content-length' in r.headers and not content:
                        await update_progress_total(int(r.headers['content-length']))
                    async for chunk in r.aiter_bytes(chunk_size=self._chunk_size):
                        content.extend(chunk)
                        if task_id is not None:
                            await self.progress.update(task_id, advance=len(chunk))
                        await self._check_speed(len(chunk))
                if task_id is not None and 'content-length' not in r.headers:
                    await update_progress_total(len(content))
                break
            except (httpx.HTTPStatusError, httpx.TransportError):
                continue
        else:
            raise Exception(f"STREAM max retry {url}")
        content = convert_func(bytes(content)) if convert_func else content
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
        if task_id is None:
            self.logger.done(path.name)
        return path

    def _change_score(self, exc: Union[httpx.HTTPStatusError, httpx.TransportError]):
        """change url score according to exception"""
        if isinstance(exc, httpx.HTTPStatusError):
            self._url_scores[exc.request.url] -= 4
        elif isinstance(exc, httpx.TransportError):
            self._url_scores[exc.request.url] -= 1
        self._url_scores[exc.request.url] = max(1, self._url_scores[exc.request.url])

    def _choose_stream_url(self, urls: List[str]) -> int:
        """choose a stream url idx from urls"""

        return random.choices(range(len(urls)), weights=[self._url_scores[url] for url in urls], k=1)[0]

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
            self._change_score(e)
            raise
        except httpx.TransportError as e:
            msg = f'STREAM {e.__class__.__name__} 异常可能由于网络条件不佳或并发数过大导致，若重复出现请考虑降低并发数'
            self.logger.warning(msg) if times > 2 else self.logger.debug(msg)
            await asyncio.sleep(.1 * (times + 1))
            self._change_score(e)
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
    def _chunk_size(self) -> Optional[int]:
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


class DefaultLRUCache(OrderedDict):
    def __init__(self, default_factory, capacity: int):
        self.default_factory = default_factory
        self.capacity = capacity
        super().__init__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            value = self.default_factory()
            self[key] = value
            return value

    def __setitem__(self, key, value):
        if key not in self and len(self) >= self.capacity:
            self.popitem(last=False)
        super().__setitem__(key, value)
