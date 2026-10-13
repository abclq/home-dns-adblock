# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

## [1.1.2] — 2026-10-13

订阅地址全部改为 **jsDelivr 全球 CDN（`fastly.jsdelivr.net`）** —— 国内直连可用，海外同样快，给大伙一个开箱即用的链接。

### 修复

- **全仓库订阅地址从 `raw.githubusercontent.com` 换成 `fastly.jsdelivr.net`**
  - 原因：GitHub 原始文件地址在国内时通时不通，用户拿到链接经常直接拉不动
  - 涉及 `README.md` / `README.en.md` / `docs/use-with-other-apps.md` / `dist/README.md`
- **修掉文档里推荐的 `cdn.jsdelivr.net` 前缀**（3 处真实配置示例）
  - 实测：`cdn.jsdelivr.net` 国内**连接被重置**；`fastly.` / `gcore.` / `testingcf.` 三个前缀均 200
  - 受影响：Clash 配置示例、Quantumult X 配置示例

### 验证

| 项目 | 结果 |
|------|------|
| 7 个规则文件走 `fastly.jsdelivr.net` | ✓ 全部 200 |
| 三镜像一致性 | ✓ `fastly` / `gcore` / `testingcf` 均 200 |
| `cdn.jsdelivr.net` | ✗ 连接被重置（已在文档中标注避开） |
| 海外访问 | ✓ jsDelivr 为 Cloudflare + Fastly 全球 CDN |

---

## [1.1.1] — 2026-10-11

补漏红果短剧广告域名 —— 修复 issue #1「还是有很多漏网之鱼」。

### 修复

- **补充 `v11` / `v13` / `v96` 三个版本号的 `-reading-ad` 广告子域**（各 4 个变体，共 12 条）
  - 背景：issue #1 指出 `v11-reading-ad` / `v13-reading-ad` 缺失；实测确认这三个主机均真实存在（CNAME 分别指向腾讯云 CDN / 百度云加速 / 阿里云 CDN）
  - 原规则只覆盖 v5/v6/v7/v9/v26/v95/v99/v100，漏了 v11/v13/v96
- 规则总数 **206 → 218 条唯一域名**

### 验证

| 项目 | 结果 |
|------|------|
| 域名实存性 | ✓ `dig` 实测 v11/v13/v96 的 `-reading-ad` 均返回 CNAME |
| 正片白名单 | ✓ 未新增任何 `-reading-video` 相关拦截，零误伤原则保持 |
| 回归 | ✓ 原有 188 条规则零丢失（逐域名集合比对） |

---

## [1.1.0] — 2026-10-05

支持「**只订阅规则**」用法 —— 不想自建服务器的人，把规则喂给已有软件即可。

### 新增

- **`scripts/export_lists.py`** —— 多格式导出器，从三份规则源去重后生成 **214 个唯一域名**
- **`config/adblock-extra.conf`** —— 16 条手工补充规则（埋点统计 + DoH 加固），独立于脚本生成的文件
- **`dist/`** —— 七种现成格式，供第三方软件直接订阅
  - `hosts.txt` / `hosts-ipv6.txt` —— AdAway、路由器固件、DNS66、Pi-hole
  - `adguard-dns.txt` —— AdGuard Home / AdGuard for Android / Pi-hole
  - `clash-surge-rules.txt` —— Clash / ClashX / Mihomo / Surge
  - `quantumultx-rules.txt` —— Quantumult X / Loon / Shadowrocket
  - `domains.txt` —— SmartDNS / mosdns / 自研脚本
  - `dnsmasq-adblock.conf` —— dnsmasq（双栈黑洞）
- **`docs/use-with-other-apps.md`** —— 各主流软件的订阅位置与步骤
- README 顶部新增「两种用法」入口（① 自建 / ② 只订阅）

### 变更

- 规则口径统一为 **214 条唯一域名**（三份来源合计 229 条，含 14 条重复）
- 导出时排除下划线开头的特殊域名（`_dns.resolver.arpa`）—— 第三方工具语法不兼容
- 明确标注 **RethinkDNS 不支持自定义 URL**（只能在官网勾选预设列表）

### 实测记录

| 项目 | 结果 |
|------|------|
| 订阅 URL 外部可达 | ✓ 7 个 URL 全部 HTTP 200 |
| 双栈拦截 | ✓ A → `0.0.0.0`、AAAA → `::`（`address=/domain/#`） |
| 回归测试 | ✓ 正片 / 直播流 / 支付 / 定位 / 苹果证书校验 / iCloud / 微信 / 推送鉴权 全部正常 |

---

## [1.0.0] — 2026-10-05

首个可用版本。方案在真实家庭网络中 7×24 运行，并完成「出门在外」异地实测。

### 新增

- **`config/adblock-fq.conf`** —— 198 条精确域名规则，全部经过实机抓包验证，不含任何宽泛关键字规则
- **`scripts/gen_rules.py`** —— 规则生成器，多社区源合并 + **白名单保护**（防止把正片域名一起拦掉）
- **`scripts/adblock-helper.sh`** —— 抓包速查工具，10 个子命令，核心是 `win N`（按时间戳回溯最近 N 分钟的查询）
- **`scripts/install.sh`** —— 一键部署脚本
- **`scripts/verify.sh`** —— 部署后自检（端口 / 规则 / 日志 / 拦截是否生效）
- **`config/dnsmasq.conf.example`** —— 配置模板，脱敏后可直接使用
- **`config/dnsmasq-adblock.logrotate`** —— 日志轮转，防止长期运行写满磁盘
- **`docs/principles.md`** —— 原理详解（含 Tailscale P2P 打洞、控制面与数据面分离）
- **`docs/domain-list.md`** —— 域名清单：该拦的 vs **绝不能拦的**
- **`docs/pitfalls.md`** —— 踩坑全记录（9 个实际踩过的坑）
- **`docs/tailscale-remote.md`** —— 出门在外方案完整步骤

### 实测记录

| 项目 | 结果 |
|------|------|
| 在家场景 | ✓ 通过（局域网直连 dnsmasq:53） |
| 在外场景 | ✓ 通过（异地 WiFi，Tailscale P2P 直连 39 ms） |
| 规则误伤 | 0（正片 / 图床 / 业务接口全部正常） |
| 资源占用 | 内存 2.5 MB、CPU 0.0% |
| 广告拦截 | ✓ 开屏 / 信息流 / 激励视频广告均加载失败被跳过 |

### 已知限制

- **直播插播广告**拦不住 —— 与正片共用视频 CDN 域名，拦了会连正片一起废
- **已缓存的广告**拦不住 —— DNS 只管"新的解析请求"
- **只验证了 iOS + Ubuntu** —— Android / OpenWrt / 群晖待社区补充
