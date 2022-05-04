import pytest
from bilix import Downloader


@pytest.mark.asyncio
async def test_get_series():
    d = Downloader()
    await d.get_series('https://www.bilibili.com/video/BV1sa411b786')
    await d.aclose()


@pytest.mark.asyncio
async def test_get_up():
    d = Downloader()
    await d.get_up_videos('436482484', total=1)
    await d.aclose()


@pytest.mark.asyncio
async def test_get_cate():
    d = Downloader()
    await d.get_cate_videos('宅舞', num=1)
    await d.aclose()


