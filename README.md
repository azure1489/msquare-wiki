# msquare-wiki — M Square 产品知识库 Skill

把 **M Square（旅行收纳品牌）产品知识库**接入你的 AI Agent。用自然语言提需求
（"给 K141510 写条小红书推广文并配图"、"轻旅行系列有哪些产品"、"心心魔术贴的促销文案"），
本 Skill 负责**检索知识库、取回带中文描述的官方产品图片与资料**，供 Agent 生成
**推广文 / 小红书文案 / 图生图输入 / 系列促销素材**。

- 形态：标准 [Agent Skill](https://github.com/vercel-labs/skills)（根目录 `SKILL.md` + 参考脚本 + 完整接口文档）
- 数据来源：远端只读 HTTP API（`https://wiki.aworld.ltd`），本仓库只封装"怎么调用"，不含数据
- 依赖：仅需 Python 3（参考脚本只用标准库，无第三方依赖）

---

## 给 Agent 的安装清单（可直接执行）

> 按顺序执行；每步附了成功判据。`<TOKEN>` 由知识库管理员提供，**不要写进任何文件或提交**。

```bash
# 1. 安装 Skill 到全局（所有项目可用）。装到 ~/.claude/skills/msquare-wiki/
npx skills add azure1489/msquare-wiki -g
#    成功判据：npx skills list 能看到 msquare-wiki

# 2. 配置 API Token（必需，否则所有调用返回 401）
export MSQUARE_WIKI_TOKEN='<TOKEN>'        # 建议写进 shell profile / 密钥管理，勿硬编码

# 3. 验证连通（应打印命中页面正文摘要 + 图片 URL 列表，退出码 0）
python3 ~/.claude/skills/msquare-wiki/scripts/msquare_query.py "心心魔术贴" --top-k 3
#    成功判据：退出码 0；输出含 "== 图片（N 张，url 可直接 GET）=="
```

三步都通过即安装完成。之后向用户/模型提需求即可触发本 Skill（描述见 `SKILL.md` 的 frontmatter）。

---

## 安装方式详解

### 方式一：`skills` CLI（推荐）

使用开放 skills 生态的 CLI 安装，自动放进对应 agent 的 skills 目录：

```bash
# 全局：装到 ~/.claude/skills/（所有项目可用，推荐——这是通用产品知识库 skill）
npx skills add azure1489/msquare-wiki -g

# 项目级：装到当前项目的 .claude/skills/（只在本项目可用）
npx skills add azure1489/msquare-wiki
```

常用管理命令：

```bash
npx skills list                       # 列出已安装的 skill，确认 msquare-wiki 在内
npx skills remove msquare-wiki        # 卸载（项目级）
npx skills remove --global msquare-wiki   # 卸载（全局）
```

> `skills` CLI 支持多种 agent（Claude Code、Cursor 等），会把本仓库识别为根目录布局的 skill（`SKILL.md` 在根）。

### 方式二：手动 git clone（不依赖 CLI 的兜底方案）

直接 clone 到 Claude Code 的 skills 目录即可被发现：

```bash
# 全局
git clone https://github.com/azure1489/msquare-wiki.git ~/.claude/skills/msquare-wiki

# 或项目级（在你的项目根目录执行）
git clone https://github.com/azure1489/msquare-wiki.git .claude/skills/msquare-wiki
```

更新到最新：`git -C ~/.claude/skills/msquare-wiki pull`。

---

## 配置 Token（必需）

所有 `/api/v1/**` 请求都需要 Bearer Token，缺失返回 `401`。Token 由知识库管理员提供，
通过环境变量传入，**绝不写进代码 / 文档 / 提交记录 / 对话**：

| 环境变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `MSQUARE_WIKI_TOKEN` | 是 | — | API 鉴权 Token |
| `MSQUARE_WIKI_BASE` | 否 | `https://wiki.aworld.ltd` | 知识库 Base URL（一般不用改） |

```bash
export MSQUARE_WIKI_TOKEN='<管理员提供的Token>'
```

> 安全提示：避免把 Token 作为命令行参数明文传入（会留在 shell 历史）；优先用 `export` 或密钥管理工具。

---

## 验证安装

```bash
# 1) 服务健康（免鉴权）——应返回 {"ok":true,"status":"running",...}
curl -s https://wiki.aworld.ltd/health

# 2) 端到端连通（需已设置 MSQUARE_WIKI_TOKEN）——应打印正文摘要 + 图片 URL
python3 <skills目录>/msquare-wiki/scripts/msquare_query.py "心心魔术贴"
```

`agent/page` 返回的 `images[].url` 是**可直接 GET 的完整 HTTPS 链接**，原样取图即得官方产品图（不要二次编码）。

---

## 安装后如何使用

核心是三步只读工作流（完整说明见 `SKILL.md`）：

```
① POST /api/v1/projects/current/search   {"query":"<产品名/型号/系列>","topK":N}  → results[].path
② GET  /api/v1/projects/current/agent/page?path=<上一步 path>                     → page.body + page.images[]
③ 用 body + images[].description 写文案；用 images[].url 作配图 / 图生图输入
```

更多内容看这三个文件：

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 面向使用者的"怎么用"——连接配置、三步工作流、三个生成配方、常见问题 |
| `reference/agent-api.md` | 完整接口契约——所有端点 / 参数 / 响应 / 错误码 / 配额 |
| `scripts/msquare_query.py` | `search → agent/page` 的参考实现（仅标准库，可直接试跑） |

---

## 故障排查（安装相关）

| 现象 | 原因 / 处理 |
|---|---|
| 脚本报 "缺少 MSQUARE_WIKI_TOKEN 环境变量" | 未执行 `export MSQUARE_WIKI_TOKEN=...`，或在新 shell 里丢失——写进 shell profile |
| 调用返回 `401` | Token 缺失 / 过期 / 写错，检查 `Authorization` 头与 Token 值 |
| `npx skills` 提示找不到包 | 需联网；或改用方式二 `git clone` 手动安装 |
| 取图 `404` | 确认用的是 `agent/page` 的 `images[].url`，且**没有**对它二次 encode/decode |
| `search` 返回空 | 换更具体的型号或产品名（中/英文均可） |
