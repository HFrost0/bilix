# bilix 开发指南

感谢你对贡献bilix有所兴趣，在你开始之前可以阅读下面的一些提示。请注意，bilix正快速迭代，
如果你在阅读本文档时发现有些内容已经过时，请以master分支的代码为准。

# 开始之前

在一切开始之前，你需要先 **fork** 本仓库，然后clone你fork的仓库到你的本地：

```shell
git clone https://github.com/your_user_name/bilix
```

拉取至本地后，我**建议**你在独立的python环境中进行测试和开发，确认后进行本地源码可编辑安装：

```shell
pip install -e .
```

试试bilix命令能否正常执行。通过测试了？至此，你可以在本地开发bilix了🍻

# bilix 结构

在动手改动代码之前你需要对bilix的结构有一定的了解，下面是bilix的大致目录和各模块相应功能：

```text
bilix
├── __init__.py
├── __main__.py
├── _process.py  # 多进程相关
├── cli
│   ├── assign.py  # 分配任务，动态导入相关
│   └── main.py    # 命令行入口
├── download
│   ├── base_downloader.py
│   ├── base_downloader_m3u8.py  # 基础m3u8下载器
│   ├── base_downloader_part.py  # 基础分段文件下载器
│   └── utils.py                 # 下载相关的一些工具函数
├── exception.py
├── log.py
├── progress
│   ├── abc.py            # 进度条抽象类
│   ├── cli_progress.py   # 命令行进度条
│   └── ws_progress.py
├── serve
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── serve.py
│   └── user.py
├── sites     # 站点扩展目录，稍后介绍
└── utils.py  # 通用工具函数
```

## 基础下载器

bilix在`bilix.download`中提供了两种基础下载器，m3u8下载器和分段文件下载器。
它们基于`httpx`乃至更底层的`asyncio`及IO多路复用，并且集成了速度控制，并发控制，断点续传，时间段切片，进度条显示等许多实用功能。
bilix的站点扩展下载功能都将基于这些基础下载器完成，基础下载器本身也提供cli服务

## 下载器是如何提供cli服务的

在bilix中，一个类只要实现了`handle`方法，就可以被注册到命令行（cli）中，`handle`方法的函数签名为

```python
@classmethod
def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
    ...
```

handle函数的实现应该满足下面三个原则：

1. 如果类根据`method` `keys` `options`认为自己不应该承担下载任务，`handle`函数应该返回`None`
2. 如果类可以承担任务，但发现`method`不在自己的可接受范围内，应该抛出`HandleMethodError`异常
3. 如果类可以承担任务，且`method`在自己的可接受范围内，应该返回两个值，第一个值为下载器实例，第二个值为下载coroutine

Q：🙋为什么我看到有的下载器返回的是类本身，以及下载函数对象？

```python
@classmethod
def handle(cls, method: str, keys: Tuple[str, ...], options: dict):
    if method == 'f' or method == 'get_file':
        return cls, cls.get_file
```

A：为了偷懒，如果返回值是类以及下载函数对象，将根据命令行参数及type hint自动组装为实例和coroutine，
适用于当命令行options的名字和方法，类参数名字、类型一致的情况

其实`handle`函数给你了较大的自由，你可以根据自己的需求，自由的组合出适合你的下载器的cli服务

## 如何快速添加一个站点的支持

在`bilix/sites`下，已经有一些站点的支持，如果你想要添加一个新的站点支持，可以按照下面的步骤进行：

1. 在`sites`文件夹下新建一个站点文件夹，例如`example`
2. 在`example`文件夹下添加站点的api模块`api.py`，仿照其他站点的格式实现从输入网页url到输出视频url，视频title的各种api
3. 在`example`文件夹下添加站点api模块的测试`api_test.py`，让大家随时测试站点是否可用
4. 在`example`文件夹下添加站点的下载器`donwloader.py`，定义`DownloaderExample`
   类，根据该站点使用的传输方法选择相应的`BaseDownloader`进行继承，然后在类中定义好下载视频的方法，并实现`handle`
   方法。另外你还可以添加`downloader_test.py`来验证你的下载器是否可用
5. 在`example`文件夹下添加`__init__.py`，将`DownloaderExample`类导入，并且在`__all__`中添加`DownloaderExample`以方便bilix找到你的下载器

搞定，使用bilix命令测试一下吧

当前已经有其他开发者为bilix对其他站点的适配做出了贡献🎉，
或许被接受的[New site PR](https://github.com/HFrost0/bilix/pulls?q=is%3Apr+is%3Aclosed+label%3A%22New+site%22)也能为你提供帮助

