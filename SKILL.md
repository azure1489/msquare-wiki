---
name: msquare-wiki
description: >-
  查询 M Square（旅行收纳品牌）产品知识库——产品、系列、品类、公司简介——
  返回带中文描述的官方产品图片与资料。当用户要 M Square 的产品信息、写推广文/
  小红书文案/促销文案、要产品配图或做图生图、整理某系列/品类的营销素材时使用。
  通过只读 HTTP API（search → agent/page）检索，图片返回开箱即用的 URL。
---

# M Square 产品知识库（msquare-wiki）

把 LLM Wiki 部署的 **M Square 产品知识库**接入对话。用户用自然语言提需求
（"给 K141510 写条推广文并配图"、"轻旅行系列有哪些产品"、"心心 IP 的促销文案"），
本技能负责**检索知识库、取回带中文描述的官方图片与产品资料**，供你生成
**推广文 / 图生图 / 产品促销信息**。

> 完整接口契约（所有端点、参数、错误码、配额）见 `reference/agent-api.md`。
> 本文件只讲**怎么用**。

## 连接配置

| 项 | 值 |
|---|---|
| Base URL | `https://wiki.aworld.ltd` |
| API 前缀 | `/api/v1` |
| Project ID | 用别名 `current`（指向当前 M Square 库） |
| 鉴权 | 每个请求带 `Authorization: Bearer <TOKEN>` |

**Token**：由知识库管理员提供，存为环境变量 `MSQUARE_WIKI_TOKEN`（或你的密钥管理），
**不要硬编码进代码/对话**。下文示例里的 `$MSQUARE_WIKI_TOKEN` 即指它。

## 核心工作流（三步）

```
① 检索   POST /api/v1/projects/current/search   {"query": "<产品名/型号/系列/品类>", "topK": 5}
            → 取 results[].path（最相关页面）

② 取页   GET  /api/v1/projects/current/agent/page?path=<上一步 path>
            → page.body              产品分析正文（卖点/材质/系列/年份）
            → page.images[]          每项 { url, description, path }

③ 生成   用 body + images[].description 写文案；用 images[].url 作为配图/图生图输入
```

### 取图规则（重要，别踩坑）

- **只用 `agent/page` 返回的 `images[].url` 取图**——它是已编码、可直接 GET 的完整 HTTPS 链接，
  **原样使用，不要再做 encode/decode**。
- **不要**用 `search` 结果里的 `images[].url`——那是原始相对路径，不能直接取图，仅供预览判断。
- 每张图都带 `description`（中文，逐字含图中文字、颜色、材质、款式），用它判断选哪张图最合适。

## 调用示例

```bash
# ① 检索
curl -s -X POST "https://wiki.aworld.ltd/api/v1/projects/current/search" \
  -H "Authorization: Bearer $MSQUARE_WIKI_TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"K141510 儿童多功能手提包","topK":3}'

# ② 取结构化页面（path 含 % 时务必 url-encode，curl 用 --data-urlencode）
curl -s -G "https://wiki.aworld.ltd/api/v1/projects/current/agent/page" \
  -H "Authorization: Bearer $MSQUARE_WIKI_TOKEN" \
  --data-urlencode "path=<results[].path>"

# ③ 取图（直接用 agent/page 的 images[].url，原样 GET）
curl -o product.jpg "<images[].url>"
```

辅助脚本 `scripts/msquare_query.py` 封装了①②两步，可直接试跑（见文件头注释）。

## 三个生成配方

### 推广文 / 小红书文案
1. `search` 产品名或型号 → 取 `results[0].path`
2. `agent/page` 取 `body` + `images[]`
3. 用 `body`（定位、系列、年份、材质、卖点）+ `images[].description`（图中细节）写文案，
   附 1–3 张 `images[].url` 作配图。

### 图生图
1. `search` → `agent/page` 拿 `images[]`
2. 按 `description` 选最合适的图，把它的 `url` 直接作为图生图模型的输入图（init image）。

### 品类 / 系列促销合集
1. `search`（如 `{"query":"轻旅行系列","topK":20}`）拿多条 `path`
2. 逐条 `agent/page` 聚合 `body` + `images`，生成系列促销长文 / 多图素材包
3. 可选：`GET /graph?q=<关键词>` 扩展关联产品。

## 常见问题
- **取图 404**：确认用的是 `agent/page` 的 `url`、且**没有**对它二次编码。
- **search 返回空**：换更具体的型号或产品名；中文/英文都可。
- **401**：Token 缺失或过期，检查 `Authorization` 头。
- **页面类型**：`source` 页（`wiki/sources/`）通常带最多产品图；其余类型见 `reference/agent-api.md` §5。

## 参考
- `reference/agent-api.md` — 完整接口文档（端点 / 参数 / 响应 / 错误码 / 配额 / 部署配置）
- `scripts/msquare_query.py` — 检索 + 取页 + 列图的辅助脚本
