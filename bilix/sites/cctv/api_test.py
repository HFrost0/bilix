import httpx
import pytest
from bilix.sites.cctv import api

client = httpx.AsyncClient(**api.dft_client_settings)


@pytest.mark.asyncio
async def test_get_video_info():
    pid, vide, vida = await api.get_id(client, "https://tv.cctv.com/2012/05/02/VIDE1355968282695723.shtml")
    data = await api.get_media_info(client, pid)
    data = await api.get_series_info(client, vide, vida)
    pass
