"""Pull every call on the sparring agent from ElevenLabs and write data/calls.json.

Runs in GitHub Actions every morning. Needs the ELEVENLABS_API_KEY secret.
Uses only the Python standard library.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://api.eu.residency.elevenlabs.io/v1/convai"  # EU data residency
AGENT_ID = os.environ.get("AGENT_ID", "agent_3301m3rwayvvekn88jhbhh012zre")
MIN_SECONDS = 20  # skip greetings, hang-ups and connection tests
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "calls.json")

KEY = os.environ.get("ELEVENLABS_API_KEY")
if not KEY:
    sys.exit("ELEVENLABS_API_KEY is not set")


def get(path, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"xi-api-key": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def truthy(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("true", "yes", "1"):
        return True
    if s in ("false", "no", "0"):
        return False
    return None


def num(v):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return None


def flag(v):
    """1, 0 or None so the page can skip unknowns."""
    t = truthy(v)
    return None if t is None else (1 if t else 0)


def normalise(d):
    meta = d.get("metadata") or {}
    an = d.get("analysis") or {}
    crit = an.get("evaluation_criteria_results") or {}
    dc = {k: (v or {}).get("value") for k, v in (an.get("data_collection_results") or {}).items()}

    res, why = {}, {}
    for k, v in crit.items():
        r = (v or {}).get("result")
        if r in ("success", "failure"):
            res[k] = 1 if r == "success" else 0
            if r == "failure" and v.get("rationale"):
                why[k] = v["rationale"]

    start = meta.get("start_time_unix_secs") or 0
    return {
        "id": d.get("conversation_id"),
        "user_id": d.get("user_id") or meta.get("user_id") or "",
        "date": datetime.fromtimestamp(start, tz=timezone.utc).isoformat(),
        "dur": meta.get("call_duration_secs") or 0,
        "score": num(dc.get("score_0_100")),
        "outcome": (dc.get("call_outcome") or "unknown"),
        "persona": dc.get("persona_played") or "",
        "difficulty": (dc.get("difficulty") or "").lower(),
        "objections": num(dc.get("objection_count")) or 0,
        "talkHigh": truthy(dc.get("rep_talk_ratio_high")) is True,
        "lang": (meta.get("main_language") or d.get("main_language") or "").upper() or "",
        "res": res,
        "why": why,
        "spin": [flag(dc.get(k)) for k in ("situation_uncovered", "problem_uncovered", "implication_explored", "needpayoff_established")],
        "obj": [flag(dc.get(k)) for k in ("obj_listened", "obj_acknowledged", "obj_explored", "obj_responded_with_value")],
        "good": dc.get("one_thing_done_well") or "",
        "fix": dc.get("top_improvement_area") or "",
        "summary": an.get("transcript_summary") or "",
    }


def main():
    ids, cursor = [], None
    while True:
        params = {"agent_id": AGENT_ID, "page_size": 100}
        if cursor:
            params["cursor"] = cursor
        page = get("/conversations", params)
        for c in page.get("conversations", []):
            if (c.get("call_duration_secs") or 0) >= MIN_SECONDS:
                ids.append(c["conversation_id"])
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")

    calls = []
    for cid in ids:
        c = normalise(get(f"/conversations/{cid}"))
        if c["score"] is None:  # not analysed yet
            continue
        calls.append(c)
    calls.sort(key=lambda c: c["date"], reverse=True)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(), "agent_id": AGENT_ID, "calls": calls}, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(calls)} calls")


if __name__ == "__main__":
    main()
