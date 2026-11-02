<div align="center">

<a href="https://cloud.astrbot.app/market"><img src="logo.png" width="180" height="180" alt="PluginLogo" style="border-radius: 50%;"></a>

</div>

<div align="center">

# astrbot_plugin_game_torrent


_⭐ 基于 AstrBot 的游戏资源搜索插件 ⭐_

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![AstrBot](https://img.shields.io/badge/AstrBot-4.17.0%2B-orange)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

## ⭐ 介绍

支持搜索游戏、回复编号获取资源链接、切换网站和发送二维码。

- 四个来源：Aimhaven、Fitgirl、123资源库、Gamer520。
- 使用 AstrBot 原生命令与会话等待接口，支持群聊和私聊；群内不同用户的结果选择相互隔离。
- 源切换立即持久化，重启后恢复；进行中的搜索始终使用开始时的网站。
- WebUI 可配置默认源、发送格式、二维码、代理、请求超时和结果数量。

## 📜 使用声明

请仅查询和使用你有权访问、下载与分享的资源，遵守来源网站条款和相关法律法规，支持正版游戏。插件只读取公开页面，不下载游戏文件，不处理登录、付费或加密内容。外部网站的内容、可用性与安全性由各网站负责。

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

在 AstrBot WebUI 的插件配置中修改，保存后重载插件生效。无需编辑 NoneBot 的 `.env`。

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

当前源保存在 `data/plugin_data/astrbot_plugin_game_torrent/source.json`，切换成功后立即写入。它对整个机器人生效，所有有权使用插件的用户均可切换。要恢复配置中的默认源，可停止插件后移走此文件，再重载。搜索会话只存在内存中，重载后需重新查询。

代理地址必须能由 AstrBot 进程访问；容器中的 `127.0.0.1` 指容器自身。本插件配置不要求安装 SOCKS 依赖，建议使用 HTTP 代理。

## ⭐ 使用

示例使用 `/` 前缀，实际以 AstrBot 的唤醒前缀配置为准。机器人应已连接聊天平台，并允许当前群聊或私聊使用插件。

| 指令 | 作用 | 示例 |
| :--- | :--- | :--- |
| `/搜游戏 游戏名` | 搜索游戏，省略名称时提示输入 | `/搜游戏 奥日` |
| `/游戏源` | 显示当前网站和列表 | `/游戏源` |
| `/切换源 编号或名称` | 切换网站，省略参数时提示输入 | `/切换源 4`、`/切换源 Gamer520` |
| `/游戏帮助` | 查看帮助 | `/游戏帮助` |

兼容别名：`/游戏搜索`、`/搜索游戏`、`/切换游戏源`、`/种子源 show`、`/种子源 change 4`、`/源 show`、`/源 change 4`；`显示`、`查看`、`更换`、`切换` 子命令同样可用。

搜索后直接回复结果编号，无需再加命令前缀。等待输入时回复“取消”、`cancel`、`quit` 或 `q` 结束；默认 60 秒未回复自动结束。每位用户在同一聊天中同时只能进行一次交互。等待期间该用户的下一条消息会作为输入，请先取消再发新命令。

**首次查询流程**（每步等待机器人回复后再发送下一条消息）：

1. 发送 `/游戏帮助` 查看指令，再发送 `/游戏源` 确认当前源。
2. 如需更换，发送 `/切换源 3`，等待切换成功提示。该操作会影响整个机器人后续的搜索。
3. 发送 `/搜游戏 游戏名`，将“游戏名”替换为你已核实有权获取的游戏名称。也可只发送 `/搜游戏`，再按提示回复名称。
4. 收到结果列表后，在**同一聊天中由发起查询的用户**回复半角数字，例如 `1`。不要发送 `/1`、全角数字或结果标题。
5. 收到资源信息后，先核实链接目标及授权条件。插件只返回链接，不会启动下载、发送游戏安装包或验证链接中的文件。

```text
/游戏源
/切换源 3
/搜游戏 游戏名
1
```

上方各行应逐条发送，“游戏名”是占位文本；若没有搜索结果，则无需回复编号。编号仅对应当前列表，不能在会话结束后继续使用旧编号。

**交互注意事项**：

- 输入无效或超出范围的编号会结束本次选择，需要重新搜索；当前实现不会持续提示重输，也不支持一次选择多个编号。
- 超时、取消或插件重载后，请重新发起命令。省略游戏名时，“输入名称”和“选择编号”分别按 `session_timeout` 等待。
- 同一群聊中不同用户可以分别查询，私聊与群聊的交互也相互隔离；这只是输入匹配隔离，不代表群聊结果保密。
- 等待名称、编号或源名称时，先单独发送“取消”并等待确认，再发送其他命令，避免新命令被当作本轮输入。
- 搜索只查询当前选中的一个网站，不会同时聚合四个来源；已开始的网站搜索不会因他人切换源而改变。

### 支持的网站

| 编号 | 网站 | 搜索语言 | 返回内容 |
| :--- | :--- | :--- | :--- |
| 1 | [Aimhaven](https://www.aimhaven.com/) | 推荐英文 | 页面公开的下载入口 |
| 2 | [Fitgirl](https://fitgirl-repacks.site/) | 推荐英文 | 页面公开的磁力链接 |
| 3 | [123资源库](https://www.123zyk.com/) | 支持中文 | 正文磁力优先，否则第一个公开网盘链接 |
| 4 | [Gamer520](https://www.gamer520.com/) | 支持中文 | 正文磁力优先，其次公开网盘链接，否则该网站明确标注“免费”的下载入口 |

这里的“免费”仅为来源网站页面标记，不代表游戏权利人授权，也不代表该入口属于游戏开发者或发行商。

网盘和网站下载入口沿用 `magnet` 输出字段。插件不跟踪下载入口，不自动解析网盘跳转，也不会绕过网站的访问限制。页面缺少大小或更新时间时显示 `Unknown`。平台可能限制磁力链接或图片发送，二维码开关开启时仍会保留文字结果。

**常见问题排查**：

| 现象 | 检查与处理 |
| :--- | :--- |
| 发送命令没有回复 | 确认插件成功加载、平台连接正常、当前会话获准使用插件，并核对唤醒前缀；若仍在等待输入，先发送“取消” |
| 未找到游戏 | 当前来源可能没有收录，或关键词不匹配；缩短名称，英文来源优先使用英文名，必要时切换源后重新查询 |
| 编号无效或回复编号无反应 | 使用当前列表范围内的半角数字，确认由同一用户在同一会话、超时前回复；已结束的会话需重新搜索 |
| 网站请求失败、403 或超时 | 查看运行日志，检查 AstrBot 所在环境的网络和代理；稍后重试或切换可合法访问的来源，不要尝试绕过访问控制 |
| 页面没有可用公开链接 | 页面可能只有受限入口，或网站结构已变化；不要尝试绕过登录、付费或加密限制，可反馈解析问题 |
| 更改默认源后仍使用旧源 | 已保存的选择优先；使用 `/切换源`，或按上文步骤备份并移走 `source.json` 后重载 |
| 保存游戏源失败 | 检查插件数据目录及 Docker 挂载目录的写入权限；处理后重新切换，并通过 `/游戏源` 确认 |
| 模板修改后无法加载 | 恢复默认格式，核对字段名称、花括号和参数范围；保存后重载 |
| 文字已发出但二维码失败 | 可能是链接过长、图片生成或平台发送失败；使用已经返回的文字链接，或关闭二维码 |
| 显示 `Unknown`、链接失效或平台拦截 | `Unknown` 表示页面未提供可解析信息；链接可用性和平台发送限制不由插件保证，不要据此推断资源安全或已获授权 |

反馈故障时请附上插件与 AstrBot 版本、部署方式、使用的源、复现步骤及脱敏后的错误日志。不要提交账号密码、代理凭据、聊天隐私或未经授权的资源文件。

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

测试使用离线 HTML 和 HTTP Mock，覆盖网站解析、请求失败、源持久化、交互取消、超时、用户隔离与二维码。命令测试运行 AstrBot 4.17.0 的真实会话等待模块，事件与消息发送使用轻量接口替身；不能代替真实 AstrBot 与聊天平台的端到端验证。GitHub Actions 配置为 Python 3.12、3.13、3.14。

真实部署后建议依次验证 `/游戏帮助`、`/游戏源`、`/切换源 3`、`/搜游戏 奥日` 和编号回复，再验证二维码与重载后的源恢复。网站结构、风控或网络环境可能导致查询失败，遇到 403 或超时可切换源或检查代理。

## 💝 特别鸣谢

- [Cvandia/nonebot-plugin-game-torrent](https://github.com/Cvandia/nonebot-plugin-game-torrent)：搜索器实现与 README 结构来源；移植参考提交 `0e3c37829b69ed6b0f4afe59c86908a6921ddef5`，保留原 MIT 许可。
- [anka-afk/astrbot_plugin_meme_manager](https://github.com/anka-afk/astrbot_plugin_meme_manager)：AstrBot 插件组织、元数据及配置描述方式参考。
- [AstrBot](https://github.com/AstrBotDevs/AstrBot)：插件框架与原生会话接口。

本项目使用 [MIT License](LICENSE)。
