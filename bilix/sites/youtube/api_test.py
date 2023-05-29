import httpx
import pytest
from bilix.sites.youtube import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://www.youtube.com/watch?v=26lanyBFXw8")
    assert data.video_url and data.audio_url and data.title
