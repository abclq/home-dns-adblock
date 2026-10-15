# dist/ — 多格式规则文件

本目录由 `scripts/export_lists.py` 自动生成，**请勿手工编辑**。重新生成：

```bash
python3 scripts/export_lists.py
```

## 文件说明

| 文件 | 格式 | 适用工具 |
|---|---|---|
| `hosts.txt` | `0.0.0.0 domain` | AdAway、路由器固件、DNS66、Pi-hole、各种 hosts 导入器 |
| `hosts-ipv6.txt` | `:: domain` | 与 `hosts.txt` 组合，实现 IPv4 + IPv6 双栈拦截 |
| `adguard-dns.txt` | `\|\|domain^` | AdGuard Home、AdGuard for Android、Pi-hole |
| `domains.txt` | 纯域名列表 | SmartDNS、mosdns、自研脚本 |
| `dnsmasq-adblock.conf` | `address=/domain/` | dnsmasq ≥ 2.86（返回 NXDOMAIN，App 不重试） |
| `upstream-domains.txt` | 纯域名列表 | 上游社区规则（928 条），单独订阅用 |
| `clash-surge-rules.txt` | `DOMAIN-SUFFIX,x,REJECT` | Clash、ClashX、Mihomo、Surge |
| `quantumultx-rules.txt` | `host-suffix, x, reject` | Quantumult X、Loon、Shadowrocket |

> 各软件的**具体添加位置**见 [`docs/use-with-other-apps.md`](../docs/use-with-other-apps.md)。
> 注意 **RethinkDNS 不支持自定义 URL**（只能勾选它预设的列表）。

**关于 dnsmasq 写法**：本项目用 `address=/domain/`（空地址 = **NXDOMAIN**，即「域名不存在」）。
实测比旧的 `address=/domain/#`（0.0.0.0 黑洞）更好 —— 0.0.0.0 会让 App 以为「服务器暂时不可用」
而**反复重试**（实测某广告域 20 分钟被重试 206 次）；NXDOMAIN 则让 App **立刻放弃**，重试归零。
需要 dnsmasq ≥ 2.86（2020 年发布）。若你的版本更老，把 `/domain/` 改回 `/domain/#` 即可。

## 快速用法

**AdGuard Home**：过滤器 → DNS 黑名单 → 添加 URL 订阅
```
https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/adguard-dns.txt
```

**AdGuard / RethinkDNS App**：自定义过滤规则 → 从 URL 导入（同上）

**dnsmasq**：主配置里加一行后重启
```conf
conf-file=/path/to/dnsmasq-adblock.conf
```

**hosts 类工具**：把 `hosts.txt`（可再拼上 `hosts-ipv6.txt`）覆盖或追加到系统 hosts

## 订阅地址

**走 jsDelivr 全球 CDN —— 国内直连可用，海外同样快。** 前缀统一用 `fastly.`（`cdn.jsdelivr.net` 在国内会被重置，别用）。

| 格式 | URL |
|---|---|
| AdGuard 语法 | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/adguard-dns.txt` |
| hosts | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/hosts.txt` |
| hosts IPv6 | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/hosts-ipv6.txt` |
| 纯域名 | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/domains.txt` |
| Clash / Surge / Mihomo | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/clash-surge-rules.txt` |
| Quantumult X / Loon | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/quantumultx-rules.txt` |
| dnsmasq | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/dnsmasq-adblock.conf` |
| **上游规则（纯域名）** | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/upstream-domains.txt` |
| 打包下载（全部格式） | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/home-dns-adblock-rules.zip` |

> 拉不动就把 `fastly` 换成 `gcore` 或 `testingcf`，路径不变。
> 海外用户也可直接用 `https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/...`。

## 定位说明

本列表**只针对国内 App 的广告、埋点、统计域名**（抖音 / 番茄小说 / 红果短剧 / 小红书 / 高德等），
从真实设备的 DNS 查询日志中逐条提取，**不加通配、不误伤正片**。

它**不包含**国外通用广告域名（Google Ads、DoubleClick 等）——
那部分请配合 EasyList、anti-AD、AdGuard Base Filter 等成熟列表使用。

### 两套列表，按需选

本仓库实际产出**两套**规则，来源和维护方式不同：

| 套件 | 文件 | 条数 | 来源 | 特点 |
|---|---|---|---|---|
| **主列表** | `domains.txt` / `hosts.txt` / `dnsmasq-adblock.conf` … | 86 | 实机 DNS 日志逐条提取 | 精准、不误伤、**国内 App 专用** |
| **上游列表** | `upstream-domains.txt` | 928 | 社区规则（AWAvenue-Ads-Rule）自动同步 | 覆盖广、每天更新、**已过白名单** |

两套可以**一起用**（互补，主列表更精准、上游覆盖更广），也可以只用其中一套。
上游列表由 GitHub Actions 每天 04:00 自动更新，已自动剔除会误伤正片的域名（见 `config/whitelist.txt`）。

## 已知边界

DNS 层拦截做不到的事（别浪费时间）：

- **微信朋友圈广告** — 与好友动态走同一个 API，服务端混排，没有独立域名可拦
- **淘宝/京东首页推荐流** — 同上
- **直播中途插播广告** — 与正片共用 CDN 域名，且可能复用已建立连接
