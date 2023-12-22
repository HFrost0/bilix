import httpx
import pytest
from bilix.sites.pronhub import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://cn.pornhub.com/view_video.php?viewkey=6562b25f656ea")
    assert data.qualities


@pytest.mark.asyncio
async def test_get_uploader_info():
    data = await api.get_uploader_urls(client, "https://cn.pornhub.com/model/hongkongdoll/videos")
    assert data
