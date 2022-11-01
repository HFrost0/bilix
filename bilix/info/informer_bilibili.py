import httpx
import re
import bilix.api.bilibili as api
from bilix.assign import Handler
from bilix.info.base_informer import BaseInformer

__all__ = ['InformerBilibili']


def parse_bilibili_url(url: str):
    if re.match(r'https://space\.bilibili\.com/\d+/favlist\?fid=\d+$', url):
        return 'fav'
    elif re.match(r'https://space\.bilibili\.com/\d+/channel/seriesdetail\?sid=\d+$', url):
        return 'list'
    elif re.match(r'https://space\.bilibili\.com/\d+/channel/collectiondetail\?sid=\d+$', url):
        return 'col'
    elif re.match(r'https://space\.bilibili\.com/\d+$', url):  # up space url
        return 'up'
    elif re.search(r'www\.bilibili\.com', url):
        return 'video'
    raise ValueError(f'{url} no match for bilibili')


class InformerBilibili(BaseInformer):
    def __init__(self, sess_data):
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
        pass


@Handler("bilibili info")
def handle(**kwargs):
    key = kwargs['key']
    method = kwargs['method']
    if 'bilibili' in key and 'info' == method:
        informer = InformerBilibili(sess_data=kwargs['cookie'])
        cor = informer.info_key(key)
        return informer, cor
