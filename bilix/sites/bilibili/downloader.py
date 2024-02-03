import asyncio
import functools
import re
from pathlib import Path
from typing import Union, Sequence, Tuple, List
import aiofiles
import httpx
from datetime import datetime, timedelta
from . import api
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix._process import SingletonPPE
from bilix.utils import legal_title, cors_slice, valid_sess_data, t2s, json2srt
from bilix.download.utils import req_retry, path_check
from bilix.exception import HandleMethodError, APIUnsupportedError, APIResourceError, APIError
from bilix.cli.assign import kwargs_filter, auto_assemble
from bilix import ffmpeg

from danmakuC.bilibili import proto2ass


class DownloaderBilibili(BaseDownloaderPart):
    cookie_domain = "bilibili.com"  # for load cookies quickly
    pattern = re.compile(r"^https?://([A-Za-z0-9-]+\.)*(bilibili\.com|b23\.tv)")

    def __init__(
            self,
            *,
            client: httpx.AsyncClient = None,
            browser: str = None,
            speed_limit: Union[float, int, None] = None,
            stream_retry: int = 5,
            progress=None,
            logger=None,
            part_concurrency: int = 10,
            # unique params
            sess_data: str = None,
            video_concurrency: Union[int, asyncio.Semaphore] = 3,
            hierarchy: bool = True,
    ):
        """

        :param client:
        :param browser:
        :param speed_limit:
        :param stream_retry:
        :param progress:
        :param logger:
        :param sess_data: bilibili SESSDATA cookie
        :param part_concurrency: 媒体分段并发数
        :param video_concurrency: 视频并发数
        :param hierarchy: 是否使用层级目录
        """
        client = client or httpx.AsyncClient(**api.dft_client_settings)
        super(DownloaderBilibili, self).__init__(
            client=client,
            browser=browser,
            speed_limit=speed_limit,
            stream_retry=stream_retry,
            progress=progress,
            logger=logger,
            part_concurrency=part_concurrency,
        )
        client.cookies.set('SESSDATA', valid_sess_data(sess_data))
        self._cate_meta = None
        self.v_sema = asyncio.Semaphore(video_concurrency)
        self.api_sema = asyncio.Semaphore(video_concurrency)
        self.hierarchy = hierarchy
        self.title_overflow = 50

    @classmethod
    def parse_url(cls, url: str):
        if re.match(r'https://space\.bilibili\.com/\d+/favlist\?fid=\d+', url):
            return cls.get_favour
        elif re.match(r'https://space\.bilibili\.com/\d+/channel/seriesdetail\?sid=\d+', url):
            return cls.get_collect_or_list
        elif re.match(r'https://space\.bilibili\.com/\d+/channel/collectiondetail\?sid=\d+', url):
            return cls.get_collect_or_list
        elif re.match(r'https://space\.bilibili\.com/\d+', url):  # up space url
            return cls.get_up
        elif re.search(r'(www\.bilibili\.com)|(b23\.tv)', url):
            return cls.get_video
        raise ValueError(f'{url} no match for bilibili')

    async def get_collect_or_list(self, url, path=Path('.'),
                                  quality=0, image=False, subtitle=False, dm=False, only_audio=False, codec: str = ''):
        """
        下载合集或视频列表
        :cli: short: col
        :param url: 合集或视频列表详情页url
        :param path: 保存路径
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param codec:
        :return:
        """
        if 'series' in url:
            list_name, up_name, bvids = await api.get_list_info(self.client, url)
            name = legal_title(f"【视频列表】{up_name}", list_name)
        elif 'collection' in url:
            col_name, up_name, bvids = await api.get_collect_info(self.client, url)
            name = legal_title(f"【合集】{up_name}", col_name)
        else:
            raise ValueError(f'{url} invalid for get_collect_or_list')
        if self.hierarchy:
            path /= name
            path.mkdir(parents=True, exist_ok=True)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i}", path=path, quality=quality, codec=codec,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio)
              for i in bvids])

    async def get_favour(self, url_or_fid, path=Path('.'),
                         num=20, keyword='', quality=0, series=True, image=False, subtitle=False,
                         dm=False, only_audio=False, codec: str = ''):
        """
        下载收藏夹内的视频
        :cli: short: fav
        :param url_or_fid: 收藏夹url或收藏夹id
        :param path: 保存路径
        :param num: 下载数量
        :param keyword: 搜索关键词
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec:
        :return:
        """
        fav_name, up_name, total_size, bvids = await api.get_favour_page_info(self.client, url_or_fid, keyword=keyword)
        if self.hierarchy:
            name = legal_title(f"【收藏夹】{up_name}-{fav_name}")
            path /= name
            path.mkdir(parents=True, exist_ok=True)
        total = min(total_size, num)
        ps = 20
        page_nums = total // ps + min(1, total % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                num = total - (page_nums - 1) * ps
            else:
                num = ps
            cors.append(self._get_favor_by_page(
                url_or_fid, path, i + 1, num, keyword, quality, series, image, subtitle, dm, only_audio, codec=codec))
        await asyncio.gather(*cors)

    async def _get_favor_by_page(self, url_or_fid, path: Path, pn=1, num=20, keyword='', quality=0,
                                 series=True, image=False, subtitle=False, dm=False, only_audio=False, codec=''):
        ps = 20
        num = min(ps, num)
        _, _, _, bvids = await api.get_favour_page_info(self.client, url_or_fid, pn, ps, keyword)
        cors = []
        for i in bvids[:num]:
            func = self.get_series if series else self.get_video
            # noinspection PyArgumentList
            cors.append(func(f'https://www.bilibili.com/video/{i}', path=path, quality=quality, codec=codec,
                             image=image, subtitle=subtitle, dm=dm, only_audio=only_audio))
        await asyncio.gather(*cors)

    @property
    async def cate_meta(self):
        if not self._cate_meta:
            self._cate_meta = asyncio.ensure_future(api.get_cate_meta(self.client))
            self._cate_meta = await self._cate_meta
        elif asyncio.isfuture(self._cate_meta):
            await self._cate_meta
        return self._cate_meta

    async def get_cate(self, cate_name: str, path=Path('.'), num=10, order='click', keyword='', days=7,
                       quality=0, series=True, image=False, subtitle=False, dm=False, only_audio=False, codec='', ):
        """
        下载分区视频
        :cli: short: cate
        :param cate_name: 分区名称
        :param path: 保存路径
        :param num: 下载数量
        :param order: 何种排序，click播放数，scores评论数，stow收藏数，coin硬币数，dm弹幕数
        :param keyword: 搜索关键词
        :param days: 过去days天中的结果
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec:
        :return:
        """
        cate_meta = await self.cate_meta
        if cate_name not in cate_meta:
            return self.logger.error(f'未找到分区 {cate_name}')
        if 'subChannelId' not in cate_meta[cate_name]:
            sub_names = [i['name'] for i in cate_meta[cate_name]['sub']]
            return self.logger.error(f'{cate_name} 是主分区，仅支持子分区，试试 {sub_names}')
        if self.hierarchy:
            path /= legal_title(f"【分区】{cate_name}")
            path.mkdir(parents=True, exist_ok=True)
        cate_id = cate_meta[cate_name]['tid']
        time_to = datetime.now()
        time_from = time_to - timedelta(days=days)
        time_from, time_to = time_from.strftime('%Y%m%d'), time_to.strftime('%Y%m%d')
        pagesize = 30
        page = 1
        cors = []
        while num > 0:
            cors.append(self._get_cate_by_page(
                cate_id, path, time_from, time_to, page, min(pagesize, num), order, keyword, quality,
                series, image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, codec=codec))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_by_page(
            self, cate_id, path: Path, time_from, time_to, pn=1, num=30, order='click', keyword='',
            quality=0, series=True, image=False, subtitle=False, dm=False, only_audio=False, codec=''):
        bvids = await api.get_cate_page_info(self.client, cate_id, time_from, time_to, pn, 30, order, keyword)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        cors = [func(f"https://www.bilibili.com/video/{i}", path=path, quality=quality, codec=codec,
                     image=image, subtitle=subtitle, dm=dm, only_audio=only_audio)
                for i in bvids]
        await asyncio.gather(*cors)

    async def get_up(
            self, url_or_mid: str, path=Path('.'), num=10, order='pubdate', keyword='', quality=0,
            series=True, image=False, subtitle=False, dm=False, only_audio=False, codec='', ):
        """
        下载up主视频
        :cli: short: up
        :param url_or_mid: b站用户空间页面url 或b站用户id，在空间页面的url中可以找到
        :param path: 保存路径
        :param num: 下载总数
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec:
        :return:
        """
        ps = 30
        up_name, total_size, bv_ids = await api.get_up_video_info(self.client, url_or_mid, 1, ps, order, keyword)
        if self.hierarchy:
            path /= legal_title(f"【up】{up_name}")
            path.mkdir(parents=True, exist_ok=True)
        num = min(total_size, num)
        page_nums = num // ps + min(1, num % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                p_num = num - (page_nums - 1) * ps
            else:
                p_num = ps
            cors.append(self._get_up_by_page(
                url_or_mid, path, i + 1, p_num, order, keyword, quality, series, image=image,
                subtitle=subtitle, dm=dm, only_audio=only_audio, codec=codec))
        await asyncio.gather(*cors)

    async def _get_up_by_page(self, url_or_mid, path: Path, pn=1, num=30, order='pubdate', keyword='', quality=0,
                              series=True, image=False, subtitle=False, dm=False, only_audio=False, codec='', ):
        ps = 30
        num = min(ps, num)
        _, _, bvids = await api.get_up_video_info(self.client, url_or_mid, pn, ps, order, keyword)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        await asyncio.gather(
            *[func(f'https://www.bilibili.com/video/{bv}', path=path, quality=quality, codec=codec,
                   image=image, subtitle=subtitle, dm=dm, only_audio=only_audio) for bv in bvids])

    async def get_series(self, url: str, path=Path('.'),
                         quality: Union[str, int] = 0, image=False, subtitle=False,
                         dm=False, only_audio=False, p_range: Sequence[int] = None, codec: str = ''):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法
        :cli: short: s
        :param url: 系列中任意一个视频的url
        :param path: 保存路径
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param p_range: 下载集数范围，例如(1, 3)：P1至P3
        :param codec: 视频编码（可通过info获取）
        :return:
        """
        try:
            async with self.api_sema:
                video_info = await api.get_video_info(self.client, url)
        except (APIResourceError, APIUnsupportedError) as e:
            return self.logger.warning(e)
        if self.hierarchy and len(video_info.pages) > 1:
            path /= video_info.title
            path.mkdir(parents=True, exist_ok=True)
        cors = [self.get_video(p.p_url, path=path,
                               quality=quality, image=image, subtitle=subtitle, dm=dm,
                               only_audio=only_audio, codec=codec,
                               video_info=video_info if idx == video_info.p else None)
                for idx, p in enumerate(video_info.pages)]
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, path=Path('.'),
                        quality: Union[str, int] = 0, image=False, subtitle=False, dm=False, only_audio=False,
                        codec: str = '', time_range: Tuple[int, int] = None, video_info: api.VideoInfo = None):
        """
        下载单个视频
        :cli: short: v
        :param url: 视频的url
        :param path: 保存路径
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec: 视频编码（可通过codec获取）
        :param time_range: 切片的时间范围
        :param video_info: 额外数据，提供时不用再次请求页面
        :return:
        """
        async with self.v_sema:
            if not video_info:
                try:
                    video_info = await api.get_video_info(self.client, url)
                except (APIResourceError, APIUnsupportedError) as e:
                    return self.logger.warning(e)
            p_name = legal_title(video_info.pages[video_info.p].p_name)
            task_name = legal_title(video_info.title, p_name)
            # if title is too long, use p_name as base_name
            base_name = p_name if len(video_info.title) > self.title_overflow and self.hierarchy and p_name else \
                task_name
            media_name = base_name if not time_range else legal_title(base_name, *map(t2s, time_range))
            media_cors = []
            task_id = await self.progress.add_task(total=None, description=task_name)
            if video_info.dash:
                try:  # choose video quality
                    video, audio = video_info.dash.choose_quality(quality, codec)
                except KeyError:
                    self.logger.warning(
                        f"{task_name} 清晰度<{quality}> 编码<{codec}>不可用，请检查输入是否正确或是否需要大会员")
                else:
                    tmp: List[Tuple[api.Media, Path]] = []
                    # 1. only video
                    if not audio and not only_audio:
                        tmp.append((video, path / f'{media_name}.mp4'))
                    # 2. video and audio
                    elif audio and not only_audio:
                        exists, media_path = path_check(path / f'{media_name}.mp4')
                        if exists:
                            self.logger.info(f'[green]已存在[/green] {media_path.name}')
                        else:
                            tmp.append((video, path / f'{media_name}-v'))
                            tmp.append((audio, path / f'{media_name}-a'))
                            # task need to be merged
                            await self.progress.update(task_id=task_id, upper=ffmpeg.combine)
                    # 3. only audio
                    elif audio and only_audio:
                        tmp.append((audio, path / f'{media_name}{audio.suffix}'))
                    else:
                        self.logger.warning(f"No audio for {task_name}")
                    # convert to coroutines
                    if not time_range:
                        media_cors.extend(self.get_file(t[0].urls, path=t[1], task_id=task_id) for t in tmp)
                    else:
                        if len(tmp) > 0:
                            fut = asyncio.Future()  # to fix key frame
                            v = tmp[0]
                            media_cors.append(self.get_media_clip(v[0].urls, v[1], time_range,
                                                                  init_range=v[0].segment_base['initialization'],
                                                                  seg_range=v[0].segment_base['index_range'],
                                                                  set_s=fut,
                                                                  task_id=task_id))
                        if len(tmp) > 1:  # with audio
                            a = tmp[1]
                            media_cors.append(self.get_media_clip(a[0].urls, a[1], time_range,
                                                                  init_range=a[0].segment_base['initialization'],
                                                                  seg_range=a[0].segment_base['index_range'],
                                                                  get_s=fut,
                                                                  task_id=task_id))

            elif video_info.other:
                self.logger.warning(
                    f"{task_name} 未解析到dash资源，转入durl mp4/flv下载（不需要会员的电影/番剧预览，不支持dash的视频）")
                media_name = base_name
                if len(video_info.other) == 1:
                    m = video_info.other[0]
                    media_cors.append(
                        self.get_file(m.urls, path=path / f'{media_name}.{m.suffix}', task_id=task_id))
                else:
                    exist, media_path = path_check(path / f'{media_name}.mp4')
                    if exist:
                        self.logger.info(f'[green]已存在[/green] {media_path.name}')
                    else:
                        p_sema = asyncio.Semaphore(self.part_concurrency)

                        async def _get_file(media: api.Media, p: Path) -> Path:
                            async with p_sema:
                                return await self.get_file(media.urls, path=p, task_id=task_id)

                        for i, m in enumerate(video_info.other):
                            f = f'{media_name}-{i}.{m.suffix}'
                            media_cors.append(_get_file(m, path / f))
                        await self.progress.update(task_id=task_id, upper=ffmpeg.concat)
            else:
                self.logger.warning(f'{task_name} 需要大会员或该地区不支持')
            # additional task
            add_cors = []
            if image or subtitle or dm:
                extra_path = path / "extra" if self.hierarchy else path
                extra_path.mkdir(exist_ok=True)
                if image:
                    add_cors.append(self.get_static(video_info.img_url, path=extra_path / base_name))
                if subtitle:
                    add_cors.append(self.get_subtitle(url, path=extra_path, video_info=video_info))
                if dm:
                    try:
                        width, height = video.width, video.height
                    except UnboundLocalError:
                        width, height = 1920, 1080
                    add_cors.append(self.get_dm(
                        url, path=extra_path, convert_func=self._dm2ass_factory(width, height), video_info=video_info))
            path_lst, _ = await asyncio.gather(asyncio.gather(*media_cors), asyncio.gather(*add_cors))

        if upper := self.progress.tasks[task_id].fields.get('upper', None):
            await upper(path_lst, media_path)
            self.logger.info(f'[cyan]已完成[/cyan] {media_path.name}')
        await self.progress.update(task_id, visible=False)

    @staticmethod
    def _dm2ass_factory(width: int, height: int):
        async def dm2ass(protobuf_bytes: bytes) -> bytes:
            loop = asyncio.get_event_loop()
            f = functools.partial(proto2ass, protobuf_bytes, width, height, font_size=width / 40, )
            content = await loop.run_in_executor(SingletonPPE(), f)
            return content.encode('utf-8')

        return dm2ass

    async def get_dm(self, url, path=Path('.'), update=False, convert_func=None, video_info=None):
        """
        下载视频的弹幕
        :cli: short: dm
        :param url: 视频url
        :param path: 保存路径
        :param update: 是否更新覆盖之前下载的弹幕文件
        :param convert_func:
        :param video_info: 额外数据，提供则不再访问前端
        :return:
        """
        if not video_info:
            video_info = await api.get_video_info(self.client, url)
        aid, cid = video_info.aid, video_info.cid
        file_type = '.' + ('pb' if not convert_func else convert_func.__name__.split('2')[-1])
        p_name = video_info.pages[video_info.p].p_name
        # to avoid file name too long bug
        if len(video_info.title) > self.title_overflow and self.hierarchy and p_name:
            file_name = legal_title(p_name, "弹幕") + file_type
        else:
            file_name = legal_title(video_info.title, p_name, "弹幕") + file_type
        file_path = path / file_name
        exist, file_path = path_check(file_path)
        if not update and exist:
            self.logger.info(f"[green]已存在[/green] {file_name}")
            return file_path
        dm_urls = await api.get_dm_urls(self.client, aid, cid)
        cors = [req_retry(self.client, dm_url) for dm_url in dm_urls]
        results = await asyncio.gather(*cors)
        content = b''.join(res.content for res in results)
        content = convert_func(content) if convert_func else content
        if asyncio.iscoroutine(content):
            content = await content
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        self.logger.info(f"[cyan]已完成[/cyan] {file_name}")
        return file_path

    async def get_subtitle(self, url, path=Path('.'), convert_func=json2srt, video_info=None):
        """
        下载视频的字幕文件
        :cli: short: sub
        :param url: 视频url
        :param path: 字幕文件保存路径
        :param convert_func: function used to convert original subtitle text
        :param video_info: 额外数据，提供则不再访问前端
        :return:
        """
        if not video_info:
            video_info = await api.get_video_info(self.client, url)
        p, cid = video_info.p, video_info.cid
        p_name = video_info.pages[p].p_name
        try:
            subtitles = await api.get_subtitle_info(self.client, video_info.bvid, cid)
        except APIError as e:
            return self.logger.warning(e)
        cors = []

        for sub_url, sub_name in subtitles:
            if len(video_info.title) > self.title_overflow and self.hierarchy and p_name:
                file_name = legal_title(p_name, sub_name)
            else:
                file_name = legal_title(video_info.title, p_name, sub_name)
            cors.append(self.get_static(sub_url, path / file_name, convert_func=convert_func))
        paths = await asyncio.gather(*cors)
        return paths

    @classmethod
    @auto_assemble
    def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
        if cls.pattern.match(keys[0]) or method == 'cate' or method == 'get_cate':
            if method in {'auto', 'a'}:
                m = cls.parse_url(keys[0])
            elif method in cls._cli_map:
                m = cls._cli_map[method]
            else:
                raise HandleMethodError(cls, method=method)
            d = cls(sess_data=options['cookie'], **kwargs_filter(cls, options))
            return d, m
