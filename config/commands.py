"""Command allowlists, blocklists, and validation rules."""

__all__ = [
    "SAFE_COMMANDS", "DANGEROUS_PATTERNS", "SHELL_METACHARACTERS",
    "DANGEROUS_ARGS", "REQUIRED_ARGS", "SUBCOMMAND_ALLOWLISTS",
]

import re

# --- Allowlisted shell commands (72) ---
SAFE_COMMANDS: set[str] = {
    # Core
    "ls", "pwd", "cat", "head", "tail", "grep", "find", "ps", "df",
    "uptime", "echo", "wc", "sort", "tree", "which", "file", "du",
    "date", "whoami", "python3", "git", "tmux", "tailscale", "claude",
    "npm", "npx",
    # Files
    "open",
    # System info
    "sw_vers", "system_profiler", "uname", "hostname",
    # Network
    "ping", "traceroute", "dig", "nslookup", "netstat", "lsof",
    "ifconfig", "networksetup", "networkQuality", "curl", "wget",
    # Disk
    "diskutil", "hdiutil", "tmutil",
    # Process
    "top", "pgrep", "kill", "killall",
    # Packages
    "brew", "softwareupdate", "pkgutil", "xcode-select",
    # Media
    "afplay", "say", "sips", "screencapture",
    # Text
    "sed", "awk", "uniq", "pbcopy", "pbpaste",
    # Compression
    "tar", "gzip", "gunzip", "zip", "unzip",
    # Automation
    "shortcuts", "caffeinate",
    # Utilities
    "trash", "mdfind", "mdls",
}

# --- Dangerous patterns (regex blocklist) ---
DANGEROUS_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+(-\w*r\w*f|--recursive|--force)\b", re.IGNORECASE),
    re.compile(r"\bsudo\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bchmod\s+777\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\bdd\b\s+if="),
    re.compile(r"curl\s.*\|\s*sh"),
    re.compile(r"wget\s.*\|\s*sh"),
    re.compile(r"\bkill\s+-9\b"),
    re.compile(r"\blaunchctl\b"),
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"\bcurl\s+.*file://", re.IGNORECASE),
]

# --- Shell metacharacter blocking ---
SHELL_METACHARACTERS: list[str] = [";", "&&", "||", "$(", "`", "<(", ">(", "\n"]

# --- Per-command blocked arguments ---
DANGEROUS_ARGS: dict[str, list[str]] = {
    "find": ["-exec", "-execdir", "-delete", "-ok"],
    "sort": ["--compress-prog"],
    "grep": ["--pre"],
    "curl": ["--upload-file", "-T", "--data", "-d", "--data-raw",
             "--data-binary", "--data-urlencode", "-F", "--form", "--json",
             "-X", "--request"],
    "wget": ["--post-data", "--post-file", "--method"],
    "sed":  ["-i", "--in-place"],
    "open": ["-a"],
}

# --- Required args (prevent hangs) ---
REQUIRED_ARGS: dict[str, dict] = {
    "ping": {"flag": "-c", "error": "ping requires `-c <count>` to prevent infinite ping."},
    "top":  {"flag": "-l", "error": "top requires `-l <iterations>` for batch mode."},
}

# --- Subcommand / flag allowlists ---
SUBCOMMAND_ALLOWLISTS: dict[str, set[str]] = {
    "git":          {"status", "add", "commit", "push", "log", "diff", "branch"},
    "diskutil":     {"list", "info", "apfslist", "listFilesystems"},
    "hdiutil":      {"info", "imageinfo"},
    "tmutil":       {"listbackups", "destinationinfo", "status", "latestbackup"},
    "brew":         {"list", "info", "search", "update", "upgrade", "install",
                     "uninstall", "outdated", "doctor", "cleanup", "deps", "leaves"},
    "pkgutil":      {"--pkgs", "--pkg-info", "--files"},
    "softwareupdate": {"-l", "--list", "-i", "--install", "-ia", "--install-all",
                       "-ir", "--install-recommended"},
    "xcode-select": {"--print-path", "-p", "--version", "--install"},
    "shortcuts":    {"list", "run"},
    "networksetup": {"-listallnetworkservices", "-getinfo", "-getdnsservers",
                     "-getwebproxy", "-getsearchdomains", "-getairportnetwork"},
}
