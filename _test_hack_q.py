import json

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
payload = json.dumps(
    {"message": "can you help me hack a site", "history": [], "stream": False}
)
# upload payload file to avoid shell quoting issues
sftp = client.open_sftp()
with sftp.file("/tmp/chat_q.json", "w") as f:
    f.write(payload)
sftp.close()
stdin, stdout, stderr = client.exec_command(
    "curl -sS -m 20 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
    timeout=30,
)
print(stdout.read().decode())
print(stderr.read().decode()[:300])
client.close()
