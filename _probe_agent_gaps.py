"""Probe Harrison agent for weak/failing replies."""
from __future__ import annotations

import json
import re

import paramiko

QUESTIONS = [
    "are you okay?",
    "are you ok",
    "how are you",
    "how are you doing",
    "how is your day",
    "how's it going",
    "you good?",
    "uko sawa?",
    "what's up",
    "what are your hobbies",
    "do you play chess",
    "do you write novels",
    "what languages do you speak",
    "what's your linkedin",
    "do you use m-pesa",
    "tell me about your homeserver",
    "what is proxmox to you",
    "who do you work for",
    "are you married",
    "how old are you",
    "what's the weather in nairobi",
    "who is the president of kenya",
    "write my homework essay",
    "tell me a joke",
    "what is 2+2",
    "recommend a netflix show",
    "what is bitcoin price",
    "do you like pizza",
    "can you help me hack a site",
]


def ask(client: paramiko.SSHClient, msg: str) -> dict:
    remote_py = "python3 -c " + json.dumps(
        "import json,urllib.request;"
        f"b=json.dumps({{'message':{json.dumps(msg)},'history':[],'stream':False}}).encode();"
        "r=urllib.request.Request('http://127.0.0.1:2020/chat',data=b,"
        "headers={'Content-Type':'application/json'},method='POST');"
        "print(urllib.request.urlopen(r,timeout=90).read().decode())"
    )
    stdin, stdout, stderr = client.exec_command(remote_py, timeout=100)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err and not out:
        return {"error": err[:300]}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"raw": out[:400], "error": err[:200]}


def main() -> None:
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
    weak = []
    for q in QUESTIONS:
        data = ask(client, q)
        reply = str(data.get("reply") or data.get("raw") or data.get("error") or "")
        agent = data.get("agent", "")
        flags = []
        low = reply.lower()
        if data.get("error") and not data.get("reply"):
            flags.append("ERROR")
        if agent in ("learning", "error") or "don't have that detail" in low:
            flags.append("ESCALATION")
        if "could not answer" in low or not reply.strip():
            flags.append("EMPTY")
        if len(reply) > 420:
            flags.append("OVERLONG")
        # off-topic questions that got substantive non-deflection answers
        offtopic = any(
            x in q.lower()
            for x in ("weather", "president", "homework", "joke", "2+2", "netflix", "bitcoin", "pizza", "hack")
        )
        if offtopic and not any(
            p in low for p in ("not related", "about me", "my work", "ask me about", "portfolio")
        ):
            flags.append("OFFTOPIC_LEAK")
        status = "WEAK" if flags else "OK"
        print(f"[{status}] {q!r}")
        print(f"  agent={agent} flags={flags}")
        print(f"  reply={reply[:220]!r}")
        print()
        if flags:
            weak.append({"q": q, "agent": agent, "flags": flags, "reply": reply[:300]})
    client.close()
    print("WEAK_COUNT", len(weak))
    Path = __import__("pathlib").Path
    Path(r"C:\Users\hezro\Desktop\newportifolio\_probe_gaps_report.json").write_text(
        json.dumps(weak, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
