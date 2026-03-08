#!/usr/bin/env python3
"""Unified CLI entry point for home-server services.

Usage:
    python3 main.py                  # start all services (default)
    python3 main.py --bot            # bot only
    python3 main.py --stream         # screen stream only
    python3 main.py --no-stream      # bot + go2rtc, skip screen stream
    python3 main.py --port 8888      # override screen stream port
    python3 main.py -C ~/projects     # change working directory before start
"""
import argparse
import atexit
import os
import signal
import subprocess
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(PROJECT_DIR, ".service_pids")
PYTHON = sys.executable
DEFAULT_PORT = 9999

processes: dict[str, subprocess.Popen] = {}
service_configs: dict[str, dict] = {}   # original configs for auto-restart
restart_counts: dict[str, int] = {}     # restart counter per service
MAX_RESTARTS = 10
RESTART_DELAY = 2  # seconds
shutting_down = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start home-server services selectively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 main.py                # all services\n"
            "  python3 main.py --bot          # bot only\n"
            "  python3 main.py --stream       # screen stream only\n"
            "  python3 main.py --no-go2rtc    # skip go2rtc\n"
            "  python3 main.py --port 8888    # custom stream port\n"
            "  python3 main.py -C ~/projects  # change working dir"
        ),
    )
    parser.add_argument("--bot", action="store_true", help="start the Telegram bot")
    parser.add_argument("--stream", action="store_true", help="start screen_stream.py")
    parser.add_argument("--go2rtc", action="store_true", help="start go2rtc relay")
    parser.add_argument("--no-stream", action="store_true", help="skip screen_stream.py")
    parser.add_argument("--no-go2rtc", action="store_true", help="skip go2rtc relay")
    parser.add_argument("--port", type=int, default=None, help="override screen stream port")
    parser.add_argument("-C", "--cd", metavar="DIR", default=None,
                        help="change to DIR before starting services")
    return parser.parse_args()


def resolve_services(args: argparse.Namespace) -> list[dict]:
    """Build the list of services to launch based on CLI flags."""
    explicit = args.bot or args.stream or args.go2rtc

    run_bot = args.bot if explicit else True
    run_stream = args.stream if explicit else True
    run_go2rtc = args.go2rtc if explicit else True

    # --no-* flags override
    if args.no_stream:
        run_stream = False
    if args.no_go2rtc:
        run_go2rtc = False

    stream_cmd = [PYTHON, os.path.join(PROJECT_DIR, "screen_stream.py")]
    if args.port is not None:
        stream_cmd.extend(["--port", str(args.port)])

    services = []
    if run_stream:
        services.append({"name": "screen_stream", "cmd": stream_cmd, "optional": False})
    if run_go2rtc:
        services.append({"name": "go2rtc", "cmd": [os.path.join(PROJECT_DIR, "go2rtc")], "optional": True})
    if run_bot:
        services.append({"name": "bot", "cmd": [PYTHON, os.path.join(PROJECT_DIR, "bot.py")], "optional": False})

    return services


def write_pid_file():
    """Write all child PIDs to a file for stale process cleanup."""
    with open(PID_FILE, "w") as f:
        for name, proc in processes.items():
            f.write(f"{proc.pid} {name}\n")


def cleanup_stale_processes():
    """Kill any leftover processes from a previous run."""
    if not os.path.isfile(PID_FILE):
        return
    killed = []
    with open(PID_FILE) as f:
        for line in f:
            parts = line.strip().split(None, 1)
            if not parts:
                continue
            pid = int(parts[0])
            name = parts[1] if len(parts) > 1 else "unknown"
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
                killed.append(f"{name} (PID {pid})")
            except (ProcessLookupError, PermissionError, OSError):
                pass
    if killed:
        print(f"Cleaned up stale processes: {', '.join(killed)}")
    os.remove(PID_FILE)


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

    # Clean up PID file
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def main():
    args = parse_args()

    if args.cd:
        target = os.path.expanduser(args.cd)
        if not os.path.isdir(target):
            print(f"Error: directory not found: {target}")
            sys.exit(1)
        os.chdir(target)
        print(f"Working directory: {os.getcwd()}")
    else:
        os.chdir(PROJECT_DIR)

    cleanup_stale_processes()

    services = resolve_services(args)
    if not services:
        print("No services selected. Use --help to see options.")
        sys.exit(1)

    names = ", ".join(svc["name"] for svc in services)
    print(f"Starting home-server services from {PROJECT_DIR}")
    print(f"  Services: {names}\n")

    for svc in services:
        start_service(svc)
        service_configs[svc["name"]] = svc
        restart_counts[svc["name"]] = 0

    if not processes:
        print("No services started.")
        sys.exit(1)

    print(f"\n{len(processes)} service(s) running. Press Ctrl+C to stop all.\n")

    write_pid_file()
    atexit.register(shutdown_all)
    signal.signal(signal.SIGINT, lambda *_: shutdown_all())
    signal.signal(signal.SIGTERM, lambda *_: shutdown_all())
    signal.signal(signal.SIGHUP, lambda *_: shutdown_all())

    try:
        while not shutting_down:
            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    code = proc.returncode
                    print(f"  [{name}] exited with code {code}")
                    del processes[name]

                    if shutting_down:
                        break

                    # Auto-restart if we haven't exceeded the limit
                    if name in service_configs and restart_counts.get(name, 0) < MAX_RESTARTS:
                        restart_counts[name] = restart_counts.get(name, 0) + 1
                        count = restart_counts[name]
                        print(f"  [{name}] restarting ({count}/{MAX_RESTARTS})...")
                        time.sleep(RESTART_DELAY)
                        if start_service(service_configs[name]):
                            write_pid_file()
                    elif name in service_configs:
                        print(f"  [{name}] exceeded max restarts ({MAX_RESTARTS}), not restarting")

            if not processes:
                print("All services have exited.")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown_all()


if __name__ == "__main__":
    main()
