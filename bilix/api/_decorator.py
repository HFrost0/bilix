from bilix.exception import APIParseError, APIError
from functools import wraps
from httpx import HTTPError, AsyncClient


def api(func):
    @wraps(func)
    async def wrapped(client: AsyncClient, *args, **kwargs):
        try:
            return await func(client, *args, **kwargs)
        except (APIError, HTTPError):
            raise
        except Exception as e:
            raise APIParseError(e, func) from e

    return wrapped
