# 📚 docs/ —— 文档索引

按「你是谁、想干嘛」挑入口。

## 我是用户，想用起来

| 文档 | 内容 |
|---|---|
| [../README.md](../README.md) | **主文档**：两种用法、快速开始、常用命令 |
| [tailscale-remote.md](tailscale-remote.md) | 出门在外（4G / 别人家 WiFi）也能生效怎么配 |
| [use-with-other-apps.md](use-with-other-apps.md) | 把规则喂给别的软件（AdGuard Home / Pi-hole / 路由器 等） |
| [domain-list.md](domain-list.md) | 规则清单：86 条精确规则逐条说明 |

## 我是协作者 / 机器人，要动这个仓库

| 文档 | 内容 |
|---|---|
| [for-agents.md](for-agents.md) | **先读这个**：硬规矩、条数口径、数字铁律、改文件前必看 |
| [coordination.md](coordination.md) | 本机 ↔ 云机的协作台账：谁在干嘛、待办、已关项 |
| [principles.md](principles.md) | 设计原则：为什么这么封、为什么不那么封 |
| [pitfalls.md](pitfalls.md) | 踩过的坑合集：每条都带「错在哪 / 怎么改」 |
| [capture-method.md](capture-method.md) | **怎么抓包**：无 root 安卓机 ARP 中间人 + tcpdump（配 `scripts/hg_capture.sh`） |

## 我想看它是怎么想出来的

| 文档 | 内容 |
|---|---|
| [redguo-case-study.md](redguo-case-study.md) | 红果短剧案例复盘：怎么从抓包回溯出规则 |

---

## 几个关键数字（口径别搞混）

- **86** = 精确规则条数（`config/adblock-fq.conf` 51 条 + `config/adblock-extra.conf` 可导出 34 条）
- **36** = dnsmasq 实际加载的 extra 条数（比 34 多一条 `_dns.resolver.arpa`，屏蔽 DDR 发现；导出第三方格式时会跳过 `_` 开头）
- **938** = 上游社区规则条数（自动同步）
- **1021** = 去重后合计

数字改动后跑 `python3 scripts/update_counts.py` 自动刷新文档里的计数，别手改。

## 文档维护约定

- 改文件前先 `git pull --rebase`
- 规则文件改动用 `rules:` 开头提交；文档用 `docs:`；脚本用 `fix:` / `feat:`
- 提交作者写 `林柒 <abclq@users.noreply.github.com>`
