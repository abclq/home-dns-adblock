#!/bin/bash
# 抓包收尾：清 arpspoof/tcpdump/scrcpy + 清 iptables（独立版，不依赖 systemd）
#
# 用法: sudo ./hg_autostop.sh [手机IP] [pcap目录]
# 说明: ARP 劫持不清 → 手机一直绕经本机。务必执行。
# 背景: 见 ../docs/capture-method.md

set -u

PHONE="${1:?请传手机 IP，例: ./hg_autostop.sh 192.168.x.x}"        # ← 改成手机 IP
D="${2:-/tmp}"                     # ← pcap 所在目录

{
  echo "$(date '+%F %T') ===== 到点收尾 ====="
  pkill -x arpspoof 2>/dev/null && echo "  arpspoof 已清" || echo "  arpspoof 无"
  pkill -x tcpdump  2>/dev/null && echo "  tcpdump 已清"  || echo "  tcpdump 无"
  pkill -x scrcpy   2>/dev/null && echo "  scrcpy 已清"   || echo "  scrcpy 无"
  iptables -D FORWARD -s "$PHONE" -j ACCEPT 2>/dev/null
  iptables -D FORWARD -d "$PHONE" -j ACCEPT 2>/dev/null
  echo "  iptables FORWARD 规则已清"
  F=$(ls -t "$D"/*.pcap 2>/dev/null | head -1)
  if [ -n "$F" ]; then
    echo "  pcap: $F  $(stat -c %s "$F" | awk '{printf "%.1f MB", $1/1048576}')"
  fi
  echo "$(date '+%F %T') ===== 收尾完成 ====="
} | tee -a "$D/autostop.log"
