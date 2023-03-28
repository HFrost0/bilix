# 进阶使用
请使用`bilix -h`查看更多参数提示，包括方法名简写，视频画面质量选择，并发量控制，下载速度限制，下载目录等。

## 方法名简写

觉得get_series，get_video这些方法名写起来太麻烦了？同感！你可以使用他们的简写，这样快多了：

```shell
bilix s 'url'
bilix v 'url'
...
```
更多简写请查看`bilix -h`

## 登录

你是大会员？🥸，两种方式登录

* 直接填写cookie

  在`--cookie`参数中填写浏览器缓存的`SESSDATA`cookie，填写后可以下载需要大会员的视频

* 从浏览器载入cookie

  在浏览器中登录之后，使用`-fb --from-browser`参数从浏览器中读取cookie，例如`-fb chrome`，使用这种方法可能需要授权，bilix读取浏览器cookie的
  方式为开源项目[browser_cookie3](https://github.com/borisbabic/browser_cookie3)。
:::tip
如果你总是需要保持登录，在linux和mac系统中你可以使用`alias bilix=bilix --cookie xxxxxx`或`alias bilix=bilix -fb chrome`来为`bilix`命令创建别名
:::

## 画质，音质和编码选择

你可以使用`--quality`即`-q`参数选择画面分辨率，bilix支持两种不同的选择方式：

* 相对选择（默认）

  bilix在默认情况下会为你选择可选的最高画质进行下载（即`-q 0`），如果你想下载第二清晰的可使用`-q 1`进行指定，以此类推，指定序号越大画质越低，
  当超过可选择范围时，默认选择到最低画质，例如你总是可以通过`-q 999`来选择到最低画质。
* 绝对选择

  在某些时候，你只希望下载720P的视频，但是720P在相对选择中并不总是处于固定的位置，这在下载收藏夹，合集等等场景中经常出现。
  另外有可能你就是喜欢通过`-q 1080P`这样的方式来指定画质。
  没问题，bilix同时也支持通过`-q 4K` `-q '1080P 高码率'`等字符串的形式来直接指定画质，字符串为b站显示的画质名称的子串即可。

在更加专业用户的需求中，可能需要指定特定的视频编码进行下载，而b站支持的编码在网页或app中是不可见的，bilix为此设计了方法`info`
， 通过它你可以完全了解该视频的所有信息：

```text
bilix info 'https://www.bilibili.com/video/BV1kG411t72J' --cookie 'xxxxx' 
                        
 【4K·HDR·Hi-Res】群青 - YOASOBI  33,899👀 1,098👍 201🪙
┣━━ 画面 Video
┃   ┣━━ HDR 真彩
┃   ┃   ┗━━ codec: hev1.2.4.L153.90                 total: 149.86MB
┃   ┣━━ 4K 超清
┃   ┃   ┣━━ codec: avc1.640034                      total: 320.78MB
┃   ┃   ┗━━ codec: hev1.1.6.L153.90                 total: 106.54MB
┃   ┣━━ 1080P 60帧
┃   ┃   ┣━━ codec: avc1.640032                      total: 171.91MB
┃   ┃   ┗━━ codec: hev1.1.6.L150.90                 total: 24.66MB
┃   ┣━━ 1080P 高清
┃   ┃   ┣━━ codec: avc1.640032                      total: 86.01MB
┃   ┃   ┗━━ codec: hev1.1.6.L150.90                 total: 24.18MB
┃   ┣━━ 720P 高清
┃   ┃   ┣━━ codec: avc1.640028                      total: 57.39MB
┃   ┃   ┗━━ codec: hev1.1.6.L120.90                 total: 11.53MB
┃   ┣━━ 480P 清晰
┃   ┃   ┣━━ codec: avc1.64001F                      total: 25.87MB
┃   ┃   ┗━━ codec: hev1.1.6.L120.90                 total: 7.61MB
┃   ┗━━ 360P 流畅
┃       ┣━━ codec: hev1.1.6.L120.90                 total: 5.24MB
┃       ┗━━ codec: avc1.64001E                      total: 11.59MB
┗━━ 声音 Audio
    ┣━━ 默认音质
    ┃   ┗━━ codec: mp4a.40.2                        total: 10.78MB
    ┗━━ Hi-Res无损
        ┗━━ codec: fLaC                             total: 94.55MB
```

看上去不错😇，那么我要怎么才能下到指定编码的视频呢？

bilix提供了另一个参数`--codec`来指定编码格式，例如你可以通过组合`-q 480P --codec hev1.1.6.L120.90`来指定下载7.61MB的那个。
`--codec`参数与`-q`参数类似，也支持子串指定，例如你可以通过`--codec hev`来使得所有视频都选择`hev`开头的编码。

对于音质，部分视频会含有大会员专享的杜比全景声和Hi-Res无损音质，利用`--codec`参数可以指定这些音频，例如

```shell
bilix v 'https://www.bilibili.com/video/BV1kG411t72J' --cookie 'xxxxx' --codec hev:fLaC 
```

`--codec hev:fLaC`中使用`:`将画质编码和音频编码隔开，如只指定音频编码，可使用`--codec :fLaC`

## 关于断点重连

用户可以通过Ctrl+C中断任务，对于未完成的文件，重新执行命令会在之前的进度基础上下载，已完成的文件会进行跳过。
但是对于未完成的文件，以下情况建议清除未完成任务的临时文件再执行命令，否则可能残留部分临时文件。

- 中断后改变画面质量`-q`或编码`--codec`
- 中断后改变分段并发数`--part-con`
- 中断后改变时间范围`--time-range`


## 更多站点支持
bilix除了b站以外也支持了一些别的站点，但作者精力有限，所以失效也不奇怪。具体可见[discussion](https://github.com/HFrost0/bilix/discussions/39)