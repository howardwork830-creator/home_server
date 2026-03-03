# Mac M1 Home Server + Telegram Remote Admin Bot

<!--
AI AGENT CONTEXT:
- This project runs a Telegram bot on a Mac M1 for comprehensive remote administration via phone
- Bot uses Claude for code generation, 69 allowlisted shell commands, system/network/process/package management
- All traffic goes through Tailscale VPN; visual monitoring via VNC over Tailscale
- Key constraints: command allowlist with subcommand restrictions, dangerous-pattern blocklist, Telegram 4096 char limit
- Reference: macOS-CLI-Guide.md contains the full macOS CLI command reference
-->

---

## Project Summary

| Field | Value |
|-------|-------|
| **Purpose** | Comprehensive remote Mac administration via Telegram — SSH-like control from phone, powered by Claude |
| **Platform** | Mac M1 (Apple Silicon), macOS Ventura+ |
| **Stack** | Python 3.12, python-telegram-bot v20+, Anthropic SDK, Tailscale VPN |
| **Working Dir** | `/Users/howard/Desktop/VS code file/home server` |
| **Bot Dir** | `/Users/howard/Desktop/VS code file/home server` |
| **Log Dir** | `/Users/howard/Desktop/VS code file/home server` (bot.log, bot_stdout.log, bot_stderr.log) |

---

## Architecture

```
Phone (Telegram App)              VNC Client (iPhone/iPad/Mac)
        │ HTTPS                           │ VNC over Tailscale
        ▼                                 ▼
Telegram Bot API                  macOS Screen Sharing
        │                                 │
        ▼                                 ▼
Mac M1 (Home) ────────────────────────────────────
  ├── Tailscale VPN (encrypted overlay network)
  ├── Telegram Bot (python-telegram-bot)
  │   ├── Shell commands (69 allowlisted)
  │   ├── System admin (disk, process, package, network)
  │   └── Claude AI agent (coding assistant)
  ├── Screen Stream Pipeline
  │   ├── screen_stream.py (capture → JPEG HTTP server :9999)
  │   ├── go2rtc (MJPEG→HLS/WebRTC relay :1984)
  │   └── miniapp/monitor.html (Telegram Mini App viewer)
  ├── Screen Sharing / VNC (full GUI access)
  └── Shell / Git / brew / tmux / tools
```

**Connectivity:** Tailscale (NAT traversal, secure overlay, no router config).
**UI:** Telegram bot (buttons + text) for command-line control; VNC for GUI access.
**AI:** Claude as coding assistant.
**Visual:** Full VNC over Tailscale for interactive GUI access.

References: [Tailscale macOS](https://tailscale.com/docs/concepts/macos-variants), [python-telegram-bot](https://python-telegram-bot.org), [Anthropic API](https://dev.to/engineerdan/generating-python-code-using-anthropic-api-for-claude-ai-4ma4), [macOS-CLI-Guide.md](macOS-CLI-Guide.md)

---

## Goals & Scope

### Goals

- Turn Mac M1 into 24/7 home administration server
- SSH-like control entirely from phone via Telegram bot
- Use Claude for code generation, refactoring, debugging, and "vibe coding"
- Full system monitoring: processes, disk, network, VNC
- Package management: Homebrew, macOS software updates
- Seamless enough to feel like controlling a Linux machine from a terminal

### Supported Capabilities

| Category | Commands / Features |
|----------|---------------------|
| **Files & Navigation** | `ls`, `pwd`, `cat`, `head`, `tail`, `grep`, `find`, `echo`, `wc`, `sort`, `tree`, `which`, `file`, `du`, `open` |
| **System Information** | `sw_vers`, `system_profiler`, `uname`, `hostname`, `date`, `whoami`, `uptime` |
| **Network & Diagnostics** | `ping`, `traceroute`, `dig`, `nslookup`, `netstat`, `lsof`, `ifconfig`, `networksetup`, `networkQuality`, `curl`, `wget`, `tailscale` |
| **Disk & Storage** | `df`, `diskutil`, `hdiutil`, `tmutil` |
| **Process Management** | `ps`, `top` (batch mode), `pgrep`, `kill`, `killall` |
| **Package Management** | `brew`, `softwareupdate`, `pkgutil`, `xcode-select` |
| **Audio & Media** | `afplay`, `say`, `sips`, `screencapture` |
| **Text Processing** | `sed`, `awk`, `uniq`, `pbcopy`, `pbpaste` |
| **Compression** | `tar`, `gzip`, `gunzip`, `zip`, `unzip` |
| **Automation** | `shortcuts`, `caffeinate` |
| **Development** | `python3`, `git`, `npm`, `npx`, `claude` |
| **Session Management** | `tmux` |
| **Git** | `git status`, `git add`, `git commit`, `git push`, `git log`, `git diff`, `git branch` |
| **Claude AI** | Code generation, refactoring, error explanation, file editing |
| **Claude chat** | `/chat` for interactive back-and-forth coding; `/exit` to leave |
| **Files** | Upload via Telegram → working dir; view via `cat` / `head` / `tail` |
| **Directory** | `/cd` to switch project; `/newproject` to create new project folder |
| **Live Monitor** | `/monitor` opens live HLS screen stream in Telegram Mini App (go2rtc) |
| **Visual Monitoring** | VNC over Tailscale for full GUI access |

### Hard Limits

| Limit | Value |
|-------|-------|
| Telegram message size | 4096 chars (must chunk output) |
| Command timeout | 300 seconds (run longer jobs in tmux) |
| Interactive TUI | Not supported (no `vim`, `nano`, `htop` over Telegram) |
| `top` command | Batch mode only (`-l 1`) — interactive mode not supported |
| VNC access | Requires separate VNC client app; not integrated into Telegram |

---

## Security Model

### Risks

- Bot token leak → attacker controls bot
- Weak command validation → destructive commands (`rm -rf`, `sudo`, etc.)
- Claude API key leak → API credit abuse
- Tailscale misconfig → unintended exposure
- Expanded command surface → more potential for abuse (mitigated by subcommand allowlists)

### Mitigations

- **User whitelist:** `AUTHORIZED_USER_IDS` in `.env`; only listed users can use bot
- **Allowlist:** 69 commands in `SAFE_COMMANDS`, each individually vetted for safety
- **Subcommand allowlists:** Per-command restrictions (e.g., `git` limited to safe subcommands, `diskutil` limited to read-only operations)
- **Argument injection defense:** Dangerous arguments blocked per-command (e.g., `find -exec`, `sort --compress-prog`)
- **Blocklist:** Regex patterns for `rm -rf`, `sudo`, `mkfs`, `chmod 777`, `reboot`, `shutdown`, `launchctl`, etc.
- **Working dir:** Bot runs in the configured `WORK_DIR`
- **Secrets:** `.env` with `chmod 600`, never in Git
- **Tailscale ACLs:** 2-device personal tailnet uses default ACLs (Mac + iPhone); acceptable for this threat model since both devices are owner-controlled

### Deferred Commands (Risky — Future Consideration)

| Command | Risk | Notes |
|---------|------|-------|
| `osascript` | AppleScript can execute arbitrary system actions | May add with sandboxed script allowlist |
| `defaults write` | Can modify system preferences | Read-only `defaults read` may be added first |
| `launchctl` | macOS service management | Needs its own subcommand allowlist |
| `sudo` | Root access | Permanently blocked |
| `dd`, `mkfs`, `reboot`, `shutdown` | Destructive operations | Permanently blocked |

---

## Visual Monitoring

### Live Screen Monitor

Three-component pipeline for near-real-time screen viewing inside Telegram:

```
screen_stream.py ──► go2rtc ──► miniapp/monitor.html
  (CoreGraphics      (MJPEG→HLS    (Telegram Mini App,
   capture, JPEG      relay,         JS frame polling,
   HTTP :9999)        port :1984)    hosted on GitHub Pages)
```

- **`screen_stream.py`** — Captures the display via CoreGraphics, serves JPEG frames on `/frame` and MJPEG on `/`
- **`go2rtc`** — Relays the MJPEG stream, provides HLS/WebRTC endpoints for the Mini App
- **`miniapp/monitor.html`** — Telegram WebApp that polls `/frame` for live updates; hosted on GitHub Pages

**Launch all services:** `python3 start_all.py` (starts screen_stream, go2rtc, and bot together; Ctrl+C stops all)

### Full GUI Access via VNC

For interactive visual control, macOS built-in Screen Sharing runs over Tailscale:

```
iPhone/iPad/Mac ──── Tailscale tunnel (encrypted) ──── Mac M1
   VNC Client                                        Screen Sharing
```

**Setup:**
1. Enable Screen Sharing: System Settings → General → Sharing → Screen Sharing → On
2. Connect from any tailnet device using the Mac's Tailscale IP (`vnc://100.94.x.x`)
3. On iPhone/iPad: use a VNC client app (Screens, RealVNC, etc.)

**When to use which:**
- **Telegram bot** — Quick commands, status checks, file operations, coding with Claude
- **VNC** — GUI-heavy tasks, visual debugging, app interactions requiring mouse/keyboard

---

## Requirements

### Hardware

- Mac with Apple Silicon (M1/M2/M3)
- 8GB+ RAM (16GB recommended)
- ≥ 20GB free disk
- Always plugged in (24/7)
- Stable internet (≥ 5 Mbps upload)

### Software

- macOS Ventura (13.x) or newer
- Homebrew, Python 3.10+ (3.12 recommended)
- Tailscale, Git, tmux

### Accounts

- Telegram, Tailscale, Anthropic (Claude API key with billing)

---

## Environment Variables

Location: `/Users/howard/Desktop/VS code file/home server/.env`
Permissions: `chmod 600`

```env
TELEGRAM_BOT_TOKEN=123456789:ABC...
AUTHORIZED_USER_IDS=123456789
ANTHROPIC_API_KEY=sk-ant-...
WORK_DIR=/Users/howard/Desktop/VS code file/home server
LOG_FILE=/Users/howard/Desktop/VS code file/home server/bot.log
LOG_LEVEL=INFO
```

---

## Setup Steps

### 1. Prepare Mac

```bash
# Install tools
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
brew install python@3.12 git tmux htop wget tree

# Prevent sleep on power
sudo pmset -c sleep 0
sudo pmset -c displaysleep 10
sudo pmset -c disksleep 0
sudo pmset -c autopoweroff 0

# Bot lives in: /Users/howard/Desktop/VS code file/home server
```

### 2. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4    # Record IP (e.g. 100.94.x.x)
```

### 3. Enable Screen Sharing (VNC)

1. System Settings → General → Sharing → Screen Sharing → On
2. Set a VNC password when prompted
3. Connect from tailnet devices using `vnc://<tailscale-ip>`

### 4. Create Telegram Bot

1. Telegram → `@BotFather` → `/newbot`
2. Get `BOT_TOKEN`
3. `/setprivacy` → Disable (so bot sees all messages)
4. Get your `USER_ID` via `@userinfobot`

### 5. Claude

- Anthropic console → create API key, enable billing
- `pip3 install anthropic`

### 6. Bot Dependencies

```bash
cd "/Users/howard/Desktop/VS code file/home server"
pip3 install python-telegram-bot anthropic aiofiles python-dotenv
```

---

## Bot Design (Implementation Reference)

### Tech Stack

- `python-telegram-bot` v20+
- `anthropic` Python client
- `asyncio` + `subprocess` for shell
- `python-dotenv` for config

### Command Handlers

| Command | Behavior |
|---------|----------|
| `/start` | Auth check; show buttons: Shell, Claude, Files, Status, tmux, Git, CD, Chat, New Project |
| `/help` | Describe supported commands and limits |
| `/status` | Run `df -h`, `uptime`, optional `tailscale status` |
| `/claude <prompt>` | Send prompt to Claude, return response (chunked) |
| `/claude_continue <prompt>` | Continue the last Claude conversation |
| `/chat` | Enter interactive Claude chat mode (back-and-forth coding) |
| `/exit` | Leave chat mode |
| `/cd` | Select a project directory from Desktop folders |
| `/newproject <name>` | Create a new project folder on Desktop and switch to it |
| `/network` | Run network diagnostics (interfaces, public IP, connectivity) |
| `/monitor` | Open live screen monitor (Telegram Mini App via go2rtc HLS) |
| Plain text | Treated as shell command (allowlist + blocklist); routed to Claude in chat mode |
| Document | Save to `WORK_DIR`, confirm path |

### Safety Logic

- Parse command → check base command in `SAFE_COMMANDS` (69 commands) → check per-command argument restrictions → check against `DANGEROUS_PATTERNS` regex
- `os.chdir(WORK_DIR)` before running
- Async subprocess with timeout (300s); group kill on timeout
- Output split into ≤ 4000-char chunks for Telegram

---

## LaunchAgent (Run as Service)

File: `~/Library/LaunchAgents/com.howard.telegrambot.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.howard.telegrambot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Library/Frameworks/Python.framework/Versions/3.13/bin/python3</string>
        <string>/Users/howard/Desktop/VS code file/home server/bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/howard/Desktop/VS code file/home server</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/howard/Desktop/VS code file/home server/bot_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/howard/Desktop/VS code file/home server/bot_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/howard/.npm-global/bin:/opt/homebrew/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.howard.telegrambot.plist
launchctl list | grep telegrambot
```

---

## Usage Reference

### Typical Flow (Phone over 4G)

1. Turn on Tailscale VPN on phone
2. Open Telegram bot chat
3. `/status` → check disk, uptime
4. `/claude <prompt>` for coding help
5. Run commands: `python3 main.py`, `git status`, etc.
6. Open VNC client for full visual control when needed

### Command Cheat Sheet

```text
# Files
ls -la | pwd | cat file | head -50 log | tail -50 log | tree -L 2

# Git
git status | git add . | git commit -m "msg" | git push

# System Info
sw_vers | system_profiler SPHardwareDataType | uname -a | uptime | whoami

# Network
ping -c 4 google.com | traceroute 8.8.8.8 | dig example.com
networkQuality | ifconfig en0 | netstat -an | lsof -i :8080
tailscale status

# Disk & Storage
df -h | diskutil list | du -sh * | tmutil listbackups

# Processes
ps aux | pgrep -l python | top -l 1 -n 10 | kill 12345

# Packages
brew update | brew list | brew install <pkg> | softwareupdate -l

# Audio & Media
say "hello" | screencapture -x /tmp/screen.png | sips --getProperty pixelWidth img.png

# Compression
tar czf archive.tar.gz dir/ | unzip file.zip | gzip file.txt

# Automation
caffeinate -t 3600 | shortcuts list

# Claude
/claude 幫我重構這段程式碼
/claude 解釋這個錯誤訊息

```

---

## Maintenance

| Frequency | Tasks |
|-----------|-------|
| Weekly | `brew update && brew upgrade`; check `bot.log` |
| Monthly | Rotate Claude API key; review Tailscale ACLs; check disk < 80% |

---

## Reality Check

| Can | Cannot |
|-----|--------|
| Remote admin via phone — shell, files, git, processes, packages, network | Full interactive TUI (vim, htop) over Telegram |
| Live screen stream via /monitor (HLS in Telegram Mini App) | Sub-second latency (HLS has 3-6s delay) |
| Full GUI control via VNC over Tailscale | VNC integrated into Telegram (requires separate client) |
| Most daily dev + sysadmin tasks | Zero security risk (deliberate remote command surface) |
| Install/update packages via Homebrew | Run arbitrary scripts without allowlist approval |
| Monitor and kill processes | Run `sudo` or modify system-level settings |

**Trade-off:** Convenience vs. complexity + residual risk. Design reduces risk but does not eliminate it. The expanded command set increases the attack surface but each command is individually vetted, and subcommand allowlists limit what can be done with powerful tools.
