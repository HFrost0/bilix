# 安装
bilix是一个强大的Python异步视频下载工具，安装它需要完成两个步骤：

1. pip安装（需要python3.8及以上）
   ```shell
   pip install bilix
   ```

2. [FFmpeg](https://ffmpeg.org) ：一个命令行视频工具，用于合成下载的音频和视频

    * macOS 下可以通过`brew install ffmpeg`进行安装。
    * Windows 下载请至官网 https://ffmpeg.org/download.html#build-windows ，安装好后需要配置环境变量。

   ::: info
   最终确保在命令行中可以调用`ffmpeg`命令即可。
   :::
