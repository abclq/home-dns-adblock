# 踩坑全记录

**按"踩坑时有多抓狂"排序。** 每一条都是在真实环境里撞出来的，附诊断命令。

---

## 🔴 一级坑（不知道就必翻车）

### 坑 1：iOS「VPN 图标亮着」≠「App 已登录」

**症状**：手机设置里 VPN 开关是开的、状态栏有 VPN 图标、Tailscale App 显示已连接，
但**数据面完全不工作** —— 家里那台机收不到手机的任何数据包。

**为什么难发现**：iOS 的 VPN 图标反映的是「**配置文件已激活**」，
而**不是**「Tailscale 账号已登录」。账号未登录时，配置照样能激活。

**诊断命令**（在家里那台机上跑）：

```bash
sudo tailscale status --json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for k,v in (d.get('Peer') or {}).items():
    print('设备:', v.get('HostName'))
    print('  InNetworkMap :', v.get('InNetworkMap'))   # 控制面是否知道它
    print('  InMagicSock  :', v.get('InMagicSock'))    # ★ 数据面是否通过
    print('  LastHandshake:', v.get('LastHandshake'))  # ★ 最后握手时间
"
```

**判读**：

| 现象 | 含义 |
|------|------|
| `InNetworkMap: True` + `InMagicSock: False` | ★ **手机从没发过数据包 = 手机端根本没登录** |
| `LastHandshake: 0001-01-01` | 同上，从没握过手 |
| `InMagicSock: True` + 有真实握手时间 | ✓ 正常 |

**解法**：让用户在手机上**重新走一遍登录**（选 Google → 选对账号 → 授权 → 回 App 打开开关）。

---

### 坑 2：Tailscale 后台不勾「Override local DNS」= 全部白配

**症状**：本机配好了、隧道通了、手机也登录了，**但拦截完全不生效** ——
因为手机的 DNS 查询**根本没发到你的机器**。

**原因**：在 `login.tailscale.com/admin/dns` 添加 nameserver **只对 `*.ts.net` 域名生效**。
不打开 **Override local DNS**，手机查 `ads3-normal-hl.zijieapi.com` 时压根不问你的机器。

**验证**（配好后，在家那台机上看日志）：

```bash
grep -c "<手机的Tailscale IP>" /etc/dnsmasq-adblock/queries.log
# 0 → 没生效      >0 且持续增长 → ✓ 生效
```

**★ 这个坑的特点是「一切看起来都正常」** —— 隧道通、ping 通、App 显示连接，
唯一异常就是"广告还在"。**只能靠日志确认**。

---

### 坑 3：`listen-address` 改完，`pkill -HUP` 不生效

**症状**：往 dnsmasq 配置里加了 `listen-address=<新IP>`，
发 `SIGHUP` 让它重载，**新地址死活监听不上**。

**原因**：`SIGHUP` 只重载**规则类配置**（`address=` / `conf-file` 等），
**网络监听地址的变更必须重启整个进程**。

**解法**：

```bash
# ✗ 没用
sudo pkill -HUP dnsmasq

# ✓ 必须整进程重启
sudo pkill -f "dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf"
sudo dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf
```

**验证**：

```bash
ss -tulnp | grep :53
# 应该看到两个监听地址：内网IP:53 和 TailscaleIP:53
```

---

### 坑 4：iOS 的「配置 DNS」只能填一个地址，混入不通的会断网

**症状**：在 iPhone 上手动配 DNS，把 `192.168.1.2` 和 `1.1.1.1` 都填上 →
**手机直接上不了网**。

**原因**：iOS 会**轮询**多个 DNS。`1.1.1.1` / `8.8.8.8` 在国内多数网络下**不可达**，
轮到它时解析超时 → 表现为"网络时好时坏"或彻底断网。

**解法**：**只留一个** —— 本机地址。删掉其它所有条目。

---

## 🟡 二级坑（会多花你半小时）

### 坑 5：系统自带的 dnsmasq 服务抢 53 端口

**症状**：手动起的 dnsmasq 起不来，日志里 `Address already in use`。

**原因**：Debian/Ubuntu 装 dnsmasq 时会自动起一个 `dnsmasq.service`，**它已经占了 53**。

**解法**：

```bash
sudo systemctl stop dnsmasq
sudo systemctl disable dnsmasq     # 防止重启后又回来
# 然后用本项目自己的配置文件手动起（或写成独立 service）
```

**本项目选择"独立配置文件 + 独立进程"**的原因：避免和系统服务打架，
配置改动互不干扰，回退时直接删目录即可。

---

### 坑 6：本机自己不该吃自己的 DNS（`--accept-dns=false`）

**症状**：家里那台机加入 tailnet 后，**自己的 DNS 被改掉了**，可能导致本机解析异常。

**原因**：Tailscale 默认会把 tailnet 的 DNS 配置**应用到本机**。
但本机是**提供 DNS 服务的那一方**，不该消费自己的服务。

**解法**：

```bash
sudo tailscale up --hostname=my-dns --accept-dns=false --accept-routes=false
```

| 参数 | 作用 |
|------|------|
| `--accept-dns=false` | 本机不改 DNS 设置（我是提供方，不是消费方） |
| `--accept-routes=false` | 不接管子网路由（本项目只做 DNS，不做网关） |

---

### 坑 7：iOS 同时只能有一个 VPN

**症状**：手机上装了翻墙 VPN，Tailscale 起不来 / 或者起来了但拦截失效。

**原因**：iOS **同时只允许一个 VPN 处于连接状态**。而且**系统级 VPN 会接管所有 DNS** ——
翻墙 VPN 一开，DNS 查询就绕过你的机器了。

**解法**：要用拦截就**只开 Tailscale**；要翻墙就接受广告回来。
**二者不可兼得** —— 这是 iOS 的系统限制，无解。

---

### 坑 8：测「出门场景」时，没插 SIM 卡的手机测不了 4G

**症状**：想验证"在外面能不能用"，结果手机没插卡 / 只连 WiFi → **测了个寂寞**。

**解法**：
- **用另一台设备开热点**，让目标手机连上去（跟家里网络无关，等同"在外"）
- 或者去外面连别人的 WiFi（本项目就是用**医院 WiFi** 完成异地验证的）

**★ 更严谨的判断方法**：对比手机的**公网出口 IP** 和**家宽的 WAN IP** ——
两个不一样，才说明真的在外面。

```bash
# 家里那台机上，ping 手机时可以观察到对方的出口地址
sudo tailscale ping <手机名>
# 输出里的 via <IP:port> 就是对方的公网出口
# 跟家宽 WAN IP 对比，不同 → 确实在外网
```

---

## 🟢 三级坑（容易忽略但影响长期运行）

### 坑 9：宽泛关键字规则会误伤整个 App

```conf
# ✗ 绝对不要写
address=/ads/0.0.0.0          # 会误伤所有含 ads 的正常域
address=/snssdk.com/0.0.0.0   # aweme.snssdk.com 是抖音核心 API → 功能全废
```

**本项目原则**：**只写精确完整域名**。
宁可规则少（198 条），也不要一条误伤。

**注意 `address=` 的匹配语义**：写 `address=/example.com/0.0.0.0`
**会同时覆盖 `example.com` 及其所有子域** —— 所以写父域极其危险。

---

### 坑 10：白名单必须保护正片（`-reading-ad` vs `-reading-video`）

**症状**：拦了"广告视频"之后，**正片也播不了了**。

**原因**：正片和广告视频**在同一个 CDN 域下**，只有子域前缀不同：

```
正片  v11-reading-video.qznovelvod.com   ← 必须放行
广告  v11-reading-ad.qznovelvod.com      ← 要拦
```

**解法**：把 `qznovelvod.com` 整个加进白名单保护，然后**在代码里显式穿透**
（见 `scripts/gen_rules.py` 的白名单 + 例外逻辑）。

**同理适用于**：
- `douyinpic.com`（图床）→ 只拦 `p3-webcast` / `p3-sign` 这种具体子域
- `byteimg.com`（图床）→ 只拦 `p*-ad-sign` / `p*-novel-sign`
- `snssdk.com`（核心）→ 只拦 `i.` / `is.` / `mcs.` 这种上报子域

---

### 坑 11：DNS 日志不轮转会写满磁盘

**症状**：跑了几个月，磁盘满了 / 日志文件几个 GB。

**原因**：打开 `log-queries` 后，**一部手机刷一小时短剧能产生上万行日志**。

**解法**：`config/dnsmasq-adblock.logrotate` ——
每天轮转、保留 7 天、压缩归档，轮转后发 `SIGUSR2` 让 dnsmasq 重新打开文件句柄。

```bash
sudo cp config/dnsmasq-adblock.logrotate /etc/logrotate.d/
```

**另外**：如果只是想排查问题，可以**临时**开日志，
平时关掉 `log-queries` —— 需要时再开（本项目建议常年开着，因为"抓新广告域"依赖它）。

---

### 坑 11 续：轮转配置写错属主 → 日志静默断掉 ★

**症状**：轮转配置写好了，第一次轮转之后**日志再也不更新**，
但 dnsmasq 进程还在、拦截也还正常 —— **没有任何报错**。

**原因**：用 `create 0644 root root` 重建日志文件，**属主变成 root**，
而 dnsmasq 通常以 `nobody` 运行 → **写不进去，且不会报错**：

```
轮转前: -rw-rw-rw- 1 nobody wang  queries.log   ← dnsmasq 能写
轮转后: -rw-r--r-- 1 root   root  queries.log   ← dnsmasq 写不进去 ✗ 且无报错
```

**这个坑极具欺骗性**：拦截本身照常工作（规则在内存里），
只有"看日志抓新广告域"这个能力悄悄失效了。

**解法**：用 `copytruncate` 代替 `create + postrotate`：

```conf
/etc/dnsmasq-adblock/queries.log {
    su root root
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate          # ★ 原地清空，属主和文件句柄都不变
}
```

**为什么 `copytruncate` 更稳**：把文件截断为 0 字节并归档副本，
**文件本身不变**（inode / 属主 / 权限都不动），dnsmasq 继续往同一句柄写 ——
连 `postrotate` 的重启信号都不需要。

**代价**：截断瞬间理论上可能丢几条日志（对 DNS 日志无所谓）。

**验证轮转是否会正常工作**（debug 模式，不会真轮转）：

```bash
sudo logrotate -d /etc/logrotate.d/dnsmasq-adblock
# 看到 "log does not need rotating" 或 "rotating" 都正常
# 看到 error / 权限相关警告 → 有问题
```

---

### 坑 12：DNS 拦不住的东西，别期待太高

| 现象 | 原因 | 有解吗 |
|------|------|--------|
| 直播插播广告还在 | 与正片**共用视频 CDN 域名** | ✗ 拦了正片一起废 |
| 已经看过的广告还会出现 | 已经**缓存在本地** | ✗ 清缓存可缓解 |
| 日志里出现 `原域名.<hash>.c.cdnhwc1.com` | App 拿到 CNAME 后**自行解析** | ✗ 无法拦 |
| 某些 App 广告照常 | 用了 **DoH / 系统级 VPN** | ✗ 绕过本机 DNS |

**正确的心态**：DNS 拦截是**投入产出比最高**的方案，但**不是万能的**。
它能干掉绝大多数"接口型"广告，干不掉"流媒体型"和"已缓存型"。

---

## 附：一键自检

部署完成后跑 `./scripts/verify.sh`，它会依次检查：

1. dnsmasq 进程是否在跑
2. 53 端口是否在监听（内网 IP + Tailscale IP）
3. 规则文件条数是否正确
4. 广告域是否真的被答 `0.0.0.0`
5. 正常域是否正常解析
6. 日志是否在写入

**6 项全过 = 部署成功。**
