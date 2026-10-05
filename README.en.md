# 🏠 home-dns-adblock

**Home DNS ad-blocking — works at home, and away from home too.**

DNS-level ad blocking for Chinese "watch ads to unlock free content" apps
(红果免费短剧 / Fanqie Novel / other ByteDance apps).

**No root. No config profiles. No CA certificates. No app modification.**
Just a DNS blackhole running on an always-on Linux box.

- **At home** — point your device DNS at the box → ad domains answer `0.0.0.0`
- **Away** (4G / hotel WiFi) — a Tailscale tunnel carries DNS queries back home → same protection

---

## Why this exists

Generic DNS blocking is a solved problem:
[Pi-hole](https://github.com/pi-hole/pi-hole) (61k ⭐),
[AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) (37k ⭐).

This project solves a different problem:

| | Generic blockers | App Hook solutions | **This project** |
|---|---|---|---|
| Domain list | 100k+ broad rules | — | **198 precise rules** |
| App breakage | possible | — | **zero (whitelist protection)** |
| Root / jailbreak | not needed | **required** | **not needed** |
| Works away from home | ✗ | ✗ | **✓ via Tailscale** |
| Targets 红果 / 番茄 | ✗ | some | **✓ at DNS level** |

---

## Key techniques

### 1. Ad video vs. real video — one word apart

```
REAL   v11-reading-video.qznovelvod.com   ← allow
AD     v11-reading-ad.qznovelvod.com      ← block
                    ↑↑↑
```

Parent-domain whitelisting + precise child-domain blocking make
"block the ad videos" and "keep the real ones" hold simultaneously.
Without this trick you either keep the ads or break playback.

### 2. Finding ad domains without packet capture

No mitmproxy, no CA certificates. Just **timestamp clustering in DNS logs**:

> Ad domains are queried **only at the exact moment an ad appears**.

```bash
./scripts/adblock-helper.sh win 3    # cut a recent 3-minute query window
```

Six original domains (absent from every community list) were found this way.

### 3. Free "away from home" coverage

Tailscale hands out virtual LAN IPs, so your phone reaches the home DNS
from any network, with automatic NAT hole punching (39 ms direct, no relay).
Three traps are documented in `docs/pitfalls.md`:

- backend must have **"Override local DNS"** checked, or nothing works silently
- on iOS, **"VPN icon is on" ≠ "logged in"** (data plane stays dead)
- iOS allows **only one VPN at a time**

---

## Quick start

```bash
git clone https://github.com/abclq/home-dns-adblock.git
cd home-dns-adblock
sudo ./scripts/install.sh 192.168.1.2   # your LAN IP
sudo ./scripts/verify.sh                # 11-point self check
```

Then point your device DNS at that IP.
For away-from-home coverage see [`docs/tailscale-remote.md`](docs/tailscale-remote.md).

---

## Measured numbers (real home network)

| Metric | Value |
|--------|-------|
| Rules | **198** precise domains (no broad keyword rules) |
| Memory | **2.5 MB** |
| CPU | **0.0%** |
| Away-from-home latency | **39 ms** (Tailscale P2P direct, no relay) |
| False positives | **0** (video / image CDN / business APIs all intact) |
| Verified on | iOS + Ubuntu, including external WiFi (non-home network) |

---

## Limitations (no wishful thinking)

- **Live-stream ads** cannot be blocked — they share the video CDN domain with real content
- **Already-cached ads** cannot be blocked — DNS only sees new queries
- **DoH / system-level VPN** bypasses this entirely
- Verified on **iOS + Ubuntu** only; Android / OpenWrt / Synology welcome as contributions

---

## Documentation (Chinese, detailed)

| File | Content |
|------|---------|
| [README.md](README.md) | Main docs (Chinese) |
| [docs/principles.md](docs/principles.md) | How it works, incl. Tailscale hole punching |
| [docs/domain-list.md](docs/domain-list.md) | ★ **What to block vs. what must NEVER be blocked** |
| [docs/pitfalls.md](docs/pitfalls.md) | ★ **13 real pitfalls**, with diagnostic commands |
| [docs/tailscale-remote.md](docs/tailscale-remote.md) | Away-from-home setup, step by step |

---

## Credits

Rule bases: [honue/rules](https://github.com/honue/rules) ·
[chxm1023/Script_X](https://github.com/chxm1023/Script_X) ·
[anti-AD](https://github.com/privacy-protection-tools/anti-AD) ·
[AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule)

Networking: [Tailscale](https://tailscale.com/)

Full list in [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

**Author**: [@abclq](https://github.com/abclq) · **License**: MIT

> For personal study and home-network optimization only.
