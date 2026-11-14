# Privacy audit — training / reward loop

**Date:** 2026-11-14  
**Scope:** Visitor chat UI vs admin training inbox  
**Verdict:** PASS for visitor surfaces (no training/logging disclosure). Admin-only training is gated by Django `superuser_required`.

## Rules

1. Visitors must never see that chats are logged, recorded, or used for training.
2. `TEACH_TOKEN` stays server-side (agent env + PythonAnywhere env). Never in HTML, JS, or query strings.
3. Only superusers open `/dashboard/training/`. Anonymous → login. Signed-in non-superuser → home.
4. Browser `fetch` for rewards goes to `/dashboard/training/reward/` (Django). The agent URL and teach token are attached only in the Django view.

## Visitor surfaces checked

| Surface | Result |
| --- | --- |
| Chat page / widget copy | No “logged”, “recorded”, “training data”, “reward”, or inbox links |
| `harrison-chat.js` | Talks to public chat / stream only |
| Public footer (anonymous / member) | No Training link |
| About “Training” section | CV / professional courses only — not chat training |

## Admin surfaces (allowed)

| Surface | Allowed language |
| --- | --- |
| `/dashboard/training/` | “Review”, “train”, Approve / Edit / Reject |
| Sidebar “Training inbox” | Superuser only |
| Agent `/learn` HTML | Private admin page; not linked from the portfolio |

## Data location

- Chat rows and rewards live on the agent VPS under `data/learning/` (`chats.json`, `learned.json`, `pending.json`, `rewards.json`).
- Portfolio DB does not store training JSON.
- No visitor IP / user-agent is added to training payloads.

## Regression checks

- Django tests in `harrison/tests.py` (`TrainingInboxTests`, `test_public_pages_hide_the_training_inbox`).
- After deploy: view-source on `/chat/` must not contain `TEACH_TOKEN` or `/dashboard/training/` for anonymous users.
