# MONITOR A — ML API report

**Verdict: PASS (5 / 5).**  
**Inspected:** 2026-11-14 ~04:15 (UTC+3). Filesystem read plus local pytest and a TestClient auth probe. No agent code was changed.  
**Agent tree:** `C:\Users\hezro\Desktop\harrison-agent`  
**Spec:** `docs/MASTER_PROMPT_ML_REWARD_TRAINING.md` Layer B–D and worker steps 2–5.  
**Prior report:** FAIL 0/4 at ~03:35. Those four gaps are now on disk, and the auth check holds.

## 1. `app/agents/training.py` — PASS

File exists. It exports:

- `needs_training_score(chat_row) -> float` — clamped 0–1. Weights cover unknown, overshare, offtopic leak, contradiction vs `canonical_for`, low reward, novelty, and frequency.
- `cluster_questions(rows) -> list[dict]` — token Jaccard via `memory._jaccard`, plus short contact asks (email / phone / reach you) on one card.
- `ranked_inbox(limit=20)` — scores chat rows (and pending rows that are not already in chats), clusters them, drops scores under 0.2, sorts highest first.

`app/routers/learn.py` calls this `ranked_inbox`, not the extra copy in `memory.py`.

## 2. Rewards, recall, reject, canonical — PASS

- `memory.REWARDS_PATH` is `data/learning/rewards.json`. The file is created on the first reward write (`_write`). It is not on disk until then. `data/learning/` currently has `learned.json` and `.gitkeep`.
- `reward_answer(action, chat_id="", item_id="", answer=None, admin="harrisonmuraya")` appends an event (`id`, `chat_id`, `question`, `answer`, `action`, `reward`, `fingerprint`, `created`, `admin`) and updates the learned row: `reward_score`, `wins` / `losses`. Values are approve `+1.0`, edit `+1.5`, reject `-1.0`. Reject does not delete the chat.
- Reject blacklists the answer. The event stores `fingerprint` (`answer_fingerprint`). `rejected_fingerprints()` loads reject events. `recall` skips a learned row when that fingerprint matches, when the row is marked `rejected`, or when `reward_score < 0`.
- `recall` prefers `reward_score` among learned rows that clear similarity `0.6`: it keeps the band within `0.05` of the best similarity, then sorts by higher `reward_score`. Rows below `0.6` stay out.
- Canonical still wins over learned. `recall` returns `None` when `canonical_for(question)` is set, and it skips learned rows whose own question is a canonical fact. `orchestrator._instant` returns the canonical line before it calls `recall`, on both `answer` and `stream_answer`.

## 3. `GET /learn/inbox` and `POST /learn/reward` — PASS

`app/routers/learn.py` registers both. `main.py` includes `learn.router`.

- `GET /learn/inbox` returns `training.ranked_inbox()` as JSON (`clusters` and `items`).
- `POST /learn/reward` accepts `{chat_id|item_id, action, answer?}` and calls `memory.reward_answer`. Unknown action, missing id, or edit with no answer → 400.
- Existing `GET /learn` and `POST /learn` are still registered.

## 4. Auth on inbox and reward — PASS

`_inbox_token_ok` is fail-closed. If `settings.teach_token` is blank, it returns false before comparing, and both routes raise **401**. A matching `X-Teach-Token` or `Authorization: Bearer <token>` is accepted (`secrets.compare_digest`). Those handlers have no token query parameter and do not read a body token.

Probe with `TestClient` (token value not recorded):

| Request | Status |
| --- | --- |
| `TEACH_TOKEN=""` on GET `/learn/inbox` and POST `/learn/reward`, including a header | 401 |
| Token set, no header | 401 |
| `?token=` on GET and POST | 401 |
| JSON body `token` with no header | 401 |
| `X-Teach-Token` or `Bearer` with the right secret | 200 |
| Wrong Bearer | 401 |

`GET /learn` and `POST /learn` still use `_allowed`, which opens when `TEACH_TOKEN` is empty and still accepts a query or body token. That is the old HTML route, outside this check.

## 5. Tests — PASS (4 passed after an import shim)

`tests/test_reward_training.py` has four tests: unknown score, edit-then-recall, reject-blocks-recall, inbox/reward API.

- Stock `python -m pytest tests/test_reward_training.py` did not collect. Import died in `anyio` on `from typing_extensions import sentinel` (this machine’s `typing_extensions` only has `Sentinel`). Zero tests ran. That is the local site-packages mix, not an assertion failure.
- Same file, project on `sys.path`, with `typing_extensions.sentinel` aliased to `Sentinel` in that process only: **4 passed**, 1 warning, 2.33s.

## Residuals (do not flip the verdict)

- Recall’s reward preference is a 0.05 similarity tie-break, plus a hard skip of `reward_score < 0`. It does not rank every candidate by `similarity * (1 + reward_score)`.
- `memory.ranked_inbox` is a second inbox helper. The HTTP route uses `training.ranked_inbox`.
- `rewards.json` appears on first `reward_answer`, not as a checked-in file.
- HTML `/learn` stays fail-open when `TEACH_TOKEN` is empty.

| # | Check | Result |
| --- | --- |
| 1 | `training.py`: `needs_training_score`, `cluster_questions`, `ranked_inbox` | **PASS** |
| 2 | `REWARDS_PATH` + `reward_answer`; recall prefers `reward_score`; reject fingerprints; `canonical_for` wins | **PASS** |
| 3 | `GET /learn/inbox` and `POST /learn/reward` | **PASS** |
| 4 | Empty `TEACH_TOKEN` → 401; `X-Teach-Token` or Bearer; no query token on those routes | **PASS** |
| 5 | `tests/test_reward_training.py` (4 passed with import shim; stock pytest did not collect) | **PASS** |
