import httpx
import pytest
import bilix.api.yhdmp as api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://www.yhdmp.cc/vp/22224-1-0.html")
    data = await api.get_m3u8_url(client, "https://www.yhdmp.cc/vp/22224-1-0.html")
    pass
