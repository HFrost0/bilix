# Quickstart

bilix offers a simple command line interface, so open the terminal and start downloading now!

## Batch download

Batch download entire anime series, TV shows, movies, and UP submissions... just replace the `url` in the
command with the web link of any video in the series you want to download.

Head over to bilibili and find one to try (like [this](https://www.bilibili.com/video/BV1JE411g7XF)),
`bilix` will download the files to the `videos` folder in the current directory of the command line, which is automatically created by default.

```shell
bilix get_series 'url'
```

`get_series` is powerful, as it automatically recognizes and downloads all videos in a series.

::: info
* What is a series: For example, all parts of a multi-part submission, all episodes of an anime or TV show.
* Some URLs containing parameters need to be wrapped in `''` when used in the terminal.
The Windows cmd does not support `''`, but you can use PowerShell or Windows Terminal as an alternative.
:::

## Single download

User😨：I don't want to download that many, just a single video. No problem, try this, just provide the web link of that video:

```shell
bilix get_video 'url'
```
:::info
Do you know that? methods like `get_series` `get_video` all has a [shorthand](/en/advance_guide)
:::


## Audio download

Assuming you like the music and only want to download audio, then you can use the optional parameter `--only-audio`

```shell
bilix get_series 'url' --only-audio
```

## Clip download

The video, live record is too long, I need to download the clip I am interested in✂️, then you can use the
`--time-range -tr` parameter to specify the time range

```shell
bilix get_vedio 'url' -tr 0:16:53-0:17:49
```

In this example, a time range from 16 minutes 53 seconds to 17 minutes 49 seconds is specified.
The format can be `h:m:s-h:m:s`, or `s-s`

this option is only available in `get_video`, you can combine `-tr` with `--only-audio` to download audio clip

## Uploader download

If you want to download the latest 100 submissions from an uploader

```shell
bilix get_up 'https://space.bilibili.com/672328094' --num 100
```

`https://space.bilibili.com/672328094` is the uploader space url，you can also use uploader id `672328094` to replace `url`


## Download Videos by Category

Suppose you enjoy watching the dance category👍 and want to download the top 20 超级敏感 宅舞 videos with
the highest play count in the last 30 days, you can use:

```shell
bilix get_cate 宅舞 --keyword 超级敏感 --order click --num 20 --days 30
```

`get_cate` supports every sub-category on bilibili and offers options for sorting and keyword searching.
For more details, please refer to `bilix -h` or the code comments.

## Download Videos from Favorites

If you need to download videos from your own or someone else's favorites, you can use the `get_favour` method

```shell
bilix get_favour 'https://space.bilibili.com/11499954/favlist?fid=1445680654' --num 20
```

`https://space.bilibili.com/11499954/favlist?fid=1445680654` is the URL for the favorites. If you want to know
the URL of a favorites, the easiest way is to click on it in the Bilibili webpage's left-side menu, and the URL
will appear in the browser's address bar. Alternatively, you can directly replace the URL with the fid `1445680654`

## Download collection or video list

If you want to download the collection or video list released by a uploader, you can use the `get_collect` method

```shell
bilix get_collect 'url'
```

Replace `url` with the url of a collection or video list details page（[for example](https://space.bilibili.com/369750017/channel/collectiondetail?sid=630)）


## Download subtitle, danmaku, cover...

Add options `--subtitle` `--dm` `--image` according to your need to download these additional files

```shell
bilix get_series 'url' --subtitle --dm --image
```
