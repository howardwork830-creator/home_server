# Mac M1 Home Server + Telegram Coding Bot

<!--
AI AGENT CONTEXT:
- This project runs a Telegram bot on a Mac M1 that enables remote coding via phone
- Bot uses Claude for code generation, shell commands, Git, and file uploads
- All traffic goes through Tailscale VPN
- Key constraints: command allowlist, dangerous-pattern blocklist, Telegram 4096 char limit
-->

---

## Project Summary

| Field | Value |
|-------|-------|
| **Purpose** | Remote coding server controlled from phone via Telegram, powered by Claude |
| **Platform** | Mac M1 (Apple Silicon), macOS Ventura+ |
| **Stack** | Python 3.12, python-telegram-bot v20+, Anthropic SDK, Tailscale VPN |
| **Working Dir** | `~/Server/Projects` |
| **Bot Dir** | `~/Server/TelegramBot` |
| **Log Dir** | `~/Server/Logs` |

---

## Architecture

```
Phone (Telegram App)
        │ HTTPS
        ▼
Telegram Bot API
        │
        ▼
Mac M1 (Home)
  ├── Tailscale VPN
  ├── Telegram Bot (python-telegram-bot)
  ├── Claude client (Anthropic SDK)
  └── Shell / Git / tmux / tools
```

**Connectivity:** Tailscale (NAT traversal, secure overlay, no router config).  
**UI:** Telegram bot (buttons + text).  
**AI:** Claude as coding assistant.

References: [Tailscale macOS](https://tailscale.com/docs/concepts/macos-variants), [python-telegram-bot](https://python-telegram-bot.org), [Anthropic API](https://dev.to/engineerdan/generating-python-code-using-anthropic-api-for-claude-ai-4ma4)

---

## Goals & Scope

### Goals

- Turn Mac M1 into 24/7 home dev server
- Control entirely from phone via Telegram bot
- Use Claude for code generation, refactoring, debugging, and “vibe coding”

### Supported Capabilities

| Category | Commands / Features |
|----------|---------------------|
| **Shell** | `ls`, `pwd`, `cat`, `head`, `tail`, `grep`, `find`, `ps`, `df`, `uptime` (non-interactive only) |
| **Git** | `git status`, `git add`, `git commit`, `git push` |
| **Claude** | Code generation, refactoring, error explanation |
| **Files** | Upload via Telegram → `~/Server/Projects`; view via `cat` / `head` / `tail` |
| **Status** | `df -h`, `uptime`, process/memory snapshots |
| **tmux** | List sessions; send simple non-interactive commands |

### Hard Limits

| Limit | Value |
|-------|-------|
| Telegram message size | 4096 chars (must chunk output) |
| Command timeout | ~30 seconds (run long jobs in tmux) |
| Interactive TUI | Not supported (no `vim`, `nano`, `htop` over Telegram) |

---

## Security Model

### Risks

- Bot token leak → attacker controls bot
- Weak command validation → destructive commands (`rm -rf`, `sudo`, etc.)
- Claude API key leak → API credit abuse
- Tailscale misconfig → unintended exposure

### Mitigations

- **User whitelist:** `AUTHORIZED_USER_IDS` in `.env`; only listed users can use bot
- **Allowlist:** Only base commands in `SAFE_COMMANDS` (e.g. `ls`, `git`, `python3`, `df`, `ps`, `tmux`, `tailscale`)
- **Blocklist:** Regex patterns for `rm -rf`, `sudo rm`, `mkfs`, `chmod 777`, `reboot`, `shutdown`, etc.
- **Working dir:** Bot runs in `~/Server/Projects` only
- **Secrets:** `.env` with `chmod 600`, never in Git
- **Tailscale ACLs:** Restrict devices and ports

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

Location: `~/Server/TelegramBot/.env`  
Permissions: `chmod 600`

```env
TELEGRAM_BOT_TOKEN=123456789:ABC...
AUTHORIZED_USER_IDS=123456789
ANTHROPIC_API_KEY=sk-ant-...
WORK_DIR=/Users/yourname/Server/Projects
LOG_FILE=/Users/yourname/Server/Logs/bot.log
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

# Create dirs
mkdir -p ~/Server/{Projects,Logs,Backups,TelegramBot}
```

### 2. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4    # Record IP (e.g. 100.94.x.x)
```

### 3. Create Telegram Bot

1. Telegram → `@BotFather` → `/newbot`
2. Get `BOT_TOKEN`
3. `/setprivacy` → Disable (so bot sees all messages)
4. Get your `USER_ID` via `@userinfobot`

### 4. Claude

- Anthropic console → create API key, enable billing
- `pip3 install anthropic`

### 5. Bot Dependencies

```bash
cd ~/Server/TelegramBot
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
| `/start` | Auth check; show buttons: Shell, Claude, Files, Status, tmux, Git |
| `/help` | Describe supported commands and limits |
| `/status` | Run `df -h`, `uptime`, optional `tailscale status` |
| `/claude <prompt>` | Send prompt to Claude, return response (chunked) |
| Plain text | Treated as shell command (allowlist + blocklist) |
| Document | Save to `WORK_DIR`, confirm path |

### Safety Logic

- Parse command → check base command in `SAFE_COMMANDS` → check against `DANGEROUS_PATTERNS` regex
- `os.chdir(WORK_DIR)` before running
- Async subprocess with timeout; group kill on timeout
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
        <string>/opt/homebrew/bin/python3</string>
        <string>/Users/yourname/Server/TelegramBot/bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/Server/TelegramBot</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict><key>SuccessfulExit</key><false/></dict>
    <key>StandardOutPath</key>
    <string>/Users/yourname/Server/Logs/bot_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourname/Server/Logs/bot_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
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

### Command Cheat Sheet

```text
# Files
ls -la | pwd | cat file | head -50 log | tail -50 log | tree -L 2

# Git
git status | git add . | git commit -m "msg" | git push

# System
df -h | uptime | tailscale status | ps aux --sort=-%mem | head -10

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
| Remote coding via phone + Claude | Full interactive TUI (vim, htop) over Telegram |
| Most daily dev tasks (code, run, commit, push) | Zero security risk (deliberate remote command surface) |

**Trade-off:** Convenience vs. complexity + residual risk. Design reduces risk but does not eliminate it.
