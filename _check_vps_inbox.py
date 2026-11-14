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
cmd = r"""
set -e
test -f /home/harr/harrison-agent/app/agents/training.py && echo training_py=yes
if grep -q '^TEACH_TOKEN=.\+' /home/harr/harrison-agent/.env 2>/dev/null; then echo teach_token=set; else echo teach_token=empty_or_missing; fi
code=$(curl -s -o /dev/null -w '%{http_code}' -H 'X-Teach-Token: wrong' http://127.0.0.1:2020/learn/inbox || true)
echo inbox_wrong_token_http=$code
code2=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:2020/learn/inbox || true)
echo inbox_no_token_http=$code2
"""
_, stdout, stderr = client.exec_command(cmd, timeout=40)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print("ERR", err[:300])
client.close()
