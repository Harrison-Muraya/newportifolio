import base64
import json
from pathlib import Path

rel = "portifolio_project/settings.py"
root = Path(__file__).resolve().parent
b64 = base64.b64encode((root / rel).read_bytes()).decode("ascii")
expression = f"""(async () => {{
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
  const text = atob({json.dumps(b64)});
  const path = '/api/v0/user/harrisonmuraya/files/path/home/harrisonmuraya/newportifolio/{rel}';
  const fd = new FormData();
  fd.append('content', new Blob([text], {{type:'text/plain'}}), 'settings.py');
  const putRes = await fetch(path, {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}, body: fd}});
  const reloadRes = await fetch('/api/v0/user/harrisonmuraya/webapps/harrisonmuraya.pythonanywhere.com/reload/', {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}}});
  return JSON.stringify({{put: putRes.status, reload: reloadRes.status}});
}})()"""
(root / "_pa_settings_upload.json").write_text(
    json.dumps({"expression": expression, "returnByValue": True, "awaitPromise": True}),
    encoding="utf-8",
)
print("ok")
