# 出门在外也能用 —— Tailscale 方案

**目标**：手机在 4G / 别人家 WiFi 下，DNS 查询仍然送回家里的 dnsmasq，继续吃同一份黑名单。

**成本**：0 元（Tailscale 个人免费版：3 用户 / 100 设备）
**维护**：0（隧道自动重连，规则改动只在本机一处）

---

## 为什么必须用隧道

| 想做的事 | 为什么不行 |
|---------|-----------|
| 手机 DNS 直接填家里公网 IP | 家宽公网 IP **动态变化**；且暴露 53 到公网 = 开放解析器，会被滥用 |
| 用 FRP / 内网穿透把 53 映射出去 | 穿透服务商通常**只给非标准端口**；而 **iOS 的「配置 DNS」只能填 IP，不能填端口** ✗ |
| 用云主机做中间层 | 国内大厂云**默认封禁 53**，解封要域名备案 + 工单 |

**Tailscale 的优势**：给设备分配**虚拟内网 IP**（`100.x.y.z`），
手机不管接哪个网络，都能像在家里一样直接访问 `100.x.y.z:53`。

---

## 完整步骤（四步）

### 第 1 步：家里那台机安装并登录

```bash
curl -fsSL https://tailscale.com/install.sh | sh

# ★ 关键参数：本机是 DNS 提供方，不该消费自己的 DNS
sudo tailscale up --hostname=my-dns --accept-dns=false --accept-routes=false
```

**会打印一个授权链接** —— 在浏览器打开，登录你的账号（Google / Microsoft / GitHub 任选，
**记住用哪个，手机必须用同一个**）。

**完成后记下本机的 Tailscale IP**：

```bash
tailscale ip -4
# 例：100.x.y.z  ← 后面要用
```

**验证**：

```bash
tailscale status
# 应显示本机在线
```

---

### 第 2 步：让 dnsmasq 也监听 Tailscale 地址

```bash
# 追加两行到配置
sudo tee -a /etc/dnsmasq-adblock/dnsmasq.conf > /dev/null <<'EOF'
listen-address=100.x.y.z      # ← 改成你的 Tailscale IP
interface=tailscale0
EOF
```

**★ 必须整进程重启**（`SIGHUP` 对 `listen-address` 无效，见 pitfalls 坑 3）：

```bash
sudo pkill -f "dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf"
sudo dnsmasq -C /etc/dnsmasq-adblock/dnsmasq.conf

# 验证：应该看到两个监听地址
ss -tulnp | grep :53
#  192.168.1.2:53   ← 局域网
#  100.x.y.z:53     ← ★ Tailscale
```

---

### 第 3 步：后台配置 DNS（★ 最容易漏的一步）

打开 https://login.tailscale.com/admin/dns

**① 添加 nameserver**

```
Global nameservers → Add nameserver → Custom
  填：100.x.y.z     ← 你的 Tailscale IP
```

**② 打开「Override local DNS」★★★**

**不开这个 = 全部白配。** 不开的话，你的机器只会被当作 `*.ts.net` 的解析器，
手机查广告域时**根本不会问你的机器**。

**验证**：回到家里那台机，看日志

```bash
tail -f /etc/dnsmasq-adblock/queries.log
# 手机上随便上网，应该能看到查询涌入
```

---

### 第 4 步：手机安装并登录

| 平台 | 操作 |
|------|------|
| **iOS** | App Store 搜 `Tailscale` → 装 → 点登录 → **选和第 1 步同一个登录方式** → 选对账号 → 授权 → **回 App 打开顶部开关** |
| **Android** | Play 商店搜 `Tailscale`（商店没有就用官网 APK）→ 同上 |

**★ 三个必须注意的**：

1. **登录方式必须和第 1 步一致** —— 用 Google 登的就选 Google。
   **选错 = 登到另一个 tailnet = 两台设备根本不在一个网里** ✗
2. **账号要选对** —— 手机上有多个 Google 账号时，一定要选**同一个**
3. **回 App 把开关打开** —— 只在设置里开 VPN 是不够的（见 pitfalls 坑 1）

---

## 验证三板斧

### ① 数据面是否通过（最关键）

在家里那台机跑：

```bash
sudo tailscale status --json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for k,v in (d.get('Peer') or {}).items():
    print(v.get('HostName'),
          '| InMagicSock:', v.get('InMagicSock'),
          '| 最后握手:', v.get('LastHandshake'))
"
```

**合格标准**：`InMagicSock: True` + 有真实握手时间。

### ② 链路是否直连（看快不快）

```bash
sudo tailscale ping <手机主机名>
```

- `pong ... in 39ms` + 日志里 `via=direct` → ★ **P2P 直连，最快**
- 只有 `via DERP` → 走中继了（也能用，延迟高些）

### ③ 拦截是否真的生效

```bash
# 手机上网后，看有没有来自手机 Tailscale IP 的查询
grep "<手机TailscaleIP>" /etc/dnsmasq-adblock/queries.log | tail -10

# 看有没有广告域被黑洞
grep "is 0.0.0.0" /etc/dnsmasq-adblock/queries.log | tail -20
```

**出现 `config xxx is 0.0.0.0` = 拦截生效** ✓

---

## 常见问题

| 现象 | 原因 | 解法 |
|------|------|------|
| 手机显示已连接，但日志里一条查询都没有 | **后台没勾 Override local DNS** | 见第 3 步 ② |
| `InMagicSock: False` | **手机端 App 没真正登录** | 手机上重新登录，注意选对账号 |
| 家里设备突然上不了网 | 本机 `--accept-dns` 没关 | `sudo tailscale up --accept-dns=false` 重跑 |
| 手机连上了但拦截失效 | **手机上其它 VPN 开着** | 只开 Tailscale（iOS 同时只能一个 VPN） |
| 延迟几百毫秒 | 打洞失败走了 DERP 中继 | 通常是运营商 NAT 类型问题，能用就先用 |
| 换了 Tailscale 账号 | **tailnet 重建，虚拟 IP 全变** | 回到第 2 步重配 `listen-address` |

---

## 安全说明

**问：用 Google 账号登录，Google 能看到我的 DNS 查询吗？**

**不能。** 三个层面：

| 角色 | 能看到什么 |
|------|-----------|
| **Google** | 只在**授权那一次**参与（验证"你是你"），之后**完全不在链路里** |
| **Tailscale 服务器** | 只知道「哪两台设备在通信」，**看不到内容**（WireGuard 端到端加密） |
| **DNS 查询内容** | 走加密隧道，而且**打洞成功时是设备间 P2P 直连**，连 Tailscale 服务器都不经过 |

**登录方式（Google / Microsoft / GitHub）只是身份验证方式，与隐私无关。**

**问：Tailscale 免费版够用吗？**

个人免费版：**3 个用户 + 100 台设备**。家庭用绰绰有余。

**问：会不会影响家里网络性能？**

不会。DNS 查询包极小（几百字节），且视频流**不经过**这条隧道 ——
视频是手机直接连 CDN 的。实测本机服务占用：内存 2.5 MB / CPU 0.0%。

---

## 一句话总结

```
在家：手机 WiFi ──► 192.168.1.2:53        （局域网直连，<1ms）
在外：手机任意网 ──► Tailscale 隧道 ──► 100.x.y.z:53  （P2P 直连，~40ms）
                          ↓
                   同一份黑名单 & 同一份日志
```
