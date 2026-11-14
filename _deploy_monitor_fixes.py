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
for rel in [
    "app/agents/conversation.py",
    "app/agents/orchestrator.py",
]:
    sftp.put(str(base / rel), f"/home/harr/harrison-agent/{rel}")
    print("put", rel)
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
    print("wait", i, out.replace("\n", " | "))
    if out.startswith("active") and out.endswith("200"):
        break


def ask(msg, history):
    payload = json.dumps({"message": msg, "history": history, "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 30 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=40,
    )
    data = json.loads(stdout.read().decode())
    reply = data["reply"]
    history = history + [
        {"role": "user", "content": msg},
        {"role": "assistant", "content": reply},
    ]
    return reply, data.get("agent"), history


# Monitor checklist highlights
history = []
for msg in [
    "hi",
    "what's your name?",
    "and your email?",
    "and email?",
    "hi",
    "do you like pizza",
    "what have you built?",
    "and your phone?",
    "how are you?",
]:
    reply, agent, history = ask(msg, history)
    print(f"U: {msg}\nH[{agent}]: {reply}\n")

# Local FAQ follow-up should not fire (simulate JS rule)
import re

def match_local(message):
    lower = message.lower().strip().rstrip("!?.")
    if re.match(r"^(and|also|what about|how about)\b", lower):
        return None
    if re.match(r"^(and\s+)?(email|mail|phone|number)\s*$", lower):
        return None
    if "your email" in lower:
        return "hezronmuraya9@gmail.com"
    if "phone" in lower:
        return "BAD_PHONE_MATCH"
    return None

for s in ["and your email?", "and email?", "and your phone?", "what is your email"]:
    print("local", s, "=>", match_local(s))

client.close()
