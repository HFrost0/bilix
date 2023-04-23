# API Examples
bilix provides the APIs of various websites, and they are all asynchronous
```python
import asyncio
from bilix.sites.bilibili import api
from httpx import AsyncClient


async def main():
    # instantiate a httpx client for making http requests
    client = AsyncClient(**api.dft_client_settings)
    data = await api.get_video_info(client, 'https://www.bilibili.com/bangumi/play/ep90849')
    print(data)


asyncio.run(main())

```
