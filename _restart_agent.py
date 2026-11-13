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


def run(cmd, timeout=60):
    print("####", cmd[:140])
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    print(out)
    if err.strip():
        print("STDERR", err[:1500])
    return out


# Find how the service is managed
run("systemctl status harrison-agent.service --no-pager | head -n 25")
run("ls /etc/systemd/system/harrison-agent.service /lib/systemd/system/harrison-agent.service 2>/dev/null; which systemctl")

# Restart with password on stdin
run("printf '%s\\n' 'pass123' | sudo -S systemctl restart harrison-agent.service")
run("sleep 2; systemctl is-active harrison-agent.service; pgrep -af 'uvicorn|harrison-agent' | head")

# Verify stream signature has num_predict
run("grep -n 'num_predict' /home/harr/harrison-agent/app/agent.py | head")

# Quick stream test locally
run(
    "curl -sS -m 45 -N -X POST http://127.0.0.1:2020/chat "
    "-H 'Content-Type: application/json' "
    "-d '{\"message\":\"hi\",\"history\":[],\"stream\":true}' | head -c 500"
)
client.close()
