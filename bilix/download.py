import asyncio
import httpx
import re
import random
import json
import json5
from datetime import datetime, timedelta
import os
from anyio import run_process
from rich import print as rprint
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby
from bilix.subtitle import json2srt
from bilix.dm import parse_view, dm2ass_factory
from bilix.utils import legal_title


class Downloader:
    def __init__(self, videos_dir='videos', sess_data='', video_concurrency=3, part_concurrency=10, http2=True):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
        :param video_concurrency: 限制最大同时下载的视频数量
        :param part_concurrency: 每个媒体的分段并发数
        :param http2: 是否使用http2协议
        """
        # assert video_concurrency * part_concurrency <= 100  # todo 是否限制
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

    async def aclose(self):
        self.progress.stop()
        await self.client.aclose()

    def _make_hierarchy_dir(self, hierarchy, add_name: str):
        """Make and return new hierarchy according to old hierarchy and add name"""
        assert hierarchy is True or (type(hierarchy) is str and len(hierarchy) > 0)
        hierarchy = add_name if hierarchy is True else f'{hierarchy}/{add_name}'
        if not os.path.exists(f'{self.videos_dir}/{hierarchy}'):
            os.makedirs(f'{self.videos_dir}/{hierarchy}')
        return hierarchy

    async def _load_cate_info(self):
        if 'cate_info' not in dir(self):
            self.cate_info = {}
            res = await self._req('https://s1.hdslb.com/bfs/static/laputa-channel/client/assets/index.c0ea30e6.js')
            cate_data = re.search('Za=([^;]*);', res.text).groups()[0]
            cate_data = json5.loads(cate_data)['channelList']
            for i in cate_data:
                if 'sub' in i:
                    for j in i['sub']:
                        self.cate_info[j['name']] = j
                self.cate_info[i['name']] = i

    async def get_collect_or_list(self, url, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                                  hierarchy=None):
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
        sid = re.search(r'sid=(\d+)', url).groups()[0]
        if 'seriesdetail' in url:
            await self.get_list(sid, quality, image, subtitle, dm, only_audio, hierarchy)
        elif 'collectiondetail' in url:
            await self.get_collect(sid, quality, image, subtitle, dm, only_audio, hierarchy)
        else:
            raise Exception(f'未知的详情页 {url}')

    async def get_list(self, sid, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                       hierarchy=None):
        """
        下载视频列表

        :param sid: 列表id
        :param quality:
        :param image:
        :param subtitle:
        :param dm:
        :param only_audio:
        :param hierarchy:
        :return:
        """
        res = await self._req(f'https://api.bilibili.com/x/series/series?series_id={sid}')  # meta api
        meta = json.loads(res.text)
        mid = meta['data']['meta']['mid']
        params = {'mid': mid, 'series_id': sid, 'ps': meta['data']['meta']['total']}
        list_res, up_res = await asyncio.gather(self._req('https://api.bilibili.com/x/series/archives', params=params),
                                                self._req(f'https://api.bilibili.com/x/space/acc/info?mid={mid}'))
        list_info, up_info = json.loads(list_res.text), json.loads(up_res.text)
        if hierarchy:
            list_name, up_name = meta['data']['meta']['name'], up_info['data']['name']
            name = legal_title(f"【视频列表】{up_name}-{list_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in list_info['data']['archives']])

    async def get_collect(self, sid, quality=0, image=False, subtitle=False, dm=False, only_audio=False,
                          hierarchy=None):
        """
        下载合集

        :param sid: 合集id
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :param hierarchy:
        :return:
        """
        params = {'season_id': sid}
        res = await self._req('https://api.bilibili.com/x/space/fav/season/list', params=params)
        data = json.loads(res.text)
        medias = data['data']['medias']
        info = data['data']['info']
        if hierarchy:
            col_name, up_name = info['title'], medias[0]['upper']['name']
            name = legal_title(f"【合集】{up_name}-{col_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality,
                              image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
              for i in medias])

    async def get_favour(self, fid, num=20, keyword='', quality=0, series=True, image=False, subtitle=False, dm=False,
                         only_audio=False, hierarchy=None):
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
        ps = 20
        params = {'media_id': fid, 'pn': 1, 'ps': ps, 'keyword': keyword, 'order': 'mtime'}
        res = await self._req(url='https://api.bilibili.com/x/v3/fav/resource/list', params=params)
        data = json.loads(res.text)['data']
        if hierarchy:
            fav_name, up_name = data['info']['title'], data['info']['upper']['name']
            name = legal_title(f"【收藏夹】{up_name}-{fav_name}")
            hierarchy = self._make_hierarchy_dir(hierarchy, name)
        total = min(data['info']['media_count'], num)
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
                                 image=False, subtitle=False, dm=False, only_audio=False, hierarchy=None):
        ps = 20
        num = min(ps, num)
        params = {'media_id': fid, 'order': 'mtime', 'ps': ps, 'pn': pn, 'keyword': keyword}
        res = await self._req('https://api.bilibili.com/x/v3/fav/resource/list', params=params)
        info = json.loads(res.text)
        cors = []
        for i in info['data']['medias'][:num]:
            bvid = i['bvid']
            if i['title'] == '已失效视频':
                rprint(f'[red]已失效视频 https://www.bilibili.com/video/{bvid}')
            else:
                func = self.get_series if series else self.get_video
                # noinspection PyArgumentList
                cors.append(func(f'https://www.bilibili.com/video/{bvid}', quality=quality,
                                 image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy))
        await asyncio.gather(*cors)

    async def get_cate_videos(self, cate_name: str, num=10, order='click', keyword='', days=7, quality=0, series=True,
                              image=False, subtitle=False, dm=False, only_audio=False, hierarchy=None):
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
        await self._load_cate_info()
        if cate_name not in self.cate_info:
            rprint(f'未找到分区 {cate_name}')
            return
        if 'subChannelId' not in self.cate_info[cate_name]:
            sub_names = [i['name'] for i in self.cate_info[cate_name]['sub']]
            rprint(f'{cate_name} 是主分区，仅支持子分区，试试 {sub_names}')
            return
        if hierarchy:
            hierarchy = self._make_hierarchy_dir(hierarchy, legal_title(f"【分区】{cate_name}"))
        cate_id = self.cate_info[cate_name]['tid']
        time_to = datetime.now()
        time_from = time_to - timedelta(days=days)
        time_from, time_to = time_from.strftime('%Y%m%d'), time_to.strftime('%Y%m%d')
        pagesize = 30
        page = 1
        cors = []
        while num > 0:
            params = {'search_type': 'video', 'view_type': 'hot_rank', 'cate_id': cate_id, 'pagesize': pagesize,
                      'keyword': keyword, 'page': page, 'order': order, 'time_from': time_from, 'time_to': time_to}
            cors.append(self._get_cate_videos_by_page(min(pagesize, num), params, quality, series,
                                                      image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                                                      hierarchy=hierarchy))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_videos_by_page(self, num, params, quality=0, series=True,
                                       image=False, subtitle=False, dm=False, only_audio=False, hierarchy=None):
        res = await self._req('https://s.search.bilibili.com/cate/search', params=params)
        info = json.loads(res.text)
        info = info['result'][:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        cors = [func(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality,
                     image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
                for i in info]
        await asyncio.gather(*cors)

    async def get_up_videos(self, mid: str, num=10, order='pubdate', keyword='', quality=0, series=True,
                            image=False, subtitle=False, dm=False, only_audio=False, hierarchy=None):
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
        params = {'mid': mid, 'order': order, 'ps': ps, 'pn': 1, 'keyword': keyword}
        res = await self._req('https://api.bilibili.com/x/space/arc/search', params=params)
        info = json.loads(res.text)
        if hierarchy:
            name = info['data']['list']['vlist'][0]['author']
            hierarchy = self._make_hierarchy_dir(hierarchy, legal_title(f"【up】{name}"))
        num = min(info['data']['page']['count'], num)
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
                                     image=False, subtitle=False, dm=False, only_audio=False, hierarchy=None):
        ps = 30
        num = min(ps, num)
        params = {'mid': mid, 'order': order, 'ps': ps, 'pn': pn, 'keyword': keyword}
        res = await self._req('https://api.bilibili.com/x/space/arc/search', params=params)
        info = json.loads(res.text)
        bv_ids = [i['bvid'] for i in info['data']['list']['vlist']][:num]
        func = self.get_series if series else self.get_video
        # noinspection PyArgumentList
        await asyncio.gather(
            *[func(f'https://www.bilibili.com/video/{bv}', quality=quality,
                   image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy) for bv in bv_ids])

    async def get_series(self, url: str, quality: int = 0, image=False, subtitle=False, dm=False, only_audio=False,
                         p_range: tuple = None, hierarchy=None):
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
        url = url.split('?')[0]
        res = await self._req(url, follow_redirects=True)
        init_info = re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0]
        init_info = json.loads(init_info)
        cors = []
        if len(init_info.get('error', {})) > 0:
            rprint(f'[red]视频已失效 {url}')  # 404 啥都没有，在分区下载的时候可能产生
        elif 'videoData' in init_info:  # bv视频
            if hierarchy:
                title = legal_title(init_info['videoData']['title'])
                if len(init_info['videoData']['pages']) > 1:
                    hierarchy = self._make_hierarchy_dir(hierarchy, title)
                else:
                    hierarchy = hierarchy if type(hierarchy) is str else None
            for idx, i in enumerate(init_info['videoData']['pages']):
                p_url = f"{url}?p={idx + 1}"
                add_name = f"P{idx + 1}-{i['part']}" if len(init_info['videoData']['pages']) > 1 else ''
                cors.append(self.get_video(p_url, quality, add_name,
                                           image=True if idx == 0 and image else False,
                                           subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy))
        elif 'initEpList' in init_info:  # 动漫，电视剧，电影
            if hierarchy:
                title = legal_title(re.search('property="og:title" content="([^"]*)"', res.text).groups()[0])
                if len(init_info['initEpList']) > 1:
                    hierarchy = self._make_hierarchy_dir(hierarchy, title)
                else:
                    hierarchy = hierarchy if type(hierarchy) is str else None
            for idx, i in enumerate(init_info['initEpList']):
                p_url = i['link']
                add_name = i['title']
                cors.append(self.get_video(p_url, quality, add_name, image=image,
                                           subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy))
        else:
            rprint(f'[red]未知类型 {url}')
            return
        if p_range:
            h, t = p_range[0] - 1, p_range[1]
            assert 0 <= h <= t
            [cor.close() for idx, cor in enumerate(cors) if idx < h or idx >= t]  # avoid runtime warning
            cors = cors[h:t]
        await asyncio.gather(*cors)

    async def get_video(self, url: str, quality: int = 0, add_name='', image=False, subtitle=False, dm=False,
                        only_audio=False, hierarchy=None):
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
        :return:
        """
        await self.sema.acquire()
        res = await self._req(url, follow_redirects=True)
        init_info = json.loads(re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0])
        if len(init_info.get('error', {})) > 0:
            rprint(f'[red]视频已失效 {url}')  # 404 啥都没有，在分区下载的时候可能产生
            return
        title = re.search('<h1[^>]*title="([^"]*)"', res.text).groups()[0]
        title = legal_title(title, add_name)
        try:  # find video and audio url
            play_info = re.search('<script>window.__playinfo__=({.*})</script><script>', res.text).groups()[0]
            play_info = json.loads(play_info)
            video_info, video_urls = None, None  # avoid ide warning
            # choose quality
            for q, (_, i) in enumerate(groupby(play_info['data']['dash']['video'], key=lambda x: x['id'])):
                video_info = next(i)
                video_urls = (video_info['base_url'], *(video_info['backup_url'] if video_info['backup_url'] else ()))
                if q == quality:
                    break
            audio_info = play_info['data']['dash']['audio'][0]
            audio_urls = (audio_info['base_url'], *(audio_info['backup_url'] if audio_info['backup_url'] else ()))
        except (KeyError, AttributeError):  # KeyError-电影，AttributeError-动画
            # todo https://www.bilibili.com/video/BV1Jx411r776?p=3 未处理，老视频mp4
            rprint(f'[rgb(234,122,153)]{title} 需要大会员，或该地区不支持')
            self.sema.release()
            return
        cid = audio_urls[0].split('/')[-2]

        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy and len(hierarchy) > 0 else self.videos_dir
        task_id = self.progress.add_task(
            total=1,
            description=title if len(title) < 33 else f'{title[:15]}...{title[-15:]}', visible=False)
        cors = []
        # add cor according to params
        if not only_audio:
            if os.path.exists(f'{file_dir}/{title}.mp4'):
                rprint(f'[green]{title}.mp4 已经存在')
            else:
                cors.append(self._get_media(video_urls, f'{title}-video', task_id, hierarchy))
                cors.append(self._get_media(audio_urls, f'{title}-audio', task_id, hierarchy))
        else:
            cors.append(self._get_media(audio_urls, f'{title}.mp3', task_id, hierarchy))
        # additional task
        if image or subtitle or dm:
            extra_hierarchy = self._make_hierarchy_dir(hierarchy if hierarchy else True, 'extra')
            if image:
                img_url = re.search('property="og:image" content="([^"]*)"', res.text).groups()[0]
                cors.append(self._get_static(img_url, title, hierarchy=extra_hierarchy))
            if subtitle:
                cors.append(self.get_subtitle(url, extra={'cid': cid, 'title': title}, hierarchy=extra_hierarchy))
            if dm:
                aid = init_info['aid'] if 'aid' in init_info else init_info['epInfo']['aid']  # normal or ep video
                w, h = video_info['width'], video_info['height']
                cors.append(self.get_dm(cid, aid, title, convert_func=dm2ass_factory(w, h), hierarchy=extra_hierarchy))
        await asyncio.gather(*cors)
        self.sema.release()

        if not only_audio and not os.path.exists(f'{file_dir}/{title}.mp4'):
            await run_process(
                ['ffmpeg', '-i', f'{file_dir}/{title}-video', '-i', f'{file_dir}/{title}-audio',
                 '-codec', 'copy', f'{file_dir}/{title}.mp4', '-loglevel', 'quiet'])
            os.remove(f'{file_dir}/{title}-video')
            os.remove(f'{file_dir}/{title}-audio')
        # make progress invisible and print
        if self.progress.tasks[task_id].visible:
            self.progress.update(task_id, advance=1, visible=False)
            print(f'{title}{".mp3" if only_audio else ".mp4"} 完成')
        # todo return file path

    async def get_dm(self, cid, aid, title, update=False, convert_func=None, hierarchy=None):
        """

        :param cid:
        :param aid:
        :param title: 弹幕文件名
        :param update: 是否更新覆盖之前下载的弹幕文件
        :param convert_func:
        :param hierarchy:
        :return:
        """
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        file_type = '.' + ('bin' if not convert_func else convert_func.__name__.split('2')[-1])
        file_path = f'{file_dir}/{title}-弹幕{file_type}'
        if not update and os.path.exists(file_path):
            rprint(f'[dark_green]{title}-弹幕{file_type} 已经存在')
            return file_path
        params = {'oid': cid, 'pid': aid, 'type': 1}
        res = await self._req(f'https://api.bilibili.com/x/v2/dm/web/view', params=params)
        view = parse_view(res.content)
        total = int(view['dmSge']['total'])
        cors = []
        for i in range(total):
            url = f'https://api.bilibili.com/x/v2/dm/web/seg.so?oid={cid}&type=1&segment_index={i + 1}'
            cors.append(self._req(url))
        results = await asyncio.gather(*cors)
        content = b''.join(res.content for res in results)
        content = await convert_func(content) if convert_func else content
        with open(file_path, 'wb') as f:
            f.write(content)
        rprint(f'[grey39]{title}-弹幕{file_type} 完成')
        return file_path

    async def get_subtitle(self, url, extra: dict = None, convert=True, hierarchy=None):
        """
        获取某个视频的字幕文件

        :param url: 视频url
        :param extra: {cid:.. title:...}提供则不再请求前端
        :param convert: 是否转换成srt
        :param hierarchy:
        :return:
        """
        if not extra:
            res = await self._req(url)
            init_info = json.loads(re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0])
            bvid = init_info['bvid']
            (p, cid), = init_info['cidMap'][bvid]['cids'].items()
            title = init_info['videoData']['title']
            add_name = ''
            if len(init_info['videoData']['pages']) > 1:
                part_title = init_info['videoData']['pages'][int(p) - 1]['part']
                add_name = f'P{p}-{part_title}'
            title = legal_title(title, add_name)
        else:
            bvid = url.split('?')[0].strip('/').split('/')[-1]
            cid, title = extra['cid'], extra['title']
        params = {'bvid': bvid, 'cid': cid}
        res = await self._req('https://api.bilibili.com/x/player/v2', params=params)
        info = json.loads(res.text)
        if info['code'] == -400:
            rprint(f'[red]未找到字幕信息 {url}')
            return
        subtitles = info['data']['subtitle']['subtitles']
        cors = []
        for i in subtitles:
            sub_url = f'http:{i["subtitle_url"]}'
            sub_name = f"{title}-{i['lan_doc']}"
            cors.append(self._get_static(sub_url, sub_name, convert_func=json2srt if convert else None,
                                         hierarchy=hierarchy))
        paths = await asyncio.gather(*cors)
        return paths

    async def _req(self, url, method='GET', follow_redirects=False, **kwargs) -> httpx.Response:
        """Client request with retry"""
        for _ in range(3):  # repeat 3 times to handle Exception
            try:
                res = await self.client.request(method, url, follow_redirects=follow_redirects, **kwargs)
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
                rprint(f'[red]警告：{e.__class__} 可能由于网络不佳 {method} {url}')
                await asyncio.sleep(0.1)
            except Exception as e:
                rprint(f'[red]警告：未知异常{e.__class__} {method} {url}')
                await asyncio.sleep(0.5)
            else:
                break
        else:
            rprint(f'[red]超过重复次数 {url}')
            raise Exception('超过重复次数')
        res.raise_for_status()
        return res

    async def _get_static(self, url, name, convert_func=None, hierarchy=None) -> str:
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
        file_path = f'{file_dir}/{name}' + file_type
        if os.path.exists(file_path):
            rprint(f'[dark_green]{name + file_type} 已经存在')  # extra file use different color
        else:
            res = await self._req(url)
            content = convert_func(res.content) if convert_func else res.content
            with open(file_path, 'wb') as f:
                f.write(content)
            rprint(f'[grey39]{name + file_type} 完成')  # extra file use different color
        return file_path

    async def _get_media(self, media_urls: tuple, media_name, task_id, hierarchy=None):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if os.path.exists(f'{file_dir}/{media_name}'):
            rprint(f'[green]{media_name} 已经存在')
            return f'{file_dir}/{media_name}'
        res = await self._req(media_urls[0], method='HEAD')
        total = int(res.headers['Content-Length'])
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
                rprint('Interrupt, but waiting for file merge, please try again later')
                merge()
            [os.remove(f'{file_dir}/{part}') for part in part_names]

        merge()
        return f'{file_dir}/{media_name}'

    async def _get_media_part(self, media_urls: tuple, part_name, task_id, exception=0, hierarchy=None):
        file_dir = f'{self.videos_dir}/{hierarchy}' if hierarchy else self.videos_dir
        if exception > 5:
            rprint(f'[red]超过重试次数 {part_name}')
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
        except httpx.ReadTimeout as e:
            rprint(f'[red]警告：{e.__class__} in streaming，该异常可能由于网络条件不佳或并发数过大导致，若重复出现请考虑降低并发数')
            await asyncio.sleep(.1 * exception)
            await self._get_media_part(media_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
        except Exception as e:
            rprint(f'[red]警告：未知异常{e.__class__} {part_name}')
            await asyncio.sleep(.5 * exception)
            await self._get_media_part(media_urls, part_name, task_id, exception=exception + 1, hierarchy=hierarchy)
