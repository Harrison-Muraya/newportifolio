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
for i in range(10):
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
        timeout=10,
    )
    code = stdout.read().decode().strip()
    print("code", code)
    if code == "200":
        break

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
