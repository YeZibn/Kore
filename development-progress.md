# Kore 开发进度

> 个人 AI 助手 & Agent Runtime
> 技术栈：Python (FastAPI) + Tauri (React + TypeScript)

---

## 项目定位

Kore 是一个面向个人的超级 AI 助手，运行在本地桌面，具备：
- 双模式自适应执行（Direct 快捷 / Plan 规划）
- 工具调用（文件、终端、浏览器、搜索等）
- 三层记忆系统（上下文 → 日记忆 → 核心记忆）
- 知识库（Markdown Wiki + 知识图谱）
- 技能系统（安装、管理、执行）
- 多渠道接入（Web/Tauri、Telegram、微信等）
- MCP 协议集成
- 可观察性（Trace 事件流）

---

## 设计原则

1. **轻量优先** — 简单请求走快捷路径，复杂任务才启用规划
2. **结构优先于 Prompt** — 用状态机和类型系统承担约束
3. **可观察性** — 系统能清楚回答"在做什么、做到哪、为什么停"
4. **各层解耦** — 每一层可独立替换和扩展
5. **单机部署** — SQLite + 本地文件系统，零外部依赖

---

## 架构概览

```
Tauri Desktop (React + TypeScript)
        │ HTTP / SSE
        ▼
Python Backend (FastAPI)
        │
   ┌────┴────┐
   │ AgentCore │
   └────┬────┘
        │
   Router (Direct / Plan)
        │
   ┌────┴────┐
   │         │
 Direct    Plan
 (ReAct)  (Steps → ReAct per step)
   │         │
   └────┬────┘
        │
   ┌────┴────────────────┐
   │    │    │    │       │
  LLM  Tools Memory Skills
   │    │    │    │       │
   └────┴────┴────┴───────┘
        │
   Storage (SQLite + ChromaDB + Files)
```

---

## 目录结构

```
Kore/
├── backend/                      # Python 后端
│   ├── pyproject.toml            # 依赖与构建配置
│   ├── .env.example              # 环境变量模板
│   ├── kore/
│   │   ├── runtime/              # 运行时核心 (AgentCore, RunContext, Router)
│   │   ├── solver/               # 局部求解器 (ReAct 循环)
│   │   ├── llm/                  # 多模型抽象层 (OpenAI, Claude, DeepSeek, Qwen)
│   │   ├── tools/                # 工具系统 (Registry, Executor, 内置工具)
│   │   ├── memory/               # 三层记忆系统
│   │   ├── knowledge/            # 知识库 (Wiki + 知识图谱)
│   │   ├── skills/               # 技能系统 (Loader, Executor, Hub)
│   │   ├── channels/             # 多渠道接入
│   │   ├── mcp/                  # MCP 协议集成
│   │   ├── api/                  # REST API 路由
│   │   ├── storage/              # 存储层 (SQLite + ChromaDB)
│   │   ├── tracing/              # 可观察性 (Trace 事件流)
│   │   └── prompting/            # Prompt 模板与构建
│   └── tests/
│
├── frontend/                     # Tauri 桌面端
│   ├── src-tauri/                # Rust 层 (窗口管理, Python sidecar)
│   │   ├── Cargo.toml
│   │   └── src/main.rs
│   └── src/                      # React + TypeScript
│       ├── pages/                # Chat, Memory, Knowledge, Skills, Settings
│       ├── components/           # UI 组件
│       ├── hooks/                # useChat, useSSE
│       ├── services/             # API 调用封装
│       └── types/                # TypeScript 类型定义
│
├── skills/                       # 技能目录
├── data/                         # 运行时数据 (.gitignore)
│   ├── memory/                   # 记忆数据
│   ├── knowledge/                # 知识库文件
│   └── traces/                   # Trace 事件
└── scripts/                      # 部署/运维脚本
```

---

## 开发阶段规划

### Phase 1: 基础骨架 ← **当前阶段**

目标：项目结构搭建，基础框架能跑通

| 任务 | 状态 | 说明 |
|------|------|------|
| 目录结构创建 | ✅ 完成 | 后端 + 前端目录骨架 |
| Python 依赖配置 | ✅ 完成 | pyproject.toml |
| 环境变量模板 | ✅ 完成 | .env.example |
| .gitignore | ✅ 完成 | |
| 后端 FastAPI 入口 | ⬜ 待做 | main.py, config.py, API router |
| 后端能启动运行 | ⬜ 待做 | uvicorn 启动，/health 可访问 |
| 前端 Tauri + React 初始化 | ⬜ 待做 | npm create + Tauri 配置 |
| 前端能启动运行 | ⬜ 待做 | 显示空白页面即可 |

### Phase 2: 核心执行框架

目标：Agent 能接收消息并返回回复

| 任务 | 状态 | 说明 |
|------|------|------|
| LLM 抽象层 | ⬜ 待做 | LLMProvider 基类, ChatResponse |
| OpenAI Provider | ⬜ 待做 | 基于 openai SDK |
| DeepSeek Provider | ⬜ 待做 | OpenAI 兼容接口 |
| AgentCore | ⬜ 待做 | 路由判断 + Direct 模式 ReAct |
| 工具注册中心 | ⬜ 待做 | ToolRegistry, @tool 装饰器 |
| 基础工具实现 | ⬜ 待做 | web_search, read_file |
| Chat API | ⬜ 待做 | POST /api/chat/send (SSE 流式) |
| 端到端测试 | ⬜ 待做 | 发送消息 → Agent 调用 LLM → 返回回复 |

### Phase 3: Plan 模式 + 工具扩展

目标：复杂任务规划能力，更多内置工具

| 任务 | 状态 | 说明 |
|------|------|------|
| Router 实现 | ⬜ 待做 | LLM 判断 Direct vs Plan |
| Plan 生成 | ⬜ 待做 | LLM 生成步骤列表 |
| 逐步执行 | ⬜ 待做 | 每个 step 内部 ReAct |
| Plan API 事件 | ⬜ 待做 | SSE 推送 plan/step_start/step_complete |
| write_file 工具 | ⬜ 待做 | |
| web_fetch 工具 | ⬜ 待做 | |
| terminal 工具 | ⬜ 待做 | |
| MCP 客户端 | ⬜ 待做 | 连接外部 MCP Server |

### Phase 4: 记忆系统

目标：Agent 拥有跨会话记忆

| 任务 | 状态 | 说明 |
|------|------|------|
| 对话上下文管理 | ⬜ 待做 | 滑动窗口 + token 预算 |
| 日记忆 | ⬜ 待做 | 每日自动提取摘要 |
| 核心记忆 MEMORY.md | ⬜ 待做 | 长期记忆文件 |
| Deep Dream 蒸馏 | ⬜ 待做 | 定期将日记忆蒸馏到核心记忆 |
| 混合检索 | ⬜ 待做 | 关键词 + 向量 (ChromaDB) |
| Memory API | ⬜ 待做 | /api/memory/* 端点 |

### Phase 5: 知识库 + 技能系统

目标：结构化知识管理 + 可扩展技能

| 任务 | 状态 | 说明 |
|------|------|------|
| Wiki 管理器 | ⬜ 待做 | Markdown wiki CRUD |
| 知识图谱数据模型 | ⬜ 待做 | 节点 + 边 |
| 知识自动提取 | ⬜ 待做 | 从对话中提取有价值信息 |
| 技能 Manifest 格式 | ⬜ 待做 | YAML 定义 |
| 技能加载器 | ⬜ 待做 | 从目录加载技能 |
| Skill Hub 客户端 | ⬜ 待做 | 搜索和安装技能 |

### Phase 6: 前端 UI

目标：Tauri 桌面应用完整交互界面

| 任务 | 状态 | 说明 |
|------|------|------|
| Tauri 初始化 | ⬜ 待做 | create-tauri-app |
| Python sidecar 管理 | ⬜ 待做 | Tauri 启动时自动拉起后端 |
| 对话页面 | ⬜ 待做 | 消息列表 + 输入框 |
| SSE 流式展示 | ⬜ 待做 | 实时显示 Agent 思考过程 |
| 设置页面 | ⬜ 待做 | 模型配置、API Key |
| 记忆管理页面 | ⬜ 待做 | 查看/编辑记忆 |
| 知识图谱可视化 | ⬜ 待做 | react-force-graph |

### Phase 7: 多渠道 + 打磨

目标：接入更多渠道，整体打磨

| 任务 | 状态 | 说明 |
|------|------|------|
| Web Channel | ⬜ 待做 | 默认渠道 |
| Telegram Channel | ⬜ 待做 | python-telegram-bot |
| 渠道管理 UI | ⬜ 待做 | 设置页面中添加/配置渠道 |
| Trace 查看 UI | ⬜ 待做 | 查看运行历史详情 |
| 打包发布 | ⬜ 待做 | Tauri build → .app / .dmg |

---

## 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端框架 | FastAPI + uvicorn | 最新稳定版 |
| 数据库 | SQLite (aiosqlite) | |
| 向量存储 | ChromaDB | |
| LLM SDK | openai, anthropic, httpx | |
| 前端框架 | React + TypeScript | 18+ |
| 构建工具 | Vite | |
| 桌面壳 | Tauri | 2.x |
| UI 样式 | Tailwind CSS + shadcn/ui | |
| 包管理 | pip/venv (Python), pnpm (Node) | |

---

## 执行框架设计（核心）

### 双模式自适应

```
用户消息 → Router → Direct 模式 (简单请求)
                  → Plan 模式   (复杂任务)
```

**Direct 模式**：纯 ReAct 循环
```
LLM → tool_call → 执行 → 观察 → LLM → ... → 无 tool_call → 返回回复
```

**Plan 模式**：先规划再逐步执行
```
LLM 生成 Plan [Step1, Step2, Step3]
→ 逐步执行，每步内部是 ReAct 循环
→ 最后一步的 result = 最终回复
```

### 关键数据结构

- `RunMode`: DIRECT | PLAN
- `RunContext`: 一次运行的完整上下文
- `PlanStep`: 轻量步骤（id, name, goal, depends_on, status, result）
- `Message`: 统一消息格式
- `ToolCall`: 工具调用（id, name, arguments）
- `ChatResponse`: LLM 响应（content, tool_calls, usage）

---

## 开发日志

### 2026-06-04: Phase 1 — ReAct 推理框架最小实现

**完成内容**：
- 配置管理 (`config.py`) — KoreConfig + 子配置，支持 .env 加载
- LLM 抽象层 (`llm/`) — LLMProvider 基类、OpenAIProvider、LLMFactory
- 工具系统 (`tools/`) — ToolRegistry、@tool 装饰器、ToolExecutor、3 个内置工具
- ReAct 推理循环 (`runtime/agent_core.py`) — Direct 模式 ReAct 循环
- Prompt 管理 (`prompting/`) — 模板 + PromptBuilder
- FastAPI 入口 + Chat API — `/health`、`/api/status`、`POST /api/chat/send`

**验证结果**：
- `/health` 返回 `{"status": "ok"}`
- `/api/status` 返回 `{"status": "running"}`
- 服务正常启动于 `http://127.0.0.1:9899`

**环境**：使用 huolala Python 环境 (`/Users/yezibin/huolala/`)

**Spec 文档**：`specs/agent-runtime.md`

### 2026-06-04: Phase 2 — 模型切换与完整 API

**完成内容**：
- ModelState 全局状态 (`runtime/models.py`) — 运行时模型切换、Provider 列表
- AgentCore 改造 (`runtime/agent_core.py`) — 从 ModelState 读取当前模型
- 模型管理 API (`api/models.py`) — `/api/models/list`、`/api/models/switch`、`/api/models/providers`
- 配置读写 API (`api/config.py`) — `/api/config/models` GET/PUT（API Key 脱敏显示）

**新增端点**：
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models/list` | 列出可用模型 + 当前模型 |
| POST | `/api/models/switch` | 切换当前模型 |
| GET | `/api/models/providers` | 列出 Provider 及配置状态 |
| GET | `/api/config/models` | 获取模型配置（API Key 脱敏） |
| PUT | `/api/config/models` | 更新模型配置 |

**验证结果**：
- 模型切换成功：`deepseek-chat` → `gpt-4o`
- 配置更新成功：API Key 脱敏显示为 `sk-*********6789`
- Provider 状态联动：配置后 `configured: true`

### 2026-06-05: LLM config and switching — `.env` 持久化与返回模型修正

- 对应 spec: `specs/llm-config-and-switching.md`
- 完成内容:
  - 将后端配置文件路径显式固定为 `backend/.env`
  - 为 provider 配置更新增加 `.env` 持久化逻辑，保留原有运行时内存更新
  - 修正 `POST /api/chat/send` 的 `model` 字段，改为返回运行时 `current_model`
  - 将后端 Python 版本要求从 `>=3.12` 调整为 `>=3.11`，以匹配 `agent` conda 环境
  - 写入 DeepSeek 本地配置并完成真实联调
- 关键决策:
  - 本次只将 provider 配置写回 `.env`，不把运行时模型切换结果持久化
  - 缺少 `backend/.env` 时，持久化逻辑以 `.env.example` 为模板生成
  - 为优先完成联调，接受当前后端运行时约束下调到 Python 3.11
- 验证情况:
  - 已通过 `py_compile` 完成改动文件语法校验
  - 使用 `agent` conda 环境安装后端依赖成功
  - `GET /api/models/providers` 返回 DeepSeek `configured: true`
  - `POST /api/models/switch` 成功切换 `deepseek-chat -> gpt-4o`
  - 真实 DeepSeek 调用成功：`POST /api/chat/send` 返回 `200`，响应 `{"reply":"pong","model":"deepseek-chat"}`
- 后续事项:
  - 如需长期运行服务，可补充启动脚本或固定后端运行环境说明

### 2026-06-05: CLI — 面向用户的终端入口首版实现

- 对应 spec: `specs/cli.md`
- 完成内容:
  - 新增 `kore` 命令入口和 `backend/kore/cli.py`
  - 基于 `typer + httpx + rich` 实现用户型 CLI
  - 支持 `kore` 聊天模式、`kore ask`、`kore status`
  - 支持 `kore model list`、`kore model switch`
  - 支持 `kore config show`、`kore config set`
  - 实现后端健康检查与本地后端自动拉起
  - 为自动拉起失败补充启动日志尾部回显
- 关键决策:
  - CLI 走本地 FastAPI，而不是直连 AgentCore
  - 第一版优先做高质量 CLI，不扩展为复杂 TUI
  - 聊天模式输出更详细上下文，但不展示内部推理和工具调用事件
- 验证情况:
  - 已通过 `py_compile` 校验 CLI 文件语法
  - `python -m kore.cli --help` 正常显示命令结构
  - `kore status` 可自动启动后端并展示当前模型与 provider 状态
  - `kore model switch deepseek-chat` 执行成功
  - `kore config show` 与 `kore config set --provider deepseek --base-url https://api.deepseek.com/v1` 执行成功
  - `kore ask "请只回复 pong"` 返回 `pong`
- 后续事项:
  - 评估是否补充流式输出
  - 评估是否在聊天模式加入更多斜杠命令
  - 评估自动拉起后端的生命周期管理策略

### 2026-06-05: LLM config and switching — DeepSeek 官方模型修正与 thinking 开关

- 对应 spec: `specs/llm-config-and-switching.md`
- 完成内容:
  - 将 DeepSeek 展示模型从旧别名 `deepseek-chat`、`deepseek-reasoner` 修正为官方当前主模型 `deepseek-v4-flash`、`deepseek-v4-pro`
  - 将默认模型从 `deepseek-chat` 修正为 `deepseek-v4-flash`
  - 新增 `deepseek_thinking_enabled` 配置项并写入 `.env`
  - 将 DeepSeek `thinking` 通过 OpenAI-compatible SDK 的 `extra_body` 透传到请求体
  - 扩展配置 API 和 CLI，使 `thinking` 可查看、可切换
- 关键决策:
  - 严格按官方当前模型展示，不再把兼容别名作为主模型暴露
  - `thinking` 第一版仅为 DeepSeek 提供，不提前抽象成跨 provider 通用布尔开关
  - `thinking` 作为独立开关控制，而不是继续用旧模型名区分思考与非思考
- 验证情况:
  - `GET /api/models/list` 返回 DeepSeek 模型为 `deepseek-v4-flash`、`deepseek-v4-pro`
  - `GET /api/config/models` 返回 `deepseek.thinking_enabled`
  - `kore config show` 正确展示 DeepSeek `thinking` 状态
  - `kore config set --provider deepseek --no-thinking` 后，真实请求返回 `pong`
  - `kore config set --provider deepseek --thinking` 后，真实请求返回 `pong`
- 后续事项:
  - 如需支持更多 provider 的 reasoning 能力，应设计更通用的能力抽象，而不是复用同名布尔开关

### 2026-06-06: CLI — 聊天模式补充 thinking 命令

- 对应 spec: `specs/cli.md`
- 完成内容:
  - 为聊天模式增加 `/thinking`
  - 为聊天模式增加 `/thinking on`
  - 为聊天模式增加 `/thinking off`
  - 在聊天欢迎区显示当前 DeepSeek thinking 状态
- 关键决策:
  - REPL 内的 thinking 切换直接复用既有配置 API，不新增专用端点
  - thinking 命令当前仅作用于 DeepSeek
- 验证情况:
  - 通过脚本化输入验证 `/thinking`、`/thinking on`、`/thinking off` 在聊天模式中可正常工作
- 后续事项:
  - 当前再次执行 `pip install -e backend` 暴露出 setuptools 自动发现 `kore`、`data`、`skills` 的打包问题，后续需要在 `pyproject.toml` 中显式约束包发现范围

### 2026-06-06: Agent runtime — 工具系统基础设施第一轮升级

- 对应 spec: `specs/agent-runtime.md`
- 完成内容:
  - 扩展 `ToolDefinition`，补充 `args_model`、`read_only`、`destructive`、`requires_confirmation`
  - 将工具参数定义统一切换到 `pydantic` 参数模型
  - 重写 `@tool` 装饰器，使其从 `args_model` 生成 JSON Schema
  - 改造 `ToolExecutor`，在执行前统一完成 JSON 解析与参数校验
  - 将 `ToolResult` 改为结构化返回：`ok`、`error_type`、`metadata`
  - 将内置工具 `get_current_time`、`calculate`、`echo` 迁移到 `pydantic` 参数模型
- 关键决策:
  - 本轮不再继续扩展基于函数签名的弱 schema 生成路径
  - 参数校验统一收敛到执行器，不再依赖工具函数内部自行兜底
  - 本轮只做基础设施，不处理 timeout、trace、确认交互
- 验证情况:
  - 已通过 `py_compile` 校验工具系统改动文件
  - 已验证工具 schema 可从 `pydantic` 模型正确生成
  - 已验证 `echo` 在参数缺失时返回结构化 `invalid_arguments`
- 后续事项:
  - 基于这套基础设施继续补充只读核心工具，如 `list_dir`、`read_file`、`search_text`

### 2026-06-06: Agent runtime — 工具执行控制层

- 对应 spec: `specs/agent-runtime.md`
- 完成内容:
  - 为 `ToolDefinition` 增加 `timeout_seconds` 与 `retry_count`
  - 将全局工具默认重试次数调整为 `0`
  - 为 `AgentConfig` 增加 `tool_timeout_seconds`
  - 在 `ToolExecutor` 中实现 `requires_confirmation` 拦截，返回 `confirmation_required`
  - 在 `ToolExecutor` 中实现工具级 timeout 控制，返回 `timeout`
  - 在 `ToolExecutor` 中实现工具级 retry 控制
  - 在 `ToolResult.metadata` 中补充 `attempt_count`、`duration_ms`、`timed_out`、`confirmation_required`
- 关键决策:
  - 默认不自动重试工具调用，避免副作用工具被重复执行
  - `requires_confirmation=True` 的工具在当前阶段只拦截，不做真实用户确认交互
  - 本轮只做执行控制与结果元数据，不做完整 trace 事件流
- 验证情况:
  - 已通过 `py_compile` 校验改动文件
  - 已验证 confirmation 工具会返回 `confirmation_required` 且不会执行
  - 已验证超时工具会返回 `timeout`
  - 已验证工具级 `retry_count=1` 可在第一次失败后重试成功
  - 已验证参数缺失仍返回结构化 `invalid_arguments`
- 后续事项:
  - 补充真正的只读文件工具后，可基于这些 metadata 接入 CLI 或 UI 展示

### 2026-06-06: Specs — 模块整理与索引建立

- 对应 spec: `specs/README.md`、`specs/agent-runtime.md`
- 完成内容:
  - 为 `specs/` 建立统一索引 `specs/README.md`
  - 将规格整理为 6 个核心模块：
    - `agent-runtime.md`
    - `cli.md`
    - `chat-ui.md`
    - `memory-system.md`
    - `knowledge-system.md`
    - `skills-system.md`
  - 将 `llm-config-and-switching.md` 的职责并回 `agent-runtime.md`
  - 在 `agent-runtime.md` 中补入模型配置、DeepSeek thinking 与文件工具第一层边界的归属说明
  - 更新 `spec-driven-coding` skill，要求先查索引、再写 spec、再更新索引
- 关键决策:
  - specs 按核心模块组织，不继续让配置或单一功能主题长期单列成零散 md
  - `specs/README.md` 作为规格入口和归属判断依据
- 验证情况:
  - 当前 `specs` 目录已从 3 个零散文件整理为索引 + 核心模块结构
- 后续事项:
  - 后续新增 `chat-ui.md`、`memory-system.md`、`knowledge-system.md`、`skills-system.md` 时应按索引规则落盘

### 2026-06-08: Specs — 按 Agent 组成部件二次细分

- 对应 spec: `specs/README.md`
- 完成内容:
  - 将 specs 从 6 个粗模块调整为 12 个更贴近 Agent 组成部件的模块
  - 新增并索引 `runtime-core.md`、`planner.md`、`react-loop.md`、`llm-system.md`、`tool-system.md`、`prompt-system.md`、`memory-system.md`、`knowledge-system.md`、`skills-system.md`、`channel-interfaces.md`、`api-surface.md`、`safety-and-policy.md`
  - 将 `agent-runtime.md` 调整为历史聚合和跳转文档，不再作为新任务首选归属
  - 将 CLI 第一版详细内容保留在 `cli.md`，但后续入口类任务统一归属 `channel-interfaces.md`
  - 将 API、LLM 配置、工具边界、安全策略等残留内容迁移到对应细分模块
- 关键决策:
  - specs 以 Agent 组成部件划分，而不是以单次任务或过粗系统块划分
  - `specs/README.md` 作为写入前的归属判断入口，模块 spec 更新后必须同步更新索引摘要
  - 旧文档先作为历史详细文档保留，避免重整过程中丢失上下文
- 验证情况:
  - 已确认 `specs/README.md` 存在并列出当前模块
  - 已核对 `agent-runtime.md`、`cli.md` 与新模块之间的归属关系
- 后续事项:
  - 继续沙箱开发时，应同步更新 `tool-system.md` 与 `safety-and-policy.md`

### 2026-06-08: Tool system — workspace_root 文件沙箱第一层

- 对应 spec: `specs/tool-system.md`、`specs/safety-and-policy.md`
- 完成内容:
  - 为配置新增 `KORE_WORKSPACE_ROOT`，并将当前项目路径写入 `backend/.env`
  - 新增 `FileSandbox`，统一完成用户路径解析、绝对路径规范化与 workspace 内外判断
  - 新增 workspace 外访问的 `ConfirmationRequiredError`
  - 在 `ToolExecutor` 中捕获 workspace 外访问并返回结构化 `confirmation_required`
  - 新增只读文件工具 `list_dir`、`read_file`、`search_text`
  - 将内置文件工具注册到 `AgentCore`
- 关键决策:
  - 第一层只处理文件系统空间边界，不做 denylist
  - workspace 外访问不直接执行，先返回 confirmation，不永久放宽边界
  - 文件工具第一版只做只读能力，写入工具等后续再接入同一套沙箱
- 验证情况:
  - 已通过 `python -m compileall backend/kore`
  - 已验证项目内路径通过 `FileSandbox`
  - 已验证 `/etc/hosts` 被识别为 workspace 外
  - 已验证 `read_file` 读取 workspace 内文件成功
  - 已验证 `read_file` 访问 workspace 外文件返回 `confirmation_required`
- 后续事项:
  - 实现 CLI / UI 收到 `confirmation_required` 后向用户确认，并在用户同意后只执行本次调用
  - 根据后续需要补充写入工具和更完整的输出裁剪策略

### 2026-06-08: Channel interfaces — REPL workspace 配置入口

- 对应 spec: `specs/api-surface.md`、`specs/channel-interfaces.md`、`specs/safety-and-policy.md`
- 完成内容:
  - 新增 `GET /api/config/workspace`，用于查看当前 workspace sandbox 配置
  - 新增 `PUT /api/config/workspace`，用于更新当前 workspace
  - 后端更新 workspace 时校验路径存在且为目录
  - 成功更新后写入 `KORE_WORKSPACE_ROOT`，更新当前 runtime config，并重建 `AgentCore`
  - 在 `kore` 聊天 REPL 中新增 `/workspace`
  - 在 `kore` 聊天 REPL 中新增 `/workspace <path>`
  - REPL 欢迎区新增当前 workspace 展示
- 关键决策:
  - workspace 第一版只做 REPL 内部命令，不新增外部 `kore workspace` 命令
  - CLI 不直接写 `.env`，所有 workspace 修改都通过后端 API
  - 修改 workspace 只影响后续工具调用，不重放历史调用
- 验证情况:
  - 已通过 `python -m compileall backend/kore`
  - 已通过 FastAPI TestClient 验证 workspace GET、有效 PUT、无效路径 400
  - 已通过脚本化 REPL 验证 `/workspace`
  - 已通过脚本化 REPL 验证 `/workspace /Users/yezibin/Project/Kore`
  - 已通过脚本化 REPL 验证无效路径错误展示
- 后续事项:
  - 继续实现工具调用 `confirmation_required` 后的用户确认与同次调用继续执行流程

### 2026-06-08: LLM system — 可用模型过滤与切换校验

- 对应 spec: `specs/llm-system.md`、`specs/api-surface.md`、`specs/channel-interfaces.md`
- 完成内容:
  - 为 provider 模型配置增加 `active` 标记
  - 模型列表只返回当前正式接入的 DeepSeek 模型
  - OpenAI、Qwen 等未正式接入验证的模型不再显示在 CLI 模型列表中
  - 模型切换前校验目标模型是否在可用模型列表中
  - `POST /api/models/switch` 对不可用模型返回 400
  - REPL `/model <name>` 捕获切换错误并展示错误面板，不退出聊天模式
- 关键决策:
  - 当前正式可用模型只保留 `deepseek-v4-flash` 与 `deepseek-v4-pro`
  - 未正式接入验证的 provider 可继续保留配置能力，但不进入可切换模型列表
- 验证情况:
  - 已通过 `python -m compileall backend/kore`
  - 已通过 FastAPI TestClient 验证 `/api/models/list` 只返回 DeepSeek 模型
  - 已验证切换 `deepseek-v4-pro` 成功
  - 已验证切换 `gpt-4o` 返回 400
  - 已通过脚本化 REPL 验证 `/model` 只展示 DeepSeek 模型
  - 已通过脚本化 REPL 验证 `/model gpt-4o` 展示错误并继续运行
- 后续事项:
  - 后续 OpenAI、Qwen 等 provider 完成正式接入和验证后，再将对应 provider 标为 active

### 2026-06-08: Channel interfaces — REPL 后端关闭命令

- 对应 spec: `specs/api-surface.md`、`specs/channel-interfaces.md`、`specs/runtime-core.md`
- 完成内容:
  - 新增 `POST /api/server/shutdown`
  - 新增 REPL 内部命令 `/shutdown`
  - 新增 REPL 内部命令 `/server stop` 作为 `/shutdown` 等价别名
  - `/shutdown` 成功请求后显示关闭提示并退出当前 REPL
  - 后端在返回成功响应后通过 SIGTERM 结束当前 uvicorn 进程
- 关键决策:
  - `/quit`、`/exit` 仍只退出聊天，不关闭后端
  - 关闭后端必须通过显式 `/shutdown` 或 `/server stop`
  - 第一版只做本地 CLI 使用，不扩展成远程服务器管理能力
- 验证情况:
  - 已通过 `python -m compileall backend/kore`
  - 已确认 `/api/server/shutdown` 路由注册成功
  - 已通过临时端口验证 `/shutdown` 能关闭后端，端口无残留
  - 已通过临时端口验证 `/server stop` 能关闭后端，端口无残留
  - 已关闭改动前遗留在 `9899` 上的旧后端进程，避免继续连到旧代码
- 后续事项:
  - 后续可考虑在 CLI 增加更明确的后端生命周期状态展示

---

## 参考资料

- [CowAgent](https://github.com/zhayujie/CowAgent) — 多渠道、技能系统、记忆架构参考
- [InDepth runtime-v2](https://github.com/YeZibn/InDepth) — Task Graph、正式状态机、可观察性参考
- [Tauri 2.0 文档](https://tauri.app/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
