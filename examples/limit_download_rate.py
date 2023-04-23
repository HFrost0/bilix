"""
限制下载速度很简单
limit download rate is simple
"""
import asyncio
from bilix.sites.bilibili import DownloaderBilibili
from bilix.sites.cctv import DownloaderCctv


async def main():
    async with DownloaderBilibili(speed_limit=1e6) as d:  # limit to 1MB/s
        await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")


async def main2():
    # 就像并发控制一样，每个downloader的速度设置也是独立的
    # Like concurrency control, the speed settings of each downloader are independent
    async with DownloaderBilibili(speed_limit=1e6) as bili_d, DownloaderCctv(speed_limit=3e6) as cctv_d:
        await asyncio.gather(
            bili_d.get_series('https://www.bilibili.com/video/BV1cd4y1Z7EG'),
            cctv_d.get_series('https://www.douyin.com/video/7132430286415252773')
        )


if __name__ == '__main__':
    asyncio.run(main())
