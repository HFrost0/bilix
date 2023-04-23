import httpx
import pytest
from bilix.sites.bilibili import DownloaderBilibili


@pytest.mark.asyncio
async def test_get_collect_or_list():
    d = DownloaderBilibili()
    await d.get_collect_or_list('https://space.bilibili.com/54296062/channel/collectiondetail?sid=412818&ctype=0',
                                quality=999)
    await d.get_collect_or_list('https://space.bilibili.com/8251621/channel/seriesdetail?sid=2323334&ctype=0',
                                quality=999)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_favour():
    d = DownloaderBilibili()
    await d.get_favour("69072721", num=1, quality=999)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_cate():
    d = DownloaderBilibili()
    await d.get_cate("宅舞", num=1, order="click", keyword="jk", quality=1)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_up():
    d = DownloaderBilibili()
    await d.get_up("455511061", num=1, order="pubdate", quality=1)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_series():
    d = DownloaderBilibili()
    await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=3", p_range=(5, 5), quality=999)
    # only audio
    await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=3", p_range=(5, 5), only_audio=True)
    # image
    await d.get_series("https://www.bilibili.com/video/BV1jK4y1N7ST?p=3", p_range=(1, 1), image=True, quality=999)
    # 单个视频
    await d.get_series("https://www.bilibili.com/video/BV1sS4y1b7qb?spm_id_from=333.999.0.0", quality=999)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_dm():
    d = DownloaderBilibili()
    await d.get_dm('https://www.bilibili.com/video/BV11Z4y1z7s8?spm_id_from=333.337.search-card.all.click')
    await d.aclose()


@pytest.mark.asyncio
async def test_get_subtitle():
    d = DownloaderBilibili()
    await d.get_subtitle("https://www.bilibili.com/video/BV1hS4y1m7Ma")
    await d.aclose()


@pytest.mark.asyncio
async def test_choose_quality():
    import os
    from bilix.sites.bilibili import api

    client = httpx.AsyncClient()
    client.cookies.set('SESSDATA', os.getenv('BILI_TOKEN'))
    # dolby
    data = await api.get_video_info(client, "https://www.bilibili.com/video/BV13L4y1K7th")
    try:
        video, audio = data.dash.choose_quality(quality=999, codec=":ec-3")
    except KeyError:
        assert not os.getenv("BILI_TOKEN")
    # normal
    data.dash.choose_quality(quality="360P", codec="hev")
    # hi-res
    data = await api.get_video_info(client, "https://www.bilibili.com/video/BV16K411S7sk")
    try:
        video, audio = data.dash.choose_quality(quality='1080P', codec="hev:fLaC")
    except KeyError:
        assert not os.getenv("BILI_TOKEN")
