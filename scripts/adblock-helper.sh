#!/bin/bash
# 红果广告拦截 —— 抓包速查工具
# 用法: adblock-helper.sh {live|ad|dev|suspect|top|mark|reset}
LOG=/etc/dnsmasq-adblock/queries.log
DIR=/etc/dnsmasq-adblock
MARK=$DIR/.mark

case "$1" in
  live)
    # 实时看所有设备的 DNS 查询
    tail -f "$LOG"
    ;;
  ad)
    # 只看被黑洞拦下的（config → 0.0.0.0）
    grep -E "config .*is 0\.0\.0\.0" "$LOG" | tail -${2:-30}
    ;;
  dev)
    # 各设备查询量排行（谁在用）
    grep -oE "from [0-9.]+" "$LOG" | sort | uniq -c | sort -rn
    ;;
  suspect)
    # 疑似广告域清单（唯一）
    grep -oE "query\[[A-Za-z]+\] [^ ]+" "$LOG" | awk '{print $2}' | sort -u \
      | grep -iE "ad-|-ad\.|ads[0-9]|sinf|bdurl|novel-sign|pangolin|csj"
    ;;
  top)
    # 查询量 Top 30 域名
    grep -oE "query\[[A-Za-z]+\] [^ ]+" "$LOG" | awk '{print $2}' | sort | uniq -c | sort -rn | head -30
    ;;
  new)
    # 从上次标记点之后的新增内容
    tail -n +$(( $(cat "$MARK" 2>/dev/null || echo 0) + 1 )) "$LOG" \
      | grep -oE "query\[[A-Za-z]+\] [^ ]+ from [0-9.]+" | awk '{print $NF, $2}' | head -60
    ;;
  win)
    # 最近 N 分钟（默认 3）的所有查询 —— 看到广告后用这个
    python3 - "$LOG" "${2:-3}" <<'PY'
import sys, re, datetime
log, m = sys.argv[1], int(sys.argv[2])
cut = datetime.datetime.now() - datetime.timedelta(minutes=m)
pat = re.compile(r'^(\w{3})\s+(\d+)\s+(\d{2}:\d{2}:\d{2})')
yr = datetime.datetime.now().year
rows = []
for line in open(log, errors='ignore'):
    mm = pat.match(line)
    if not mm:
        continue
    try:
        t = datetime.datetime.strptime(f"{mm.group(1)} {mm.group(2)} {mm.group(3)} {yr}", "%b %d %H:%M:%S %Y")
    except ValueError:
        continue
    if t >= cut:
        rows.append((t, line.rstrip()))
if not rows:
    print(f"  （最近 {m} 分钟无任何查询）")
for t, l in rows:
    print(l)
print(f"\n  === 共 {len(rows)} 条 / 最近 {m} 分钟 ===", file=sys.stderr)
PY
    ;;
  one)
    # 只盯某一台设备：~/adblock-helper.sh one 150
    IP=${2:-150}
    echo "  盯梢 192.168.1.$IP （Ctrl-C 退出）"
    tail -f "$LOG" | grep --line-buffered -E "from 192\.168\.31\.$IP($| )" | grep --line-buffered -vE "resolver.arpa|captive.apple|push.apple"
    ;;
  ad150)
    # .150 的广告域名组（按时间戳聚类，只看可疑的）
    grep "from 192.168.1.150" "$LOG" | grep -E "bdurl|ad-sign|sinfonlinea|ugsdk|novel-sign|\.ad\.|ads[0-9]|douyinpic\.com$|bsgslb|byteimg" | tail -40
    ;;
  mark|reset)
    wc -l < "$LOG" > "$MARK"
    echo "标记点已重置 → 第 $(cat $MARK) 行（$(date '+%H:%M:%S')）"
    ;;
  *)
    echo "用法: adblock-helper.sh {live|ad|dev|suspect|top|new|mark}"
    echo "  live     实时看所有 DNS 查询"
    echo "  ad       只看被拦下来的广告域"
    echo "  dev      各设备查询量（看谁在用）"
    echo "  suspect  疑似广告域清单"
    echo "  top      查询量 Top30 域名"
    echo "  new      标记点之后的新增查询"
    echo "  one N    只盯某一台设备(默认150) —— ~/adblock-helper.sh one 150"
echo "  ad150    只看 .150 的广告域名组"
echo "  win [N]  最近 N 分钟(默认3)的所有查询 —— 看到广告就用这个"
echo "  mark     重置标记点"
    ;;
esac
