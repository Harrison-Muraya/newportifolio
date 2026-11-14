"""Deploy voice/training upgrades to the home Harrison agent and smoke-test replies."""
from __future__ import annotations

import json
from pathlib import Path

import paramiko
import urllib.request

HOST = "197.248.201.233"
PORT = 2021
USER = "harr"
PASSWORD = "pass123"
LOCAL = Path(r"C:\Users\hezro\Desktop\harrison-agent")
REMOTE = "/home/harr/harrison-agent"

FILES = [
    "app/agents/intent.py",
    "app/agents/router.py",
    "app/agents/orchestrator.py",
    "app/agents/memory.py",
    "app/agent.py",
    "app/config.py",
    "data/profile/personal.md",
    "data/learning/learned.json",
]


def main() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        timeout=40,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = client.open_sftp()
    for rel in FILES:
        local = LOCAL / rel
        remote = f"{REMOTE}/{rel}"
        # ensure parent exists
        parent = "/".join(remote.split("/")[:-1])
        client.exec_command(f"mkdir -p {parent}")
        sftp.put(str(local), remote)
        print("put", rel)
    sftp.close()

    stdin, stdout, stderr = client.exec_command(
        "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 2 && systemctl is-active harrison-agent.service",
        timeout=60,
    )
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err.strip():
        print(err[:500])
    client.close()

    # Prefer public HTTP agent for smoke tests
    chat = "http://197.248.201.233:2020/chat"
    for msg in ("hi", "sasa", "what is your full name", "what have you built"):
        body = json.dumps({"message": msg, "history": [], "stream": False}).encode()
        req = urllib.request.Request(
            chat,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
            reply = data.get("reply", "")
            print(f"Q: {msg!r}\nA: {reply[:220]!r}\n agent={data.get('agent')}\n")


if __name__ == "__main__":
    main()
