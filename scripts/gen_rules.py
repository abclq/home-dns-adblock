#!/usr/bin/env python3
"""生成红果/番茄去广告 dnsmasq 规则
来源：honue/rules、chxm1023/Script_X、anti-AD、秋风广告规则、字节系社区规则
已剔除会误伤正片的白名单域（qznovelvod / douyincdn / fqnovelpic 等）
"""
import subprocess, datetime

D = set()

# ① 字节广告计费域：ads{0-5}-normal-{线路}
for i in range(6):
    for seg in ("lq", "hl", "lf", "zj", "gr", "sg", "hk"):
        D.add(f"ads{i}-normal-{seg}.zijieapi.com")

# ② 广告签名（图片/小说）
for i in ("3", "6", "9"):
    D.add(f"p{i}-ad-sign.byteimg.com")
    D.add(f"p{i}-novel-sign.byteimg.com")

# ③ 广告计费（小说）
for i in ("3", "5"):
    D.add(f"api{i}-normal-sinfonlinea.fqnovel.com")

# ④ 广告跳转追踪
D.add("dig.bdurl.net")

# ⑤ 穿山甲 SDK（字节广告联盟）
D.update({
    "api-access.pangolin-sdk-toutiao.com",
    "api-access.pangolin-sdk-toutiao1.com",
    "pangolin-sdk-toutiao.com",
    "pglstatp-toutiao.com",
    "pangle.io",
    "ad.toutiao.com",
})

# ⑥ TNC 调度（广告位调度，实机抓包确认 tnc0-aliec2）
for i in range(4):
    for j in ("1", "2", "3"):
        D.add(f"tnc{i}-aliec{j}.zijieapi.com")
        D.add(f"tnc{i}-alisc{j}.zijieapi.com")

# ⑦ 字节广告/统计 SDK（社区规则交叉验证 + 实机抓包确认）
D.update({
    "i.snssdk.com", "i-lq.snssdk.com", "i-lq-snssdk.com", "is.snssdk.com",
    "mcs.snssdk.com", "security-lq.snssdk.com", "vas-lf-x.snssdk.com",
    "activity-ag.awemeughun.com",
    "sf3-ttcdn-tos.pstatp.com",
    "byteorge.com", "bytegoofy.com",
    "msync-im1-vip6-std.easemob.com",
    "apd-pcdnwxlogin.teg.tencent-cloud.net",
    "api.iegadp.qq.com",
    "v6-novelapp.ixigua.com",
    "praisewindow.ugsdk.cn",
    "volcengineapi.com",
})

# 红果/番茄广告视频域（正片走 qznovelvod 的 *-reading-video，广告走 *-reading-ad）
D.add("fqnovelvod.com")
# ★ 关键：广告视频子域统一用 -reading-ad 标记，逐代补全（正片是 -reading-video，不冲突）
for v in ("v5", "v6", "v7", "v9", "v26", "v95", "v99", "v100"):
    D.add(f"{v}-reading-ad.qznovelvod.com")
    D.add(f"{v}-bd-daily-reading-ad.qznovelvod.com")
    D.add(f"{v}-se-daily-reading-ad.qznovelvod.com")

# ⑨ 直播封面/广告位图（webcast 封面图，非直播流本身）
D.update({
    "p3-webcast.douyinpic.com",
    "lf9-webcast-cdn-tos-ncdn.bytegecko.com",
    "lf-webcast-gr-sourcecdn.bytegecko.com",
})

# ⑩ ★ 实机抓包新发现（与 p3-ad-sign 同时出现 → 判定为广告域名组）
D.add("p3-sign.douyinpic.com")
D.add("l2-toutiao-quic-ipv6-ml.gslb.ksyuncdn.com")
for i in range(1, 10):
    for seg in ("hl", "lf", "lq", "zj", "gr", "sg", "hk"):
        D.add(f"minigame{i}-normal-{seg}.zijieapi.com")

# ★ 白名单：绝不能拦（红果正片 / 图床 / 通用视频 CDN / 正常业务）
WL = (
    "qznovelvod.com", "fqnovelpic.com", "douyincdn.com", "douyinliving.com",
    "bytedance.com", "aweme.snssdk.com", "ecombdimg.com", "ecombdapi.com",
    "douyinpic.com", "snssdk.com", "byteimg.com", "ixigua.com",
)
D = {d for d in D if not any(d == w or d.endswith("." + w) for w in WL)}
# 例外：白名单里挂着的具体子域仍然要拦
D.update({"p3-webcast.douyinpic.com", "p3-sign.douyinpic.com",
          "i.snssdk.com", "i-lq.snssdk.com",
          "i-lq-snssdk.com", "is.snssdk.com", "mcs.snssdk.com",
          "security-lq.snssdk.com", "vas-lf-x.snssdk.com",
          "p3-ad-sign.byteimg.com", "p6-ad-sign.byteimg.com", "p9-ad-sign.byteimg.com",
          "p3-novel-sign.byteimg.com", "p6-novel-sign.byteimg.com", "p9-novel-sign.byteimg.com"})
# 例外：*_reading-ad_* 是广告视频（正片是 *_reading-video_*），必须绕过 qznovelvod 白名单
for v in ("v5", "v6", "v7", "v9", "v26", "v95", "v99", "v100"):
    D.add(f"{v}-reading-ad.qznovelvod.com")
    D.add(f"{v}-bd-daily-reading-ad.qznovelvod.com")
    D.add(f"{v}-se-daily-reading-ad.qznovelvod.com")
    D.add(f"{v}-se-sjy-daily-reading-ad.qznovelvod.com")

out = "adblock-fq.conf"
with open(out, "w") as f:
    f.write("# 红果/番茄去广告规则（dnsmasq）\n")
    f.write("# 来源：honue/rules · chxm1023/Script_X · anti-AD · AWAvenue-Ads-Rule · 字节系社区规则\n")
    f.write(f"# 生成：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  共 {len(D)} 条\n")
    f.write("# 白名单保护：qznovelvod(正片) fqnovelpic(图床) douyincdn/douyinliving(正片+直播流)\n")
    for d in sorted(D):
        f.write(f"address=/{d}/0.0.0.0\n")
print(f"✓ {out}  共 {len(D)} 条")
