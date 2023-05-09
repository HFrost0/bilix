import asyncio
import click
from click.testing import CliRunner
from bilix import __version__
from bilix.log import logger
from bilix.cli_new.core import CustomCommand
from bilix.progress.cli_progress import CLIProgress


def handle_version(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing:
        return
    print(f"Version {__version__}")
    ctx.exit()


def handle_debug(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing:
        return
    logger.setLevel('DEBUG')
    logger.debug("Debug on, more information will be shown")


@click.command(cls=CustomCommand)
@click.option(
    "--debug",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    help="Enable debug mode.",
    callback=handle_debug,
)
@click.option(
    "--version", '-v',
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=handle_version,
    help="Show version and exit",
)
@click.pass_context
def main(ctx, method, keys, **options):
    loop = asyncio.new_event_loop()  # avoid deprecated warning in 3.11
    asyncio.set_event_loop(loop)
    logger.debug(f"method: {method}, keys: {keys}, options: {options}")

    handler_cls = ctx.obj['handler_cls']
    init_options = {op: options[op] for op in ctx.obj['init_options']}
    method_options = {op: options[op] for op in ctx.obj['method_options']}
    handler, cor = handler_cls.handle(method, keys, init_options, method_options)

    try:
        CLIProgress.start()
        loop.run_until_complete(cor)
    except KeyboardInterrupt:
        logger.info('[cyan]提示：用户中断，重复执行命令可继续下载')
    finally:
        CLIProgress.stop()


if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(main(
        [
            'v',
            'https://www.bilibili.com/video/BV1Zk4y1772p/',
            # '--debug',
            # '-p', '3jfjf/123',
            # '-a', 'adfad',
            # "--hierarchy", "False",
            # "--speed-limit", '1M',
            "--help"
        ]))
    # main()
