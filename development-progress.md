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

## 参考资料

- [CowAgent](https://github.com/zhayujie/CowAgent) — 多渠道、技能系统、记忆架构参考
- [InDepth runtime-v2](https://github.com/YeZibn/InDepth) — Task Graph、正式状态机、可观察性参考
- [Tauri 2.0 文档](https://tauri.app/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
