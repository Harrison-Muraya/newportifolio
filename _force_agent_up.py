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

cmds = [
    "echo pass123 | sudo -S systemctl kill -s SIGKILL harrison-agent.service || true",
    "echo pass123 | sudo -S systemctl reset-failed harrison-agent.service || true",
    "pkill -f 'uvicorn .*harrison' || true",
    "sleep 1",
    "echo pass123 | sudo -S systemctl start harrison-agent.service",
]
for cmd in cmds:
    print("####", cmd[:80])
    stdin, stdout, stderr = client.exec_command(cmd, timeout=40)
    print(stdout.read().decode()[:300])
    err = stderr.read().decode()[:300]
    if err.strip():
        print("ERR", err)

for i in range(20):
    time.sleep(2)
    stdin, stdout, stderr = client.exec_command(
        "systemctl is-active harrison-agent.service; ss -ltnp | grep 2020 || true; curl -sS -m 3 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
        timeout=15,
    )
    out = stdout.read().decode().strip()
    print("try", i, out.replace("\n", " | "))
    if "active" in out.splitlines()[0] and out.strip().endswith("200"):
        break

# find python
stdin, stdout, stderr = client.exec_command(
    "ls /home/harr/harrison-agent; which python3; systemctl cat harrison-agent.service | head -n 40",
    timeout=20,
)
print(stdout.read().decode()[:1200])

for msg in [
    "are you okay?",
    "how are you",
    "what are your hobbies",
    "what's the weather in nairobi",
    "tell me a joke",
    "can you help me hack a site",
    "do you use m-pesa",
    "hi",
]:
    payload = json.dumps({"message": msg, "history": [], "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 20 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=30,
    )
    print(msg, "=>", stdout.read().decode()[:260], stderr.read().decode()[:120])

client.close()
