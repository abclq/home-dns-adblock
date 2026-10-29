# AI 维护：把任意模型（含 Muse）接进这个仓库

## 一句话

仓库里加了 `scripts/ai_triage.py` + `.github/workflows/ai-maintain.yml`：
模型负责**看 issue、分类、写答复草案**，全部跑在 GitHub Actions，**不占本机、不需要常开机**。
换模型只改三个 secret，不改代码。

## 为什么做成「OpenAI 兼容」而不是写死 Muse

Muse 的聊天是**加密 WebSocket（Noise 协议）**，没有公开的 HTTP API。社区那几个 muse2api
项目（`czg86389-hub/muse2api`、`its-benjamin/muse2api`、`luckeyfaraday/muse-shim` 等）都是
**不逆向协议、改驱动无头浏览器**，对外暴露成 OpenAI 兼容的 `/v1/chat/completions`。

所以正确的接法不是「为 Muse 写一套代码」，而是**让仓库只会说 OpenAI 这一种方言**：
Muse 进来，它是 OpenAI；明天换成别的中转站或本地 Ollama，它也是 OpenAI。仓库代码零改动。

## 接 Muse：三步

### 1. 把 muse2api 部署到云主机（不要放本机）

选一个 fork（推荐 `its-benjamin/muse2api`，增强版），按它的 README 起服务，得到类似：

```
http://<云主机>:<端口>/v1
```

要求：**模型名、鉴权方式、请求体格式**都与 OpenAI 一致。验证：

```bash
curl -s http://<云主机>:<端口>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"model":"<模型名>","messages":[{"role":"user","content":"ping"}]}' | head
```

能返回 `choices[0].message.content` 就算通。

> 云主机必须**公网可达**（GitHub 的 runner 在国外，访问不了局域网）。
> 家里那台不需要开任何端口，也不需要 FRP —— 这是「不接本机」的关键。

### 2. 在仓库填三个 secret

Settings → Secrets and variables → Actions → New repository secret：

| 名称 | 值 |
|---|---|
| `MUSE_BASE_URL` | `http://<云主机>:<端口>/v1` |
| `MUSE_API_KEY` | 反代服务的令牌（没有就随便填 `x`） |
| `MUSE_MODEL` | 反代里配置的模型名 |

### 3. 手动跑一次验证

Actions → **AI 维护分诊** → Run workflow：

- `limit` 填 `5`（一次最多看 5 个 issue）
- `post_comment` **先留空**（只上传报告 artifact，不往 issue 里写东西）
- 跑完在 run 页面下载 `ai-triage-report` 看输出

确认语气/判断没问题，再把 `post_comment` 填成具体 issue 号（例如 `1`），它才会评论上去。

每周一 09:00（北京时间）会自动跑一次，只出报告、不自动评论。

## 安全边界（刻意做成这样）

- 权限只有 `contents: read` + `issues: write` —— **不能推代码、不能改规则**
- 模型只产出**文本报告/评论**，任何规则改动仍需人工确认后提交
- 没配 secret 时工作流**不会失败**，只输出「待处理 issue 清单」
- 模型调用失败会写进报告，不会让 CI 变红

## 换模型的例子

| 场景 | `AI_BASE_URL` | `AI_MODEL` |
|---|---|---|
| Muse（muse2api） | `http://<云主机>:<端口>/v1` | 反代里配的名字 |
| 中转站（OpenAI 兼容） | `https://<中转站>/v1` | `gpt-4o-mini` 之类 |
| 本地 Ollama（公网机） | `http://<host>:11434/v1` | `qwen2.5:7b` |
| 官方 OpenAI | `https://api.openai.com/v1` | `gpt-4.1-mini` |

## 本地手动跑（调试用）

```bash
cd home-dns-adblock
export AI_BASE_URL=... AI_API_KEY=... AI_MODEL=...
python3 scripts/ai_triage.py --dry          # 先看它会发什么 prompt
python3 scripts/ai_triage.py --out /tmp/r.md   # 真调模型，写报告
```

`GITHUB_TOKEN` 没设时会用 `gh auth token`，所以本机装了 `gh` 就能直接读 issue。
