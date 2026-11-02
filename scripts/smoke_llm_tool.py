"""Smoke test against the installed AstrBot API, without a model credential."""

import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("astrbot_plugin_game_torrent")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package

main = importlib.import_module("astrbot_plugin_game_torrent.main")
from astrbot.core.provider.register import llm_tools  # noqa: E402

tool = next(item for item in llm_tools.func_list if item.name == "search_game_torrent")
assert tool.parameters["properties"]["keyword"]["type"] == "string"
assert set(tool.parameters["properties"]) == {"keyword"}
assert tool.handler is main.GameTorrentPlugin.search_game_torrent


async def check():
    fetcher = SimpleNamespace(
        fetch_name="SmokeSource",
        base_url="https://example.com",
        search=AsyncMock(return_value=[SimpleNamespace(game_name="Elden Ring", url="/elden-ring")]),
    )
    plugin = main.GameTorrentPlugin.__new__(main.GameTorrentPlugin)
    plugin._closing = False
    plugin.settings = SimpleNamespace(max_results=10)
    plugin.manager = SimpleNamespace(current=fetcher)
    result = json.loads(await tool.handler(plugin, object(), keyword="Elden Ring"))
    assert result["results"] == [
        {"game_name": "Elden Ring", "url": "https://example.com/elden-ring"}
    ]
    fetcher.search.assert_awaited_once_with("Elden Ring")
    print("AstrBot registration, keyword schema and registered handler invocation: PASS")


asyncio.run(check())
