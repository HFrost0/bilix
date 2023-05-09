import asyncio
import inspect
import re
from dataclasses import dataclass
from click import UsageError
from typing import Dict, Tuple, Coroutine, Optional, List, Callable, Any


@dataclass(frozen=True)
class ParamInfo:
    empty = inspect.Parameter.empty
    name: str
    annotation: Any
    default: Any
    desc: str


@dataclass(frozen=True)
class MethodInfo:
    name: str
    short: str
    func: Callable
    params: Dict[str, ParamInfo]


class HandlerMeta(type):
    def __new__(cls, name, bases, dct):
        dct['cli_info']: Dict[str, MethodInfo] = {}
        cli_info = dct['cli_info']
        for method_name, method in dct.items():
            if not method_name.startswith('_') and inspect.iscoroutinefunction(method):
                if cls.check_unique_method(method, bases):
                    if method_info := cls.parse_method(method):
                        cli_info[method_name] = method_info
                        if method_info.short:
                            assert method_info.short not in cli_info, f"short name {method_info.short} duplicated"
                            cli_info[method_info.short] = method_info
            elif method_name == '__init__':
                cli_info[method_name] = cls.parse_init(method, bases)
        # Some classes may not have an `__init__` method, for example, the Handler class does not override `__init__`,
        # in this case, we try to find `__init__` info from base class
        if '__init__' not in cli_info:
            # try to find __init__ info from base class
            for base in bases:
                if '__init__' in base.cli_info:
                    cli_info['__init__'] = base.cli_info['__init__']
        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def check_unique_method(method_name: str, bases: Tuple[type, ...]):
        for base in bases:
            if method_name in base.__dict__:
                return False
        return True

    @staticmethod
    def parse_param_descriptions(docstring: Optional[str]) -> dict:
        if docstring is None:
            return {}
        params_matches = re.findall(r":param (\w+): (.+)", docstring)
        if params_matches:
            return {param: description for param, description in params_matches}
        else:
            return {}

    @staticmethod
    def parse_short_name(docstring: str) -> Optional[str]:
        if docstring is None:
            return None
        cli_short_match = re.search(r":cli: short: (\w+)", docstring)
        return cli_short_match.group(1) if cli_short_match else None

    @classmethod
    def parse_init(cls, init_func: Callable, bases) -> MethodInfo:
        docstring = init_func.__doc__
        param_descriptions = cls.parse_param_descriptions(docstring)

        params = {}
        sig = inspect.signature(init_func)
        for param in sig.parameters.values():
            # skip self
            if param.name == 'self':
                continue
            annotation = param.annotation
            if annotation == inspect.Parameter.empty:
                # try to get annotation from base class if it's not specified
                for base in bases:
                    cli_info = getattr(base, 'cli_info', {})
                    if '__init__' in cli_info and param.name in cli_info['__init__'].params and \
                            cli_info['__init__'].params[param.name].annotation != inspect.Parameter.empty:
                        annotation = cli_info['__init__'].params[param.name].annotation
                        break

            desc = param_descriptions.get(param.name, "")
            if desc == '':
                # try to get description from base class if it's not specified
                for base in bases:
                    cli_info = getattr(base, 'cli_info', {})
                    if '__init__' in cli_info and param.name in cli_info['__init__'].params and \
                            cli_info['__init__'].params[param.name].desc != '':
                        desc = cli_info['__init__'].params[param.name].desc
                        break

            params[param.name] = ParamInfo(
                name=param.name,
                annotation=annotation,
                default=param.default,
                desc=desc
            )
        return MethodInfo(name="__init__", short=None, params=params, func=init_func)

    @classmethod
    def parse_method(cls, func: Callable) -> Optional[MethodInfo]:
        docstring = func.__doc__
        if not docstring or ':cli:' not in docstring:
            return None
        # parse short name
        short_name = cls.parse_short_name(docstring)
        param_descriptions = cls.parse_param_descriptions(docstring)
        # parse params
        params = {}
        sig = inspect.signature(func)
        # skip self and key
        for param in list(sig.parameters.values())[2:]:
            params[param.name] = ParamInfo(
                name=param.name,
                annotation=param.annotation,
                default=param.default,
                desc=param_descriptions.get(param.name, "")
            )
        return MethodInfo(name=func.__name__, short=short_name, params=params, func=func)


class Handler(metaclass=HandlerMeta):
    """handler for bilix cli service"""
    pattern: re.Pattern = None
    cli_info: Dict[str, MethodInfo]

    @classmethod
    def decide_handle(cls, method_name: str, keys: Tuple[str, ...]) -> bool:
        """check if the method and keys can be handled by this handler"""
        if cls.pattern:
            return cls.pattern.match(keys[0]) is not None
        else:
            return method_name in cls.cli_info

    @classmethod
    def handle(
            cls,
            method_name: str,
            keys: Tuple[str, ...],
            init_options: dict,
            method_options: dict
    ) -> Tuple[object, Coroutine]:
        if cls.decide_handle(method_name, keys):
            try:
                func = cls.cli_info[method_name].func
            except KeyError:
                raise UsageError(f"For {cls.__name__} method '{method_name}' is not available")
            else:
                handler = cls(**init_options)
                cors = [func(handler, key, **method_options) for key in keys]
                return handler, asyncio.gather(*cors)
