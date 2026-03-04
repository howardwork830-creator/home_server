"""Telegram bot command and message handlers.

Handlers by domain:

    Core:
        auth.py         — @authorized decorator (access control)
        start.py        — /start welcome menu, /help command list
        shell.py        — Plain text → shell execution (catch-all)
        terminal.py     — /t persistent terminal sessions

    Claude AI:
        claude.py       — /claude, /claude_continue, /chat, /exit

    System & monitoring:
        status.py       — /status (uptime, disk, Tailscale)
        sysinfo.py      — /sysinfo (battery, memory, hardware)
        network.py      — /network (interfaces, IPs, connectivity)
        monitor.py      — /monitor (live screen capture)
        app.py          — /app (launch, quit applications)
        tmux.py         — /tmux (raw tmux session control)

    Files & navigation:
        cd.py           — /cd (directory selector)
        newproject.py   — /newproject (create project folder)
        files.py        — Document upload handler
        getfile.py      — /getfile (download file to Telegram)
"""
