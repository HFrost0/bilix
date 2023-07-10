import asyncio
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Union, Annotated, List, Tuple, Callable, Dict
import httpx
from rich import print as rprint
from bilix.download.base_downloader_m3u8 import BaseDownloaderM3u8
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.download.utils import path_check, parse_speed_str, str2path, parse_time_range
from bilix.progress.abc import Progress
from bilix.download.utils import req_retry
from bilix.utils import legal_title

__all__ = ['AutoDownloader']


class HTMLStrategy(Enum):
    NORMAL = 'normal'
    BROWSER = 'browser'
    FILE = 'file'


class AutoDownloader(BaseDownloaderM3u8, BaseDownloaderPart):
    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Annotated[float, parse_speed_str] = None,
            stream_retry: int = 5,
            progress: Progress = None,
            logger: logging.Logger = None,
            part_concurrency: int = 10,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
    ):
        super().__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
            video_concurrency=video_concurrency,
        )

    def _find_video_tag_urls(self, html: str) -> List[str]:
        """find video srcs in html"""
        video_srcs = re.findall(r'<video[^>]*src=[\'"](http[^\'"]*)', html)
        video_srcs = set(video_srcs)  # remove duplicate
        return list(video_srcs)

    def _find_m3u8_urls(self, html: str) -> List[str]:
        m3u8_urls = re.findall(r'https?://[^\'"]+\.m3u8(?:\?[^\'"]+)?', html)
        m3u8_urls = set(m3u8_urls)  # remove duplicate
        return list(m3u8_urls)

    def _find_mp4_urls(self, html: str) -> List[str]:
        mp4_urls = re.findall(r'https?://[^\'"]+\.mp4(?:\?[^\'"]+)?', html)
        mp4_urls = set(mp4_urls)  # remove duplicate
        return list(mp4_urls)

    def _find_title(self, html: str) -> str:
        """find html title"""
        title = re.findall(r'<title>([^<]+)</title>', html)[0]
        title = legal_title(title)
        return title

    @property
    def _find_strategies(self) -> Dict[Callable[[str], List[str]], Callable]:
        return {
            self._find_m3u8_urls: self.get_m3u8_video,
            self._find_video_tag_urls: self.get_file,
            self._find_mp4_urls: self.get_file,
        }

    def _find_referer(self, url: str) -> str:
        """find referer domain in url"""
        referer = re.findall(r'https?://\S+/', url)[0]
        return referer

    async def _get_html(self, url: str, html_strategy: HTMLStrategy, html_path: Path = None) -> str:
        if html_strategy == HTMLStrategy.NORMAL.value:
            res = await req_retry(self.client, url)
            html = res.text
            return html
        elif html_strategy == HTMLStrategy.FILE.value:
            assert html_path is not None, 'html_path must be provided when html_strategy is file'
            with open(html_path, 'r') as f:
                html = f.read()
            return html
        elif html_strategy == HTMLStrategy.BROWSER.value:
            from selenium import webdriver
            with webdriver.Chrome() as browser:
                browser.get(url)
                html = browser.page_source
            return html

    async def auto_get_video(self, url: str, path: Annotated[Path, str2path] = Path('.'),
                             ask: bool = False,
                             html_strategy: HTMLStrategy = HTMLStrategy.NORMAL.value,
                             html_path: Annotated[Path, str2path] = None,
                             ):
        """
        auto find and get video from a html page
        :cli short: autov
        :param url: html url
        :param path: download dir
        :param ask: if there is more than one predicted video url, ask before download
        :param html_strategy: how to get html
        :param html_path: html file path, if provided and html_strategy is file, parse html from file instead of url
        :return:
        """
        html = await self._get_html(url, html_strategy, html_path)
        self.client.headers['referer'] = self._find_referer(url)
        title = self._find_title(html)
        file_path = (path / title).with_suffix('.mp4')
        exist, file_path = path_check(file_path)
        if exist:
            self.logger.exist(file_path.name)
            return file_path

        cor = None
        for find_strategy, download_func in self._find_strategies.items():
            video_urls = find_strategy(html)
            if len(video_urls) > 1 or ask:
                self.logger.info(f"For {title}, found {len(video_urls)} url by strategy {find_strategy.__name__},"
                                 f" you can choose one in: ")
                d = {idx: video_url for idx, video_url in enumerate(video_urls)}
                rprint(d)
                pre_status = self.progress._progress.disable
                self.progress.stop()
                n = int(input('Your choice [num]: '))
                if n not in d:
                    continue
                video_url = d[n]
                cor = download_func(video_url, (path / title).with_suffix('.mp4'))
                if not pre_status:
                    self.progress.start()
            elif len(video_urls) == 1:
                cor = download_func(video_urls[0], (path / title).with_suffix('.mp4'))
            else:
                self.logger.debug(f"no urls found by strategy: {find_strategy.__name__}")
            if cor is not None:
                break
        else:
            self.logger.error("no m3u8 or mp4 urls found")
            return
        return await cor
