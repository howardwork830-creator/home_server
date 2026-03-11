# Mac M1 Home Server — Telegram Remote Admin

A Telegram bot for comprehensive remote administration of a Mac M1 home server. Execute shell commands, manage system resources, run Claude AI coding sessions, monitor network status, control packages and processes — all from Telegram.

## Features

- **Persistent terminal sessions** — Up to 3 concurrent tmux-backed terminals per user; `cd`, env vars, and state persist between commands
- **Shell commands** — Run allowlisted commands (`ls`, `git status`, `python3 script.py`, `brew update`, etc.) with input validation and output scrubbing
- **System administration** — Check disk usage, system info, process management, package updates
- **Network diagnostics** — Ping, traceroute, DNS lookups, interface info, connection quality testing
- **Claude AI agent** — Full coding assistant that can read, edit, and create files with controlled permissions
- **Claude chat mode** — `/chat` enters interactive back-and-forth coding with Claude; `/exit` to leave
- **Live screen monitor** — `/monitor` opens a live HLS stream in a Telegram Mini App (go2rtc + M1 hardware encoding)
- **Visual monitoring** — macOS Screen Sharing (VNC) over Tailscale for full GUI access
- **File uploads** — Send documents to save them to the working directory
- **Directory switching** — `/cd` to pick a project folder on Desktop; `/newproject` to create one
- **Process management** — List, search, and kill processes
- **Package management** — Homebrew operations, macOS software updates
- **Audio & media** — Text-to-speech, image processing, audio playback
- **Compression** — Archive and extract files (tar, zip, gzip)
- **Quick tools grid** — `/tools` for one-tap access to common shell commands (files, system, network, dev)
- **Steam Remote Play** — `/steam` to start/stop Steam, enter Big Picture mode, launch games from an allowlist, and get Steam Link setup tips
- **Terminal management** — `/t` to list, create, switch, and close persistent terminals
- **Tmux control** — List and send commands to tmux sessions
- **System status** — Uptime, disk usage, and Tailscale status
- **Command menu** — Type `/` in Telegram to see all available commands

## Quick Start

### 1. Prerequisites

- Python 3.11+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))

### 2. Install

```bash
cd "home server"
pip install -r requirements.txt
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=your-bot-token-here
AUTHORIZED_USER_IDS=123456789
WORK_DIR=/path/to/your/working/directory
LOG_FILE=/path/to/bot.log
LOG_LEVEL=INFO
```

Find your Telegram user ID by messaging [@userinfobot](https://t.me/userinfobot). Multiple users can be comma-separated.

### 4. Run

```bash
# Bot only
python3 bot.py

# All services (bot + screen stream + go2rtc)
python3 main.py

# Selective services
python3 main.py --bot              # bot only (via unified launcher)
python3 main.py --no-go2rtc        # skip go2rtc relay
python3 main.py --port 8888        # custom stream port
python3 main.py -C ~/projects      # change working directory
```

## Commands

| Command | Description |
|---|---|
| `/start` | Show main menu with keyboard buttons |
| `/help` | List all commands and allowed shell commands |
| `/claude <prompt>` | Start a Claude AI coding session |
| `/claude_continue <prompt>` | Continue the last Claude conversation |
| `/chat` | Enter interactive Claude chat mode |
| `/exit` | Leave chat mode |
| `/cd` | Select a project directory (Desktop folders) |
| `/newproject <name>` | Create a new project folder on Desktop |
| `/status` | System status (uptime, disk, Tailscale) |
| `/network` | Network diagnostics (interfaces, public IP, connectivity) |
| `/t` | List terminal sessions |
| `/t new [name]` | Create a new persistent terminal (max 3) |
| `/t <id>` | Switch active terminal |
| `/t close <id>` | Close a terminal |
| `/tmux ls` | List tmux sessions |
| `/tmux send <session> <cmd>` | Send a command to a tmux session |
| `/getfile <path>` | Download a file from server |
| `/app` | List, launch, or quit applications |
| `/tools` | Quick tools grid (files, system, network, dev) |
| `/steam` | Control Steam & Remote Play (status, start, quit, bigpicture, play, games, tips) |
| `/sysinfo` | Detailed system info (battery, memory, hardware) |
| `/monitor` | Open live screen monitor (Telegram Mini App) |
| `exit` | Close the active terminal |
| *plain text* | Execute as a shell command (in active terminal) |
| *file upload* | Save document to working directory |

## Claude AI Agent

The `/claude` command runs Claude in full agent mode. Claude can:

- **Read** files in the workspace
- **Search** files with glob patterns and grep
- **Edit** and **create** files (with confirmation)
- **Run** `git`, `python3`, `ls`, and `cat` commands

Claude **cannot**:
- Run unrestricted shell commands
- Access `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.config`, or `.env` files
- Run `sudo`, `rm -rf`, or destructive commands
- Exceed $1.00 API spend per request

### Session Continuity

After a `/claude` session, use `/claude_continue <follow-up>` to resume the same conversation. The session ID is stored per-user.

## Visual Monitoring

### Live Screen Monitor (Telegram Mini App)

Use `/monitor` in Telegram to capture a screenshot instantly, or tap "Open Live Monitor" for a near-real-time screen feed inside Telegram — no separate VNC client needed.

**Pipeline:** `screen_stream.py` (capture) → `go2rtc` (relay) → `miniapp/monitor.html` (viewer)

**Setup:**
1. Download the [go2rtc binary for Apple Silicon](https://github.com/AlexxIT/go2rtc/releases) and place it in the project directory
2. Set `GO2RTC_HOST` in `.env` to your Mac's Tailscale IP + port (e.g., `100.94.x.x:1984`)
3. Set `MINIAPP_BASE_URL` in `.env` to your GitHub Pages URL
4. Start all services: `python3 main.py` (or start individually: `python3 screen_stream.py`, `./go2rtc`, `python3 bot.py`)
5. In Telegram: `/monitor` → tap "Open Live Monitor"

The "Open Live Monitor" button only appears when `GO2RTC_HOST` and `MINIAPP_BASE_URL` are set. Without them, `/monitor` still works as a screenshot tool with a Refresh button.

### Full GUI Access via VNC

For interactive visual control, use macOS built-in Screen Sharing over Tailscale:

1. **Enable Screen Sharing** on the Mac: System Settings → General → Sharing → Screen Sharing → On
2. **Connect via Tailscale IP**: From any device on your tailnet, open a VNC client and connect to the Mac's Tailscale IP (e.g., `vnc://100.94.x.x`)
3. **On iPhone/iPad**: Use a VNC client app (e.g., Screens, RealVNC) pointing to the Tailscale IP

This gives full mouse/keyboard GUI control — useful for tasks that require visual interaction beyond what Telegram text commands can provide. Traffic is encrypted end-to-end by Tailscale.

## Security

### Defense Layers

| Layer | What it does |
|---|---|
| **User authorization** | Only Telegram user IDs in `AUTHORIZED_USER_IDS` can interact |
| **Command allowlist** | Only 72 vetted commands can be executed |
| **Subcommand allowlists** | Per-command restrictions (e.g., only safe `git` and `diskutil` subcommands) |
| **Shell metacharacter blocking** | `;`, `&&`, `\|\|`, `` ` ``, `$(`, `<(`, `>(` are rejected |
| **Argument injection defense** | `find -exec`, `sort --compress-prog`, `grep --pre`, `python3 -c` blocked |
| **Path guard** | Arguments resolving to sensitive paths are rejected |
| **Dangerous pattern filter** | `rm -rf`, `sudo`, `mkfs`, `chmod 777`, `reboot`, etc. blocked |
| **Git subcommand allowlist** | Only `status`, `add`, `commit`, `push`, `log`, `diff`, `branch` |
| **Claude tool allowlist** | Only `Read`, `Glob`, `Grep`, `Edit`, `Write`, and restricted `Bash` |
| **Claude system prompt** | Injected rules forbidding access to secrets and destructive ops |
| **Claude budget cap** | $1.00 max API spend per request |
| **Output scrubbing** | API keys, tokens, and `PASSWORD=`/`SECRET=` lines redacted before sending |
| **Rate limiting** | 20 shell commands/minute, 5 Claude requests/minute per user |
| **Output size cap** | Truncate at 50KB to prevent memory issues and Telegram spam |
| **Audit log** | Every action logged to `audit.jsonl` (never logs command output) |
| **Connection resilience** | TCP keepalive (60s), polling timeouts, NetworkError auto-retry, child process auto-restart |

### Deferred (Risky) Commands

These commands are intentionally **not** in the allowlist due to their risk profile. They may be added in the future with appropriate safeguards:

- `osascript` — AppleScript can execute arbitrary system actions
- `defaults write` — Can modify system preferences (read-only `defaults read` may be added)
- `launchctl` — macOS service management (needs its own subcommand allowlist)
- `sudo`, `dd`, `mkfs`, `reboot`, `shutdown` — Permanently blocked

### Blocked Sensitive Paths

Any command argument resolving to these locations is rejected:

- `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.docker/`, `~/.config/`
- `~/.zshrc`, `~/.bashrc`, `~/.zsh_history`, `~/.bash_history`
- `~/Library/Keychains/`
- `/etc/passwd`, `/etc/shadow`
- Any `.env` file

### Output Scrubbing

Before sending output to Telegram, these patterns are redacted to `[REDACTED]`:

- Anthropic keys (`sk-ant-...`)
- OpenAI keys (`sk-...`)
- GitHub PATs (`ghp_...`)
- Slack tokens (`xoxb-...`)
- Telegram bot tokens (`123456:ABC...`)
- Lines matching `PASSWORD=`, `SECRET=`, `TOKEN=`, `KEY=`

### Audit Log

Every action is recorded in `audit.jsonl`:

```json
{"ts": "2026-03-01T12:00:00+00:00", "user_id": 123, "action": "shell", "prompt": "ls -la", "result": "ok", "duration_s": 0.12}
{"ts": "2026-03-01T12:00:05+00:00", "user_id": 123, "action": "claude", "prompt": "Write fizzbuzz", "result": "ok", "duration_s": 8.5}
```

Command output is never logged (could contain secrets).

## Project Structure

```
home server/
├── bot.py                     # Entry point — handlers, polling with TCP keepalive
├── main.py                    # Unified CLI launcher with auto-restart (--bot, --stream, --no-go2rtc)
├── screen_stream.py           # Screen capture HTTP server (MJPEG + /frame)
├── test_security.py           # Security test suite (424 tests)
├── config/                    # Configuration (split by concern)
│   ├── __init__.py            #   Re-exports everything for backward compat
│   ├── env.py                 #   Environment variables, paths, tokens
│   ├── commands.py            #   Allowlists, blocklists, validation rules
│   ├── security.py            #   Sensitive paths, secret patterns, app allowlist
│   ├── steam.py               #   Steam game allowlist, app path
│   ├── claude.py              #   Claude AI agent settings
│   ├── limits.py              #   Timeouts, rate limits, size constraints, polling/keepalive
│   └── logging_setup.py       #   Logging configuration + logger
├── handlers/                  # Telegram command handlers (by domain)
│   ├── auth.py                #   @authorized decorator (access control)
│   ├── shell.py               #   Plain text → terminal execution (catch-all)
│   ├── terminal.py            #   /t persistent terminal sessions
│   ├── start.py               #   /start welcome, /help command list
│   ├── claude.py              #   /claude, /chat, /exit, /claude_continue
│   ├── status.py              #   /status (uptime, disk, Tailscale)
│   ├── sysinfo.py             #   /sysinfo (battery, memory, hardware)
│   ├── network.py             #   /network diagnostics
│   ├── monitor.py             #   /monitor live screen capture
│   ├── app.py                 #   /app launch/quit applications
│   ├── steam.py               #   /steam control Steam & Remote Play
│   ├── tools.py               #   /tools quick-action button grid
│   ├── tmux.py                #   /tmux raw session control
│   ├── cd.py                  #   /cd directory selector
│   ├── newproject.py          #   /newproject create project folder
│   ├── files.py               #   Document upload handler
│   └── getfile.py             #   /getfile download to Telegram
├── utils/                     # Shared utilities
│   ├── command_validator.py   #   7-layer command validation pipeline
│   ├── terminal_manager.py    #   tmux session lifecycle
│   ├── subprocess_runner.py   #   Async shell execution + timeout
│   ├── path_guard.py          #   Sensitive path blocking
│   ├── scrubber.py            #   Secret redaction from output
│   ├── rate_limiter.py        #   Sliding window rate limiter
│   ├── chunker.py             #   Split text for Telegram's limit
│   ├── claude_stream.py       #   Parse Claude CLI stream-json
│   └── audit.py               #   Structured JSONL audit logging
├── miniapp/
│   └── monitor.html           #   Telegram Mini App — live screen viewer
├── docs/
│   ├── USER-MANUAL.md         #   End-user Telegram bot manual
│   ├── project.md             #   Project design & architecture reference
│   └── macOS-CLI-Guide.md     #   macOS CLI command reference
└── deploy/
    └── com.howard.telegrambot.plist  # macOS LaunchAgent config
```

## Allowed Shell Commands

### Files & Navigation

```
ls, pwd, cat, head, tail, grep, find, echo, wc, sort, tree, which, file, du, open
```

### System Information

```
sw_vers, system_profiler, uname, hostname, date, whoami, uptime
```

### Network & Diagnostics

```
ping, traceroute, dig, nslookup, netstat, lsof, ifconfig, networksetup, networkQuality, curl, wget, tailscale
```

### Disk & Storage

```
df, diskutil, hdiutil, tmutil
```

### Process Management

```
ps, top (batch mode only), pgrep, kill, killall
```

### Package Management

```
brew, softwareupdate, pkgutil, xcode-select
```

### Audio & Media

```
afplay, say, sips, screencapture
```

### Text Processing

```
sed, awk, uniq, pbcopy, pbpaste
```

### Compression

```
tar, gzip, gunzip, zip, unzip
```

### Automation

```
shortcuts, caffeinate
```

### Development

```
python3, git, npm, npx, claude
```

### Session Management

```
tmux
```

### Utilities

```
trash, mdfind, mdls
```

Pipes (`|`) are supported between allowlisted commands. All other shell operators are blocked.

## Documentation

- **[User Manual](docs/USER-MANUAL.md)** — Complete guide for Telegram bot users
- **[Project Design](docs/project.md)** — Architecture, security model, and setup reference
- **[macOS CLI Guide](docs/macOS-CLI-Guide.md)** — Full macOS command reference

## Running Tests

```bash
python3 test_security.py
```

Runs 424 tests covering all security layers: metacharacter blocking, argument injection defense, path guards, output scrubbing, rate limiting, audit logging, stream parsing, output capping, and command validation.
