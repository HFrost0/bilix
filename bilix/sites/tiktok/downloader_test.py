import pytest
from bilix.sites.tiktok import DownloaderTiktok


@pytest.mark.asyncio
async def test_get_video():
    async with DownloaderTiktok() as d:
        await d.get_video('https://www.tiktok.com/@evil0ctal/video/7168978761973550378')

