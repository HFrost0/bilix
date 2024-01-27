# bilix

[![GitHub license](https://img.shields.io/github/license/HFrost0/bilix?style=flat-square)](https://github.com/HFrost0/bilix/blob/master/LICENSE)
![PyPI](https://img.shields.io/pypi/v/bilix?style=flat-square&color=blue)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/HFrost0/bilix)
![PyPI - Downloads](https://img.shields.io/pypi/dm/bilix?label=pypi%20downloads&style=flat-square)

⚡️Lightning-fast asynchronous download tool for bilibili and more | 快如闪电的异步下载工具，支持bilibili及更多


<div align="center"> <img src='https://s2.loli.net/2022/08/31/P5X8YAQ7WyNEbrq.gif' style="border-radius: 8px"> </div>

## Vesrion 1.x

Version 1.x is on alpha, refer to [link]() to see detals

## Features

### ⚡️ Fast & Async

Asynchronous high concurrency support, controllable concurrency and speed settings.

### 😉 Lightweight & User-friendly

Lightweight user-friendly CLI with progress notification, focusing on core functionality.

### 📝 Fully-featured

Submissions, anime, TV Series, video clip, audio, favourite, danmaku ,cover...

### 🔨 Extensible

Extensible Python module suitable for more download scenarios.

## Install

```shell
pip install bilix
```

for macOS, you can also install `bilix` by `brew`

```shell
brew install bilix
```

## Usage Example

* If you prefer to use command line interface (cli)

```shell
bilix v 'url'
```

> `v` is a method short alias for `get_video`

* If you prefer to code with python

```python
from bilix.sites.bilibili import DownloaderBilibili
import asyncio


async def main():
    async with DownloaderBilibili() as d:
        await d.get_video('url')


asyncio.run(main())
```

## Community

If you find any bugs or other issues, feel free to raise an [Issue](https://github.com/HFrost0/bilix/issues).

If you have new ideas or new feature requests👍，welcome to participate in
the [Discussion](https://github.com/HFrost0/bilix/discussions)

If you find this project helpful, you can support the author by [Star](https://github.com/HFrost0/bilix/stargazers)🌟

## Contribute

❤️ Welcome! Details can be found in [Contributing](https://github.com/HFrost0/bilix/blob/master/CONTRIBUTING_EN.md)
