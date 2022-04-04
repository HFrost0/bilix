"""
ffmpeg should be installed
pip install 'httpx[http2]' rich
"""
import asyncio
import anyio
import httpx
import re
import random
import json
import os
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from itertools import groupby


class Downloader:
    def __init__(self, videos_dir='videos', max_concurrency=2, sess_data=''):
        """

        :param videos_dir: 下载到哪个目录，默认当前目录下的为videos中，如果路径不存在将自动创建
        :param max_concurrency: 限制最大同时下载的视频数量
        :param sess_data: 有条件的用户填写大会员凭证，填写后可下载大会员资源
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
        self.sema = asyncio.Semaphore(max_concurrency)

    async def aclose(self):
        self.progress.stop()
        await self.client.aclose()

    async def get_series(self, url: str, quality: int = 0):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param url: 系列中任意一个视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :return:
        """
        url = url.split('?')[0]
        res = await self.client.get(url)
        initial_state = re.search(r'<script>window.__INITIAL_STATE__=({.*});', res.text).groups()[0]
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
            raise Exception('未知类型')
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
        res = await self.client.get(url)
        title = re.search('<h1 title="([^"]*)"', res.text).groups()[0].strip()
        if add_name:
            title += f'-{add_name.strip()}'
        # replace windows illegal character in title
        title = re.sub(r"[/\\:*?\"<>|]", '', title)
        if os.path.exists(f'{self.videos_dir}/{title}.mp4'):
            print(f'{title}.mp4 已经存在')
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
            print(f'{title} 需要大会员，或该地区不支持')
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

    async def _get_media(self, media_urls: tuple, media_name, task_id, concurrency=5):
        res = await self.client.head(random.choice(media_urls))
        total = int(res.headers['Content-Length'])
        self.progress.update(task_id, total=self.progress.tasks[task_id].total + total)
        part_length = total // concurrency
        cos = []
        part_names = []
        for i in range(concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < concurrency - 1 else total - 1
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cos.append(self._get_media_part(media_urls, (start, end), part_name, task_id))
        await asyncio.gather(*cos)
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


if __name__ == '__main__':
    async def main():
        d = Downloader(max_concurrency=2)
        await d.get_series(
            'https://www.bilibili.com/video/BV1y34y1s7J7?spm_id_from=333.337.search-card.all.click'
            , quality=0)
        await d.aclose()


    asyncio.run(main())
