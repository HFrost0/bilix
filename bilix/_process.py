import signal
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial


def _init():
    def shutdown(*args):
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)


def singleton(cls):
    _instance = {}

    def inner(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return inner


# singleton ProcessPoolExecutor to avoid recreation in spawn process
SingletonPPE = singleton(partial(ProcessPoolExecutor, initializer=_init))

if __name__ == '__main__':
    p = SingletonPPE(max_workers=5)
    p.shutdown()
