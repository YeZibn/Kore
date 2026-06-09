# LLM System

> Provider 抽象、模型路由、thinking / reasoning 参数映射与 provider 配置。

---

## 当前状态

- 已具备 OpenAI-compatible 抽象和 DeepSeek thinking 配置

## 当前共识 / 开发方向

- DeepSeek 展示模型严格使用当前官方提供且有 API 的模型：`deepseek-v4-flash`、`deepseek-v4-pro`
- `deepseek-chat`、`deepseek-reasoner` 仅作为历史兼容别名，不作为主模型展示
- 模型列表只展示当前已正式接入并验证的 provider 模型
- OpenAI、Qwen 等未完成正式接入验证前，不在模型列表中展示
- 模型切换必须校验目标模型是否在可用模型列表中，不允许切到任意字符串
- 模型切换成功后必须持久化到 `KORE_AGENT__CHAT_MODEL`
- 后端重启时应从 `.env` 恢复上次选择的 chat model
- DeepSeek 的“思考 / 非思考”通过独立 `thinking` 开关控制，不通过旧模型名区分
- `thinking` 当前通过 provider 配置接入，并在调用层通过 `extra_body` 透传
- 其他 provider 的 reasoning / thinking 能力后续应做能力映射，不直接假设所有主流模型都支持同一参数

## 配置管理

配置层级：

```text
KoreConfig
  ├── AgentConfig
  ├── LLMProviderConfig
  ├── ServerConfig
  ├── system_prompt
  ├── data_dir
  └── skills_dir
```

加载方式：

- 默认值
- `.env` 覆盖
- 环境变量覆盖，使用 `KORE_` 前缀

## 实现状态

- 已支持 DeepSeek API key、base URL 与 thinking 配置读写
- 已支持 CLI 与 API 查看、切换 DeepSeek thinking
- 已完成 DeepSeek 模型展示修正
- 已完成模型列表过滤与无效模型切换错误提示
- 已实现模型切换持久化，重启后会从 `.env` 恢复上次选择
