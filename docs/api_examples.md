# API案例
bilix 提供了各个网站的api，如果你有需要当然可以使用，并且它们都是异步的
```python
import asyncio
from bilix.api import bilibili
from httpx import AsyncClient


async def main():
    # 需要先实例化一个用来进行http请求的client
    client = AsyncClient(**bilibili.dft_client_settings)
    data = await bilibili.get_video_info(client, 'https://www.bilibili.com/bangumi/play/ep90849')
    print(data)


asyncio.run(main())

```
