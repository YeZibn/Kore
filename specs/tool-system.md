# Tool System

> ToolDefinition、ToolRegistry、ToolExecutor、执行控制与工具边界。

---

## 当前状态

- 已具备基础设施、执行控制与第一层文件空间边界实现

## 当前共识 / 开发方向

- 工具参数模型只保留 `pydantic` 参数模型，不继续维护弱 schema 路径
- `ToolExecutor` 负责统一参数解析、校验、确认拦截、超时和重试
- 默认不自动重试工具调用，避免副作用工具被重复执行
- `requires_confirmation=True` 的工具在执行前返回结构化 `confirmation_required`
- 第一层文件工具边界先服务只读文件工具，如 `list_dir`、`read_file`、`search_text`
- 工具接受相对路径和绝对路径，但内部必须统一做规范化路径解析
- 文件工具通过 `FileSandbox` 基于 `workspace_root` 解析路径

## 文件工具第一层边界

目标：

- 第一层边界只处理文件系统空间范围
- 默认允许空间由 `workspace_root` 决定
- 用户应能在启动或配置阶段明确项目位置，作为 `workspace_root`
- workspace 内路径可直接访问
- workspace 外路径不直接拒绝，而是返回结构化 `confirmation_required`
- 用户同意后，本次调用可以访问 workspace 外路径，但不永久放宽边界
- 第一层暂不做 denylist

## 关键接口 / 数据结构

- `ToolDefinition.args_model`
- `ToolDefinition.read_only`
- `ToolDefinition.destructive`
- `ToolDefinition.requires_confirmation`
- `ToolDefinition.timeout_seconds`
- `ToolDefinition.retry_count`
- `ToolResult.ok`
- `ToolResult.error_type`
- `ToolResult.metadata`
- `FileSandbox`
- `ConfirmationRequiredError`

## 实现状态

- 已实现 `pydantic` 参数模型驱动的工具定义
- 已实现结构化 `ToolResult`
- 已实现 confirmation 拦截、timeout 和 retry
- 已实现基于 `workspace_root` 的路径沙箱基础设施
- 已实现 `list_dir`、`read_file`、`search_text` 只读文件工具
- 已将 workspace 外路径访问接入 `ToolExecutor` 的 `confirmation_required` 返回
- 待实现用户确认后的同一次调用继续执行流程
