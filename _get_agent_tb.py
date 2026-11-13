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
cmd = "journalctl -u harrison-agent.service -n 120 --no-pager"
stdin, stdout, stderr = client.exec_command(cmd, timeout=40)
text = stdout.read().decode("utf-8", "replace")
print(text[-5000:])
client.close()
