# Agent Runtime

> Agent 执行框架：推理循环、LLM 抽象层、工具系统、Prompt 管理、API 层

---

## 1. 执行模型

### 双模式自适应

```
用户消息 → Router → Direct 模式 (简单请求)
                  → Plan 模式   (复杂任务)
```

- **Direct 模式**：纯 ReAct 循环，适用于大多数请求
- **Plan 模式**：先规划步骤列表，再逐步执行（待实现）

当前已实现 Direct 模式。

### Direct 模式 — ReAct 循环

```
用户消息
  → 构建 messages (system prompt + user message)
  → 获取 tools schema
  → ReAct 循环 (最多 max_direct_steps 步):
      LLM.chat(messages, tools)
      → if tool_calls: 执行工具 → 追加结果到 messages → 继续
      → if 无 tool_calls: 返回 content 作为最终回复
  → 达到最大步数: 强制让 LLM 生成最终回复
```

### 状态模型

```python
class RunMode:  DIRECT | PLAN
class RunStatus: RUNNING | COMPLETED | FAILED
```

---

## 2. LLM 抽象层

### 架构

```
LLMProvider (ABC)
  ├── OpenAIProvider    — OpenAI / DeepSeek / Qwen (OpenAI 兼容 API)
  ├── ClaudeProvider    — Anthropic Claude (待实现)
  └── ...

LLMFactory
  └── create(model_name) → LLMProvider
```

### 核心接口

```python
class LLMProvider(ABC):
    async def chat(self, messages, *, tools=None, model="") -> ChatResponse: ...
    async def chat_stream(self, messages, ...) -> AsyncIterator[str]: ...  # 可选
    async def embed(self, texts) -> list[list[float]]: ...                # 可选
```

### 数据类

- `ChatResponse`: content, tool_calls, usage, model, finish_reason
- `ToolCall`: id, name, arguments (JSON string)
- `TokenUsage`: prompt_tokens, completion_tokens, total_tokens

### 模型路由

| 模型关键词 | Provider | Base URL |
|-----------|----------|----------|
| deepseek | OpenAIProvider | api.deepseek.com/v1 |
| qwen | OpenAIProvider | dashscope.aliyuncs.com |
| gpt/o1/o3/o4 | OpenAIProvider | api.openai.com/v1 |
| 其他 | OpenAIProvider | 默认 OpenAI base_url |

---

## 3. 工具系统

### 架构

```
ToolRegistry (注册中心)
  ├── 注册 ToolDefinition
  ├── get_schemas() → OpenAI function calling 格式
  └── get(name) → ToolDefinition

ToolExecutor (执行器)
  └── execute(tool_calls) → list[ToolResult]
      └── 查找定义 → 解析参数 → 执行(含重试) → 返回结果

@tool 装饰器 (简化注册)
  └── 自动从函数签名生成 JSON Schema
```

### 内置工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `get_current_time` | 获取当前日期时间 | 无 |
| `calculate` | 计算数学表达式 | expression: str |
| `echo` | 回显文本（测试用） | text: str |

### 工具注册流程

```python
@tool(name="my_tool", description="描述")
async def my_tool(param: str) -> str:
    return "result"

# 注册
definition = get_definition(my_tool)
registry.register(definition)
```

---

## 4. Prompt 管理

### PromptBuilder

```python
builder = PromptBuilder(base_prompt)
prompt = builder.build(
    memory_context=["记忆片段1", "记忆片段2"],
    knowledge_context=["知识片段1"],
)
```

当前 system prompt 定义在 `prompting/templates.py`，包含：
- 能力说明
- 工具使用原则
- 回复风格要求

---

## 5. 模型切换

### 全局状态

在 `app.state` 上维护运行时模型状态，AgentCore 每次调用时读取：

```python
# app.state 上的模型状态
class ModelState:
    current_model: str          # 当前对话模型，如 "deepseek-chat"
    providers: dict[str, dict]  # 已配置的 provider 信息
```

### 切换流程

```
POST /api/models/switch {"model": "gpt-4o"}
  → app.state.model_state.current_model = "gpt-4o"
  → 后续 AgentCore.run() 使用新模型
```

AgentCore 在 `_run_direct` 中从 `app.state` 读取当前模型：

```python
model = app.state.model_state.current_model  # 而非 config.agent.chat_model
llm = self.llm_factory.create(model)
response = await llm.chat(messages, tools=tools, model=model)
```

### Provider 列表

系统支持的 provider 列表为静态配置：

| Provider | 关键词匹配 | Base URL |
|----------|-----------|----------|
| DeepSeek | deepseek | api.deepseek.com/v1 |
| OpenAI | gpt/o1/o3/o4 | api.openai.com/v1 |
| Qwen | qwen | dashscope.aliyuncs.com |

---

## 6. API 层

### 端点总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/status` | 系统状态 |
| POST | `/api/chat/send` | 发送消息给 Agent |
| GET | `/api/models/list` | 列出可用模型 |
| POST | `/api/models/switch` | 切换当前模型 |
| GET | `/api/models/providers` | 列出支持的 Provider |
| GET | `/api/config/models` | 获取当前模型配置（API Key 状态） |
| PUT | `/api/config/models` | 更新模型配置（API Key、Base URL） |

### Chat API

```
POST /api/chat/send
Request:  { "message": "用户消息", "session_id": "" }
Response: { "reply": "Agent回复", "model": "deepseek-chat" }
```

### 模型管理 API

```
GET /api/models/list
Response: {
  "current_model": "deepseek-chat",
  "models": [
    {"name": "deepseek-chat", "provider": "DeepSeek"},
    {"name": "gpt-4o", "provider": "OpenAI"},
    {"name": "qwen-plus", "provider": "Qwen"}
  ]
}

POST /api/models/switch
Request:  { "model": "gpt-4o" }
Response: { "success": true, "current_model": "gpt-4o" }

GET /api/models/providers
Response: {
  "providers": [
    {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "configured": true},
    {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "configured": false},
    {"name": "Qwen", "base_url": "...", "configured": false}
  ]
}

GET /api/config/models
Response: {
  "providers": {
    "deepseek": {"api_key": "sk-***masked", "base_url": "..."},
    "openai": {"api_key": "", "base_url": "..."},
    "qwen": {"api_key": "", "base_url": "..."}
  }
}

PUT /api/config/models
Request:  { "provider": "deepseek", "api_key": "sk-xxx", "base_url": "https://..." }
Response: { "success": true }
```

---

## 7. 配置管理

### 层级

```
KoreConfig (根配置)
  ├── AgentConfig      — 模型选择、步数限制、token预算
  ├── LLMProviderConfig — API keys、base URLs
  ├── ServerConfig     — host、port、CORS
  ├── system_prompt    — 系统人设
  ├── data_dir         — 数据目录 (default: data/)
  └── skills_dir       — 技能目录 (default: skills/)
```

### 加载方式

- 默认值 → `.env` 文件覆盖 → 环境变量覆盖（`KORE_` 前缀）

---

## 8. 待实现

- [x] 模型切换与完整 API (2026-06-04)
- [ ] Plan 模式（Router + 步骤规划 + 逐步执行）
- [ ] Claude Provider（后续独立演进）
- [ ] 流式输出 (SSE)
- [ ] 更多内置工具（file_ops, web_search, web_fetch, terminal）
- [ ] MCP 协议集成
- [ ] 会话管理（多轮对话历史）
