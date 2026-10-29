#!/usr/bin/env python3
"""AI 维护助手 —— 用任意 OpenAI 兼容模型给 issue 做分诊 + 出补漏建议。

设计原则（为什么不硬编码某一家）：
  仓库维护不应该绑死在某一个模型/平台上。任何提供 OpenAI 兼容
  /chat/completions 的端点都能接：Muse（经 muse2api 反代）、各地中转站、
  本地 Ollama、官方 OpenAI 都行。只换环境变量，不改代码。

环境变量：
  AI_BASE_URL   形如 https://host/v1        （不带结尾斜杠也可以）
  AI_API_KEY    Bearer token
  AI_MODEL      模型名，例如 muse-chat
  GITHUB_TOKEN  Actions 自带；本地跑时用 gh auth token
  兼容别名：MUSE_BASE_URL / MUSE_API_KEY / MUSE_MODEL

用法：
  python3 scripts/ai_triage.py                    # 只生成报告文件
  python3 scripts/ai_triage.py --post-comment 1   # 并把结果评论到 issue 1
  python3 scripts/ai_triage.py --dry              # 打印将要发送的 prompt，不调 API

退出码永远是 0（除了参数错误）——没配密钥时跳过，不让 CI 变红。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "abclq/home-dns-adblock")


def env(*names, default=""):
    for n in names:
        v = os.environ.get(n)
        if v:
            return v.strip()
    return default


def api(url, token=None, data=None, method=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-triage"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def list_issues(token, state="open"):
    out = []
    for page in (1, 2):
        url = f"https://api.github.com/repos/{REPO}/issues?state={state}&per_page=50&page={page}"
        batch = api(url, token)
        if not batch:
            break
        out += [i for i in batch if "pull_request" not in i]
        if len(batch) < 50:
            break
    return out


def issue_comments(token, num):
    return api(f"https://api.github.com/repos/{REPO}/issues/{num}/comments?per_page=100", token)


def repo_stats():
    """给模型一点事实基础，避免它瞎猜规则规模。"""
    def count(path, pred):
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                return sum(1 for line in f if pred(line.strip()))
        except OSError:
            return 0

    return {
        "精确规则(config/)": count("config/adblock-fq.conf", lambda s: s.startswith("address="))
        + count("config/adblock-extra.conf", lambda s: s.startswith("address=")),
        "上游规则(config/adblock-upstream.conf)": count(
            "config/adblock-upstream.conf", lambda s: s.startswith("address=")
        ),
        "全量导出(dist/adguard-dns-full.txt)": count(
            "dist/adguard-dns-full.txt", lambda s: s.startswith("||")
        ),
    }


SYSTEM = """你是 github.com/{repo} 的维护助手。这个仓库提供国内 App（红果短剧/番茄小说/抖音/小红书/高德）
的 DNS 广告拦截规则，分两层：精确规则（真实设备抓包，零误拦，条数少）与上游社区规则（覆盖面大，
有误伤风险）。导出文件由 scripts/export_lists.py 生成，不要手工编辑 dist/。

你的任务：针对给出的 issue，判断问题属于哪一类，并给出**可以直接照做**的下一步。
类别只能是以下之一：
  A. 订阅没生效（URL 用错、只订了精确规则漏了上游、CDN 前缀 cdn. 被重置、客户端缓存没更新）
  B. 规则缺口（确实是新域名，需要补进精确规则）
  C. 环境问题（私人 DNS/DoH 绕过、路由器没走本机、加密 DNS、非 DNS 层广告如直连 IP）
  D. 期望不符（诉求超出 DNS 拦截能力，例如想拦 App 内嵌 H5 广告）
  E. 信息不足

输出要求（Markdown，中文，直接给用户看的口气）：
1. 一句话结论
2. 判断类别（A-E）+ 依据（引用 issue 里的话）
3. 最多 4 步「照着做」清单，每步要具体到点哪里、填什么
4. 如果属于 B，给出需要补的域名候选与「怎么自己确认是不是广告域」的方法
5. 不要承诺做不到的事；不确定就说不确定
不要输出思考过程，直接给最终答复。"""


def build_prompt(issues, token, limit=5):
    stats = repo_stats()
    blocks = []
    for it in issues[:limit]:
        cs = issue_comments(token, it["number"])[-4:]
        thread = "\n".join(
            f"- {(c.get('user') or {}).get('login','?')}: {(c.get('body') or '')[:600]}"
            for c in cs
        ) or "（无评论）"
        blocks.append(
            f"### issue #{it['number']} {it.get('title') or ''}\n"
            f"作者: {(it.get('user') or {}).get('login','?')}  最后更新: {it.get('updated_at','?')}\n"
            f"正文:\n{(it.get('body') or '（空）')[:1800]}\n\n最近评论:\n{thread}\n"
        )
    return (
        f"仓库当前规模：{json.dumps(stats, ensure_ascii=False)}\n"
        f"订阅地址约定：全量用 "
        f"https://fastly.jsdelivr.net/gh/{REPO}@main/dist/adguard-dns-full.txt ，"
        f"精确规则用 dist/adguard-dns.txt（只有精确层，单订它会漏 900+ 条上游）。\n\n"
        + "\n".join(blocks)
    )


def chat(base, key, model, system, user):
    url = base.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1600,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-comment", type=int, default=0, help="把结果评论到指定 issue 号")
    ap.add_argument("--dry", action="store_true", help="只打印 prompt，不调模型")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="ai-triage-report.md")
    args = ap.parse_args()

    base = env("AI_BASE_URL", "MUSE_BASE_URL")
    key = env("AI_API_KEY", "MUSE_API_KEY")
    model = env("AI_MODEL", "MUSE_MODEL")
    gh = env("GITHUB_TOKEN") or os.popen("gh auth token 2>/dev/null").read().strip()

    if not gh:
        print("[skip] 没有 GITHUB_TOKEN，无法读取 issue")
        return 0

    issues = list_issues(gh)
    if not issues:
        print("[ok] 没有待处理 issue")
        return 0

    prompt = build_prompt(issues, gh, args.limit)
    if args.dry:
        print(prompt)
        return 0

    if not (base and key and model):
        msg = (
            f"# AI 维护报告（未配置模型，跳过）\n\n"
            f"待处理 issue {len(issues)} 条：\n"
            + "\n".join(f"- #{i['number']} {i['title']}" for i in issues)
            + "\n\n配置 `AI_BASE_URL` / `AI_API_KEY` / `AI_MODEL` 后重跑即可让模型分诊。\n"
            + "（Muse 走 muse2api 反代时，三者分别填反代地址、令牌、模型名）\n"
        )
        open(args.out, "w", encoding="utf-8").write(msg)
        print(msg)
        return 0

    try:
        report = chat(base, key, model, SYSTEM.format(repo=REPO), prompt)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
        print(f"[warn] 模型调用失败：{e}")
        report = f"# AI 维护报告（模型调用失败）\n\n错误：{e}\n\n待处理 issue：\n" + "\n".join(
            f"- #{i['number']} {i['title']}" for i in issues
        )

    header = (
        f"# AI 维护报告\n\n模型 `{model}` · 待处理 issue {len(issues)} 条 · "
        f"仓库规模 {json.dumps(repo_stats(), ensure_ascii=False)}\n\n---\n\n"
    )
    open(args.out, "w", encoding="utf-8").write(header + report + "\n")
    print(header + report)

    if args.post_comment:
        body = (
            "🤖 **维护助手自动分诊**（仅供参考，规则改动仍需人工确认）\n\n"
            + report
            + "\n\n---\n> 由仓库 AI 维护工作流生成。"
        )
        api(
            f"https://api.github.com/repos/{REPO}/issues/{args.post_comment}/comments",
            gh,
            {"body": body},
        )
        print(f"[ok] 已评论到 issue #{args.post_comment}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
