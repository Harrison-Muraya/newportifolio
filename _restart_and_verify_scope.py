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

# non-blocking restart
client.exec_command(
    "echo pass123 | sudo -S systemctl restart harrison-agent.service",
    timeout=30,
)
time.sleep(5)
stdin, stdout, stderr = client.exec_command(
    "systemctl is-active harrison-agent.service; curl -sS -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/",
    timeout=20,
)
print("status:", stdout.read().decode().strip())

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
    print(msg, "=>", out[:260] if out else stderr.read().decode()[:200])

client.close()
