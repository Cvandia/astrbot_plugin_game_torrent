"""Framework-independent models and HTTP client lifecycle."""

from abc import ABC, abstractmethod

from httpx import AsyncClient
from pydantic import BaseModel

DEFAULT_FORMAT = "game: {game_name}\nsize: {size}\nlast_update: {last_update}\nmagnet: {magnet}\n"


class TorrentResource(BaseModel):
    game_name: str
    magnet: str
    size: str
    last_update: str
    torrent_path: str = ""
    is_hacked: bool = True

    def render(self, template: str = DEFAULT_FORMAT) -> str:
        return template.format(**self.model_dump())

    def __str__(self) -> str:
        return self.render()


class TorrentTag(BaseModel):
    game_name: str
    url: str


class BaseFetcher(ABC):
    fetch_name: str
    base_url: str

    def __init__(self, timeout: float = 30, proxy: str = ""):
        self.timeout = timeout
        self.proxy = proxy
        self._client: AsyncClient | None = None

    @property
    def client(self) -> AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = AsyncClient(
                base_url=self.base_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AstrBotGameTorrent/0.1)"},
                timeout=self.timeout,
                proxy=self.proxy or None,
                follow_redirects=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def search(self, keyword: str) -> list[TorrentTag]:
        """Search public game pages."""

    @abstractmethod
    async def fetch(self, tag: TorrentTag) -> TorrentResource | None:
        """Extract a public download link from a result."""
