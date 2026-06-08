# Specs Index

> Kore agent 规格索引。开始新任务前先查看本文件，确定应该更新哪个模块 spec；更新模块 spec 后，再同步回写本索引摘要。

---

## 1. runtime-core.md

范围：
- AgentCore
- RunContext / RunMode / RunStatus
- 总体运行时生命周期
- Direct / Plan 的总调度边界

写入场景：
- runtime 主循环骨架
- 执行状态模型
- 运行期上下文结构

当前概况：
- 已从旧聚合文档中拆出为独立归属，后续继续细化 runtime 状态模型

## 2. planner.md

范围：
- Plan mode
- step 拆解
- 依赖关系
- step 执行顺序与收敛策略

写入场景：
- 复杂任务规划
- 步骤级执行控制

当前概况：
- 尚未实质实现

## 3. react-loop.md

范围：
- Direct 模式 ReAct 循环
- tool call 回填
- 终止条件
- 最大步数与最终回复生成

写入场景：
- ReAct 行为调整
- 观察-执行循环设计

当前概况：
- 已有最小实现，后续需要继续细化 tool call 回填与终止条件

## 4. llm-system.md

范围：
- LLMProvider 抽象
- provider factory
- 模型路由
- reasoning / thinking 参数映射
- provider 配置

写入场景：
- 模型接入
- provider 配置
- reasoning / thinking 能力映射

当前概况：
- 已具备 OpenAI-compatible 抽象、DeepSeek 官方模型展示修正与 thinking 配置

## 5. tool-system.md

范围：
- ToolDefinition
- ToolRegistry
- ToolExecutor
- 参数模型
- timeout / retry / confirmation
- 文件工具第一层边界

写入场景：
- 工具定义
- 工具安全边界
- 工具执行控制

当前概况：
- 已具备基础设施、执行控制与 workspace_root 文件沙箱，下一步实现用户确认后的继续执行流程

## 6. prompt-system.md

范围：
- system prompt
- PromptBuilder
- memory / knowledge 注入位置
- prompt 分层策略

写入场景：
- 提示词管理
- 上下文拼装

当前概况：
- 已有最小 PromptBuilder，仍待拆分整理

## 7. memory-system.md

范围：
- 对话上下文管理
- 日记忆
- 核心记忆
- 检索与蒸馏

写入场景：
- 记忆层数据模型
- 长短期记忆协作

当前概况：
- 尚未开始实质实现

## 8. knowledge-system.md

范围：
- Markdown Wiki
- 文档导入
- 检索
- 知识图谱

写入场景：
- 知识导入与索引
- 知识图谱与检索设计

当前概况：
- 尚未开始实质实现

## 9. skills-system.md

范围：
- skill manifest
- skill loader
- skill 执行
- skill 安装与 hub

写入场景：
- skill 生命周期
- skill 注册与分发

当前概况：
- 尚未开始实质实现

## 10. channel-interfaces.md

范围：
- CLI
- Chat UI
- Tauri / Web 等前端入口
- 各入口如何接 runtime

写入场景：
- 终端入口
- UI 接入层
- 多渠道接入策略

当前概况：
- CLI 已有第一版实现
- REPL 内部 workspace 命令已实现
- Chat UI 仍未实质开始

## 11. api-surface.md

范围：
- REST API
- SSE / 事件流
- chat / models / config / status 等接口

写入场景：
- API 协议定义
- 接口返回结构
- 客户端与后端边界

当前概况：
- 已有最小 REST API，workspace config API 已实现

## 12. safety-and-policy.md

范围：
- 工具沙箱
- 权限边界
- confirmation
- 输出裁剪
- 安全策略

写入场景：
- 风险控制
- 沙箱规则
- 用户确认策略

当前概况：
- 第一层文件空间边界已完成基础实现，workspace 修改入口已接入 REPL，尚未接入 CLI / UI 二次确认交互

## 历史 / 详细文档

- `agent-runtime.md`：历史聚合文档，只作为迁移跳转与历史上下文，不再作为新任务首选归属。
- `cli.md`：CLI 第一版详细记录，后续 CLI 新任务优先写入 `channel-interfaces.md`。

## 使用规则

1. 开始 substantial task 前，先查看本索引并确定归属模块。
2. 优先写入已有模块 spec，不轻易新增新的 spec 文件。
3. 如果模块边界变化，先更新本索引，再更新对应模块 spec。
4. 更新模块 spec 后，必须同步回写本索引中的“当前概况”。
