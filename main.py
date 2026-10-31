"""AstrBot commands and per-user interactive selection."""

import asyncio
import io
import json

import qrcode
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.utils.session_waiter import SessionController, SessionFilter, session_waiter

from .config import Settings
from .exception import RequestError
from .source import SourceManager

CANCEL_WORDS = {"取消", "cancel", "quit", "q"}


class UserSessionFilter(SessionFilter):
    def filter(self, event: AstrMessageEvent) -> str:
        return "game_torrent:" + json.dumps([event.unified_msg_origin, event.get_sender_id()])


def command_argument(event: AstrMessageEvent) -> str:
    """AstrBot removes the configured wake prefix before command dispatch."""
    parts = event.get_message_str().strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else ""


def qr_bytes(link: str) -> bytes:
    output = io.BytesIO()
    qrcode.make(link).save(output, format="PNG")
    return output.getvalue()


class GameTorrentPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.settings = Settings.model_validate(dict(config))
        self.manager = SourceManager(
            StarTools.get_data_dir("astrbot_plugin_game_torrent") / "source.json",
            self.settings.default_source,
            self.settings.request_timeout,
            self.settings.proxy,
        )
        self._active: dict[str, asyncio.Task] = {}
        self._closing = False

    async def initialize(self):
        await self.manager.load()

    def source_menu(self) -> str:
        return (
            f"当前游戏源：{self.manager.current.fetch_name}\n"
            + "\n".join(f"{i + 1}. {f.fetch_name}" for i, f in enumerate(self.manager.fetchers))
            + "\n发送 /切换源 编号或名称 切换，对整个机器人生效。"
        )

    async def _input(self, event: AstrMessageEvent, prompt: str) -> str | None:
        value = None

        @session_waiter(timeout=self.settings.session_timeout)
        async def receive(controller: SessionController, incoming: AstrMessageEvent):
            nonlocal value
            value = incoming.get_message_str().strip()
            incoming.stop_event()
            controller.stop()

        await event.send(event.plain_result(prompt))
        try:
            await receive(event, session_filter=UserSessionFilter())
        except TimeoutError:
            await event.send(event.plain_result("等待回复超时，已结束。发送 /游戏帮助 查看用法。"))
            return None
        if value is None or value.casefold() in CANCEL_WORDS:
            await event.send(event.plain_result("操作已取消。"))
            return None
        return value

    async def _search(self, event: AstrMessageEvent, keyword: str):
        if not keyword:
            keyword = await self._input(
                event, "请回复游戏名（Aimhaven、Fitgirl 请用英文），或发送“取消”。"
            )
            if keyword is None:
                return
        if not keyword.strip():
            await event.send(event.plain_result("游戏名不能为空，请重新发送 /搜游戏 游戏名。"))
            return
        # Keep the same source throughout this search, even if another user switches it.
        fetcher = self.manager.current
        await event.send(event.plain_result(f"正在 {fetcher.fetch_name} 搜索“{keyword}”…"))
        tags = (await fetcher.search(keyword))[: self.settings.max_results]
        if not tags:
            await event.send(
                event.plain_result(f"未找到“{keyword}”。请换个关键词，或发送 /游戏源 更换网站。")
            )
            return
        choice = await self._input(
            event,
            f"{fetcher.fetch_name} 搜索结果：\n"
            + "\n".join(f"{i + 1}. {tag.game_name}" for i, tag in enumerate(tags))
            + f"\n回复编号 1–{len(tags)} 获取链接，或发送“取消”（{self.settings.session_timeout} 秒内）。",
        )
        if choice is None:
            return
        if not choice.isascii() or not choice.isdecimal() or not 1 <= int(choice) <= len(tags):
            await event.send(
                event.plain_result(f"编号无效，请重新发送 /搜游戏 {keyword} 并选择 1–{len(tags)}。")
            )
            return
        resource = await fetcher.fetch(tags[int(choice) - 1])
        if resource is None:
            await event.send(
                event.plain_result("该页面没有可用的公开资源链接，请换一个结果或切换网站。")
            )
            return
        if not resource.is_hacked:
            await event.send(event.plain_result("请按游戏发布页面的说明获取资源。"))
        # Always send text so long links remain accessible if QR encoding fails.
        await event.send(event.plain_result(resource.render(self.settings.torrent_send_format)))
        if self.settings.magnet_to_qrcode:
            try:
                data = await asyncio.to_thread(qr_bytes, resource.magnet)
                await event.send(event.chain_result([Image.fromBytes(data)]))
            except Exception as exc:
                logger.warning(f"游戏资源二维码发送失败：{type(exc).__name__}")
                await event.send(event.plain_result("二维码生成或发送失败，请使用上方文字链接。"))

    async def _switch(self, event: AstrMessageEvent, value: str):
        if not value:
            value = await self._input(
                event, self.source_menu() + "\n请回复编号或网站名称，或发送“取消”。"
            )
            if value is None:
                return
        try:
            await self.manager.select(value)
        except ValueError:
            await event.send(event.plain_result("来源无效，请发送 /游戏源 查看编号和名称。"))
            return
        except OSError:
            logger.exception("保存游戏源失败")
            await event.send(event.plain_result("保存游戏源失败，请检查插件数据目录写入权限。"))
            return
        await event.send(event.plain_result("已更换至" + self.manager.current.fetch_name))

    async def _run(self, event: AstrMessageEvent, action: str, value: str):
        event.stop_event()
        if self._closing:
            return
        key = UserSessionFilter().filter(event)
        if key in self._active:
            await event.send(event.plain_result("你有正在进行的查询，请先回复或发送“取消”。"))
            return
        self._active[key] = asyncio.current_task()
        try:
            if action == "search":
                await self._search(event, value)
            else:
                await self._switch(event, value)
        except RequestError as exc:
            logger.warning(f"游戏资源请求失败：{exc}")
            await event.send(
                event.plain_result("当前网站请求失败，请稍后重试，或发送 /游戏源 更换网站。")
            )
        finally:
            self._active.pop(key, None)

    @filter.command("搜游戏", alias={"游戏搜索", "搜索游戏"})
    async def search_game(self, event: AstrMessageEvent):
        """搜索游戏，回复编号获取链接。"""
        await self._run(event, "search", command_argument(event))

    @filter.command("游戏源")
    async def show_source(self, event: AstrMessageEvent):
        """显示当前游戏源与可用网站。"""
        event.stop_event()
        await event.send(event.plain_result(self.source_menu()))

    @filter.command("切换源", alias={"切换游戏源"})
    async def change_source(self, event: AstrMessageEvent):
        """切换游戏源，支持编号或名称。"""
        await self._run(event, "switch", command_argument(event))

    @filter.command("种子源", alias={"源"})
    async def legacy_source(self, event: AstrMessageEvent):
        """兼容种子源 show/change 指令。"""
        argument = command_argument(event).split(maxsplit=1)
        if not argument or argument[0] in {"show", "显示", "查看"}:
            await self.show_source(event)
        elif argument[0] in {"change", "更换", "切换"}:
            await self._run(event, "switch", argument[1] if len(argument) > 1 else "")
        else:
            event.stop_event()
            await event.send(event.plain_result("用法：/种子源 show 或 /种子源 change 编号或名称"))

    @filter.command("游戏帮助")
    async def game_help(self, event: AstrMessageEvent):
        """显示游戏资源查询帮助。"""
        event.stop_event()
        await event.send(
            event.plain_result(
                "/搜游戏 游戏名：搜索，回复编号获取链接\n"
                "/游戏源：显示网站列表\n/切换源 编号或名称：切换网站\n"
                f"等待输入时发送“取消”结束；{self.settings.session_timeout} 秒未回复自动结束。\n"
                "Aimhaven、Fitgirl 请用英文游戏名。切换源对整个机器人生效。\n"
                "示例使用 / 前缀，实际以 AstrBot 配置的唤醒前缀为准。"
            )
        )

    async def terminate(self):
        self._closing = True
        tasks = set(self._active.values()) - {asyncio.current_task()}
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.manager.aclose()
