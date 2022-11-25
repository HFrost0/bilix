import pytest
from bilix.download import DownloaderTikTok


@pytest.mark.asyncio
async def test_get_video():
    async with DownloaderTikTok() as d:
        await d.get_video('https://www.tiktok.com/@evil0ctal/video/7168978761973550378')

