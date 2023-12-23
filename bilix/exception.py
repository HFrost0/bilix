class APIError(Exception):
    """API Error during request to website"""

    def __init__(self, msg: str, resource):
        self.msg = msg
        self.resource = resource

    def __str__(self):
        return f"{self.msg} resource: {self.resource}"


class APIParseError(APIError):
    """API Parse Error, maybe cased by website interface change, raise by decorator"""

    def __init__(self, e, func):
        self.e = e
        self.func = func

    def __str__(self):
        return f"APIParseError Caused by {self.e.__class__.__name__} in <{self.func.__module__}:{self.func.__name__}>"


class APIResourceError(APIError):
    """API Error that resource is not available (like deleted by uploader)"""


class APIUnsupportedError(APIError):
    """The resource parse is not supported yet"""


class APIInvalidError(APIError):
    """API request is invalid"""


class HandleError(Exception):
    """the error related to bilix cli handle"""


class HandleMethodError(HandleError):
    """the error that handler can not recognize the method"""

    def __init__(self, executor_cls, method):
        self.executor_cls = executor_cls
        self.method = method

    def __str__(self):
        return f"For {self.executor_cls.__name__} method '{self.method}' is not available"
