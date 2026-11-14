import json
from pathlib import Path

import paramiko

# ensure merge ran
import _merge_grok_training  # noqa: F401

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
for rel in ["app/agents/intent.py", "data/learning/learned.json"]:
    sftp.put(str(base / rel), f"/home/harr/harrison-agent/{rel}")
    print("put", rel)
sftp.close()

stdin, stdout, stderr = client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 2 && systemctl is-active harrison-agent.service",
    timeout=60,
)
print("service:", stdout.read().decode().strip())
print(stderr.read().decode()[:160])

for msg in ["vipi", "niajee", "hodii", "wewe ni nani", "hi"]:
    remote_py = "python3 -c " + json.dumps(
        "import json,urllib.request;"
        f"b=json.dumps({{'message':{json.dumps(msg)},'history':[],'stream':False}}).encode();"
        "r=urllib.request.Request('http://127.0.0.1:2020/chat',data=b,"
        "headers={'Content-Type':'application/json'},method='POST');"
        "print(urllib.request.urlopen(r,timeout=45).read().decode())"
    )
    stdin, stdout, stderr = client.exec_command(remote_py, timeout=55)
    print(msg, "->", stdout.read().decode()[:240].strip())
    err = stderr.read().decode().strip()
    if err:
        print("ERR", err[:200])

client.close()
