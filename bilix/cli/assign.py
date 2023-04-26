import asyncio
import inspect
import re
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Union, Tuple
from importlib import import_module

from bilix.exception import HandleMethodError, HandleError
from bilix.log import logger


def kwargs_filter(obj: Union[type, Callable], kwargs: dict):
    """

    :param obj:
    :param kwargs:
    :return:
    """
    sig = inspect.signature(obj)
    obj_require = set(sig.parameters.keys())

    def check(k):
        if k in obj_require:
            p = sig.parameters[k]
            # check type hint
            try:
                if p.annotation is inspect.Signature.empty or \
                        isinstance(kwargs[k], p.annotation):
                    return True
                else:
                    logger.debug(f"kwarg {k}:{kwargs[k]} has been drop due to type hint missmatch")
                    return False
            except TypeError:  # https://peps.python.org/pep-0604/#isinstance-and-issubclass
                # lower than 3.10, Union
                # TypeError: Subscripted generics cannot be used with class and instance checks
                return True
        return False

    kwargs = {k: kwargs[k] for k in filter(check, kwargs)}
    return kwargs


def module_handle_funcs(module):
    """find and yield all handle func in module"""
    attrs = getattr(module, '__all__', None)
    attrs = attrs or dir(module)
    for attr_name in attrs:
        if attr_name.startswith('__'):
            continue
        executor_cls = getattr(module, attr_name)
        if not inspect.isclass(executor_cls):
            continue
        handle_func = getattr(executor_cls, 'handle', None)
        if handle_func is None:
            continue
        yield handle_func


def auto_assemble(handle_func):
    @wraps(handle_func)
    def wrapped(cls, method: str, keys: Tuple[str, ...], options: dict):
        res = handle_func(cls, method, keys, options)
        if res is NotImplemented or res is None:
            return res
        executor, cor = res
        # handle func return class instead of instance
        if inspect.isclass(executor):
            kwargs = kwargs_filter(executor, options)
            executor = executor(**kwargs)
            logger.debug(f"auto assemble {executor} by {kwargs}")
        # handle func return async function instead of coroutine
        if inspect.iscoroutinefunction(cor):
            kwargs = kwargs_filter(cor, options)
            cors = []
            for key in keys:
                if not hasattr(cor, '__self__'):  # coroutine function has not bound to instance
                    cors.append(cor(executor, key, **kwargs))  # bound executor to self
                else:
                    cors.append(cor(key, **kwargs))
                logger.debug(f"auto assemble {cor} by {kwargs}")
            cor = asyncio.gather(*cors)
        return executor, cor

    return wrapped


def longest_common_len(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_length = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                max_length = max(max_length, dp[i][j])
    return max_length


def find_sites():
    sites_path = Path(__file__).parent.parent / 'sites'
    for site in sites_path.iterdir():
        if not site.is_dir() or not (site / '__init__.py').exists():
            continue
        yield site


def assign(cli_kwargs):
    method = cli_kwargs.pop('method')
    keys = cli_kwargs.pop('keys')
    options = cli_kwargs
    modules = [
        # path, cmp_key
        ('download.base_downloader_m3u8', 'm3u8'),
        ('download.base_downloader_part', 'file'),
    ]
    for site in find_sites():
        modules.append((f"sites.{site.name}", site.name))
    pattern = re.compile(r"https?://(?:[\w-]*\.)?([\w-]+)\.([\w-]+)")
    if g := pattern.search(keys[0]):
        cmp_base = g.group(1)
    else:
        cmp_base = keys[0]

    def key(x: Tuple[str, str]):
        if x[0].startswith("sites"):
            return longest_common_len(cmp_base, x[-1])
        else:  # base_downloader
            return longest_common_len(method, x[-1])

    for module, _ in sorted(modules, key=key, reverse=True):
        a = time.time()
        try:
            module = import_module(f"bilix.{module}")
        except ImportError as e:
            logger.debug(f"duo to ImportError <{e}>, skip <module 'bilix.{module}'>")
            continue
        logger.debug(f"import cost {time.time() - a:.6f} s <module '{module.__name__}'>")
        exc = None
        for handle_func in module_handle_funcs(module):
            try:
                res = handle_func(method, keys, options)
            except HandleMethodError as e:
                exc = e
                continue
            if res is NotImplemented or res is None:
                continue
            executor, cor = res
            logger.debug(f"Assign to {executor.__class__.__name__}")
            return executor, cor
        if exc is not None:  # for the module, some handler can handle, but method miss match
            raise exc
    raise HandleError(f"Can't find any handler for method: '{method}' keys: {keys}")
