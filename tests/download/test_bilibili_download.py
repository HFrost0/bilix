import pytest
from bilix.download import Downloader

d = Downloader()


@pytest.mark.asyncio
async def test_get_dm():
    await d.get_dm('https://www.bilibili.com/video/BV11Z4y1z7s8?spm_id_from=333.337.search-card.all.click')
