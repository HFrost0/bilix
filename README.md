# Bilix

[![GitHub license](https://img.shields.io/github/license/HFrost0/bilix?style=flat-square)](https://github.com/HFrost0/bilix/blob/master/LICENSE)
![PyPI](https://img.shields.io/pypi/v/bilix?style=flat-square&color=blue)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/HFrost0/bilix)
![PyPI - Downloads](https://img.shields.io/pypi/dm/bilix?label=pypi%20downloads&style=flat-square)

⚡️快如闪电的 [bilibili](https://www.bilibili.com/) 视频下载工具，基于 Python 现代 Async 异步特性，高速批量下载整部动漫，电视剧，电影，up投稿...

<div align="center"> <img src='https://s1.ax1x.com/2022/05/03/OFh34O.gif' style="border-radius: 8px"> </div>

⚡️在200M宽带中实测可以拉满网速

<div align="center"> <img src='https://s1.ax1x.com/2022/05/03/OANTvF.gif' style="border-radius: 8px"> </div>

- [特性 Features](#%E7%89%B9%E6%80%A7-features)
- [依赖环境 Environment](#%E4%BE%9D%E8%B5%96%E7%8E%AF%E5%A2%83-environment)
- [快速上手 Quick Start](#%E5%BF%AB%E9%80%9F%E4%B8%8A%E6%89%8B-quick-start)
  - [批量下载](#%E6%89%B9%E9%87%8F%E4%B8%8B%E8%BD%BD)
  - [单个下载](#%E5%8D%95%E4%B8%AA%E4%B8%8B%E8%BD%BD)
  - [下载音频](#%E4%B8%8B%E8%BD%BD%E9%9F%B3%E9%A2%91)
  - [下载特定up主的投稿](#%E4%B8%8B%E8%BD%BD%E7%89%B9%E5%AE%9Aup%E4%B8%BB%E7%9A%84%E6%8A%95%E7%A8%BF)
  - [下载分区视频](#%E4%B8%8B%E8%BD%BD%E5%88%86%E5%8C%BA%E8%A7%86%E9%A2%91)
  - [下载收藏夹视频](#%E4%B8%8B%E8%BD%BD%E6%94%B6%E8%97%8F%E5%A4%B9%E8%A7%86%E9%A2%91)
  - [下载合集或视频列表](#%E4%B8%8B%E8%BD%BD%E5%90%88%E9%9B%86%E6%88%96%E8%A7%86%E9%A2%91%E5%88%97%E8%A1%A8)
  - [下载字幕，弹幕，封面...](#%E4%B8%8B%E8%BD%BD%E5%AD%97%E5%B9%95%E5%BC%B9%E5%B9%95%E5%B0%81%E9%9D%A2)
- [进阶使用 Advance Guide](#%E8%BF%9B%E9%98%B6%E4%BD%BF%E7%94%A8-advance-guide)
  - [你是大会员？🥸](#%E4%BD%A0%E6%98%AF%E5%A4%A7%E4%BC%9A%E5%91%98%F0%9F%A5%B8)
  - [在 python 中调用](#%E5%9C%A8-python-%E4%B8%AD%E8%B0%83%E7%94%A8)
  - [关于断点重连](#%E5%85%B3%E4%BA%8E%E6%96%AD%E7%82%B9%E9%87%8D%E8%BF%9E)
- [欢迎提问](#%E6%AC%A2%E8%BF%8E%E6%8F%90%E9%97%AE)
- [未来工作](#%E6%9C%AA%E6%9D%A5%E5%B7%A5%E4%BD%9C)
  - [已知的bug 🤡](#%E5%B7%B2%E7%9F%A5%E7%9A%84bug-)

## 特性 Features

高性能，高并发，Asynchronous everywhere，得益于Python对于协程的支持，以及现代 Async HTTP 框架 [httpx](https://www.python-httpx.org/)
，和 [anyio](https://anyio.readthedocs.io/en/stable/) ：

* 媒体文件（音频/视频）分段异步下载，以及备选服务器的同时利用
* 视频的音画异步下载与合成
* 视频之间乃至任务之间的异步下载
* 断点续传
* 用户可控的并发量设置
* 与高并发配合的很好的进度条
* HTTP/2协议支持

## 依赖环境 Environment

1. pip安装（需要python3.8及以上）

```shell
pip install bilix
```

2. [FFmpeg](https://ffmpeg.org/contact.html#MailingLists) ：一个命令行视频工具，用于合成下载的音频和视频

    * macOS 下可以通过`brew install ffmpeg`进行安装。
    * Windows 下载请至官网 https://ffmpeg.org/download.html#build-windows ，安装好后需要配置环境变量。
    * 最终确保在命令行中可以调用`ffmpeg`命令即可。

## 快速上手 Quick Start

bilix提供了简单的命令行使用方式，打开终端开始下载吧～

### 批量下载

批量下载整部动漫，电视剧，电影，up投稿.....只需要把命令中的`url`替换成你要下载的系列中任意一个视频的网页链接。\
到 bilibili 上找一个来试试吧～，比如这个李宏毅老师的机器学习视频：[链接](https://www.bilibili.com/video/BV1JE411g7XF)

```shell
bilix get_series 'url'
```

`bilix`会下载文件至命令行当前目录的`videos`文件夹中，默认自动创建。

💡提示：在zsh终端中可能要用`''`将url包住，其他终端暂未测试。

* 目前支持的类型
    * 投稿视频
    * 番剧
    * 电视剧
    * 纪录片
    * 电影

`get_series`很强大，会自动识别系列所有视频并下载，如果该系列只有一个视频（比如单p投稿）也是可以正常下载的。

💡什么是一个系列：比如一个多p投稿的所有p，一部动漫的所有集。

另外`get_series`支持集数选择参数`-p`，例如通过`-p 1 3`即可指定下载P1至P3的视频

### 单个下载

用户😨：我不想下载那么多，只想下载单个视频。没问题，试试这个，只需要提供那个视频的网页链接：

```shell
bilix get_video 'url'
```

### 下载音频

假设你喜欢音乐区，只想下载音频，那么可以使用可选参数`--only-audio`，例如下面是下载[A叔](https://space.bilibili.com/6075139)一个钢琴曲合集音频的例子

```shell
bilix get_series 'https://www.bilibili.com/video/BV1ts411D7mf' --only-audio
```

### 下载特定up主的投稿

假设你是一个嘉心糖，想要下载嘉然小姐最新投稿的100个视频，那么你可以使用命令：

```shell
bilix get_up '672328094' --num 100
```

`672328094`是up主的id，在up空间首页的url中就可以找到哦，例如： https://space.bilibili.com/672328094

### 下载分区视频

假设你喜欢看舞蹈区👍，想要下载最近30天播放量最高的20个超级敏感宅舞视频，那么你可以使用

```shell
bilix get_cate 宅舞 --keyword 超级敏感 --order click --num 20 --days 30
```

`get_cate`支持大部分分区，可以使用排序，关键词搜索等，详细请参考`bilix -h`或代码注释

### 下载收藏夹视频

如果你需要下载自己或者其他人收藏夹中的视频，你可以使用`get_favour`方法

```shell
bilix get_favour '1445680654' --num 20
```

`1445680654`
是收藏夹id，如果要知道一个收藏夹的id是什么，最简单的办法是在b站网页左侧列表中点击切换到该收藏夹，然后浏览器的url就会出现该收藏夹的id，例如 https://space.bilibili.com/11499954/favlist?fid=1445680654
，其中url中的`fid`就是收藏夹id。

### 下载合集或视频列表

如果你需要下载up主发布的合集或视频列表，你可以使用`get_collect`方法

```shell
bilix get_collect 'url'
```

将`url`替换为某个合集或视频列表详情页的url（例如[这个](https://space.bilibili.com/369750017/channel/collectiondetail?sid=630)）即可下载合集或列表内所有视频

💡合集和视频列表有什么区别？b站的合集可以订阅，列表则没有这个功能，但是他们都在up主空间页面的合集和列表菜单中，例如[这个](https://space.bilibili.com/369750017/channel/series)
，`get_collect`则会根据详情页url中的信息判断这个链接是合集还是列表

### 下载字幕，弹幕，封面...

在命令中加入可选参数`--subtitle`（字幕） `--dm`（弹幕） `--image`（封面），即可下载这些附属文件

```shell
bilix get_series 'url' --subtitle --dm --image
```

## 进阶使用 Advance Guide

请使用`bilix -h`查看更多参数提示，包括方法名简写（例如`get_series`简写为`s`），视频画面质量选择，并发量控制，下载目录等。

### 你是大会员？🥸

请在`--cookie`参数中填写浏览器缓存的`SESSDATA`cookie，填写后可以下载需要大会员的视频。

### 在 python 中调用

觉得命令行太麻烦，不够强大？想要直接调用模块？下面是一个小例子。

```python
import asyncio
from bilix import Downloader


async def main():
    d = Downloader(video_concurrency=5, part_concurrency=10)
    cor1 = d.get_series(
        'https://www.bilibili.com/bangumi/play/ss28277?spm_id_from=333.337.0.0'
        , quality=999)
    cor2 = d.get_up_videos(mid='436482484')
    cor3 = d.get_video('https://www.bilibili.com/bangumi/play/ep477122?from_spmid=666.4.0.0')
    await asyncio.gather(cor1, cor2, cor3)
    await d.aclose()


if __name__ == '__main__':
    asyncio.run(main())
```

`Downloader`类的下载方法都是异步的，例如`d.get_series(...)`返回的是一个协程`Coroutine`对象，我们可以自由组合这些方法的返回值，然后通过`await asyncio.gather`
方法并发执行这些任务。例如上面的例子中我们同时执行了三种不同的任务。

你要组合很多很多任务？不用担心！`d`对象执行这些任务的并发度受到初始化参数的严格控制🫡，`video_concurrency`控制了同时下载的视频数量，而`part_concurrency`
则控制了每个媒体文件（音频/画面）的分段并发数，如果你不太明白可以在代码和注释中找到他们的详细作用，或者就让他们保持默认吧。

### 关于断点重连

用户可以通过Ctrl+C中断任务，对于未完成的文件，重新执行命令会在之前的进度基础上下载，已完成的文件会进行跳过。但是对于未完成的文件，以下情况不能使用断点重连，建议清除未完成任务的临时文件再执行命令。

- 中断后改变画面质量
- 中断后改变分段并发数`part_concurrency`

🫠在0.6.4版本之前的断点重连存在bug，可能导致视频音画缺失，请通过命令升级最新版本

```
pip install bilix --upgrade
```

## 欢迎提问

由于本项目受到b站接口或者网站前端变动的影响，如果你发现任何bug或者其他问题，欢迎提issue，作者会保证最新版本可以正常运行。

如果觉得该项目对你有所帮助，可以给作者一个小小的Star🌟

## 未来工作

- [x] 下载视频封面
- [ ] 每日测试（GitHub Action），但目前Github Action不能正常访问b站？单元测试。
- [x] 支持下载字幕，目前已支持下载json，以及转换成srt格式
- [x] 支持弹幕下载，目前已支持下载protobuf的的弹幕文件，以及基于[biliass](https://github.com/yutto-dev/biliass)
  的ass格式转换 [issue](https://github.com/HFrost0/bilix/issues/7)
- [x] 支持用pip安装，并提供更简明的命令行调用方式
- [x] 支持层级文件夹
- [x] 支持更可控的中断（包含弹幕合成中断）
- [ ] 支持切片下载

### 已知的bug 🤡

* 当两个视频名字完全一样时，任务冲突但不会报错，可能导致视频缺胳膊少腿
* 暂不支持少数没有音画分开下载方式（dash）的视频
