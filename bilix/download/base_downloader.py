from typing import Union
import aiofiles
import httpx
import os
from bilix.utils import req_retry
from bilix.log import logger
from bilix.progress import CLIProgress, BaseProgress


class BaseDownloader:
    def __init__(self, client: httpx.AsyncClient, videos_dir='videos', speed_limit: Union[float, int] = None,
                 progress: BaseProgress = None):
        """

        :param client: client used for http request
        :param videos_dir: download to which directory, default to ./videos, if not exists will be auto created
        :param speed_limit: global download rate for the downloader, should be a number (Byte/s unit)
        :param progress: progress obj
        """
        self.client = client
        self.videos_dir = videos_dir
        self.speed_limit = speed_limit
        if not os.path.exists(self.videos_dir):
            os.makedirs(videos_dir)
        if progress is None:
            # if no progress_cls provided by upper class, use cli progress by default
            self.progress = CLIProgress(holder=self)
        else:
            self.progress = progress
            progress.holder = self

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        await self.client.aclose()

    def _make_hierarchy_dir(self, hierarchy: Union[bool, str], add_dir: str):
        """
        Make and return new hierarchy according to old hierarchy and add dir

        :param hierarchy: current hierarchy, if True means add_dir becomes new hierarchy
        :param add_dir: new dir add to hierarchy
        :return:
        """
        assert hierarchy is True or (type(hierarchy) is str and len(hierarchy) > 0) and len(add_dir) > 0
        hierarchy = add_dir if hierarchy is True else f'{hierarchy}/{add_dir}'
        if not os.path.exists(f'{self.videos_dir}/{hierarchy}'):
            os.makedirs(f'{self.videos_dir}/{hierarchy}')
        return hierarchy

    async def _get_static(self, url, name, convert_func=None, hierarchy: str = '') -> str:
        """

        :param url:
        :param name: file name (with file type)
        :param convert_func: function used to convert res.content, must be named like ...2...
        :return:
        """
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if convert_func:
            file_type = '.' + convert_func.__name__.split('2')[-1]  #
        else:
            file_type = f".{url.split('.')[-1]}" if len(url.split('/')[-1].split('.')) > 1 else ''
            file_type = file_type.split('?')[0]
        file_name = name + file_type
        file_path = f'{file_dir}/{file_name}'
        if os.path.exists(file_path):
            logger.info(f'[green]已存在[/green] {file_name}')  # extra file use different color
        else:
            res = await req_retry(self.client, url)
            content = convert_func(res.content) if convert_func else res.content
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            logger.info(f'[cyan]已完成[/cyan] {name + file_type}')  # extra file use different color
        return file_path
