# CLI

> 面向用户的 Kore 命令行入口，参考 Claude Code 风格，走本地 FastAPI

---

## 背景

当前 Kore 已具备后端 Agent Runtime、聊天接口、模型管理接口和配置接口，但还没有统一、可直接使用的终端入口。现阶段需要一个面向最终用户的 CLI，用于提供自然的本地交互体验，同时复用已有 FastAPI 后端能力。

当前已知情况：

- 后端已提供 `/health`、`/api/status`、`/api/chat/send`
- 后端已提供 `/api/models/list`、`/api/models/switch`、`/api/models/providers`
- 后端已提供 `/api/config/models` 的读取与更新能力
- 项目后端依赖中已包含 `rich`，可以用于高质量终端渲染
- 用户希望 CLI 风格参考 Claude Code，强调简洁、专业、清晰，而不是花哨终端玩具

## 当前目标

实现第一版面向用户的 CLI，满足以下目标：

1. 提供一个统一的 `kore` 命令入口
2. 支持进入式聊天体验和单次命令模式
3. 复用本地 FastAPI，而不是重复实现一套 Agent 调用逻辑
4. 提供模型切换、状态查看和基础配置查看能力
5. 在终端中呈现干净、专业、接近 Claude Code 的交互风格

## 当前共识 / 开发方向

本模块按以下方向实现：

- 模块 spec 文件使用 `specs/cli.md`
- CLI 面向最终用户，而不是开发调试工具优先
- CLI 走本地 FastAPI 调用链路，定位为后端之上的终端前端
- 同时支持：
  - 进入式聊天：直接执行 `kore`
  - 单次提问：`kore ask "..."`
  - 状态查看：`kore status`
  - 模型相关：`kore model ...`
  - 配置查看与更新：`kore config ...`
- 风格参考 Claude Code：信息层级清楚、颜色克制、输出整洁、交互反馈直接
- 聊天模式优先提供更详细的终端反馈，而不是只打印最终回复
- 第一版直接支持 `kore config set`
- 当本地后端未启动时，CLI 自动尝试启动后端服务

## 设计方案

### 总体架构

CLI 作为一个轻量终端前端，默认请求本地 Kore 后端：

```text
User Terminal
   -> Kore CLI
   -> HTTP client
   -> http://127.0.0.1:9899
   -> FastAPI backend
```

这样可以复用既有聊天、模型和配置接口，使 CLI、桌面端和未来其他入口共享同一套服务能力。

### 命令结构

第一版建议命令结构如下：

- `kore`
  - 进入聊天模式
- `kore ask "<message>"`
  - 单次发送消息并打印回复
- `kore status`
  - 查看服务状态、当前模型、provider 配置状态
- `kore model list`
  - 查看可用模型与当前模型
- `kore model switch <model>`
  - 切换当前模型
- `kore config show`
  - 查看 provider 配置摘要

第一版直接支持配置写入命令：

- `kore config set --provider deepseek --api-key ...`
- `kore config set --provider deepseek --base-url ...`

### 交互模式

#### 进入式聊天

执行 `kore` 后进入循环会话，行为类似：

- 显示简洁欢迎区与当前模型
- 提示用户直接输入消息
- 每轮请求调用 `/api/chat/send`
- 显示更详细的上下文信息，例如当前模型、会话标识、状态提示和回复区块
- 显示回复后保留输入提示
- 支持基础退出命令，例如 `/exit`、`/quit`
- 支持基础命令，例如 `/model`、`/status`
- 支持基础配置命令，例如 `/thinking`、`/thinking on`、`/thinking off`

#### 单次命令

命令型子命令用于：

- 快速提问
- shell 脚本调用
- 状态检查
- 非交互管理

### 视觉与输出风格

终端风格遵循以下原则：

- 不使用过度装饰
- 使用有限颜色区分系统信息、用户输入、模型回复和错误
- 使用 `rich` 做标题、边框、状态行、表格和错误提示
- 默认输出保持紧凑，不制造大面积噪音
- 对关键状态使用明确标签，例如当前模型、后端地址、provider 是否已配置

目标不是做复杂 TUI，而是做高质量 CLI。

### 后端连接策略

第一版先假设后端地址默认为：

- `http://127.0.0.1:9899`

CLI 需要：

- 在请求失败时明确提示“后端未启动或不可达”
- 输出可执行的后续动作，而不是裸异常栈

第一版需要在后端不可达时自动尝试拉起本地服务。

### 实现建议

第一版可基于：

- `typer` 或 `argparse` 实现命令结构
- `httpx` 作为 HTTP 客户端
- `rich` 负责输出样式

若无额外约束，优先选 `typer`，因为它更适合清晰的命令层次和用户型 CLI。

## 关键接口 / 数据结构

- `GET /health`
- `GET /api/status`
- `POST /api/chat/send`
- `GET /api/models/list`
- `POST /api/models/switch`
- `GET /api/models/providers`
- `GET /api/config/models`

## 约束与取舍

- 第一版优先做 CLI，不扩展为完整 TUI
- 第一版优先复用后端 API，不引入 CLI 直连 AgentCore 的第二套执行逻辑
- 第一版先做清晰体验与基本可用，不强行加入复杂流式输出、会话持久化或多面板布局
- 第一版支持自动拉起本地后端

## 待确认事项

- 是否在后续版本为聊天模式补充流式输出
- 是否需要单独暴露工具调用、推理步骤等更细粒度事件
- 是否需要支持自动拉起后端后的生命周期管理，例如退出 CLI 时是否主动关闭后端

## 实现状态

- 已完成模块方向讨论
- 已确认 CLI 走本地 FastAPI
- 已确认第一版支持 `config set`
- 已确认第一版在后端不可达时自动尝试启动
- 已确认聊天模式需要更详细的终端呈现
- 已新增 `kore` CLI 入口与 `typer` 命令结构
- 已实现 `kore` 进入式聊天模式
- 已实现 `kore ask`、`kore status`、`kore model list`、`kore model switch`
- 已实现 `kore config show` 与 `kore config set`
- 已实现后端健康检查、自动拉起与启动失败日志回显
- 已完成真实命令验证：
  - `kore status` 可自动启动后端并显示状态
  - `kore model switch deepseek-v4-flash` 可成功切换模型
  - `kore config show` 可显示脱敏配置
  - `kore config set --provider deepseek --base-url ...` 可成功写入
  - `kore ask "请只回复 pong"` 可成功返回 `pong`
- 下一步补充聊天模式中的 `/thinking on`、`/thinking off`
