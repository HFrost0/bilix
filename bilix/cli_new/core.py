"""
use handler to provide click(typer) cli service
"""
from typing import List, Optional, Union, get_origin, get_args, Annotated
from click import UsageError, Context
from typer.models import OptionInfo, ParameterInfo, ParamMeta
from typer.core import TyperCommand, TyperOption, TyperArgument
from typer.main import get_click_param
from bilix.cli_new.assign import assign
from bilix.cli_new.handler import ParamInfo


def to_typer_param_meta(p: ParamInfo) -> ParamMeta:
    annotation = p.annotation
    default = p.default

    if annotation == p.empty and default != p.empty:
        annotation = type(default)
    elif (origin := get_origin(annotation)) is Union:
        annotation = get_args(annotation)[0]  # use the first type in Union, it's a convention
    elif origin is Annotated:
        # base_annotation, *convertors = get_args(annotation)
        # todo metavar
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
            print(convertor)
        return option
    except RuntimeError as e:
        print(e)
    except AssertionError as e:
        print(e)
    assert p.default != p.empty, f"Parameter '{p.name}' has no available type hint and no default value."


class CustomCommand(TyperCommand):
    def parse_args(self, ctx: Context, args: List[str]):
        try:
            method, keys = self._find_method_keys(ctx, args)
        except UsageError:
            return super().parse_args(ctx, args)
        handler_cls = assign(method, keys)
        cli_info = handler_cls.cli_info
        # add dynamic_params to ctx
        ctx.ensure_object(dict)
        ctx.obj["init_options"] = []
        ctx.obj["method_options"] = []
        for p in cli_info['__init__'].params.values():
            if option := get_click_option(p):
                option.rich_help_panel = f"Options for {handler_cls.__name__}"
                self.params.append(option)
                ctx.obj["init_options"].append(option.name)

        for p in cli_info[method].params.values():
            if option := get_click_option(p):
                option.rich_help_panel = f"Options for {cli_info[method].name}"
                self.params.append(option)
                ctx.obj["method_options"].append(option.name)
        ctx.obj['handler_cls'] = handler_cls

        self.params.append(TyperArgument(param_decls=['method'], type=str, required=True, hidden=True))
        self.params.append(TyperArgument(param_decls=['keys'], type=str, required=True, nargs=-1,
                                         help=cli_info[method].desc))

        return super().parse_args(ctx, args)

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
