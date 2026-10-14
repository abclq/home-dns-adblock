#!/usr/bin/env python3
"""生成红果/番茄去广告 dnsmasq 规则（★ 安全模式）

来源：honue/rules、chxm1023/Script_X、anti-AD、秋风广告规则、字节系社区规则

★★ 安全模式（2026-10-13 起）★★
本脚本**绝不覆盖线上规则文件**。原因：线上 adblock-fq.conf 才是唯一真源（手工维护
+ 上游自动同步），而本脚本的源列表只是历史快照。直接覆盖会：
  ① 抹掉手工封的域（tnc3-bjlgy.snssdk.com、webcast5-open-hl.douyin.com、
     wmzfylgdsz.com、v11/v13/v96 三代 reading-ad 等 16 条）
  ② 加回已经手工删掉的误伤域（is.snssdk.com、fqnovelvod.com 裸域等 14 条）
  ③ 把封禁写法从 NXDOMAIN 退回 0.0.0.0（会引发重试风暴）

改成：
  - 结果写到 adblock-fq.generated.conf（独立文件），线上文件一个字节都不动
  - 生成时把线上已有规则**并进来** → 手工加的东西不会丢
  - DEPRECATED 里的域（历史上手工删过的）**排除**，不会再加回去
  - 跑完打印「新增 / 线上独有」差异，人工确认后自己决定要不要采用
"""
import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# 线上真源：优先环境变量 → 仓库 config/ → 本机 dns 目录
_LIVE_CANDIDATES = [
    os.environ.get("LIVE_FQ"),
    os.path.join(HERE, "..", "config", "adblock-fq.conf"),      # 仓库布局
    "/home/wang/.hermes/dns/adblock-fq.conf",                   # 本机布局
]
LIVE = next((p for p in _LIVE_CANDIDATES if p and os.path.exists(p)), None)

# 输出：永远写到独立文件，绝不指向 LIVE
OUT = os.environ.get("OUT_FQ") or os.path.join(HERE, "adblock-fq.generated.conf")

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
    "i.snssdk.com", "i-lq.snssdk.com", "is.snssdk.com",
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

# ⑧ 红果/番茄广告视频域（正片走 qznovelvod 的 *-reading-video，广告走 *-reading-ad）
D.add("fqnovelvod.com")
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

# ⑩ 实机抓包新发现（与 p3-ad-sign 同时出现 → 广告域名组）
D.add("p3-sign.douyinpic.com")
D.add("l2-toutiao-quic-ipv6-ml.gslb.ksyuncdn.com")
for i in range(1, 10):
    for seg in ("hl", "lf", "lq", "zj", "gr", "sg", "hk"):
        D.add(f"minigame{i}-normal-{seg}.zijieapi.com")

# ★ 白名单：绝不能拦（红果正片 / 图床 / 通用视频 CDN / 正常业务）
# 下面这份硬编码只是【兜底】；权威名单是 config/whitelist.txt —— 与上游过滤、文档共用同一份。
# 两份取并集，保证不会因为哪边漏了而误拦。
WL = {
    "qznovelvod.com", "fqnovelpic.com", "douyincdn.com", "douyinliving.com",
    "bytedance.com", "aweme.snssdk.com", "ecombdimg.com", "ecombdapi.com",
    "douyinpic.com", "snssdk.com", "byteimg.com", "ixigua.com",
}
_WL_CANDIDATES = [
    os.path.join(HERE, "whitelist.txt"),
    os.path.join(HERE, "config", "whitelist.txt"),
    os.path.join(os.path.dirname(HERE), "config", "whitelist.txt"),
]
_WL_LOADED = None
for _p in _WL_CANDIDATES:
    if os.path.exists(_p):
        with open(_p, encoding="utf-8") as _f:
            for _l in _f:
                _l = _l.split("#")[0].strip().rstrip(".")
                if _l:
                    WL.add(_l)
        _WL_LOADED = _p
        break
if _WL_LOADED:
    print(f"✓ 白名单 {len(WL)} 条（硬编码 ∪ {_WL_LOADED}）")
else:
    print(f"⚠️ 找不到 whitelist.txt（找过 {_WL_CANDIDATES}），只用硬编码 {len(WL)} 条")

D = {d for d in D if not any(d == w or d.endswith("." + w) for w in WL)}

# 例外：*_reading-ad_* 是广告视频（正片是 *_reading-video_*），必须绕过 qznovelvod 白名单
for v in ("v5", "v6", "v7", "v9", "v26", "v95", "v99", "v100"):
    D.add(f"{v}-reading-ad.qznovelvod.com")
    D.add(f"{v}-bd-daily-reading-ad.qznovelvod.com")
    D.add(f"{v}-se-daily-reading-ad.qznovelvod.com")
    D.add(f"{v}-se-sjy-daily-reading-ad.qznovelvod.com")

# ★★ 已知误伤：历史上手工删掉的域，绝不能再靠生成器加回来
# （这 14 条 = 生成器源列表里有、但线上 adblock-fq.conf 里没有的，即你手工删过的）
DEPRECATED = {
    "is.snssdk.com",                            # 红果风控域，封了红果直接废
    "fqnovelvod.com",                           # 裸域，封了整片全废
    "p3-sign.douyinpic.com",                    # 图床签名域
    "p3-webcast.douyinpic.com",
    "p3-novel-sign.byteimg.com",
    "p6-novel-sign.byteimg.com",
    "p9-novel-sign.byteimg.com",
    "volcengineapi.com",                        # 正常业务 API
    "byteorge.com", "bytegoofy.com",
    "api3-normal-sinfonlinea.fqnovel.com",
    "api5-normal-sinfonlinea.fqnovel.com",
    "lf9-webcast-cdn-tos-ncdn.bytegecko.com",
    "lf-webcast-gr-sourcecdn.bytegecko.com",
}

# 读线上文件：手工规则并进来（保证不丢手工成果）
live = set()
if LIVE:
    with open(LIVE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("address=/"):
                dom = line[len("address=/"):].split("/")[0]
                if dom:
                    live.add(dom)

# 并集 → 手工加的都在；再排除 DEPRECATED（连线上有的一起排除，避免误伤复活）
merged = (D | live) - DEPRECATED

# ★ 输出到独立文件，NXDOMAIN 写法（与线上一致）
with open(OUT, "w", encoding="utf-8") as f:
    f.write("# 红果/番茄去广告规则（dnsmasq）—— 生成建议文件，勿直接当线上用\n")
    f.write("# 来源：honue/rules · chxm1023/Script_X · anti-AD · AWAvenue-Ads-Rule · 字节系社区规则\n")
    f.write(f"# 生成：{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  共 {len(merged)} 条\n")
    f.write(f"# 线上真源：{LIVE or '（未找到）'}\n")
    f.write("# ★ 本文件不覆盖线上规则；确认无误后请手动合并\n")
    for d in sorted(merged):
        f.write(f"address=/{d}/\n")

# ---- 差异报告 ----
only_new = sorted((D - live) - DEPRECATED)          # 生成器想加、线上还没有
only_live = sorted(live - D)                        # 线上有、生成器不知道（手工成果）
revived = sorted(live & DEPRECATED)                 # 线上居然有 DEPRECATED（要留意）

print(f"✓ 生成建议 → {OUT}")
print(f"  线上真源：{LIVE or '（未找到，仅生成）'}")
print(f"  线上 {len(live)} 条 + 生成器 {len(D)} 条 → 并集去重后 {len(merged)} 条")
print(f"  已排除 {len(DEPRECATED)} 个历史误伤域（不会再被加回来）")
print()
print(f"【生成器想新增 {len(only_new)} 条】")
for d in only_new[:40]:
    print(f"  + {d}")
if len(only_new) > 40:
    print(f"  ... 还有 {len(only_new) - 40} 条")
print()
print(f"【线上独有 {len(only_live)} 条】← 你手工加的，已全部保留在生成结果里")
for d in only_live[:40]:
    print(f"  · {d}")
if len(only_live) > 40:
    print(f"  ... 还有 {len(only_live) - 40} 条")
if revived:
    print()
    print(f"⚠️ 线上存在 {len(revived)} 个历史误伤域（已从生成结果排除，请自己确认是否该留）：")
    for d in revived:
        print(f"  ! {d}")
print()
print("★ 线上文件未被修改。确认无误后请手动合并，或直接以线上为准。")
