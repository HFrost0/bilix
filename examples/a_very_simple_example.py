"""
使用bilix在python中最简单的实践🤖
"""
import asyncio
# import下载器，里面有很多方法，例如get_series, get_video, get_favour，get_dm等等，总能找到符合你需求的
from bilix import DownloaderBilibili


async def main():
    # 你可以使用with上下文管理器来开启和关闭一个下载器
    async with DownloaderBilibili() as d:
        # 然后用await等待下载完成
        await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")


async def main2():
    d = DownloaderBilibili()
    await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")
    # 或者，手动关闭，一样很简单
    await d.aclose()


if __name__ == '__main__':
    asyncio.run(main())
