# 异步基础
异步无疑是python中处理网络请求的最佳技术，因为它可以承载极高的并发量。
在python中使用bilix之前，你需要先对python中的异步编程有一些了解。python官方使用[asyncio](https://docs.python.org/3/library/asyncio.html)
提供异步I/O的支持。

```python
async def hello():
    print("hello world")
```

对于一个async函数（`def`变为`async def`）来说调用不会直接执行函数，而是返回一个协程（coroutine）对象

```python
c = hello()
>>> c
<coroutine object hello at 0x100a92540>

```

我们可以将这个coroutine提交到asyncio的事件循环中执行它

```python
import asyncio

>>> asyncio.run(c)
"hello world"
```

bilix的所有下载方法都是异步的，所以你也可以这样执行他们
```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili

d = DownloaderBilibili()
asyncio.run(d.get_video('url'))
```
