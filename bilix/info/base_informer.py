import httpx
from rich.console import Console

__all__ = ['BaseInformer']


class BaseInformer:
    console = Console()

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def aclose(self):
        await self.client.aclose()
