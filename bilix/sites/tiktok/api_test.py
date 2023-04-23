import httpx
import pytest
from bilix.sites.tiktok import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://www.tiktok.com/@lindaselection/video/7171715528124271877")
    assert data.nwm_urls
