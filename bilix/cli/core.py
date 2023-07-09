"""
use handler to provide click(typer) cli service
"""
from importlib import import_module
from typing import List, Optional, Union, get_origin, get_args, Annotated
from click import UsageError, Context, Command
from rich.panel import Panel
from rich.table import Table
from typer import rich_utils
from typer.models import OptionInfo, ParameterInfo, ParamMeta
from typer.core import TyperCommand, TyperOption, TyperArgument
from typer.main import get_click_param
from typer.rich_utils import STYLE_OPTIONS_PANEL_BORDER, ALIGN_OPTIONS_PANEL
from bilix.cli.assign import assign, sites_module_infos, base_module_infos, sorted_modules, handler_classes
from bilix.cli.handler import ParamInfo, Handler
from bilix.log import logger
from rich import print as rprint
from rich.markdown import Markdown


def to_typer_param_meta(p: ParamInfo) -> ParamMeta:
    annotation = p.annotation
    default = p.default

    if annotation == p.empty and default != p.empty:
        annotation = type(default)
    elif (origin := get_origin(annotation)) is Union:
        annotation = get_args(annotation)[0]  # use the first type in Union, it's a convention
    elif origin is Annotated:
        # base_annotation, *convertors = get_args(annotation)
        annotation = str
    # convert default to OptionInfo to ensure no ArgumentInfo is created
    if not isinstance(default, ParameterInfo):
        default = OptionInfo(default=... if default == p.empty else default, help=p.desc)
    return ParamMeta(name=p.name, annotation=annotation, default=default)


def get_click_option(p: ParamInfo) -> Optional[TyperOption]:
    """
    typer get_click_param with some logic to handle more cases
    """
    p = to_typer_param_meta(p)
    try:
        option, convertor = get_click_param(p)
        if convertor:
            logger.debug(f"ignore {convertor}")
        return option
    except RuntimeError as e:
        logger.debug(e)
    except AssertionError as e:
        logger.debug(e)
    assert p.default != p.empty, f"Parameter '{p.name}' has no available type hint and no default value."


def print_site_help(name: str):
    """print help for site downloader or base downloader
    :param name: BaseDownloaderXxx or site name
    :return:
    """
    infos = sorted_modules(name, [name])
    for info in infos:
        if (name.startswith('Base') and _convert_path_to_name(info.module_path) == name) or \
                name == info.module_path.split('.')[-1]:
            try:
                module = import_module(info.module_path)
            except ImportError as e:
                logger.debug(f"duo to ImportError <{e}>, skip <module '{info.module_path}'>")
                continue
            for cls in handler_classes(module):
                print_handler_help(cls)
            rprint('✨ use [cyan]bilix METHOD KEYS... --help[/cyan] to get more help for options of method')
            return
    predicted_info = infos[0]
    predicted_name = predicted_info.module_path.split('.')[-1]
    if '_' in predicted_name:
        predicted_name = _convert_path_to_name(predicted_info.module_path)
    rprint(f"Can't find help for name: [cyan]{name}[/cyan]. Do you mean: [cyan]bilix help {predicted_name}[/cyan] ?")


def print_handler_help(cls: Handler):
    table = Table(show_header=True, show_lines=False, title_justify='left', box=None, header_style='yellow',
                  expand=True)
    table.add_column("Method Name")
    table.add_column("Short Name")
    table.add_column("Method Description")
    table.add_column("Key Description")
    methods = sorted(set(cls.cli_info.values()), key=lambda x: x.name)
    for method_info in methods:
        if method_info.name == '__init__':
            continue
        method_key_desc = next(iter(method_info.params.values())).desc
        table.add_row(method_info.name, method_info.short, method_info.desc or '...', method_key_desc or '...')
    rprint(Panel(
        table,
        border_style=STYLE_OPTIONS_PANEL_BORDER,
        title=cls.__name__,
        title_align=ALIGN_OPTIONS_PANEL,
    ))


class CustomContext(Context):
    @property
    def command_path(self) -> str:
        """The computed command path.  This is used for the ``usage``
        information on the help page.  It's automatically created by
        combining the info names of the chain of contexts to the root.
        """
        rv = ""
        if self.info_name is not None:
            rv = self.info_name
        if self.parent is not None:
            parent_command_path = [self.parent.command_path]

            if isinstance(self.parent.command, Command):
                for param in self.parent.command.get_params(self):
                    parent_command_path.extend(param.get_usage_pieces(self))

            rv = f"{' '.join(parent_command_path)} {rv}"
        res = rv.lstrip()
        if self.obj:
            method, keys = self.obj['method'], self.obj['keys']
            return f"{res} {method.short if method.short else method.name} KEYS..."
        else:
            return res


class CustomCommand(TyperCommand):
    context_class = CustomContext

    def parse_args(self, ctx: Context, args: List[str]):
        if '--debug' in args:  # preparse debug option to ensure log assign debug info
            logger.setLevel('DEBUG')
            logger.debug("Debug on, more information will be shown")
        try:
            method, keys = self._find_method_keys(ctx, args)
        except UsageError:
            return super().parse_args(ctx, args)

        # method is help
        if method == 'help':
            if len(keys) != 1:
                raise UsageError("Please specify one site name or downloader name")
            else:
                print_site_help(keys[0])
                ctx.exit()

        handler_cls = assign(method, keys)
        cli_info = handler_cls.cli_info
        method = cli_info[method]
        # add dynamic_params to ctx
        ctx.ensure_object(dict)
        ctx.obj["init_options"] = []
        ctx.obj["method_options"] = []
        ctx.obj['method'] = method
        ctx.obj['keys'] = keys
        # for handler init
        for p in cli_info['__init__'].params.values():
            if option := get_click_option(p):
                option.rich_help_panel = f"Options for {handler_cls.__name__}"
                self.params.append(option)
                ctx.obj["init_options"].append(option.name)
        # for method
        ps = list(method.params.values())
        # skip key
        for p in ps[1:]:
            if option := get_click_option(p):
                option.rich_help_panel = f"Options for {method.name} (alias: {method.short})"
                self.params.append(option)
                ctx.obj["method_options"].append(option.name)
        ctx.obj['handler_cls'] = handler_cls

        self.params.append(TyperArgument(param_decls=['method'], type=str, required=True, hidden=True,
                                         # metavar=f'{method.name} ({method.short})' if method.short else method.name,
                                         ))
        self.params.append(TyperArgument(param_decls=['keys'], type=str, required=True, nargs=-1, help=ps[0].desc, ))
        self.help = '✨ ' + method.desc
        try:
            return super().parse_args(ctx, args)
        except UsageError as e:
            e.message = f"[For {handler_cls.__name__} {method.name}] {e.message}"
            raise

    @staticmethod
    def _find_method_keys(ctx, args):
        if len(args) == 0:
            raise UsageError("method is required", ctx)
        for idx, arg in enumerate(args):
            if arg.startswith('-'):
                if idx == 0:
                    raise UsageError("method should be first", ctx)
                return args[0], args[1:idx]
        return args[0], args[1:]

    def collect_usage_pieces(self, ctx: Context) -> List[str]:
        """basically copy from click.core.Command.collect_usage_pieces, but with option metavar moved to the end"""
        rv = []
        # for param in self.get_params(ctx):
        #     rv.extend(param.get_usage_pieces(ctx))
        if self.options_metavar:
            rv.append(self.options_metavar)
        return rv

    def format_help(self, ctx: Context, formatter) -> None:
        if ctx.obj:  # with method and keys
            self.help = f"✨ {ctx.obj['method'].desc}"
            return rich_utils.rich_format_help(
                obj=self,
                ctx=ctx,
                markup_mode=self.rich_markup_mode,
            )
        else:
            rich_utils.rich_format_help(
                obj=self,
                ctx=ctx,
                markup_mode=self.rich_markup_mode,
            )
            msg = "bilix supports many sites:\n"
            for info in sorted(sites_module_infos(), key=lambda x: x.cmp_key):  # alphasort
                msg += f"* {info.cmp_key}\n"
            msg += "\n✨ use `bilix help <site>` to see more\n"
            rprint(Panel(
                Markdown(msg),
                border_style=STYLE_OPTIONS_PANEL_BORDER,
                title="Supported Sites",
                title_align=ALIGN_OPTIONS_PANEL,
            ))
            msg = "For fundamental downloading scenarios such as file downloads or m3u8 video downloads: \n"
            for info in base_module_infos():
                msg += f"* `{_convert_path_to_name(info.module_path)}` for {info.cmp_key} downloads\n"
            msg += "\n✨ use `bilix help <downloader>` to see more\n"
            rprint(Panel(
                Markdown(msg),
                border_style=STYLE_OPTIONS_PANEL_BORDER,
                title="Base Downloaders",
                title_align=ALIGN_OPTIONS_PANEL,
            ))


def _convert_path_to_name(module_path):
    return ''.join([name.capitalize() for name in module_path.split('.')[-1].split('_')])
