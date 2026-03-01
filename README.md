# Mac M1 Home Server — Telegram Bot

A Telegram bot for remote control of a Mac M1 home server. Execute shell commands, run Claude AI coding sessions, upload files, manage tmux sessions, and monitor system status — all from Telegram.

## Features

- **Shell commands** — Run allowlisted commands (`ls`, `git status`, `python3 script.py`, etc.) with input validation and output scrubbing
- **Claude AI agent** — Full coding assistant that can read, edit, and create files with controlled permissions
- **Claude chat mode** — `/chat` enters interactive back-and-forth coding with Claude; `/exit` to leave
- **File uploads** — Send documents to save them to the working directory
- **Directory switching** — `/cd` to pick a project folder on Desktop; `/newproject` to create one
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
python3 bot.py
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
| `/tmux ls` | List tmux sessions |
| `/tmux send <session> <cmd>` | Send a command to a tmux session |
| *plain text* | Execute as a shell command |
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

## Security

### Defense Layers

| Layer | What it does |
|---|---|
| **User authorization** | Only Telegram user IDs in `AUTHORIZED_USER_IDS` can interact |
| **Command allowlist** | Only 24 safe commands can be executed |
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
├── bot.py                     # Entry point — handler registration and polling
├── config.py                  # All configuration, constants, and security rules
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── handlers/
│   ├── auth.py                # @authorized decorator + audit logging
│   ├── claude.py              # /claude and /claude_continue handlers
│   ├── cd.py                  # /cd directory selector handler
│   ├── newproject.py          # /newproject project creation handler
│   ├── shell.py               # Shell command validation and execution
│   ├── files.py               # File upload handler
│   ├── start.py               # /start and /help handlers
│   ├── status.py              # /status handler
│   ├── tmux.py                # /tmux handler
│   └── git_cmd.py             # Git subcommand validation helper
└── utils/
    ├── subprocess_runner.py   # Async command execution with timeout + output cap
    ├── chunker.py             # Split text for Telegram's message limit
    ├── claude_stream.py       # Parse Claude CLI stream-json output
    ├── path_guard.py          # Sensitive path blocking
    ├── scrubber.py            # Secret redaction from output
    ├── rate_limiter.py        # Sliding window rate limiter
    └── audit.py               # Structured JSON audit logging
```

## Allowed Shell Commands

```
ls, pwd, cat, head, tail, grep, find, ps, df, uptime, echo, wc, sort,
tree, which, file, du, date, whoami, python3, git, tmux, tailscale, claude
```

Pipes (`|`) are supported between allowlisted commands. All other shell operators are blocked.

## Running Tests

```bash
python3 test_security.py
```

Runs 173 tests covering all security layers: metacharacter blocking, argument injection defense, path guards, output scrubbing, rate limiting, audit logging, stream parsing, output capping, and command validation.
