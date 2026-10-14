#!/usr/bin/env python3
"""把文档里写死的规则条数刷新成真实值。

为什么需要它：config/adblock-upstream.conf 由云端 Actions 每天重新生成，
条数每天都在变；README / docs 里手写的数字必然天天过期（云机巡检每天都在挑这个）。
改完规则后跑一次即可，sync_adblock_repo.sh 也会自动调用。

用法：  python3 scripts/update_counts.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config")
DRY = "--dry-run" in sys.argv


def doms(name):
    """从 adblock-*.conf 里取出所有被拦的域名集合。"""
    s = set()
    p = os.path.join(CFG, name)
    if not os.path.exists(p):
        return s
    with open(p, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^address=/([^/]+)/", line.strip())
            if m:
                s.add(m.group(1))
    return s


fq = doms("adblock-fq.conf")
ex = doms("adblock-extra.conf")
up = doms("adblock-upstream.conf")

N_FQ = len(fq)
N_EX = len(ex)
N_UP = len(up)
PRECISE = len(fq | ex)        # 精确规则合计（fq + extra 去重）
TOTAL = len(fq | ex | up)     # 三者去重合计

# (正则, 替换) —— 全部带上下文锚点，不会误伤文档里无关的数字
RULES = [
    (r"\d+ 条精确规则",                    f"{PRECISE} 条精确规则"),
    (r"\d+ 条精确域名",                    f"{PRECISE} 条精确域名"),
    (r"\d+ precise rules",                f"{PRECISE} precise rules"),
    (r"\*\*\d+\*\* precise domains",      f"**{PRECISE}** precise domains"),
    (r"精确规则 \d+ 条",                    f"精确规则 {PRECISE} 条"),
    (r"该拦清单（\d+ 条",                   f"该拦清单（{N_FQ} 条"),
    (r"红果/番茄系手工规则（\d+ 条）",        f"红果/番茄系手工规则（{N_FQ} 条）"),
    (r"# \d+ 条现成规则",                   f"# {N_FQ} 条现成规则"),
    (r"（\d+ 条精确域名）",                  f"（{N_FQ} 条精确域名）"),
    (r"fq \d+ / extra \d+",               f"fq {N_FQ} / extra {N_EX}"),
    (r"\| \d+ \| 实机 DNS 日志逐条提取",     f"| {PRECISE} | 实机 DNS 日志逐条提取"),
    (r"\| `config/adblock-fq\.conf` \| 实机抓包 \+ 社区规则交叉验证 \| \*\*人\*\*（本仓库） \| \d+ \|",
     f"| `config/adblock-fq.conf` | 实机抓包 + 社区规则交叉验证 | **人**（本仓库） | {N_FQ} |"),
    (r"\d+ 条上游社区规则",                 f"{N_UP} 条上游社区规则"),
    (r"\d+ upstream community rules",     f"{N_UP} upstream community rules"),
    (r"上游同步（\d+ 条）",                 f"上游同步（{N_UP} 条）"),
    (r"去重后合计 \d+ 条",                  f"去重后合计 {TOTAL} 条"),
    (r"\(\d+ unique after dedup\)",       f"({TOTAL} unique after dedup)"),
]

FILES = [
    "README.md",
    "README.en.md",
    "dist/README.md",
    "docs/domain-list.md",
    "docs/for-agents.md",
    "docs/pitfalls.md",
    "docs/principles.md",
    "docs/use-with-other-apps.md",
]

print(f"真实条数：fq={N_FQ}  extra={N_EX}  upstream={N_UP}  精确合计={PRECISE}  三者去重={TOTAL}")
changed_total = 0
for rel in FILES:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        continue
    src = open(path, encoding="utf-8").read()
    out = src
    hits = []
    for pat, rep in RULES:
        out, n = re.subn(pat, rep, out)
        if n:
            hits.append(f"{pat} ×{n}")
    if out != src:
        changed_total += len(hits)
        print(f"  {'(dry) ' if DRY else ''}✎ {rel}: {len(hits)} 处")
        for h in hits:
            print(f"      - {h}")
        if not DRY:
            open(path, "w", encoding="utf-8").write(out)

print(f"{'[dry-run] ' if DRY else ''}共刷新 {changed_total} 处")
