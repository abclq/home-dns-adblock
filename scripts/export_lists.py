#!/usr/bin/env python3
"""
导出多种格式的广告屏蔽规则，供第三方工具使用。

支持的输出格式：
  hosts.txt          通用 hosts（0.0.0.0）—— AdAway / 路由器 / DNS66 / 各类固件
  hosts-ipv6.txt     仅 IPv6 黑洞（::）—— 可与 hosts.txt 组合双栈
  adguard-dns.txt    AdGuard DNS 语法（||domain^）—— AdGuard Home / AdGuard App / AdGuard DNS
  domains.txt        纯域名列表 —— RethinkDNS / SmartDNS / dnsmasq 手动导入
  dnsmasq-adblock.conf  dnsmasq 语法（address=/domain/#）—— 双栈黑洞

用法：
  python3 scripts/export_lists.py            # 输出到 dist/
  python3 scripts/export_lists.py <输出目录>  # 自定义输出目录
"""
import os
import re
import sys
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 规则来源（仓库内）
SOURCES = [
    'config/dnsmasq.conf.example',   # 主配置里的手工规则
    'config/adblock-fq.conf',        # 社区规则集
    'config/adblock-extra.conf',     # 手工补充规则
]

RULE_RE = re.compile(r'^(?:address|local)=/([^/]+)/')


def load_domains():
    """从所有来源文件里提取域名，去重排序。"""
    domains = set()
    stats = []
    for rel in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        n = 0
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = RULE_RE.match(line.strip())
                if m:
                    d = m.group(1).strip().lower().rstrip('.')
                    # 排除下划线开头的特殊域名（如 _dns.resolver.arpa）
                    # 原因: 第三方工具（AdGuard/hosts）的语法校验不接受这类域名，
                    #       且它只对苹果设备的 DDR 发现协议有意义，本机自用即可。
                    if d and not d.startswith('_'):
                        if d not in domains:
                            n += 1
                        domains.add(d)
        stats.append((rel, n))
    return sorted(domains), stats


HEADER = """# {title}
# 由 export_lists.py 生成 — 请勿手工编辑
# 规则指纹: {fp}    （内容不变时此值不变，重复生成结果完全一致）
# 规则条数: {n}
# 项目: https://github.com/abclq/home-dns-adblock
#
# 说明: 本列表针对国内 App（抖音/番茄小说/红果短剧/小红书/高德等）的
#       广告、埋点、统计域名，从真实设备 DNS 查询日志中提取。
#       不含通用/国外广告域名 —— 那部分请另配 EasyList / anti-AD 等。
"""


def write(path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'  ✓ {os.path.relpath(path, ROOT)}')


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist')
    os.makedirs(outdir, exist_ok=True)

    domains, stats = load_domains()
    n = len(domains)
    # 规则指纹：只对域名内容取 hash，不含时间戳。
    # 这样内容不变时重复导出得到完全相同的文件，定时同步脚本才能靠 git diff
    # 判断"规则真的变了吗"，不会每次运行都刷出一堆空提交。
    fp = hashlib.sha256('\n'.join(domains).encode('utf-8')).hexdigest()[:16]

    print(f'  来源:')
    for rel, c in stats:
        print(f'    {rel:<38} 新增 {c} 条')
    print(f'  去重后合计: {n} 条')
    print()

    # ① hosts
    body = HEADER.format(title='Home DNS Adblock — hosts 格式 / hosts format', fp=fp, n=n)
    body += '\n'.join(f'0.0.0.0 {d}' for d in domains) + '\n'
    write(os.path.join(outdir, 'hosts.txt'), body)

    # ② hosts IPv6
    body = HEADER.format(title='Home DNS Adblock — hosts IPv6 黑洞（可选，配合 hosts.txt 做双栈）', fp=fp, n=n)
    body += '\n'.join(f':: {d}' for d in domains) + '\n'
    write(os.path.join(outdir, 'hosts-ipv6.txt'), body)

    # ③ AdGuard DNS 语法
    body = HEADER.format(title='Home DNS Adblock — AdGuard DNS 语法 / AdGuard syntax', fp=fp, n=n)
    body += '\n'.join(f'||{d}^' for d in domains) + '\n'
    write(os.path.join(outdir, 'adguard-dns.txt'), body)

    # ④ 纯域名
    body = HEADER.format(title='Home DNS Adblock — 纯域名列表 / domain list', fp=fp, n=n)
    body += '\n'.join(domains) + '\n'
    write(os.path.join(outdir, 'domains.txt'), body)

    # ⑤ dnsmasq
    body = HEADER.format(title='Home DNS Adblock — dnsmasq 语法（address=/domain/# 双栈黑洞）', fp=fp, n=n)
    body += '\n'.join(f'address=/{d}/#' for d in domains) + '\n'
    write(os.path.join(outdir, 'dnsmasq-adblock.conf'), body)

    # ⑥ Clash / Surge / Mihomo（同一套 DOMAIN-SUFFIX 语法，可两用）
    body = HEADER.format(
        title='Home DNS Adblock — Clash / Surge / Mihomo 规则（贴进 rules: 段）', fp=fp, n=n)
    body += '\n'.join(f'DOMAIN-SUFFIX,{d},REJECT' for d in domains) + '\n'
    write(os.path.join(outdir, 'clash-surge-rules.txt'), body)

    # ⑦ Quantumult X / Loon（host-suffix 语法）
    body = HEADER.format(
        title='Home DNS Adblock — Quantumult X / Loon 规则（贴进 [filter_local] 段）', fp=fp, n=n)
    body += '\n'.join(f'host-suffix, {d}, reject' for d in domains) + '\n'
    write(os.path.join(outdir, 'quantumultx-rules.txt'), body)

    print()
    print(f'  输出目录: {outdir}')


if __name__ == '__main__':
    main()
