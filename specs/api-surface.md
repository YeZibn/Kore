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

## 当前约束

- Chat API 第一版返回完整回复，不做 SSE 流式
- API key 返回时必须脱敏
- 模型列表只展示当前明确支持 API 调用的模型
- `thinking` 属于 provider 配置项，由 config API 暴露
- `workspace_root` 属于安全/运行配置，不归入 LLM provider 配置
- 更新 workspace 时必须校验路径存在且为目录
- 更新 workspace 后必须写回 `.env`，并让当前运行中的 AgentCore 立即使用新的文件沙箱
- Workspace Config API 已实现

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

## 待确认事项

- 后续是否为 ReAct 步骤、工具调用和确认请求补充 SSE / 事件流
- 后续是否将 confirmation 设计成专用 API 协议
