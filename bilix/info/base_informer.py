import httpx
from rich.console import Console
from bilix.utils import update_cookies_from_browser


class BaseInformer:
    console = Console()

    def __init__(self, client: httpx.AsyncClient, browser: str = None):
        self.client = client
        if browser:  # load cookies from browser, may need auth
            update_cookies_from_browser(self.client, browser, self.domain if hasattr(self, "domain") else "")

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        await self.client.aclose()
