# Systemd (optional)

There is **no** bundled `motadata-orchestrator.service` in this repository. Use **`runtime/scripts/governed_services.sh`** from cron, a process manager, or a **local** systemd unit you author.

Example **user** unit (adjust `User=` and paths):

```ini
[Unit]
Description=Motadata governed services (vLLM + Plan-Gate)
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/YOU/m-coder
Environment=HOME=/home/YOU
ExecStart=/bin/bash /home/YOU/m-coder/runtime/scripts/governed_services.sh start
ExecStop=/bin/bash /home/YOU/m-coder/runtime/scripts/governed_services.sh stop

[Install]
WantedBy=multi-user.target
```

Requires **`/home/YOU/m-coder/runtime/config/demo_stack.env`** with **`VLLM_BASE_MODEL`** set before **`systemctl start`**.

See [ORCHESTRATOR_GUIDE.md](ORCHESTRATOR_GUIDE.md) for manual commands.
