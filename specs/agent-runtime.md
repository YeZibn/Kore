# Agent Runtime

> 历史聚合文档。运行时内容正在拆分到更细的模块 spec 中，优先查看 `specs/README.md`。

---
## 模块归属

- 运行时主循环与状态模型：`runtime-core.md`
- ReAct 行为：`react-loop.md`
- LLM 与 provider：`llm-system.md`
- 工具系统与执行控制：`tool-system.md`
- PromptBuilder 与 prompt 结构：`prompt-system.md`
- API 与接口返回：`api-surface.md`
- 工具沙箱与安全策略：`safety-and-policy.md`
- CLI 与前端入口：`channel-interfaces.md`

## 当前用途

- 保留历史上下文，避免重整期间丢失已有设计
- 新任务不要继续优先写入本文件
- 需要继续整理时，应把这里的内容逐步迁移到上面的细分模块

---

## 已迁移内容

- API 层迁移到 `api-surface.md`
- LLM provider、DeepSeek 模型与 thinking 配置迁移到 `llm-system.md`
- 文件工具边界与执行控制迁移到 `tool-system.md`
- 沙箱、confirmation 与权限策略迁移到 `safety-and-policy.md`
- CLI 入口归属迁移到 `channel-interfaces.md`

## 待实现

- [x] 模型切换与完整 API (2026-06-04)
- [ ] Plan 模式（Router + 步骤规划 + 逐步执行）
- [ ] Claude Provider（后续独立演进）
- [ ] 流式输出 (SSE)
- [ ] 更多内置工具（file_ops, web_search, web_fetch, terminal）
- [ ] MCP 协议集成
- [ ] 会话管理（多轮对话历史）
