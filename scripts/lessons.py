#!/usr/bin/env python3
"""Nihongo Line lesson helper.

  python3 scripts/lessons.py status          what today's run should do
  python3 scripts/lessons.py check           validate every lesson + index (run before every push)
  python3 scripts/lessons.py bump DATE       move the lesson at DATE to the first free day after the last lesson

Add --today YYYY-MM-DD to any command to pretend it's another day.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "lessons"
INDEX = LESSONS / "index.json"
TOPICS = ROOT / "topics.json"
TZ = "Europe/Madrid"

NEWS_OPTIONAL_AFTER = 8   # days since last news: write one if there's a good story
NEWS_DUE_AFTER = 10       # days since last news: always write one
REVIEW_EVERY = 12         # lessons since last review before a review is allowed

RUBY = re.compile(r"\{([^|{}]+)\|([^{}]+)\}")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REGISTERS = {"polite", "casual", "neutral"}


def today_str(override):
    if override:
        dt.date.fromisoformat(override)
        return override
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(TZ)).date().isoformat()
    except Exception:
        # Fallback: Madrid is UTC+1 in winter, UTC+2 in summer; +1 is close enough to pick the date.
        return (dt.datetime.utcnow() + dt.timedelta(hours=1)).date().isoformat()


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def strings(o, path=""):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f"{path}[{i}]")


def check_lesson(lid, L, topic_ids, errs):
    def need(obj, keys, where):
        for k in keys:
            if not isinstance(obj, dict) or not isinstance(obj.get(k), str) or not obj[k].strip():
                errs.append(f"{lid}: {where}.{k} missing or empty")

    need(L, ["topic", "title_jp", "context", "dialogue_setting", "category"], "lesson")
    if L.get("category") not in topic_ids:
        errs.append(f"{lid}: category '{L.get('category')}' is not in topics.json")
    ph = L.get("phrases")
    if not isinstance(ph, list) or len(ph) != 5:
        errs.append(f"{lid}: needs exactly 5 phrases")
    else:
        for i, p in enumerate(ph):
            need(p, ["jp", "en", "register"], f"phrases[{i}]")
            if isinstance(p, dict) and p.get("register") not in REGISTERS:
                errs.append(f"{lid}: phrases[{i}].register must be polite, casual or neutral")
    dl = L.get("dialogue")
    if not isinstance(dl, list) or not 4 <= len(dl) <= 6:
        errs.append(f"{lid}: dialogue needs 4-6 lines")
    else:
        for i, d in enumerate(dl):
            need(d, ["speaker", "jp", "en"], f"dialogue[{i}]")
        if not any(isinstance(d, dict) and d.get("me") is True for d in dl):
            errs.append(f"{lid}: no dialogue line has \"me\": true")
    need(L.get("kanji"), ["kanji", "reading", "romaji", "meaning", "where"], "kanji")
    need(L.get("tip"), ["mark", "title", "body"], "tip")
    need(L.get("challenge"), ["prompt", "hint", "model_answer"], "challenge")
    if L.get("news"):
        if L.get("category") != "news":
            errs.append(f"{lid}: news lessons need category 'news'")
        if not str(L.get("topic", "")).startswith("News:"):
            errs.append(f"{lid}: news topic must start with 'News:'")
    elif L.get("category") == "news":
        errs.append(f"{lid}: category 'news' needs \"news\": true")

    for path, s in strings(L):
        if path in ("kanji.kanji", "kanji.reading"):
            if re.search(r"[{}|]", s):
                errs.append(f"{lid}: {path} must not contain furigana markup")
            continue
        rest = RUBY.sub("", s)
        if re.search(r"[{}|]", rest):
            errs.append(f"{lid}: broken furigana markup in {path}: {s[:60]}")
        for base, reading in RUBY.findall(s):
            if not re.search(r"[぀-ヿ]", reading):
                errs.append(f"{lid}: reading '{reading}' for '{base}' in {path} should be kana")


def cmd_check(args):
    errs = []
    try:
        topics = load_json(TOPICS)
        topic_ids = {t["id"] for t in topics}
    except Exception as e:
        print(f"FAIL topics.json: {e}")
        return 1
    try:
        idx = load_json(INDEX)
    except Exception as e:
        print(f"FAIL lessons/index.json is not valid JSON: {e}")
        return 1
    if not isinstance(idx, list):
        print("FAIL lessons/index.json must be a list")
        return 1
    ids = []
    for i, e in enumerate(idx):
        if not isinstance(e, dict) or not DATE.match(str(e.get("id", ""))):
            errs.append(f"index[{i}]: bad id")
            continue
        try:
            dt.date.fromisoformat(e["id"])
        except ValueError:
            errs.append(f"index[{i}]: {e['id']} is not a real date")
        if not e.get("topic"):
            errs.append(f"index {e['id']}: missing topic")
        if e.get("category") not in topic_ids:
            errs.append(f"index {e['id']}: category '{e.get('category')}' is not in topics.json")
        ids.append(e["id"])
    if ids != sorted(set(ids)):
        errs.append("index.json must be sorted by id with no duplicates")
    files = {p.stem for p in LESSONS.glob("*.json") if p.name != "index.json"}
    for lid in sorted(set(ids) - files):
        errs.append(f"index lists {lid} but lessons/{lid}.json is missing")
    for lid in sorted(files - set(ids)):
        errs.append(f"lessons/{lid}.json exists but is not in index.json")
    by_id = {e["id"]: e for e in idx if isinstance(e, dict) and "id" in e}
    for lid in sorted(files & set(ids)):
        try:
            L = load_json(LESSONS / f"{lid}.json")
        except Exception as e:
            errs.append(f"{lid}: invalid JSON ({e})")
            continue
        check_lesson(lid, L, topic_ids, errs)
        if L.get("topic") != by_id[lid].get("topic"):
            errs.append(f"{lid}: topic differs between lesson file and index.json")
        if L.get("category") != by_id[lid].get("category"):
            errs.append(f"{lid}: category differs between lesson file and index.json")
    if errs:
        print("FAIL\n- " + "\n- ".join(errs))
        return 1
    print(f"OK: {len(ids)} lessons, index valid.")
    return 0


def cmd_status(args):
    today = today_str(args.today)
    idx = load_json(INDEX)
    topics = load_json(TOPICS)
    ids = [e["id"] for e in idx]
    past = [e for e in idx if e["id"] <= today]
    today_entry = next((e for e in idx if e["id"] == today), None)
    upcoming = [e for e in idx if e["id"] > today]

    news = [e["id"] for e in past if e.get("category") == "news"]
    since_ref = news[-1] if news else (ids[0] if ids else today)
    days = (dt.date.fromisoformat(today) - dt.date.fromisoformat(since_ref)).days
    if today_entry and today_entry.get("category") == "news":
        news_state = "DONE"
    elif days >= NEWS_DUE_AFTER:
        news_state = "DUE"
    elif days >= NEWS_OPTIONAL_AFTER:
        news_state = "OPTIONAL"
    else:
        news_state = "NOT YET"

    reviews = [i for i, e in enumerate(past) if e.get("category") == "review"]
    since_review = len(past) - (reviews[-1] + 1) if reviews else len(past)
    review_ok = since_review >= REVIEW_EVERY

    last_used = {}
    for e in idx:
        last_used[e.get("category")] = e["id"]
    pool = [t for t in topics if t["id"] not in ("news", "review")]
    if review_ok:
        pool = [t for t in topics if t["id"] == "review"] + pool
    order = {t["id"]: i for i, t in enumerate(topics)}
    pool.sort(key=lambda t: (t["id"] != "review", last_used.get(t["id"], ""), order[t["id"]]))

    print(f"Today: {today}")
    print(f"Today's lesson: {'exists (' + today_entry['topic'] + ')' if today_entry else 'not written yet'}")
    print(f"Pre-written upcoming lessons: {len(upcoming)}" + (f" (last {upcoming[-1]['id']})" if upcoming else ""))
    print(f"Last news lesson: {news[-1] if news else 'none yet'} -> {days} days ago -> news {news_state}")
    print(f"Review allowed: {'yes' if review_ok else 'no'} ({since_review} lessons since last review)")
    print("Least recently used topics: " + ", ".join(
        f"{t['id']} ({last_used.get(t['id'], 'never')})" for t in pool[:6]))
    print()
    if news_state == "DUE":
        if today_entry:
            print(f"DECISION: write a NEWS lesson for {today}. First run: python3 scripts/lessons.py bump {today}")
        else:
            print(f"DECISION: write a NEWS lesson for {today}.")
    elif today_entry:
        print("DECISION: today's lesson already exists. Write nothing; just report its topic.")
    elif news_state == "OPTIONAL":
        print(f"DECISION: write a NEWS lesson if you find a good story from the last 10 days; "
              f"otherwise a regular lesson on '{pool[0]['id']}'.")
    else:
        print(f"DECISION: write a regular lesson on '{pool[0]['id']}' ({pool[0]['name']}).")
    return 0


def cmd_bump(args):
    idx = load_json(INDEX)
    src = args.date
    entry = next((e for e in idx if e["id"] == src), None)
    if not entry:
        print(f"No lesson at {src}")
        return 1
    taken = {e["id"] for e in idx}
    d = dt.date.fromisoformat(max(taken)) + dt.timedelta(days=1)
    while d.isoformat() in taken:
        d += dt.timedelta(days=1)
    dst = d.isoformat()
    (LESSONS / f"{src}.json").rename(LESSONS / f"{dst}.json")
    entry["id"] = dst
    idx.sort(key=lambda e: e["id"])
    save_json(INDEX, idx)
    print(f"Moved {src} ({entry['topic']}) -> {dst}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--today", help="pretend today is YYYY-MM-DD")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("check")
    b = sub.add_parser("bump")
    b.add_argument("date")
    args = ap.parse_args()
    return {"status": cmd_status, "check": cmd_check, "bump": cmd_bump}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
