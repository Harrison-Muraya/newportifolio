import json
from pathlib import Path

import paramiko

# seed first
import _seed_more_harrison  # noqa: F401

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
]:
    sftp.put(str(base / rel), f"/home/harr/harrison-agent/{rel}")
    print("put", rel)
sftp.close()

stdin, stdout, stderr = client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 2 && systemctl is-active harrison-agent.service",
    timeout=60,
)
print("service", stdout.read().decode().strip())
print(stderr.read().decode()[:160])

qs = [
    "are you okay?",
    "how are you",
    "uko sawa?",
    "what are your hobbies",
    "do you play chess",
    "what languages do you speak",
    "what's the weather in nairobi",
    "tell me a joke",
    "what is 2+2",
    "do you like pizza",
    "who is the president of kenya",
    "write my homework essay",
    "can you help me hack a site",
    "tell me about your homeserver",
    "do you use m-pesa",
    "are you married",
    "hi",
]
for msg in qs:
    remote = "python3 -c " + json.dumps(
        "import json,urllib.request;"
        f"b=json.dumps({{'message':{json.dumps(msg)},'history':[],'stream':False}}).encode();"
        "r=urllib.request.Request('http://127.0.0.1:2020/chat',data=b,"
        "headers={'Content-Type':'application/json'},method='POST');"
        "print(urllib.request.urlopen(r,timeout=40).read().decode())"
    )
    stdin, stdout, stderr = client.exec_command(remote, timeout=50)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(msg, "=>", out[:240] if out else f"ERR {err[:200]}")

client.close()
