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

sftp = client.open_sftp()
sftp.put(
    r"C:\Users\hezro\Desktop\harrison-agent\app\agents\intent.py",
    "/home/harr/harrison-agent/app/agents/intent.py",
)
sftp.close()

client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service",
    timeout=20,
)
for i in range(15):
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command(
        "systemctl is-active harrison-agent.service; curl -sS -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
        timeout=10,
    )
    line = stdout.read().decode().strip()
    print("wait", i, line)
    if line.startswith("active") and line.endswith("200"):
        break

# prove intent module on server
stdin, stdout, stderr = client.exec_command(
    "cd /home/harr/harrison-agent && ./venv/bin/python -c \"from app.agents.intent import is_offtopic,is_smalltalk; print(is_smalltalk('are you okay?'), is_offtopic('can you help me hack a site'), is_offtopic('what are your hobbies'))\"",
    timeout=30,
)
print("intent:", stdout.read().decode().strip(), stderr.read().decode()[:200])

for msg in ["are you okay?", "can you help me hack a site", "hi"]:
    payload = json.dumps({"message": msg, "history": [], "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 15 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=25,
    )
    print(msg, "=>", stdout.read().decode()[:250], stderr.read().decode()[:120])

client.close()
