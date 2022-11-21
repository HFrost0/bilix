import httpx
import pytest
import asyncio
import bilix.api.hanime1 as api

client = httpx.AsyncClient(headers={'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://hanime1.me'})


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://hanime1.me/watch?v=39123")
    assert data.title
    data = await api.get_video_info(client, "https://hanime1.me/watch?v=13658")
    assert data.title
