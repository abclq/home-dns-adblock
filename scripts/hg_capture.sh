#!/bin/bash
# 无 root 安卓手机抓包：ARP 劫持 + tcpdump（只存前 500 字节/包，够拿 DNS+SNI）
#
# 用法: sudo ./hg_capture.sh <输出.pcap> [手机IP] [网关IP] [网卡]
# 示例: sudo ./hg_capture.sh /tmp/hg.pcap 192.168.x.x 192.168.x.x enp2s0
#
# 前置: sudo apt install -y dsniff tcpdump
# 说明: 抓包期间手机流量绕经本机（会变慢）；收尾必须跑 hg_autostop.sh
# 背景: 见 ../docs/capture-method.md

set -u

OUT="${1:-/tmp/hg_capture.pcap}"
PHONE="${2:?请传手机 IP}"                                  # ← 改成手机 IP
GW="${3:?请传网关 IP}"                                       # ← 改成网关 IP
IFACE="${4:-$(ip route | awk '/default/{print $5; exit}')}"

echo "[*] 手机 $PHONE  网关 $GW  网卡 $IFACE"
echo "[*] 输出 $OUT"

sysctl -w net.ipv4.ip_forward=1 >/dev/null
iptables -I FORWARD 1 -s "$PHONE" -j ACCEPT 2>/dev/null
iptables -I FORWARD 1 -d "$PHONE" -j ACCEPT 2>/dev/null

P1=""; P2=""
cleanup() {
  echo "[*] 停止 ARP 劫持，恢复网络"
  [ -n "$P1" ] && kill "$P1" 2>/dev/null
  [ -n "$P2" ] && kill "$P2" 2>/dev/null
  sleep 2
}
trap cleanup EXIT TERM INT

echo "[*] ARP 劫持 $PHONE <-> $GW"
arpspoof -i "$IFACE" -t "$PHONE" "$GW" >/dev/null 2>&1 &
P1=$!
arpspoof -i "$IFACE" -t "$GW" "$PHONE" >/dev/null 2>&1 &
P2=$!
sleep 3

echo "[*] 抓包 → $OUT  (snaplen 500)"
tcpdump -i "$IFACE" -s 500 -U -w "$OUT" \
  "host $PHONE and (port 53 or port 80 or port 443 or port 8080 or port 8443)"
