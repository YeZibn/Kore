# Channel Interfaces

> CLI、Chat UI、Tauri / Web 等各类 agent 接入端。

---

## 当前状态

- CLI 已有第一版实现
- Chat UI 仍未开始实质实现

## 当前共识 / 开发方向

- `channel-interfaces.md` 作为所有面向用户入口的主 spec
- 历史 `cli.md` 暂时保留为 CLI 第一版详细记录，新任务优先写入本文件
- CLI 面向最终用户，风格参考 Claude Code，保持简洁、专业、输出层级清晰
- CLI 欢迎区应展示 Kore 品牌文字、当前运行状态、模型、thinking、workspace、session 与常用命令
- CLI 欢迎区应使用 ASCII icon + wordmark 表达 Kore 品牌，不直接渲染 JPG 图像
- CLI `/help` 应使用中文分组说明，覆盖对话、模型、工作空间、服务控制、退出等命令
- CLI `/status` 应展示更完整的运行状态，包括 backend、health、version、当前模型、可用模型数量、thinking、workspace
- CLI ASCII icon + wordmark 欢迎区、中文 `/help` 和详细 `/status` 已实现
- CLI REPL 输入层应使用 `prompt_toolkit`，避免 `rich.prompt` 在中文、长文本和退格编辑上的不稳定
- CLI REPL 输入层应支持基础历史记录和内部命令补全
- CLI REPL 输入层已升级为 `prompt_toolkit`；非 TTY 输入回退到 `input()`，便于脚本化验证
- CLI 通过本地 FastAPI 接入 runtime，不重复实现 Agent 调用逻辑
- CLI 在后端不可达时自动尝试启动本地服务
- CLI 自动启动的后端默认会常驻；用户可通过 REPL `/shutdown` 主动关闭
- CLI 支持进入式聊天、单次提问、状态查看、模型切换、配置查看与配置写入
- CLI 模型列表只展示后端返回的正式可用模型
- CLI 切换不存在模型时必须展示明确错误，不应静默切换
- CLI 聊天模式支持 `/thinking`、`/thinking on`、`/thinking off`
- CLI 聊天模式支持 `/workspace` 查看当前 workspace
- CLI 聊天模式支持 `/workspace <path>` 切换当前 workspace
- workspace 第一版只做 REPL 内部命令，不新增外部 `kore workspace` 命令
- `/workspace` REPL 命令已实现
- `/shutdown` REPL 命令用于关闭当前后端并退出聊天
- `/server stop` 作为 `/shutdown` 的等价别名
- `/shutdown` 与 `/server stop` 已实现
- `/chat restart` REPL 命令用于重开当前对话 session，不重启后端
- `/server restart` REPL 命令用于重启当前后端服务，并留在 REPL 中继续使用
- `/chat restart` 与 `/server restart` 已实现
- Kore 第一版专属图标采用用户提供的原始 JPG：`loop + core sparkle + lowercase kore wordmark`

## CLI 命令结构

- `kore`
- `kore ask "<message>"`
- `kore status`
- `kore model list`
- `kore model switch <model>`
- `kore config show`
- `kore config set --provider <provider> ...`

## REPL 内部命令

- `/help`
- `/status`
- `/model`
- `/model <model_name>`
- `/thinking`
- `/thinking on`
- `/thinking off`
- `/workspace`
- `/workspace <path>`
- `/chat restart`
- `/shutdown`
- `/server stop`
- `/server restart`
- `/quit`
- `/exit`

workspace 命令语义：

- `/workspace` 调用 `GET /api/config/workspace` 并展示当前路径、是否存在、是否为目录
- `/workspace <path>` 调用 `PUT /api/config/workspace` 修改当前 workspace
- 修改成功后立即影响后续文件工具调用
- 修改失败时展示明确错误，不进入普通聊天请求

shutdown 命令语义：

- `/shutdown` 调用 `POST /api/server/shutdown`
- `/server stop` 与 `/shutdown` 等价
- 成功请求关闭后，CLI 显示提示并退出当前 REPL
- `/quit` 和 `/exit` 仍只退出聊天，不关闭后端

restart 命令语义：

- `/chat restart` 生成新的 session id，并刷新欢迎状态，不关闭后端
- `/server restart` 调用 shutdown API，等待当前后端停止，再由 CLI 自动启动新后端
- `/server restart` 成功后刷新模型、thinking、workspace 等运行状态，并继续停留在 REPL
- `/server restart` 不改变 `.env` 中的持久化配置

## Brand Icon

第一版图标方向：

- 主体是 `∞` loop 与 core sparkle 的组合
- `∞` 表示 Agent loop、ReAct 循环与长期运行
- sparkle 表示智能核心、工具触发与运行时中枢
- 完整 logo 使用 lowercase `kore` 字标
- 第一版直接保存用户提供的 JPG，不再转成 SVG
- CLI welcome banner 后续可使用简化文字版，不强行渲染图片

当前资产：

- `assets/kore-logo.jpg`

## 后续方向

- Chat UI / Tauri / Web 接入同一套 API，不绕过 runtime
- 后续如果工具调用确认进入用户界面，CLI 与 Chat UI 都应消费同一套 confirmation 结构
- 流式输出和 ReAct 过程展示应优先通过 API 事件流提供，而不是在 channel 内各自实现
