"""Section 5 smoke test: ranked training inbox and reward approve.

Probes the local agent and the documented public agent. Sends TEACH_TOKEN
as the admin header. Does not deploy and does not restart any service.

When GET /learn/inbox is absent, prints SKIP and exits 0.
When that inbox responds, checks the ranked JSON shape, then POSTs
action=approve for the top card (reward +1.0).

Usage (PowerShell, from this folder):

    $env:TEACH_TOKEN = "<admin token>"
    python .\\_ml_training_acceptance.py

Optional base URL (skips the default probe list):

    $env:AGENT_BASE_URL = "http://127.0.0.1:8000"
    python .\\_ml_training_acceptance.py

Exit codes:
    0  inbox shape and approve passed, or SKIP because the APIs are not served
    1  an inbox/reward API responded but the shape or approve flow failed
    2  bad arguments
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import quote
from typing import Any

INBOX_PATH = "/learn/inbox"
REWARD_PATH = "/learn/reward"

# README local port, the port the VPS agent binds, then the documented public agent.
DEFAULT_BASES = (
    "http://127.0.0.1:8000",
    "http://127.0.0.1:2020",
    "http://197.248.201.233:2020",
)

LIST_KEYS = ("items", "clusters", "inbox", "results", "cards")
ID_KEYS = ("chat_id", "item_id", "id", "cluster_id")


class ProbeMiss(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AuthRequired(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def bases() -> list[str]:
    override = os.environ.get("AGENT_BASE_URL", "").strip().rstrip("/")
    if override:
        return [override]
    return [item.rstrip("/") for item in DEFAULT_BASES]


def timeout_for(base: str) -> float:
    host = base.lower()
    if "127.0.0.1" in host or "localhost" in host:
        return 3.0
    return 8.0


def auth_headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["X-Teach-Token"] = token
        headers["Authorization"] = f"Bearer {token}"
        headers["TEACH_TOKEN"] = token
    return headers


def redact(url: str) -> str:
    marker = "token="
    if marker not in url:
        return url
    head, _, tail = url.partition(marker)
    value, sep, rest = tail.partition("&")
    hidden = f"{head}{marker}***"
    if sep:
        hidden += sep + rest
    return hidden


def request_raw(
    method: str,
    url: str,
    token: str,
    body: dict[str, str] | None = None,
    timeout: float = 5.0,
) -> tuple[int, str, bytes]:
    headers = auth_headers(token)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ProbeMiss(f"unreachable ({reason})") from exc


def parse_json(raw: bytes, content_type: str) -> Any:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        raise ProbeMiss("empty body")
    looks_json = "json" in content_type.lower() or text[:1] in "{["
    if not looks_json:
        raise ProbeMiss("response is not JSON")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProbeMiss(f"invalid JSON ({exc.msg})") from exc


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def with_token_query(url: str, token: str) -> str:
    join = "&" if "?" in url else "?"
    return f"{url}{join}token={quote(token, safe='')}"


def fetch(method: str, url: str, token: str, body: dict[str, str] | None, timeout: float) -> tuple[str, int, Any]:
    """Return the URL that worked, status, and JSON. Raises ProbeMiss or AuthRequired."""
    status, content_type, raw = request_raw(method, url, token, body, timeout)
    used = url
    if status in (401, 403) and token and "token=" not in url:
        used = with_token_query(url, token)
        status, content_type, raw = request_raw(method, used, token, body, timeout)
    if status in (401, 403):
        if token:
            raise AuthRequired(f"HTTP {status} (TEACH_TOKEN rejected)")
        raise AuthRequired(f"HTTP {status} (TEACH_TOKEN is not set)")
    if status == 404:
        raise ProbeMiss("HTTP 404")
    if status not in (200, 201):
        raise ProbeMiss(f"HTTP {status}")
    payload = parse_json(raw, content_type)
    return used, status, payload


def extract_items(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return value
    fail(
        "inbox JSON must be a list, or an object with one of: "
        + ", ".join(LIST_KEYS)
    )
    return []


def has_question(item: dict[str, Any]) -> bool:
    for key in ("question", "questions", "cluster", "text"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and any(isinstance(part, str) and part.strip() for part in value):
            return True
    return False


def card_ids(item: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    for key in ID_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            found[key] = value.strip()
        elif isinstance(value, int) and not isinstance(value, bool):
            found[key] = str(value)
    return found


def score_of(item: dict[str, Any], index: int) -> float:
    if "needs_training_score" not in item:
        fail(f"inbox item {index} is missing needs_training_score")
    value = item["needs_training_score"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"inbox item {index} needs_training_score must be a number from 0 to 1, got {value!r}")
    number = float(value)
    if number < 0 or number > 1:
        fail(f"inbox item {index} needs_training_score must be from 0 to 1, got {number}")
    return number


def check_inbox(payload: Any) -> list[dict[str, Any]]:
    items = extract_items(payload)
    cards: list[dict[str, Any]] = []
    scores: list[float] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            fail(f"inbox item {index} must be an object")
        if not has_question(item):
            fail(f"inbox item {index} is missing question text")
        if not card_ids(item):
            fail(f"inbox item {index} is missing chat_id, item_id, or id")
        scores.append(score_of(item, index))
        cards.append(item)
    for index in range(len(scores) - 1):
        if scores[index] + 1e-9 < scores[index + 1]:
            fail(
                "inbox is not ranked by needs_training_score descending "
                f"({scores[index]} before {scores[index + 1]})"
            )
    if cards:
        print(
            f"PASS: inbox JSON shape ok ({len(cards)} item(s), "
            f"top needs_training_score {scores[0]:.3f})."
        )
    else:
        print("PASS: inbox JSON shape ok (0 items).")
    return cards


def approve_body(card: dict[str, Any]) -> dict[str, str]:
    ids = card_ids(card)
    body: dict[str, str] = {"action": "approve"}
    if ids.get("chat_id"):
        body["chat_id"] = ids["chat_id"]
    if ids.get("item_id"):
        body["item_id"] = ids["item_id"]
    if "chat_id" not in body and "item_id" not in body:
        body["item_id"] = ids.get("id") or ids["cluster_id"]
    return body


def check_reward(status: int, payload: Any) -> None:
    if status not in (200, 201):
        fail(f"POST /learn/reward returned HTTP {status}")
    if not isinstance(payload, dict):
        fail("reward response must be a JSON object")
    if payload.get("ok") is False:
        fail(f"reward response reports failure: {json.dumps(payload)[:300]}")
    action = payload.get("action")
    if action is not None and action != "approve":
        fail(f"reward action is {action!r}; approve flow expects action 'approve'")
    if "reward" in payload:
        reward = payload["reward"]
        if isinstance(reward, bool) or not isinstance(reward, (int, float)):
            fail(f"approve reward must be 1.0, got {reward!r}")
        if abs(float(reward) - 1.0) > 1e-6:
            fail(f"approve reward must be 1.0, got {reward!r}")
    reward_text = ""
    if "reward" in payload:
        reward_text = f" reward={payload['reward']}"
    print(f"PASS: reward approve flow ok (HTTP {status}{reward_text}).")


def skip(tried: list[str]) -> None:
    print(
        "SKIP: /learn/inbox is not served on the local or documented agent URLs. "
        "Inbox JSON shape and reward approve were not tested."
    )
    print("Tried:")
    print("\n".join(tried))
    print("Set AGENT_BASE_URL when GET /learn/inbox and POST /learn/reward are up.")


def main() -> None:
    unknown = [arg for arg in sys.argv[1:] if arg not in ("-h", "--help")]
    if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
        print(__doc__.strip())
        return
    if unknown:
        print("This script takes no arguments. Set TEACH_TOKEN and optional AGENT_BASE_URL.")
        raise SystemExit(2)

    token = os.environ.get("TEACH_TOKEN", "").strip()
    tried: list[str] = []
    auth_hits: list[str] = []

    for base in bases():
        inbox_url = base + INBOX_PATH
        try:
            used_url, _status, payload = fetch("GET", inbox_url, token, None, timeout_for(base))
        except AuthRequired as exc:
            auth_hits.append(f"  {inbox_url} -> {exc.reason}")
            continue
        except ProbeMiss as exc:
            tried.append(f"  {inbox_url} -> {exc.reason}")
            continue

        print(f"Using {redact(used_url)}")
        if not token:
            print("Note: TEACH_TOKEN is empty; the inbox accepted the call without a token.")
        cards = check_inbox(payload)
        if not cards:
            print("SKIP: reward approve was not run because the inbox has no card to approve.")
            return

        body = approve_body(cards[0])
        reward_url = base + REWARD_PATH
        try:
            _used, status, reward_payload = fetch(
                "POST", reward_url, token, body, timeout_for(base)
            )
        except AuthRequired as exc:
            fail(f"{reward_url} {exc.reason}")
        except ProbeMiss as exc:
            if exc.reason == "HTTP 404":
                fail(f"{reward_url} is not served (HTTP 404) after the inbox responded.")
            fail(f"{reward_url} {exc.reason}")
        ident = body.get("chat_id") or body.get("item_id")
        print(f"POST {reward_url} action=approve id={ident}")
        check_reward(status, reward_payload)
        return

    if auth_hits:
        print("FAIL: /learn/inbox is present and refused the call.")
        print("\n".join(auth_hits))
        print("Set TEACH_TOKEN to the agent admin token and rerun.")
        raise SystemExit(1)

    skip(tried)


if __name__ == "__main__":
    main()
