import base64
import json
from pathlib import Path

FILES = [
    "harrison/views.py",
    "harrison/urls.py",
    "harrison/tests.py",
    "harrison/templates/harrison/training.html",
    "harrison/templates/harrison/dashboard_base.html",
    "harrison/templates/harrison/dashboard.html",
    "harrison/templates/partials/footer.html",
    "portifolio_project/settings.py",
]

root = Path(__file__).resolve().parent
out = root / "_pa_upload_exprs"
out.mkdir(exist_ok=True)

for index, rel in enumerate(FILES):
    b64 = base64.b64encode((root / rel).read_bytes()).decode("ascii")
    expression = f"""(async () => {{
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
  const rel = {json.dumps(rel)};
  const text = atob({json.dumps(b64)});
  const remote = '/home/harrisonmuraya/newportifolio/' + rel;
  const path = '/api/v0/user/harrisonmuraya/files/path' + remote;
  const fd = new FormData();
  const name = rel.split('/').pop();
  fd.append('content', new Blob([text], {{type:'text/plain'}}), name);
  const putRes = await fetch(path, {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}, body: fd}});
  return JSON.stringify({{rel, status: putRes.status, body: (await putRes.text()).slice(0,200)}});
}})()"""
    payload = {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
    }
    path = out / f"{index:02d}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    print(index, rel, path.stat().st_size)

reload_expr = {
    "expression": """(async () => {
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
  const reloadRes = await fetch('/api/v0/user/harrisonmuraya/webapps/harrisonmuraya.pythonanywhere.com/reload/', {method:'POST', credentials:'include', headers:{'X-CSRFToken': csrf}});
  return JSON.stringify({reload: reloadRes.status, body: (await reloadRes.text()).slice(0,120)});
})()""",
    "returnByValue": True,
    "awaitPromise": True,
}
(out / "reload.json").write_text(json.dumps(reload_expr), encoding="utf-8")
print("reload ready")
