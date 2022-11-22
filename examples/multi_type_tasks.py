"""
你可以组合下载器返回的协程对象，利用gather并发执行他们，他们执行的并发度收到下载器对象的严格约束，因此不会对服务器造成意想不到的负担。

You can combine coroutine objects returned by the downloader and use gather to execute them concurrently.
The concurrency is strictly constrained by the downloader object, so it will not cause unexpected burden on
the site server.
"""
import asyncio
from bilix import DownloaderBilibili


async def main():
    d = DownloaderBilibili(video_concurrency=5, part_concurrency=10)
    cor1 = d.get_series(
        'https://www.bilibili.com/bangumi/play/ss28277?spm_id_from=333.337.0.0'
        , quality=999)
    cor2 = d.get_up_videos(url_or_mid='436482484', quality=999)
    cor3 = d.get_video('https://www.bilibili.com/bangumi/play/ep477122?from_spmid=666.4.0.0', quality=999)
    await asyncio.gather(cor1, cor2, cor3)
    await d.aclose()


if __name__ == '__main__':
    asyncio.run(main())
