#!/usr/bin/env python3
"""上游广告规则同步 —— 云上跑（GitHub Actions 定时执行）

来源：AWAvenue-Ads-Rule（专治中文 App 广告，AdGuard 格式）
安全：① 白名单硬保护（config/whitelist.txt，子域自动匹配）
      ② 裸域危险规则剔除（.zijieapi.com 这种封整域的一律不要）
      ③ 输出统一 NXDOMAIN 写法（address=/域名/）

输出：config/adblock-upstream.conf   本机 dnsmasq 直接 conf-file 加载
      dist/upstream-domains.txt      纯域名，给别的工具用
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WHITELIST = ROOT / "config" / "whitelist.txt"
OUT_CONF = ROOT / "config" / "adblock-upstream.conf"
OUT_DOMAINS = ROOT / "dist" / "upstream-domains.txt"

UPSTREAMS = [
    ("AWAvenue-Ads-Rule",
     "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/AWAvenue-Ads-Rule.txt"),
]

# 这些域绝不整域封（裸域规则）
BARE_FORBIDDEN = {
    "zijieapi.com", "snssdk.com", "isnssdk.com", "toutiao.com", "bytedance.com",
    "byteimg.com", "amemv.com", "ixigua.com", "douyin.com", "fqnovel.com",
    "bytefcdn.com", "douyincdn.com", "douyinliving.com",
}

DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?\.[a-z]{2,}$")


def load_whitelist() -> list[str]:
    out = []
    for line in WHITELIST.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip().lower()
        if line:
            out.append(line)
    return out


def is_whitelisted(domain: str, wl: list[str]) -> bool:
    return any(domain == w or domain.endswith("." + w) for w in wl)


def parse_adguard(text: str) -> set[str]:
    """AdGuard 语法 → 纯域名。跳过注释/例外/通配符。"""
    out: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("!", "[", "#")):
            continue
        if line.startswith("@@"):          # 例外规则
            continue
        if "$" in line:                    # 带修饰符，跳过（可能限定 App）
            continue
        d = line
        if d.startswith("||"):
            d = d[2:]
        d = d.rstrip("^").lstrip("|").lstrip(".").lower()
        if not d or "*" in d or "/" in d:
            continue
        if DOMAIN_RE.match(d):
            out.add(d)
    return out


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "home-dns-adblock-sync/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")


def main() -> int:
    wl = load_whitelist()
    print(f"白名单保护 {len(wl)} 个域：{' '.join(wl)}")

    domains: set[str] = set()
    for name, url in UPSTREAMS:
        try:
            text = fetch(url)
        except Exception as e:
            print(f"⚠️  {name} 拉取失败：{e} —— 本轮跳过该源", file=sys.stderr)
            continue
        got = parse_adguard(text)
        print(f"✅ {name}：解析出 {len(got)} 个域名")
        domains |= got

    if not domains:
        print("❌ 所有源都失败，不覆盖现有文件", file=sys.stderr)
        return 1

    # 白名单过滤 + 裸域危险规则剔除
    kept, dropped_wl, dropped_bare = set(), 0, 0
    for d in domains:
        if is_whitelisted(d, wl):
            dropped_wl += 1
            continue
        if d in BARE_FORBIDDEN:
            dropped_bare += 1
            continue
        kept.add(d)

    # 去掉手写列表已有的（config/adblock-fq.conf）
    ours: set[str] = set()
    fq = ROOT / "config" / "adblock-fq.conf"
    if fq.exists():
        ours = set(re.findall(r"^address=/([^/]+)/", fq.read_text(encoding="utf-8"), re.M))
    before = len(kept)
    kept -= ours

    print(f"过滤：白名单剔除 {dropped_wl} · 裸域剔除 {dropped_bare} · 与手写列表重复 {before - len(kept)}")
    print(f"最终上游规则 {len(kept)} 条")

    domains_sorted = sorted(kept)
    OUT_CONF.write_text(
        "# 上游广告规则（自动生成，勿手改）\n"
        "# 来源：" + " · ".join(n for n, _ in UPSTREAMS) + "\n"
        "# 生成：GitHub Actions 定时任务\n"
        f"# 条数：{len(domains_sorted)}（已过白名单过滤）\n"
        "# 白名单保护：" + " ".join(wl) + "\n\n"
        + "".join(f"address=/{d}/\n" for d in domains_sorted),
        encoding="utf-8",
    )
    OUT_DOMAINS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOMAINS.write_text("\n".join(domains_sorted) + "\n", encoding="utf-8")
    print(f"写入 {OUT_CONF.relative_to(ROOT)} 和 {OUT_DOMAINS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
