import asyncio
import httpx
from rich.tree import Tree

import bilix.api.bilibili as api
from bilix.log import logger
from bilix.utils import req_retry, convert_size, parse_bilibili_url
from bilix.assign import Handler
from bilix.info.base_informer import BaseInformer

__all__ = ['InformerBilibili']


class InformerBilibili(BaseInformer):
    def __init__(self, sess_data: str = ''):
        cookies = {'SESSDATA': sess_data}
        headers = {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}
        client = httpx.AsyncClient(headers=headers, cookies=cookies, http2=True)
        super().__init__(client)
        self.type_map = {
            'up': self.info_up,
            'fav': self.info_fav,
            'list': self.info_list,
            'col': self.info_col,
            'video': self.info_video
        }

    async def info_key(self, key):
        t = parse_bilibili_url(key)
        return await self.type_map[t](key)

    async def info_up(self, url: str):
        up_name, total_size, bvids = await api.get_up_info(self.client, url)
        self.console.print(up_name)

    async def info_fav(self, url: str):
        pass

    async def info_list(self, url: str):
        pass

    async def info_col(self, url: str):
        pass

    async def info_video(self, url: str):
        video_info = await api.get_video_info(self.client, url)
        dash = video_info.dash
        if video_info.dash is None:
            logger.warning(f'{video_info.h1_title} 需要大会员或该地区不支持')
            return

        async def ensure_size(data):
            if 'size' not in data:
                res = await req_retry(self.client, data['base_url'], method='GET', headers={'Range': 'bytes=0-1'})
                data['size'] = int(res.headers['Content-Range'].split('/')[-1])

        cors = [ensure_size(d) for d in dash['video']]
        cors.append(ensure_size(dash['audio'][0]))
        if dash['dolby']['audio']:
            cors.append(ensure_size(dash['dolby']['audio'][0]))
        if dash.get('flac', None) and dash['flac']['audio']:  # for some video there is no 'flac' key
            cors.append(ensure_size(dash['flac']['audio']))
        await asyncio.gather(*cors)

        tree = Tree(
            f"[bold reverse] {video_info.h1_title} [/]"
            f" {video_info.status['view']:,}👀 {video_info.status['like']:,}👍 {video_info.status['coin']:,}🪙",
            guide_style="bold cyan")
        video_tree = tree.add("[bold]画面 Video")
        audio_tree = tree.add("[bold]声音 Audio")
        # for video
        for f in video_info.support_formats:
            p_tree = video_tree.add(f['new_description'])
            q_id = f['quality']
            for v in dash['video']:  # todo can be speed up...
                if v['id'] == q_id:
                    p_tree.add(f"codec: {v['codecs']:32} total: {convert_size(v['size'])}")
            if len(p_tree.children) == 0:
                p_tree.style = "rgb(242,93,142)"
                p_tree.add("需要登录或大会员")
        # for audio
        audio_tree.add("默认音质").add(
            f"codec: {dash['audio'][0]['codecs']:32} total: {convert_size(dash['audio'][0]['size'])}")
        if dash['dolby']['type'] != 0:
            sub_tree = audio_tree.add("杜比全景声 Dolby")
            if dash['dolby']['audio']:
                sub_tree.add(
                    f"codec: {dash['dolby']['audio'][0]['codecs']:32}"
                    f" total: {convert_size(dash['dolby']['audio'][0]['size'])}")
            else:
                sub_tree.style = "rgb(242,93,142)"
                sub_tree.add("需要登录或大会员")
        if dash.get('flac', None):
            sub_tree = audio_tree.add("Hi-Res无损")
            if dash['flac']['audio']:
                sub_tree.add(
                    f"codec: {dash['flac']['audio']['codecs']:32}"
                    f" total: {convert_size(dash['flac']['audio']['size'])}")
            else:
                sub_tree.style = "rgb(242,93,142)"
                sub_tree.add("需要登录或大会员")
        self.console.print(tree)


@Handler("bilibili info")
def handle(**kwargs):
    key = kwargs['key']
    method = kwargs['method']
    if 'bilibili' in key and 'info' == method:
        informer = InformerBilibili(sess_data=kwargs['cookie'])
        cor = informer.info_key(key)
        return informer, cor
