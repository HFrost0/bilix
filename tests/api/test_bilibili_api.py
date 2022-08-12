import pytest
import asyncio
from datetime import datetime, timedelta
import bilix.api.bilibili as api


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
    data = await api.get_cate_meta()
    assert '舞蹈' in data and "sub" in data["舞蹈"]
    assert "宅舞" in data and 'tid' in data['宅舞']


@pytest.mark.asyncio
async def test_get_list_info():
    list_name, up_name, bvids = await api.get_list_info(
        "https://space.bilibili.com/8251621/channel/seriesdetail?sid=2323334&ctype=0")
    assert list_name == 'mrfz'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_collect_info():
    list_name, up_name, bvids = await api.get_collect_info(
        "https://space.bilibili.com/54296062/channel/collectiondetail?sid=412818&ctype=0")
    assert list_name == 'asyncio协程'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_favour_page_info():
    fav_name, up_name, total_size, bvids = await api.get_favour_page_info(fid="69072721")
    assert fav_name == '默认收藏夹'
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_cate_page_info():
    time_to = datetime.now()
    time_from = time_to - timedelta(days=7)
    time_from, time_to = time_from.strftime('%Y%m%d'), time_to.strftime('%Y%m%d')
    meta = await api.get_cate_meta()
    bvids = await api.get_cate_page_info(cate_id=meta['宅舞']['tid'], time_from=time_from, time_to=time_to)
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_up_info():
    up_name, total_size, bvids = await api.get_up_info(mid="8251621")
    assert len(bvids) > 0 and bvids[0].startswith('BV')


@pytest.mark.asyncio
async def test_get_video_info():
    # 单个bv视频
    data = await api.get_video_info("https://www.bilibili.com/video/BV1sS4y1b7qb?spm_id_from=333.999.0.0")
    assert len(data.pages) == 1
    assert data.p == 0
    assert data.bvid
    # assert data.dash  # todo since GitHub action can not get dash, there is no dash check...
    # 多个bv视频
    data = await api.get_video_info("https://www.bilibili.com/video/BV1jK4y1N7ST?p=5")
    assert len(data.pages) > 1
    assert data.p == 4
    assert data.bvid
    # 电视剧
    data = await api.get_video_info("https://www.bilibili.com/bangumi/play/ss24053?spm_id_from=333.337.0.0")
    assert len(data.pages) > 1
    # 动漫
    data = await api.get_video_info("https://www.bilibili.com/bangumi/play/ss5043?spm_id_from=333.337.0.0")
    assert len(data.pages) > 1
    # 电影
    data = await api.get_video_info("https://www.bilibili.com/bangumi/play/ss33343?theme=movie&spm_id_from=333.337.0.0")
    assert data.title == '天气之子'
    # 纪录片
    data = await api.get_video_info("https://www.bilibili.com/bangumi/play/ss40509?from_spmid=666.9.hotlist.3")
    assert len(data.pages) > 1


@pytest.mark.asyncio
async def test_get_subtitle_info():
    data = await api.get_video_info("https://www.bilibili.com/video/BV1hS4y1m7Ma")
    data = await api.get_subtitle_info(data.bvid, data.cid)
    assert data[0][0].startswith('http')
    assert data[0][1]


@pytest.mark.asyncio
async def test_get_dm_info():
    data = await api.get_video_info("https://www.bilibili.com/bangumi/play/ss33343?theme=movie&spm_id_from=333.337.0.0")
    data = await api.get_dm_info(data.aid, data.cid)
    assert len(data) > 0
