import threading


class Handler:
    registered = {}
    _lock = threading.RLock()

    def __init__(self, name):
        self.name = name

    def __call__(self, handle_func):
        with self._lock:
            if self.name in self.registered:
                raise KeyError(f"Handler {self.name} all ready exists")
            self.registered[self.name] = handle_func
        return handle_func

    def __repr__(self):
        return f"Handler <name: {self.name} func:{self.registered['name']}>"
