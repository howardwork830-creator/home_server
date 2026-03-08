# Telegram Bot User Manual

Your Mac M1 Home Server bot gives you SSH-like control of your Mac from Telegram. This manual covers every command and feature.

---

## Getting Started

Open your Telegram bot chat and send `/start`. You'll see a keyboard with quick-access buttons. Any plain text you type is executed as a shell command on your Mac.

The first command you send automatically creates a **persistent terminal session**. Your working directory, environment variables, and shell state carry over between commands — just like a real terminal.

---

## Persistent Terminal Sessions

Every command runs inside a tmux-backed terminal. You get up to **3 terminals** running in parallel.

### How It Works

| Action | What happens |
|--------|-------------|
| Send any command (e.g. `ls`) | Auto-creates Terminal 1 if none exist, runs command in it |
| `cd src` then `ls` | `cd` persists — `ls` shows contents of `src/` |
| Type `exit` | Closes the active terminal |

Output is prefixed with the terminal indicator: `[T1]`, `[T2: build]`, etc.

### Managing Terminals with `/t`

| Command | Description |
|---------|-------------|
| `/t` | List all terminals (* marks the active one) |
| `/t list` | Same as `/t` |
| `/t new` | Create a new terminal |
| `/t new build` | Create a new terminal named "build" |
| `/t 2` | Switch active terminal to #2 |
| `/t use 2` | Same as `/t 2` |
| `/t close 2` | Close terminal #2 |

### Example Workflow

```
You:  ls                         → Auto-creates T1, shows files
Bot:  [T1] file1.txt  src/

You:  cd src                     → Runs in T1 (directory persists)
You:  ls                         → Shows src/ contents
Bot:  [T1] main.py  utils/

You:  /t new build               → Creates T2 named "build"
Bot:  Created terminal 2 (build). Use `/t 2` to switch.

You:  /t 2                       → Switch to T2
You:  npm install                → Runs in T2
Bot:  [T2: build] added 150 packages...

You:  /t 1                       → Switch back to T1
You:  pwd                        → Still in src/ from earlier
Bot:  [T1] /Users/howard/Desktop/project/src

You:  exit                       → Closes T1, falls back to T2
Bot:  Closed terminal 1. Active terminal: 2

You:  /t close 2                 → Closes T2
Bot:  Closed terminal 2. No active terminals.

You:  ls                         → Auto-creates new T1 again
```

---

## Shell Commands

Type any allowlisted command as plain text. Pipes (`|`) work between commands.

### Files & Navigation
```
ls, ls -la, pwd, cat file.txt, head -50 file, tail -50 file
grep "pattern" file, find . -name "*.py", tree -L 2
echo "hello", wc -l file, sort file, which python3
file image.png, du -sh *, open file.pdf
```

### System Information
```
uptime, date, whoami, hostname, uname -a
sw_vers, system_profiler SPHardwareDataType
```

### Git
```
git status, git add ., git commit -m "message"
git push, git log, git diff, git branch
```

### Development
```
python3 script.py, npm install, npx create-react-app my-app
```

### Network
```
ping -c 4 google.com, traceroute 8.8.8.8
dig example.com, nslookup example.com
netstat -an, lsof -i :8080
ifconfig en0, networkQuality
curl https://example.com, wget https://example.com/file
tailscale status
```

### Disk & Storage
```
df -h, diskutil list, diskutil info disk0
du -sh *, tmutil listbackups
```

### Process Management
```
ps aux, pgrep -l python, top -l 1 -n 10
kill 12345, killall Safari
```

### Packages
```
brew list, brew install <pkg>, brew update, brew upgrade
brew search <term>, brew outdated, brew doctor
softwareupdate -l, xcode-select --install
```

### Media
```
say "hello world", afplay sound.mp3
screencapture -x /tmp/screen.png
sips --getProperty pixelWidth image.png
```

### Text Processing
```
sed 's/old/new/g' file, awk '{print $1}' file
uniq file, pbcopy, pbpaste
```

### Compression
```
tar czf archive.tar.gz folder/
tar xzf archive.tar.gz
zip -r archive.zip folder/
unzip archive.zip
gzip file, gunzip file.gz
```

### Automation
```
caffeinate -t 3600
shortcuts list, shortcuts run "shortcut name"
```

### Utilities
```
trash file.txt, mdfind "query", mdls file.txt
```

### Important Flags

Some commands require specific flags to prevent hangs:
- `ping` requires `-c <count>` (e.g. `ping -c 4 google.com`)
- `top` requires `-l <iterations>` (e.g. `top -l 1`)

---

## Bot Commands

These are activated with the `/` prefix.

| Command | What it does |
|---------|-------------|
| `/start` | Show main menu with keyboard buttons |
| `/help` | List all commands and allowed shell commands |
| `/status` | System status (uptime, disk, Tailscale) |
| `/network` | Network diagnostics (interfaces, public IP, connectivity) |
| `/claude <prompt>` | One-shot Claude AI coding session |
| `/claude_continue <prompt>` | Continue the last Claude conversation |
| `/chat` | Enter interactive Claude chat mode |
| `/exit` | Leave Claude chat mode |
| `/t` | Manage persistent terminal sessions |
| `/cd` | Select a project directory (Desktop folders) |
| `/newproject <name>` | Create a new project folder on Desktop |
| `/tmux ls` | List raw tmux sessions |
| `/tmux send <session> <cmd>` | Send a command to a specific tmux session |
| `/getfile <path>` | Download a file from server to Telegram |
| `/app` | List, launch, or quit applications |
| `/sysinfo` | Detailed system info (battery, memory, hardware, storage) |
| `/monitor` | Live screen monitor (screenshot or Mini App stream) |

---

## Claude AI

### One-Shot Mode

```
/claude Fix the bug in main.py where the loop never exits
/claude Explain what this error means: TypeError: cannot unpack non-sequence NoneType
/claude Write a Python script that converts CSV to JSON
```

Claude can read, search, edit, and create files in your workspace. It runs with restricted tool access and a $1.00 per-request budget cap.

### Chat Mode

```
/chat                    → Enter chat mode
"Add error handling"     → Claude responds, remembers context
"Now add tests for it"   → Continues the conversation
/exit                    → Leave chat mode
```

In chat mode, all plain text goes to Claude instead of the shell. Use `/exit` to return to shell mode.

### Continuing a Session

```
/claude_continue Actually, use async instead of sync
```

This resumes the last Claude conversation with a follow-up.

---

## File Operations

### Upload Files

Drag and drop (or attach) any document in the Telegram chat. The file is saved to your current working directory.

### Download Files

```
/getfile path/to/file.txt
/getfile /absolute/path/to/image.png
```

The bot sends the file back to you in Telegram.

---

## Directory Management

### Switch Directory

```
/cd                      → Shows Desktop folders as buttons
/cd VS code file/home server  → Direct path (must be under ~/Desktop)
```

The selected directory becomes the working directory for new terminal sessions.

### Create a Project

```
/newproject my-app       → Creates ~/Desktop/my-app/ and switches to it
```

---

## Application Control

```
/app                     → List running applications
/app launch Safari       → Launch an application
/app quit Safari         → Quit an application
```

Only apps in the safety allowlist can be launched (Safari, Finder, Terminal, VS Code, Preview, TextEdit, Activity Monitor, Console, Music, Photos, Calculator, Notes).

---

## System Monitoring

### Quick Status
```
/status                  → Uptime, disk usage, Tailscale status
```

### Detailed Info
```
/sysinfo                 → Battery, memory, CPU, storage, hardware details
```

### Network Diagnostics
```
/network                 → All interfaces, public IP, DNS, connectivity test
```

### Live Screen Monitor
```
/monitor                 → Captures a screenshot, with optional live stream
```

If go2rtc is configured, you'll see an "Open Live Monitor" button for a near-real-time screen stream inside Telegram.

---

## Security Notes

- Only your authorized Telegram ID can use the bot
- Dangerous commands (`rm -rf`, `sudo`, `reboot`, etc.) are blocked
- Sensitive paths (`~/.ssh`, `~/.aws`, `.env` files, etc.) are protected
- API keys and secrets in command output are automatically redacted
- Rate limits: 20 shell commands/min, 5 Claude requests/min
- Command timeout: 300 seconds
- Output is capped at 50KB per command

---

## Keyboard Buttons

The main menu keyboard provides quick access:

| Button | Action |
|--------|--------|
| Shell | Tips for shell usage |
| Claude | Tips for Claude usage |
| Files | Tips for file uploads |
| Git | Tips for git commands |
| Status | Tips for /status |
| Terminal | Tips for terminal management |
| CD | Tips for /cd |
| Chat | Tips for /chat |
| New Project | Tips for /newproject |
| Network | Tips for /network |
| Monitor | Tips for /monitor |
| Get File | Tips for /getfile |
| App | Tips for /app |
| Sys Info | Tips for /sysinfo |

---

## Tips

- **First command auto-creates a terminal** — you don't need to set anything up
- **`cd` sticks** — change directory once, all subsequent commands use it
- **Use multiple terminals** for parallel tasks (e.g. one for dev, one for builds)
- **`exit` closes the terminal**, not the bot — you can always send another command
- **Pipes work**: `ps aux | grep python`, `cat file.txt | wc -l`
- **Long output is chunked** — large outputs are split into multiple Telegram messages
- **Secrets are scrubbed** — API keys in output are replaced with `[REDACTED]`
- **Connection is resilient** — TCP keepalive probes prevent Tailscale/NAT idle disconnects; the bot auto-recovers from network errors
