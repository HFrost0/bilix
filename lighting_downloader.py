"""
ffmpeg should be installed
pip install 'httpx[http2]' bs4 rich
"""
import asyncio
import anyio
import httpx
import re
import json
import os
import rich
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn
from itertools import groupby
from bs4 import BeautifulSoup


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
            rich.progress.TimeRemainingColumn())
        self.progress.start()
        self.sema = asyncio.Semaphore(max_concurrency)

    async def aclose(self):
        self.progress.stop()
        await self.client.aclose()

    async def get_series(self, front_url: str, quality: int = 0):
        """
        下载某个系列（包括up发布的多p投稿，动画，电视剧，电影等）的所有视频。只有一个视频的情况下仍然可用该方法

        :param front_url: 系列中任意一个视频的url
        :param quality: 下载视频画面的质量，默认0为可下载的最高画质，数字越大质量越低，数值超过范围时默认选取最低画质
        :return:
        """
        front_url = front_url.split('?')[0]
        res = await self.client.get(front_url)
        initial_state = re.search(r'<script>window.__INITIAL_STATE__=({.*});', res.text).groups()[0]
        initial_state = json.loads(initial_state)
        video_urls = []
        add_names = []
        if 'videoData' in initial_state:  # bv视频
            for idx, i in enumerate(initial_state['videoData']['pages']):
                video_urls.append(f"{front_url}?p={idx + 1}")
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
        soup = BeautifulSoup(res.text, 'html.parser')
        title = re.sub(r"[/\\:*?\"<>|]", '',  # replace windows illegal character in title
                       f"{soup.h1['title'].strip()}-{add_name}" if add_name else soup.h1['title'].strip())
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
                video_url = next(i)['base_url']
                if quality == q:
                    break
            audio_url = play_info['data']['dash']['audio'][0]['base_url']
        except (KeyError, AttributeError):  # KeyError-电影，AttributeError-动画
            print(f'{title} 需要大会员，或该地区不支持')
            self.sema.release()
            return
        task_id = self.progress.add_task(total=1,
                                         description=title if len(title) < 43 else f'{title[:20]}...{title[-20:]}')
        await asyncio.gather(
            self._get_media(video_url, f'{title}-video', task_id),
            self._get_media(audio_url, f'{title}-audio', task_id)
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

    async def _get_media(self, media_url, media_name, task_id, concurrency=5):
        res = await self.client.head(media_url)
        total = int(res.headers['Content-Length'])
        self.progress.update(task_id, total=self.progress.tasks[task_id].total + total)
        part_length = total // concurrency
        cos = []
        part_names = []
        for i in range(concurrency):
            start = i * part_length
            end = (i + 1) * part_length - 1 if i < concurrency - 1 else total - 1
            range_header = {'Range': f'bytes={start}-{end}'}
            part_name = f'{media_name}-{start}-{end}'
            part_names.append(part_name)
            cos.append(self._get_media_part(media_url, range_header, part_name, task_id))
        await asyncio.gather(*cos)
        async with await anyio.open_file(f'{self.videos_dir}/{media_name}.m4s', 'wb') as f:
            for part_name in part_names:
                async with await anyio.open_file(f'{self.videos_dir}/{part_name}.m4s', 'rb') as pf:
                    await f.write(await pf.read())
                os.remove(f'{self.videos_dir}/{part_name}.m4s')

    async def _get_media_part(self, media_url, range_header, part_name, task_id):
        try:
            async with self.client.stream("GET", media_url, headers=range_header) as r:
                async with await anyio.open_file(f'{self.videos_dir}/{part_name}.m4s', 'ab') as f:
                    downloaded = r.num_bytes_downloaded
                    async for chunk in r.aiter_bytes():
                        await f.write(chunk)
                        self.progress.update(task_id, advance=r.num_bytes_downloaded - downloaded)
                        downloaded = r.num_bytes_downloaded
        except httpx.RemoteProtocolError:
            start, end = range_header['Range'][6:].split('-')
            start = int(start) + downloaded
            range_header = {'Range': f'bytes={start}-{end}'}
            await self._get_media_part(media_url, range_header, part_name, task_id)


if __name__ == '__main__':
    async def main():
        d = Downloader(max_concurrency=2)
        await d.get_series(
            'https://www.bilibili.com/bangumi/play/ss20490?spm_id_from=333.337.0.0'
            , quality=0)
        await d.aclose()


    asyncio.run(main())
