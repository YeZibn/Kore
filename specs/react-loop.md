# ReAct Loop

> Direct 模式的 Reason / Act / Observe 循环。

---

## 当前状态

- 已有最小实现，待从旧 `agent-runtime.md` 中拆分归位

## 实时 Trace 事件

第一版 ReAct 实时透明化输出结构化事件，不输出模型隐藏思维链。

事件类型：

- `run_started`
- `llm_step_started`
- `llm_step_completed`
- `llm_reasoning`
- `tool_call_started`
- `tool_call_completed`
- `tool_confirmation_required`
- `run_completed`
- `run_failed`

事件语义：

- `llm_step_started` 展示当前 step、模型和阶段
- `llm_reasoning` 展示 provider 返回的可见 reasoning 摘要、长度和 provider 名称
- `tool_call_started` 展示工具名和参数摘要
- `tool_call_completed` 展示工具名、成功/失败、耗时、错误类型和输出摘要
- `tool_confirmation_required` 展示请求路径、workspace 和确认原因
- `run_completed` 展示最终回答摘要和 token / tool call 统计

约束：

- trace 展示可公开执行轨迹，不展示模型私有 chain-of-thought
- provider 返回可展示 thinking/reasoning 字段时，通过 `llm_reasoning` 独立事件接入
- 第一版不做长期 trace 存储，只服务实时 CLI 输出

当前实现状态：

- `AgentCore.run_with_events()` 已支持向外部 sink 发送结构化 trace 事件
- Direct ReAct loop 已在 LLM step 前后、工具调用前后、确认请求、run 成功/失败时发出事件
- 工具事件第一版由 AgentCore 在调用 ToolExecutor 前后发出，不做工具内部更细粒度 trace
- provider reasoning 事件已接入，DeepSeek 第一版读取 `reasoning_content`
