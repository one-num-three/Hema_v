---
name: new-api-proxy-model-discovery
category: mlops
description: 探测 New-API / One API 中转站（如 ctiao.com）上的可用模型列表、供应商、分组和价格信息。当 `/v1/models` 返回空列表时使用。
tags:
  - new-api
  - one-api
  - proxy
  - model-discovery
  - api-probe
---

# New-API 中转站模型探测

## 适用场景

用户给了一个 API 中转站地址（如 `https://example.com/v1`），想要知道该站有哪些可用模型。但 `/v1/models` 接口返回空列表（`data: []`）。

## 识别中转站类型

根据错误信息可判断是否是 **New-API** 框架：

```
{"error":{"code":"model_not_found","message":"No available channel for model xxx under group default (distributor)","type":"new_api_error"}}
```

特征：`code: "model_not_found"`、`type: "new_api_error"`、错误消息中提到 `under group xxx (distributor)`。

## 探测步骤

### 1. 获取完整模型、供应商、分组信息

New-API 内部有一个 `/api/pricing` 端点，无需管理员权限即可访问（仅需正常的 API key 或无需认证）：

```bash
curl -s https://example.com/api/pricing \
  -H "Authorization: Bearer sk-your-key-here"
```

返回内容包含：
- `data[]` — 模型列表（模型名、供应商ID、倍率、价格、可用分组、支持端点类型）
- `vendors[]` — 供应商列表（ID、名称、图标）
- `usable_group{}` — 可用分组名称中文说明
- `group_ratio{}` — 分组倍率
- `supported_endpoint{}` — 支持的端点路径
- `auto_groups[]` — 自动分组

### 2. 用 Python 解析结果

```python
import json

# data 来自 curl 输出
for m in data['data']:
    print(f"{m['model_name']} | vendor={m['vendor_id']} | "
          f"input_ratio={m['model_ratio']}x | "
          f"output_ratio={m.get('completion_ratio', m['model_ratio'])}x | "
          f"groups={m['enable_groups']}")

print("Vendors:", {v['id']: v['name'] for v in data['vendors']})
print("Groups:", data['usable_group'])
print("Ratios:", data['group_ratio'])
```

### 3. 验证模型是否可用（可选）

用对应端点的模型名测试一次调用：

```bash
# OpenAI 兼容
curl -s https://example.com/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"model-name","messages":[{"role":"user","content":"hi"}],"max_tokens":1}'
```

### 4. 如果仍想列出 JS 硬编码的参考模型列表

网站的 JS bundle 里可能嵌有模型参考名。下载主 JS 文件搜索模型名模式：

```bash
# 找出页面引用的 JS 文件
curl -s https://example.com | grep -oP 'src="/assets/[^"]*\.js"'

# 搜索模型名
curl -s https://example.com/assets/index-xxx.js | \
  grep -oP '"gpt-[^"]*"|"claude-[^"]*"|"deepseek-[^"]*"|"gemini-[^"]*"|"qwen-[^"]*"|"o[0-9][^"]*"' | sort -u
```

## 配置为 Hermes Custom Provider

发现可用模型后，可以将其添加到 Hermes 的 `~/.hermes/config.yaml` 中作为自定义提供者：

### 基本配置

```yaml
model:
  default: model-name-here         # 默认使用的模型
  provider: custom:my-provider     # 对应下方 custom_providers 的 name

custom_providers:
  - name: my-provider              # 任意名称，provider 字段引用
    base_url: https://example.com/v1
    api_key: sk-your-key-here      # API 密钥
    api_mode: chat_completions     # 固定为 OpenAI 兼容模式
    models:                        # 可选，文档用途
      - model-1
      - model-2
```

### API 模式说明

| 端点类型 | api_mode | 说明 |
|---------|----------|------|
| OpenAI 兼容 | `chat_completions` | 用 `/v1/chat/completions` |
| Anthropic 原生 | `anthropic_messages` | 用 `/v1/messages` |
| OpenAI Responses | `codex_responses` | 用 `/v1/responses` |

New-API 中转站的 Claude 模型通常走 OpenAI 兼容格式（`api_mode: chat_completions`），即使底层是 Anthropic。可以通过 `supported_endpoint_types` 字段查看模型支持哪些模式。

### New-API 专题：Claude 模型通过 OpenAI 接口

ctiao.com 这类 New-API 中转站支持将 Claude 模型通过 OpenAI 兼容接口调用（格式仍是 chat/completions，New-API 内部转换）。验证方法：

```bash
curl -s https://example.com/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

返回格式仍是 OpenAI 风格，但 `usage` 中会包含 Anthropic 特有的缓存字段（`claude_cache_creation_5_m_tokens` 等）。

### API Key 安全性

- API key 直接写在 `config.yaml` 的 `custom_providers[].api_key` 字段中
- 也可通过 `OPENAI_API_KEY` 环境变量设置（优先级：explicit > config > env）
- 密钥明文存储在配置文件中，注意文件权限

## 常见坑

1. **模型列表为空 ≠ 没模型** — 可能是 New-API 配置了隐藏列表或分组隔离。
2. **`/v1/models` 返回空但 `/api/pricing` 有数据** — 说明管理员设置了分组权限，你的 key 所在分组可能无权使用这些模型。
3. **调用返回 `model_not_found under group default`** — 你的 key 在 `default` 分组，但模型配置在别组（如 `claude-default`），需要管理员把 key 分配到对应分组。
4. **`/api/pricing` 也返回空** — 可能被反代拦截了路径，或非 New-API 框架。
5. **永远不要直接用 `/v1/models` 的结果做结论** — 它只返回当前 key 在当前分组下的可见模型。

## 扩展探测

如果 `/api/pricing` 也没数据，可以尝试 New-API 的其他内部端点：

| 端点 | 说明 |
|------|------|
| `/api/models` | 管理员用的模型列表 |
| `/api/user/models` | 用户可见模型（常需更高权限） |
| `/api/user/self/groups` | 当前用户分组信息 |
