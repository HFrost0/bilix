import pytest
from bilix.info import InformerBilibili

informer = InformerBilibili()


@pytest.mark.asyncio
async def test_bilibili_informer():
    await informer.info_video('https://www.bilibili.com/video/BV1oG4y1Z7fx')
    await informer.info_video('https://www.bilibili.com/video/BV1eV411W7tt')
    await informer.info_video("https://www.bilibili.com/video/BV1Re4y1x7Ax")
