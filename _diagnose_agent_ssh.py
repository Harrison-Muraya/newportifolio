"""SSH diagnose home Harrison Agent + Cloudflare tunnel."""
from __future__ import annotations

import sys

import paramiko

HOST = "197.248.201.233"
PORT = 2021
USER = "harr"
PASSWORD = "pass123"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    HOST,
    port=PORT,
    username=USER,
    password=PASSWORD,
    timeout=40,
    allow_agent=False,
    look_for_keys=False,
)


def run(cmd: str, timeout: int = 120) -> str:
    print("####", cmd[:220])
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    sys.stdout.write(out)
    if err.strip():
        sys.stdout.write("STDERR: " + err[:3000] + "\n")
    return out


run('curl -sS -m 8 -w "\\nhttp=%{http_code}\\n" http://127.0.0.1:2020/ || true')
run(
    "systemctl is-active harrison-agent.service 2>/dev/null; "
    "systemctl --user is-active harrison-agent.service 2>/dev/null; "
    "pgrep -af 'uvicorn|harrison|ollama|cloudflared' || true; "
    "ss -ltnp 2>/dev/null | grep -E '2020|11434' || true"
)
run("tail -n 100 /tmp/cloudflared-agent.log 2>/dev/null || true")
run(
    "curl -sS -m 90 -X POST http://127.0.0.1:2020/chat "
    "-H 'Content-Type: application/json' "
    "-d '{\"message\":\"hi\",\"history\":[],\"stream\":false}' "
    '-w "\\nhttp=%{http_code}\\n" || true'
)
run(
    "journalctl -u harrison-agent.service -n 50 --no-pager 2>/dev/null || true; "
    "ls -la /home/harr 2>/dev/null | head; "
    "ls -la /opt 2>/dev/null | head; "
    "find /home/harr /opt /var/www -maxdepth 3 -name 'main.py' 2>/dev/null | head"
)
run("curl -sS -m 15 http://127.0.0.1:11434/api/tags || true")
client.close()
