import os
import pytest
from bilix.dm import dm2ass_factory


@pytest.mark.asyncio
async def test_dm2ass():
    dm2ass = dm2ass_factory(1920, 1080)
    path = os.path.dirname(__file__)
    with open(f'{path}/test_dm.bin', 'rb') as f:
        content = f.read()
    data = await dm2ass(content)
    data.decode('utf8')
