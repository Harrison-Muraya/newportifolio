# MASTER PROMPT — Harrison Agent: Admin ML Reward Training System

**Role:** You are implementing a practical reward-based training loop for Harrison Muraya’s portfolio chat agent.  
**Constraint:** Visitors must never see that chats are recorded or used for training. Only superuser/admin sees the inbox.  
**Do not** fine-tune a giant cloud LLM. Prefer local ranking + rewarded answer bank + existing Ollama path.

---

## 1. Goal (what “done” means)

When Harrison (superuser) logs into `https://harrisonmuraya.pythonanywhere.com`:

1. He opens an **Admin → Training inbox**.
2. He sees **new / weak / clustered questions** from real chats.
3. He can **Approve (+reward)**, **Edit & teach (+strong reward)**, or **Reject (−reward)**.
4. The live agent immediately prefers rewarded answers for similar future asks.
5. Consistency rules already shipped (canonical facts, history, no bio on `hi`) stay intact.

---

## 2. How the ML works (architecture — implement exactly this)

### Layer A — Capture (already partially exists)
- Every public chat turn is logged privately in `harrison-agent/data/learning/chats.json` via `log_chat`.
- Unknown answers still go to `pending.json`.
- Taught answers live in `learned.json`.

### Layer B — Score / rank (NEW light ML — no GPU required)
For each chat row, compute a **needs_training_score** (0–1) from heuristics + optional tiny embedding similarity:

| Signal | High score when |
| --- | --- |
| unknown / escalation | agent said it doesn’t know |
| overshare | greeting/smalltalk reply too long or contains project dump |
| offtopic leak | answered weather/politics/etc. |
| contradiction | conflicts with canonical fact |
| low reward history | prior −rewards on similar Q |
| novelty | no close match in `learned.json` |
| frequency | many similar questions in last N days |

Sort inbox by `needs_training_score` desc, then cluster near-duplicates into one card (“email / contact / reach you” → one teach action).

**Clustering:** token Jaccard / cosine on bag-of-words is enough for v1. Optional: local sentence-transformers later. Do **not** block shipping on embeddings.

### Layer C — Reward store (NEW)
File: `data/learning/rewards.json` (list of events)

```json
{
  "id": "r1",
  "chat_id": "...",
  "question": "...",
  "answer": "...",
  "action": "approve|edit|reject",
  "reward": 1.0,
  "created": "ISO-8601",
  "admin": "harrisonmuraya"
}
```

Reward values:
- `approve` → `+1.0` (keep answer, bump priority)
- `edit` → `+1.5` (save new answer into learned, mark chat trained)
- `reject` → `-1.0` (blacklist answer fingerprint for similar Q)

Also store aggregate on learned rows:
- `reward_score` (running sum)
- `wins` / `losses`
- `priority = similarity_match * (1 + reward_score)`

### Layer D — Policy (how chat uses rewards)
Answer order (must preserve):

1. Monitor blocks (exams/degrees)
2. Greeting / smalltalk / offtopic / vague / continue (history-aware)
3. **Canonical facts** (name/email/phone/…) — never overwritten by weak learned rows
4. **Rewarded learned recall** — prefer highest `priority` among similarity ≥ threshold
5. Ollama generation with conversation rules
6. Escalation → pending for admin

On `approve`/`edit`: upsert into `learned.json` with high `reward_score`.  
On `reject`: do not delete history; add negative preference so recall skips that answer text.

### Layer E — Admin UX
**Portfolio (Django)** — superuser only:
- Route e.g. `/dashboard/training/` or `/train/`
- Lists clusters from agent API
- Actions call agent teach/reward API with secret token (server-side, never expose token to browser as a public constant — proxy via Django view)

**Agent (FastAPI)** — extend `/learn`:
- `GET /learn/inbox` → ranked JSON (auth: `TEACH_TOKEN` / admin header)
- `POST /learn/reward` → `{chat_id|item_id, action, answer?}`
- Keep existing HTML `/learn` working; improve it OR make Django the primary UI

Privacy copy: admin UI may say “review” / “train”. Public chat UI must **not** mention logging/training.

---

## 3. Paths (repos)

| Area | Path |
| --- | --- |
| Agent | `C:\Users\hezro\Desktop\harrison-agent\` |
| Portfolio | `C:\Users\hezro\Desktop\newportifolio\` |
| Existing learn | `app/routers/learn.py`, `app/agents/memory.py` |
| Chat policy | `app/agents/orchestrator.py`, `conversation.py`, `intent.py` |
| Deploy target | VPS `harr@197.248.201.233:2021` → `/home/harr/harrison-agent` + `systemctl restart harrison-agent` |
| Live site | PythonAnywhere `harrisonmuraya` — reload after Django changes |

---

## 4. Non-goals (do not do in v1)
- Full RLHF / PPO fine-tune of Ollama weights
- Sending visitor PII to external cloud ML APIs
- Showing “this chat is recorded” to visitors
- Letting non-superusers open the inbox
- Breaking canonical consistency for name/email/phone

---

## 5. Acceptance tests
1. Superuser opens training inbox → sees ranked new/weak questions.  
2. Non-superuser → 403 / redirect.  
3. Edit & teach email → next similar ask returns exact taught line.  
4. Reject a bad bio-dump → that dump is not recalled for `hi`.  
5. Visitor UI has zero training/logging language.  
6. Multi-turn history + canonical still work after reward wiring.  
7. Deployed agent on VPS serves new `/learn/inbox` and `/learn/reward`.

---

## 6. Implementation order for workers
1. Spec reward schema + inbox wireframes (markdown)  
2. `rewards.json` + memory APIs (`reward_answer`, `ranked_inbox`, cluster)  
3. FastAPI inbox/reward endpoints  
4. Scorer module `app/agents/training.py`  
5. Wire recall to use `reward_score`  
6. Django superuser Training page + proxy views  
7. Privacy audit  
8. Tests  
9. Deploy agent + PA  
10. Monitors confirm each track

---

## 7. Style / safety (carry forward)
- Kenyan-friendly, WhatsApp short voice  
- Answer only what was asked  
- Off-topic → not about Harrison  
- Never invent personal facts; admin teach is source of truth for new facts  
- Never mention exams/degrees  

---

**End of master prompt.** Workers must implement against this document and report: files changed, how to test, residual risks.
