"""Deploy ML reward training files to the home Harrison agent and smoke-test APIs."""
from __future__ import annotations

import json
import os
from pathlib import Path

import paramiko
import urllib.request

HOST = "197.248.201.233"
PORT = 2021
USER = "harr"
PASSWORD = "pass123"
LOCAL = Path(r"C:\Users\hezro\Desktop\harrison-agent")
REMOTE = "/home/harr/harrison-agent"
CHAT = "http://197.248.201.233:2020"

FILES = [
    "app/agents/training.py",
    "app/agents/memory.py",
    "app/agents/conversation.py",
    "app/agents/orchestrator.py",
    "app/routers/learn.py",
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
        parent = "/".join(remote.split("/")[:-1])
        client.exec_command(f"mkdir -p {parent}")
        sftp.put(str(local), remote)
        print("put", rel)
    sftp.close()

    stdin, stdout, stderr = client.exec_command(
        "echo pass123 | sudo -S systemctl restart harrison-agent.service && sleep 3 && systemctl is-active harrison-agent.service",
        timeout=90,
    )
    print("service:", stdout.read().decode().strip())
    err = stderr.read().decode()
    if err.strip():
        print(err[:400])
    client.close()

    # Public chat still works
    body = json.dumps({"message": "hi", "history": [], "stream": False}).encode()
    req = urllib.request.Request(
        f"{CHAT}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        print("chat hi ->", (data.get("reply") or "")[:120], "agent=", data.get("agent"))

    token = os.environ.get("TEACH_TOKEN", "").strip()
    if not token:
        print("TEACH_TOKEN not set locally — skip live inbox probe (set env to verify).")
        return
    inbox_req = urllib.request.Request(
        f"{CHAT}/learn/inbox",
        headers={"Accept": "application/json", "X-Teach-Token": token},
        method="GET",
    )
    with urllib.request.urlopen(inbox_req, timeout=30) as resp:
        inbox = json.loads(resp.read().decode())
        print("inbox ok=", inbox.get("ok"), "clusters=", len(inbox.get("clusters") or []))


if __name__ == "__main__":
    main()
