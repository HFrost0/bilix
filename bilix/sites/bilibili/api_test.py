import httpx
import pytest
import asyncio
from datetime import datetime, timedelta
from bilix.sites.bilibili import api

client = httpx.AsyncClient(**api.dft_client_settings)


# https://stackoverflow.com/questions/61022713/pytest-asyncio-has-a-closed-event-loop-but-only-when-running-all-tests
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_get_cate_meta():
    data = await api.get_cate_meta(client)
    assert '舞蹈' in data and "sub" in data["舞蹈"]
    assert "宅舞" in data and 'tid' in data['宅舞']


@pytest.mark.asyncio
async def test_get_list_info():
    list_name, up_name, bvids = await api.get_list_info(
        client,
        "https://space.bilibili.com/369750017/channel/seriesdetail?sid=2458228")
    assert list_name == '瘦腰腹跟练'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_collect_info():
    list_name, up_name, bvids = await api.get_collect_info(
        client,
        "https://space.bilibili.com/54296062/channel/collectiondetail?sid=412818&ctype=0")
    assert list_name == 'asyncio协程'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_favour_page_info():
    fav_name, up_name, total_size, bvids = await api.get_favour_page_info(client, "69072721")
    assert fav_name == '默认收藏夹'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_cate_page_info():
    time_to = datetime.now()
    time_from = time_to - timedelta(days=7)
    time_from, time_to = time_from.strftime('%Y%m%d'), time_to.strftime('%Y%m%d')
    meta = await api.get_cate_meta(client)
    bvids = await api.get_cate_page_info(client, cate_id=meta['宅舞']['tid'], time_from=time_from, time_to=time_to)
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_up_video_info():
    up_name, total_size, bvids = await api.get_up_video_info(client, "316568752", keyword="什么")
    assert len(bvids) > 0 and bvids[0].startswith('BV')


# GitHub actions problem...
# @pytest.mark.asyncio
# async.md def test_get_special_audio():
#     # Dolby
#     data = await api.get_video_info(client, 'https://www.bilibili.com/video/BV13L4y1K7th')
#     assert data.dash['dolby']['type'] != 0
#     # Hi-Res
#     data = await api.get_video_info(client, 'https://www.bilibili.com/video/BV16K411S7sk')
#     assert data.dash['flac']['display']


@pytest.mark.asyncio
async def test_get_video_info():
    methods = (api._get_video_info_from_html, api._get_video_info_from_api)
    for method in methods:
        # 单个bv视频
        data = await method(client, "https://www.bilibili.com/video/BV1sS4y1b7qb?spm_id_from=333.999.0.0")
        assert len(data.pages) == 1
        assert data.p == 0
        assert data.bvid
        assert data.img_url.startswith('http://') or data.img_url.startswith('https://')
        assert data.dash
        # 多个bv视频
        data = await method(client, "https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")
        assert len(data.pages) > 1
        assert data.p == 4
        assert data.bvid
        if method is api._get_video_info_from_api:
            continue
        # 电视剧
        data = await method(client, "https://www.bilibili.com/bangumi/play/ss24053?spm_id_from=333.337.0.0")
        assert len(data.pages) > 1
        assert data.status.follow
        # 动漫
        data = await method(client, "https://www.bilibili.com/bangumi/play/ss5043?spm_id_from=333.337.0.0")
        assert len(data.pages) > 1
        assert data.status.follow
        # 电影
        data = await method(client,
                            "https://www.bilibili.com/bangumi/play/ss33343?theme=movie&spm_id_from=333.337.0.0")
        assert data.title == '天气之子'
        assert data.status.follow
        # 纪录片
        data = await method(client, "https://www.bilibili.com/bangumi/play/ss40509?from_spmid=666.9.hotlist.3")
        assert len(data.pages) > 1
        assert data.status.follow


@pytest.mark.asyncio
async def test_get_subtitle_info():
    data = await api.get_video_info(client, "https://www.bilibili.com/video/BV1hS4y1m7Ma")
    data = await api.get_subtitle_info(client, data.bvid, data.cid)
    assert data[0][0].startswith('http')
    assert data[0][1]


@pytest.mark.asyncio
async def test_get_dm_info():
    data = await api.get_video_info(client,
                                    "https://www.bilibili.com/bangumi/play/ss33343?theme=movie&spm_id_from=333.337.0.0")
    data = await api.get_dm_urls(client, data.aid, data.cid)
    assert len(data) > 0
