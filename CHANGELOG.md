# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

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
