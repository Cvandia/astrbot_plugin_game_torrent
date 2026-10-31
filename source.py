"""Source selection persisted immediately using atomic file replacement."""

import asyncio
import json
import logging
from pathlib import Path

from .fetcher import AHF, FGF, G520F, ZYKF, BaseFetcher

logger = logging.getLogger(__name__)


class SourceManager:
    def __init__(
        self,
        path: Path,
        default: str = "Aimhaven",
        timeout: float = 30,
        proxy: str = "",
        fetchers: tuple[BaseFetcher, ...] | None = None,
    ):
        self.path = path
        self.fetchers = fetchers or tuple(cls(timeout, proxy) for cls in (AHF, FGF, ZYKF, G520F))
        self.index = self.resolve(default)
        self._lock = asyncio.Lock()

    @property
    def current(self) -> BaseFetcher:
        return self.fetchers[self.index]

    def resolve(self, value: str) -> int:
        if not isinstance(value, str):
            raise ValueError("游戏源必须是编号或网站名称")
        value = value.strip()
        for i, fetcher in enumerate(self.fetchers):
            if value.casefold() == fetcher.fetch_name.casefold() or value == str(i + 1):
                return i
        raise ValueError("无效的游戏源")

    async def load(self) -> None:
        try:
            data = await asyncio.to_thread(self.path.read_text, encoding="utf-8")
            self.index = self.resolve(json.loads(data)["source"])
        except FileNotFoundError:
            pass
        except (OSError, ValueError, KeyError, TypeError):
            logger.warning("游戏源存储不可读或已损坏，使用配置中的默认源。")

    def _write(self, index: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"source": self.fetchers[index].fetch_name}, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    async def select(self, value: str) -> None:
        index = self.resolve(value)
        async with self._lock:
            await asyncio.to_thread(self._write, index)
            self.index = index

    async def aclose(self) -> None:
        await asyncio.gather(*(fetcher.aclose() for fetcher in self.fetchers))
