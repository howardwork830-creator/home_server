#!/usr/bin/env python3
"""Start all home-server services with a single command.

Launches:
  1. screen_stream.py  — screen capture HTTP server (port 9999)
  2. go2rtc             — WebRTC/HLS relay (optional, skipped if binary missing)
  3. bot.py             — Telegram bot

Ctrl+C gracefully stops all services.
"""
import os
import signal
import subprocess
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

SERVICES = [
    {
        "name": "screen_stream",
        "cmd": [PYTHON, os.path.join(PROJECT_DIR, "screen_stream.py")],
        "optional": False,
    },
    {
        "name": "go2rtc",
        "cmd": [os.path.join(PROJECT_DIR, "go2rtc")],
        "optional": True,
    },
    {
        "name": "bot",
        "cmd": [PYTHON, os.path.join(PROJECT_DIR, "bot.py")],
        "optional": False,
    },
]

processes: dict[str, subprocess.Popen] = {}
shutting_down = False


def start_service(svc: dict) -> bool:
    """Start a single service. Returns True if started successfully."""
    name = svc["name"]
    cmd = svc["cmd"]

    if svc["optional"] and not os.path.isfile(cmd[0]):
        print(f"  [{name}] binary not found, skipping (optional)")
        return False

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        processes[name] = proc
        print(f"  [{name}] started (PID {proc.pid})")
        return True
    except Exception as e:
        print(f"  [{name}] failed to start: {e}")
        return False


def shutdown_all():
    """Gracefully terminate all services (5s timeout, then force kill)."""
    global shutting_down
    if shutting_down:
        return
    shutting_down = True

    print("\nShutting down services...")
    for name, proc in processes.items():
        if proc.poll() is None:
            print(f"  [{name}] sending SIGTERM...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass

    deadline = time.monotonic() + 5
    for name, proc in processes.items():
        remaining = max(0, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
            print(f"  [{name}] stopped")
        except subprocess.TimeoutExpired:
            print(f"  [{name}] force killing...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()
            print(f"  [{name}] killed")


def main():
    os.chdir(PROJECT_DIR)

    print(f"Starting home-server services from {PROJECT_DIR}\n")

    for svc in SERVICES:
        start_service(svc)

    if not processes:
        print("No services started.")
        sys.exit(1)

    print(f"\n{len(processes)} service(s) running. Press Ctrl+C to stop all.\n")

    signal.signal(signal.SIGINT, lambda *_: shutdown_all())
    signal.signal(signal.SIGTERM, lambda *_: shutdown_all())

    try:
        while not shutting_down:
            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    print(f"  [{name}] exited with code {proc.returncode}")
                    del processes[name]
            if not processes:
                print("All services have exited.")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown_all()


if __name__ == "__main__":
    main()
