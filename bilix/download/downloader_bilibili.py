import asyncio
from typing import Union, Sequence, Tuple, Optional
import aiofiles
import httpx
from datetime import datetime, timedelta
import os
from itertools import groupby
from anyio import run_process
import bilix.api.bilibili as api
from bilix.handle import Handler, HandleMethodError
from bilix.download.base_downloader_part import BaseDownloaderPart
from bilix.subtitle import json2srt
from bilix.dm import dm2ass_factory
from bilix.utils import legal_title, req_retry, cors_slice, parse_bilibili_url
from bilix.log import logger

__all__ = ['DownloaderBilibili']


def choose_quality(dash, support_formats, quality: Union[str, int], codec: str = '') -> Tuple[dict, dict]:
    """

    :param dash:
    :param support_formats:
    :param quality:
    :param codec: should be like xxx (for video only) :xxxx (for audio only) xxx:xxx (for video and audio)
    :return: video_info, audio_info, video_urls, audio_urls
    """
    v_codec, a_codec, *_ = codec.split(':') + [""]
    # for audio
    if a_codec == '':
        audio_info = dash['audio'][0]
        audio_info['suffix'] = '.aac'
    else:
        if dash['dolby']['audio'] and dash['dolby']['audio'][0]['codecs'].startswith(a_codec):
            audio_info = dash['dolby']['audio'][0]
            audio_info['suffix'] = '.eac3'  # todo other dolby codec?
        elif dash.get('flac', None) and dash['flac']['audio'] and dash['flac']['audio']['codecs'].startswith(a_codec):
            audio_info = dash['flac']['audio']
            audio_info['suffix'] = '.flac'
        else:
            raise ValueError(f'Invalid quality and codec quality:{quality} codec: {codec}')
    audio_info['urls'] = (audio_info['base_url'], *(audio_info['backup_url'] if audio_info['backup_url'] else ()))

    # for video
    if isinstance(quality, str):  # 1. absolute choice with quality name like 4k 1080p '1080p 60帧'
        for f_info in support_formats:
            if f_info['new_description'].upper().startswith(quality.upper()):
                q_id = f_info['quality']
                for video_info in dash['video']:
                    if video_info['id'] == q_id and (v_codec == '' or video_info['codecs'].startswith(v_codec)):
                        video_info['urls'] = (video_info['base_url'], *(video_info['backup_url']
                                                                        if video_info['backup_url'] else ()))
                        logger.debug(f"quality <{f_info['new_description']}>"
                                     f" codec <{video_info['codecs']}:{audio_info['codecs']}> has been chosen")
                        return video_info, audio_info
    else:  # 2. relative choice
        quality = min(quality, len(set(i['id'] for i in dash['video'])) - 1)
        for q, (q_id, it) in enumerate(groupby(dash['video'], key=lambda x: x['id'])):
            if q == quality:
                for video_info in it:
                    if v_codec == '' or video_info['codecs'].startswith(v_codec):
                        video_info['urls'] = (video_info['base_url'], *(video_info['backup_url']
                                                                        if video_info['backup_url'] else ()))
                        logger.debug(f"relative quality <{quality}>"
                                     f" codec <{video_info['codecs']}:{audio_info['codecs']}> has been chosen")
                        return video_info, audio_info
    raise ValueError(f'Invalid quality and codec quality:{quality} codec: {codec}')


class DownloaderBilibili(BaseDownloaderPart):
    def __init__(self, videos_dir='videos', sess_data='', video_concurrency=3, part_concurrency=10,
                 speed_limit: Union[float, int] = None, progress=None):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
        :param video_concurrency: 限制最大同时下载的视频数量
        :param part_concurrency: 每个媒体的分段并发数
        :param speed_limit: 下载速度限制，单位B/s
        :param progress: 进度对象，不提供则使用rich命令行进度
        """
        cookies = {'SESSDATA': sess_data}
        headers = {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}
        client = httpx.AsyncClient(headers=headers, cookies=cookies, http2=True)
        super(DownloaderBilibili, self).__init__(client, videos_dir, part_concurrency, speed_limit=speed_limit,
                                                 progress=progress)
        self.speed_limit = speed_limit
        self.v_sema = asyncio.Semaphore(video_concurrency)
        self._cate_meta = None

    async def get_collect_or_list(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                                  codec: str = '', hierarchy: Union[bool, str] = True):
        """
        下载合集或视频列表

        :param url: 合集或视频列表详情页url
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param codec:
        :param hierarchy: 是否使用层次目录保存文件
        :return:
        """
        t = parse_bilibili_url(url)
        if t == 'list':
            cor = self.get_list
        elif t == 'col':
            cor = self.get_collect
        else:
            raise ValueError(f'{url} invalid for get_collect_or_list')
        # noinspection PyArgumentList
        await cor(url=url, quality=quality, image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                  codec=codec, hierarchy=hierarchy)

    async def get_list(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                       codec: str = '', hierarchy: Union[bool, str] = True):
        """
        下载视频列表

        :param url: 列表详情页url
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param codec
        :param hierarchy:
        :return:
        """
        list_name, up_name, bvids = await api.get_list_info(self.client, url)
        if hierarchy:
            name = legal_title(f"【视频列表】{up_name}-{list_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i}", quality=quality, codec=codec,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in bvids])

    async def get_collect(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                          codec: str = '', hierarchy: Union[bool, str] = True):
        """
        下载合集

        :param url: 合集详情页url
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec:
        :param hierarchy:
        :return:
        """
        col_name, up_name, bvids = await api.get_collect_info(self.client, url)
        if hierarchy:
            name = legal_title(f"【合集】{up_name}-{col_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i}", quality=quality, codec=codec,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in bvids])

    async def get_favour(self, url_or_fid, num=20, keyword='', quality=0, series=True, image=False, subtitle=False,
                         dm=False, only_audio=False, codec: str = '', hierarchy: Union[bool, str] = True):
        """
        下载收藏夹内的视频

        :param url_or_fid: 收藏夹url或收藏夹id
        :param num: 下载数量
        :param keyword: 搜索关键词
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec:
        :param hierarchy:
        :return:
        """
        fav_name, up_name, total_size, bvids = await api.get_favour_page_info(self.client, url_or_fid, keyword=keyword)
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
            cors.append(self._get_favor_by_page(url_or_fid, i + 1, num, keyword, quality, series,
                                                image, subtitle, dm, only_audio, codec=codec, hierarchy=hierarchy))
        await asyncio.gather(*cors)

    async def _get_favor_by_page(self, url_or_fid, pn=1, num=20, keyword='', quality=0, series=True,
                                 image=False, subtitle=False, dm=False, only_audio=False, codec='', hierarchy=True):
        ps = 20
        num = min(ps, num)
        _, _, _, bvids = await api.get_favour_page_info(self.client, url_or_fid, pn, ps, keyword)
        cors = []
        for i in bvids[:num]:
            func = self.get_series if series else self.get_video
            # noinspection PyArgumentList
            cors.append(func(f'https://www.bilibili.com/video/{i}', quality=quality, codec=codec,
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
                              image=False, subtitle=False, dm=False, only_audio=False, codec='',
                              hierarchy: Union[bool, str] = True):
        """
        下载分区视频

        :param cate_name: 分区名称
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
        :param hierarchy:
        :return:
        """
        cate_meta = await self.cate_meta
        if cate_name not in cate_meta:
            logger.error(f'未找到分区 {cate_name}')
            return
        if 'subChannelId' not in cate_meta[cate_name]:
            sub_names = [i['name'] for i in cate_meta[cate_name]['sub']]
            logger.error(f'{cate_name} 是主分区，仅支持子分区，试试 {sub_names}')
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
                                              only_audio=only_audio, codec=codec, hierarchy=hierarchy))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_videos_by_page(self, cate_id, time_from, time_to, pn=1, num=30, order='click', keyword='',
                                       quality=0, series=True, image=False, subtitle=False, dm=False,
                                       only_audio=False, codec='', hierarchy=True):
        bvids = await api.get_cate_page_info(self.client, cate_id, time_from, time_to, pn, 30, order, keyword)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        cors = [func(f"https://www.bilibili.com/video/{i}", quality=quality, codec=codec,
                     image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
                for i in bvids]
        await asyncio.gather(*cors)

    async def get_up_videos(self, url_or_mid: str, num=10, order='pubdate', keyword='', quality: Union[int, str] = 0,
                            series=True, image=False, subtitle=False, dm=False, only_audio=False, codec='',
                            hierarchy: Union[bool, str] = True):
        """

        :param url_or_mid: b站用户空间页面url 或b站用户id，在空间页面的url中可以找到
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
        :param hierarchy:
        :return:
        """
        ps = 30
        up_name, total_size, bv_ids = await api.get_up_info(self.client, url_or_mid, 1, ps, order, keyword)
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
            cors.append(self._get_up_videos_by_page(url_or_mid, i + 1, p_num, order, keyword, quality, series,
                                                    image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                                                    codec=codec, hierarchy=hierarchy))
        await asyncio.gather(*cors)

    async def _get_up_videos_by_page(self, url_or_mid, pn=1, num=30, order='pubdate', keyword='', quality=0,
                                     series=True, image=False, subtitle=False, dm=False, only_audio=False, codec='',
                                     hierarchy=None):
        ps = 30
        num = min(ps, num)
        _, _, bvids = await api.get_up_info(self.client, url_or_mid, pn, ps, order, keyword)
        bvids = bvids[:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        await asyncio.gather(
            *[func(f'https://www.bilibili.com/video/{bv}', quality=quality, codec=codec,
                   image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy) for bv in bvids])

    async def get_series(self, url: str, quality: Union[str, int] = 0, image=False, subtitle=False,
                         dm=False, only_audio=False, p_range: Sequence[int] = None, codec: str = '',
                         hierarchy: Union[bool, str] = True):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param url: 系列中任意一个视频的url
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param p_range: 下载集数范围，例如(1, 3)：P1至P3
        :param codec: 视频编码（可通过info获取）
        :param hierarchy:
        :return:
        """
        try:
            video_info = await api.get_video_info(self.client, url)
        except AttributeError as e:
            logger.warning(f'{e} {url}')
            return
        title = video_info.title
        pages = video_info.pages
        p = video_info.p
        if hierarchy and len(pages) > 1:
            hierarchy = self._make_hierarchy_dir(hierarchy, title)
        else:
            hierarchy = hierarchy if type(hierarchy) is str else ''  # incase hierarchy is False
        cors = [self.get_video(p_url, quality, add_name,
                               image=image,
                               subtitle=subtitle, dm=dm, only_audio=only_audio, codec=codec, hierarchy=hierarchy,
                               extra=video_info if idx == p else None)
                for idx, (add_name, p_url) in enumerate(pages)]
        if p_range:
            cors = cors_slice(cors, p_range)
        await asyncio.gather(*cors)

    async def get_video(self, url: str, quality: Union[str, int] = 0, add_name='', image=False, subtitle=False,
                        dm=False, only_audio=False, codec: str = '', hierarchy: str = '', extra=None):
        """
        下载单个视频

        :param url: 视频的url
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质，或者直接使用字符串指定'1080p'等名称
        :param add_name: 给文件的额外添加名，用户请直接保持默认
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param codec: 视频编码（可通过codec获取）
        :param hierarchy:
        :param extra: 额外数据，提供时不用再次请求页面
        :return:
        """
        async with self.v_sema:
            if not extra:
                try:
                    extra = await api.get_video_info(self.client, url)
                except AttributeError as e:
                    logger.warning(f'{url} {e}')
                    return
            title = extra.h1_title
            title = legal_title(title, add_name)
            extra.title = title  # update extra title
            dash = extra.dash
            img_url = extra.img_url
            formats = extra.support_formats
            if not dash:
                logger.warning(f'{extra.title} 需要大会员或该地区不支持')
                return
            # choose video quality
            try:
                video_info, audio_info = choose_quality(dash, formats, quality, codec)
            except ValueError:
                logger.warning(
                    f"{extra.title} 清晰度<{quality}> 编码<{codec}>不可用，请检查输入是否正确或是否需要大会员")
                return

            file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
            task_id = await self.progress.add_task(
                total=1, description=title if len(title) < 33 else f'{title[:15]}...{title[-15:]}', visible=False)
            cors = []
            # add cor according to params
            if not only_audio:
                if os.path.exists(f'{file_dir}/{title}.mp4'):
                    logger.info(f'[green]已存在[/green] {title}.mp4')
                else:
                    cors.append(self.get_media(video_info['urls'], f'{title}-video', task_id, hierarchy))
                    cors.append(self.get_media(audio_info['urls'], f'{title}-audio', task_id, hierarchy))
            else:
                cors.append(self.get_media(audio_info['urls'], f'{title}{audio_info["suffix"]}', task_id, hierarchy))
            # additional task
            if image or subtitle or dm:
                extra_hierarchy = self._make_hierarchy_dir(hierarchy if hierarchy else True, 'extra')
                if image:
                    cors.append(self._get_static(img_url, title, hierarchy=extra_hierarchy))
                if subtitle:
                    cors.append(self.get_subtitle(url, extra=extra, hierarchy=extra_hierarchy))
                if dm:
                    w, h = video_info['width'], video_info['height']
                    cors.append(
                        self.get_dm(url, convert_func=dm2ass_factory(w, h), hierarchy=extra_hierarchy, extra=extra))
            await asyncio.gather(*cors)

        if not only_audio and not os.path.exists(f'{file_dir}/{title}.mp4'):
            cmd = ['ffmpeg', '-i', f'{file_dir}/{title}-video', '-i', f'{file_dir}/{title}-audio',
                   '-codec', 'copy', '-loglevel', 'quiet']
            # ffmpeg: flac in MP4 support is experimental, add '-strict -2' if you want to use it.
            if audio_info['codecs'] == 'fLaC':
                cmd.extend(['-strict', '-2'])
            cmd.append(f'{file_dir}/{title}.mp4')
            await run_process(cmd)
            os.remove(f'{file_dir}/{title}-video')
            os.remove(f'{file_dir}/{title}-audio')
        # make progress invisible
        if self.progress.tasks[task_id].visible:
            await self.progress.update(task_id, advance=1, visible=False)
            logger.info(f'[cyan]已完成[/cyan] {title}{audio_info["suffix"] if only_audio else ".mp4"}')

    async def get_dm(self, url, update=False, convert_func=None, hierarchy: str = '', extra=None):
        """

        :param url: 视频url
        :param update: 是否更新覆盖之前下载的弹幕文件
        :param convert_func:
        :param hierarchy:
        :param extra: 额外数据，提供则不再访问前端
        :return:
        """
        if not extra:
            extra = await api.get_video_info(self.client, url)
        title = extra.title
        aid, cid = extra.aid, extra.cid

        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        file_type = '.' + ('bin' if not convert_func else convert_func.__name__.split('2')[-1])
        file_name = f"{title}-弹幕{file_type}"
        file_path = f'{file_dir}/{file_name}'
        if not update and os.path.exists(file_path):
            logger.info(f"[green]已存在[/green] {file_name}")
            return file_path
        dm_urls = await api.get_dm_info(self.client, aid, cid)
        cors = [req_retry(self.client, dm_url) for dm_url in dm_urls]
        results = await asyncio.gather(*cors)
        content = b''.join(res.content for res in results)
        content = convert_func(content) if convert_func else content
        if asyncio.iscoroutine(content):
            content = await content
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        logger.info(f"[cyan]已完成[/cyan] {file_name}")
        return file_path

    async def get_subtitle(self, url, convert=True, hierarchy: str = '', extra=None):
        """
        获取某个视频的字幕文件

        :param url: 视频url
        :param convert: 是否转换成srt
        :param hierarchy:
        :param extra: 额外数据，提供则不再访问前端
        :return:
        """
        if not extra:
            extra = await api.get_video_info(self.client, url)
        bvid = extra.bvid
        p, cid = extra.p, extra.cid
        title = extra.title
        add_name = extra.pages[p][0]
        title = legal_title(title, add_name)
        try:
            subtitles = await api.get_subtitle_info(self.client, bvid, cid)
        except AttributeError as e:
            logger.warning(f'{url} {e}')
            return
        cors = []
        for sub_url, sub_name in subtitles:
            file_name = f"{title}-{sub_name}"
            cors.append(self._get_static(sub_url, file_name, convert_func=json2srt if convert else None,
                                         hierarchy=hierarchy))
        paths = await asyncio.gather(*cors)
        return paths


@Handler(name='bilibili')
def handle(
        method: str,
        key: str,
        videos_dir: str,
        video_concurrency: int,
        part_concurrency: int,
        cookie: str,
        quality: Union[str, int],
        days: int,
        num: int,
        order: str,
        keyword: str,
        no_series: bool,
        hierarchy: bool,
        image: bool,
        subtitle: bool,
        dm: bool,
        only_audio: bool,
        p_range,
        codec: str,
        speed_limit: Optional[str]
):
    d = DownloaderBilibili(videos_dir=videos_dir,
                           video_concurrency=video_concurrency,
                           part_concurrency=part_concurrency,
                           speed_limit=speed_limit,
                           sess_data=cookie)
    if method == 'get_series' or method == 's':
        cor = d.get_series(key, quality=quality, image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                           p_range=p_range, hierarchy=hierarchy, codec=codec)
    elif method == 'get_video' or method == 'v':
        cor = d.get_video(key, quality=quality,
                          image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, codec=codec)
    elif method == 'get_up' or method == 'up':
        cor = d.get_up_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy, codec=codec
        )
    elif method == 'get_cate' or method == 'cate':
        cor = d.get_cate_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, days=days, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy, codec=codec)
    elif method == 'get_favour' or method == 'fav':
        cor = d.get_favour(key, quality=quality, num=num, keyword=keyword, series=no_series, codec=codec,
                           image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    elif method == 'get_collect' or method == 'col':
        cor = d.get_collect_or_list(key, quality=quality, codec=codec,
                                    image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                                    hierarchy=hierarchy)
    else:
        raise HandleMethodError(executor=d, method=method)
    return d, cor
