# 🏠 home-dns-adblock

**中文** | [English](README.en.md) · `MIT` · `198 条规则` · `零误伤`

**家庭 DNS 广告拦截 —— 7×24 在家跑，出门在外照样生效**

针对国内「看广告换免费内容」类 App（红果免费短剧 / 番茄小说 / 字节系）的 DNS 层广告拦截方案。

> ### 跟 Pi-hole / AdGuard Home 有什么不一样？
>
> 它们解决的是「**通用**广告拦截」，本项目解决的是「**国内特定 App 的零侵入拦截 + 出门在外也生效**」：
>
> | | 通用方案（Pi-hole / AdGuard）| App Hook 方案 | **本项目** |
> |---|---|---|---|
> | 规则数量 | 10 万+ 宽泛规则 | — | **198 条精确规则** |
> | 误伤风险 | 有可能 | — | **零（白名单保护正片）** |
> | 需要 root / 越狱 | 不需要 | **需要** | **不需要** |
> | 出门在外可用 | ✗ | ✗ | **✓ Tailscale 隧道** |
> | 专门针对红果 / 番茄 | ✗ | 有（Hook 路线）| **✓ DNS 层** |
> | 已缓存的广告 | 拦不住 | 能拦 | 拦不住（见「效果边界」）|

**不 root、不装描述文件、不装 CA 证书、不改任何 App** —— 只在一台常开的 Linux 主机上做 DNS 层黑洞。
家里所有设备把 DNS 指过来即可生效；人在外面（4G / 别人家 WiFi）通过 Tailscale 隧道，**同样生效**。

---

## ✨ 效果一览

| 场景 | 做法 | 效果 |
|------|------|------|
| **在家** | 设备 DNS 手填本机内网 IP | 广告域一律答 `0.0.0.0`，广告拉不到数据被跳过 |
| **在外** | 装 Tailscale，登同一账号 | DNS 走加密隧道回家，**4G/异地 WiFi 依然拦截** |

**实测数据**（2026-10，红果免费短剧 + 番茄小说主力场景）

| 指标 | 数值 |
|------|------|
| 规则条数 | 198 条精确域名（无一条宽泛关键字规则） |
| 服务资源占用 | **内存 2.5 MB · CPU 0.0%** |
| 出门链路延迟 | **39 ms（P2P 直连，不走中继）** |
| 异地实测 | 医院 WiFi 下，1431 条 DNS 查询全部回落本机并正常拦截 |
| 误伤 | 0（正片 / 图床 / 业务接口全部放行） |

> 关键词：**红果免费短剧 / 番茄小说 / 去广告 / dnsmasq / DNS 黑洞 / Tailscale / 出门可用**

---

## 🧠 原理（30 秒版）

App 要显示一条广告，第一步必须**解析广告服务器的域名**（查号）。

我们在这一层做手脚：**凡是问广告域的，一律回答 `0.0.0.0`（黑洞地址）** → App 连不上 → 广告加载失败 → 被跳过。

**为什么比拦 IP 聪明**：广告服务器的 IP 天天变，但**域名是固定的**。拦住"查号"这一步，它换多少 IP 都没用。

**为什么比改 hosts 干净**：本方案跑在**独立主机**上，改动不落到任何设备，随时可回退；
设备侧只需把 DNS 指过来，取消也是改一个字段。

---

## 🏗 架构

```
                    ┌──────────────── 在家 ────────────────┐
   手机 / 平板 / 电脑 ── WiFi ──> 192.168.1.2:53 (dnsmasq)
                                              │
                                              ├─ 命中黑名单 → 答 0.0.0.0   ← 广告被黑洞
                                              └─ 其余       → 转发上游 DNS ← 正常上网

                    ┌──────────────── 在外 ────────────────┐
   手机(4G/异地WiFi) ── Tailscale 加密隧道(P2P 39ms) ──> 100.x.y.z:53 (同一份黑名单)
                                                              ↑
                                          管理后台配 Global nameserver
                                          + 打开「Override local DNS」
```

**关键设计**：在家走局域网直连，在外走 Tailscale 隧道 —— **两个入口共用同一份黑名单和同一份日志**，
规则只需要维护一处。

---

## 🚀 快速开始

### 0. 前置条件

- 一台**常开**的 Linux 主机（Ubuntu / Debian / OpenWrt / 树莓派 / 迷你主机均可）
- 主机有**固定内网 IP**（DHCP 静态绑定即可）
- 若要在外面也能用：一个 Tailscale 账号（免费版够用：3 用户 / 100 设备）

### 1. 装 dnsmasq 并灌规则

```bash
sudo apt-get install -y dnsmasq
sudo mkdir -p /etc/dnsmasq-adblock
sudo cp config/adblock-fq.conf /etc/dnsmasq-adblock/          # 198 条现成规则
sudo cp config/dnsmasq.conf.example /etc/dnsmasq-adblock/dnsmasq.conf
```

**改配置里的三处**（`config/dnsmasq.conf.example` 已标注）：

```conf
listen-address=192.168.1.2        # ← 改成你主机的内网 IP
log-facility=/etc/dnsmasq-adblock/queries.log
conf-file=/etc/dnsmasq-adblock/adblock-fq.conf
```

启动：

```bash
sudo dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf
```

> 注意：**dnsmasq 系统服务默认占用 53 端口**，若与系统自带实例冲突，
> 先 `sudo systemctl stop dnsmasq && sudo systemctl disable dnsmasq`（本项目用自己的配置文件手动起）。

### 2. 让设备用上

| 设备 | 操作 |
|------|------|
| **iPhone / iPad** | 设置 → 无线局域网 → ⓘ → 配置 DNS → 手动 → 删掉原有条目，**只留** `192.168.1.2` |
| **Android** | 设置 → 网络 → 私人 DNS（关闭）→ WiFi 详情 → IP 设置 → 静态 → DNS1 填 `192.168.1.2` |
| **Windows** | 网卡属性 → IPv4 → 使用下面的 DNS → 首选 `192.168.1.2` |
| **路由器（推荐）** | DHCP 下发的 DNS 改成 `192.168.1.2`，全屋设备自动生效 |

> ★ **iOS 上只留一个 DNS**，混入 `1.1.1.1` 之类在国内不通的条目会导致断网。

### 3.（可选）出门在外也能用 —— Tailscale

完整步骤见 **[docs/tailscale-remote.md](docs/tailscale-remote.md)**，四步概括：

```bash
# ① 本机安装并登录（会打印授权链接，浏览器点开）
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --hostname=my-dns --accept-dns=false --accept-routes=false

# ② dnsmasq 增加监听 Tailscale 网段
echo "listen-address=100.x.y.z" | sudo tee -a /etc/dnsmasq-adblock/dnsmasq.conf
echo "interface=tailscale0"     | sudo tee -a /etc/dnsmasq-adblock/dnsmasq.conf
sudo pkill -f "dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf"
sudo dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf

# ③ 后台 https://login.tailscale.com/admin/dns
#    添加 nameserver = 100.x.y.z  +  打开「Override local DNS」★

# ④ 手机装 Tailscale，登同一账号，打开开关
```

**★ 三个最容易踩死的坑**（详见 docs/pitfalls.md）：

1. **不勾「Override local DNS」= 白配** —— 手机只在解析 `*.ts.net` 时才会问你的机器
2. **iOS 上「VPN 图标亮着」≠「App 已登录」** —— 账号没登录时数据面完全不工作
3. **iOS 同时只能有一个 VPN** —— 其它翻墙 VPN 开着时 Tailscale 起不来

---

## 📐 规则是怎么来的

**精确域名，绝不使用宽泛关键字。** 这是本方案不误伤的核心。

```bash
python3 scripts/gen_rules.py     # 重新生成 config/adblock-fq.conf
```

规则来源（社区规则集交叉验证 + 实机抓包确认）：

- [honue/rules](https://github.com/honue/rules) — Loon 插件格式
- [chxm1023/Script_X](https://github.com/chxm1023/Script_X) — 过滤规则
- [anti-AD](https://github.com/privacy-protection-tools/anti-AD)
- [AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule)
- 字节系社区规则
- **本机 DNS 日志实机抓包确认**（最关键的一环，见下）

**发现新广告域的工作流**（本项目最实用的部分）：

```bash
# 看到广告的那一刻，记录时间 → 事后从全量日志按时间戳回溯
./scripts/adblock-helper.sh win 3      # 最近 3 分钟的所有查询
./scripts/adblock-helper.sh suspect    # 疑似广告域清单
./scripts/adblock-helper.sh ad         # 已被黑洞拦下的
./scripts/adblock-helper.sh top        # 查询量 Top30
```

广告域的特征：**只在广告出现的那一瞬间被查询，平时完全不出现**。
用这个特征可以把广告域从几百条日志里精准挑出来 → 补进 `gen_rules.py` → 重新生成。

---

## ⚠️ 效果边界（诚实说明，别抱不切实际的期待）

**能拦住的**：广告 SDK 的接口请求、广告计费、点击上报、广告素材签名、小说广告视频 —— 普遍能让广告"加载不出来"而被跳过。

**拦不住的**：

| 类型 | 原因 |
|------|------|
| **直播流插播广告** | 与正片**共用同一个视频 CDN 域名**（`pull-*.douyincdn.com`），拦了正片一起废 |
| **已缓存的广告** | DNS 只拦"新的"解析请求，已经下载到本地的广告照样播 |
| **App 拿到 CNAME 后自行解析** | 日志里表现为 `原域名.<hash>.c.cdnhwc1.com`，绕过黑名单 |
| **DoH / 系统级 VPN** | 客户端改用加密 DNS 或全局 VPN，直接绕过本机 DNS |

**另外**：这套方案让**所有**经过它的设备一起去广告 —— 这是优点（家人零配置），
也是风险（误拦会影响全家）。所以新增规则**必须先在单台设备上验证正片正常**，再全量放开。

---

## 📁 目录结构

```
.
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTORS.md
├── config/
│   ├── adblock-fq.conf            # ★ 现成规则，198 条精确域名
│   ├── dnsmasq.conf.example       # 配置模板（改 3 处即可用）
│   └── dnsmasq-adblock.logrotate  # 日志轮转
├── scripts/
│   ├── gen_rules.py               # 规则生成器（多源合并 + 白名单保护）
│   ├── adblock-helper.sh          # 抓包速查工具（发现新广告域的利器）
│   ├── install.sh                 # 一键部署
│   └── verify.sh                  # 部署后自检
└── docs/
    ├── principles.md              # 原理与架构详解
    ├── domain-list.md             # ★ 域名清单：该拦的 / 绝不能拦的
    ├── pitfalls.md                # ★ 踩坑全记录
    └── tailscale-remote.md        # 出门在外方案
```

---

## 🛠 常用命令

```bash
# 部署自检
./scripts/verify.sh

# 实时看所有设备的 DNS 查询
tail -f /etc/dnsmasq-adblock/queries.log

# 只看被拦下的广告
grep "is 0.0.0.0" /etc/dnsmasq-adblock/queries.log | tail -30

# 某台设备在查什么
grep "from 192.168.1.150" /etc/dnsmasq-adblock/queries.log | tail -50

# 重新生成规则
python3 scripts/gen_rules.py && sudo pkill -HUP dnsmasq

# 回退（配置改动前先备份）
sudo cp /etc/dnsmasq-adblock/dnsmasq.conf.bak /etc/dnsmasq-adblock/dnsmasq.conf
sudo pkill -f "dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf"
sudo dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf
```

---

## 🤝 贡献

欢迎提交**实测有效的新广告域名** —— 这是本项目最有价值的贡献类型。

**提交规则请务必说明**：

1. **触发场景**：哪个 App、什么位置（开屏 / 信息流 / 激励视频）出现的广告
2. **证据**：该域在广告出现**那一刻**是否被查询（DNS 日志片段）
3. **是否误伤**：确认正片 / 图片 / 业务功能正常
4. **只提交精确域名** —— 不接受 `DOMAIN-KEYWORD` 类的宽泛规则

**贡献流程**：Fork → 在 `scripts/gen_rules.py` 里加上你的域名（**并写好注释说明来源**）→
跑 `python3 scripts/gen_rules.py` 重新生成 → 提交 PR 附带实测证据。

**绝不要提交**的域名类型见 [docs/domain-list.md](docs/domain-list.md) 的「禁拦清单」。

---

## 🙏 致谢

本项目站在这些社区规则集的肩膀上：

- [honue/rules](https://github.com/honue/rules)
- [chxm1023/Script_X](https://github.com/chxm1023/Script_X)
- [anti-AD](https://github.com/privacy-protection-tools/anti-AD)
- [AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule)

以及 [Tailscale](https://tailscale.com/) 提供的免费安全组网 —— 让「出门也能用家里 DNS」这件事变得零成本。

完整名单见 [CONTRIBUTORS.md](CONTRIBUTORS.md)。

---

## 📄 License

[MIT](LICENSE)

> 本项目仅供**个人学习与自家网络环境优化**使用。
> 请遵守各 App 的用户协议，在合法合规范围内使用。
