"""
find and assign handler class for command line interface
"""
from dataclasses import dataclass
from itertools import chain
import re
import time
from pathlib import Path
from types import ModuleType
from typing import List
from importlib import import_module
from click import UsageError
import bilix
from bilix.cli.handler import Handler
from bilix.log import logger


def longest_common_len(str1: str, str2: str) -> int:
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_length = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                max_length = max(max_length, dp[i][j])
    return max_length


@dataclass
class ModuleInfo:
    module_path: str
    cmp_key: str


def sites_module_infos():
    sites_path = Path(bilix.__file__).parent / 'sites'
    for site in sites_path.iterdir():
        if not site.is_dir() or not (site / '__init__.py').exists():
            continue
        yield ModuleInfo(f'bilix.sites.{site.name}', site.name)


def base_module_infos():
    infos = (
        ModuleInfo('bilix.download.base_downloader_m3u8', cmp_key='m3u8'),
        ModuleInfo('bilix.download.base_downloader_part', cmp_key='file'),
        ModuleInfo('bilix.download.auto_downloader', cmp_key='autov'),
    )
    for info in infos:
        yield info


def sorted_modules(method: str, keys: List[str]) -> List[ModuleInfo]:
    pattern = re.compile(r"https?://(?:[\w-]*\.)?([\w-]+)\.([\w-]+)")
    if g := pattern.search(keys[0]):
        cmp_base = g.group(1)
    else:
        cmp_base = keys[0]

    def key(info: ModuleInfo):
        if "sites" in info.module_path:
            return longest_common_len(cmp_base, info.cmp_key)
        else:
            return longest_common_len(method, info.cmp_key)

    infos = chain(base_module_infos(), sites_module_infos())
    return sorted(infos, key=key, reverse=True)


def handler_classes(module: ModuleType):
    """find and yield all available handler class in module"""
    attrs = getattr(module, '__all__', None)
    if attrs is None:
        attrs = dir(module)
    for attr_name in attrs:
        if attr_name.startswith('_'):
            continue
        handler_cls = getattr(module, attr_name)
        try:
            if not issubclass(handler_cls, Handler):
                continue
        except TypeError:
            continue
        yield handler_cls


def assign(method: str, keys: List[str]) -> Handler:
    if len(keys) == 0:
        raise UsageError("at least one key is required")
    for module_info in sorted_modules(method, keys):
        a = time.time()
        try:
            module = import_module(module_info.module_path)
        except ImportError as e:
            logger.debug(f"duo to ImportError <{e}>, skip <module '{module_info.module_path}'>")
            continue
        logger.debug(f"import cost {time.time() - a:.6f} s <module '{module.__name__}'>")
        exc = None
        for handler_cls in handler_classes(module):
            if handler_cls.decide_handle(method, keys):
                if method not in handler_cls.cli_info:
                    exc = UsageError(f"For {handler_cls.__name__} method '{method}' is not available")
                    continue
                logger.debug(f"Assign to {handler_cls.__name__}")
                return handler_cls
        if exc is not None:  # for the module, some handler can handle, but method miss match
            raise exc
    raise UsageError(f"Can't find any handler for method: '{method}' keys: {keys}")
