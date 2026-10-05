# 配合其他软件使用（不自建服务器）

不想装 dnsmasq、不想折腾路由器？**把本项目的规则订阅到你已有的软件里就行。**

本文按平台给了**下载链接**和**具体添加步骤**，每个都标注了「是否真的能用」——
踩过的坑（比如某个软件其实不支持自定义 URL、某个已经停更）都写在对应条目里，避免你白折腾。

---

## 一、先看结论：我该用哪个？

| 你的平台 | 推荐 | 为什么 |
|---|---|---|
| **软路由 / NAS / 常开小主机** | **AdGuard Home** | 一次配置，全屋设备生效，带 Web 界面和日志 |
| **Android** | **BlockAds** ★ | 免费开源、**支持自定义 URL**、**不用 root**、还在活跃更新 |
| **Android（不想装 App）** | 系统「私人 DNS」 | 只能填 DoH/DoT 服务器地址，**填不了规则文件**，见第四节 |
| **iOS / iPadOS** | **NextDNS 免费档** ★ | iOS 上**唯一免费**的"自定义规则"路径，见第三节 |
| **iOS（愿意付费）** | Shadowrocket / Quantumult X / Loon / Surge | 直接吃规则文件，体验最好 |
| **Windows / macOS 桌面** | **Clash Verge Rev** / **Mihomo Party** | 图形界面，规则用 `rule-providers` 订阅 |
| **树莓派 / Debian 主机** | **dnsmasq** 或 **Pi-hole** | 就是本项目原方案的轻量版 / 带界面的版本 |

> **一句话**：Android 用 BlockAds，iOS 用 NextDNS，软路由用 AdGuard Home，桌面用 Clash Verge。
> 这四条是各自平台上最省事的路。

---

## 二、订阅地址

```
AdGuard 语法   https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/adguard-dns.txt
hosts          https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts.txt
hosts IPv6     https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/hosts-ipv6.txt
纯域名         https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/domains.txt
Clash/Surge    https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/clash-surge-rules.txt
Quantumult X   https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/quantumultx-rules.txt
dnsmasq        https://raw.githubusercontent.com/abclq/home-dns-adblock/main/dist/dnsmasq-adblock.conf
```

### 国内拉不动 `raw.githubusercontent.com` 怎么办

GitHub 的原始文件地址在国内时通时不通。两个办法：

**① 换 jsDelivr 镜像**（实测可用，把 `raw.githubusercontent.com/abclq/home-dns-adblock/main` 换成 `cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main`）：

```
https://cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/adguard-dns.txt
```

**② 直接下载文件导入**：本仓库 `dist/` 目录里就是这些文件，下载到本地再"从文件导入"即可。

> 规则内容：**214 条精确域名**，只针对国内 App 的广告与埋点，**不含通配符**，不会误伤正片。

---

## 三、各软件：下载链接 + 添加步骤

### 🖥 桌面 / 软路由

#### AdGuard Home ★ 最推荐
> 在软路由、NAS 或常开小主机上跑，**全屋设备自动生效**，不用每台设备装东西。

**下载**：
- 官方 Releases：<https://github.com/AdguardTeam/AdGuardHome/releases>
- 官方文档：<https://adguard-dns.io/kb/zh-CN/adguard-home/getting-started/>

**添加**：
```
设置 → 过滤器 → DNS 黑名单 → 添加黑名单
  → 名称填 home-dns-adblock，URL 填 adguard-dns.txt 的地址 → 保存
```
回到列表点「**检查更新**」，看到规则数上升就成了。

**常用**：`过滤器 → 自定义过滤规则` 里能看命中日志，方便排查。

---

#### dnsmasq（本项目原始方案）
> 最轻量，Linux 上一条命令就能跑，适合对资源敏感的设备。

**下载**：系统包管理器自带
```
Debian / Ubuntu:  sudo apt install dnsmasq
OpenWrt:          opkg install dnsmasq  （通常已预装）
macOS:            brew install dnsmasq
```

**添加**：在主配置里加一行，然后**重启服务**：
```conf
conf-file=/path/to/dnsmasq-adblock.conf
```
```bash
sudo systemctl restart dnsmasq     # 注意：SIGHUP 不重读配置文件，必须真重启
```

---

#### Pi-hole
> 树莓派上最流行的方案，Web 界面完善，适合家庭网关。

**下载**：<https://pi-hole.net/>

**添加**：
```
Settings → Adlists → 粘贴 hosts.txt 或 adguard-dns.txt 的 URL → Add
→ Tools → Update Gravity   （必须点这步，否则不生效）
```

---

#### Clash Verge Rev / Mihomo Party（Windows / macOS / Linux）
> 图形界面的 Mihomo 客户端，适合已经在用代理的人顺手加规则。

**下载**：
- Clash Verge Rev：<https://github.com/clash-verge-rev/clash-verge-rev/releases>
- Mihomo Party：<https://github.com/mihomo-party-org/mihomo-party/releases>

**添加**（在订阅配置里加 `rule-providers`）：
```yaml
rule-providers:
  homedns:
    type: http
    behavior: classical
    url: "https://cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/clash-surge-rules.txt"
    interval: 86400
    path: ./ruleset/homedns.yaml

rules:
  - RULE-SET,homedns,REJECT
```

---

#### SmartDNS / mosdns
> 进阶玩家用来做 DNS 分流，本项目只提供纯域名列表。

**下载**：
- SmartDNS：<https://github.com/pymumu/smartdns>
- mosdns：<https://github.com/IrineSistiana/mosdns>

**添加**：用 `domains.txt`（每行一个域名的纯列表），按各自文档挂进黑名单。

---

#### Surge（macOS / iOS，付费）
**下载**：<https://nssurge.com/>

在配置的 `[Rule]` 段加：
```
RULE-SET,https://cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/clash-surge-rules.txt,REJECT
```

---

### 🤖 Android

#### BlockAds: Clean Internet ★ 最推荐
> **免费、开源（GPL-3.0）、不用 root**，明确支持"添加自定义过滤列表 URL"，
> 而且**一直在更新**（2026 年还在发新版）。它是下面 DNS66 停更后最合适的替代。

**下载**：
- F-Droid：<https://f-droid.org/packages/app.pwhs.blockads/>
- 官网：<https://blockads.pwhs.app/>
- 源码（GPL-3.0）：<https://github.com/pass-with-high-score/blockads-android>

**添加**：
```
打开 BlockAds → 授予 VPN 权限（它靠本地 VPN 拦 DNS，不需要 root）
→ 找到「自定义过滤列表 / Custom filter lists」→ 添加 URL → 填 adguard-dns.txt 的地址
→ 打开总开关
```
支持 AdGuard 语法，用 `adguard-dns.txt` 即可。

> 国内访问 raw.githubusercontent 不稳时，用第一节的 jsDelivr 镜像地址。

---

#### AdGuard for Android
> 功能最全，但注意**免费版和付费版的能力边界**（下面写清楚了，避免你装完发现不生效）。

**下载**：
- 官网（含中文说明）：<https://adguard.com/zh_cn/adguard-android/overview.html>
- 直链安装页：<https://adguard.com/zh_cn/adguard-android/install.html>
- 官方对比（免费 vs 付费）：<https://adguard.com/kb/zh-CN/adguard-for-android/features/free-vs-full/>

**添加**：
```
保护 → DNS 保护 → DNS 过滤器 → 添加自定义过滤器 → 填 adguard-dns.txt 的地址
```

**⚠️ 免费版能做 / 不能做**（据官方「免费版和完整版」页面，付费项为：拦截应用内广告、跟踪保护、安全浏览、自定义过滤器和用户规则、用户脚本）：
- ✅ **DNS 保护模块（含 DNS 过滤器）属免费功能** —— 用它做域名拦截可行
- ❌ 「**自定义过滤器和用户规则**」是**付费**项 —— 那指的是 **HTTP 层**的过滤器（拦截网页广告），与 DNS 过滤器是两个入口，别搞混
- ❌ 拦截**应用内**的广告（非浏览器应用）需要付费

> 各版本界面文案有差异，若你的版本里 DNS 过滤器要求激活许可证，以官方对比页为准。

---

#### AdAway
> 经典老牌，但**需要 root**；没 root 别选它，用上面的 BlockAds。

**下载**：
- GitHub Releases：<https://github.com/AdAway/AdAway/releases>
- F-Droid：<https://f-droid.org/packages/org.adaway/>

**添加**：
```
设置 → 主机源（Hosts sources）→ 添加 → 填 hosts.txt 的地址 → 应用
```

---

#### ~~DNS66~~ ✗ 已停更，不要用
> 作者已于 **2026-08-05 将仓库归档**（转为只读），最后一个版本停留在 **2021 年的 0.6.8**，
> 官方标注只支持到 Android 10，新的 Android 版本上能否正常工作没人保证。
>
> **请改用上面的 BlockAds** —— 定位相同（不用 root 的 DNS 层拦截），而且还在维护。

---

### 🍎 iOS / iPadOS

**先说清楚一个现实**：iOS 上**能加载自定义规则文件的 App 基本都是付费的**——
系统不允许免费 App 长期驻留 VPN 做 DNS 过滤。所以 iOS 只有两条路：

#### 方案 A：NextDNS 免费档 ★ 免费的唯一可行路径
> 思路：把本项目规则挂到 NextDNS 的**自定义 Denylist**，拿到一个专属 DoH 地址，
> 再填进 iOS 的「配置 DNS」。全程免费（免费额度足够个人使用）。

**步骤**：
1. 注册 NextDNS：<https://nextdns.io/>（免费档即可）
2. 在配置页找到 **Denylist**，添加本项目 `domains.txt` 或 `hosts.txt` 的地址
3. 记下你的专属地址，形如 `xxxxxx.dns.nextdns.io`
4. iOS：`设置 → 通用 → VPN 与设备管理 → DNS → 添加 DNS 描述文件`，填该 DoH 地址
   （或用免费的 `DNSecure` 之类工具填：<https://apps.apple.com/app/id1519465325>）

> ⚠️ 两点如实说明：
> ① NextDNS 服务器在境外，**国内解析延迟会变高**，不如本机方案快；
> ② 免费档有月度查询量上限，超了会停止过滤。重度使用建议付费档或走方案 B。

#### 方案 B：付费 App（体验最好）
| App | 下载 | 用什么文件 |
|---|---|---|
| **Shadowrocket** | <https://apps.apple.com/us/app/shadowrocket/id932747118> | `quantumultx-rules.txt` |
| **Quantumult X** | <https://apps.apple.com/us/app/quantumult-x/id1443988620> | `quantumultx-rules.txt` |
| **Loon** | <https://apps.apple.com/us/app/loon/id1373567447> | `quantumultx-rules.txt` |
| **Surge** | <https://nssurge.com/> | `clash-surge-rules.txt` |

> Shadowrocket 在**美区** App Store 才有；国区搜不到属正常。
> Quantumult X 在 `[filter_remote]` 段加：
> ```
> https://cdn.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/quantumultx-rules.txt, tag=home-dns-adblock, force-policy=reject, enabled=true
> ```

#### AdGuard for iOS 说明
免费的 AdGuard for iOS **只做 Safari 浏览器内的内容拦截，不能过滤其它 App 的流量**；
要 DNS 层过滤得用**付费的 AdGuard Pro**：<https://adguard.com/zh_cn/adguard-ios/overview.html>

---

## 四、这些"看起来能用"其实要小心

### 系统「私人 DNS」（Android）
`设置 → 网络 → 私人 DNS` 只能填一个 **DoH/DoT 服务器域名**，
**填不了规则文件**。想用它必须自己有个能返回过滤结果的 DNS 服务端。

### RethinkDNS ✗ 不支持自定义 URL
它在官网配置页只能**勾选预设列表**，无法导入自己的 URL。
想用它就选它内置的 anti-AD / 1Hosts 等——本项目的规则喂不进去，**别白费劲**。

### 只做加密解析、不做过滤的工具
`DNSecure`、各种"DNS 切换器"之类，作用是**换 DNS 服务器**或**加密查询**，
必须配合有过滤能力的服务端（见 iOS 方案 A）才有拦截效果。

---

## 五、注意事项

**1. 本列表只管国内 App**
覆盖抖音 / 番茄小说 / 红果短剧 / 小红书 / 高德等的广告与埋点域名。
**不含** Google Ads、DoubleClick 等国外广告域。需要的话另行搭配：
- EasyList、AdGuard Base Filter（国外通用）
- [anti-AD](https://github.com/privacy-protection-tools/anti-AD)（国内通用，覆盖更广但误伤率也更高）

**2. 别用来路不明的通配规则**
本项目坚持**只加精确域名、不加通配**。通配规则是"App 莫名其妙打不开"的主要元凶。

**3. 拦不掉的东西别怪列表**
DNS 层天然拦不了（详见 [README 的「已知边界」](../README.md)）：
- 微信朋友圈广告（与好友动态走同一个 API）
- 淘宝 / 京东 / 拼多多首页推荐流（服务端混排，没有独立广告域名）
- 直播中途插播的广告（与正片共用 CDN 域名，拦了正片也没了）

**4. 发现漏网域名欢迎反馈**
抓到新域名请提 Issue，附上「哪个 App、什么场景、域名是什么」。
最好同时说明**怎么复现**，方便判断它是不是与正片共用域名（那种不能加）。

---

## 六、规则多久更新一次？

本仓库的规则**每 6 小时自动同步一次**（规则变了才产生新提交，没变不会刷版本）。
各软件按各自的更新周期拉取，AdGuard Home / Clash 一般一天内就会拿到最新版。
