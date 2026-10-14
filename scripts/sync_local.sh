#!/bin/bash
# ⚠️ 本文件是【只读镜像】，仅供云机巡检时审阅代码用。
#    权威版本在【本机】 ~/.hermes/scripts/sync_adblock_repo.sh —— 改它才生效。
#    本镜像由本机手工同步（不自动覆盖），最后同步：2026-10-14 23:22:58
# 行为：
#   无变化  → 完全静默退出（不产生提交、不发通知）
#   有变化  → 拉最新规则 → 重新导出 dist/ → commit → push → 输出一行结果
#   推送失败→ 本地保留提交，输出错误，下次运行自动重试
#
# 由 cron 定时调用（no_agent 模式：有输出=通知用户，无输出=静默）

set -uo pipefail

REPO=~/projects/home-dns-adblock
SRC=~/.hermes/dns
BRANCH=main

cd "$REPO" 2>/dev/null || { echo "✗ 仓库目录不存在: $REPO"; exit 1; }

# ---------- 0. 先拉最新（云机指出：原来只在 push 被拒时才 pull）----------
# 原逻辑漏洞：本机没东西可推时，pull 永远不跑 → 本地副本停在旧版本
# → 看不到云机提交 → 反向同步（sync_one）也不会触发 → 两边长期分叉。
# 修：第 1 步之前无条件 pull --rebase，失败就退出（宁可不动，也别在旧版本上瞎改）。
if ! git pull --rebase -q origin "$BRANCH" >/dev/null 2>&1; then
    git rebase --abort >/dev/null 2>&1
    echo "✗ $(date '+%F %T')  拉取远端失败（网络或冲突）—— 本轮不动，下次重试"
    exit 1
fi

# ---------- 1. 本机规则 → 仓库 config/ ----------
# adblock-fq.conf     : 手工维护（实机抓包确认，条数见 docs/for-agents.md 基线）
# adblock-extra.conf  : 手工维护（DoH 加固 + 埋点统计）
# 注意：主配置 dnsmasq.conf 里的 15 条硬编码是脱敏后的模板（dnsmasq.conf.example），
#      不直接同步，避免把内网 IP / 真实路径带进公开仓库
# ⚠️ 覆盖前先查：这个文件在仓库里【最后一次改动是谁做的】。
#    如果是云机 agent（author 含 Hark）改的 —— 本机【不覆盖】。
#    否则会出现「她改 → 我冲 → 她又改」的死循环（真发生过）。
#
# 2026-10-14 云机指出漏洞：原来一旦最后改动者是云机就【永久跳过】，
# 会导致本机自己后续的白名单改动永远推不出去、两边长期分叉。
# 改成【反向同步】：
#   · 有效内容（去掉注释/空行）一致，只差注释 → 采纳仓库版到本机（两边收敛）
#   · 有实质差异 → 停手，两边都不动，只告警，由人在 docs/coordination.md 决定
sync_one() {
    local src="$1" dst="$2"
    [ -f "$src" ] || { echo "  ⚠️ 本机缺 $src，跳过"; return 0; }
    local last_author
    last_author=$(git log -1 --format='%an' -- "$dst" 2>/dev/null || echo "")
    case "$last_author" in
        *Hark*)
            [ -f "$dst" ] || { echo "  ⚠️ 仓库缺 $dst，无法反向同步"; return 1; }
            local ta tb
            ta=$(mktemp); tb=$(mktemp)
            grep -vE '^[[:space:]]*#|^[[:space:]]*$' "$src" > "$ta" 2>/dev/null || true
            grep -vE '^[[:space:]]*#|^[[:space:]]*$' "$dst" > "$tb" 2>/dev/null || true
            if diff -q "$ta" "$tb" >/dev/null 2>&1; then
                rm -f "$ta" "$tb"
                if ! cmp -s "$src" "$dst"; then
                    cp -f "$src" "$src.bak.$(date +%Y%m%d%H%M%S)"
                    cp -f "$dst" "$src"
                    echo "  ↩️ $dst —— 只有注释差异，已反向同步云机版到本机（原文件已备份 .bak）"
                fi
                return 0
            fi
            rm -f "$ta" "$tb"
            echo "  🛑 $dst —— 仓库最后改动是云机（$last_author），且与本机【有实质差异】"
            echo "     两边都不动。请在 docs/coordination.md 对账后人工决定。"
            return 1
            ;;
    esac
    cp -f "$src" "$dst"
    return 0
}

DIVERGED=0
sync_one "$SRC/adblock-fq.conf"    config/adblock-fq.conf    || DIVERGED=1
sync_one "$SRC/adblock-extra.conf" config/adblock-extra.conf || DIVERGED=1
# 白名单也同步（本地改了保护域，仓库必须跟）
sync_one "$SRC/whitelist.txt"      config/whitelist.txt      || DIVERGED=1
[ "$DIVERGED" = 1 ] && echo "  ℹ️ 有文件被云机改过、本机已跳过（没覆盖）。对账见 docs/coordination.md"
# 注意：adblock-upstream.conf 由 GitHub Actions 云端生成，本机【不推】，
#      避免和云端任务互相覆盖（本机只拉不推）。

# ---------- 2. 重新导出多格式 ----------
if ! python3 scripts/export_lists.py >/dev/null 2>&1; then
    echo "✗ 导出规则失败（scripts/export_lists.py）"
    exit 1
fi

# ---------- 2.5 刷新文档里写死的条数 ----------
# adblock-upstream.conf 由云端 Actions 每天重新生成，条数天天变；
# README / docs 里手写的数字必然过期 → 用真实值回写（幂等，无变化时静默）
if [ -f scripts/update_counts.py ]; then
    python3 scripts/update_counts.py >/dev/null 2>&1 \
        || echo "⚠️ 文档条数刷新失败（scripts/update_counts.py），规则同步继续"
fi

# ---------- 3. 判断是否要动 ----------
DIRTY=$(git status --porcelain)
AHEAD=$(git rev-list --count "origin/$BRANCH..HEAD" 2>/dev/null || echo 0)

if [ -z "$DIRTY" ] && [ "$AHEAD" = "0" ]; then
    exit 0          # 无变化、无待推提交 → 静默
fi

# ---------- 4. 提交 ----------
N=$(grep -vcE '^#|^$' dist/domains.txt 2>/dev/null || echo '?')
if [ -n "$DIRTY" ]; then
    git add -A
    # 提交信息：默认「自动同步」；若这次动了规则文件（config/*.conf），说明是手工修复，
    # 标成 rules: 以便在历史里区分（云机 2026-10-14 提的问题）。
    # 也可用 SYNC_MSG="..." 完全覆盖。
    if [ -n "${SYNC_MSG:-}" ]; then
        MSG="$SYNC_MSG"
    elif git diff --cached --name-only | grep -qE '^config/(adblock-fq|adblock-extra)\.conf$'; then
        MSG="rules: 规则手工调整 $(date +%F) —— 共 ${N} 条唯一域名

规则文件（config/*.conf）有改动，不是纯自动同步。对账见 docs/coordination.md。"
    else
        MSG="chore: 规则自动同步 $(date +%F) —— ${N} 条唯一域名

由 sync_adblock_repo.sh 从本机 dnsmasq 规则导出。
来源: adblock-fq.conf + adblock-extra.conf + dnsmasq.conf.example
产物: config/ 更新 + dist/ 七种格式重新生成"
    fi
    if ! git commit -q -m "$MSG"; then
        echo "✗ 提交失败"
        exit 1
    fi
fi

# ---------- 5. 推送 ----------
# 远端可能有云端 GitHub Actions 的提交（adblock-upstream.conf 由云端生成并推送），
# 这时直接 push 会被 "! [rejected] ... (fetch first)" 拒绝 —— 先 rebase 再重推。
if ! git push -q origin "$BRANCH" 2>/dev/null; then
    if git pull --rebase -q origin "$BRANCH" >/dev/null 2>&1; then
        :   # rebase 成功，下面重推
    else
        git rebase --abort >/dev/null 2>&1
        echo "✗ $(date '+%F %T')  远端与本地冲突，rebase 失败 —— 需人工处理（本地提交已保留）"
        exit 1
    fi
fi
if git push -q origin "$BRANCH" 2>/dev/null; then
    echo "✓ $(date '+%F %T')  规则已同步到仓库：${N} 条唯一域名"
    echo "  https://github.com/abclq/home-dns-adblock/commit/$(git rev-parse --short HEAD)"
else
    echo "✗ $(date '+%F %T')  推送失败（网络？），本地已提交，下次运行会自动重试"
    exit 1
fi
