"""Deploy CORS update and verify tunnel chat + OPTIONS from PythonAnywhere origin."""
from pathlib import Path
import json
import urllib.request

import paramiko

LOCAL = Path(r"C:\Users\hezro\Desktop\harrison-agent\app\main.py")
REMOTE = "/home/harr/harrison-agent/app/main.py"
TUNNEL_CHAT = "https://college-inner-respondents-passage.trycloudflare.com/chat"
ORIGIN = "https://harrisonmuraya.pythonanywhere.com"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    "197.248.201.233",
    port=2021,
    username="harr",
    password="pass123",
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
sftp = client.open_sftp()
sftp.put(str(LOCAL), REMOTE)
sftp.close()
stdin, stdout, stderr = client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 3 && systemctl is-active harrison-agent.service",
    timeout=60,
)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()

# OPTIONS preflight
req = urllib.request.Request(
    TUNNEL_CHAT,
    method="OPTIONS",
    headers={
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
)
with urllib.request.urlopen(req, timeout=30) as r:
    print("OPTIONS", r.status, r.headers.get("Access-Control-Allow-Origin"))

# POST non-stream short
body = json.dumps({"message": "What is your full name?", "history": [], "stream": False}).encode()
req = urllib.request.Request(
    TUNNEL_CHAT,
    data=body,
    headers={"Content-Type": "application/json", "Origin": ORIGIN},
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as r:
    print("POST", r.status, r.read()[:300].decode("utf-8", "replace"))
