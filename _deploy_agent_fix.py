"""Deploy fixed agent.py (num_predict on stream) and restart service."""
from pathlib import Path

import paramiko

LOCAL = Path(r"c:\Users\hezro\Desktop\harrison-agent\app\agent.py")
REMOTE = "/home/harr/harrison-agent/app/agent.py"

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
sftp = client.open_sftp()
sftp.put(str(LOCAL), REMOTE)
sftp.close()
print("uploaded", REMOTE)

# also sync orchestrator in case remote is stale
for name in ("orchestrator.py",):
    local = Path(r"c:\Users\hezro\Desktop\harrison-agent\app\agents") / name
    remote = f"/home/harr/harrison-agent/app/agents/{name}"
    sftp = client.open_sftp()
    sftp.put(str(local), remote)
    sftp.close()
    print("uploaded", remote)

stdin, stdout, stderr = client.exec_command(
    "sudo -n systemctl restart harrison-agent.service || systemctl --user restart harrison-agent.service || "
    "(echo pass123 | sudo -S systemctl restart harrison-agent.service)",
    timeout=60,
)
print(stdout.read().decode())
print(stderr.read().decode()[:1000])
stdin, stdout, stderr = client.exec_command(
    "sleep 2; systemctl is-active harrison-agent.service; "
    "curl -sS -m 8 -o /dev/null -w 'home=%{http_code}\\n' http://127.0.0.1:2020/",
    timeout=30,
)
print(stdout.read().decode())
print(stderr.read().decode()[:500])
client.close()
