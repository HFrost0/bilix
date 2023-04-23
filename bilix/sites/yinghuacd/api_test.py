import httpx
import pytest
from bilix.sites.yinghuacd import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "http://www.yinghuacd.com/v/5606-7.html")
    pass
