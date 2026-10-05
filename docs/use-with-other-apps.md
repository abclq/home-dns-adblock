# 配合其他软件使用（不自建服务器）

不想装 dnsmasq / 不想折腾路由器？**把本项目的规则订阅到你手机上已有的软件里就行。**

---

## 一、先确定你的软件支持自定义 URL 订阅

| 软件 | 平台 | 自定义 URL | 用哪个文件 |
|---|---|---|---|
| **AdGuard Home** | 路由器 / NAS / PC | ✓✓ 最标准 | `adguard-dns.txt` |
| **AdGuard for Android** | Android | ✓ | `adguard-dns.txt` |
| **Pi-hole** | 树莓派 / NAS | ✓ | `hosts.txt` 或 `adguard-dns.txt` |
| **AdAway** | Android（需 root） | ✓ | `hosts.txt` |
| **DNS66** | Android | ✓ | `hosts.txt` |
| **Clash / ClashX / Mihomo** | 全平台 | ✓ | `clash-surge-rules.txt` |
| **Surge** | iOS / macOS | ✓ | `clash-surge-rules.txt` |
| **Quantumult X** | iOS | ✓ | `quantumultx-rules.txt` |
| **Loon / Shadowrocket** | iOS | ✓ | `quantumultx-rules.txt` |
| **dnsmasq** | 路由器 / PC | ✓ | `dnsmasq-adblock.conf` |
| **RethinkDNS** | Android | ✗ **不支持** | — |

> **RethinkDNS 特殊**：它的规则只能在官网配置页**勾选预设列表**，不能导入自己的 URL。
> 想用它的话，本列表用不上；请直接选它内置的 anti-AD / 1Hosts 等列表。

---

## 二、订阅地址

```
AdGuard 语法   https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/adguard-dns.txt
hosts          https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts.txt
hosts IPv6     https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts-ipv6.txt
纯域名         https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/domains.txt
Clash/Surge    https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/clash-surge-rules.txt
Quantumult X   https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/quantumultx-rules.txt
```

> 国内访问 `raw.githubusercontent.com` 可能不稳。可选：
> - 用 `https://cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/adguard-dns.txt`
> - 或直接下载文件后本地导入（本项目 `dist/` 目录里就有）

---

## 三、各软件的添加位置

### AdGuard Home ★ 推荐（路由器/NAS 上跑）
```
设置 → 过滤器 → DNS 黑名单 → 添加黑名单 → 填入上面的 adguard-dns.txt URL → 保存
```
加完点「检查更新」，看到规则数上升就成了。

### AdGuard for Android
```
设置 → 内容拦截 → 过滤器 → 自定义过滤器 → 添加自定义过滤器 → 填 URL
```
> 免费版即可用。注意要在「内容拦截」页把总开关打开。

### AdAway（需 root）
```
设置 → 主机源（Hosts sources）→ 添加 → 填 hosts.txt 的 URL → 应用
```

### DNS66（开源免费）
```
Hosts 页 → 添加 hosts 源 → 填 hosts.txt 的 URL → 重启 DNS66
```
> DNS66 已多年未更新，新系统可能有兼容问题；能用则用。

### Pi-hole
```
Settings → Adlists → 粘贴 hosts.txt 或 adguard-dns.txt 的 URL
→ Tools → Update Gravity
```

### Clash / ClashX / Mihomo
把 `clash-surge-rules.txt` 的内容贴进配置的 `rules:` 段，或放进 `rule-providers`：
```yaml
rule-providers:
  homedns:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/clash-surge-rules.txt"
    interval: 86400
    path: ./ruleset/homedns.yaml
```

### Surge
在配置的 `[Rule]` 段：
```
RULE-SET,https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/clash-surge-rules.txt,REJECT
```

### Quantumult X
在 `[filter_remote]` 段：
```
https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/quantumultx-rules.txt, tag=home-dns-adblock, force-policy=reject, enabled=true
```

### dnsmasq
主配置里加一行，然后**重启**（不是 SIGHUP —— SIGHUP 不重读配置文件）：
```conf
conf-file=/path/to/dnsmasq-adblock.conf
```

---

## 四、注意事项

**1. 本列表只管国内 App**
覆盖抖音 / 番茄小说 / 红果短剧 / 小红书 / 高德等的广告与埋点域名。
**不含** Google Ads、DoubleClick 等国外广告域 —— 请另外搭配：
- EasyList、AdGuard Base Filter（国外通用）
- anti-AD（国内通用，覆盖广但误伤率略高）

**2. 别用来路不明的通配规则**
本项目坚持**只加精确域名、不加通配**。通配规则是"App 打不开"的主要元凶。

**3. 拦不掉东西别怪列表**
DNS 层天然拦不了这些（详见 [README 的「已知边界」](../README.md)）：
- 微信朋友圈广告（与好友动态同一 API）
- 淘宝/京东首页推荐流
- 直播中途插播广告（与正片共用 CDN 域名）

**4. 想反馈漏网域名**
抓到新域名欢迎提 Issue，附上「哪个 App、什么场景、域名是什么」。
