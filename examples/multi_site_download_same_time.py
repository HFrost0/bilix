"""
你可以同时初始化不同网站的下载器，并且利用他们方法返回的协程对象进行并发下载。
各个下载器之间的并发控制是独立的，因此可以最大化利用自己的网络资源。

You can initialize the downloaders of different websites at the same time, and use the coroutine objects returned by
their methods to download concurrently. The concurrency control between each downloader is independent, so you can
maximize the use of your network resources.
"""
import asyncio
from bilix import DownloaderBilibili, DownloaderDouyin, DownloaderCctv


async def main():
    async with DownloaderBilibili() as d_bl, DownloaderDouyin() as d_dy, DownloaderCctv() as d_tv:
        await asyncio.gather(
            d_bl.get_video('https://www.bilibili.com/video/BV1cd4y1Z7EG', quality=999),
            d_dy.get_video('https://www.douyin.com/video/7132430286415252773'),
            d_tv.get_video('https://tv.cctv.com/2012/05/02/VIDE1355968282695723.shtml', quality=999)
        )


if __name__ == '__main__':
    asyncio.run(main())
