# Installation
bilix is a powerful Python asynchronous video download tool that requires two steps to install:

1. pip install（require python >= 3.8）
   ```shell
   pip install bilix
   ```

2. [FFmpeg](https://ffmpeg.org) ：A command-line video tool for compositing downloaded audio and video

    * For macOS, it can be installed via `brew install ffmpeg`
    * For Windows, please go to the official website https://ffmpeg.org/download.html#build-windows , you need to configure environment variables after installation

   ::: info
   Just make sure that you can call the `ffmpeg` command from the command line in the end.
   :::
