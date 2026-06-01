---
name: grsai-api
description: Grsai 图片生成 API — 通过 grsaiapi.com 调用 gpt-image-2/gpt-image-2-vip 模型生成图片，支持同步(json/stream)和异步轮询模式
category: mlops
---

# Grsai API — 图片生成

Grsai 提供图片生成 API，基于 OpenAI 兼容接口。支持 gpt-image-2 和 gpt-image-2-vip 模型。

## 基础信息

| 项目 | 值 |
|------|-----|
| 全球节点 | `https://grsaiapi.com` |
| 国内节点 | `https://grsai.dakka.com.cn` |
| API Key 获取 | https://grsai.ai/zh/dashboard/api-keys |
| 认证方式 | `Authorization: Bearer <API_KEY>` |

## 可用模型

| 模型 | 说明 |
|------|------|
| `gpt-image-2` | 基础图片生成模型 |
| `gpt-image-2-vip` | 高清图片生成，支持 2K/4K |

## 接口一：生成请求

```
POST https://{base_url}/v1/api/generate
```

**Headers:**
```
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

**请求体:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `gpt-image-2` 或 `gpt-image-2-vip` |
| `prompt` | string | 是 | 提示词 |
| `images` | array[string] | 否 | 参考图，支持 base64 和 URL |
| `aspectRatio` | string | 否 | 像素尺寸，如 `1024x1024` |
| `replyType` | string | 是 | `json` / `stream` / `async` |

**replyType 说明:**
- `json` — 同步返回完整结果
- `stream` — 流式返回
- `async` — 异步轮询，返回 task_id，需要调用查询接口获取结果

**请求示例:**
```json
{
  "model": "gpt-image-2",
  "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
  "images": [],
  "aspectRatio": "1024x1024",
  "replyType": "json"
}
```

### gpt-image-2 支持的 aspectRatio 像素对照表

| 比例 | 1K | 2K | 4K (仅 vip) |
|------|-----|-----|-----|
| 1:1 | 1024x1024 | 2048x2048 | 2880x2880 |
| 16:9 | 1774x887 | 2048x1152 | 3840x2160 |
| 9:16 | 887x1774 | 1152x2048 | 2160x3840 |
| 3:2 | 1536x1024 | 2048x1360 | 3504x2336 |
| 2:3 | 1024x1536 | 1360x2048 | 2336x3504 |
| 21:9 | 2048x880 | 3840x1648 | - |
| 9:21 | 880x2048 | 1648x3840 | - |
| 1:3 | 688x2048 | 1280x3840 | - |
| 3:1 | 2048x688 | 3840x1280 | - |
| 2:1 | 2048x1024 | 3840x1920 | - |
| 1:2 | 1024x2048 | 1920x3840 | - |

> 像素比例没有严格限制，可根据官网支持的像素比输入。

## 接口二：异步结果查询

```
GET https://{base_url}/v1/api/result?id={task_id}
```

**Headers:**
```
Authorization: Bearer <API_KEY>
```

**Query 参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 任务 ID（生成接口返回） |

**返回结果:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务 ID |
| `status` | string | 任务状态 |
| `results` | array | 生成结果列表（成功时） |
| `results[].url` | string | 图片链接 |
| `progress` | integer | 进度 (0~100) |
| `error` | string | 报错信息（失败时） |

**status 取值:**
- `running` — 生成中，继续轮询
- `succeeded` — 生成成功
- `violation` — 违规
- `failed` — 生成失败

**成功响应示例:**
```json
{
  "id": "14-5f3cf761-a4bb-486a-8016-77f490998f80",
  "status": "succeeded",
  "results": [
    {
      "url": "https://file1.aitohumanize.com/file/fcdd2d07449d438d9d69d450f5626976.png"
    }
  ]
}
```

**失败响应示例:**
```json
{
  "id": "12-1f771fbf-f23a-4b89-a7d0-a98ba9862edb",
  "status": "failed",
  "error": "generate failed"
}
```

## Python 调用示例

### 同步模式 (replyType=json)

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "https://grsaiapi.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gpt-image-2",
    "prompt": "a cute corgi dog sitting on a beach",
    "images": [],
    "aspectRatio": "1024x1024",
    "replyType": "json"
}

resp = requests.post(f"{BASE_URL}/v1/api/generate", headers=headers, json=payload)
data = resp.json()
print(data["results"][0]["url"])
```

### 异步轮询模式 (replyType=async)

```python
import requests
import time

API_KEY = "your-api-key-here"
BASE_URL = "https://grsaiapi.com"

headers = {"Authorization": f"Bearer {API_KEY}"}

# 1. 提交生成任务
payload = {
    "model": "gpt-image-2",
    "prompt": "a beautiful sunset over mountains",
    "replyType": "async",
    "aspectRatio": "1024x1024"
}

resp = requests.post(f"{BASE_URL}/v1/api/generate", headers=headers, json=payload)
task_id = resp.json()["id"]
print(f"Task ID: {task_id}")

# 2. 轮询查询结果
while True:
    result = requests.get(f"{BASE_URL}/v1/api/result", headers=headers, params={"id": task_id})
    data = result.json()
    status = data["status"]

    if status == "succeeded":
        print(f"生成成功: {data['results'][0]['url']}")
        break
    elif status in ("failed", "violation"):
        print(f"生成失败: {data.get('error', 'unknown error')}")
        break
    else:
        print(f"生成中... ({data.get('progress', '?')}%)")
        time.sleep(3)
```

## curl 调用示例

```bash
# 生成图片（同步）
curl --location 'https://grsaiapi.com/v1/api/generate' \
  --header 'Authorization: Bearer <API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "gpt-image-2",
    "prompt": "生成一张边牧与古牧正在抖音直播间直播带货截图",
    "images": [],
    "aspectRatio": "1024x1024",
    "replyType": "json"
  }'

# 查询异步结果
curl --location 'https://grsaiapi.com/v1/api/result?id=<task_id>' \
  --header 'Authorization: Bearer <API_KEY>'
```

## Pitfalls

1. **API Key 必填** — 所有请求都需要 `Authorization: Bearer` header，从 https://grsai.ai/zh/dashboard/api-keys 获取。建议存入 `.env` 文件（`GRSAI_API_KEY=sk-xxx`），Python 代码中从环境变量读取。
2. **国内/全球节点** — 国内用户用 `grsai.dakka.com.cn`，海外用 `grsaiapi.com`
3. **异步轮询策略** — 生图平均 15s+，建议：第一次等 15 秒再查，之后每 5 秒查一次，超过 2 分钟放弃
4. **禁止提及艺术家名字** — 提示词中不能出现真实艺术家名字（如 "Makoto Shinkai" / "新海诚"、宫崎骏等），会触发内容政策违规。**解决办法**：描述画风特征而非作者名，例如 "anime style, vibrant blue sky, cinematic lighting, soft cloud gradients, high saturation, dreamy atmosphere"
5. **vip 支持 2K/4K** — `gpt-image-2-vip` 可以使用更大的像素尺寸（如 3840x2160）
6. **图生图（img2img）** — `images` 参数支持 base64 和 URL。本地图片建议先上传到公网图床获取 URL 再传参，避免请求体过大。
7. **Web UI 图片显示 (Windows)** — 生成的图片要保存到 Web UI 能访问的目录（即 Hermes 项目目录下，如 `F:\hema-fix\hema-fix\`），否则 download API 返回 404。路径格式使用 Windows 绝对路径（如 `F:\hema-fix\hema-fix\xxx.png`），**不要**在路径前加 `/`。
8. **GBK 编码问题 (Windows)** — Python 脚本中不要使用 emoji 做 print，否则会触发 `UnicodeEncodeError: 'gbk' codec can't encode character`。设置环境变量 `PYTHONIOENCODING=utf-8` 或避免 print(emoji)。
