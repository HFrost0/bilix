import asyncio
import click
from bilix import __version__
from bilix.log import logger
from bilix.cli.core import CustomCommand
from bilix.progress.cli_progress import CLIProgress


def handle_version(ctx: click.Context, param, value):
    if not value or ctx.resilient_parsing:
        return
    print(f"Version {__version__}")
    ctx.exit()


@click.command(cls=CustomCommand,
               help=f"""⚡️ bilix: a lightning-fast async download tool. Version {__version__}""")
@click.option(
    "--debug",
    is_flag=True,
    is_eager=True,
    help="Enable debug mode.",
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
def main(ctx, method=None, keys=None, **options):
    if method is None and keys is None:
        print(ctx.get_help())
        ctx.exit()
    debug = options.pop('debug')
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
        logger.interrupted()
    except Exception as e:
        if debug:
            raise e
        else:
            logger.error(f"Unexpected Exception: {repr(e)}. Use --debug to see more information.")
    finally:
        CLIProgress.stop()
