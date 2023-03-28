# 快速上手

bilix提供了简单的命令行使用方式，打开终端开始下载吧～

## 批量下载

批量下载整部动漫，电视剧，纪录片，电影，up投稿.....只需要把命令中的`url`替换成你要下载的系列中任意一个视频的网页链接。\
到 bilibili 上找一个来试试吧～，比如这个李宏毅老师的机器学习视频：[链接](https://www.bilibili.com/video/BV1JE411g7XF)，
`bilix`会下载文件至命令行当前目录的`videos`文件夹中，默认自动创建。

```shell
bilix get_series 'url'
```

`get_series`很强大，会自动识别系列所有视频并下载，当然，如果该系列只有一个视频（比如单p投稿）也是可以正常下载的。

::: info
* 什么是一个系列(series)：比如一个多p投稿的所有p，一部动漫，电视剧的所有集。

* 某些含有参数的url在终端中要用`''`包住，而windows的命令提示符不支持`''`，可用powershell或windows terminal代替。
:::

## 单个下载

用户😨：我不想下载那么多，只想下载单个视频。没问题，试试这个，只需要提供那个视频的网页链接：

```shell
bilix get_video 'url'
```
:::info
你知道吗？`get_series` `get_video`方法名都有[简写](/advance_guide)
:::


## 下载音频

假设你喜欢音乐区，只想下载音频，那么可以使用可选参数`--only-audio`，例如下面是下载[A叔](https://space.bilibili.com/6075139)
一个钢琴曲合集音频的例子

```shell
bilix get_series 'https://www.bilibili.com/video/BV1ts411D7mf' --only-audio
```

## 切片下载

视频，直播录像太长，我需要下载我感兴趣的片段✂️，那么可以使用`--time-range -tr`参数指定时间段下载切片

```shell
bilix get_vedio 'url' -tr 0:16:53-0:17:49
```

这个例子中指定了16分53秒至17分49秒的片段。 `-tr`参数的格式为`h:m:s-h:m:s`，起始时间和结束时间以`-`分割，时分秒以`:`
分割。或者`s-s`格式，例如1013秒至1069秒`1013-1069`

该参数仅在`get_video`中生效，仅下载音频也支持该参数

## 下载特定up主的投稿

假设你是一个嘉心糖，想要下载嘉然小姐最新投稿的100个视频，那么你可以使用命令：

```shell
bilix get_up 'https://space.bilibili.com/672328094' --num 100
```

`https://space.bilibili.com/672328094` 是up空间页url，另外用up主id`672328094`替换url同样也是可以的

## 下载分区视频

假设你喜欢看舞蹈区👍，想要下载最近30天播放量最高的20个超级敏感宅舞视频，那么你可以使用

```shell
bilix get_cate 宅舞 --keyword 超级敏感 --order click --num 20 --days 30
```

`get_cate`支持b站的每个子分区，可以使用排序，关键词搜索等，详细请参考`bilix -h`或代码注释

## 下载收藏夹视频

如果你需要下载自己或者其他人收藏夹中的视频，你可以使用`get_favour`方法

```shell
bilix get_favour 'https://space.bilibili.com/11499954/favlist?fid=1445680654' --num 20
```

`https://space.bilibili.com/11499954/favlist?fid=1445680654` 是收藏夹url，如果要知道一个收藏夹的url是什么，
最简单的办法是在b站网页左侧列表中点击切换到该收藏夹，url就会出现在浏览器的地址栏中。另外直接使用url中的fid`1445680654`
替换url也是可以的。

## 下载合集或视频列表

如果你需要下载up主发布的合集或视频列表，你可以使用`get_collect`方法

```shell
bilix get_collect 'url'
```

将`url`替换为某个合集或视频列表详情页的url（例如[这个](https://space.bilibili.com/369750017/channel/collectiondetail?sid=630)）即可下载合集或列表内所有视频

:::info
合集和视频列表有什么区别？b站的合集可以订阅，列表则没有这个功能，但是他们都在up主空间页面的合集和列表菜单中，例如[这个](https://space.bilibili.com/369750017/channel/series)
，`get_collect`会根据详情页url中的信息判断这个链接是合集还是列表
:::

## 下载字幕，弹幕，封面...

在命令中加入可选参数`--subtitle`（字幕） `--dm`（弹幕） `--image`（封面），即可下载这些附属文件

```shell
bilix get_series 'url' --subtitle --dm --image
```
