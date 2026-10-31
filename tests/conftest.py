"""Load the plugin as AstrBot would, with lightweight event/API doubles."""

import importlib.metadata
import importlib.util
import logging
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("astrbot_plugin_game_torrent")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package


class Event:
    def __init__(self, text="", user="alice", origin="test:GroupMessage:group"):
        self.text = text
        self.user = user
        self.unified_msg_origin = origin
        self.sent = []
        self.stopped = False

    def get_message_str(self):
        return self.text

    def get_sender_id(self):
        return self.user

    def stop_event(self):
        self.stopped = True

    def plain_result(self, text):
        return text

    def chain_result(self, chain):
        return chain

    async def send(self, result):
        self.sent.append(result)


@pytest.fixture
def plugin_api(monkeypatch, tmp_path):
    """Use the real AstrBot waiter without importing unrelated framework services."""
    names = [
        "astrbot",
        "astrbot.api",
        "astrbot.api.event",
        "astrbot.api.message_components",
        "astrbot.api.star",
        "astrbot.core",
        "astrbot.core.utils",
        "astrbot.core.platform",
        "astrbot.core.message",
        "astrbot.core.message.components",
    ]
    modules = {name: ModuleType(name) for name in names}
    for name, module in modules.items():
        module.__path__ = []
        monkeypatch.setitem(sys.modules, name, module)
        if "." in name:
            parent, attr = name.rsplit(".", 1)
            setattr(modules[parent], attr, module)
    modules["astrbot.api"].AstrBotConfig = dict
    modules["astrbot.api"].logger = logging.getLogger("test")
    modules["astrbot.api.event"].AstrMessageEvent = Event
    modules["astrbot.api.event"].filter = SimpleNamespace(
        command=lambda *args, **kwargs: lambda fn: fn,
    )
    modules["astrbot.api.message_components"].Image = SimpleNamespace(fromBytes=lambda data: data)
    modules["astrbot.core.platform"].AstrMessageEvent = Event
    modules["astrbot.core.message.components"].BaseMessageComponent = object

    class Star:
        def __init__(self, context):
            self.context = context

    modules["astrbot.api.star"].Star = Star
    modules["astrbot.api.star"].Context = object
    modules["astrbot.api.star"].StarTools = SimpleNamespace(get_data_dir=lambda name: tmp_path)
    source = os.environ.get("ASTRBOT_SESSION_WAITER")
    if not source:
        source = str(
            importlib.metadata.distribution("astrbot").locate_file(
                "astrbot/core/utils/session_waiter.py",
            )
        )
    name = "astrbot.core.utils.session_waiter"
    spec = importlib.util.spec_from_file_location(name, source)
    waiter = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, waiter)
    spec.loader.exec_module(waiter)
    name = "astrbot_plugin_game_torrent.main"
    spec = importlib.util.spec_from_file_location(name, ROOT / "main.py")
    main = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, main)
    spec.loader.exec_module(main)
    return SimpleNamespace(main=main, waiter=waiter, Event=Event)
