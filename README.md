# Lighting-bilibili-download
⚡️快如闪电的 [bilibili](https://www.bilibili.com/) 视频下载工具，基于 Python 现代 Async 异步特性，高速批量下载整部动漫，电视剧，电影，up投稿...

<div align="center"> <img src='https://s1.ax1x.com/2022/05/03/OFh34O.gif' style="border-radius: 8px"> </div>

⚡️在200M宽带中实测可以拉满网速

<div align="center"> <img src='https://s1.ax1x.com/2022/05/03/OANTvF.gif' style="border-radius: 8px"> </div>

## 特性 Features
高性能，高并发，Asynchronous everywhere，得益于Python对于协程的支持，以及现代 Async HTTP 框架 [httpx](https://www.python-httpx.org/) ，和 [anyio](https://anyio.readthedocs.io/en/stable/) ：
* 媒体文件（音频/视频）分段异步下载，以及备选服务器的同时利用
* 视频的音画异步下载
* 视频之间乃至任务之间的异步下载
* 断点续传
* 用户可控的并发量设置
* 与高并发配合的很好的进度条
* HTTP/2协议支持
* 异步文件I/O和异步视频合成

## 依赖环境 Environment
1. Python 相关依赖（需要python3.8及以上）
```shell
pip install 'httpx[http2]' rich json5 protobuf
```
2. [FFmpeg](https://ffmpeg.org/contact.html#MailingLists) ：一个命令行视频工具，用于合成下载的音频和视频

    * macOS 下可以通过`brew install ffmpeg`进行安装。
    * Windows 下载请至官网 https://ffmpeg.org/download.html#build-windows ，安装好后需要配置环境变量。
    * 最终确保在命令行中可以调用`ffmpeg`命令即可。

## 快速上手 Quick Start
### 批量下载
批量下载整部动漫，电视剧，电影，up投稿.....只需要把命令中的`url`替换成你要下载的系列中任意一个视频的网页链接。\
到 bilibili 上找一个来试试吧～，比如这个李宏毅老师的机器学习视频：[链接](https://www.bilibili.com/video/BV1JE411g7XF)
```shell
python bili_cmd.py get_series 'url'
```
会下载文件至当前目录的`videos`文件夹中，默认自动创建。

💡提示：在zsh终端中可能要用`''`将url包住，其他终端暂未测试。
* 目前支持的类型
  * 投稿视频
  * 番剧
  * 电视剧
  * 纪录片
  * 电影

`get_series`很强大，会自动识别系列所有视频并下载，如果该系列只有一个视频（比如单p投稿）也是可以正常下载的。

💡什么是一个系列：比如一个多p投稿的所有p，一部动漫的所有集。
### 单个下载
用户😨：我不想下载那么多，只想下载单个视频。没问题，试试这个，只需要提供那个视频的网页链接：
```shell
python bili_cmd.py get_video 'url'
```
### 下载音频
假设你喜欢音乐区，只想下载音频，那么可以使用可选参数`--only_audio`，例如下面是下载[A叔](https://space.bilibili.com/6075139)一个钢琴曲合集音频的例子
```shell
python bili_cmd.py get_series 'https://www.bilibili.com/video/BV1ts411D7mf' --only_audio
```

### 下载特定up主的投稿

假设你是一个嘉心糖，想要下载嘉然小姐最新投稿的100个视频，那么你可以使用命令：
```shell
python bili_cmd.py get_up '672328094' -num 100
```
`672328094`是up主的id，在up空间首页的url中就可以找到哦，例如： https://space.bilibili.com/672328094

### 下载分区视频
假设你喜欢看舞蹈区👍，想要下载最近30天播放量最高的20个超级敏感宅舞视频，那么你可以使用
```shell
python bili_cmd.py get_cate 宅舞 -keyword 超级敏感 -order click -num 20 -days 30
```
`get_cate`支持大部分分区，可以使用排序，关键词搜索等，详细请参考`python bili_cmd.py -h`或代码注释

### 下载收藏夹视频
如果你需要下载自己或者其他人收藏夹中的视频，你可以使用`get_favour`方法
```shell
python bili_cmd.py get_favour '1445680654' -num 20
```
`1445680654`是收藏夹id，如果要知道一个收藏夹的id是什么，最简单的办法是在b站网页左侧列表中点击切换到该收藏夹，然后浏览器的url就会出现该收藏夹的id，例如 https://space.bilibili.com/11499954/favlist?fid=1445680654 ，其中url中的`fid`就是收藏夹id。

### 下载合集
如果你需要下载up主发布的合集，你可以使用`get_collect`方法
```shell
python bili_cmd.py get_collect '630'
```
`630`是合集id，如果要知道一个合集的id是什么，最简单的办法是在该合集详情页的url找到`sid`参数，例如 https://space.bilibili.com/369750017/channel/collectiondetail?sid=630


## 进阶使用 Advance Guide
请使用`python bili_cmd.py -h`查看更多参数提示，视频画面质量选择，包括并发量控制，下载目录等。
### 你是大会员？🥸
请在`-cookie`参数中填写浏览器缓存的`SESSDATA`cookie，填写后可以下载需要大会员的视频。
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


asyncio.run(main())

```
`Downloader`类的下载方法都是异步的，例如`d.get_series(...)`返回的是一个协程`Coroutine`对象，我们可以自由组合这些方法的返回值，然后通过`await asyncio.gather`方法并发执行这些任务。例如上面的例子中我们同时执行了三种不同的任务。

你要组合很多很多任务？不用担心！`d`对象执行这些任务的并发度受到初始化参数的严格控制🫡，`video_concurrency`控制了同时下载的视频数量，而`part_concurrency`则控制了每个媒体文件（音频/画面）的分段并发数，如果你不太明白可以在代码和注释中找到他们的详细作用，或者就让他们保持默认吧。

### 关于断点重连
用户可以通过Ctrl+C中断任务，对于未完成的文件，重新执行命令会在之前的进度基础上下载，已完成的文件会进行跳过。特别的，对于未完成文件，以下情况不能使用断点重连，建议清除未完成任务的临时文件再执行命令

- 中断后改变画面质量
- 中断后改变分段并发数`part_concurrency`

## 欢迎提问
由于本项目受到b站接口或者网站前端变动的影响，如果你发现任何bug或者其他问题，欢迎提issue，作者会保证最新版本可以正常运行。

如果觉得该项目对你有所帮助，可以给作者一个小小的Star🌟

## 未来工作
- [x] 下载视频封面
- [ ] 每日测试（GitHub Action），但目前Github Action不能正常访问b站？
- [x] 支持下载字幕，目前已支持下载json，以及转换成srt格式
- [x] 支持弹幕下载，目前已支持下载protobuf的的弹幕文件，各位可以在[issue](https://github.com/HFrost0/Lighting-bilibili-download/issues/7)中讨论这个问题
- [ ] 支持用pip安装，并提供更简明的命令行调用方式
### 已知的bug 🤡
* 出现未被正常捕捉的异常后断点重连可能导致视频画面或者音频部分缺失（例如突然拉闸😅）
* 不支持部分的没有音画分开下载方式的老视频
* 当两个视频名字完全一样时，任务冲突但不会报错，可能导致视频缺胳膊少腿
