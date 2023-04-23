# Async basic
Asynchronous programming in Python excels at handling network requests with high concurrency.
Before using bilix in Python, you need to have some understanding of asynchronous programming in Python.
The official Python [asyncio](https://docs.python.org/3/library/asyncio.html) library provides support for asynchronous I/O.

```python
async def hello():
    print("hello world")
```

For an async function (async def), calling it will not directly execute the function but instead return a coroutine object.
```python
c = hello()
>>> c
<coroutine object hello at 0x100a92540>

```

We can submit the coroutine obj to asyncio's event loop to execute it

```python
import asyncio

>>> asyncio.run(c)
"hello world"
```

All download methods of bilix are asynchronous, so you can execute them like this
```python
import asyncio
from bilix.sites.bilibili import DownloaderBilibili

d = DownloaderBilibili()
asyncio.run(d.get_video('url'))
```
