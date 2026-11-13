"""Install cloudflared into ~/bin (no sudo) and start a quick HTTPS tunnel to :2020."""
from __future__ import annotations

import re
import sys
import time

import paramiko

HOST = "197.248.201.233"
PORT = 2021
USER = "harr"
PASSWORD = "pass123"
CF = "$HOME/bin/cloudflared"

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


def run(cmd: str, timeout: int = 180) -> tuple[str, str]:
    print("####", cmd[:160])
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    sys.stdout.write(out)
    if err.strip():
        sys.stdout.write("STDERR: " + err[:3000] + "\n")
    return out, err


run("curl -sS -m 8 -o /dev/null -w 'agent=%{http_code}\\n' http://127.0.0.1:2020/")
run("systemctl is-active harrison-agent.service")

out, _ = run(f"test -x {CF} && {CF} --version || echo NEED_INSTALL")
if "NEED_INSTALL" in out or "cloudflared version" not in out.lower():
    print("Installing cloudflared to ~/bin ...")
    install = r"""
set -e
mkdir -p "$HOME/bin"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64|amd64) CF_ARCH=amd64 ;;
  aarch64|arm64) CF_ARCH=arm64 ;;
  *) echo "unsupported arch $ARCH"; exit 1 ;;
esac
TMP=$(mktemp -d)
cd "$TMP"
curl -fsSL -o cloudflared.tgz \
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
# latest may be raw binary named cloudflared-linux-ARCH
if file cloudflared.tgz | grep -qi 'gzip\|archive'; then
  tar -xzf cloudflared.tgz
  BIN=$(find . -type f -name 'cloudflared' | head -n1)
  cp "$BIN" "$HOME/bin/cloudflared"
else
  mv cloudflared.tgz "$HOME/bin/cloudflared"
fi
chmod +x "$HOME/bin/cloudflared"
"$HOME/bin/cloudflared" --version
rm -rf "$TMP"
"""
    # Prefer official binary URL (not .tgz for linux amd64 - it's a raw binary)
    install2 = r"""
set -e
mkdir -p "$HOME/bin"
ARCH=$(uname -m)
case "$ARCH" in
  x86_64|amd64) CF_ARCH=amd64 ;;
  aarch64|arm64) CF_ARCH=arm64 ;;
  *) echo "unsupported arch $ARCH"; exit 1 ;;
esac
curl -fsSL -o "$HOME/bin/cloudflared" \
  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
chmod +x "$HOME/bin/cloudflared"
"$HOME/bin/cloudflared" --version
"""
    run(install2, timeout=240)

run("pkill -f 'cloudflared tunnel' || true")
time.sleep(1)

start = (
    f"nohup {CF} tunnel --url http://127.0.0.1:2020 "
    "--no-autoupdate > /tmp/cloudflared-agent.log 2>&1 & echo $!"
)
out, _ = run(start)
print("tunnel_pid_line=", out.strip())

url = None
for i in range(40):
    time.sleep(2)
    log, _ = run("tail -n 120 /tmp/cloudflared-agent.log || true")
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", log)
    if m:
        url = m.group(0)
        break
    if "failed to run command" in log or "error" in log.lower():
        print("log_snippet:", log[-500:])
    print(f"waiting for tunnel url... {i+1}")

if not url:
    print("FAILED_TO_GET_TUNNEL_URL")
    client.close()
    sys.exit(1)

print("TUNNEL_BASE=" + url)
print("CHAT_URL=" + url.rstrip("/") + "/chat")
run(f"curl -sS -m 20 -o /dev/null -w 'tunnel_home=%{{http_code}}\\n' {url}/")
client.close()
