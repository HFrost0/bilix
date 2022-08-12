import asyncio
from typing import Union, Sequence
import httpx
import random
from datetime import datetime, timedelta
import os
from anyio import run_process
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby
import bilix.api.bilibili as api
from bilix.subtitle import json2srt
from bilix.dm import dm2ass_factory
from bilix.utils import legal_title, req_retry
from bilix.log import log


class Downloader:
    def __init__(self, videos_dir='videos', sess_data='', video_concurrency=3, part_concurrency=10, http2=True):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
        :param video_concurrency: 限制最大同时下载的视频数量
        :param part_concurrency: 每个媒体的分段并发数
        :param http2: 是否使用http2协议
        """
        # assert video_concurrency * part_concurrency <= 100
        self.videos_dir = videos_dir
        if not os.path.exists(self.videos_dir):
            os.makedirs(videos_dir)
        cookies = {'SESSDATA': sess_data}
        headers = {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}
        self.client = httpx.AsyncClient(headers=headers, cookies=cookies, http2=http2)
        self.progress = Progress(
            "{task.description}",
            "{task.percentage:>3.0f}%",
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            'ETA',
            TimeRemainingColumn(), transient=True)
        self.progress.start()
        self.sema = asyncio.Semaphore(video_concurrency)
        self.part_concurrency = part_concurrency
        self._cate_meta = None

    async def aclose(self):
        self.progress.stop()
        await self.client.aclose()

    def _make_hierarchy_dir(self, hierarchy: Union[bool, str], add_dir: str):
        """Make and return new hierarchy according to old hierarchy and add name"""
        assert hierarchy is True or (type(hierarchy) is str and len(hierarchy) > 0) and len(add_dir) > 0
        hierarchy = add_dir if hierarchy is True else f'{hierarchy}/{add_dir}'
        if not os.path.exists(f'{self.videos_dir}/{hierarchy}'):
            os.makedirs(f'{self.videos_dir}/{hierarchy}')
        return hierarchy

    async def get_collect_or_list(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                                  hierarchy: Union[bool, str] = True):
        """
        下载合集或视频列表

        :param url: 合集或视频列表详情页url
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param hierarchy: 是否使用层次目录保存文件
        :return:
        """
        if 'seriesdetail' in url:
            await self.get_list(url, quality, image, subtitle, dm, only_audio, hierarchy)
        elif 'collectiondetail' in url:
            await self.get_collect(url, quality, image, subtitle, dm, only_audio, hierarchy)
        else:
            raise Exception(f'未知的详情页 {url}')

    async def get_list(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                       hierarchy: Union[bool, str] = True):
        """
        下载视频列表

        :param url: 列表详情页url
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param hierarchy:
        :return:
        """
        list_name, up_name, bvids = await api.get_list_info(url, self.client)
        if hierarchy:
            name = legal_title(f"【视频列表】{up_name}-{list_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i}", quality=quality,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in bvids])

    async def get_collect(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                          hierarchy: Union[bool, str] = True):
        """
        下载合集

        :param url: 合集详情页url
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :return:
        """
        col_name, up_name, bvids = api.get_collect_info(url, self.client)
        if hierarchy:
            name = legal_title(f"【合集】{up_name}-{col_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i}", quality=quality,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in bvids])

    async def get_favour(self, fid, num=20, keyword='', quality=0, series=True, image=False, subtitle=False, dm=False,
                         only_audio=False, hierarchy: Union[bool, str] = True):
        """
        下载收藏夹内的视频

        :param fid: 收藏夹id
        :param num: 下载数量
        :param keyword: 搜索关键词
        :param quality:
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :return:
        """
        fav_name, up_name, total_size, bvids = await api.get_favour_page_info(fid, keyword=keyword, client=self.client)
        if hierarchy:
            name = legal_title(f"【收藏夹】{up_name}-{fav_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        total = min(total_size, num)
        ps = 20
        page_nums = total // ps + min(1, total % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                num = total - (page_nums - 1) * ps
            else:
                num = ps
            cors.append(self._get_favor_by_page(fid, i + 1, num, keyword, quality, series,
                                                image, subtitle, dm, only_audio, hierarchy=hierarchy))
        await asyncio.gather(*cors)

    async def _get_favor_by_page(self, fid, pn=1, num=20, keyword='', quality=0, series=True,
                                 image=False, subtitle=False, dm=False, only_audio=False, hierarchy=True):
        ps = 20
        num = min(ps, num)
        _, _, _, bvids = await api.get_favour_page_info(fid, pn, ps, keyword, self.client)
        cors = []
        for i in bvids[:num]:
            func = self.get_series if series else self.get_video
            # noinspection PyArgumentList
            cors.append(func(f'https://www.bilibili.com/video/{i}', quality=quality,
                             image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy))
        await asyncio.gather(*cors)

    @property
    async def cate_meta(self):
        if not self._cate_meta:
            self._cate_meta = asyncio.ensure_future(api.get_cate_meta(self.client))
            self._cate_meta = await self._cate_meta
        elif asyncio.isfuture(self._cate_meta):
            await self._cate_meta
        return self._cate_meta

    async def get_cate_videos(self, cate_name: str, num=10, order='click', keyword='', days=7, quality=0, series=True,
                              image=False, subtitle=False, dm=False, only_audio=False,
                              hierarchy: Union[bool, str] = True):
        """
        下载分区视频

        :param cate_name: 分区名称
        :param num: 下载数量
        :param order: 何种排序，click播放数，scores评论数，stow收藏数，coin硬币数，dm弹幕数
        :param keyword: 搜索关键词
        :param days: 过去days天中的结果
        :param quality: 画面质量
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :return:
        """
        cate_meta = await self.cate_meta
        if cate_name not in cate_meta:
            log.error(f'未找到分区 {cate_name}')
            return
        if 'subChannelId' not in cate_meta[cate_name]:
            sub_names = [i['name'] for i in cate_meta[cate_name]['sub']]
            log.error(f'{cate_name} 是主分区，仅支持子分区，试试 {sub_names}')
            return
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, legal_title(f"【分区】{cate_name}"))
        cate_id = cate_meta[cate_name]['tid']
        time_to = datetime.now()
        time_from = time_to - timedelta(days=days)
        time_from, time_to = time_from.strftime('%Y%m%d'), time_to.strftime('%Y%m%d')
        pagesize = 30
        page = 1
        cors = []
        while num > 0:
            cors.append(
                self._get_cate_videos_by_page(cate_id, time_from, time_to, page, min(pagesize, num), order, keyword,
                                              quality, series, image=image, subtitle=subtitle, dm=dm,
                                              only_audio=only_audio, hierarchy=hierarchy))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_videos_by_page(self, cate_id, time_from, time_to, pn=1, num=30, order='click', keyword='',
                                       quality=0, series=True, image=False, subtitle=False, dm=False,
                                       only_audio=False, hierarchy=True):
        bvids = await api.get_cate_page_info(cate_id, time_from, time_to, pn, 30, order, keyword, self.client)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        cors = [func(f"https://www.bilibili.com/video/{i}", quality=quality,
                     image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
                for i in bvids]
        await asyncio.gather(*cors)

    async def get_up_videos(self, mid: str, num=10, order='pubdate', keyword='', quality=0, series=True,
                            image=False, subtitle=False, dm=False, only_audio=False,
                            hierarchy: Union[bool, str] = True):
        """

        :param mid: b站用户id，在空间页面的url中可以找到
        :param num: 下载总数
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :return:
        """
        ps = 30
        up_name, total_size, bv_ids = await api.get_up_info(mid, 1, ps, order, keyword, self.client)
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, legal_title(f"【up】{up_name}"))
        num = min(total_size, num)
        page_nums = num // ps + min(1, num % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                p_num = num - (page_nums - 1) * ps
            else:
                p_num = ps
            cors.append(self._get_up_videos_by_page(mid, i + 1, p_num, order, keyword, quality, series,
                                                    image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                                                    hierarchy=hierarchy))
        await asyncio.gather(*cors)

    async def _get_up_videos_by_page(self, mid, pn=1, num=30, order='pubdate', keyword='', quality=0, series=True,
                                     image=False, subtitle=False, dm=False, only_audio=False,
                                     hierarchy=None):
        ps = 30
        num = min(ps, num)
        _, _, bvids = await api.get_up_info(mid, pn, ps, order, keyword, self.client)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        await asyncio.gather(
            *[func(f'https://www.bilibili.com/video/{bv}', quality=quality,
                   image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy) for bv in bvids])

    async def get_series(self, url: str, quality: int = 0, image=False, subtitle=False, dm=False, only_audio=False,
                         p_range: Sequence[int] = None,
                         hierarchy: Union[bool, str] = True):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param url: 系列中任意一个视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param p_range: 下载集数范围，例如(1, 3)：P1至P3
        :param hierarchy:
        :return:
        """
        try:
            video_info = await api.get_video_info(url, self.client)
        except AttributeError as e:
            log.warning(f'{e} {url}')
            return
        title = video_info.title
        pages = video_info.pages
        p = video_info.p
        if len(pages) > 1:
            hierarchy = self._make_hierarchy_dir(hierarchy, title)
        else:
            hierarchy = hierarchy if type(hierarchy) is str else None
        cors = [self.get_video(p_url, quality, add_name,
                               image=True if idx == 0 and image else False,
                               subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy,
                               extra=video_info if idx == p else None)
                for idx, (add_name, p_url) in enumerate(pages)]
        if p_range:
            h, t = p_range[0] - 1, p_range[1]
            assert 0 <= h <= t
            [cor.close() for idx, cor in enumerate(cors) if idx < h or idx >= t]  # avoid runtime warning
            cors = cors[h:t]
        await asyncio.gather(*cors)

    async def get_video(self, url: str, quality: int = 0, add_name='', image=False, subtitle=False, dm=False,
                        only_audio=False, hierarchy: Union[bool, str] = True, extra=None):
        """
        下载单个视频

        :param url: 视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param add_name: 给文件的额外添加名，用户请直接保持默认
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :param extra: 额外数据，提供时不用再次请求页面
        :return:
        """
        await self.sema.acquire()
        if not extra:
            try:
                extra = await api.get_video_info(url, self.client)
            except AttributeError as e:
                log.warning(f'{url} {e}')
                self.sema.release()
                return
        title = extra.h1_title
        title = legal_title(title, add_name)
        dash = extra.dash
        img_url = extra.img_url
        if not dash:
            log.warning(f'{extra.title} 需要大会员或该地区不支持')
            self.sema.release()
            return
        video_info, video_urls = None, None  # avoid ide warning
        # choose quality
        for q, (_, i) in enumerate(groupby(dash['video'], key=lambda x: x['id'])):
            video_info = next(i)
            video_urls = (video_info['base_url'], *(video_info['backup_url'] if video_info['backup_url'] else ()))
            if q == quality:
                break
        audio_info = dash['audio'][0]
        audio_urls = (audio_info['base_url'], *(audio_info['backup_url'] if audio_info['backup_url'] else ()))

        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy and len(hierarchy) > 0 else self.videos_dir
        task_id = self.progress.add_task(
            total=1,
            description=title if len(title) < 33 else f'{title[:15]}...{title[-15:]}', visible=False)
        cors = []
        # add cor according to params
        if not only_audio:
            if os.path.exists(f'{file_dir}/{title}.mp4'):
                log.info(f'[green]已存在[/green] {title}.mp4')
            else:
                cors.append(self._get_media(video_urls, f'{title}-video', task_id, hierarchy))
                cors.append(self._get_media(audio_urls, f'{title}-audio', task_id, hierarchy))
        else:
            cors.append(self._get_media(audio_urls, f'{title}.mp3', task_id, hierarchy))
        # additional task
        if image or subtitle or dm:
            extra_hierarchy = self._make_hierarchy_dir(hierarchy if hierarchy else True, 'extra')
            if image:
                cors.append(self._get_static(img_url, title, hierarchy=extra_hierarchy))
            if subtitle:
                cors.append(self.get_subtitle(url, extra=extra, hierarchy=extra_hierarchy))
            if dm:
                w, h = video_info['width'], video_info['height']
                cors.append(self.get_dm(url, convert_func=dm2ass_factory(w, h), hierarchy=extra_hierarchy, extra=extra))
        await asyncio.gather(*cors)
        self.sema.release()

        if not only_audio and not os.path.exists(f'{file_dir}/{title}.mp4'):
            await run_process(
                ['ffmpeg', '-i', f'{file_dir}/{title}-video', '-i', f'{file_dir}/{title}-audio',
                 '-codec', 'copy', f'{file_dir}/{title}.mp4', '-loglevel', 'quiet'])
            os.remove(f'{file_dir}/{title}-video')
            os.remove(f'{file_dir}/{title}-audio')
        # make progress invisible
        if self.progress.tasks[task_id].visible:
            self.progress.update(task_id, advance=1, visible=False)
            log.info(f'[cyan]已完成[/cyan] {title}{".mp3" if only_audio else ".mp4"}')

    async def get_dm(self, url, update=False, convert_func=None,
                     hierarchy: str = '', extra=None):
        """

        :param url: 视频url
        :param update: 是否更新覆盖之前下载的弹幕文件
        :param convert_func:
        :param hierarchy:
        :param extra: 额外数据，提供则不再访问前端
        :return:
        """
        if not extra:
            extra = await api.get_video_info(url, self.client)
        title = extra.title
        aid, cid = extra.aid, extra.cid

        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        file_type = '.' + ('bin' if not convert_func else convert_func.__name__.split('2')[-1])
        file_name = f"{title}-弹幕{file_type}"
        file_path = f'{file_dir}/{file_name}'
        if not update and os.path.exists(file_path):
            log.info(f"[green]已存在[/green] {file_name}")
            return file_path
        dm_urls = await api.get_dm_info(aid, cid, self.client)
        cors = [req_retry(self.client, dm_url) for dm_url in dm_urls]
        results = await asyncio.gather(*cors)
        content = b''.join(res.content for res in results)
        content = await convert_func(content) if convert_func else content
        with open(file_path, 'wb') as f:
            f.write(content)
        log.info(f"[cyan]已完成[/cyan] {file_name}")
        return file_path

    async def get_subtitle(self, url, convert=True, hierarchy: str = '', extra=None):
        """
        获取某个视频的字幕文件

        :param url: 视频url
        :param extra: {cid:.. title:...}提供则不再请求前端
        :param convert: 是否转换成srt
        :param hierarchy:
        :return:
        """
        if not extra:
            extra = await api.get_video_info(url, self.client)
        bvid = extra.bvid
        p, cid = extra.p, extra.cid
        title = extra.title
        add_name = extra.pages[p][0]
        title = legal_title(title, add_name)
        try:
            subtitles = await api.get_subtitle_info(bvid, cid, self.client)
        except AttributeError as e:
            log.warning(f'{url} {e}')
            return
        cors = []
        for sub_url, sub_name in subtitles:
            file_name = f"{title}-{sub_name}"
            cors.append(self._get_static(sub_url, file_name, convert_func=json2srt if convert else None,
                                         hierarchy=hierarchy))
        paths = await asyncio.gather(*cors)
        return paths

    async def _get_static(self, url, name, convert_func=None, hierarchy: str = '') -> str:
        """

        :param url:
        :param name:
        :param convert_func: function used to convert res.content, must be named like ...2...
        :return:
        """
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if convert_func:
            file_type = '.' + convert_func.__name__.split('2')[-1]  #
        else:
            file_type = f".{url.split('.')[-1]}" if len(url.split('/')[-1].split('.')) > 1 else ''
        file_name = name + file_type
        file_path = f'{file_dir}/{file_name}'
        if os.path.exists(file_path):
            log.info(f'[green]已存在[/green] {file_name}')  # extra file use different color
        else:
            res = await req_retry(self.client, url)
            content = convert_func(res.content) if convert_func else res.content
            with open(file_path, 'wb') as f:
                f.write(content)
            log.info(f'[cyan]已完成[/cyan] {name + file_type}')  # extra file use different color
        return file_path

    async def _content_length(self, url_or_urls) -> int:
        try:
            res = await req_retry(self.client, url_or_urls, method='HEAD')
            total = int(res.headers['Content-Length'])
        except httpx.HTTPStatusError:
            # deal with HEAD 404 bug https://github.com/HFrost0/bilix/issues/16
            res = await req_retry(self.client, url_or_urls, method='GET', headers={'Range': 'bytes=0-1'})
            total = int(res.headers['Content-Range'].split('/')[-1])
        return total

    async def _get_media(self, media_urls: Sequence[str], media_name, task_id, hierarchy: str = ''):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if os.path.exists(f'{file_dir}/{media_name}'):
            log.info(f'[green]已存在[/green] {media_name}')
            return f'{file_dir}/{media_name}'
        total = await self._content_length(media_urls)
        self.progress.update(task_id, total=self.progress.tasks[task_id].total + total, visible=True)
        part_length = total // self.part_concurrency
        cors = []
        part_names = []
        for i in range(self.part_concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < self.part_concurrency - 1 else total - 1
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cors.append(self._get_media_part(media_urls, part_name, task_id, hierarchy=hierarchy))
        await asyncio.gather(*cors)

        def merge():
            try:  # make sure merge will not interrupt by user
                with open(f'{file_dir}/{media_name}', 'wb') as f:
                    for part in part_names:
                        with open(f'{file_dir}/{part}', 'rb') as pf:
                            f.write(pf.read())
            except KeyboardInterrupt:
                log.warning('Interrupt, but waiting for file merge, please try again later')
                merge()
            [os.remove(f'{file_dir}/{part}') for part in part_names]

        merge()
        return f'{file_dir}/{media_name}'

    async def _get_media_part(self, media_urls: Sequence[str], part_name, task_id, exception=0, hierarchy: str = ''):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if exception > 5:
            log.error(f'超过重试次数 {part_name}')
            raise Exception('超过重试次数')
        start, end = map(int, part_name.split('-')[-2:])
        if os.path.exists(f'{file_dir}/{part_name}'):
            downloaded = os.path.getsize(f'{file_dir}/{part_name}')
            start += downloaded
            if exception == 0:
                self.progress.update(task_id, advance=downloaded)
        if start > end:
            return  # skip already finished
        try:
            async with self.client.stream("GET", random.choice(media_urls),
                                          headers={'Range': f'bytes={start}-{end}'}) as r:
                r.raise_for_status()
                with open(f'{file_dir}/{part_name}', 'ab') as f:
                    async for chunk in r.aiter_bytes():
                        f.write(chunk)
                        self.progress.update(task_id, advance=len(chunk))
        except httpx.RemoteProtocolError:
            await self._get_media_part(media_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            log.warning(f'STREAM {e.__class__.__name__} 异常可能由于网络条件不佳或并发数过大导致，若重复出现请考虑降低并发数')
            await asyncio.sleep(.1 * exception)
            await self._get_media_part(media_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
        except Exception as e:
            log.warning(f'STREAM {e.__class__.__name__} 未知异常')
            await asyncio.sleep(.5 * exception)
            await self._get_media_part(media_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
