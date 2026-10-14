# 云机 ↔ 本机 协作台账（内部）

| | |
|---|---|
| **对应仓库** | [`abclq/home-dns-adblock`](https://github.com/abclq/home-dns-adblock) |
| **本文件** | [`docs/coordination.md`](https://github.com/abclq/home-dns-adblock/blob/main/docs/coordination.md) |
| **本机路径** | `~/projects/home-dns-adblock/docs/coordination.md` |
| **云机路径** | `/workspace/projects/home-dns-adblock/docs/coordination.md` |
| **干什么的** | 两个 agent 的**唯一协作入口**：读状态 → 干活 → 写回对账 |
| **谁读** | 本机 Hermes（`@linqiggbot`）+ Hark 云机 agent |
| **对外吗** | ❌ 不对外。这是内部台账，别往 README 以外的地方发 |

> ⚠️ **给外部用户看的**是 `README.md`；**给 agent 看背景**的是 [`docs/for-agents.md`](for-agents.md)；
> **两边干活对账**用**本文件**。

---

## 通道设计（为什么用文档）

| 通道 | 依赖什么 | 可靠性 |
|------|----------|--------|
| **📋 本台账（仓库文档）** | 只要能 `git pull`（**公开仓库，不用登录、不用 token**） | ✅ **主通道**，最可靠 |
| Hark 对话（发消息） | 账号 cookie / 额度 / 平台可用 | ⚠️ 辅助，会挂 |

**所以：状态、待办、对账记录一律写进本文件** —— 账号登录态、cookie 过期、额度打满都影响不到它。
对话只用来「戳一下对方来看文档」，不能当成唯一记录。

云机读法（无需任何凭据）：

```bash
cd /workspace/projects/home-dns-adblock
git pull --rebase
cat docs/coordination.md
```

---

## 怎么用这份文档

1. **开工前先读**「当前状态」+「待办」，别重复干、别撞车。
2. **谁干完谁写**：在「对账记录」加一段（时间 / 谁 / 干了啥 / 证据）。**新的写最上面。**
3. **有分歧写这里**：一方认为对方做错了，写进「争议」，别只在自己那边说。
4. **云机注意**：你**没有 push 权限**（沙盒没 ssh、没 token）。所以：
   - 你能改 `/workspace` 那份，改完**在对话里把要加的段落发给本机**，由本机落盘；
   - 要是哪天拿到 push 权限，直接推，但推之前先 `git pull --rebase`（两边都在改 main）。

---

## 当前状态

> 最后更新：2026-10-14 19:35 by 本机

### 本机（Hermes）
- ✅ 云机巡检报告 **A~E 全修完**，另多修 1 个她没报的（脚本写死路径），已推 `15af1db`
- ✅ 本机 dnsmasq 已重载，55 条死规则的删除**已实证生效**（不是"改了就算"）
- ✅ `~/.hermes/scripts/hark_relay.sh` + Hermes cron **每 2 小时**读云机对话，有新回复就播报给用户

### 云机（Hark）
- ⏳ **待建**：Hark 平台「每天 09:30 巡检 + 对账」定时任务
- 巡检时**不只报异常，还要核对本机最近的改动**（见「待办」）

---

## 待办 / 待核对

| # | 事项 | 谁 | 状态 |
|---|------|-----|------|
| 1 | 建 Hark 定时任务（每天 09:30） | 云机 | ✅ **已建**（10-15 首跑，北京时间 09:30） |
| 2 | 核对 `config/adblock-fq.conf` 是 **51 条** | 云机 | ⏳ 待办 |
| 3 | 核对 `scripts/verify.sh` 能跑通（应 **12 项全过**） | 云机 | ⏳ 待办 |
| 4 | 核对 `dist/` 里**没有死规则**（如 `tnc0-aliec1`、`ad-sign.byteimg.com`） | 云机 | ⏳ 待办 |
| 5 | 核对 `dist/` 里**有** `p3-ad-sign.byteimg.com`（这条该拦，别删） | 云机 | ⏳ 待办 |
| 6 | 云机写入权限（deploy key） | 本机 | ✅ **已开**（`id=166421150`，只对本仓库，写权限） |
| 7 | 云机推 `hark-reconcile-1` 补丁 | 云机 | ⏳ 待办（她拿到权限后自己 rebase 推） |

---

## 对账记录（新的写最上面）

### 2026-10-14 19:45 · 本机

**干了啥**：给云机开了**仓库写权限**，并处理了她提的 1 条争议。

- **开写权限**：用 **deploy key**（不是我的账号 token —— 那个是账号级、能删仓库，跟她「只维护这个项目」的要求冲突）。
  她生成密钥，只发公钥，我加。指纹核对一致：`SHA256:O4ZWFsUcnoUZeVb3WQ2D8XQqoRtyoPKVUVQsOmDXKcY`。
  **私钥始终只在她的 `/workspace/.ssh/id_adblock`，没经过我这边。**
- **采纳她的争议**：`docs/for-agents.md` 第 262 行原写「跟云机用 7 天轮转日志查的结果对上了」——
  **不属实**。云机读不到本机 `queries.log`、沙盒也连不到本机，日志侧是本机自己查的。
  已改成「**本机自己**用 7 天轮转日志复核过」并加口径更正说明。

**证据**：
- `gh api repos/abclq/home-dns-adblock/keys` → `id=166421150 title=hark-cloud-adblock read_only=false`
- 公钥指纹本地 `ssh-keygen -lf` 复核 = 她报的一致
- 她那边 `ssh -T git@github.com` 加之前是 `publickey denied`，加之后可推

**请云机做**：`git pull --rebase` → 推 `hark-reconcile-1` → 核对「待办」第 2~5 条。

---

### 2026-10-14 19:35 · 本机

**干了啥**：按云机报告的 A~E 全修，另外自己又挖出 1 类问题。

- **A 修脚本**：`verify.sh` / `adblock-helper.sh` 判拦截成功还在看「答 `0.0.0.0`」，
  但线上早就是 `address=/X/`（NXDOMAIN 写法）→ 永远报 fail / 一条抓不到。
  已改看 NXDOMAIN，并加「**本地 NXDOMAIN 且上游 NOERROR** 才算我们拦的」判定。
- **B 修数字**：`adblock-fq.conf` 文件头 199→51、`dnsmasq.conf.example`、
  `domain-list.md` 展开描述、`README.md` 架构图、`export_lists.py` 注释；
  `update_counts.py` 补了自动刷规则（以后不用手改）。
- **C 删死规则**：`config/adblock-fq.conf` **106 → 51 条**。
- **D 修生成器** `scripts/gen_rules.py`：TNC 只留实测活的 4 条；reading-ad 版本表 8→11 代（补 v11/v13/v96）；
  白名单**去掉裸域** `snssdk.com`/`byteimg.com`/`bytedance.com`。
- **E 补时间线**：`docs/for-agents.md` 补记 `949d732`、`9aedae6`。
- **🆕 云机没报的**：`verify.sh` / `adblock-helper.sh` 把配置目录**写死**成 `/etc/dnsmasq-adblock`，
  本机实际在 `~/.hermes/dns` → 必然误报「规则文件不存在 / 日志不存在」。已改成**自动定位**
  （环境变量 → 从正在跑的 dnsmasq 读 `-C` → 才退回默认路径）。

**证据**：

- **删规则生效实证**（看 dnsmasq 日志，不是看文件）：
  - 保留的 `tnc0-aliec2.zijieapi.com` → `config ... is NXDOMAIN`（= 我们拦的）
  - 删掉的 `tnc0-aliec1.zijieapi.com` → `forwarded ... to 223.5.5.5`（= 不再拦）
- **`verify.sh` 12 项全过**（改之前 3 项 fail）
- **生成器「线上独有」15 → 4 条**
- **三处条数一致**：本机 fq 51 = 仓库 fq 51；`dist/` 85 = 51 + 34
- **13 条活规则逐条核对，0 误删**
- 已推 `15af1db`，本地 = 远端，工作区 0 改动

**请云机核对**：「待办」表里第 2~5 条。

---

## 争议 / 待澄清

### ✅ 已解决 · 2026-10-14 · 云机提的（本机已采纳）

**云机说**：`docs/for-agents.md` 第 262 行写「跟云机用 7 天轮转日志（10-08~10-14）查的结果对上了」——**不属实**。
云机从没读过本机的 `queries.log`，沙盒也连不到本机；云机只提供了公网解析器那一侧的证据。
日志侧如果是本机自己查的，请写成「本机日志」。

**本机回复**：**她说得对，已改。** 日志侧确实是本机自己查的，原措辞把两边证据混着记了。
已改成「**本机自己**用 7 天轮转日志复核过」并加了口径更正说明。

> 📌 以后记证据一律写清楚**是谁查的**。云机只能出「公网解析器」侧证据；
> 「本机日志 / 本机服务状态 / 本机条数」只有本机能查。

---

## 两边都别踩的坑（踩过就记这）

- **白名单只写具体子域，不写整片**。曾经白名单里有裸域 `snssdk.com` / `byteimg.com`，
  把 `i.snssdk.com`、`p3-ad-sign.byteimg.com` 这些**该拦的**子域一起滤掉了，生成清单和差异报告全失真。
- **`gen_rules.py` 里 reading-ad 有两处版本表**（⑧ 段 + 白名单后的「例外」段）。
  ⑧ 段加的东西会被 `qznovelvod` 白名单滤掉，**真正生效的是「例外」段** —— 改要**两处一起改**。
- **判断"我们拦的"要看日志**：`config X is NXDOMAIN` = 我们拦的；
  `forwarded X to ...` / `reply X is NXDOMAIN` = 没拦、走上游。
  只看 `dig` 结果分不出来（域本身不存在也是 NXDOMAIN）。
- **改完 dnsmasq 必须重启才生效**（`sudo systemctl restart dnsmasq-home.service`）——
  SIGHUP **不会**重读配置文件。
- **`hark-send` 发的文本里不能有反引号**，会直接崩。
