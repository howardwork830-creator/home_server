# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A security-hardened Telegram bot that serves as a remote coding assistant on a Mac M1 home server. Users interact via Telegram to run shell commands, invoke Claude AI as a coding agent, manage files, and control tmux sessions. The bot enforces 15 defense layers to prevent unauthorized access and dangerous operations.

## Commands

```bash
# Run the bot only
python3 bot.py

# Run all services (bot + screen stream + go2rtc)
python3 main.py

# Run all 424 security tests
python3 test_security.py

# Install dependencies
pip install -r requirements.txt
```

There is no separate lint or build step. The test suite (`test_security.py`) uses a custom `test()` function with no external test runner.

## Architecture

**Entry point:** `bot.py` registers Telegram handlers and starts polling with configured timeouts, TCP keepalive (SO_KEEPALIVE + TCP_KEEPALIVE), and a `NetworkError` handler for automatic recovery from Tailscale/NAT connection drops. Plain text messages are routed to `shell_handler` as a catch-all (must be registered last).

**Handler pattern:** Each handler in `handlers/` is decorated with `@authorized` (from `handlers/auth.py`) which checks the user's Telegram ID against `AUTHORIZED_USER_IDS` and logs to the audit trail. Handlers receive `(update, context)` and use `context.user_data` for per-user state (`working_dir`, `claude_session_id`, `claude_chat_mode`, `terminals`, `active_terminal`).

**Command validation pipeline** (`utils/command_validator.py` → `validate_command()`):
1. Block shell metacharacters (`;`, `&&`, `||`, `` ` ``, `$(`, etc.)
2. Block dangerous patterns via regex (sudo, rm -rf, reboot, etc.)
3. Block sensitive paths via `utils/path_guard.py`
4. Split by pipe `|`, parse each segment with `shlex`
5. Check base command against `SAFE_COMMANDS` allowlist
6. Check per-command dangerous arguments (`DANGEROUS_ARGS`)
7. Validate subcommands against `SUBCOMMAND_ALLOWLISTS`

**Screen Monitor Pipeline:** Three services work together for live screen viewing in Telegram:
- `screen_stream.py` — CoreGraphics screen capture, serves JPEG frames over HTTP (port 9999)
- `go2rtc` — Relays the MJPEG stream as HLS/WebRTC (port 1984); optional, binary not in git
- `miniapp/monitor.html` — Telegram Mini App that polls frames for live updates (hosted on GitHub Pages)
- `main.py` — Unified CLI launcher for all services with selective flags (`--bot`, `--stream`, `--no-go2rtc`, etc.) and auto-restart of crashed child processes (up to 10 restarts per service)

**Persistent terminal sessions** (`handlers/terminal.py` + `utils/terminal_manager.py`): Shell commands run inside tmux-backed persistent terminals (up to 3 per user). State (working directory, env vars) persists between commands. Output is captured via temp files with `tmux wait-for` synchronization. The `/t` command manages terminals (list, new, switch, close). Typing `exit` as a plain-text message closes the active terminal.

**Inline Keyboard Callback pattern:** Many handlers use a dual-function pattern — a command handler sends an `InlineKeyboardMarkup`, and a `CallbackQueryHandler` handles button taps. Callback data uses unique prefixes per handler (`br:/cd/cdset:` for cd, `stm:` for steam, `app:` for app, `term:` for terminal, `tl:` for tools, `monitor_refresh` for monitor). Callback handlers perform manual auth checks against `AUTHORIZED_USER_IDS` since the `@authorized` decorator expects `update.message`.

**Claude integration** (`handlers/claude.py`): Invokes the `claude` CLI in agent mode with `--output-format stream-json`. Output is parsed by `utils/claude_stream.py`, buffered for 3-second intervals, and sent to Telegram in chunks. Tool access is restricted to `CLAUDE_ALLOWED_TOOLS` in config.

**Utilities in `utils/`:**
- `command_validator.py` — 7-layer command validation pipeline (extracted from shell.py)
- `terminal_manager.py` — Stateless tmux session lifecycle helpers (create, kill, run_in_session)
- `path_guard.py` — Resolves and blocks access to sensitive paths (pre-expanded at import time)
- `scrubber.py` — Redacts API keys and secrets from output using `SECRET_PATTERNS`
- `rate_limiter.py` — Sliding window rate limiter (20 shell/min, 5 Claude/min)
- `subprocess_runner.py` — Async execution with timeout and process group cleanup
- `audit.py` — Structured JSONL audit logging (never logs command output)
- `chunker.py` — Splits output into Telegram-safe 4000-char chunks

## Key Configuration (`config/`)

Configuration is split into focused modules under the `config/` package. All imports like `from config import SAFE_COMMANDS` work unchanged — `config/__init__.py` re-exports everything.

| Module | Contents |
|--------|----------|
| `config/env.py` | Environment variables, paths, tokens (loads `.env`) |
| `config/commands.py` | `SAFE_COMMANDS`, `DANGEROUS_PATTERNS`, `DANGEROUS_ARGS`, `SUBCOMMAND_ALLOWLISTS` |
| `config/security.py` | `BLOCKED_PATHS`, `SECRET_PATTERNS`, `APP_LAUNCH_ALLOWLIST` |
| `config/steam.py` | `STEAM_GAMES`, `STEAM_APP_PATH` |
| `config/claude.py` | `CLAUDE_ALLOWED_TOOLS`, `CLAUDE_SYSTEM_PROMPT`, `CLAUDE_MAX_BUDGET_USD` |
| `config/limits.py` | Timeouts, rate limits, size caps, `MAX_TERMINALS`, polling/keepalive constants |
| `config/logging_setup.py` | Logging configuration and `logger` instance |

## Adding a New Handler

1. Create `handlers/new_handler.py` with an async function taking `(update, context)`
2. Decorate with `@authorized` from `handlers/auth.py`
3. Register in `bot.py` with the appropriate handler type
4. If it's a command, add a `BotCommand` entry to `BOT_COMMANDS` in `bot.py`
5. If using inline keyboards, add a `*_callback_handler` function with manual auth check (`AUTHORIZED_USER_IDS`)
6. Register `CallbackQueryHandler` with a unique prefix pattern in `bot.py`
7. Add to `handlers/start.py` `HELP_TEXT`
8. Add tests in `test_security.py` (new section + registration test in section 23)
9. Update `docs/USER-MANUAL.md` and `README.md`

## Testing

All tests live in `test_security.py`. Tests use a custom `test(name, condition)` function (not unittest.TestCase). Sections are numbered 1–25 with printed headers during the run. All tests run together (`python3 test_security.py`); there is no way to run individual sections. New tests go before the RESULTS block at the end. Section 23 tests bot.py handler registration — add new handlers there too.

## Environment

Requires a `.env` file (see `.env.example`): `TELEGRAM_BOT_TOKEN`, `AUTHORIZED_USER_IDS`, `WORK_DIR`, `LOG_FILE`, `LOG_LEVEL`. Optional monitor vars: `SCREEN_STREAM_PORT`, `GO2RTC_HOST`, `MINIAPP_BASE_URL`. The bot runs as a macOS LaunchAgent (`main.py`) for 24/7 operation with auto-restart for child processes.
