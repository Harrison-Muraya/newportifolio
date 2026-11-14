# Reward schema and admin training inbox

Spec only. No Python or JS in this step. Implement against `docs/MASTER_PROMPT_ML_REWARD_TRAINING.md` and the shapes below.

This document fixes the JSON contracts, the cluster card, the three admin actions, the Django proxy, and the privacy rules. Later workers wire `rewards.json`, FastAPI, the scorer, recall, and the dashboard page to this file.

Primary UI is the portfolio dashboard. The existing agent HTML page at `GET /learn` stays as a fallback and is not replaced in v1.

---

## 1. Where data lives

| File | Role | Shape |
| --- | --- | --- |
| `harrison-agent/data/learning/chats.json` | Append-only visitor turns from `log_chat` | list of chat rows |
| `harrison-agent/data/learning/pending.json` | Unknown questions waiting on a human | list of pending rows |
| `harrison-agent/data/learning/learned.json` | Taught answer bank | list of learned rows |
| `harrison-agent/data/learning/rewards.json` | **New.** Append-only reward events | list of reward events |

All four files are JSON lists. A missing file is an empty list. A file that is not valid JSON is a hard error: readers return 500 and writers must not replace it with `[]`.

Chat cap stays 500 (`CHAT_CAP`). Reward events are not capped in v1 (expect tens to low hundreds). Learned rows grow only when an admin approve/edit or the existing auto-promote path writes one.

Tokenizer for every similarity number in this spec is the one already in `app/agents/memory.py`: lowercase `[a-z0-9']+` tokens, drop the existing stopword set, drop tokens of length ≤ 2.

Two similarity functions, do not collapse them:

- **Containment** (already `_similarity`): `|A ∩ B| / min(|A|, |B|)`. Used for recall match (≥ 0.6) and “same question” upsert (≥ 0.85).
- **Jaccard** (new, clustering only): `|A ∩ B| / |A ∪ B|`. Merge threshold **0.42**.

Embeddings are out of v1. Do not block the inbox on them.

---

## 2. `rewards.json` event

Append-only. One object per successful admin action. Never rewrite history to “fix” an old event; a later event is how a decision changes.

```json
{
  "id": "r_a1b2c3d4e5",
  "chat_id": "f3e8c91ab2",
  "cluster_id": "c_9f3a21bc01d2",
  "learned_id": "c0ffee12",
  "question": "how can I email you",
  "answer": "hezronmuraya9@gmail.com",
  "previous_answer": "I don't have that detail yet. Email hezronmuraya9@gmail.com or call +254 726 688 832 and I can follow up.",
  "action": "edit",
  "reward": 1.5,
  "answer_fingerprint": "7c1e0aa4b91d33f0",
  "question_fingerprint": "b04a91ce77d012ab",
  "member_ids": ["f3e8c91ab2", "aa0199cc21"],
  "signals": {
    "unknown": 0.35,
    "overshare": 0.0,
    "offtopic_leak": 0.0,
    "contradiction": 0.0,
    "low_reward": 0.0,
    "novelty": 0.18,
    "frequency": 0.08
  },
  "needs_training_score": 0.61,
  "created": "2026-11-14T12:04:11+00:00",
  "admin": "harrisonmuraya"
}
```

| Field | Rule |
| --- | --- |
| `id` | `r_` + 10 hex chars. Server-generated. |
| `chat_id` | Chat id of the card’s representative turn. Required. |
| `cluster_id` | See §5. Required. |
| `learned_id` | Learned row created or updated. `null` on reject, and `null` when approve only marks a canonical turn reviewed. |
| `question` | Representative visitor text, trimmed, max 4000 chars. |
| `answer` | The answer the admin kept, wrote, or blacklisted. Max 2000 chars. |
| `previous_answer` | Agent text shown on the card before the action. Max 4000. Empty string if none. |
| `action` | `"approve"` \| `"edit"` \| `"reject"`. |
| `reward` | `1.0` approve, `1.5` edit, `-1.0` reject. No other values in v1. |
| `answer_fingerprint` | First 16 hex chars of SHA-256 over the normalized answer (§3). |
| `question_fingerprint` | First 16 hex chars of SHA-256 over the normalized question. |
| `member_ids` | Chat ids in the cluster at action time. Includes `chat_id`. |
| `signals` | The seven weights from §4 at action time. Missing keys mean `0`. |
| `needs_training_score` | Clamped sum, 0–1, three decimals. |
| `created` | UTC ISO-8601 with offset. |
| `admin` | Django `request.user.username`. Server sets this. Ignore any `admin` field in the browser body. |

`learned_id` may be `null`. Every other field is required.

### Idempotency

A second POST with the same `chat_id` + `action` + `answer_fingerprint` while that cluster is already in the resulting state returns the existing event and does **not** add reward again.

- Approve or edit sticks when every `member_ids` chat has `trained: true` and `reward_action` equal to that action.
- Reject sticks when a reward event already exists for that `answer_fingerprint` and a question whose containment with this question is ≥ 0.55.

The HTTP status is still 200. Body includes `"idempotent": true`.

### What reject stores

Reject does not delete the chat row, the pending row, or the learned row. It appends the event above with `reward: -1.0`. Recall treats that `answer_fingerprint` as a blacklist key (§7).

---

## 3. Fingerprints

```text
normalize(text) = lowercase → strip → collapse internal whitespace to one space → trim to 4000 chars
fingerprint(text) = sha256(normalize(text)).hexdigest()[:16]
```

Same answer with different casing or extra spaces is one fingerprint. Different wording is a different fingerprint.

---

## 4. Needs-training score

Computed per chat row. Not stored on the chat. Stored on the reward event as a snapshot, and returned on the inbox cluster.

Each signal is `0` or the weight below. Sum, then clamp to `[0, 1]`. Round to 3 decimals.

| Key | Weight | High when |
| --- | --- | --- |
| `unknown` | 0.35 | `is_unknown(answer)`, or `agent` is `learning`, or the answer contains the escalation sentence, or `needs_review` is true and the answer is empty |
| `overshare` | 0.30 | `agent` is `greeting`, `smalltalk`, `thanks`, `vague`, or `continue`, **and** (`len(answer) > 180` or the answer mentions a project dump: HostPro, KENA, GitHub, Ashkey, Sunne, Alpha Loans, “fullstack”) |
| `offtopic_leak` | 0.28 | The question is off-topic (weather, politics, sports scores, celebrities — same idea as `is_offtopic`) **and** the answer is longer than the short refusal (more than 160 chars, or it states a fact that is not “not about Harrison”) |
| `contradiction` | 0.32 | `canonical_for(question)` returns a fact, and the normalized answer does not contain the distinctive token of that fact (email local-part, phone digits `726688832`, the name `Muraya`, and so on) |
| `low_reward` | 0.22 | Some reward event with `reward < 0` has question containment ≥ 0.55 against this question, or the best learned row within containment ≥ 0.55 has `reward_score < 0` |
| `novelty` | 0.18 | No learned row has containment ≥ 0.6 against this question |
| `frequency` | 0.15 × min(1, (n − 1) / 4) | `n` = chats in the last 7 days (by `created`) whose question containment is ≥ 0.55. One ask scores 0. Five or more score 0.15 |

Inbox sort: cluster score descending, then representative `created` descending.

A cluster’s score is the **max** member score, not the average. One bad turn should surface the whole group.

Default inbox includes a cluster when its score is ≥ 0.25, or any member has `needs_review: true`, or any member is untrained and the agent was `learning`. Trained approve/edit clusters leave the default tab (§8).

---

## 5. Clustering

Greedy, in score order, over the candidate chats (the 500 stored turns, filtered as above).

1. Take the highest-scoring chat not yet clustered. It is the medoid.
2. Every remaining chat whose question Jaccard with the medoid is ≥ **0.42** joins the cluster.
3. `cluster_id` = `c_` + first 12 hex chars of SHA-256 of the sorted significant tokens of the medoid question, joined by a single space.

The id is stable for the same medoid wording, so “email”, “your email”, and “how do I reach you” only share a card when Jaccard actually clears 0.42. Near-duplicates of one intent (“email / contact / reach you”) land together when they share those tokens; a phone question stays on its own card.

Representative question shown on the card is the medoid’s question. Other phrasings are `variants` (up to 4 extra strings, most recent first).

Do not cluster across a canonical fact boundary. If `canonical_for` returns different keys (`email` vs `phone`), keep them in separate cards even when Jaccard ≥ 0.42.

---

## 6. Learned row reward fields

Existing rows stay valid. Readers treat a missing reward field as the default. Do not rewrite `learned.json` just to backfill.

```json
{
  "id": "contact01",
  "question": "what is your email",
  "answer": "hezronmuraya9@gmail.com — harrisonmuraya8@gmail.com also reaches me.",
  "learned": "2026-11-14T00:00:00+00:00",
  "source": "seed",
  "reward_score": 1.5,
  "wins": 1,
  "losses": 0,
  "answer_fingerprint": "7c1e0aa4b91d33f0",
  "updated": "2026-11-14T12:04:11+00:00",
  "suppressed": false
}
```

| Field | Default if missing | Meaning |
| --- | --- | --- |
| `id` | — | Existing 8-char id, or the pending/chat id `teach()` already uses. New admin rows: 8 hex chars. |
| `question` | — | Taught question text. |
| `answer` | — | Taught answer text. Max 2000. |
| `learned` | — | First time this row was written. Do not change it on later rewards. |
| `source` | `"seed"` if absent on old rows; new writes set it | `"seed"` \| `"auto"` \| `"admin"`. |
| `reward_score` | `0` | Running sum of rewards applied to this row. Soft cap **[-5.0, 8.0]** after each add. |
| `wins` | `0` | Count of approve + edit applied to this row. |
| `losses` | `0` | Count of rejects applied to this row. |
| `answer_fingerprint` | computed on read | Fingerprint of `answer`. Persist it when the row is written. |
| `updated` | same as `learned` | Last reward write. |
| `suppressed` | `false` | `true` means recall must skip this row. |

`priority` is **not stored**. It depends on the live question:

```text
similarity = containment(live_question, row.question)
priority   = similarity * (1 + reward_score)
```

Examples: similarity 0.8 and `reward_score` 1.5 → priority 2.0. Similarity 0.8 and `reward_score` -1.0 → priority 0, which recall drops.

### Upsert rules

On approve or edit, find a learned row with question containment ≥ 0.85.

- If found, update that row in place (same `id`). Add the reward to `reward_score`, increment `wins`, set `source` to `"admin"` only on edit (approve keeps the previous source), refresh `answer_fingerprint` and `updated`. On edit, replace `answer` with the admin text. On approve, keep the row answer if it is already the approved text; if the row answer differs, do not silently overwrite — write a **new** row for the approved text instead and leave the old row’s score unchanged.
- If not found, append a new row. Approve starts `reward_score` at `1.0`, `wins` at `1`. Edit starts `reward_score` at `1.5`, `wins` at `1`, `source` `"admin"`.

On reject:

- If a learned row has the same `answer_fingerprint` and question containment ≥ 0.55, add `-1.0` to `reward_score` (then cap), increment `losses`, set `suppressed` to `true` when `reward_score < 0`.
- If no learned row matches, still append the reward event. Recall’s blacklist (§7) is enough.

Monitor rule, same as `teach()`: if `answer_blocked` or `question_blocked` (exams, transcripts, degrees), do not write a reward, do not touch learned, return HTTP 400 `blocked`.

Canonical rule: if `canonical_for(question)` is not null, do **not** upsert a learned row. Approve on a canonical cluster only marks the member chats reviewed (`trained: true`, `needs_review: false`) and appends a reward with `learned_id: null` and `reward: 1.0`. Edit that would save different wording returns HTTP 400 `canonical_locked`. Canonical copy stays in `conversation.py`. Recall never outranks it because the answer order in §7 runs canonical first.

---

## 7. How recall uses the fields

Answer order stays:

1. Monitor blocks (exams / degrees).
2. Greeting, smalltalk, thanks, vague, continue (history-aware). No bio on `hi`.
3. Canonical facts (name, email, phone, contact, stack, work, GitHub, LinkedIn, languages, hobbies, projects).
4. **Rewarded learned recall.**
5. Ollama, with the existing conversation rules.
6. Escalation → `pending.json`.

Step 4, for each learned row:

- Skip if `suppressed` is true.
- Skip if `answer_fingerprint` equals any reject event’s `answer_fingerprint` whose question containment is ≥ 0.55.
- Skip if `answer_blocked`.
- Skip if containment < 0.6 (same threshold as today).
- Skip if `priority <= 0`.
- Among the rest, pick the highest `priority`. Tie-break: higher `reward_score`, then newer `updated`.

Rejecting a long bio dump therefore does two things: the greeting path still answers `hi` with the short greeting, and if that dump exists as a learned row it is suppressed so recall cannot hand it back.

Approve and edit do not change steps 1–3. A weak or strong learned row never replaces a canonical fact.

---

## 8. Chat row fields the reward flow may set

`log_chat` already writes `id` (10 hex), `question`, `answer`, `agent`, `source`, `created`, `needs_review`. Reward actions may set:

| Field | When |
| --- | --- |
| `trained` | `true` after approve or edit |
| `needs_review` | `false` after approve or edit. Stays `true` after reject if the cluster still has no positive taught answer |
| `reward_action` | `"approve"` \| `"edit"` \| `"reject"` |
| `reward_id` | Id of the latest reward event |
| `trained_at` | UTC ISO-8601 on approve or edit |
| `taught_answer` | Edit only. The admin text. Do **not** replace `answer` — the original agent text stays for audit |

Reject does not set `trained`. The historical `answer` is never deleted.

---

## 9. Agent HTTP

Auth for the two new routes: header `X-Teach-Token: <TEACH_TOKEN>` **or** `Authorization: Bearer <TEACH_TOKEN>`.

- Token is `settings.teach_token` / env `TEACH_TOKEN`.
- These two routes require a non-empty token that matches. Empty token → **401**. (The legacy `GET/POST /learn` page may keep its current empty-token behavior. Do not copy that looseness onto the inbox.)
- Do not accept the token as a query parameter on these two routes.
- Compare with a constant-time compare.

`admin` is taken from `X-Admin-User` if present, else `"harrisonmuraya"`. Django is what sets that header. Cap it at 64 chars, strip spaces.

### `GET /learn/inbox`

Query:

| Param | Default | Values |
| --- | --- | --- |
| `status` | `open` | `open` \| `taught` \| `rejected` \| `all` |
| `limit` | `40` | 1–100 |

`open`: score ≥ 0.25 or needs review, and the cluster is not fully trained by approve/edit.  
`taught`: latest reward action on the cluster is approve or edit.  
`rejected`: latest reward action is reject, and there is no later approve/edit.  
`all`: open + taught + rejected, still sorted by score.

Response 200:

```json
{
  "ok": true,
  "status": "open",
  "generated": "2026-11-14T12:10:00+00:00",
  "counts": { "open": 3, "taught": 12, "rejected": 1 },
  "clusters": [
    {
      "cluster_id": "c_9f3a21bc01d2",
      "score": 0.61,
      "status": "open",
      "canonical_key": null,
      "signals": {
        "unknown": 0.35,
        "overshare": 0.0,
        "offtopic_leak": 0.0,
        "contradiction": 0.0,
        "low_reward": 0.0,
        "novelty": 0.18,
        "frequency": 0.08
      },
      "question": "how can I email you",
      "variants": ["what's your email", "email address?"],
      "member_count": 3,
      "frequency_7d": 3,
      "latest_created": "2026-11-14T11:58:02+00:00",
      "representative": {
        "chat_id": "f3e8c91ab2",
        "question": "how can I email you",
        "answer": "I don't have that detail yet. Email hezronmuraya9@gmail.com or call +254 726 688 832 and I can follow up.",
        "agent": "learning",
        "created": "2026-11-14T11:58:02+00:00",
        "needs_review": true,
        "trained": false
      },
      "answers": [
        {
          "answer": "I don't have that detail yet. Email hezronmuraya9@gmail.com or call +254 726 688 832 and I can follow up.",
          "fingerprint": "aa11bb22cc33dd44",
          "count": 2,
          "selected": true
        }
      ],
      "learned_preview": null,
      "reward_preview": null,
      "actions": {
        "approve": true,
        "edit": true,
        "reject": true,
        "canonical_locked": false
      }
    }
  ]
}
```

`answers` lists distinct answer fingerprints in the cluster, most common first, max 3. `selected: true` marks the text the Approve button will keep (most recent non-empty answer that is not only the escalation, else the most recent answer).

`learned_preview` is the best current learned row within containment ≥ 0.6, or `null`:

```json
{
  "learned_id": "contact02",
  "question": "what is your email",
  "answer": "hezronmuraya9@gmail.com — harrisonmuraya8@gmail.com also reaches me.",
  "reward_score": 0,
  "wins": 0,
  "losses": 0,
  "suppressed": false,
  "similarity": 0.72
}
```

`reward_preview` is the latest reward event for this cluster or for a question with containment ≥ 0.85, or `null`:

```json
{
  "id": "r_a1b2c3d4e5",
  "action": "reject",
  "reward": -1.0,
  "created": "2026-11-14T10:00:00+00:00",
  "admin": "harrisonmuraya"
}
```

When `canonical_key` is set (`"email"`, `"phone"`, `"name"`, …), `actions.edit` is false, `actions.canonical_locked` is true, and `actions.approve` means “mark reviewed” only.

Errors:

| Status | Body | When |
| --- | --- | --- |
| 401 | `{"detail": "Unauthorized."}` | Missing or wrong token |
| 500 | `{"detail": "Training store is unreadable."}` | Corrupt JSON. Do not overwrite the file |

No visitor ip, user-agent, or session id exists today. Do not add those fields to this payload.

### `POST /learn/reward`

Request JSON:

```json
{
  "chat_id": "f3e8c91ab2",
  "cluster_id": "c_9f3a21bc01d2",
  "action": "edit",
  "answer": "hezronmuraya9@gmail.com — harrisonmuraya8@gmail.com also reaches me."
}
```

| Field | Rule |
| --- | --- |
| `chat_id` | Required. 1–40 chars. Must exist in `chats.json` or `pending.json`. |
| `cluster_id` | Optional. If sent, it must match a cluster that contains `chat_id`, else 400 `cluster_mismatch`. Server recomputes the cluster either way and stores that id. |
| `action` | Required. `approve` \| `edit` \| `reject`. |
| `answer` | Required for `edit` (1–2000 chars after trim). Optional for `approve` (omit = the selected cluster answer). Ignored for `reject` except as a hint; server blacklists the selected answer fingerprint, not a browser-invented string, unless `answer` is sent and its fingerprint matches one of the cluster’s answers. |

Success 200:

```json
{
  "ok": true,
  "idempotent": false,
  "reward": {
    "id": "r_a1b2c3d4e5",
    "action": "edit",
    "reward": 1.5,
    "chat_id": "f3e8c91ab2",
    "cluster_id": "c_9f3a21bc01d2",
    "learned_id": "c0ffee12",
    "answer_fingerprint": "7c1e0aa4b91d33f0",
    "created": "2026-11-14T12:04:11+00:00"
  },
  "learned": {
    "id": "c0ffee12",
    "reward_score": 1.5,
    "wins": 1,
    "losses": 0,
    "suppressed": false
  }
}
```

On reject, `learned` is `null` when no row was updated. When a row was suppressed, return that row’s new `reward_score`, `losses`, and `suppressed: true`.

| Status | `detail` code | When |
| --- | --- | --- |
| 400 | `empty_answer` | Edit with blank answer |
| 400 | `blocked` | Exam / degree / transcript content |
| 400 | `canonical_locked` | Edit on a canonical question, or approve/edit answer that contradicts the canonical fact |
| 400 | `cluster_mismatch` | `cluster_id` does not contain `chat_id` |
| 400 | `not_found` | `chat_id` is not in chats or pending |
| 400 | `answer_too_long` | Over 2000 chars |
| 401 | `Unauthorized.` | Token |
| 500 | `Training store is unreadable.` | Corrupt file |

Pending rows taught by edit are removed from `pending.json` the same way `teach()` already removes them. Approve of an unknown question also removes the matching pending row once the learned upsert succeeds.

---

## 10. Admin inbox UX

Surface: portfolio dashboard, superuser only, same shell as Messages (`dashboard_base.html`).

Visual tokens already in the shell: background `#F4F2EB`, surface `#FDFCF8`, ink `#0D0D0D`, muted `#7A7060`, accent `#E8391D`, type Outfit for UI and Fraunces for the small wordmark. Training cards use that shell. Do not invent a second admin theme.

### Nav

Add one sidebar link, **Training**, in the Content group, under Messages and above Projects. Badge = `counts.open`. Active state block name: `nav_training`.

Link copy is “Training”. Tooltip / page subtitle may say “Review answers”. Do not say “recorded chats” or “we log visitors” anywhere in this UI.

### Page

`GET /dashboard/training/`

Top bar title: **Training**. Subtitle under the title, one line: “Review weak answers. The public chat does not show this.”

Tabs (links, not a second app):

| Tab | Query | What it lists |
| --- | --- | --- |
| Needs training | `?status=open` (default) | Open clusters |
| Taught | `?status=taught` | Approve / edit |
| Rejected | `?status=rejected` | Reject, still no later teach |
| All | `?status=all` | Everything in the payload |

Each tab shows its count from `counts`.

Server renders the first paint. The browser does not call the agent. The browser does not see `TEACH_TOKEN`.

### Cluster card

One card per cluster. Stack, score order, full width of the dashboard content column (max ~760px so the answer stays readable).

```text
┌─────────────────────────────────────────────────────────────┐
│  0.61   Unknown   New                         3 similar · 2d │
│                                                             │
│  how can I email you                                        │
│  also: what's your email · email address?                   │
│                                                             │
│  Agent reply                                                │
│  I don't have that detail yet. Email hezronmuraya9@…        │
│                                                             │
│  Taught already                                             │
│  hezronmuraya9@gmail.com — harrisonmuraya8@gmail.com also…  │
│  score 0 · not suppressed                                   │
│                                                             │
│  [ Approve ]   [ Edit & teach ]   [ Reject ]                │
└─────────────────────────────────────────────────────────────┘
```

Regions:

1. **Score** — one decimal in a pill (`0.6`). Accent pill when score ≥ 0.5, muted when lower.
2. **Signal chips** — only signals with weight > 0. Labels: Unknown, Overshare, Off-topic, Contradiction, Low reward, New, Frequent. Max 4 chips; if more, show the four heaviest.
3. **Meta** — `member_count` as “N similar”, relative day from `latest_created` (“today”, “2d”). No raw visitor id.
4. **Question** — medoid text. Under it, variants in muted type, middle-dot separated. If `canonical_key` is set, a chip **Canonical** sits on the question line and the helper line reads “This fact stays on the canonical answer.”
5. **Agent reply** — `representative.answer`, preserved whitespace, clamp to ~8 lines with a “Show all” disclosure. If `answers.length > 1`, a second line under the reply: “Also seen:” plus the other answer texts, and Approve applies to the selected one. Switching the selected answer is a radio, not a second form.
6. **Taught already** — only if `learned_preview` is non-null. Show that answer, `reward_score`, wins/losses, and “suppressed” when true. Hide the block when null.
7. **Last review** — only if `reward_preview` is non-null. One muted line: “Rejected · 14 Nov · harrisonmuraya” (or Approved / Edited).
8. **Actions** — three buttons, left to right.

Button labels and meaning:

| Button | Label | Enabled when |
| --- | --- | --- |
| Approve | `Approve` | `actions.approve`. On a canonical card the label is `Mark reviewed`. |
| Edit | `Edit & teach` | `actions.edit`. Hidden (not just disabled) when `canonical_locked`. |
| Reject | `Reject` | `actions.reject`. |

Approve is the filled accent button. Edit is an outline button. Reject is text-style in muted ink, not bright red, so it is not the default mis-click. Reject still asks for a confirm: “Skip this reply next time a similar question shows up?” Confirm / Cancel. No confirm on Approve. Edit’s confirm is the save button inside the editor.

### Edit open state

Choosing Edit & teach expands the card. Do not navigate away.

- Textarea prefilled with `learned_preview.answer` if present, else the selected agent answer, else empty.
- Placeholder: “Write the short reply to use next time.”
- Helper: “One or two sentences. Answer only what they asked.”
- Max 2000 characters, counter at 1800+.
- `Save & teach` submits action `edit`. `Cancel` collapses and restores the three buttons.
- While saving, disable the buttons and show “Saving…” on the button that was clicked.

### After a successful action

Remove the card from the open list with no full reload (or re-render from a fresh inbox fetch through Django). Toast, 3 seconds, bottom of the content column:

- Approve → “Approved. Similar questions will prefer this reply.”
- Mark reviewed → “Marked reviewed. Canonical answer unchanged.”
- Edit → “Taught. The next similar question uses your reply.”
- Reject → “Rejected. That reply will not be reused.”

Idempotent success uses the same toast plus “Already saved.” Do not double-count in the UI.

### Empty, loading, error

| State | Copy |
| --- | --- |
| Loading | Skeleton of two cards. No token, no agent URL. |
| Open tab empty | “Nothing needs a review. New weak answers will land here.” |
| Taught empty | “No taught answers yet.” |
| Rejected empty | “No rejected replies.” |
| Agent unreachable | “Training inbox is offline. Try again in a minute.” Retry button reloads the page. Do not print the agent host, the tunnel URL, or the token. |
| 401 from agent | Same offline message. Log the real status server-side only. |
| 400 `blocked` | Inline on the card: “That text mentions exams or degrees, so it was not saved.” |
| 400 `canonical_locked` | Inline: “That fact is canonical. It was not overwritten.” |
| Other 400 | Inline: “Could not save that review.” |
| Network drop mid-save | Inline: “Not saved. Try again.” Leave the textarea contents in place. |

Taught and Rejected cards are read-only except Edit & teach on a rejected card (so Harrison can still write the right answer later). Approve on an already-taught card is hidden.

### What the card must not show

- The words “logged”, “recorded”, “training data”, “RLHF”, “reward model”, “PII”.
- Chat ids, fingerprints, tokens, file paths.
- A transcript of the whole 500-row file. Variants are capped at 4.
- Visitor-supplied emails or phone numbers highlighted as “captured leads”. If a visitor typed their own contact in the question, it is just question text on an admin-only page.

---

## 11. Django route sketch

Portfolio app `harrison`. Decorator already exists: `superuser_required` (anonymous → `/login/?next=…`, authenticated non-superuser → redirect home).

Settings to add, env only, never in a template or a JS constant:

- `TEACH_TOKEN` — same secret as the agent.
- `AGENT_BASE_URL` — origin plus optional path prefix, **without** `/chat`. If unset, derive it by stripping a trailing `/chat` from the existing `AGENT_CHAT_URL`.

Routes to add in `harrison/urls.py`:

```text
path("dashboard/training/", views.training_inbox, name="training_inbox")
path("dashboard/training/reward/", views.training_reward, name="training_reward")
```

Do not put this under `/dashboard/inbox/`. That URL is the contact-message inbox.

Sketch of behavior (not the implementation):

```text
training_inbox(request):                      # GET, superuser_required
    status = query "status" if in {open, taught, rejected, all} else "open"
    payload = server_get(
        AGENT_BASE_URL + "/learn/inbox?status=" + status + "&limit=40",
        headers = { "X-Teach-Token": TEACH_TOKEN, "X-Admin-User": request.user.username },
        timeout = 15s,
    )
    on network/5xx/401: render the page with inbox_error=True and clusters=[]
    else: render harrison/training.html with clusters, counts, status
    context also includes unread_count so the Messages badge still works

training_reward(request):                     # POST, superuser_required, CSRF
    body = JSON { chat_id, cluster_id?, action, answer? }
    reject if action not in {approve, edit, reject}
    reject if chat_id missing or longer than 40
    forward = {
        chat_id, cluster_id, action, answer,
    }                                          # never forward a browser "admin" or "token"
    response = server_post(
        AGENT_BASE_URL + "/learn/reward",
        json = forward,
        headers = {
            "X-Teach-Token": TEACH_TOKEN,
            "X-Admin-User": request.user.username,
            "Content-Type": "application/json",
        },
        timeout = 15s,
    )
    return JsonResponse(agent_body, status=agent_status)
    on network error: JsonResponse {"detail": "offline"}, status 502
```

Browser `fetch` goes to `/dashboard/training/reward/` with the CSRF token. It does not know the agent URL or `TEACH_TOKEN`.

`training.html` extends `dashboard_base.html`, sets `nav_training` active, and uses the card layout in §10.

Sidebar badge for Training uses `counts.open` from this page’s context. Other dashboard pages may leave the badge off until they also proxy a cheap count; v1 does not need the badge on Overview.

Reload PythonAnywhere after the Django views ship. The agent on the VPS must already be serving `/learn/inbox` and `/learn/reward`.

---

## 12. Approve, edit, reject — exact effects

### Approve (`reward +1.0`)

1. Resolve the cluster and the selected answer text.
2. If canonical: mark every member chat `trained: true`, `needs_review: false`, `reward_action: "approve"`, `trained_at` now. Append the reward with `learned_id: null`. Stop.
3. Else upsert learned as in §6 with `+1.0` and `wins + 1`.
4. Mark every member chat trained the same way. Do not rewrite their `answer`.
5. Drop a matching pending row when the question containment is ≥ 0.9.

Live effect: the next non-canonical ask with containment ≥ 0.6 prefers this row when its priority wins.

### Edit & teach (`reward +1.5`)

1. Trim the answer. Empty → 400 `empty_answer`. Over 2000 → 400 `answer_too_long`.
2. Blocked content → 400 `blocked`. Canonical question, or an answer that contradicts the canonical fact → 400 `canonical_locked`.
3. Upsert learned with the new answer, `source: "admin"`, `reward_score += 1.5`, `wins += 1`, `suppressed: false`.
4. On every member chat: `trained: true`, `needs_review: false`, `reward_action: "edit"`, `trained_at` now, `taught_answer` = the new text. Leave `answer` as the original agent text.
5. Remove the matching pending row.

Live effect: the next similar ask returns this exact text, as long as steps 1–3 of the answer order do not claim the question.

### Reject (`reward -1.0`)

1. Fingerprint the selected agent answer (the one on the card).
2. Append the reward event. `learned_id` is the suppressed row’s id, or `null`.
3. If a learned row matches fingerprint + question containment ≥ 0.55: `reward_score -= 1.0`, `losses += 1`, `suppressed: true` when the score is negative.
4. Set `reward_action: "reject"` and `reward_id` on member chats. Do not set `trained`. Do not clear `needs_review` when the cluster still has no positive learned answer — it stays on the Rejected tab and can still be taught.
5. Do not delete chats, pending, or learned rows.

Live effect: recall skips that answer text for similar questions. `hi` still hits the greeting path, so a rejected bio dump is not what greeting returns, and it is also ineligible if recall is ever reached.

---

## 13. Privacy rules

Visitors must not be able to tell that chats are stored or used to train.

Public surfaces (portfolio chat page, chat widget, agent `index.html`, public JSON from `/chat`):

- No copy containing: recorded, recording, logged, logging, training, train this, reward, inbox, “used to improve”, “we store chats”.
- No link to `/dashboard/training/`, `/learn`, or `/learn/inbox`.
- Chat responses stay `{reply, agent}` style. They do not include scores, fingerprints, reward ids, or “needs review”.
- The existing widget must not gain a disclaimer. Absence of a disclaimer is the requirement.

Admin surfaces may say “review” and “train”. The training page subtitle in §10 is the allowed sentence. The legacy `/learn` HTML may keep “Private inbox. Visitors do not see this page.”

Access:

- Inbox page and reward POST: `superuser_required` only. Non-superuser gets the existing redirect home (browser) or 403 if a client calls the reward URL without a session — prefer 403 on the JSON reward URL so a normal user does not get a silent redirect that looks like success.
- Anonymous: redirect to login for the HTML page; 403 for the JSON reward URL.
- `TEACH_TOKEN` lives in the agent env and the PythonAnywhere env. It is not in git, not in `settings.py` defaults, not in HTML, not in JS, not in query strings.
- Django logs may record status codes. They must not record the token or full answer bodies at INFO.

Data leaving the machine:

- No visitor question or answer is sent to an external ML API. Scoring is local heuristics. Optional embeddings later must be a local model, not a hosted one.
- Reward actions do not open WhatsApp and do not call `webbrowser`. The existing pending WhatsApp link stays on the legacy `/learn` page only.

PII inside the questions:

- A visitor may type their own email or phone. That text stays inside `chats.json` on the agent VPS and is shown only on the superuser training page.
- Do not add fields for IP, account id, or browser fingerprint.
- Do not copy training JSON into the portfolio database.

Files:

- `data/learning/*.json` is not served by FastAPI static files and not by Django `static/`.
- A corrupt store fails closed (500) instead of being reset to an empty list.

Canonical and monitor boundaries are privacy-adjacent product rules, not just quality rules: reward cannot publish exam or degree details, and cannot overwrite name, email, or phone.

---

## 14. Acceptance checks for this spec

1. `GET /learn/inbox` with the token returns `clusters` sorted by `score` desc, each cluster shaped as §9.
2. Wrong or missing token on `/learn/inbox` and `/learn/reward` → 401. Legacy `/learn` still loads as it does today.
3. `POST /learn/reward` with `edit` writes one reward event (`reward: 1.5`), upserts `learned.json` with `reward_score`, `wins`, `source: "admin"`, and sets `taught_answer` without erasing the original chat `answer`.
4. A second identical POST returns the same reward id and does not change `reward_score`.
5. `reject` leaves the chat in the file, sets `suppressed` (or a blacklist hit) so recall will not return that answer text, and does not change greeting behavior for `hi`.
6. Edit on “what is your email” → 400 `canonical_locked`, canonical string unchanged.
7. Edit containing a degree or exam → 400 `blocked`, no new reward line.
8. `/dashboard/training/` as superuser renders cards. As a normal user, redirect home. Logged out, redirect to login.
9. View-source and the chat widget contain no `TEACH_TOKEN` and none of the banned public phrases in §13.
10. `priority` used at recall equals `containment * (1 + reward_score)` and a negative score cannot beat a positive one on an equal match.
