import json
import urllib.error
import urllib.request

url = "https://pills-phase-capability-luck.trycloudflare.com/chat"
body = json.dumps({"message": "hi", "history": [], "stream": False}).encode()
req = urllib.request.Request(
    url,
    data=body,
    headers={
        "Content-Type": "application/json",
        "Origin": "https://harrisonmuraya.pythonanywhere.com",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        print("status", resp.status)
        print("acao", resp.headers.get("Access-Control-Allow-Origin"))
        print(resp.read()[:800])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read()[:800])
except Exception as e:
    print("ERR", type(e).__name__, e)
