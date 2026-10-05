#!/usr/bin/env bash
# home-dns-adblock 部署自检 —— 6 项检查
# 用法: sudo ./scripts/verify.sh
set -uo pipefail

CONF_DIR="${CONF_DIR:-/etc/dnsmasq-adblock}"   # 可用环境变量覆盖，便于自测
CONF="$CONF_DIR/dnsmasq.conf"
RULES="$CONF_DIR/adblock-fq.conf"
LOG="$CONF_DIR/queries.log"

c() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
PASS=0; FAIL=0
pass() { c '32' "  ✓ $1"; PASS=$((PASS+1)); }
fail() { c '31' "  ✗ $1"; FAIL=$((FAIL+1)); }
info() { c '36' "  · $1"; }

echo
c '36' '════════ home-dns-adblock 自检 ════════'
echo

# ── 1. dnsmasq 进程 ───────────────────────────
echo "  [1/6] dnsmasq 进程"
if pgrep -f "dnsmasq -C $CONF" >/dev/null; then
  PID=$(pgrep -f "dnsmasq -C $CONF" | head -1)
  pass "运行中 (PID $PID)"
  ps -o etime=,rss=,pcpu= -p "$PID" 2>/dev/null | awk '{printf "      已运行 %s | 内存 %.1f MB | CPU %s%%\n", $1, $2/1024, $3}'
else
  fail "未运行 —— 启动: sudo dnsmasq -C $CONF"
fi
echo

# ── 2. 53 端口监听 ────────────────────────────
echo "  [2/6] 53 端口监听"
LISTEN=$(ss -tulnp 2>/dev/null | grep ':53 ' | grep -oE '[0-9.]+:53' | sort -u)
if [ -n "$LISTEN" ]; then
  pass "监听中:"
  echo "$LISTEN" | sed 's/^/      /'
  if echo "$LISTEN" | grep -qE '^100\.'; then
    pass "含 Tailscale 地址 —— 出门方案可用 ✓"
  else
    info "未监听 Tailscale 地址（只用在家？那正常；想出门用见 docs/tailscale-remote.md）"
  fi
else
  fail "53 端口无监听"
fi
echo

# ── 3. 规则文件 ───────────────────────────────
echo "  [3/6] 规则文件"
if [ -f "$RULES" ]; then
  N=$(grep -c '^address=' "$RULES")
  if [ "$N" -gt 100 ]; then
    pass "共 $N 条规则"
  else
    fail "只有 $N 条，疑似不完整"
  fi
  # 抽查关键规则是否存在
  for d in "ads3-normal-hl.zijieapi.com" "p3-ad-sign.byteimg.com"; do
    if grep -q "address=/$d/" "$RULES"; then
      pass "关键规则存在: $d"
    else
      fail "缺少关键规则: $d"
    fi
  done
else
  fail "规则文件不存在: $RULES"
fi
echo

# ── 4. ★ 拦截是否真的生效 ─────────────────────
echo "  [4/6] 拦截功能实测（核心）"
if command -v dig >/dev/null 2>&1; then
  ANS=$(dig +short +time=3 +tries=1 @127.0.0.1 ads3-normal-hl.zijieapi.com 2>/dev/null | head -1)
  if [ "$ANS" = "0.0.0.0" ]; then
    pass "广告域被黑洞: ads3-normal-hl.zijieapi.com → 0.0.0.0"
  else
    fail "广告域未被拦截，返回: ${ANS:-无响应}"
  fi
else
  info "无 dig 命令，跳过（装: apt install dnsutils）"
fi
echo

# ── 5. ★ 正常域是否放行 ───────────────────────
echo "  [5/6] 正常域放行实测（防误伤）"
if command -v dig >/dev/null 2>&1; then
  for d in "v11-reading-video.qznovelvod.com" "www.baidu.com"; do
    ANS=$(dig +short +time=3 +tries=1 @127.0.0.1 "$d" 2>/dev/null | head -1)
    if [ -n "$ANS" ] && [ "$ANS" != "0.0.0.0" ]; then
      pass "$d → ${ANS}"
    elif [ "$ANS" = "0.0.0.0" ]; then
      fail "$d 被误拦！（正片会挂）"
    else
      info "$d 无响应（上游 DNS 问题？）"
    fi
  done
else
  info "无 dig 命令，跳过"
fi
echo

# ── 6. 日志 ───────────────────────────────────
echo "  [6/6] 日志"
if [ -f "$LOG" ]; then
  SIZE=$(du -h "$LOG" 2>/dev/null | cut -f1)
  LINES=$(wc -l < "$LOG" 2>/dev/null || echo 0)
  BLOCKED=$(grep -c 'is 0\.0\.0\.0' "$LOG" 2>/dev/null || echo 0)
  pass "日志存在 ($SIZE / $LINES 行)"
  info "累计拦截: $BLOCKED 次"
  if [ "$LINES" -gt 0 ]; then
    LAST=$(tail -1 "$LOG" | cut -c1-30)
    info "最后一条: $LAST"
  fi
  LR_FILE=$(ls /etc/logrotate.d/ 2>/dev/null | grep -iE "dnsmasq|adblock" | head -1)
  if [ -n "$LR_FILE" ]; then
    pass "日志轮转已配置 (/etc/logrotate.d/$LR_FILE)"
  else
    fail "未配置日志轮转（长期运行会写满磁盘）"
  fi
else
  fail "日志文件不存在: $LOG"
fi

# ── 汇总 ─────────────────────────────────────
echo
c '36' '════════ 自检结果 ════════'
if [ "$FAIL" -eq 0 ]; then
  c '32' "  ★ 全部通过 ($PASS 项)"
else
  c '31' "  通过 $PASS 项，失败 $FAIL 项 —— 见上"
fi
echo
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
