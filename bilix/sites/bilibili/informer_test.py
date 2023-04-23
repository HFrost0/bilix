import pytest
from bilix.sites.bilibili import InformerBilibili

informer = InformerBilibili()


@pytest.mark.asyncio
async def test_bilibili_informer():
    await informer.info_video('https://www.bilibili.com/video/BV1sG411A7r3')
    await informer.info_video('https://www.bilibili.com/video/BV1oG4y1Z7fx')
    await informer.info_video('https://www.bilibili.com/video/BV1eV411W7tt')
    await informer.info_video("https://www.bilibili.com/bangumi/play/ep508404/")
