# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式。

## [Unreleased]

### 新增

- **`config/dnsmasq-home.service` —— systemd 单元模板**
  - 原因：文档里一直让人 `systemctl restart dnsmasq-home.service`，仓库却没提供这个单元；
    实际部署时 dnsmasq 静默死掉 **36 小时**无人发现，全屋去广告停摆
  - `Type=forking` + `PIDFile=/run/dnsmasq-home.pid`
  - `ExecStartPre=dnsmasq --test`：配置/规则文件有错就不启动，不会带病上线
  - `Restart=always` + `RestartSec=5` + `StartLimitIntervalSec=0`：死多少次都自动拉起
  - `After=network-online.target tailscaled.service`（没装 Tailscale 时自动忽略）
- **`scripts/install.sh` 支持 systemd**：检测到 systemd → 安装单元 + `daemon-reload` + `enable` + `restart`；
  没有 systemd（OpenWrt 等）→ 回退为裸进程启动

### 修复

- `install.sh` 只拷了 `adblock-fq.conf`，但配置模板还引用 `adblock-extra.conf` / `adblock-upstream.conf` → dnsmasq 直接起不来；现在三个规则文件都会部署
- `install.sh` 原样保留模板末尾的 Tailscale 占位符 `listen-address=100.x.y.z` → 语法错误；现在部署时先注释掉并提示
- `install.sh` 不再 `pkill -x dnsmasq`（会连系统里其它 dnsmasq 实例一起杀掉），改为按配置路径精确找本项目的旧进程
- 文档里「改完规则 `pkill -HUP dnsmasq` 生效」的说法有误：实测 `SIGHUP` 不重读 `conf-file=` 规则，
  统一改为 `sudo systemctl restart dnsmasq-home.service`（README Tailscale 段 / pitfalls / tailscale-remote；principles 补注 SIGHUP 不重读规则）

---

## [1.1.3] — 2026-10-13

一次**仓库自审**驱动的整轮修正 —— 由云电脑上的大模型巡检任务（每天 09:30）扫出 5 类问题，
逐条在本机核实（**全部为真**）后修复。核心是「**文档必须和实际规则一致**」。

### 新增

- **双向自动同步** —— 规则从此有两个来源，各走各的链路：
  - **① 主动同步别人的（主要）**：`GitHub Actions` 每天 04:00（北京时间）拉社区规则
    （AWAvenue / AdRules / anti-AD）→ 解析 AdGuard 语法 → 白名单硬保护 → 写
    `config/adblock-upstream.conf`；家里主机每天 05:00 `git pull`
  - **② 手动同步自己的**：本机实机抓包确认的新广告域，每 6h 推送到本仓库（只推不拉）
  - 上游同步放云端的原因：不依赖家里机器开机、不受家里网络影响
- **云电脑大模型巡检** —— 每天 09:30 让云上的模型读仓库、查文档与规则是否对得上，
  结果投递到 Telegram。**脚本出事实，模型出判断**，规则/白名单/配置的修改一律要人确认。

### 修复

- **`scripts/gen_rules.py` 改为安全模式** —— 原脚本会**直接覆盖线上** `adblock-fq.conf`，
  实跑一次会抹掉 16 条手工规则、加回 14 个已确认误伤的域（`is.snssdk.com`、裸域
  `fqnovelvod.com`、`p3-sign`/`p3-webcast.douyinpic.com` 等）、并把写法退回 `0.0.0.0`。
  现在**只生成 `adblock-fq.generated.conf` 建议文件**，生成时把线上已有规则并进来，
  并新增 `DEPRECATED` 集合永久排除那 14 个误伤域；跑完打印差异。
- **拦截写法统一为 NXDOMAIN** —— `address=/域/#`（回 `0.0.0.0` + NOERROR）会让 App
  拿到地址去连、卡一下才失败；`address=/域/`（空尾，真 NXDOMAIN）直接告知域名不存在。
  实测重试风暴 **12 → 0**。本轮把 `adblock-extra.conf` 16 条 + 主配置 13 条一并统一
  （`adblock-fq.conf` 此前已转）。**`dist/` 导出文件保持 `#` 写法** —— 那是给
  AdGuard / hosts 等第三方工具用的，`0.0.0.0` 是它们的通用写法。
- **清掉笔误死规则 `i-lq-snssdk.com`** —— 把点打成了横杠，真域 `i-lq.snssdk.com` 早已在
  第 60 行。该错域外部 DNS 全部 NXDOMAIN、日志 0 次查询（永不生效），但传染了
  生成器 / 文档 / 导出文件共 5 处，全套清理。
- **`docs/domain-list.md` 按实际规则全面校正（15 处）** ——
  - 禁拦清单原本与 `config/whitelist.txt` 脱节：列了 `bytedance.com` / `aweme.snssdk.com`
    等不在白名单里的，反而漏了 `bytegecko.com` / `apple.com` / `icloud.com` 等 8 个
  - 「白名单例外 · 仍要拦」表里 8 个域实际**早已移除**（`p3-sign.douyinpic.com`、
    `p3-webcast.douyinpic.com`、`p3/p6/p9-novel-sign.byteimg.com`、裸域 `fqnovelvod.com`、
    两个 `bytegecko` 直播域）—— 已从表里拿掉
  - `-reading-ad` 版本号 **8 组 → 11 组**（补 `v11` / `v13` / `v96`），44 条
  - `README.md`「配置模板（改 2 处）」→「改 3 处」
- **同步脚本加「白名单刻意例外」** —— `sync_upstream.py` / `sync_upstream.sh` 原本用后缀
  匹配过白名单，会把 `qznovelvod.com` 下 44 条**刻意穿透**的 `v{N}-*-reading-ad` 规则
  也剔掉。新增 `WL_EXCEPTIONS`（`^v\d+-(bd-daily-|se-daily-|se-sjy-daily-)?reading-ad\.qznovelvod\.com$`）
  **例外优先**，不被白名单剔除。
- **`docs/principles.md` 1.3 整节重写** —— 原文把 `#` 说成 NXDOMAIN、把 `0.0.0.0` 标成
  「推荐」，两个结论都是错的（起临时实例实测三种写法后定论）。

### 文档

- `README.md` 新增「**规则是怎么进来的（双向自动同步）**」章节 + 安全三重门说明
- `config/whitelist.txt` 注明 `-reading-ad` 的刻意例外（原文写「这些域永远不许封」，
  与实际的 44 条穿透规则字面上像自相矛盾）
- 全仓库规则条数口径统一：**精确规则 199 + 16 = 215 条（本机生效）/ 214 条（对外分发，
  故意排除 `_dns.resolver.arpa`）+ 上游社区规则 929 条，去重后合计 1140 条**
- 加 `.gitignore`（忽略 `__pycache__` / `*.pyc` / `*.log` / `*.bak.*` / 生成文件）

### 验证

| 项目 | 结果 |
|------|------|
| `dnsmasq --test` | ✓ 语法检查 OK |
| `dnsmasq-home.service` | ✓ active（systemd 托管，`Restart=always`） |
| 生效规则 | ✓ 1157 条（199+16+929+13），`#` 写法 **0 条** |
| 该拦的域 | ✓ `v5-reading-ad` / `v11-se-sjy-daily-reading-ad` / `ads0-normal-lq.zijieapi.com` 均 NXDOMAIN |
| 该放的域 | ✓ `v11-reading-video.qznovelvod.com` / `is.snssdk.com` / `gecko.snssdk.com` / `pull-f5.flive.douyincdn.com` 均正常解析 |
| 文档一致性 | ✓ 文档里每个域展开后与三份规则文件比对，「说要拦、实际没拦」**0 个** |
| `WL_EXCEPTIONS` | ✓ 44/44 命中；`v5-reading-video` / 裸域 / `evil.qznovelvod.com` / `*.qznovelvod.com.evil.com` 零误命中 |

---

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

## [未发布] 上游规则云同步

- 新增 `.github/workflows/sync-upstream.yml`：GitHub Actions 每天 04:00(北京) 自动拉取社区规则
- 新增 `scripts/sync_upstream.py`：上游列表解析 + 白名单硬保护 + 裸域危险规则剔除
- 新增 `config/whitelist.txt`：15 条保护域（正片/直播流/图床/风控）
- 新增 `config/adblock-upstream.conf`：自动生成的上游规则（默认 929 条，NXDOMAIN 写法）
- 新增 `dist/upstream-domains.txt`：纯域名版，供第三方工具订阅
