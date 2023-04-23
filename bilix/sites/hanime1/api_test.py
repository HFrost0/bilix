import httpx
import pytest
from bilix.sites.hanime1 import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://hanime1.me/watch?v=39123")
    assert data.title
    data = await api.get_video_info(client, "https://hanime1.me/watch?v=13658")
    assert data.title
