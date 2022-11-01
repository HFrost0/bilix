from bilix.log import logger


class Handler:
    registered = {}

    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        self.registered[self.name] = func
        return func


def assign(**kwargs):
    bili_handler = Handler.registered.pop('bilibili')
    for name, handle in Handler.registered.items():
        if res := handle(**kwargs):
            logger.debug(f"Assign to {name}")
            return res
    # since bilix is originally designed for bilibili, finally use bilibili handler
    return bili_handler(**kwargs)
