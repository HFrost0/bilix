import browser_cookie3
import httpx
from rich.console import Console

__all__ = ['BaseInformer']

from bilix.log import logger


class BaseInformer:
    console = Console()

    def __init__(self, client: httpx.AsyncClient, browser: str = None):
        self.client = client
        if browser:  # load cookies from browser, may need auth
            try:
                f = getattr(browser_cookie3, browser.lower())
                logger.debug(f"trying to load cookies from {browser}, may need auth")
                self.client.cookies.update(f())
            except AttributeError:
                raise AttributeError(f"Invalid Browser {browser}")

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        await self.client.aclose()
