# 域名清单：该拦的 vs 绝不能拦的

> **这份文档比规则文件本身更重要。**
> 规则文件告诉你"拦什么"，这份文档告诉你"**为什么有些看起来像广告的东西绝对不能拦**"。

---

## 一、⚠️ 禁拦清单（白名单，拦了整个 App 就废）

这些域名**看起来**完全符合"广告/CDN"的特征，但它们是**正片、图片、核心业务**的载体：

| 域名 | 实际是什么 | 拦了会怎样 |
|------|-----------|-----------|
| `qznovelvod.com` | 红果/番茄**正片视频** CDN | **整个 App 无法播放** ★ |
| `fqnovelpic.com` | 小说图床 | 封面、插图全部白屏 |
| `douyincdn.com` | 抖音系通用视频 CDN | 直播流断开 |
| `douyinliving.com` | 直播业务 | 直播打不开 |
| `bytedance.com` | 字节母公司域 | 多处业务异常 |
| `aweme.snssdk.com` | 抖音核心 API | 功能大面积异常 |
| `ecombdimg.com` / `ecombdapi.com` | 电商图片 / 接口 | 商城页白屏 |
| `douyinpic.com` | **图床**（图片 CDN） | 页面图片全挂 |
| `snssdk.com` | 核心域名 | 大面积异常 |
| `byteimg.com` | **图床** | 图片全挂 |
| `ixigua.com` | 西瓜视频 | 相关功能异常 |

**为什么 `douyinpic.com` 和 `byteimg.com` 特别危险**：广告素材**和正常图片共用这两个图床** ——
一刀切拦掉，页面所有图片都会消失。只能精确拦**具体的广告子域**（见下节）。

---

## 二、白名单里的「例外」—— 这些具体子域仍然要拦 ★

这是本项目最精妙的设计：**白名单按域名后缀保护，但允许具体子域穿透。**

| 域名 | 为什么拦它 | 为什么它安全 |
|------|-----------|-------------|
| `v{5,6,7,9,26,95,99,100}-reading-ad.qznovelvod.com` | **广告视频** | 正片走 `*-reading-**video**`，是**不同子域** ★ |
| `p3-webcast.douyinpic.com` | 直播封面广告位图 | 不是直播流本身（流走 `douyincdn`） |
| `p3-sign.douyinpic.com` | 广告素材签名 | 图床上的一个特定子域 |
| `p3/p6/p9-ad-sign.byteimg.com` | **广告图片签名** | 图床上的特定子域 |
| `p3/p6/p9-novel-sign.byteimg.com` | **小说广告签名** | 同上 |
| `i.snssdk.com` / `is.snssdk.com` / `mcs.snssdk.com` | 广告上报 / 归因 | 不是 `aweme.snssdk.com` 那种核心 API |
| `i-lq.snssdk.com` / `i-lq-snssdk.com` | 同上 | 同上 |
| `security-lq.snssdk.com` / `vas-lf-x.snssdk.com` | 风控 / 广告相关 | 同上 |

### ★ 最值得学习的一条

```
正片视频  →  v11-reading-video.qznovelvod.com    ← 放行
广告视频  →  v11-reading-ad.qznovelvod.com       ← 拦截
                    ↑↑↑
                 一字之差
```

**怎么发现这个规律的**：广告出现时抓 DNS 日志，发现 `*-reading-ad` 与广告计费域
（`ads*-normal-*`）**在同一秒被查询**；而正片播放时只有 `*-reading-video`。

**这个发现是整套规则的核心** —— 它让"拦广告视频"和"保正片"得以同时成立。

---

## 三、✅ 该拦清单（198 条，按类别）

### 3.1 广告计费接口（最典型）

```
ads{0-5}-normal-{lq,hl,lf,zj,gr,sg,hk}.zijieapi.com        ← 42 条
```
- `ads` = 广告服务；数字 = 版本；`-normal-` = 正式环境；后缀 = 接入线路（阿里/火山/自建等）
- **拦掉它 = 广告请求发不出去** ★

### 3.2 广告素材签名

```
p{3,6,9}-ad-sign.byteimg.com          ← 广告图片签名
p{3,6,9}-novel-sign.byteimg.com       ← 小说广告签名
```
签名校验不通过 → 素材无法加载 → 广告空白被跳过

### 3.3 小说广告计费

```
api{3,5}-normal-sinfonlinea.fqnovel.com
```
`sinfonlinea` = 统计/计费在线服务。**拦了它广告照样能显示但拿不到钱**，
配合其它规则一起用效果最好。

### 3.4 点击跳转追踪

```
dig.bdurl.net
```

### 3.5 穿山甲 SDK（字节的广告联盟，很多第三方 App 在用）

```
api-access.pangolin-sdk-toutiao.com
api-access.pangolin-sdk-toutiao1.com
pangolin-sdk-toutiao.com
pglstatp-toutiao.com
pangle.io
ad.toutiao.com
```

### 3.6 广告位调度（TNC）

```
tnc{0-3}-aliec{1,2,3}.zijieapi.com     ← 阿里云线路
tnc{0-3}-alisc{1,2,3}.zijieapi.com     ← 阿里云线路
```
`tnc` = Traffic Network Controller，负责决定"这个位置放哪条广告"

### 3.7 广告视频（★ 见第二节）

```
fqnovelvod.com                                          ← 整个广告视频域
v{5,6,7,9,26,95,99,100}-reading-ad.qznovelvod.com
v{5,6,7,9,26,95,99,100}-bd-daily-reading-ad.qznovelvod.com
v{5,6,7,9,26,95,99,100}-se-daily-reading-ad.qznovelvod.com
v{5,6,7,9,26,95,99,100}-se-sjy-daily-reading-ad.qznovelvod.com
```

### 3.8 直播封面广告位图

```
p3-webcast.douyinpic.com
lf9-webcast-cdn-tos-ncdn.bytegecko.com
lf-webcast-gr-sourcecdn.bytegecko.com
```
`webcast` = 直播；**注意这里拦的是"封面/广告位图"，不是直播流** ——
直播流走 `douyincdn.com` / `douyinliving.com`，在白名单里。

### 3.9 统计 / 归因 SDK

```
i.snssdk.com  ·  is.snssdk.com  ·  mcs.snssdk.com
i-lq.snssdk.com  ·  i-lq-snssdk.com
security-lq.snssdk.com  ·  vas-lf-x.snssdk.com
activity-ag.awemeughun.com
sf3-ttcdn-tos.pstatp.com
```

### 3.10 实测新发现（社区规则里没有，抓包确认）

```
p3-sign.douyinpic.com                            ← 与 p3-ad-sign 同时出现
l2-toutiao-quic-ipv6-ml.gslb.ksyuncdn.com
minigame{1-9}-normal-{lq,hl,lf,zj,gr,sg,hk}.zijieapi.com   ← 小游戏广告位 63 条
```

### 3.11 其它

```
praisewindow.ugsdk.cn            ← 激励视频/弹窗 SDK
v6-novelapp.ixigua.com           ← 小说 App 相关
byteorge.com  ·  bytegoofy.com
msync-im1-vip6-std.easemob.com
apd-pcdnwxlogin.teg.tencent-cloud.net
api.iegadp.qq.com
volcengineapi.com
```

---

## 四、命名规律速查表（用于预判新域）

发现新域名时，**先对照这张表判断**，再去日志里确认：

| 域名里出现 | 大概率是 | 建议 |
|-----------|---------|------|
| `ads{数字}` | **广告接口** | ✓ 拦 |
| `-ad-sign` / `-novel-sign` | 广告签名 | ✓ 拦 |
| `sinf` | 统计/计费 | ✓ 拦 |
| `-sign.` | 签名校验 | ⚠️ 需确认是广告还是正片 |
| `pangolin` / `pangle` | 穿山甲广告 SDK | ✓ 拦 |
| `praisewindow` | 激励视频弹窗 | ✓ 拦 |
| `bdurl` | 百度统计跳转 | ✓ 拦 |
| `tnc{数字}` | 广告位调度 | ✓ 拦 |
| `-webcast-` | 直播相关 | ⚠️ **看清是图还是流** |
| `-reading-video` | **正片视频** | ✗ **绝不能拦** |
| `-reading-ad` | **广告视频** | ✓ 拦 |
| `pic` / `img` / `photo` | 图床 | ✗ 极度危险，只能精确拦子域 |
| `vod` / `cdn` / `live` | 视频/直播流 | ✗ 极度危险 |
| `api` / `aweme` | 核心 API | ✗ 极危险 |

---

## 五、新增规则的验证流程（必走）

```
① 在日志里找到该域被查询的**时间点**
     └─ 用 ./scripts/adblock-helper.sh win 3 切出广告出现的时间窗

② 确认它**只在广告时刻出现**
     └─ 正片播放时查不到它 → 安全

③ 加进 scripts/gen_rules.py，写好注释说明来源

④ 重新生成 + 重载
     └─ python3 scripts/gen_rules.py && sudo pkill -HUP dnsmasq

⑤ ★ 先在**一台设备**上验证正片正常播放
     └─ 播放 3 分钟以上，确认不卡不断

⑥ 确认无误后，全屋生效
```

**第 ⑤ 步不能省** —— 因为这套方案是"全屋共用一份规则"，
一条错误的规则会让**所有设备**一起出问题。
