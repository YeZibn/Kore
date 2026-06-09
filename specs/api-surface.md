# API Surface

> REST API、SSE / 事件流与前后端接口边界。

---

## 当前状态

- 已有最小 REST API

## 端点总览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/status` | 系统状态 |
| POST | `/api/chat/send` | 发送消息给 Agent |
| GET | `/api/models/list` | 列出可用模型 |
| POST | `/api/models/switch` | 切换当前模型 |
| GET | `/api/models/providers` | 列出支持的 Provider |
| GET | `/api/config/models` | 获取当前模型配置 |
| PUT | `/api/config/models` | 更新模型配置 |
| GET | `/api/config/workspace` | 获取当前 workspace 配置 |
| PUT | `/api/config/workspace` | 更新当前 workspace 配置 |
| POST | `/api/server/shutdown` | 请求当前后端进程优雅关闭 |
| POST | `/api/chat/stream` | SSE 实时返回 Agent 执行 trace 与最终回复 |

## 当前约束

- Chat API 第一版返回完整回复，不做 SSE 流式
- Chat Stream API 第一版通过 SSE 返回结构化 trace 事件与最终回复
- API key 返回时必须脱敏
- 模型列表只展示当前明确支持 API 调用的模型
- 模型切换接口必须拒绝不存在或未正式接入的模型，并返回 4xx 错误
- 模型切换接口成功后必须更新 runtime config 并写回 `.env`
- `thinking` 属于 provider 配置项，由 config API 暴露
- `workspace_root` 属于安全/运行配置，不归入 LLM provider 配置
- 更新 workspace 时必须校验路径存在且为目录
- 更新 workspace 后必须写回 `.env`，并让当前运行中的 AgentCore 立即使用新的文件沙箱
- Workspace Config API 已实现
- Shutdown API 用于关闭 CLI 自动拉起后残留的本地后端进程
- Shutdown API 第一版只面向本地 CLI 使用，不做远程管理能力
- Shutdown API 已实现

## Workspace Config API

```text
GET /api/config/workspace
Response: {
  "workspace_root": "/Users/yezibin/Project/Kore",
  "exists": true,
  "is_directory": true
}

PUT /api/config/workspace
Request:  { "workspace_root": "/Users/yezibin/Project/Kore" }
Response: {
  "workspace_root": "/Users/yezibin/Project/Kore",
  "exists": true,
  "is_directory": true
}
```

更新语义：

- 后端接收路径后执行 `expanduser().resolve()`
- 路径不存在或不是目录时返回 4xx 错误
- 成功后写入 `KORE_WORKSPACE_ROOT`
- 成功后更新当前 runtime config
- 成功后重建 `AgentCore`，确保已注册文件工具绑定新的 `workspace_root`

## Server Shutdown API

```text
POST /api/server/shutdown
Response: { "success": true, "message": "Server shutdown requested." }
```

关闭语义：

- API 返回成功响应后再触发进程退出，避免 CLI 收不到响应
- 第一版使用 SIGTERM 关闭当前 uvicorn 进程
- 不把 `/quit` 或 `/exit` 等同于关闭后端，避免用户只是退出聊天时误停服务

## Chat Stream API

```text
POST /api/chat/stream
Request:  { "message": "用户消息", "session_id": "" }
SSE events:
  run_started
  llm_step_started
  llm_step_completed
  tool_call_started
  tool_call_completed
  tool_confirmation_required
  run_completed
  run_failed
```

约束：

- SSE event `data` 使用 JSON
- 最终回答通过 `run_completed.reply` 返回
- 不通过该接口输出模型隐藏 chain-of-thought
- CLI 负责将事件渲染为 Rich 面板/表格

## 待确认事项

- 后续是否为 trace 增加持久化、请求取消和更细粒度工具内部事件
- 后续是否将 confirmation 设计成专用 API 协议
