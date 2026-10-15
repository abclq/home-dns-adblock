# 实测案例：红果短剧广告（抓包 → 测漏洞 → 补规则）

> 本文是一次**完整闭环的实机验证**：从一台普通安卓手机抓下真实流量，把抓到的域名
> 逐条喂回本项目自己的规则库，**找出规则拦不住的广告域名**，补上，再验证。
>
> **两套规则怎么用**（DNS 用户 / 小火箭用户）在 [第五节](#五补漏结果怎么用两套规则) —— 只关心怎么用的话可以直接跳过去。

---

## 一、结论先行

| 项目 | 结果 |
|---|---|
| 测试对象 | 红果短剧 v7.3.9.32（`com.phoenix.read`，字节/番茄系） |
| 抓包设备 | 努比亚 Z17（NX595J），Android 10，**无 root** |
| 抓到独立域名 | **558 个** |
| 判定为广告/追踪 | 50 个（广告 10 + 追踪 17 + 第三方可疑 23） |
| **原规则拦不住的** | **42 个（漏洞）** |
| 补漏后 | Shadowrocket 规则 **42/42 命中**，dnsmasq 46 条格式零错误 |
| 误伤 | **0**（视频 CDN 白名单自检全通过） |

**最关键的一条发现：**

```
原规则里写的是  log5-applog-hl.fqnovel.com
红果实际用的是  log5-applog-lf.fqnovel.com     ← 只差一个字母
```

同一个服务，**`-hl` 和 `-lf` 是两套不同机房的域名**。规则只写了 `-hl`，
于是这个**出现频率最高（136 次）**的埋点域名**从头到尾没被拦过一次**。

> 这类「差一个字母」的漏是**看规则看不出来的**——规则写得没错，就是没覆盖到。
> 只有**用真实抓包流量去喂规则**才能发现。这正是本文存在的意义。

---

## 二、为什么要做这件事

规则库有两种坏法：

1. **拦错了** —— 把正片 CDN 拦了，用户看不了视频。（本项目已有白名单机制防这个）
2. **没拦住** —— 广告域名压根不在规则里，用户以为拦了，其实一直在跑。

第 2 种更隐蔽：**你从规则文件里看不出任何问题**，规则格式对、语法对、数量也够。
必须**拿真实流量回测**才能暴露。

所以本项目引入一个测试工具：把实机抓到的域名，**逐条喂给自己的规则库**，
输出「哪些域名漏了」。

---

## 三、抓包：怎么拿到一台手机的真实流量

### 为什么不能用代理

第一反应是给手机设 HTTP 代理，**实测行不通**：

```
adb shell settings put global http_proxy 192.168.x.x:8080
→ 代理日志 0 字节
```

**国内 App 普遍无视系统代理**（自己直连 IP + 自带 DoH 绕过）。
`adb root` 是假 root、没有 Magisk su、手机里也没有 tcpdump。

### 可行方案：ARP 双向劫持 + 本机 tcpdump

手机和本机在同一个局域网时，**从网关那一层把手机的流量"骗"到本机来**：

```bash
# ① 双向 ARP 劫持（告诉手机：网关的 MAC 是我；告诉网关：手机的 MAC 是我）
sudo arpspoof -i enp2s0 -t 192.168.x.x 192.168.x.x &
sudo arpspoof -i enp2s0 -t 192.168.x.x   192.168.x.x &

# ② 抓包（只存每包前 500 字节，够拿 DNS 查询名和 TLS SNI，文件小很多）
sudo tcpdump -i enp2s0 -s 500 -w hg3h.pcap host 192.168.x.x

# ③ 抓完必须清干净，否则手机会断网
sudo pkill -x arpspoof
```

**⚠️ 抓包期间，那台手机的所有流量都从本机过。** 抓完一定要恢复，
并告知设备使用者（本项目实测时明确告知过）。

### 坑 ①：Docker 把 `FORWARD` 设成了 `DROP`

劫持装上后**手机直接上不了网**。原因：

```bash
sudo iptables -L FORWARD -n
# Chain FORWARD (policy DROP)      ← Docker 装的，默认全丢
```

**Docker 会把 `iptables` 的 `FORWARD` 链策略改成 `DROP`**，而 ARP 劫持后的流量
正是走 FORWARD 转发的，于是被静默丢弃。

修法（**只放行被劫持的那台设备，别整体放开**）：

```bash
sudo iptables -I FORWARD 1 -s 192.168.x.x -j ACCEPT
sudo iptables -I FORWARD 1 -d 192.168.x.x -j ACCEPT
```

### 坑 ②：`pkill -f` 会把自己杀掉

```bash
pkill -f mitm_capture      # ✗ 会匹配到执行这条命令的 shell 自己，exit -15
```

**改成按 PID 杀，或 `pkill -x`（精确匹配进程名）**：

```bash
pkill -x arpspoof          # ✓ 只杀进程名完全等于 arpspoof 的
```

> 本项目在 `README.md` 的「常用命令」里也记过同一个坑（`pkill -f 'dnsmasq -C ...'`）。
> **凡是 `pkill -f` 里出现「你自己正在跑的那条命令的特征串」，都会自杀。**

---

## 四、关键：怎么区分「广告」和「视频」

抓包只能拿到**域名**，域名本身不写"我是广告"。所以必须有一套判据。

### 判据表（实测总结）

| 特征 | 判定 | 例子 |
|---|---|---|
| `ads*-normal-*.zijieapi.com` | **广告服务** | `ads3-normal-lf.zijieapi.com`（x58，最频繁） |
| `*-ad-sign.byteimg.com` | **广告签名** | `p3-ad-sign.byteimg.com`（x56） |
| `*-mgsdk-sign.byteimg.com` | **广告 SDK 签名** | `p3-mgsdk-sign.byteimg.com` |
| `luckycatopen.*` | **广告投放/活动** | `p1-luckycatopen.byteimg.com` |
| `*-applog-*` / `*-misc-*` | **埋点上报** | `log5-applog-lf.fqnovel.com` |
| `mon.*` / `timon.*` / `thanos.*` | **监控埋点** | `mon.zijieapi.com` |
| `tracking.*` / `dig.*` / `*.beacon.*` | **第三方追踪** | `tracking.miui.com`、`dig.bdurl.net`、`aeventlog.beacon.qq.com` |
| **随机字符串子域** | **广告素材/投放**（子域会轮换） | `713b2cbd.ydycdn.com`、`1957386630.qrstuvwxyzab.com` |
| `pull-flv-*.douyincdn.com` | **视频 CDN，绝不能拦** | （377 个，全是正片流） |
| `*.qznovelvod.com` / `*.fqnovelpic.com` | **视频/图片 CDN，绝不能拦** | |
| `*-sourcecdn.*` / `*pitaya*` / `vcs.*` | **基础设施，别拦** | 配置下发、语音 |

### 三条硬经验

1. **`douyincdn` / `douyinliving` / `.flive.` 全是正片 CDN。** 一开始按"字节系"一刀切
   会误伤 —— 实测这批域名占了 558 个里的 **461 个**，拦了直接看不了视频。

2. **随机子域必须按整个后缀拦。** `713b2cbd.ydycdn.com` 这种子域是**每次请求都换**的，
   只把当前抓到的写进规则，下一分钟就失效。**拦父域 `ydycdn.com` 才有效。**

3. **`-hl` / `-lf` / `-lf3` / `-lf6` 是不同机房，不是同一个域。** 写规则时
   **别只写一个**，要么都写，要么按父域写。

---

## 五、补漏结果：怎么用（两套规则）

### 数据

```
抓到的 558 个域名 → 喂进规则库 → 42 个漏
补漏后自检：
  Shadowrocket 补充规则    42/42 命中  ✅
  dnsmasq 规则             46 条，格式错误 0  ✅
  白名单自检（不能误伤）      ✅ 视频 CDN 全部安全
```

### 补了什么（4 类）

```ini
# ① 埋点（原来 -hl 写成 -lf 全漏，出现频率最高）
log5-applog-lf.fqnovel.com        136 次
rtlog5-applog-lf.fqnovel.com       27
log3-applog-lf.fqnovel.com         27
mon11-misc-lf.fqnovel.com          26
mon3-misc-lf.fqnovel.com

# ② 字节埋点监控
mon.zijieapi.com / timon.zijieapi.com / thanos.zijieapi.com
feedback-c.zijieapi.com / abtest3-misc-hl.zijieapi.com
lf3-static.bytednsdoc.com / lf3-reading.fqnovelstatic.com
lf6-webcastcdn-tos-sign.douyinstatic.com

# ③ 广告 SDK / 投放
seeds-open.comfylink.com / sdktt.data.comfylink.com
ipip-gl1.comfylink.com / cf-gl.comfylink.com
p3-mgsdk-sign.byteimg.com / p9-mgsdk-sign.byteimg.com
p1-luckycatopen.byteimg.com
vc-mirror.ndcpp.com / vc-brain.ndcpp.com
sd-gl.xinqiucc.com

# ④ 随机域名 → 按整个后缀拦（子域会轮换，只拦具体子域没用）
comfylink.com  ndcpp.com  ydycdn.com
qrstuvwxyzab.com  wuchuyun.com  xinqiucc.com
```

---

### 🅰 DNS 用户（dnsmasq / AdGuard Home / Pi-hole / hosts）

**这是本项目作者本人用的方式**：规则只在 **DNS 层**生效，全屋设备自动受益，
不用每台设备装东西。

规则已经合进 `config/adblock-extra.conf`，`scripts/export_lists.py` 会自动
导出成所有格式。**你只需要订阅或重新拉一次规则**：

| 你的环境 | 订阅哪个 | 地址 |
|---|---|---|
| **dnsmasq** | `dnsmasq-adblock.conf` | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/dnsmasq-adblock.conf` |
| **AdGuard Home** | `adguard-dns.txt` | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/adguard-dns.txt` |
| **Pi-hole / 路由器 / AdAway** | `hosts.txt` | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/hosts.txt` |
| **RethinkDNS / SmartDNS** | `domains.txt` | `https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/domains.txt` |

**dnsmasq 生效要点**：

```bash
sudo systemctl restart dnsmasq     # ⚠️ SIGHUP 不重读规则，必须真 restart
```

> 本仓库自带 `dnsmasq-home.service`，用 `sudo systemctl restart dnsmasq-home.service` 更省事。

**优点**：手机、电视、电脑**全都不用装软件**，改一处全家生效。
**缺点**：**只能按域名拦**，拦不住同域名的"广告接口"（比如广告和正片共用一个 API 域名时）。

---

### 🅱 小火箭 / Clash / Surge / Quantumult X 用户

**小火箭（Shadowrocket）用户注意：你要的不是 DNS 那份，是规则集那份。**

本项目**已经导出好了**，不需要自己转换：

| 软件 | 用哪个文件 | 语法样例 |
|---|---|---|
| **Shadowrocket** | `clash-surge-rules.txt` | `DOMAIN-SUFFIX,comfylink.com,REJECT` |
| **Clash / Surge / Stash / Mihomo** | `clash-surge-rules.txt` | `DOMAIN-SUFFIX,comfylink.com,REJECT` |
| **Quantumult X** | `quantumultx-rules.txt` | `host-suffix, comfylink.com, reject` |

**订阅地址**：

```
Shadowrocket / Clash / Surge
https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/clash-surge-rules.txt

Quantumult X
https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/quantumultx-rules.txt
```

**在 Shadowrocket 里怎么加**：

```
配置 → 本地文件（或新建配置）→ [Rule] 段里加一行 RULE-SET 引用：

RULE-SET,https://fastly.jsdelivr.net/gh/abclq/home-dns-adblock@main/dist/clash-surge-rules.txt,REJECT

或者直接「首页 → 配置 → 规则 → 右上角 + → 类型选 RULE-SET」
```

**⚠️ 顺序很重要**：`RULE-SET` 必须放在你的 **`FINAL` 兜底规则之前**，
否则永远匹配不到。本项目作者自己踩过这个坑（见 `docs/pitfalls.md`）。

**⚠️ 还有一条**：如果配置里 `FINAL` 是 `DIRECT`，而你的规则集没覆盖到，
那广告照样跑。**兜底策略和规则集要一起看。**

**优点**：能在**域名 + 连接层**同时拦，比纯 DNS 更彻底。
**缺点**：**每台设备都得单独装**、单独配。

---

### 🅲 两个都用（推荐给「家里有软路由 + 手机也装小火箭」的人）

```
家里（软路由 / 常开小主机）  →  DNS 方案（AdGuard Home / dnsmasq），全屋生效
出门（手机 4G/5G）           →  小火箭，跟着手机走
```

两边吃的是**同一份源规则**（`config/*.conf` → `export_lists.py` → `dist/` 多格式），
所以**不会出现"家里拦得住、出门拦不住"的不一致**。

---

## 六、复现：自己抓一遍

工具在 `~/hg_capture/`（本项目实测用的脚本，非仓库正式脚本）：

| 文件 | 作用 |
|---|---|
| `hg_capture3h.sh` | ARP 劫持 + tcpdump 长时间抓包（只存前 500 字节/包） |
| `hg_keepalive.sh` | 保活：让 App 一直停在播放页，防止跑回主页 |
| `leak_test.py` | **漏洞测试器**：把抓到的域名逐条喂给规则库，输出漏的 |
| `classify.py` | 域名分类（广告/追踪/视频CDN/基础设施/第三方可疑） |
| `hg_leaktest_loop.sh` | 持续测试循环（每 10 分钟重跑一轮） |

**跑一遍漏洞测试**：

```bash
# ① 从 pcap 提域名（DNS 查询 + TLS SNI 都提）
tshark -r hg3h.pcap -Y 'dns.flags.response==0' -T fields -e dns.qry.name \
  | sort | uniq -c | sort -rn > domains.txt

# ② 喂给规则库，看漏了什么
python3 leak_test.py domains.txt
# 输出：每个广告/追踪域名的 [SR=✅/❌漏] [DNS=✅/❌漏] + 出现次数
```

**判读输出**：

```
[追踪] log5-applog-lf.fqnovel.com   SR=❌漏 DNS=❌漏  (x136)   ← 两套都漏，最该补
[广告] 713b2cbd.ydycdn.com          SR=❌漏 DNS=DNS后缀 (x2)   ← DNS 靠后缀拦住了，SR 漏
```

> **`SR=❌漏` 但 `DNS=DNS后缀` 说明**：DNS 方案（按父域拦）已经覆盖，
> 但**小火箭用户拿到的规则集里没有这条** —— 这就是为什么两套要分开看。

---

## 七、踩坑记录（本文新增）

| 坑 | 症状 | 修法 |
|---|---|---|
| Docker 改 `FORWARD=DROP` | 劫持后手机**完全断网** | `iptables -I FORWARD 1 -s/-d <手机IP> -j ACCEPT` |
| `pkill -f mitm_capture` | 命令自己被杀，`exit -15` | 改 `pkill -x arpspoof` 或按 PID 杀 |
| App 无视系统代理 | 代理日志 0 字节 | 改 ARP 劫持，别在代理上耗时间 |
| 只拦具体随机子域 | 规则加完 10 分钟就失效 | 拦**父域**（`ydycdn.com`） |
| `-hl` / `-lf` 混淆 | 规则"看着对"但完全没命中 | 抓包回测，别靠肉眼 |
| 按"字节系"一刀切 | 误伤 461 个正片 CDN 域名 | 严格用第四节判据表，白名单兜底 |

---

## 八、诚实边界

- 本次是**单一 App（红果短剧）+ 单次抓包**的结果，**不代表字节系全部 App**。
  换 App（抖音、番茄小说、今日头条）需要**重新抓、重新测**。
- 抓包**只有 3 小时、一台设备、一个网络环境**。不同地区、不同时段下发的广告域名可能不同。
- **DNS 层拦截有天花板**：同一个域名既服务广告又服务正片时，DNS 拦不了。
  这种情况只能靠小火箭那套（连接层）+ 抓包定位具体接口。
- 随机域名集群（`ydycdn.com` 等）按**整个后缀**拦，**理论上存在误伤可能**。
  如果哪天发现某功能异常，**第一件事是把对应后缀改成只拦具体子域**（回退方法见 `docs/pitfalls.md`）。

---

## 九、相关文档

- [principles.md](principles.md) —— 原理与架构
- [domain-list.md](domain-list.md) —— 域名清单：该拦的 / 绝不能拦的
- [pitfalls.md](pitfalls.md) —— 踩坑全记录
- [use-with-other-apps.md](use-with-other-apps.md) —— 配合其他软件使用（订阅地址大全）
