import re
import urllib.request

html = urllib.request.urlopen(
    "https://harrisonmuraya.pythonanywhere.com/?v=corscheck",
    timeout=20,
).read().decode("utf-8", "replace")
m = re.search(r"AGENT_CHAT_URL\s*=\s*['\"]([^'\"]+)['\"]", html)
url = m.group(1) if m else "NOT_FOUND"
print("AGENT_CHAT_URL=", url)
print("mixed_content=", url.startswith("http://"))
