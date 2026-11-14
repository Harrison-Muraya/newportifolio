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
items = []
for rel in FILES:
    items.append(
        {
            "rel": rel,
            "b64": base64.b64encode((root / rel).read_bytes()).decode("ascii"),
        }
    )

expression = f"""(async () => {{
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1];
  const files = {json.dumps(items)};
  const results = [];
  for (const item of files) {{
    const text = atob(item.b64);
    const remote = '/home/harrisonmuraya/newportifolio/' + item.rel;
    const path = '/api/v0/user/harrisonmuraya/files/path' + remote;
    const fd = new FormData();
    fd.append('content', new Blob([text], {{type:'text/plain'}}), item.rel.split('/').pop());
    const putRes = await fetch(path, {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}, body: fd}});
    results.push({{rel: item.rel, status: putRes.status}});
  }}
  const reloadRes = await fetch('/api/v0/user/harrisonmuraya/webapps/harrisonmuraya.pythonanywhere.com/reload/', {{method:'POST', credentials:'include', headers:{{'X-CSRFToken': csrf}}}});
  return JSON.stringify({{results, reload: reloadRes.status}});
}})()"""

out = root / "_pa_all_upload.json"
out.write_text(
    json.dumps(
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
        ensure_ascii=True,
    ),
    encoding="utf-8",
)
print("wrote", out, "bytes", out.stat().st_size)
