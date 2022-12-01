import httpx
import pytest
import asyncio
import bilix.api.jable as api

client = httpx.AsyncClient(headers={'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://jable.tv'})


@pytest.mark.asyncio
async def test_get_video_info():
    data = await api.get_video_info(client, "https://jable.tv/videos/ssis-533/")
    assert data.model_name
    data = await api.get_video_info(client, "https://jable.tv/videos/ssis-448/")
    assert data.model_name


@pytest.mark.asyncio
async def test_get_model_info():
    data = await api.get_model_info(client, 'https://jable.tv/models/393ec3548aecc34004d54e03becd2ea9/')
    assert data['model_name'].encode('utf8') == b'\xe4\xbd\x90\xe4\xb9\x85\xe8\x89\xaf\xe5\x92\xb2\xe5\xb8\x8c'
    assert data['urls']
