import asyncio
import anyio
import httpx
import re
import random
import json
import json5
from datetime import datetime, timedelta
import os
from rich import print as rprint
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby


class Downloader:
    def __init__(self, videos_dir='videos', sess_data='', video_concurrency=3, part_concurrency=10):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
        :param video_concurrency: 限制最大同时下载的视频数量
        :param part_concurrency: 每个媒体的分段并发数
        """
        self.videos_dir = videos_dir
        if not os.path.exists(self.videos_dir):
            os.makedirs(videos_dir)
        cookies = {'SESSDATA': sess_data}
        headers = {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}
        self.client = httpx.AsyncClient(headers=headers, cookies=cookies, http2=True)
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

    async def get_favour(self, fid, num=20, keyword='', quality=0):
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
            cors.append(self.get_favor_by_page(fid, i + 1, num, keyword, quality))
        await asyncio.gather(*cors)

    async def get_favor_by_page(self, fid, pn=1, num=20, keyword='', quality=0):
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
                cors.append(self.get_series(f'https://www.bilibili.com/video/{bvid}', quality))
        await asyncio.gather(*cors)

    async def get_cate_videos(self, cate_name: str, num=10, order='click', keyword='', days=7, quality=0):
        """
        下载分区视频

        :param cate_name: 分区名称
        :param num: 下载数量
        :param order: 何种排序，click播放数，scores评论数，stow收藏数，coin硬币数，dm弹幕数
        :param keyword: 搜索关键词
        :param quality: 画面质量
        :param days: 过去days天中的结果
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
            cors.append(self._get_cate_videos_by_page(num=min(pagesize, num), params=params, quality=quality))
            num -= pagesize
            page += 1
        await asyncio.gather(*cors)

    async def _get_cate_videos_by_page(self, num, params, quality=0):
        res = await self.client.get('https://s.search.bilibili.com/cate/search', params=params)
        info = json.loads(res.text)
        info = info['result'][:num]
        cors = [self.get_series(f"https://www.bilibili.com/video/{i['bvid']}", quality=quality)
                for i in info]
        await asyncio.gather(*cors)

    async def get_up_videos(self, mid: str, total=10, order='pubdate', keyword='', quality=0):
        """

        :param mid: b站用户id，在空间页面的url中可以找到
        :param total: 下载总数
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
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
            cors.append(self.get_up_videos_by_page(mid, i + 1, num, order, keyword, quality))
        await asyncio.gather(*cors)

    async def get_up_videos_by_page(self, mid, pn=1, num=30, order='pubdate', keyword='', quality=0):
        """

        :param mid: b站用户id，在空间页面的url中可以找到
        :param pn: 页码
        :param num: 下载数量
        :param order: 何种排序，b站支持：最新发布pubdate，最多播放click，最多收藏stow
        :param keyword: 过滤关键词
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
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
            *[self.get_series(f'https://www.bilibili.com/video/{bv}', quality) for bv in bv_ids]
        )

    async def get_series(self, url: str, quality: int = 0):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param url: 系列中任意一个视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :return:
        """
        url = url.split('?')[0]
        res = await self.client.get(url, follow_redirects=True)
        initial_state = re.search(r'<script>window.__INITIAL_STATE__=({.*});\(', res.text).groups()[0]
        initial_state = json.loads(initial_state)
        video_urls = []
        add_names = []
        if 'videoData' in initial_state:  # bv视频
            for idx, i in enumerate(initial_state['videoData']['pages']):
                video_urls.append(f"{url}?p={idx + 1}")
                add_names.append(i['part'] if len(initial_state['videoData']['pages']) > 1 else '')
        elif 'initEpList' in initial_state:  # 动漫，电视剧，电影
            for i in initial_state['initEpList']:
                video_urls.append(i['link'])
                add_names.append(i['title'])
        else:
            rprint(f'[red]未知类型 {url}')
            return
        await asyncio.gather(
            *[self.get_video(url, quality, add_name) for url, add_name in zip(video_urls, add_names)]
        )

    async def get_video(self, url, quality: int = 0, add_name='', ):
        """
        下载单个视频

        :param url: 视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :param add_name: 给文件的额外添加名，用户请直接保持默认
        :return:
        """
        await self.sema.acquire()
        for _ in range(5):  # repeat 5 times to handle ReadTimeout
            try:
                res = await self.client.get(url)
            except httpx.ReadTimeout:
                await asyncio.sleep(0.1)
            else:
                break
        else:
            rprint(f'[red]超过重复次数 {url}')
            return
        title = re.search('<h1[^>]*title="([^"]*)"', res.text).groups()[0].strip()
        if add_name:
            title += f'-{add_name.strip()}'
        # replace windows illegal character in title
        title = re.sub(r"[/\\:*?\"<>|]", '', title)
        if os.path.exists(f'{self.videos_dir}/{title}.mp4'):
            rprint(f'[green]{title}.mp4 已经存在')
            self.sema.release()
            return
        # find video and audio url
        try:
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
        task_id = self.progress.add_task(total=1,
                                         description=title if len(title) < 43 else f'{title[:20]}...{title[-20:]}')
        await asyncio.gather(
            self._get_media(video_urls, f'{title}-video', task_id),
            self._get_media(audio_urls, f'{title}-audio', task_id)
        )
        self.sema.release()  # let next task begin
        await anyio.run_process(
            ['ffmpeg', '-i', f'{self.videos_dir}/{title}-video.m4s', '-i', f'{self.videos_dir}/{title}-audio.m4s',
             '-codec', 'copy', f'{self.videos_dir}/{title}.mp4', '-loglevel', 'quiet'])
        os.remove(f'{self.videos_dir}/{title}-video.m4s')
        os.remove(f'{self.videos_dir}/{title}-audio.m4s')
        self.progress.update(task_id, advance=1)
        print(f'{title} 完成')
        self.progress.update(task_id, visible=False)

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

    async def _get_media_part(self, media_urls: tuple, bytes_range: tuple, part_name, task_id, exception=False):
        start, end = bytes_range
        if os.path.exists(f'{self.videos_dir}/{part_name}.m4s'):
            downloaded = os.path.getsize(f'{self.videos_dir}/{part_name}.m4s')
            start += downloaded
            if not exception:
                self.progress.update(task_id, advance=downloaded)
        try:
            async with self.client.stream("GET", random.choice(media_urls),
                                          headers={'Range': f'bytes={start}-{end}'}) as r:
                async with await anyio.open_file(f'{self.videos_dir}/{part_name}.m4s', 'ab') as f:
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
                        self.progress.update(task_id, advance=len(chunk))
        except httpx.RemoteProtocolError:
            await self._get_media_part(media_urls, (start, end), part_name, task_id, exception=True)
        except httpx.ReadTimeout as e:
            rprint(f'[red]异常：{e.__class__}，该异常可能由于并发数过大导致，如果异常重复出现请考虑降低并发数')
            await self._get_media_part(media_urls, (start, end), part_name, task_id, exception=True)


if __name__ == '__main__':
    async def main():
        d = Downloader(part_concurrency=10, video_concurrency=5)
        # await d.get_series(
        #     'https://www.bilibili.com/video/BV1Rx411B7oa?spm_id_from=333.999.0.0'
        #     , quality=0)
        # await d.get_up_videos('18225678')
        # await d.get_cate_videos('宅舞', order='stow', days=30, keyword='超级敏感', num=100)
        # await d.get_video('https://www.bilibili.com/bangumi/play/ep471897?from_spmid=666.5.0.0')
        await d.get_favour('840276009', num=10)
        await d.aclose()


    asyncio.run(main())
