import json
import time
from pathlib import Path

import paramiko

import _seed_edge_cases  # noqa: F401

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
base = Path(r"C:\Users\hezro\Desktop\harrison-agent")
for rel in [
    "app/agents/intent.py",
    "app/agents/orchestrator.py",
    "app/agents/memory.py",
    "app/agents/router.py",
    "data/learning/learned.json",
    "data/STYLE.md",
]:
    sftp.put(str(base / rel), f"/home/harr/harrison-agent/{rel}")
    print("put", rel)
sftp.close()

client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service",
    timeout=20,
)
for i in range(15):
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command(
        "systemctl is-active harrison-agent.service; curl -sS -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
        timeout=12,
    )
    out = stdout.read().decode().strip()
    print("wait", i, out.replace("\n", " | "))
    if out.startswith("active") and out.endswith("200"):
        break

for msg in [
    "are you okay?",
    "how are you",
    "you good?",
    "help",
    "tell me something",
    "do you speak French?",
    "are you the founder of Afripixel?",
    "what's the weather in nairobi",
    "hi",
]:
    payload = json.dumps({"message": msg, "history": [], "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 15 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=25,
    )
    print(msg, "=>", stdout.read().decode()[:240])

client.close()
