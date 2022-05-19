import asyncio
import typing
import click
import rich
from rich.panel import Panel
from rich.table import Table
from bilix.download import Downloader


def handle_help(ctx: click.Context, param: typing.Union[click.Option, click.Parameter], value: typing.Any, ) -> None:
    if not value or ctx.resilient_parsing:
        return

    print_help()
    ctx.exit()


def print_help():
    console = rich.console.Console()
    console.print("\n[bold]Bilix", justify="center")
    console.print("⚡️快如闪电的bilibili下载工具，基于Python现代Async特性，高速批量下载整部动漫，电视剧，up投稿等\n", justify="center")
    console.print("使用方法： bilix [cyan]<method> <key> [OPTIONS][/cyan] ", justify="left")
    table = Table.grid(padding=1, pad_edge=False)
    table.add_column("Parameter", no_wrap=True, justify="left", style="bold")
    table.add_column("Description")

    table.add_row(
        "[cyan]<method>",
        'get_series 或 s：获取整个系列的视频（包括多p投稿，动漫，电视剧，电影，纪录片），也可以下载单个视频\n'
        'get_video 或 v：获取特定的单个视频，在用户不希望下载系列其他视频的时候可以使用\n'
        'get_up 或 up：获取某个up的所有投稿视频，支持数量选择，关键词搜索，排序\n'
        'get_cate 或 cate：获取分区视频，支持数量选择，关键词搜索，排序\n'
        'get_favour 或 fav：获取收藏夹内视频，支持数量选择，关键词搜索\n'
        'get_collect 或 col：获取合集或视频列表内视频'
    )
    table.add_row(
        "[cyan]<key>",
        '如果使用get_video或get_series，在此填写视频的url\n'
        '如果使用get_up，则在该位置填写b站用户id\n'
        '如果使用get_cate，则在该位置填写分区名称\n'
        '如果使用get_favour，则在该位置填写收藏夹id\n'
        '如果使用get_collect，则在该位置填写合集或者视频列表详情页url'
    )
    console.print(table)
    # console.rule("OPTIONS参数")
    table = Table(highlight=True, box=None, show_header=False)
    table.add_column("OPTIONS", no_wrap=True, justify="left", style="bold")
    table.add_column("type", no_wrap=True, justify="left", style="bold")
    table.add_column("Description", )
    table.add_row(
        "--dir",
        '[dark_cyan]str',
        "文件的下载目录，默认当前路径下的videos文件夹下，不存在会自动创建"
    )
    table.add_row(
        "-q --quality",
        '[dark_cyan]int',
        "视频画面质量，默认0为最高画质，越大画质越低，超出范围时自动选最低画质"
    )
    table.add_row(
        "--max-con",
        '[dark_cyan]int',
        "控制最大同时下载的视频数量，理论上网络带宽越高可以设的越高，默认3",
    )
    table.add_row(
        '--cookie',
        '[dark_cyan]str',
        '有条件的用户可以提供大会员的SESSDATA来下载会员视频'
    )
    table.add_row(
        '--days',
        '[dark_cyan]int',
        '过去days天中的结果，默认为7，仅get_up, get_cate时生效'
    )
    table.add_row(
        "-n --num",
        '[dark_cyan]int',
        "下载前多少个投稿，仅get_up，get_cate，get_favor时生效",
    )
    table.add_row(
        "--order",
        '[dark_cyan]str',
        '何种排序，pubdate发布时间（默认）， click播放数，scores评论数，stow收藏数，coin硬币数，dm弹幕数, 仅get_up, get_cate时生效',
    )
    table.add_row(
        "--keyword",
        '[dark_cyan]str',
        '搜索关键词， 仅get_up, get_cate，get_favor时生效',
    )
    table.add_row(
        "--no-series", '',
        '只下载搜索结果每个视频的第一p，仅get_up，get_cate，get_favour时生效',
    )
    table.add_row(
        "--no-hierarchy", '',
        '不使用层次目录，所有视频统一保存在下载目录下'
    )
    table.add_row(
        "--image", '',
        '下载视频封面'
    )
    table.add_row(
        "--subtitle", '',
        '下载srt字幕',
    )
    table.add_row(
        "--dm", '',
        '下载弹幕',
    )
    table.add_row(
        "--only-audio", '',
        '仅下载音频，下载的音质固定为最高音质',
    )
    table.add_row(
        "-p", '[dark_cyan]int, int',
        '下载集数范围，例如-p 1 3 只下载P1至P3，仅get_series时生效',
    )
    table.add_row("-h --help", '', "帮助信息")
    console.print(Panel(table, border_style="dim", title="Options", title_align="left"))


@click.command(add_help_option=False)
@click.argument("method", type=str)
@click.argument("key", type=str)
@click.option(
    "--dir",
    "videos_dir",
    type=str,
    default='videos',
)
@click.option(
    '-q',
    '--quality',
    'quality',
    type=int,
    default=0,
)
@click.option(
    '--max-con',
    'video_concurrency',
    type=int,
    default=3,
)
@click.option(
    '--cookie',
    'cookie',
    type=str,
)
@click.option(
    '--days',
    'days',
    type=int,
    default=7,
)
@click.option(
    '-n',
    '--num',
    type=int,
    default=10,
)
@click.option(
    '--order',
    'order',
    type=str,
    default='pubdate',
)
@click.option(
    '--keyword',
    'keyword',
    type=str
)
@click.option(
    '--no-series',
    'no_series',
    is_flag=True,
    default=True,
)
@click.option(
    '--no-hierarchy',
    'hierarchy',
    is_flag=True,
    default=True,
)
@click.option(
    '--image',
    'image',
    is_flag=True,
    default=False,
)
@click.option(
    '--subtitle',
    'subtitle',
    is_flag=True,
    default=False,
)
@click.option(
    '--dm',
    'dm',
    is_flag=True,
    default=False,
)
@click.option(
    '--only-audio',
    'only_audio',
    is_flag=True,
    default=False,
)
@click.option(
    '-p',
    'p_range',
    type=(int, int),
)
@click.option(
    '-h',
    "--help",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=handle_help,
)
def main(method: str,
         key: str,
         videos_dir: str,
         video_concurrency: int,
         cookie: str,
         quality: int,
         days: int,
         num: int,
         order: str,
         keyword: str,

         no_series: bool,
         hierarchy: bool,
         image: bool,
         subtitle: bool,
         dm: bool,
         only_audio: bool,
         p_range,
         ):
    loop = asyncio.get_event_loop()
    d = Downloader(videos_dir=videos_dir, video_concurrency=video_concurrency, sess_data=cookie)
    if method == 'get_series' or method == 's':
        cor = d.get_series(key, quality=quality, image=image, subtitle=subtitle, dm=dm, only_audio=only_audio,
                           p_range=p_range, hierarchy=hierarchy)
    elif method == 'get_video' or method == 'v':
        cor = d.get_video(key, quality=quality,
                          image=image, subtitle=subtitle, dm=dm, only_audio=only_audio)
    elif method == 'get_up' or method == 'up':
        cor = d.get_up_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy
        )
    elif method == 'get_cate' or method == 'cate':
        cor = d.get_cate_videos(
            key, quality=quality, num=num, order=order, keyword=keyword, days=days, series=no_series,
            image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    elif method == 'get_favour' or method == 'fav':
        cor = d.get_favour(key, quality=quality, num=num, keyword=keyword, series=no_series,
                           image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    elif method == 'get_collect' or method == 'col':
        cor = d.get_collect_or_list(key, quality=quality,
                                    image=image, subtitle=subtitle, dm=dm, only_audio=only_audio, hierarchy=hierarchy)
    else:
        print(f'{method}不能识别，请使用正确的方法名')
        return
    task = loop.create_task(cor)
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        rich.print('[cyan]提示：用户中断，重复执行命令可继续下载')
    finally:  # similar to asyncio.run
        tasks = [t for t in asyncio.all_tasks(loop)]
        [t.cancel() for t in tasks]
        try:
            loop.run_until_complete(asyncio.gather(*tasks, d.aclose(), return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            # print('normal out')
        except KeyboardInterrupt:
            pass  # todo bug due to KeyboardInterrupt in python3.9.../asyncio/events.py line 78-95
            # try:
            #     self._context.run(self._callback, *self._args)
            # except (SystemExit, KeyboardInterrupt):  # 💦 always raise these two kind of error regrad
            #     raise
            # except BaseException as exc:
            #     cb = format_helpers._format_callback_source(
            #         self._callback, self._args)
            #     msg = f'Exception in callback {cb}'
            #     context = {
            #         'message': msg,
            #         'exception': exc,
            #         'handle': self,
            #     }
            #     if self._source_traceback:
            #         context['source_traceback'] = self._source_traceback
            #     self._loop.call_exception_handler(context)
        finally:
            # SingletonPPE().shutdown()
            asyncio.set_event_loop(None)
            loop.close()
