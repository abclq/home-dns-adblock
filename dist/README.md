# dist/ — 多格式规则文件

本目录由 `scripts/export_lists.py` 自动生成，**请勿手工编辑**。重新生成：

```bash
python3 scripts/export_lists.py
```

## 文件说明

| 文件 | 格式 | 适用工具 |
|---|---|---|
| `hosts.txt` | `0.0.0.0 domain` | AdAway、路由器固件、DNS66、各种 hosts 导入器 |
| `hosts-ipv6.txt` | `:: domain` | 与 `hosts.txt` 组合，实现 IPv4 + IPv6 双栈拦截 |
| `adguard-dns.txt` | `\|\|domain^` | AdGuard Home、AdGuard App、AdGuard DNS、RethinkDNS |
| `domains.txt` | 纯域名列表 | RethinkDNS、SmartDNS、mosdns、自研脚本 |
| `dnsmasq-adblock.conf` | `address=/domain/#` | dnsmasq（双栈黑洞：A→0.0.0.0、AAAA→::） |

## 快速用法

**AdGuard Home**：过滤器 → DNS 黑名单 → 添加 URL 订阅
```
https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/adguard-dns.txt
```

**AdGuard / RethinkDNS App**：自定义过滤规则 → 从 URL 导入（同上）

**dnsmasq**：主配置里加一行后重启
```conf
conf-file=/path/to/dnsmasq-adblock.conf
```

**hosts 类工具**：把 `hosts.txt`（可再拼上 `hosts-ipv6.txt`）覆盖或追加到系统 hosts

## 订阅地址

| 格式 | URL |
|---|---|
| AdGuard 语法 | `https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/adguard-dns.txt` |
| hosts | `https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts.txt` |
| hosts IPv6 | `https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts-ipv6.txt` |
| 纯域名 | `https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/domains.txt` |

## 定位说明

本列表**只针对国内 App 的广告、埋点、统计域名**（抖音 / 番茄小说 / 红果短剧 / 小红书 / 高德等），
从真实设备的 DNS 查询日志中逐条提取，**不加通配、不误伤正片**。

它**不包含**国外通用广告域名（Google Ads、DoubleClick 等）——
那部分请配合 EasyList、anti-AD、AdGuard Base Filter 等成熟列表使用。

## 已知边界

DNS 层拦截做不到的事（别浪费时间）：

- **微信朋友圈广告** — 与好友动态走同一个 API，服务端混排，没有独立域名可拦
- **淘宝/京东首页推荐流** — 同上
- **直播中途插播广告** — 与正片共用 CDN 域名，且可能复用已建立连接
