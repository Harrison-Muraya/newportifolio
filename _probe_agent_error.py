import json
import paramiko
import urllib.error
import urllib.request

# Local agent error via SSH
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

cmds = [
    "curl -sS -m 30 -X POST http://127.0.0.1:2020/chat -H 'Content-Type: application/json' -d '{\"message\":\"hi\",\"history\":[],\"stream\":false}' | head -c 800",
    "journalctl -u harrison-agent.service -n 40 --no-pager || true",
    "tail -n 80 /tmp/cloudflared-agent.log || true",
]
for cmd in cmds:
    print("####", cmd[:120])
    stdin, stdout, stderr = client.exec_command(cmd, timeout=90)
    print(stdout.read().decode("utf-8", "replace")[:4000])
    err = stderr.read().decode("utf-8", "replace")
    if err.strip():
        print("STDERR", err[:1500])

client.close()

# OPTIONS preflight via tunnel
url = "https://pills-phase-capability-luck.trycloudflare.com/chat"
req = urllib.request.Request(
    url,
    method="OPTIONS",
    headers={
        "Origin": "https://harrisonmuraya.pythonanywhere.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    },
)
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("OPTIONS", resp.status, resp.headers.get("Access-Control-Allow-Origin"))
except Exception as e:
    print("OPTIONS ERR", e)

# Stream true via tunnel
body = json.dumps({"message": "hi", "history": [], "stream": True}).encode()
req = urllib.request.Request(
    url,
    data=body,
    headers={
        "Content-Type": "application/json",
        "Origin": "https://harrisonmuraya.pythonanywhere.com",
        "Accept": "text/event-stream",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        print("stream status", resp.status)
        print(resp.read()[:600])
except urllib.error.HTTPError as e:
    print("stream HTTP", e.code, e.read()[:600])
except Exception as e:
    print("stream ERR", e)
