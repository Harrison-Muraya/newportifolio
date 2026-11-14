import json
import time

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
sftp = client.open_sftp()
sftp.put(
    r"C:\Users\hezro\Desktop\harrison-agent\app\agents\conversation.py",
    "/home/harr/harrison-agent/app/agents/conversation.py",
)
sftp.put(
    r"C:\Users\hezro\Desktop\harrison-agent\app\agents\orchestrator.py",
    "/home/harr/harrison-agent/app/agents/orchestrator.py",
)
sftp.close()
client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service",
    timeout=20,
)
for i in range(12):
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command(
        "systemctl is-active harrison-agent.service; curl -sS -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
        timeout=12,
    )
    out = stdout.read().decode().strip()
    print("wait", out.replace("\n", " | "))
    if out.startswith("active") and out.endswith("200"):
        break

stdin, stdout, stderr = client.exec_command(
    "/home/harr/harrison-agent/.venv/bin/python -c \"from app.agents.conversation import canonical_for; print(canonical_for('what have you built?'))\"",
    timeout=20,
)
print("canonical_for:", stdout.read().decode(), stderr.read().decode()[:300])

payload = json.dumps(
    {"message": "what have you built?", "history": [], "stream": False}
)
sftp = client.open_sftp()
with sftp.file("/tmp/chat_q.json", "w") as f:
    f.write(payload)
sftp.close()
stdin, stdout, stderr = client.exec_command(
    "curl -sS -m 20 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
    timeout=30,
)
print(stdout.read().decode())
client.close()
