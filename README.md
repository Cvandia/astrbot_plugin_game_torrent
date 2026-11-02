<div align="center">

<a href="https://cloud.astrbot.app/market"><img src="logo.png" width="180" height="180" alt="PluginLogo" style="border-radius: 50%;"></a>

</div>

<div align="center">

# 🎮 astrbot_plugin_game_torrent

_⭐ 基于 AstrBot 的游戏资源搜索插件 ⭐_

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-4.17.0%2B-orange)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

## 🎮 介绍

支持搜索游戏、回复编号获取资源链接、切换网站和发送二维码。

- 四个来源：Aimhaven、Fitgirl、123资源库、Gamer520。
- 支持群聊和私聊，交互按会话与用户隔离。
- 切换源后立即保存，重启可恢复。
- WebUI 可配置默认源、发送格式、二维码、代理、请求超时和结果数量。

## 📜 使用声明

> **尊重版权，支持正版。仅查询、获取和分享已获相应授权的资源；公开可访问、可被搜索或标注“免费”，不等于获得版权授权。**

- **合法使用**：遵守适用法律、来源网站条款与聊天平台规则。请勿利用本插件获取、传播或售卖未经授权的游戏副本、破解内容及侵权链接，或绕过付费、登录及其他访问限制。“学习交流”“非商业用途”不能替代授权。
- **先核实再使用**：优先选择开发者、发行商或正规商店。无法确认授权时，请停止获取和传播；拥有正版副本也不应被视为从任意第三方下载或向他人分享的当然授权。
- **功能边界**：插件仅读取公开页面并提取链接，不托管或下载游戏文件，不处理登录、付费或加密内容；不具备版权核验、侵权过滤或文件安全检测能力。返回链接和二维码不代表合法性、安全性或可用性保证。
- **许可与责任**：游戏及第三方内容的权利归各自权利人所有。本项目的 [MIT 许可](LICENSE) 仅适用于项目代码及相应文档，不授予第三方游戏资源的权利。部署者和用户应审慎管理使用及分享行为，本声明不排除依法应承担的责任。
- **侵权反馈**：如发现本仓库内容或适配逻辑涉嫌侵权，请通过 [Issues](https://github.com/Cvandia/astrbot_plugin_game_torrent/issues) 提供具体位置、权利依据及处理诉求；勿公开提交敏感资料或侵权文件。第三方页面的删除请联系对应网站。

## 💿 安装

需要 Python 3.12+、AstrBot 4.17.0+。

### 在 AstrBot WebUI 安装

进入「插件」页面，通过 Git 仓库地址安装：

```text
https://github.com/Cvandia/astrbot_plugin_game_torrent
```

### 本地安装

把整个仓库目录放在 AstrBot 的 `data/plugins/astrbot_plugin_game_torrent` 下，确保 `main.py`、`metadata.yaml` 与 `_conf_schema.json` 直接位于该目录中。使用 AstrBot 实际运行的 Python 环境安装依赖：

```bash
python -m pip install -r data/plugins/astrbot_plugin_game_torrent/requirements.txt
```

随后重启 AstrBot 或在 WebUI 重载插件。Docker 部署需要把目录放到对应的挂载数据目录，并在容器的 Python 环境中安装依赖。

## ⚙️ 配置

在 AstrBot WebUI 中修改插件配置，保存后重载生效。

| 配置 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `default_source` | string | `Aimhaven` | 首次启动使用的源，支持四个网站名称；已有持久化选择优先 |
| `torrent_send_format` | text | 见下方 | 资源文字格式 |
| `magnet_to_qrcode` | bool | `false` | 在文字后附加链接二维码 |
| `request_timeout` | int | `30` | HTTPX 请求超时秒数，5–120 |
| `session_timeout` | int | `60` | 每次等待输入的超时秒数，10–300 |
| `max_results` | int | `10` | 每次最多显示的结果数量，1–30 |
| `proxy` | string | 空 | 可选 HTTP 代理，如 `http://127.0.0.1:7890`；留空遵循环境代理 |

默认文字格式（输入框中使用实际换行）：

```text
game: {game_name}
size: {size}
last_update: {last_update}
magnet: {magnet}
```

支持 `{game_name}`、`{size}`、`{last_update}`、`{magnet}`、`{torrent_path}`、`{is_hacked}`；不支持属性访问、转换或嵌套格式。`torrent_path` 保留兼容，当前为空。花括号字面量请写作 `{{` 和 `}}`。

当前源保存在 `data/plugin_data/astrbot_plugin_game_torrent/source.json`，优先于 `default_source`，对整个机器人生效；所有有权使用插件的用户均可切换。恢复默认源时，先停止插件，备份并移走此文件，再重载。

代理地址必须能由 AstrBot 进程访问；容器中的 `127.0.0.1` 指容器自身。本插件配置不要求安装 SOCKS 依赖，建议使用 HTTP 代理。

## 🚀 使用

示例使用 `/` 前缀，实际以 AstrBot 的唤醒前缀配置为准。机器人应已连接聊天平台，并允许当前群聊或私聊使用插件。

| 指令 | 作用 | 示例 |
| :--- | :--- | :--- |
| `/搜游戏 游戏名` | 搜索游戏，省略名称时提示输入 | `/搜游戏 奥日` |
| `/游戏源` | 显示当前网站和列表 | `/游戏源` |
| `/切换源 编号或名称` | 切换网站，省略参数时提示输入 | `/切换源 4`、`/切换源 Gamer520` |
| `/游戏帮助` | 查看帮助 | `/游戏帮助` |

兼容别名：`/游戏搜索`、`/搜索游戏`、`/切换游戏源`、`/种子源 show`、`/种子源 change 4`、`/源 show`、`/源 change 4`；`显示`、`查看`、`更换`、`切换` 子命令同样可用。

**快速开始**：以下消息逐条发送，等待机器人回复后再进行下一步；将“游戏名”替换为实际名称。

```text
/游戏源
/切换源 3
/搜游戏 游戏名
1
```

- 收到列表后，由发起查询的用户在同一聊天中回复半角编号（如 `1`，不加 `/`）；插件仅返回链接，不启动下载。
- 等待输入时发送“取消”、`cancel`、`quit` 或 `q` 结束，默认每次等待 60 秒。无效编号、超时、取消或重载后均需重新查询。
- 每位用户在同一聊天中只能进行一次交互；等待期间下一条消息会作为输入，发送新命令前请先取消。
- 每次只搜索当前源，切换源影响全局后续查询，不改变已开始的搜索。用户交互隔离不代表群聊结果保密。

### 支持的网站

| 编号 | 网站 | 搜索语言 | 返回内容 |
| :--- | :--- | :--- | :--- |
| 1 | [Aimhaven](https://www.aimhaven.com/) | 推荐英文 | 页面公开的下载入口 |
| 2 | [Fitgirl](https://fitgirl-repacks.site/) | 推荐英文 | 页面公开的磁力链接 |
| 3 | [123资源库](https://www.123zyk.com/) | 支持中文 | 正文磁力优先，否则第一个公开网盘链接 |
| 4 | [Gamer520](https://www.gamer520.com/) | 支持中文 | 正文磁力优先，其次公开网盘链接，否则该网站明确标注“免费”的下载入口 |

“免费”仅为网站标记，不代表权利人授权或发行商官方入口。

网盘和网站下载入口沿用 `magnet` 输出字段。插件不跟踪下载入口，不自动解析网盘跳转，也不会绕过网站的访问限制。页面缺少大小或更新时间时显示 `Unknown`。平台可能限制磁力链接或图片发送，二维码开关开启时仍会保留文字结果。

**常见问题**：

| 现象 | 处理 |
| :--- | :--- |
| 命令无回复 | 检查插件加载、平台连接、会话权限和唤醒前缀；正在等待输入时先取消 |
| 无结果或无公开链接 | 更换关键词或来源；英文来源优先用英文名，受限页面不支持解析 |
| 请求失败、403 或超时 | 检查运行环境网络、代理和日志，稍后重试；不要绕过访问限制 |
| 切换源未生效或保存失败 | 已保存的源优先于默认配置；使用 `/切换源`，并检查数据目录写入权限 |
| 修改模板后无法加载 | 恢复默认格式，检查占位符、花括号及参数范围 |
| 二维码失败或链接被拦截 | 使用已返回的文字链接；图片和链接发送受平台规则限制 |

反馈问题请附版本、部署方式、使用的源、复现步骤及脱敏日志，勿提交密码、代理凭据或聊天隐私。

## 🛠️ 开发与验证

```bash
python -m venv .venv
# 激活虚拟环境后
python -m pip install -r requirements.txt pytest pytest-asyncio ruff pyyaml
python -m pip install --no-deps astrbot==4.17.0
ruff check .
ruff format --check .
pytest -q
```

离线 HTML 与 HTTP Mock 测试覆盖解析、请求失败、源持久化、交互、用户隔离及二维码。命令测试使用 AstrBot 4.17.0 的真实会话等待模块与模拟消息接口，不能代替端到端验证；CI 覆盖 Python 3.12–3.14。

部署后按上方流程验证命令与编号回复，再检查二维码和重载后的源恢复。测试内容应为自有或已获授权的资源。

## 💝 特别鸣谢

- [Cvandia/nonebot-plugin-game-torrent](https://github.com/Cvandia/nonebot-plugin-game-torrent)：搜索器实现与 README 结构来源；移植参考提交 `0e3c37829b69ed6b0f4afe59c86908a6921ddef5`，保留原 MIT 许可。
- [anka-afk/astrbot_plugin_meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager)：AstrBot 插件组织、元数据及配置描述方式参考。
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：插件框架与原生会话接口。

本项目使用 [MIT License](LICENSE)。
