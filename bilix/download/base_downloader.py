from typing import Union
import aiofiles
import httpx
import os
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn, TextColumn
from bilix.utils import req_retry
from bilix.log import logger


class BaseDownloader:
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.percentage:>4.1f}%"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        'ETA',
        TimeRemainingColumn(), transient=True
    )

    def __init__(self, client: httpx.AsyncClient, videos_dir='videos'):
        """

        :param client:
        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        """
        self.client = client
        self.videos_dir = videos_dir
        if not os.path.exists(self.videos_dir):
            os.makedirs(videos_dir)
        self.progress.start()

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        self.progress.stop()
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
