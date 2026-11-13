"""Sync agent config/orchestrator/main to home server and restart."""
from __future__ import annotations

import json
import sys
import time

import paramiko

HOST = "197.248.201.233"
PORT = 2021
USER = "harr"
PASSWORD = "pass123"
REMOTE_ROOT = "/home/harr/harrison-agent"
LOCAL_ROOT = r"c:\Users\hezro\Desktop\harrison-agent"

FILES = [
    ("app/config.py", f"{REMOTE_ROOT}/app/config.py"),
    ("app/agents/orchestrator.py", f"{REMOTE_ROOT}/app/agents/orchestrator.py"),
    ("app/main.py", f"{REMOTE_ROOT}/app/main.py"),
    ("app/agent.py", f"{REMOTE_ROOT}/app/agent.py"),
]

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


def run(cmd: str, timeout: int = 90) -> str:
    print("####", cmd[:200])
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    sys.stdout.write(out)
    if err.strip():
        sys.stdout.write("STDERR: " + err[:2000] + "\n")
    return out


sftp = client.open_sftp()
for rel, remote in FILES:
    local = f"{LOCAL_ROOT}\\{rel.replace('/', '\\')}"
    sftp.put(local, remote)
    print("uploaded", remote)
sftp.close()

# Ensure model matches what is installed on the box.
run(
    "grep -E 'OLLAMA_MODEL|MODEL' "
    f"{REMOTE_ROOT}/.env 2>/dev/null || true; "
    "curl -sS -m 10 http://127.0.0.1:11434/api/tags | "
    "python3 -c \"import sys,json; d=json.load(sys.stdin); print('models=', [m['name'] for m in d.get('models',[])])\""
)

# Point .env at installed 1.7b if needed
run(
    f"python3 - <<'PY'\n"
    f"from pathlib import Path\n"
    f"p = Path('{REMOTE_ROOT}/.env')\n"
    f"text = p.read_text() if p.exists() else ''\n"
    f"lines = [ln for ln in text.splitlines() if not ln.startswith('OLLAMA_MODEL=')]\n"
    f"lines.append('OLLAMA_MODEL=qwen3:1.7b')\n"
    f"p.write_text('\\n'.join(lines).rstrip() + '\\n')\n"
    f"print('wrote', p)\n"
    f"print(p.read_text())\n"
    f"PY"
)

run(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service; "
    "sleep 2; systemctl is-active harrison-agent.service"
)

time.sleep(2)
run('curl -sS -m 8 -o /dev/null -w "home=%{http_code}\\n" http://127.0.0.1:2020/')

# Non-stream chat smoke test
body = json.dumps({"message": "How do I contact you?", "history": [], "stream": False})
run(
    "curl -sS -m 120 -X POST http://127.0.0.1:2020/chat "
    "-H 'Content-Type: application/json' "
    f"-d '{body}' "
    '-w "\\nhttp=%{http_code}\\n"'
)

client.close()
