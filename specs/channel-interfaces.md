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
- `/shutdown`
- `/server stop`
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

## 后续方向

- Chat UI / Tauri / Web 接入同一套 API，不绕过 runtime
- 后续如果工具调用确认进入用户界面，CLI 与 Chat UI 都应消费同一套 confirmation 结构
- 流式输出和 ReAct 过程展示应优先通过 API 事件流提供，而不是在 channel 内各自实现
