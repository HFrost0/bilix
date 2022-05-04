import asyncio
import anyio
import httpx
import re
import random
import json
import json5
import html
from datetime import datetime, timedelta
import os
from rich import print as rprint
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby
from .subtitle import json2srt
from .dm import parse_view


class Downloader:
    def __init__(self, videos_dir='videos', sess_data='', video_concurrency=3, part_concurrency=10, http2=True):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
        :param video_concurrency: 限制最大同时下载的视频数量
        :param part_concurrency: 每个媒体的分段并发数
        :param http2: 是否使用http2协议
        """
        self.videos_dir = videos_dir
        if not os.path.exists(self.videos_dir):
            os.makedirs(videos_dir)
        if not os.path.exists(f'{self.videos_dir}/extra'):
            os.makedirs(f'{self.videos_dir}/extra')
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
            TimeRemainingColumn())
        self.progress.start()
        self.sema = asyncio.Semaphore(video_concurrency)
        self.part_concurrency = part_concurrency

    async def aclose(self):
        self.progress.stop()
        await self.client.aclose()

    async def _load_cate_info(self):
        if 'cate_info' not in dir(self):
            self.cate_info = {}
            res = await self.client.get(
                'https://s1.hdslb.com/bfs/static/laputa-channel/client/assets/index.c0ea30e6.js')
            cate_data = re.search('Za=([^;]*);', res.text).groups()[0]
            cate_data = json5.loads(cate_data)['channelList']
            for i in cate_data:
                if 'sub' in i:
                    for j in i['sub']:
                        self.cate_info[j['name']] = j
                self.cate_info[i['name']] = i

    async def get_collect(self, sid, quality=0):
        """

        :param sid: 合集id，暂时不支持列表
        :param quality: 画面质量，0为可以观看的最高画质，越大质量越低，超过范围时自动选择最低画质
        :return:
        """
        params = {'season_id': sid}
        res = await self.client.get('https://api.bilibili.com/x/space/fav/season/list', params=params)
        data = json.loads(res.text)
        info = data['data']['info']
        # print(f"合集：{info['title']}，数量：{info['media_count']}")
        medias = data['data']['medias']
        await asyncio.gather(
            *[self.get_series(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality) for i in medias]
        )

    async def get_favour(self, fid, num=20, keyword='', quality=0, series=True):
        """
        下载收藏夹内的视频

        :param fid: 收藏夹id
        :param num: 下载数量
        :param keyword: 搜索关键词
        :param quality:
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :return:
        """
        ps = 20
        params = {'media_id': fid, 'pn': 1, 'ps': ps, 'keyword': keyword, 'order': 'mtime'}
        res = await self.client.get(url='https://api.bilibili.com/x/v3/fav/resource/list', params=params)
        data = json.loads(res.text)['data']
        # title = data['info']['title']
        total = min(data['info']['media_count'], num)
        page_nums = total // ps + min(1, total % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                num = total - (page_nums - 1) * ps
            else:
                num = ps
            cors.append(self.get_favor_by_page(fid, i + 1, num, keyword, quality, series))
        await asyncio.gather(*cors)

    async def get_favor_by_page(self, fid, pn=1, num=20, keyword='', quality=0, series=True):
        """
        下载收藏夹某一页的视频

        :param fid: 收藏夹id
        :param pn: 页号
        :param num: 下载数量
        :param keyword: 搜索关键词
        :param quality:
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :return:
        """
        ps = 20
        num = min(ps, num)
        params = {'media_id': fid, 'order': 'mtime', 'ps': ps, 'pn': pn, 'keyword': keyword}
        res = await self.client.get('https://api.bilibili.com/x/v3/fav/resource/list', params=params)
        res.raise_for_status()
        info = json.loads(res.text)
        cors = []
        for i in info['data']['medias'][:num]:
            bvid = i['bvid']
            if i['title'] == '已失效视频':
                rprint(f'[red]已失效视频 https://www.bilibili.com/video/{bvid}')
            else:
                cors.append(self.get_series(f'https://www.bilibili.com/video/{bvid}', quality) if series else
                            self.get_video(f'https://www.bilibili.com/video/{bvid}', quality))
        await asyncio.gather(*cors)

    async def get_cate_videos(self, cate_name: str, num=10, order='click', keyword='', days=7, quality=0, series=True):
        """
        下载分区视频

        :param cate_name: 分区名称
        :param num: 下载数量
        :param order: 何种排序，click播放数，scores评论数，stow收藏数，coin硬币数，dm弹幕数
        :param keyword: 搜索关键词
        :param days: 过去days天中的结果
        :param quality: 画面质量
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :return:
        """
        await self._load_cate_info()
        if cate_name not in self.cate_info:
            print(f'未找到分区 {cate_name}')
            return
        if 'subChannelId' not in self.cate_info[cate_name]:
            sub_names = [i['name'] for i in self.cate_info[cate_name]['sub']]
            print(f'{cate_name} 是主分区，仅支持子分区，试试 {sub_names}')
            return
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
            cors.append(self._get_cate_videos_by_page(min(pagesize, num), params, quality, series))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_videos_by_page(self, num, params, quality=0, series=True):
        res = await self.client.get('https://s.search.bilibili.com/cate/search', params=params)
        info = json.loads(res.text)
        info = info['result'][:num]
        cors = [self.get_series(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality) if series else
                self.get_video(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality)
                for i in info]
        await asyncio.gather(*cors)

    async def get_up_videos(self, mid: str, total=10, order='pubdate', keyword='', quality=0, series=True):
        """

        :param mid: b站用户id，在空间页面的url中可以找到
        :param total: 下载总数
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :return:
        """
        ps = 30
        params = {'mid': mid, 'order': order, 'ps': ps, 'pn': 1, 'keyword': keyword}
        res = await self.client.get('https://api.bilibili.com/x/space/arc/search', params=params)
        res.raise_for_status()
        info = json.loads(res.text)
        total = min(info['data']['page']['count'], total)
        page_nums = total // ps + min(1, total % ps)
        cors = []
        for i in range(page_nums):
            if i + 1 == page_nums:
                num = total - (page_nums - 1) * ps
            else:
                num = ps
            cors.append(self.get_up_videos_by_page(mid, i + 1, num, order, keyword, quality, series))
        await asyncio.gather(*cors)

    async def get_up_videos_by_page(self, mid, pn=1, num=30, order='pubdate', keyword='', quality=0, series=True):
        """

        :param mid: b站用户id，在空间页面的url中可以找到
        :param pn: 页码
        :param num: 下载数量
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param series: 每个视频是否下载所有p，False时仅下载系列中的第一个视频
        :return:
        """
        ps = 30
        num = min(ps, num)
        params = {'mid': mid, 'order': order, 'ps': ps, 'pn': pn, 'keyword': keyword}
        res = await self.client.get('https://api.bilibili.com/x/space/arc/search', params=params)
        res.raise_for_status()
        info = json.loads(res.text)
        bv_ids = [i['bvid'] for i in info['data']['list']['vlist']][:num]
        await asyncio.gather(
            *[self.get_series(f'https://www.bilibili.com/video/{bv}', quality) if series else
              self.get_video(f'https://www.bilibili.com/video/{bv}', quality)
              for bv in bv_ids]
        )

    async def get_series(self, url: str, quality: int = 0, image=False, subtitle=False, dm=False, only_audio=False):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param url: 系列中任意一个视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :return:
        """
        url = url.split('?')[0]
        res = await self.client.get(url, follow_redirects=True)
        initial_state = re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0]
        initial_state = json.loads(initial_state)
        cors = []
        if len(initial_state.get('error', {})) > 0:
            rprint(f'[red]视频已失效 {url}')  # 404 啥都没有，在分区下载的时候可能产生
        elif 'videoData' in initial_state:  # bv视频
            for idx, i in enumerate(initial_state['videoData']['pages']):
                p_url = f"{url}?p={idx + 1}"
                add_name = f"P{idx + 1}-{i['part']}" if len(initial_state['videoData']['pages']) > 1 else ''
                cors.append(self.get_video(p_url, quality, add_name,
                                           image=True if idx == 0 and image else False,
                                           subtitle=subtitle, dm=dm, only_audio=only_audio))
        elif 'initEpList' in initial_state:  # 动漫，电视剧，电影
            for idx, i in enumerate(initial_state['initEpList']):
                p_url = i['link']
                add_name = i['title']
                cors.append(self.get_video(p_url, quality, add_name, image=image,
                                           subtitle=subtitle, dm=dm, only_audio=only_audio))
        else:
            rprint(f'[red]未知类型 {url}')
            return
        await asyncio.gather(*cors)

    async def get_video(self, url, quality: int = 0, add_name='', image=False, subtitle=False, dm=False,
                        only_audio=False):
        """
        下载单个视频

        :param url: 视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param add_name: 给文件的额外添加名，用户请直接保持默认
        :param image: 是否下载封面
        :param subtitle: 是否下载字幕
        :param dm: 是否下载弹幕
        :param only_audio: 是否仅下载音频
        :return:
        """
        await self.sema.acquire()
        res = await self._req_front(url)
        title = re.search('<h1[^>]*title="([^"]*)"', res.text).groups()[0].strip()
        if add_name:
            title = f'{title}-{add_name.strip()}'
        title = html.unescape(title)  # handel & "...
        title = re.sub(r"[/\\:*?\"<>|]", '', title)
        # replace windows illegal character in title
        try:  # find video and audio url
            play_info = re.search('<script>window.__playinfo__=({.*})</script><script>', res.text).groups()[0]
            play_info = json.loads(play_info)
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

        task_id = self.progress.add_task(
            total=0,
            description=title if len(title) < 43 else f'{title[:20]}...{title[-20:]}', visible=False)
        cors = []
        # add cor according to params
        if not only_audio:
            if os.path.exists(f'{self.videos_dir}/{title}.mp4'):
                rprint(f'[green]{title}.mp4 已经存在')
            else:
                cors.append(self._get_media(video_urls, f'{title}-video', task_id))
                cors.append(self._get_media(audio_urls, f'{title}-audio', task_id))
        else:
            if os.path.exists(f'{self.videos_dir}/{title}.mp3'):
                rprint(f'[green]{title}.mp3 已经存在')
            else:
                cors.append(self._get_media(audio_urls, f'{title}-audio', task_id))
        if len(cors) > 0:
            self.progress.update(task_id, total=1, visible=True)
        # additional task
        if image:
            img_url = re.search('property="og:image" content="([^"]*)"', res.text).groups()[0]
            cors.append(self._get_static(img_url, title))
        if subtitle:
            cors.append(self.get_subtitle(url, extra={'cid': cid, 'title': title}))
        if dm:
            # todo 最后还是要读取init state，因为aid在里面，而弹幕的view需要aid，是否考虑合并get_video方法以及get_series方法呢
            init_info = json.loads(re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0])
            aid = init_info['aid'] if 'aid' in init_info else init_info['epInfo']['aid']  # normal or ep video
            cors.append(self.get_dm(cid, aid, title))

        await asyncio.gather(*cors)
        self.sema.release()

        if only_audio and not os.path.exists(f'{self.videos_dir}/{title}.mp3'):
            os.rename(f'{self.videos_dir}/{title}-audio.m4s', f'{self.videos_dir}/{title}.mp3')
        elif not only_audio and not os.path.exists(f'{self.videos_dir}/{title}.mp4'):
            await anyio.run_process(
                ['ffmpeg', '-i', f'{self.videos_dir}/{title}-video.m4s', '-i', f'{self.videos_dir}/{title}-audio.m4s',
                 '-codec', 'copy', f'{self.videos_dir}/{title}.mp4', '-loglevel', 'quiet'])
            os.remove(f'{self.videos_dir}/{title}-video.m4s')
            os.remove(f'{self.videos_dir}/{title}-audio.m4s')
        else:
            return
        self.progress.update(task_id, advance=1)
        print(f'{title} 完成')
        self.progress.update(task_id, visible=False)

    async def get_dm(self, cid, aid, title):
        file_path = f'{self.videos_dir}/extra/{title}-弹幕.bin'
        # if os.path.exists(file_path):  # never skip let update
        #     rprint(f'[dark_green]{title}-弹幕.bin 已经存在')
        #     return
        params = {'oid': cid, 'pid': aid, 'type': 1}
        res = await self.client.get(f'https://api.bilibili.com/x/v2/dm/web/view', params=params)
        view = parse_view(res.content)
        total = int(view['dmSge']['total'])
        cors = []
        for i in range(total):
            url = f'https://api.bilibili.com/x/v2/dm/web/seg.so?oid={cid}&type=1&segment_index={i + 1}'
            cors.append(self.client.get(url))
        results = await asyncio.gather(*cors)
        content = b''.join(res.content for res in results)
        async with await anyio.open_file(file_path, 'wb') as f:
            await f.write(content)
        rprint(f'[grey39]{title}-弹幕.bin 完成')

    async def get_subtitle(self, url, extra: dict = None, convert=True):
        """
        获取某个视频的字幕文件

        :param url: 视频url
        :param extra: {cid:.. title:...}提供则不再请求前端
        :param convert: 是否转换成srt
        :return:
        """
        if not extra:
            res = await self._req_front(url)
            init_state = json.loads(re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0])
            bvid = init_state['bvid']
            (p, cid), = init_state['cidMap'][bvid]['cids'].items()
            title = init_state['videoData']['title'].strip()
            if len(init_state['videoData']['pages']) > 1:
                part_title = init_state['videoData']['pages'][int(p) - 1]['part'].strip()
                title = f'{title}-P{p}-{part_title}'
            title = html.unescape(title)  # handel & "...
            title = re.sub(r"[/\\:*?\"<>|]", '', title)  # replace windows illegal character in title
        else:
            bvid = url.split('?')[0].strip('/').split('/')[-1]
            cid, title = extra['cid'], extra['title']
        params = {'bvid': bvid, 'cid': cid}
        res = await self.client.get('https://api.bilibili.com/x/player/v2', params=params)
        info = json.loads(res.text)
        if info['code'] == -400:
            rprint(f'[red]未找到字幕信息 {url}')
            return
        subtitles = info['data']['subtitle']['subtitles']
        cors = []
        for i in subtitles:
            sub_url = f'http:{i["subtitle_url"]}'
            sub_name = f"{title}-{i['lan_doc']}"
            cors.append(self._get_static(sub_url, sub_name))
        file_paths = await asyncio.gather(*cors)
        if convert:
            for file_path in file_paths:
                new_file_path = file_path.split('.')[0] + '.srt'
                async with await anyio.open_file(file_path, 'r') as f, await anyio.open_file(new_file_path, 'w') as f2:
                    srt = json2srt(await f.read())
                    await f2.write(srt)
                os.remove(file_path)

    async def _req_front(self, url) -> httpx.Response:
        """get web front url response"""
        for _ in range(5):  # repeat 5 times to handle ReadTimeout
            try:
                res = await self.client.get(url, follow_redirects=True)  # b23.tv redirect
            except httpx.ReadTimeout:
                await asyncio.sleep(0.1)
            else:
                break
        else:
            raise Exception(f'[red]超过重复次数 {url}')
        res.raise_for_status()
        return res

    async def _get_static(self, url, name) -> str:
        file_type = f".{url.split('.')[-1]}" if len(url.split('/')[-1].split('.')) > 1 else ''
        file_path = f'{self.videos_dir}/extra/{name}' + file_type
        if os.path.exists(file_path):
            rprint(f'[dark_green]{name + file_type} 已经存在')
        else:
            res = await self.client.get(url)
            async with await anyio.open_file(file_path, 'wb') as f:
                await f.write(res.content)
            rprint(f'[grey39]{name + file_type} 完成')
        return file_path

    async def _get_media(self, media_urls: tuple, media_name, task_id):
        res = await self.client.head(random.choice(media_urls))
        total = int(res.headers['Content-Length'])
        self.progress.update(task_id, total=self.progress.tasks[task_id].total + total)
        part_length = total // self.part_concurrency
        cors = []
        part_names = []
        for i in range(self.part_concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < self.part_concurrency - 1 else total - 1
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cors.append(self._get_media_part(media_urls, (start, end), part_name, task_id))
        await asyncio.gather(*cors)
        async with await anyio.open_file(f'{self.videos_dir}/{media_name}.m4s', 'wb') as f:
            for part_name in part_names:
                async with await anyio.open_file(f'{self.videos_dir}/{part_name}.m4s', 'rb') as pf:
                    await f.write(await pf.read())
                os.remove(f'{self.videos_dir}/{part_name}.m4s')

    async def _get_media_part(self, media_urls: tuple, bytes_range: tuple, part_name, task_id, exception=0):
        if exception > 5:
            raise Exception(f'{part_name}超过重试次数')
        start, end = bytes_range
        if os.path.exists(f'{self.videos_dir}/{part_name}.m4s'):
            downloaded = os.path.getsize(f'{self.videos_dir}/{part_name}.m4s')
            start += downloaded
            if exception == 0:
                self.progress.update(task_id, advance=downloaded)
        try:
            async with self.client.stream("GET", random.choice(media_urls),
                                          headers={'Range': f'bytes={start}-{end}'}) as r:
                async with await anyio.open_file(f'{self.videos_dir}/{part_name}.m4s', 'ab') as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
                        self.progress.update(task_id, advance=len(chunk))
        except httpx.RemoteProtocolError:
            await self._get_media_part(media_urls, bytes_range, part_name, task_id, exception=exception + 1)
        except httpx.ReadTimeout as e:
            rprint(f'[red]警告：{e.__class__}，该异常可能由于网络条件不佳或并发数过大导致，如果异常重复出现请考虑降低并发数')
            await asyncio.sleep(.1 * exception)
            await self._get_media_part(media_urls, bytes_range, part_name, task_id, exception=exception + 1)
