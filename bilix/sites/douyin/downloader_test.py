import pytest
from bilix.sites.douyin import DownloaderDouyin


@pytest.mark.asyncio
async def test_get_video():
    async with DownloaderDouyin() as d:
        await d.get_video('https://v.douyin.com/r4tm4Pe/')

