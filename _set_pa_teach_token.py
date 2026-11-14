"""Fetch TEACH_TOKEN from VPS and write a CDP upload expression that sets it on PA.

Never prints the secret. Writes _pa_set_token.json for browser upload of a private env file
and a tiny WSGI snippet loader if needed.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent
REMOTE_ENV = "/home/harrisonmuraya/newportifolio/.pa_secrets.env"


def vps_token() -> str:
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
    _, stdout, _ = client.exec_command(
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        "text = Path('/home/harr/harrison-agent/.env').read_text(encoding='utf-8', errors='replace')\n"
        "token = ''\n"
        "for line in text.splitlines():\n"
        "    if line.startswith('TEACH_TOKEN='):\n"
        "        token = line.split('=',1)[1].strip().strip('\"').strip(\"'\")\n"
        "print(token, end='')\n"
        "PY"
    )
    token = stdout.read().decode().strip()
    client.close()
    return token


def main() -> None:
    token = vps_token()
    if not token:
        raise SystemExit("VPS TEACH_TOKEN empty")
    content = f"TEACH_TOKEN={token}\n"
    b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    # Also patch settings.py loader is already os.environ.get — we need WSGI to load the file.
    # Upload a small loader snippet that settings can import, OR patch wsgi.py on PA.
    expression = f"""(async () => {{
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
  const results = [];
  // 1) private secrets file
  {{
    const text = atob({json.dumps(b64)});
    const remote = {json.dumps(REMOTE_ENV)};
    const path = '/api/v0/user/harrisonmuraya/files/path' + remote;
    const fd = new FormData();
    fd.append('content', new Blob([text], {{type:'text/plain'}}), '.pa_secrets.env');
    const putRes = await fetch(path, {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}, body: fd}});
    results.push({{file:'.pa_secrets.env', status: putRes.status}});
  }}
  // 2) ensure wsgi loads it
  const wsgiPath = '/api/v0/user/harrisonmuraya/files/path/var/www/harrisonmuraya_pythonanywhere_com_wsgi.py';
  const getRes = await fetch(wsgiPath, {{credentials:'include'}});
  let wsgi = await getRes.text();
  const marker = 'newportifolio/.pa_secrets.env';
  if (!wsgi.includes(marker)) {{
    const loader = '''
import os
from pathlib import Path
_secrets = Path('/home/harrisonmuraya/newportifolio/.pa_secrets.env')
if _secrets.is_file():
    for _line in _secrets.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if not _line or _line.startswith('#') or '=' not in _line:
            continue
        _k, _v = _line.split('=', 1)
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
''';
    # insert after first import block if possible
    if 'from django.core.wsgi' in wsgi:
        wsgi = wsgi.replace('from django.core.wsgi', loader + '\\nfrom django.core.wsgi', 1)
    else:
        wsgi = loader + '\\n' + wsgi
    const fd2 = new FormData();
    fd2.append('content', new Blob([wsgi], {{type:'text/plain'}}), 'harrisonmuraya_pythonanywhere_com_wsgi.py');
    const put2 = await fetch(wsgiPath, {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}, body: fd2}});
    results.push({{file:'wsgi', status: put2.status}});
  }} else {{
    results.push({{file:'wsgi', status:'already_loads_secrets'}});
  }}
  const reloadRes = await fetch('/api/v0/user/harrisonmuraya/webapps/harrisonmuraya.pythonanywhere.com/reload/', {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}}});
  return JSON.stringify({{results, reload: reloadRes.status, token_len: {len(token)}}});
}})()"""
    out = ROOT / "_pa_set_token.json"
    out.write_text(
        json.dumps(
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    print("wrote", out.name, "bytes", out.stat().st_size, "token_len", len(token))


if __name__ == "__main__":
    main()
