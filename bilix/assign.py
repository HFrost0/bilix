from typing import Union, Coroutine, Tuple
from bilix.handle import Handler
from bilix.log import logger
from bilix.download.base_downloader import BaseDownloader
from bilix.info.base_informer import BaseInformer


def assign(**kwargs) -> Tuple[Union[BaseDownloader, BaseInformer], Coroutine]:
    bili_handler = Handler.registered.pop('bilibili')
    for name, handle in Handler.registered.items():
        if res := handle(**kwargs):
            logger.debug(f"Assign to {name}")
            return res
    # since bilix is originally designed for bilibili, finally use bilibili handler
    return bili_handler(**kwargs)
