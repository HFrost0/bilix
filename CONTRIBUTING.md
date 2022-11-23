# bilix 开发指南

感谢你对贡献bilix有所兴趣，在你开始之前可以阅读下面的一些提示。

## 开始之前

在一切开始之前，你需要先 **fork** 本仓库，然后clone你fork的仓库到你的本地：

```shell
git clone https://github.com/your_user_name/bilix
```

拉取至本地后，我**建议**你在独立的python环境中进行测试和开发，你可以使用python自带的`venv`或者其他方法，
最重要的是别把你的其他环境弄乱了！确认后进行本地源码安装：

```shell
pip install -e .
```

💡另外`ffmpeg`对于bilibili的视频合成是需要的，如果你需要对bilibili有关的代码进行改动并测试，请确保`ffmpeg`也已经安装。

安装完成后，你可以先尝试运行一些测试脚本，在运行测试脚本之前，需要安装python中的测试框架`pytest`以及其拓展

```shell
pip install pytest pytest-asyncio
```

安装完成之后，可以试着运行针对`bilix.api`模块的测试（先不建议运行tests/download，因为这里面的测试会下载视频，比较花费时间）

```shell
pytest tests/api
```

通过测试了？至此，你可以在本地开发bilix了🍻

## bilix 结构

在动手改动代码之前你需要对bilix的结构有一定的了解，下面是bilix的大致目录和各模块相应功能：

```text
├── bilix
│   ├── __init__.py
│   ├── __main__.py         # 命令行相关，bilix命令的入口
│   ├── __version__.py      # 版本，作者等信息
│   ├── api                 # api模块，主要负责对各个站点的网页或接口返回的信息进行提取，获取视频链接，标题等信息
│   │   ├── __init__.py
│   │   ├── bilibili.py
│   │   ├── cctv.py
│   │   ├── ...
│   ├── assign.py           # 下载器的注册，根据命令行参数分配下载器
│   ├── dm                  # b站弹幕解析与转换
│   │   ├── __init__.py
│   │   ├── reply.proto
│   │   ├── reply_pb2.py
│   │   ├── view.proto
│   │   └── view_pb2.py
│   ├── download            # 下载模块，包含基础下载器和各站点下载器
│   │   ├── __init__.py
│   │   ├── base_downloader.py          # 所有下载器继承的父类，包含进度条等基本功能
│   │   ├── base_downloader_m3u8.py     # m3u8基础下载器（HLS方式下载）
│   │   ├── base_downloader_part.py     # part基础下载器（content-range方式下载）
│   │   ├── downloader_bilibili.py      # 各站点下载器，通过api模块获取站点信息，并基于基础下载器获取文件
│   │   ├── downloader_cctv.py
│   │   ├── ...
│   ├── js                  # 需要js逆向的站点依赖的js文件
│   │   └── yhdmp.js
│   ├── log.py              # 日志打印
│   ├── process.py          # 多进程相关
│   ├── subtitle.py         # 字幕相关
│   └── utils.py            # 一些杂七杂八的function就放在这了
├── examples        # 提供了一些python中使用bilix的样例
└── tests           # 测试
    ├── __init__.py
    ├── api         # api模块测试
    ├── dm          # 弹幕模块测试
    └── download    # download模块测试


```

## 如何快速添加一个站点的支持

1. 在api模块中新建一个站点的文件，例如`site.py`，仿照其他站点的格式实现从输入网页url到输出视频url，视频title的
   各种api。注意应当保证向外提供的所有接口的第一个参数为`httpx.AsyncClient`，并且本身为async def的function。
2. 在download模块中新建一个站点的文件，例如`downloader_site.py`，定义`DownloaderSite`类，根据该站点使用的传输方法
   选择相应的BaseDownloader进行继承，导入相应站点的api，然后在类中定义好下载视频的方法。
3. 在`downloader_site.py`中定义一个handle方法，该方法的参数`**kwargs`即命令行提供的所有参数，包括method, key, quality等
   handle方法首先应当根据key来决定是否承担这个下载任务，如果不承担应当返回`None`。如果选择承担应当返回相应的下载器和下载协程，
   如果method不在可接受范围内时应当抛出`ValueError`。
4. 在handle方法上添加一个装饰器`@Handler`，并给这个站点起一个名字作为唯一标识。并且在download模块中的`__init__.py`文件中
   导入该站点的下载器。此时该站点已经注册到bilix的可下载站点中了。
5. 使用bilix命令测试一下吧
6. 对于api模块中的接口写好相应的测试

ps:暂不接受需要js逆向的站点

当前已经有其他开发者为bilix对其他站点的适配做出了贡献🎉，
或许被接受的[New site PR](https://github.com/HFrost0/bilix/pulls?q=is%3Apr+is%3Aclosed+label%3A%22New+site%22)也能为你提供帮助

