import httpx
import pytest
import asyncio
import bilix.api.jable as api

client = httpx.AsyncClient(headers={'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://jable.tv'})


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://jable.tv/videos/ssis-448/")
    assert data.model_name
    data = await api.get_video_info(client, "https://jabel.tv/videos/ssis-533/")
    assert data.model_name
