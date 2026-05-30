#!/usr/bin/env python3
"""M Square 知识库检索 + 取页辅助脚本。

封装 search → agent/page 两步：给一个查询词，返回最相关页面的正文摘要
和图片列表（每张图带可直接 GET 的 url + 中文描述）。供调试 / 作为
Agent 接入的参考实现。

用法:
    export MSQUARE_WIKI_TOKEN=<管理员提供的 Token>
    python3 msquare_query.py "K141510 儿童多功能手提包"
    python3 msquare_query.py "轻旅行系列" --top-k 5 --result 0 --json

环境变量:
    MSQUARE_WIKI_TOKEN   必填，API 鉴权 Token
    MSQUARE_WIKI_BASE    可选，默认 https://wiki.aworld.ltd

依赖: 仅标准库（urllib）。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("MSQUARE_WIKI_BASE", "https://wiki.aworld.ltd").rstrip("/")
TOKEN = os.environ.get("MSQUARE_WIKI_TOKEN", "")
PROJECT = "current"


def _request(method, path, *, query=None, body=None):
    url = f"{BASE}/api/v1/projects/{PROJECT}/{path}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"[HTTP {e.code}] {method} {path}: {detail}")
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[请求失败] {method} {path}: {e}")


def search(query, top_k):
    return _request("POST", "search", body={"query": query, "topK": top_k})


def agent_page(path):
    # path 含 % 等字符，urlencode 会正确转义
    return _request("GET", "agent/page", query={"path": path})


def main():
    ap = argparse.ArgumentParser(description="M Square 知识库检索 + 取页")
    ap.add_argument("query", help="查询词：产品名 / 型号 / 系列 / 品类")
    ap.add_argument("--top-k", type=int, default=5, help="检索返回条数（默认 5）")
    ap.add_argument("--result", type=int, default=0, help="对第几条结果取页（默认 0）")
    ap.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = ap.parse_args()

    if not TOKEN:
        sys.exit("缺少 MSQUARE_WIKI_TOKEN 环境变量")

    hits = search(args.query, args.top_k)
    results = hits.get("results", [])
    if not results:
        sys.exit(f"未检索到与「{args.query}」相关的页面")

    if args.result >= len(results):
        sys.exit(f"--result {args.result} 越界，只有 {len(results)} 条结果")

    page = agent_page(results[args.result]["path"])["page"]

    if args.json:
        print(json.dumps(page, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"# {page['title']}  [{page['type']}]")
    print(f"path: {page['path']}\n")
    print("== 检索命中（topK）==")
    for i, r in enumerate(results):
        mark = " ←取此页" if i == args.result else ""
        print(f"  [{i}] score={r['score']:.1f}  {r['title']}{mark}")
    body = page["body"]
    print(f"\n== 正文（前 600 字，共 {len(body)} 字）==")
    print(body[:600])
    print(f"\n== 图片（{len(page['images'])} 张，url 可直接 GET）==")
    for i, im in enumerate(page["images"]):
        print(f"  [{i}] {im['url']}")
        print(f"       {im['description'][:90]}")


if __name__ == "__main__":
    main()
