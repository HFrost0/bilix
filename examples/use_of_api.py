"""
bilix 提供了各个网站的api，如果你有需要当然可以使用，并且它们都是异步的
"""
import asyncio

from bilix.api import bilibili
from httpx import AsyncClient


async def main():
    # 需要先实例化一个用来进行http请求的client
    client = AsyncClient(
        headers={'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'},
        # bilibili 全面支持http2协议，因此我们打开http2，这会使得我们的速度更快，同时给b站服务器造成的压力更小
        http2=True
    )
    data = await bilibili.get_video_info(client, 'https://www.bilibili.com/bangumi/play/ep90849')
    print(data)


asyncio.run(main())
