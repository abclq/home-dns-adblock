#!/usr/bin/env bash
# home-dns-adblock 一键部署脚本
# 用法: sudo ./scripts/install.sh [内网IP]
#   例: sudo ./scripts/install.sh 192.168.1.2
set -euo pipefail

CONF_DIR=/etc/dnsmasq-adblock
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

c() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
ok()   { c '32' "  ✓ $1"; }
warn() { c '33' "  ! $1"; }
err()  { c '31' "  ✗ $1"; }

echo
c '36' '════════ home-dns-adblock 部署 ════════'
echo

# ── 0. 权限检查 ────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
  err "需要 root 权限，请用 sudo 运行"
  exit 1
fi

# ── 1. 确定内网 IP ────────────────────────────
LAN_IP="${1:-}"
if [ -z "$LAN_IP" ]; then
  DETECTED=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1); exit}')
  echo "  检测到本机内网 IP: ${DETECTED:-未检测到}"
  read -rp "  请确认或输入内网 IP（直接回车用检测值）: " INPUT
  LAN_IP="${INPUT:-$DETECTED}"
fi
if [ -z "$LAN_IP" ]; then
  err "无法确定内网 IP，请手动指定: sudo $0 192.168.1.2"
  exit 1
fi
ok "使用内网 IP: $LAN_IP"

# ── 2. 装 dnsmasq ─────────────────────────────
echo
echo "  [1/5] 安装 dnsmasq"
if command -v dnsmasq >/dev/null 2>&1; then
  ok "已安装: $(dnsmasq --version | head -1)"
else
  if command -v apt-get >/dev/null 2>&1; then
    DEBIAN_FRONTEND=noninteractive apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dnsmasq
  elif command -v opkg >/dev/null 2>&1; then
    opkg update && opkg install dnsmasq
  else
    err "未识别的包管理器，请手动安装 dnsmasq"
    exit 1
  fi
  ok "安装完成"
fi

# ★ 停掉系统自带实例，避免抢 53 端口
if systemctl is-active --quiet dnsmasq 2>/dev/null; then
  systemctl stop dnsmasq
  systemctl disable dnsmasq 2>/dev/null || true
  warn "已停用系统自带的 dnsmasq.service（避免抢占 53 端口）"
fi

# ── 3. 部署配置 ───────────────────────────────
echo
echo "  [2/5] 部署配置文件"
mkdir -p "$CONF_DIR"
cp "$REPO_DIR/config/adblock-fq.conf" "$CONF_DIR/"
sed "s|192\.168\.1\.2|$LAN_IP|g" "$REPO_DIR/config/dnsmasq.conf.example" > "$CONF_DIR/dnsmasq.conf"
ok "配置目录: $CONF_DIR"
ok "规则条数: $(grep -c '^address=' "$CONF_DIR/adblock-fq.conf")"

# ── 4. 日志轮转 ───────────────────────────────
echo
echo "  [3/5] 配置日志轮转"
if [ -d /etc/logrotate.d ]; then
  sed "s|/etc/dnsmasq-adblock/queries.log|$CONF_DIR/queries.log|g" \
    "$REPO_DIR/config/dnsmasq-adblock.logrotate" > /etc/logrotate.d/dnsmasq-adblock
  ok "已写入 /etc/logrotate.d/dnsmasq-adblock"
else
  warn "无 logrotate，跳过（注意监控日志大小）"
fi

# ── 5. 启动 ───────────────────────────────────
echo
echo "  [4/5] 启动 dnsmasq"
pkill -f "dnsmasq -C $CONF_DIR/dnsmasq.conf" 2>/dev/null || true
sleep 1
dnsmasq -C "$CONF_DIR/dnsmasq.conf"
sleep 1
if pgrep -f "dnsmasq -C $CONF_DIR/dnsmasq.conf" >/dev/null; then
  ok "已启动 (PID $(pgrep -f "dnsmasq -C $CONF_DIR/dnsmasq.conf" | head -1))"
else
  err "启动失败，请检查: dnsmasq -C $CONF_DIR/dnsmasq.conf --test"
  exit 1
fi

# ── 6. 自检 ───────────────────────────────────
echo
echo "  [5/5] 自检"
if [ -x "$REPO_DIR/scripts/verify.sh" ]; then
  "$REPO_DIR/scripts/verify.sh" || true
else
  warn "未找到 verify.sh，跳过"
fi

echo
c '36' '════════ 部署完成 ════════'
echo
echo "  下一步：把设备的 DNS 指向 $LAN_IP"
echo "    iPhone : 设置 → 无线局域网 → ⓘ → 配置 DNS → 手动 → 只留 $LAN_IP"
echo "    Android: WiFi 详情 → IP 设置 → 静态 → DNS1 = $LAN_IP"
echo "    全屋   : 路由器 DHCP 下发的 DNS 改成 $LAN_IP"
echo
echo "  想让出门在外也能用？见 docs/tailscale-remote.md"
echo
