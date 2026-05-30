# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这个仓库是什么

这是一个 **Claude Code Skill 包**，名为 `msquare-wiki`，不是一个应用程序。它的「产物」是文档 + 一个参考脚本，作用是把 **M Square（旅行收纳品牌）产品知识库**接入对话，供生成推广文 / 小红书文案 / 图生图输入 / 系列促销素材。

知识库本身部署在远端（LLM Wiki，应用版本 0.4.16），本仓库**只封装如何通过其只读 HTTP API 调用它**，不包含知识库数据或服务端代码。

## 三个文件的分工（核心架构）

仓库是分层文档，改动时务必保持三者一致：

| 文件 | 角色 | 维护原则 |
|---|---|---|
| `SKILL.md` | 面向使用者的「怎么用」——连接配置、三步工作流、三个生成配方、常见问题 | 简明、只讲操作；frontmatter 的 `description` 决定技能何时被触发 |
| `reference/agent-api.md` | 完整接口契约——所有端点、参数、响应、错误码、配额、部署配置 | 接口的**单一事实来源**；端点行为变化先改这里 |
| `scripts/msquare_query.py` | `search → agent/page` 两步的参考实现（仅标准库 urllib，无第三方依赖） | 是契约的可执行示例；改 API 时同步更新 |

`SKILL.md` 是 `agent-api.md` 的精简操作版——两者描述同一套 API。修改任何 API 行为（端点、字段、取图规则）时，三处需同步，否则会出现文档自相矛盾。

## API 工作流（所有功能的基础）

```
① POST /api/v1/projects/current/search   {"query": "<产品名/型号/系列/品类>", "topK": N}
     → results[].path                      最相关页面路径
② GET  /api/v1/projects/current/agent/page?path=<上一步 path>
     → page.body                           产品分析正文（卖点/材质/系列/年份）
     → page.images[]                        每项 { url, description, path }
③ 用 body + images[].description 写文案；用 images[].url 作配图 / 图生图输入
```

- `projectId` 统一用别名 `current`（指向当前 M Square 库，固定 UUID `ddce884e-d0ee-40ec-98cb-2830b153f565`）。
- Base URL：`https://wiki.aworld.ltd`，API 前缀 `/api/v1`（`/health` 例外，免鉴权）。
- 鉴权：每个 `/api/v1/**` 请求带 `Authorization: Bearer <TOKEN>`，缺失返回 401。

## 关键陷阱：取图只用 agent/page 的 url

两个端点的 `images[].url` 语义不同，最容易踩坑：

- ✅ `GET /agent/page` 的 `images[].url`——完整 HTTPS、**服务端已逐段编码**，原样 GET，**不要再 encode/decode**（url 里出现 `%2520` 这种双重编码是正常的，因为 media 目录名本身含字面 `%`）。
- ❌ `POST /search` 的 `images[].url`——原始相对路径，**不可直接取图**，仅供预览判断该页有无相关图。

取图 404 时，首先确认用的是 `agent/page` 的 url 且没有二次编码。

## 鉴权 Token（不要硬编码）

Token 由知识库管理员提供，通过环境变量传入，**绝不写进代码 / 文档 / 对话**：

```bash
export MSQUARE_WIKI_TOKEN=<管理员提供的 Token>
export MSQUARE_WIKI_BASE=https://wiki.aworld.ltd   # 可选，脚本默认值
```

## 运行参考脚本

无构建 / lint / 测试框架（纯文档 + 标准库脚本）。验证 API 连通和改动用脚本试跑：

```bash
# 检索 + 取页，人类可读输出（正文前 600 字 + 图片 url 列表）
python3 scripts/msquare_query.py "K141510 儿童多功能手提包"

# 指定返回条数、对第几条结果取页、输出原始 JSON
python3 scripts/msquare_query.py "轻旅行系列" --top-k 5 --result 0 --json
```

## 页面类型速记

`agent/page` 返回的 `page.type` 中，**`source` 页（`wiki/sources/`）通常带最多产品图**，是写文案 / 取图的主力。其余类型（`overview` / `entity` / `concept` / `comparison` / `synthesis`）见 `reference/agent-api.md` §5。
