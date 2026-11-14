import json
import time
from pathlib import Path

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
base = Path(r"C:\Users\hezro\Desktop\harrison-agent")
files = [
    "app/agents/conversation.py",
    "app/agents/orchestrator.py",
    "app/agents/router.py",
    "app/agents/memory.py",
    "app/agents/intent.py",
    "app/config.py",
]
for rel in files:
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


def ask(msg: str, history: list) -> tuple[str, str, list]:
    payload = json.dumps({"message": msg, "history": history, "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 40 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=50,
    )
    raw = stdout.read().decode().strip()
    data = json.loads(raw)
    reply = data.get("reply", "")
    agent = data.get("agent", "")
    history = history + [
        {"role": "user", "content": msg},
        {"role": "assistant", "content": reply},
    ]
    return reply, agent, history


history: list = []
script = [
    "hi",
    "what is your full name",
    "and your email?",
    "hi",  # should CONTINUE, not full intro
    "what is your full name",  # same canonical wording
    "what's the weather",
    "and your phone?",
]
for msg in script:
    reply, agent, history = ask(msg, history)
    print(f"U: {msg}\nH[{agent}]: {reply}\n")

client.close()
