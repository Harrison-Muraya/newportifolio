"""Fetch TEACH_TOKEN from VPS and run acceptance smoke against the live agent."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
REMOTE_HELPER = "/tmp/read_teach_token.py"
HELPER = (
    "from pathlib import Path\n"
    "text = Path('/home/harr/harrison-agent/.env').read_text(encoding='utf-8', errors='replace')\n"
    "token = ''\n"
    "for line in text.splitlines():\n"
    "    if line.startswith('TEACH_TOKEN='):\n"
    "        token = line.split('=', 1)[1].strip().strip('\"').strip(\"'\")\n"
    "print(token, end='')\n"
)


def teach_token() -> str:
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
    with sftp.file(REMOTE_HELPER, "w") as handle:
        handle.write(HELPER)
    sftp.close()
    _, stdout, stderr = client.exec_command(f"python3 {REMOTE_HELPER}", timeout=40)
    token = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    client.exec_command(f"rm -f {REMOTE_HELPER}")
    client.close()
    if not token:
        raise RuntimeError(err[:300] or "empty token")
    return token


def main() -> int:
    token = teach_token()
    env = os.environ.copy()
    env["TEACH_TOKEN"] = token
    env["AGENT_BASE_URL"] = "http://197.248.201.233:2020"
    print("token_len", len(token))
    print("probing", env["AGENT_BASE_URL"])
    result = subprocess.run(
        [sys.executable, str(ROOT / "_ml_training_acceptance.py")],
        cwd=str(ROOT),
        env=env,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
