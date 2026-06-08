# Safety And Policy

> 工具沙箱、确认策略、输出裁剪与安全边界。

---

## 当前状态

- 第一层文件空间边界已完成基础实现

## 当前共识 / 开发方向

- 第一层安全边界先聚焦文件系统空间，不做命令 denylist
- 默认允许范围由用户确认的 `workspace_root` 决定
- workspace 内访问允许直接执行
- workspace 外访问需要向用户确认
- 用户确认只作用于当前工具调用，不自动变成永久白名单
- 路径判断必须基于规范化后的绝对路径，避免 `..`、符号链接等绕过
- 安全策略返回结构化结果，让 CLI / UI 后续可以展示确认提示
- 当前项目的默认 `workspace_root` 已写入 `backend/.env`
- 用户可通过 REPL 内部命令 `/workspace <path>` 修改当前 workspace
- workspace 修改必须通过后端 API 校验，不能由 CLI 直接写 `.env`

## 与工具系统的分工

- `tool-system.md` 负责执行机制：参数校验、路径解析接入点、结果结构、工具 metadata
- `safety-and-policy.md` 负责策略语义：默认边界、何时确认、确认作用范围、哪些风险暂不处理

## 暂不处理

- denylist
- 终端命令沙箱
- 网络访问策略
- 长期授权记忆
- trace 与审计日志

## 实现状态

- 已新增 `FileSandbox`
- 已新增 workspace 外访问的 `ConfirmationRequiredError`
- 已在工具执行器中把 workspace 外访问转换为 `ToolResult.error_type = "confirmation_required"`
- 已接入只读文件工具
- 已实现 workspace config API 与 REPL 内部 `/workspace` 命令
- 尚未实现 CLI / UI 的二次确认交互
