# LLM Config And Switching

> LLM 配置来源、模型切换、配置持久化与连通性验证

---

## 背景

当前 Kore 已具备 LLM provider 配置、运行时模型切换和聊天接口的基础骨架，但配置来源、运行时状态与持久化行为尚未完全对齐，实际可用性也未完成验证。

当前已知情况：

- `KoreConfig` 通过 `.env` 读取 provider API Key、base URL 和默认模型配置
- `ModelState.current_model` 作为运行时当前模型状态保存在 `app.state`
- DeepSeek 当前通过 `backend/.env` 提供本地配置

## 当前目标

完成 LLM 配置与模型切换的最小闭环，确保 Kore 能够：

1. 明确当前 LLM 配置从哪里读取
2. 在运行时正确切换当前模型
3. 通过配置接口更新 provider 配置时，同时写回 `backend/.env`
4. 在聊天接口中返回真实的运行时当前模型
5. 为 DeepSeek 提供基于 `.env` 的可执行验证路径

## 当前共识 / 开发方向

本模块按以下方向实现：

- 新建模块 spec 文件 `specs/llm-config-and-switching.md`
- 保留运行时 `ModelState.current_model` 作为当前模型真值
- 将 provider 配置更新扩展为“更新内存配置 + 写回 `backend/.env`”
- `.env` 作为本地持久化配置来源，不引入额外数据库或配置文件
- 聊天接口返回值中的 `model` 字段改为反映真实运行时模型
- 首个真实联通测试目标为 DeepSeek，并要求通过 `.env` 提供配置
- 为匹配现有 `agent` conda 环境，本次将后端 Python 版本要求从 `>=3.12` 调整为兼容 `3.11`

## 设计方案

### 配置来源

- 启动时从 `.env` 读取默认 provider 配置和默认模型
- 运行期间从 `app.state.config` 和 `app.state.model_state` 读取当前生效状态
- 当通过配置接口更新 provider 配置时：
  - 先更新运行时内存对象
  - 再将结果写回 `backend/.env`
  - 然后重建 `LLMFactory`

### 模型切换

- `POST /api/models/switch` 继续只负责切换 `ModelState.current_model`
- 不要求本次将当前模型切换结果写回 `.env`
- `POST /api/chat/send` 必须返回本次请求实际使用的运行时模型

### DeepSeek 验证

- 使用 `backend/.env` 提供 `KORE_LLM__DEEPSEEK_API_KEY`
- 默认模型可使用 `deepseek-chat`
- 验证链路至少包括：
  - 服务启动后可读取 DeepSeek 配置
  - `GET /api/models/providers` 能反映配置状态
  - `POST /api/models/switch` 能更新当前模型
  - `POST /api/chat/send` 在 DeepSeek 配置有效时返回成功响应

## 关键接口 / 数据结构

- `KoreConfig.llm`
- `app.state.config`
- `app.state.model_state.current_model`
- `PUT /api/config/models`
- `POST /api/models/switch`
- `POST /api/chat/send`

## 约束与取舍

- 本次仅处理本地 `.env` 持久化，不引入更复杂的配置管理方案
- 本次以 provider 配置持久化为主，不要求将运行时当前模型切换结果回写 `.env`
- 本次为了优先完成真实联调，接受将项目后端运行时约束下调到 Python 3.11
- 若缺少真实 DeepSeek API Key，可以先完成代码闭环与本地非联网验证，再等待用户提供密钥执行真实调用

## 待确认事项

- 暂无

## 实现状态

- 已新增模块 spec 并明确本次范围
- 已将配置文件路径显式固定为 `backend/.env`
- 已实现 provider 配置更新时同步写回 `backend/.env`
- 已修正 `POST /api/chat/send` 返回运行时当前模型，而不是默认配置模型
- 已完成改动文件的 Python 语法校验
- 已将后端 Python 版本约束调整为兼容 `agent` conda 环境的 Python 3.11
- 已验证 `GET /api/models/providers` 正确显示 DeepSeek `configured: true`
- 已验证 `POST /api/models/switch` 可将当前模型切换为 `gpt-4o`
- 已验证在切回 `deepseek-chat` 后，`POST /api/chat/send` 返回 `200`，回复 `pong`，且返回模型为 `deepseek-chat`
