import json
import re

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
    r"C:\Users\hezro\Desktop\harrison-agent\app\agents\intent.py",
    "/home/harr/harrison-agent/app/agents/intent.py",
)
sftp.close()
stdin, stdout, stderr = client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 2 && systemctl is-active harrison-agent.service",
    timeout=60,
)
print("service:", stdout.read().decode().strip())
print(stderr.read().decode()[:200])

messages = [
    "hi",
    "sasa",
    "hello there",
    "what is your full name",
    "what have you built",
]
for msg in messages:
    remote_py = (
        "python3 -c "
        + json.dumps(
            "import json,urllib.request;"
            f"b=json.dumps({{'message':{json.dumps(msg)},'history':[],'stream':False}}).encode();"
            "r=urllib.request.Request('http://127.0.0.1:2020/chat',data=b,"
            "headers={'Content-Type':'application/json'},method='POST');"
            "print(urllib.request.urlopen(r,timeout=60).read().decode())"
        )
    )
    stdin, stdout, stderr = client.exec_command(remote_py, timeout=70)
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("Q:", msg)
    print("A:", out[:360])
    if err.strip():
        print("ERR:", err[:250])
    print()

stdin, stdout, stderr = client.exec_command(
    "pgrep -a cloudflared || true; tail -n 50 /tmp/cloudflared-agent.log 2>/dev/null || true",
    timeout=20,
)
log = stdout.read().decode()
print("TUNNEL INFO:\n", log[-1400:])
m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", log)
if m:
    print("FOUND", m.group(0))
client.close()
