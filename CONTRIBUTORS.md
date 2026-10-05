# 贡献者

本项目由社区规则集 + 实机抓包验证共同构成。以下是各类贡献的完整名单。

## 维护者

| 角色 | 贡献 |
|------|------|
| **[@abclq](https://github.com/abclq)** | 项目发起、方案设计、规则整理、实机验证（家庭网络环境 7×24 运行） |

## 规则来源（社区项目，本项目的基础）

没有这些规则集，本项目的规则数量会少一个数量级：

| 项目 | 说明 | 本项目采用量 |
|------|------|------------|
| [honue/rules](https://github.com/honue/rules) | Loon 插件格式规则集，中文 App 覆盖广 | 主干来源 |
| [chxm1023/Script_X](https://github.com/chxm1023/Script_X) | 过滤规则集 | 主干来源 |
| [anti-AD](https://github.com/privacy-protection-tools/anti-AD) | 最老牌的广告域名列表之一 | 交叉验证 |
| [AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule) | 轻量广告规则 | 交叉验证 |

**本项目对它们的处理方式**：不做简单叠加（会导致误拦），而是**取交集 + 白名单保护 + 实机抓包复核**。
详见 [docs/domain-list.md](docs/domain-list.md)。

## 实测贡献

以下域名由本项目的**实机 DNS 日志抓包**确认（即：在广告出现的那一刻确实被查询），
社区规则集里没有，属于本项目原创验证：

- `lf-webcast-gr-sourcecdn.bytegecko.com` — 字节系广告素材分发
- `praisewindow.ugsdk.cn` — 激励视频 / 弹窗 SDK
- `tnc0-aliec2.zijieapi.com` — 阿里云线上的字节广告计费
- `is.snssdk.com` — 抖音系上报（广告归因）
- `dig.bdurl.net` — 百度统计跳转
- `adx.douyincdn.com` — 广告素材 CDN

> **发现方法**：不用抓包工具、不装证书，只看 DNS 日志的**时间戳聚类**。
> 广告域的特征是「只在广告出现的那一瞬间被查询」。工具见 `scripts/adblock-helper.sh`。

## 工具与基础设施

| 项目 | 用途 |
|------|------|
| [dnsmasq](https://thekelleys.org.uk/dnsmasq/doc.html) | 本方案的核心 —— DNS 转发 + 黑洞应答 |
| [Tailscale](https://tailscale.com/) | 「出门在外也能用家里 DNS」的零成本实现 |
| [Debian](https://www.debian.org/) / [Ubuntu](https://ubuntu.com/) | 运行环境 |
| [logrotate](https://github.com/logrotate/logrotate) | DNS 日志轮转（避免磁盘写满） |

## 如何把自己加进这个名单

任何一项都欢迎：

- **新广告域名**（最有价值）—— 见 [README 贡献节](README.md#-贡献)
- **误拦报告**（同样有价值）—— 说明哪个正常功能被拦了，附 App 和现象
- **新平台适配** —— 目前只验证了 iOS + Ubuntu，欢迎补充 Android / OpenWrt / 群晖 / 树莓派的实际部署记录
- **文档修正** —— 错别字、步骤不清、命令跑不通，都算

**提交 PR 时请附实测证据**（DNS 日志片段 / 截图 / 操作复现步骤）。
只写"这个域名好像是广告"的 PR 会被要求补证据 —— 因为误拦会殃及全家的正片播放。

---

**开发说明**：本项目的规则收集、脚本编写与文档整理过程使用了 AI 编程助手辅助，
所有规则与命令均已在本项目的实际运行环境中验证。
