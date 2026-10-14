# 给机器人/协作者的作业说明

> **这份文档是写给 AI 机器人（和未来的自己）看的，不是写给终端用户看的。**
> 用户向的说明在 `README.md`；原理在 `docs/principles.md`；踩坑在 `docs/pitfalls.md`。
>
> **开工前必读这一份。** 里面每一条「铁律」都是踩过坑换来的，违反会直接搞挂全家 DNS。

---

## 一、这个项目是什么

把**家里 dnsmasq 的广告拦截规则**做成一个可复用、可订阅、自动同步的开源仓库。
核心价值不是「规则条数多」，而是**「知道什么绝对不能拦」** —— 见 `docs/domain-list.md`。

主战场是中文 App（红果短剧 / 番茄小说 / 抖音系），字节系域名极易误伤。

---

## 二、三方布局（先搞清楚谁是谁，别改错地方）

- **本机（权威）** `/home/wang/.hermes/dns/` —— 实际生效的 dnsmasq 配置。人工 + 本机 cron 可改
- **GitHub 仓库** `abclq/home-dns-adblock` —— 对外分发源。人工 + 两条自动化可改
- **云端 Actions** `.github/workflows/sync-upstream.yml` —— 每天 04:00 生成上游规则。只有云上可改

**本机目录关键文件**

```
dnsmasq.conf            主配置（含少量内嵌规则 + conf-file 引入三个规则文件）
adblock-fq.conf         红果/番茄系手工规则（199 条）—— 主要维护对象
adblock-extra.conf      手工精挑补充（37 条）
adblock-upstream.conf   上游同步（928 条）⚠️ 云生成，本机只拉不推
whitelist.txt           白名单（15 条硬保护）
queries.log             查询日志 —— 排查误封的第一证据源
gen_rules.py            ⚠️ 历史快照生成器，已改安全模式，别当「重新生成规则」用
```

**服务形态**：`dnsmasq-home.service`（systemd 托管，`Restart=always`，开机自启）
监听 `192.168.31.88:53` + `100.120.42.82:53`（Tailscale，给手机在外用）

**当前条数基线**（改完拿这个对）：`fq 199 / extra 36 / upstream 929（本机）· 928（仓库）/ dnsmasq.conf 内嵌 13`

---

## 三、🔴 铁律（违反直接出事故，没有例外）

### 3.1 绝不能拦的东西

- **禁止封裸域**：`.zijieapi.com`、`.snssdk.com`、`.fqnovelvod.com` 这种「封整个主域」会让字节系 App 全废
- **白名单 15 条硬保护**：正片流 / 直播流 / 图床 / 风控 / 基础设施 —— 改上游同步时 `BARE_FORBIDDEN` + 白名单必须过
- **具体禁拦清单**（历史误封，勿加回）：`fqnovelvod.com`（正片 CDN 主域）、`p3/p6/p9-novel-sign.byteimg.com`（正片签名，**广告是 `ad-sign`，一字之差**）、`api3/api5-normal-sinfonlinea.fqnovel.com`（反作弊，拦了 App 功能异常）、`is.snssdk.com`、`volcengineapi.com`、`bytegecko.com`、`douyinliving.com`
- **`gecko.snssdk.com` 必须保护** —— 那是字节 H5 离线包系统，封了红果可能白屏
- 判据：`ad-` / `-ad-` / `ads` / `reading-ad` 才是广告；`novel-sign` / `sinfonlinea` / `is.snssdk` 是正片签名与风控

### 3.2 写法铁律

- **封禁一律用 NXDOMAIN = `address=/X/`（空尾）**。实测对照（dnsmasq 2.90）：

  ```
  address=/X/0.0.0.0  → 只拦 A，AAAA 转发真实值，NOERROR
  address=/X/#        → 双栈黑洞，NOERROR     （旧文档说它=NXDOMAIN，是错的）
  address=/X/         → A/AAAA 均无，NXDOMAIN  ★ 用这个
  ```

- **`dist/hosts.txt` 例外**：必须写 `0.0.0.0 域名`（hosts 格式要求 IP），不改
- **`address=/x/` 只在「标签边界」匹配**：`address=/applog-lf.fqnovel.com/` 拦不住 `log5-applog-lf.fqnovel.com`（中间是 `-` 不是 `.`）→ **跨标签必须列全域名**
- **封域要连 CNAME 真身一起封**：封了 `webcast5-open-hl.douyin.com`，App 会直接去问 `webcast5-open-hl.douyin.com.c.dsa.cdnbuild.net`，规则不匹配 → 绕过。
  排查：`grep -A2 '<被封域>' queries.log` 看 CNAME 指向哪

### 3.3 改文件的铁律

- **绝不用 `write_file` / `>` 覆盖已有文件** —— 先 `read_file` 看内容再增量改。
  （踩过：把 21 行 `.gitignore` 覆盖成 3 行，丢掉 `*.log` / `*.bak.*`，一堆备份文件变待提交）
- **增量改规则：只插入，绝不整文件重排**。注释是贴在对应规则旁边的，`sorted(整个文件)` 会把注释全挤到文件头，语义丢失

  ```python
  out=[]; ins=set()
  for line in lines:
      if line.startswith('address='):
          for r in new:                  # new 已排序
              if r not in ins and r < line:
                  out.append(r); ins.add(r)
      out.append(line)
  for r in new:                          # 兜底：比所有现存规则都大的追加末尾
      if r not in ins: out.append(r)
  ```

- **行级正则不能用 `re.sub(r'/#\s*$', ...)`** —— `\s*$` 会吃掉换行符，相邻行粘成一行 → `Bad address in --address at line N`
- **`gen_rules.py` 是历史快照，绝不能让它覆盖线上**（已改安全模式：只写 `adblock-fq.generated.conf`，线上文件一字节不动）

### 3.4 进程管理铁律

- **千万别用 `pkill -f 'dnsmasq -C ...'`** —— 会匹配到整个命令行、连自己那条 `pkill`/`sudo` 一起杀，53 端口裸奔
- 同样**别用 `pkill -f "agent-tars serve"` / `pkill -f "xxx.py"`** —— 命令串含该名就杀自己 shell（exit -15）。
  用括号写法：`pgrep -af "[m]ine_image_full"`
- **重启只能 `sudo systemctl restart dnsmasq-home.service`**
- **`pkill -HUP dnsmasq` / `systemctl reload` 都是假动作** —— `man dnsmasq` 原话：**"SIGHUP does NOT re-read the configuration file."**
  `address=` 规则**只能靠 restart 生效**
- 找进程只信 `pgrep -x dnsmasq`（`pgrep -f` 会连当前 bash 一起返回）

### 3.5 数字铁律

- **条数只信 `grep -c '^address='`**，别信文件头的注释（实测头写 198、实际 188）
- **`grep -c 'address=/p3-sign.douyinpic.com/'` 会误报** —— 被注释掉的行也含该串。判断生效用 `grep -Fxc "address=/<域>/"` 或直接建集合比对

---

## 四、同步链路（两条，别搞混）

### ① 主动同步别人的（云上跑，不依赖家里开机）

```
GitHub Actions 每天 04:00(北京)  →  .github/workflows/sync-upstream.yml
   └ scripts/sync_upstream.py：拉 AWAvenue-Ads-Rule → AdGuard 语法解析
     → whitelist.txt 白名单硬保护 → 写 config/adblock-upstream.conf + dist/upstream-domains.txt → commit
本机 cron 每天 05:00（job d806a99f31b5）→ pull_upstream_rules.sh：git pull → 比对 → 语法门 → 重启 → 验白名单
```

- 列表选型：**AWAvenue-Ads-Rule（958 条）** 专治中文 App、无裸域规则、质量高
- AdRules(20万) / anti-AD(11万) **太激进，别整包合**
- 兜底：`~/.hermes/dns/sync_upstream.sh` 可直连上游生成（GitHub 不通时用）

### ② 手动同步自己的（本机 → 仓库）

```
本机 cron 每 6h（job 9e6d54943c55）→ sync_adblock_repo.sh
   ├ 推 adblock-fq.conf + adblock-extra.conf + whitelist.txt → config/
   ├ 重跑 export_lists.py 重生 dist/
   ├ 不推 adblock-upstream.conf（云端拥有，避免互盖）
   └ 无变化 → 完全静默（no_agent）
```

**⚠️ 改完本机别等下一班 6h**，当天手动跑一次：`/home/wang/.hermes/scripts/sync_adblock_repo.sh`

**⚠️ 2026-10-14 修过的坑**：云端 Actions 会往仓库推 `adblock-upstream.conf`，本机直接 push 会被
`! [rejected] ... (fetch first)` 拒绝。脚本已加**自动 rebase 重推**；真冲突才报错退出（不硬覆盖）。

---

## 五、改规则的标准流程（照做，别跳步）

```bash
# 1. 备份（带时间戳）
cp ~/.hermes/dns/adblock-extra.conf ~/.hermes/dns/adblock-extra.conf.bak.$(date +%Y%m%d-%H%M%S)

# 2. 改（只插入，见 3.3）
#    ...

# 3. 语法门（不过就别重启）
sudo dnsmasq --test -C /home/wang/.hermes/dns/dnsmasq.conf     # 必须 "syntax check OK"

# 4. 重启（只有 restart 生效）
sudo systemctl restart dnsmasq-home.service
systemctl is-active dnsmasq-home.service                        # active

# 5. ★ 双向验证 —— 只证明"新规则生效"不够，必须同时证明"没误伤"
dig +short @192.168.31.88 <新拦的域>        # 必须 NXDOMAIN（+short 为空）
dig @192.168.31.88 <白名单正片域>           # 必须 NOERROR（如 v5-reading-video.qznovelvod.com）

# 6. 三方一致性核对（本地 / 仓库 / 生效）
for f in adblock-fq.conf adblock-extra.conf whitelist.txt; do
  printf '%-22s 本地 %s 仓库 %s\n' $f \
    "$(grep -c '^address=' ~/.hermes/dns/$f)" \
    "$(grep -c '^address=' /home/wang/projects/home-dns-adblock/config/$f)"
done

# 7. 同步仓库
/home/wang/.hermes/scripts/sync_adblock_repo.sh
```

**白名单域回 NXDOMAIN 时先别慌**：用 `dig +short @223.5.5.5 <域>` 对比外部 DNS，
若外部也是 NXDOMAIN，说明这域本来就不存在（如 `www.qznovelvod.com`），不是你拦的。

---

## 六、排查误封（用户报「XX 加载不出 / 又弹广告」）

### 第一步永远是：先确认服务还活着 ⚠️

**不要先怀疑「广告商换了新域名」** —— 先查服务在不在：

```bash
pgrep -ax dnsmasq || echo '❌ 服务没在跑'
ss -lunp | grep '192.168.31.88:53'                          # 没有监听 = 没跑
ls -l --time-style=+%m-%d\ %H:%M ~/.hermes/dns/queries.log   # 0 字节 = 服务没在写
```

**实证**：2026-10-12 13:31 dnsmasq 静默死掉（无 OOM、无 journald 记录），到 10-13 20:05 用户报
「红果弹广告」时已停摆 **36 小时**。**日志停写时间 = 死亡时间**，这是最快的定位法。
（根因：手动进程没人看管 → 已改 systemd `Restart=always` 根治）

自愈验证法：`OLD=$(systemctl show -p MainPID --value dnsmasq-home.service); sudo kill -9 $OLD; sleep 8; systemctl show -p MainPID --value dnsmasq-home.service` —— PID 变了且 active = 生效。

### 第二步：查日志

```bash
# ★ 只抓 config 前缀 = 我们自己拦的；reply 前缀 = 上游说这域名不存在（正常，不算拦截）
grep 'config .* is NXDOMAIN' ~/.hermes/dns/queries.log | sed -E 's/.*config ([^ ]+) is .*/\1/' | sort | uniq -c | sort -rn
# 再看有没有可疑的「正片域」被拦
grep 'config .* is NXDOMAIN' ~/.hermes/dns/queries.log | sed -E 's/.*config ([^ ]+) is .*/\1/' | grep -iE 'vod|video|cdn|novel|sign'
```

- 客户端 IP：手机 = `192.168.31.150`
- **`config` vs `reply` 前缀必须分清** —— 巡检脚本抓 `reply` 会一条都抓不到

### 第三步：「卡一下」不是 DNS 问题

卡顿真因是 App 启动流程「先要广告 → 广告被拦 → **等自己内部超时** → 才渲染内容」——
**这是去广告的固有代价，DNS 层解决不了**。别瞎调 `dns-forward-max`（A/B 实测无实质差别）。
DNS 健康度实测：单查询中位 25ms，并发 300 最慢 361ms。

---

## 七、我们干过什么（时间线 · 关键决策）

> 记这个是为了**别重复踩坑、别推翻已定的决策**。改之前先看这里有没有先例。

### 2026-10-05 建库

- 从本机 `queries.log`（238,094 行 / 1,991 个唯一域名）精挑出「上报/统计/追踪」类，手工补 16 条
- 定下加规则原则：**只取上报/统计/追踪，绝不碰播放/支付/定位/系统服务/云基础设施**

### 2026-10-06 红果误封事件（最重要的教训）

- 红果视频加载不出，用户换 WiFi 即好 → **实锤规则误伤**
- 误封清单（已删，勿加回）：`fqnovelvod.com`、`p3/p6/p9-novel-sign.byteimg.com`、
  `api3/api5-normal-sinfonlinea.fqnovel.com`、`is.snssdk.com`、`bytegoofy.com`、`byteorge.com`、`volcengineapi.com`
- **产出 `docs/domain-list.md`** —— 「该拦的 vs 绝不能拦的」，比规则文件本身更重要
- 注：`hongguo.com` 在公网 5 家 DNS 全部查不到（域名本身不存在），别把它当误封嫌疑

### 2026-10-13 大修一轮（8 个提交）

1. **全库写法统一为 NXDOMAIN**（原来混用 `0.0.0.0` / `#`）—— 实测 `#` 写法导致 App 撞墙重试 **12 次/500 行日志**，改 NXDOMAIN 后 **0 次**
2. **dnsmasq 静默死 36h** → 改 systemd `Restart=always` 根治；`StartLimitIntervalSec=0` 写进 `[Unit]` 段（写 `[Service]` 段会被静默忽略）
3. **`gen_rules.py` 改安全模式** —— 原脚本会抹掉手工 16 条 + 加回 14 条误伤 + 退回 `0.0.0.0`
4. **上游同步上云**（Actions 每天 04:00，不依赖家里开机）
5. **白名单过滤加「刻意例外」** —— 不再误剔 `*-reading-ad` 规则
6. **修 `domain-list.md` 15 处与实际不符**
7. **恢复被误覆盖的 `.gitignore`**
8. **修 `pkill -f` 自相矛盾 + 清理笔误死规则 `i-lq-snssdk.com`**

### 2026-10-14 红果短剧实测补漏

- **方法**：一台普通安卓手机 + ARP MITM 双向劫持，抓 **3 小时**真实流量 → 域名逐条喂回规则库比对 → 补漏
- **产出 `docs/redguo-case-study.md`**（完整闭环案例）+ `config/adblock-extra.conf` 补 16 条
- **发现「跨标签」坑**：`address=/applog-lf.fqnovel.com/` 拦不住 `log5-applog-lf.fqnovel.com`（中间是 `-`）
- **新增随机子域广告 CDN**：`ydycdn` / `wuchuyun` / `xinqiucc` / `qrstuvwxyzab` / `wmzfylgdsz`（整后缀拦）
- **⚠️ 勘误（17:20 复核）**：初版提交说「`-hl` 是误写、全部失效」—— **这是错的**。
  公网实测 `log5-applog-hl.fqnovel.com` 真能解析（且**非泛解析**，假域 `zzz-fake123.fqnovel.com` 查不到），
  是**有效规则，保留不删**。真实情况：抓包里 App 请求的是 `-lf` 系，规则里只有 `-hl` → 属**漏拦**，不是写错。
- **修 sync 脚本**：云端 Actions 推 `adblock-upstream.conf` 导致本机 push 被 `fetch first` 拒绝 → 脚本加自动 rebase
- **三方合并**：本机补 `wmzfylgdsz.com`，仓库补 `ad-sign.byteimg.com` + `aeventlog.beacon.qq.com`，两边对齐 37 条

---

## 八、📌 用户（林柒）的常设要求

> 这些是用户明确提过、需要长期执行的，不是一次性任务。

1. **「我们本地改了，仓库也要看看」**（2026-10-13 原话）—— 改完本机规则**不等于**完事，仓库必须同步。
   落地成：三方一致性核对 + 手动跑 sync 脚本
2. **两条同步链路分开**：「**主动同步别人的（主要）** + 我们手动同步自己的」
3. **文档与规则必须对齐** —— 改规则要顺手核对 `README.md` / `docs/*.md` / `dist/README.md` 里的条数与写法描述
4. **报告要有真实证据，不空说「有问题」** —— 先查根因再汇报
5. **改本机时容易忘记一起改的**：`dist/`（要重跑 `export_lists.py`）、`config/dnsmasq.conf.example`（脱敏模板，手动维护）、
   仓库的 `config/adblock-*.conf`、`CHANGELOG.md`（**不改**，改了是篡改历史）
6. **云电脑巡检**（每天 09:30）让云上的模型读仓库、查文档与规则是否对得上 —— 它扫出来的问题要当真
7. **别用真人照片做换脸**；涉及未成年人一律不碰（这条是安全底线，与项目无关但同样适用）

---

## 九、巡检机器人（每天 09:30）该检查什么

1. **服务活着吗**：`systemctl is-active dnsmasq-home.service` + `queries.log` 有没有在写
2. **三方条数对得上吗**：本机 / 仓库 / 文档里写的数字
3. **文档说要拦、实际没拦 = 0 个**：把 `docs/domain-list.md` 的域与三个规则文件比对
4. **`whitelist.txt` 每一条都在文档里**（`qznovelvod.com` 下 44 条 `v{5,6,7,9,11,13,26,95,96,99,100}-*-reading-ad`
   是**刻意例外**，正片走 `*-reading-video`，文档必须写明否则字面像自相矛盾）
5. **有没有死规则 / 笔误**（如 `-hl` vs `-lf` 这类）—— **注意先用 `dig` 验证再下结论，别像 10-14 那样误判**
6. **有没有 `.bak` / 日志类垃圾被提交进仓库**
7. **上游同步有没有跑成功**（Actions 04:00 / 本机 05:00）

---

## 十、常用命令速查

```bash
# 服务
systemctl is-active dnsmasq-home.service
sudo systemctl restart dnsmasq-home.service
sudo dnsmasq --test -C /home/wang/.hermes/dns/dnsmasq.conf

# 查条数
grep -c '^address=' ~/.hermes/dns/adblock-*.conf

# 查某域拦没拦
dig @192.168.31.88 <域> | grep status

# 查误封（只抓我们拦的）
grep 'config .* is NXDOMAIN' ~/.hermes/dns/queries.log | sed -E 's/.*config ([^ ]+) is .*/\1/' | sort | uniq -c | sort -rn | head -20

# 同步
/home/wang/.hermes/scripts/sync_adblock_repo.sh
cd /home/wang/projects/home-dns-adblock && git pull --rebase && git push

# 仓库侧（必须走代理）
export https_proxy=socks5://127.0.0.1:10808
```

---

**最后一句**：这个项目的价值是「**知道什么不能拦**」，不是「拦得多」。
加规则前先问自己：**这条会不会让用户看不了视频？** 拿不准就先 `dig` 验，别猜。
