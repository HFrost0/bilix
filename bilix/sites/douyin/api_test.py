import httpx
import pytest
from bilix.sites.douyin import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://www.douyin.com/video/7132430286415252773")
    pass
