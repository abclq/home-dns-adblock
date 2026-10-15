# 抓包方法论：无 root 安卓手机怎么抓 App 域名

> 本文只讲**怎么把流量抓下来、怎么提取域名**。
> 抓到之后怎么判广告、怎么补规则，见 [`redguo-case-study.md`](redguo-case-study.md)。
> 开工前必读 [`for-agents.md`](for-agents.md) 的「铁律」。

---

## 一、为什么不用 mitmproxy

| 做法 | 结果 |
|---|---|
| 手机装 mitmproxy / Charles 证书 | 字节系 App **证书固定（pinning）**，装了也抓不到 |
| **ARP 中间人 + tcpdump**（本文） | 只看 DNS / TLS SNI 明文头部，**不解密也能拿全域名** |

**核心：** DNS 查询名 + TLS SNI 两个字段，就足以还原 App 访问的全部域名。

---

## 二、前置

```bash
# 主机（Debian/Ubuntu）
sudo apt install -y dsniff tcpdump scrcpy tshark
# 手机：开 USB 调试，adb devices 能认出
```

记下三个值：**手机 IP**、**网关 IP**、**主机网卡**（`ip route | awk '/default/{print $5}'`）。

---

## 三、三步

### 1. 起安卓原生虚拟屏 + 启动 App

```bash
# 不占物理屏（安卓原生多显示器，需 Android 10+）
scrcpy --new-display=720x1280 --no-audio &
adb shell am start -n com.phoenix.read/com.dragon.read.pages.main.MainFragmentActivity
```

> 用 `--new-display` 而不是 Xvfb：这是安卓自己的虚拟屏，App 完全无感。

### 2. ARP 劫持 + 抓包

```bash
sudo ./hg_capture.sh /tmp/hg_$(date +%m%d_%H%M).pcap <手机IP> <网关IP> <网卡>
```

脚本做四件事：开 `ip_forward` → iptables 放行该手机 → `arpspoof` 双向劫持 → `tcpdump -s 500`。

**snaplen 500 是刻意的** —— 只存每包前 500 字节，够拿 DNS/SNI，文件小 10 倍。

### 3. 到点自动收尾（**必须跑**）

```bash
(sleep 7200; sudo ./hg_autostop.sh <手机IP> /tmp) &
```

清 `arpspoof`/`tcpdump`/`scrcpy` + 清 iptables。
**不跑收尾 → 手机一直绕经本机 → 用户以为断网。**

---

## 四、提取域名

```bash
# DNS 查询名
tshark -r cap.pcap -T fields -e dns.qry.name \
  | tr ',' '\n' | grep '\.' | sed 's/\.$//' | sort -u > dns.txt

# TLS SNI
tshark -r cap.pcap -Y 'tls.handshake.extensions_server_name' \
  -T fields -e tls.handshake.extensions_server_name \
  | tr ',' '\n' | grep '\.' | sed 's/\.$//' | sort -u > sni.txt

cat dns.txt sni.txt | sort -u > all_domains.txt
```

---

## 五、域名分类（判广告前先分类）

| 类别 | 特征 | 处置 |
|---|---|---|
| App 自家正片 | 播放/图片 CDN | **对白名单，绝不能拦** |
| 广告 | `ad-` / `-ad-` / `ads` / `reading-ad` | 候选拦截 |
| 追踪/埋点 | `log` / `applog` / `tracker` / `report` | 候选拦截 |
| 厂商系统 | 应用商店 / 系统更新 / 安全 | **谨慎，多属误伤区** |
| **可疑第三方** | **随机子域名**、无备案 | 优先排查 |
| CDN/基础 | `gstatic`、`in-addr.arpa` | 忽略 |

**最容易漏的**：随机子域名（如 `xxxxx.v1d.<域名>.com`）——
每次抓包都不一样，**必须列全具体域名**（`address=/x/` 只在标签边界匹配，拦不住父域）。

---

## 六、实测数据（2026-10-15 · 红果）

```
pcap 231 MB · 1,486,213 包 · 内核 0 丢包
独立域名 95（DNS 94 + SNI 71 去重）
分类：App 自家 18 / 字节系 36 / 厂商系统 15 / 可疑第三方 12 / CDN 4 / 其他 10
```

---

## 七、坑

- **手机 ping 不通 ≠ 断网**：运营商常封 ICMP，用 `curl` 测才准
- **脚本别用 `pkill -f`**：会自匹配把自己杀掉 → 用 `pkill -x`
- **收尾必须执行**：ARP 劫持残留 = 手机持续绕经本机
- **snaplen 别调大**：500 够用，1500 文件大 10 倍
- **无 root 别折腾证书**：pinning 拦死，直接走 ARP 中间人
- **抓到 ≠ 能拦**：先对照白名单和 `for-agents.md` 铁律，再决定加不加
