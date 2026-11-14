"""Print whether VPS TEACH_TOKEN length matches what PA needs (no secret printed)."""
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    "197.248.201.233",
    port=2021,
    username="harr",
    password="pass123",
    timeout=40,
    allow_agent=False,
    look_for_keys=False,
)
_, stdout, _ = client.exec_command(
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "text = Path('/home/harr/harrison-agent/.env').read_text(encoding='utf-8', errors='replace')\n"
    "token = ''\n"
    "for line in text.splitlines():\n"
    "    if line.startswith('TEACH_TOKEN='):\n"
    "        token = line.split('=',1)[1].strip().strip('\"').strip(\"'\")\n"
    "print('length', len(token))\n"
    "print('set', 'yes' if token else 'no')\n"
    "PY"
)
print(stdout.read().decode())
client.close()
