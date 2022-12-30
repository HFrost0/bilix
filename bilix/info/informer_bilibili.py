import asyncio
import httpx
from rich.tree import Tree

import bilix.api.bilibili as api
from bilix.log import logger
from bilix.utils import req_retry, convert_size, parse_bilibili_url
from bilix.handle import Handler
from bilix.info.base_informer import BaseInformer

__all__ = ['InformerBilibili']


class InformerBilibili(BaseInformer):
    def __init__(self, sess_data: str = ''):
        client = httpx.AsyncClient(**api.dft_client_settings)
        client.cookies.set('SESSDATA', sess_data)
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
        if video_info.dash is None:
            logger.warning(f'{video_info.h1_title} 需要大会员或该地区不支持')
            return

        async def ensure_size(m: api.Media):
            if m.size is None:
                res = await req_retry(self.client, m.base_url, method='GET', headers={'Range': 'bytes=0-1'})
                m.size = int(res.headers['Content-Range'].split('/')[-1])

        dash = video_info.dash
        cors = [ensure_size(m) for m in dash.videos] + [ensure_size(m) for m in dash.audios]
        await asyncio.gather(*cors)

        tree = Tree(
            f"[bold reverse] {video_info.h1_title} [/]"
            f" {video_info.status.view:,}👀 {video_info.status.like:,}👍 {video_info.status.coin:,}🪙",
            guide_style="bold cyan")
        video_tree = tree.add("[bold]画面 Video")
        audio_tree = tree.add("[bold]声音 Audio")
        leaf_fmt = "codec: {codec:32} size: {size}"
        # for video
        for quality in dash.video_formats:
            p_tree = video_tree.add(quality)
            for c in dash.video_formats[quality]:
                m = dash.video_formats[quality][c]
                p_tree.add(leaf_fmt.format(codec=m.codec, size=convert_size(m.size)))
            if len(p_tree.children) == 0:
                p_tree.style = "rgb(242,93,142)"
                p_tree.add("需要登录或大会员")
        # for audio
        name_map = {"default": "默认音质", "dolby": "杜比全景声 Dolby", "flac": "Hi-Res无损"}
        for k in dash.audio_formats:
            sub_tree = audio_tree.add(name_map[k])
            if m := dash.audio_formats[k]:
                sub_tree.add(leaf_fmt.format(codec=m.codec, size=convert_size(m.size)))
            else:
                sub_tree.style = "rgb(242,93,142)"
                sub_tree.add("需要登录或大会员")
        self.console.print(tree)


@Handler.register("bilibili info")
def handle(kwargs):
    key = kwargs['key']
    method = kwargs['method']
    if 'bilibili' in key and 'info' == method:
        informer = InformerBilibili(sess_data=kwargs['cookie'])
        cor = informer.info_key(key)
        return informer, cor
