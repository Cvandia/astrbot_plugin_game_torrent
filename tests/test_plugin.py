import asyncio
import json
from unittest.mock import AsyncMock

import pytest
import yaml
from astrbot_plugin_game_torrent.config import Settings
from astrbot_plugin_game_torrent.exception import RequestError
from astrbot_plugin_game_torrent.fetcher import TorrentResource, TorrentTag
from astrbot_plugin_game_torrent.source import SourceManager
from conftest import ROOT
from pydantic import ValidationError


async def wait_registered(api, event):
    for _ in range(100):
        key = api.main.UserSessionFilter().filter(event)
        if key in api.waiter.USER_SESSIONS:
            return key
        await asyncio.sleep(0)
    raise AssertionError("waiter did not register")


async def reply(api, event, text, user=None, origin=None):
    incoming = api.Event(text, user or event.user, origin or event.unified_msg_origin)
    key = api.main.UserSessionFilter().filter(incoming)
    await api.waiter.SessionWaiter.trigger(key, incoming)
    return incoming


def make_plugin(api, config=None):
    plugin = api.main.GameTorrentPlugin(object(), config or {})
    fetcher = plugin.manager.current
    fetcher.search = AsyncMock(return_value=[TorrentTag(game_name="Test Game", url="/1")])
    fetcher.fetch = AsyncMock(
        return_value=TorrentResource(
            game_name="Test Game",
            magnet="magnet:?xt=urn:btih:test",
            size="1GB",
            last_update="Unknown",
        )
    )
    return plugin, fetcher


async def test_search_scoped_to_user_and_chat_and_original_source(plugin_api):
    api = plugin_api
    plugin, fetcher = make_plugin(api)
    event = api.Event("搜游戏 Test Game Deluxe")
    task = asyncio.create_task(plugin.search_game(event))
    await wait_registered(api, event)
    fetcher.search.assert_awaited_once_with("Test Game Deluxe")
    await reply(api, event, "1", user="bob")
    await reply(api, event, "1", origin="test:GroupMessage:other")
    assert not task.done()
    await plugin.manager.select("4")
    incoming = await reply(api, event, "1")
    await task
    assert incoming.stopped
    assert event.stopped
    fetcher.fetch.assert_awaited_once()
    assert "magnet:?xt=" in event.sent[-1]
    assert not plugin._active
    assert not api.waiter.USER_SESSIONS
    assert not api.waiter.FILTERS
    await plugin.terminate()


@pytest.mark.parametrize("response", ["取消", "cancel", "q", "999", "bad", "²"])
async def test_cancel_and_invalid_index(plugin_api, response):
    api = plugin_api
    plugin, fetcher = make_plugin(api)
    event = api.Event("搜游戏 Test")
    task = asyncio.create_task(plugin.search_game(event))
    await wait_registered(api, event)
    await reply(api, event, response)
    await task
    fetcher.fetch.assert_not_awaited()
    assert "取消" in event.sent[-1] or "无效" in event.sent[-1]
    await plugin.terminate()


async def test_keyword_prompt_and_switch_prompt(plugin_api):
    api = plugin_api
    plugin, fetcher = make_plugin(api)
    fetcher.search.return_value = []
    event = api.Event("搜游戏")
    task = asyncio.create_task(plugin.search_game(event))
    await wait_registered(api, event)
    await reply(api, event, "Ori and the Blind Forest")
    await task
    fetcher.search.assert_awaited_once_with("Ori and the Blind Forest")
    event = api.Event("切换源")
    task = asyncio.create_task(plugin.change_source(event))
    await wait_registered(api, event)
    await reply(api, event, "fitgirl")
    await task
    assert plugin.manager.current.fetch_name == "Fitgirl"
    await plugin.terminate()


async def test_timeout_and_terminate_cleanup(plugin_api):
    api = plugin_api
    plugin, _ = make_plugin(api)
    # Bypass dashboard bounds to exercise a real short waiter timeout.
    plugin.settings.session_timeout = 0.01
    event = api.Event("搜游戏 Test")
    await plugin.search_game(event)
    assert "超时" in event.sent[-1]
    assert not api.waiter.USER_SESSIONS
    plugin.settings.session_timeout = 60
    task = asyncio.create_task(plugin.search_game(event))
    await wait_registered(api, event)
    await plugin.terminate()
    assert task.cancelled()
    assert not api.waiter.USER_SESSIONS
    assert not api.waiter.FILTERS


async def test_concurrent_users_and_duplicate_guard(plugin_api):
    api = plugin_api
    plugin, _ = make_plugin(api)
    a, b = api.Event("搜游戏 A"), api.Event("搜游戏 B", user="bob")
    tasks = [asyncio.create_task(plugin.search_game(event)) for event in (a, b)]
    await wait_registered(api, a)
    await wait_registered(api, b)
    duplicate = api.Event("搜游戏 C")
    await plugin.search_game(duplicate)
    assert "正在进行" in duplicate.sent[-1]
    await reply(api, a, "取消")
    await reply(api, b, "1")
    await asyncio.gather(*tasks)
    assert "取消" in a.sent[-1]
    assert "magnet:" in b.sent[-1]
    await plugin.terminate()


async def test_http_error_empty_resource_and_qr(plugin_api):
    api = plugin_api
    plugin, fetcher = make_plugin(api, {"magnet_to_qrcode": True})
    event = api.Event("搜游戏 Test")
    fetcher.search.side_effect = RequestError("HTTP 403")
    await plugin.search_game(event)
    assert "请求失败" in event.sent[-1]
    fetcher.search.side_effect = None
    for resource in [None, fetcher.fetch.return_value]:
        fetcher.fetch.return_value = resource
        task = asyncio.create_task(plugin.search_game(event))
        await wait_registered(api, event)
        await reply(api, event, "1")
        await task
        if resource is None:
            assert "没有可用" in event.sent[-1]
        else:
            assert event.sent[-1][0].startswith(b"\x89PNG")
    await plugin.terminate()


@pytest.mark.parametrize("broken", ["{broken", '{"source": null}', "[]", '{"source": "missing"}'])
async def test_source_persistence_and_corrupt_file(tmp_path, monkeypatch, broken):
    path = tmp_path / "source.json"
    manager = SourceManager(path)
    await manager.load()
    assert manager.current.fetch_name == "Aimhaven"
    await manager.select("4")
    restored = SourceManager(path, "Fitgirl")
    await restored.load()
    assert restored.current.fetch_name == "Gamer520"
    with pytest.raises(ValueError):
        await manager.select("0")
    monkeypatch.setattr(manager, "_write", lambda index: (_ for _ in ()).throw(OSError()))
    with pytest.raises(OSError):
        await manager.select("1")
    assert manager.current.fetch_name == "Gamer520"
    path.write_text(broken, encoding="utf-8")
    fallback = SourceManager(path, "123资源库")
    await fallback.load()
    assert fallback.current.fetch_name == "123资源库"


async def test_qr_failure_keeps_link(plugin_api, monkeypatch):
    api = plugin_api
    plugin, _ = make_plugin(api, {"magnet_to_qrcode": True})

    def fail_qr(link):
        raise ValueError("Too long")

    monkeypatch.setattr(api.main, "qr_bytes", fail_qr)
    event = api.Event("搜游戏 Test")
    task = asyncio.create_task(plugin.search_game(event))
    await wait_registered(api, event)
    await reply(api, event, "1")
    await task
    assert "magnet:" in event.sent[-2]
    assert "二维码生成或发送失败" in event.sent[-1]
    await plugin.terminate()


def test_schema_metadata_defaults_and_format():
    schema = json.loads((ROOT / "_conf_schema.json").read_text(encoding="utf-8"))
    assert Settings(**{key: entry["default"] for key, entry in schema.items()}) == Settings()
    metadata = yaml.safe_load((ROOT / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["name"] == "astrbot_plugin_game_torrent"
    for template in ["{unknown}", "{game_name.__class__}", "{magnet:{size}}", "{", ""]:
        with pytest.raises(ValidationError):
            Settings(torrent_send_format=template)
