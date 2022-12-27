from typing import Callable, Tuple, Union

from bilix.log import logger


class Handler:
    _registered: dict[str, Callable] = {}

    def __init__(self, name):
        self.name = name

    def __call__(self, handle_func: Callable):
        if self.name in self._registered:
            raise HandleNameError(f"Handler name: {self.name} all ready exists")
        self._registered[self.name] = handle_func
        return handle_func

    def __repr__(self):
        return f"Handler <name: {self.name} func:{self._registered['name']}>"

    @classmethod
    def assign(cls, cli_kwargs: dict):
        for name, handle_func in cls._registered.items():
            if name == 'bilibili':
                continue
            if (res := handle_func(**cli_kwargs)) is not None:
                logger.debug(f"Assign to {name}")
                return res
        # since bilix is originally designed for bilibili, finally use bilibili handler
        return cls._registered['bilibili'](**cli_kwargs)


class HandleMethodError(Exception):
    """the error that handler can not recognize the method"""

    def __init__(self, executor, method):
        self.executor = executor
        self.method = method

    def __str__(self):
        return f"For {self.executor.__class__.__name__} method '{self.method}' is not available"


class HandleNameError(Exception):
    """the error that handler name already exist"""
