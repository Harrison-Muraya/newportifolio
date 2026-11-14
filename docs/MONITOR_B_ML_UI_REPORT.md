# MONITOR B — Django admin UI + privacy

**Scope:** Portfolio repo `newportifolio` only. Re-check of the prior FAIL in this file. Admin path, visitor privacy, and the server-side teach proxy.

**Date:** 2026-11-14  
**Verdict:** **PASS.** `/dashboard/training/` is a superuser inbox. Django proxies `GET /learn/inbox` and `POST /learn/reward` with `X-Teach-Token` kept on the server. Public pages hide the inbox. `docs/PRIVACY_TRAINING_AUDIT.md` exists.

---

## Checks

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `/dashboard/training/` plus `training_inbox` / `training_reward`, both `superuser_required` | **PASS** | `harrison/urls.py` names `training_inbox` and `training_reward`. Both views in `harrison/views.py` use `@superuser_required`. Anonymous users go to `/login/?next=…`. Signed-in non-superusers go to `home`. |
| 2 | `harrison/templates/harrison/training.html` and a sidebar Training inbox link for superusers only | **PASS** | Template extends the dashboard shell and lists clusters with Approve, Edit & teach, and Reject. `dashboard_base.html` wraps the “Training inbox” sidebar link in `{% if request.user.is_superuser %}`. Footer and overview links use the same check. |
| 3 | Django proxies `GET /learn/inbox` and `POST /learn/reward` with `X-Teach-Token`; token never in templates or JS | **PASS** | `_proxy_agent_learn` sets `X-Teach-Token` from `agent_teach_token()` and calls those two paths. Browser `fetch` posts to `{% url 'training_reward' %}` with `chat_id`, `action`, and an optional `answer`. A client `token` field is dropped before the agent call. No `TEACH_TOKEN` or `X-Teach-Token` in `harrison/templates/` or `harrison/static/`. |
| 4 | `TEACH_TOKEN` in settings from the environment (empty default is fine) | **PASS** | `portifolio_project/settings.py`: `TEACH_TOKEN = os.environ.get("TEACH_TOKEN", "")`. |
| 5 | Visitors do not see the inbox; chat has no logging/training copy; privacy audit exists | **PASS** | Anonymous and member HTML omit `/dashboard/training/`. Chat copy is “Ask Harrison” only. `docs/PRIVACY_TRAINING_AUDIT.md` is present and records the same rules. |
| 6 | `TrainingInboxTests` in `harrison/tests.py` | **PASS** | Class covers login redirect, non-superuser redirect, footer gating, inbox proxy, reward proxy, missing-agent stub, and chat copy. `PublicPageContractTests.test_public_pages_hide_the_training_inbox` covers `/`, `/chat/`, `/about/`, `/work/`, and `/lab/`. |

---

## Proxy and page behavior

- `training_inbox` calls `GET {agent origin}/learn/inbox` and renders ranked clusters (`needs_training_score`, questions, sample answer, signals).
- `training_reward` accepts only `approve`, `edit`, and `reject`, then calls `POST {agent origin}/learn/reward`.
- Origin comes from `AGENT_CHAT_URL` (scheme and host only). The teach token is not placed in the URL.
- `window.AGENT_CHAT_URL` in `base.html` is the public chat endpoint. It is not the teach token.

---

## Privacy notes

Visitor chat surfaces do not say chats are logged, recorded, stored, or used for training:

- `harrison/templates/partials/agent_chat.html` — “Ask Harrison”.
- `harrison/templates/partials/agent_widget.html` — greeting and chips.
- `harrison/templates/harrison/chat.html` — same chat partial plus the public footer.
- `harrison/static/harrison/js/i18n.js` — EN/SW ask and contact strings.
- `harrison/static/harrison/js/agent-chat.js`, `agent-widget.js`, `harrison-chat.js` — no training, reward, or teach-token strings.

The chat transcript element is `id="agent-log"`. That is a DOM id, not a sentence telling visitors their chat is logged.

Other uses of “training” or “record” are not chat-capture copy:

- About `education.html`: section id `training`, heading “Professional training” (courses).
- Lab `interact.js`: “record the payout” is the M-Pesa flow.

The public footer link labeled “Training” renders only when `request.user.is_superuser`.

---

## Tests run

```
python manage.py test harrison.tests.TrainingInboxTests --settings=portifolio_project.test_settings
python manage.py test harrison.tests.PublicPageContractTests.test_public_pages_hide_the_training_inbox --settings=portifolio_project.test_settings
```

`TrainingInboxTests`: 8 passed. Public-page hide check: 1 passed.

Covered outcomes: anonymous redirect to login, member redirect home (inbox and reward), superuser cluster render, `X-Teach-Token` on the outbound inbox and reward requests, client token not forwarded, token absent from the HTML, 503 stub when the agent route is missing, chat page without “Training inbox” or “reward”.

---

## Residual notes

Empty `TEACH_TOKEN` is the configured default until the environment supplies one. The inbox then shows the “not connected” notice, and reward returns the 503 stub. That does not reopen the admin path, the privacy gate, or the proxy.
