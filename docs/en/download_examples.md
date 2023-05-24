# Download Examples

Command line is too cumbersome and not powerful enough for you? bilix can be used as a Python library
with user-friendly interfaces and enhanced functionality for greater flexibility.

## Start with the simplest

```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili


async def main():
    # you can use async with context manager to open and close a downloader
    async with DownloaderBilibili() as d:
        await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")


if __name__ == '__main__':
    asyncio.run(main())

```

## Combine multiple tasks and control concurrency

You can combine the coroutine objects returned by the downloader and use gather to execute them concurrently.
The concurrency is strictly restricted by the downloader object, ensuring no unexpected burden on the server.

```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili


async def main():
    d = DownloaderBilibili(video_concurrency=5, part_concurrency=10)
    cor1 = d.get_series(
        'https://www.bilibili.com/bangumi/play/ss28277'
        , quality=999)
    cor2 = d.get_up(url_or_mid='436482484', quality=999)
    cor3 = d.get_video('https://www.bilibili.com/bangumi/play/ep477122', quality=999)
    await asyncio.gather(cor1, cor2, cor3)
    await d.aclose()


if __name__ == '__main__':
    asyncio.run(main())


```

## Download a clip

You can download just a clip of the video

```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili


async def main():
    """download the 《嘉然我真的好喜欢你啊😭😭😭.mp4》 by timerange🤣"""
    async with DownloaderBilibili() as d:
        # time_range (start_time, end_time)
        await d.get_video('https://www.bilibili.com/video/BV1kK4y1A7tN', time_range=(0, 7))


if __name__ == '__main__':
    asyncio.run(main())

```

## Download from multiple sites simultaneously

You can initialize downloaders for different websites, and use the coroutine objects returned by their
methods for concurrent downloads. The concurrency control between different downloaders is independent, allowing you to
maximize the use of your network resources.

```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili
from bilix.sites.cctv import DownloaderCctv


async def main():
    async with DownloaderBilibili() as d_bl, DownloaderCctv() as d_tv:
        await asyncio.gather(
            d_bl.get_video('https://www.bilibili.com/video/BV1cd4y1Z7EG', quality=999),
            d_tv.get_video('https://tv.cctv.com/2012/05/02/VIDE1355968282695723.shtml', quality=999)
        )


if __name__ == '__main__':
    asyncio.run(main())

```

## Limit download speed

Limiting the download speed is very simple.
The following example limits the total download speed below 1MB/s

```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili
from bilix.sites.cctv import DownloaderCctv


async def main():
    async with DownloaderBilibili(speed_limit=1e6) as d:  # limit to 1MB/s
        await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")


if __name__ == '__main__':
    asyncio.run(main())

```

In addition, the speed settings between downloaders are also independent

```python
async def main():
    # 就像并发控制一样，每个downloader的速度设置也是独立的
    async with DownloaderBilibili(speed_limit=1e6) as bili_d, DownloaderCctv(speed_limit=3e6) as cctv_d:
        await asyncio.gather(
            bili_d.get_series('https://www.bilibili.com/video/BV1cd4y1Z7EG'),
            cctv_d.get_series('https://www.douyin.com/video/7132430286415252773')
        )
```

## Show progress bar

When using the python module, the progress bar is not displayed by default. If you want to display it, you can

```python
from bilix.progress.cli_progress import CLIProgress

CLIProgress.start()
```

or open via the `progress` object inside any downloader

```python
d.progress.start()
```

