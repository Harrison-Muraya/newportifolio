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
hist = []


def ask(msg):
    global hist
    payload = json.dumps({"message": msg, "history": hist, "stream": False})
    sftp = client.open_sftp()
    with sftp.file("/tmp/chat_q.json", "w") as f:
        f.write(payload)
    sftp.close()
    stdin, stdout, stderr = client.exec_command(
        "curl -sS -m 25 -H 'Content-Type: application/json' -d @/tmp/chat_q.json http://127.0.0.1:2020/chat",
        timeout=35,
    )
    raw = stdout.read().decode()
    err = stderr.read().decode()
    print("RAW", repr(raw[:400]), err[:120])
    data = json.loads(raw) if raw.strip().startswith("{") else {}
    reply = data.get("reply", "")
    agent = data.get("agent", "")
    hist = hist + [
        {"role": "user", "content": msg},
        {"role": "assistant", "content": reply},
    ]
    print(msg, "=>", agent, reply)


ask("what's your name?")
ask("and your phone?")
ask("how are you?")
client.close()
