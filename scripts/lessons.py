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
TRACK = ROOT / "curriculum" / "n3-kanji.json"
GRAMMAR = ROOT / "curriculum" / "grammar.json"
CAST = ROOT / "cast.json"
TZ = "Europe/Madrid"

NEWS_OPTIONAL_AFTER = 8   # days since last news: write one if there's a good story
NEWS_DUE_AFTER = 10       # days since last news: always write one
REVIEW_EVERY = 12         # lessons since last review before a review is allowed
PRACTICAL_EVERY = 3       # one regular lesson in three is on a practical field
GUEST_EVERY = 8           # lessons since the last guest before a new guest is due
FORMAT_CYCLE = ["dialogue", "line", "story", "dialogue", "text", "line"]

RUBY = re.compile(r"\{([^|{}]+)\|([^{}]+)\}")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REGISTERS = {"polite", "casual", "neutral", "dialect", "slang", "archaic"}
LEVELS = {"N5", "N4", "N3", "N2", "N1"}
KANA = re.compile(r"^[\u3040-\u30ff・ー（）()\s]+$")
HIRA = re.compile(r"^[\u3040-\u309fー（）()・\s]+$")
KATA = re.compile(r"^[\u30a0-\u30ff・\s]+$")
SRC = re.compile(r"^([pd])(\d+)$")


def load_topics():
    """-> (topics dict, set of every valid category id)."""
    T = load_json(TOPICS)
    ids = {f["id"] for f in T["fields"]} | {x["id"] for x in T["special"]} | {x["id"] for x in T.get("legacy", [])}
    return T, ids


def load_cast():
    try:
        return load_json(CAST)
    except Exception:
        return {"cast": [], "log": []}


def load_grammar():
    try:
        return load_json(GRAMMAR)["grammar"]
    except Exception:
        return []


def is_new(L):
    """Lessons written with the field x function x format system (Nov 2026 on)."""
    return isinstance(L, dict) and "format" in L


def plain(s):
    return RUBY.sub(lambda m: m.group(1), s)


def load_track():
    try:
        return load_json(TRACK)["kanji"]
    except Exception:
        return ""


def check_words(lid, L, track, errs):
    """vocab + kanji_study (the parts the app quizzes)."""
    vocab = L.get("vocab")
    if not isinstance(vocab, list) or not 8 <= len(vocab) <= 10:
        errs.append(f"{lid}: vocab needs 8-10 words")
        vocab = vocab if isinstance(vocab, list) else []
    seen = set()
    for i, v in enumerate(vocab):
        w = f"vocab[{i}]"
        if not isinstance(v, dict):
            errs.append(f"{lid}: {w} must be an object")
            continue
        for k in ("jp", "reading", "en", "level", "src", "surface"):
            if not isinstance(v.get(k), str) or not v[k].strip():
                errs.append(f"{lid}: {w}.{k} missing or empty")
        if v.get("level") not in LEVELS:
            errs.append(f"{lid}: {w}.level must be N5-N1")
        if isinstance(v.get("reading"), str) and not KANA.match(v["reading"]):
            errs.append(f"{lid}: {w}.reading must be kana")
        word = plain(str(v.get("jp", "")))
        if word in seen:
            errs.append(f"{lid}: {w} '{word}' is listed twice")
        seen.add(word)
        m = SRC.match(str(v.get("src", "")))
        lst = L.get("phrases" if m and m.group(1) == "p" else "dialogue") or []
        if not m or int(m.group(2)) >= len(lst):
            errs.append(f"{lid}: {w}.src must be p0-p4 or d0-dN pointing at a real line")
        elif str(v.get("surface", "")) not in plain(str(lst[int(m.group(2))].get("jp", ""))):
            errs.append(f"{lid}: {w}.surface '{v.get('surface')}' is not in sentence {v.get('src')}")
    ks = L.get("kanji_study")
    if not isinstance(ks, list) or len(ks) != 2:
        errs.append(f"{lid}: kanji_study needs exactly 2 kanji")
        return
    tracks = sorted(str(k.get("track")) for k in ks if isinstance(k, dict))
    if tracks != ["lesson", "n3"]:
        errs.append(f"{lid}: kanji_study needs one track 'lesson' and one track 'n3'")
    vocab_text = "".join(plain(str(v.get("jp", ""))) for v in vocab if isinstance(v, dict))
    for i, k in enumerate(ks):
        w = f"kanji_study[{i}]"
        if not isinstance(k, dict):
            errs.append(f"{lid}: {w} must be an object")
            continue
        kj = str(k.get("kanji", ""))
        if len(kj) != 1:
            errs.append(f"{lid}: {w}.kanji must be one character")
        if not str(k.get("meaning", "")).strip():
            errs.append(f"{lid}: {w}.meaning missing")
        on, kun = str(k.get("on", "")), str(k.get("kun", ""))
        if not on and not kun:
            errs.append(f"{lid}: {w} needs an on or kun reading")
        if on and not KATA.match(on):
            errs.append(f"{lid}: {w}.on must be katakana (join several with ・)")
        if kun and not HIRA.match(kun):
            errs.append(f"{lid}: {w}.kun must be hiragana (okurigana in brackets, several joined with ・)")
        if k.get("track") == "lesson" and kj not in vocab_text:
            errs.append(f"{lid}: {w} is track 'lesson' but {kj} is in none of today's vocab")
        if k.get("track") == "n3" and track and kj not in track:
            errs.append(f"{lid}: {w} is track 'n3' but {kj} is not in curriculum/n3-kanji.json")
        words = k.get("words")
        if not isinstance(words, list) or not 2 <= len(words) <= 3:
            errs.append(f"{lid}: {w}.words needs 2-3 example words")
            words = []
        for j, x in enumerate(words):
            if not isinstance(x, dict) or not all(isinstance(x.get(f), str) and x[f].strip() for f in ("jp", "reading", "en")):
                errs.append(f"{lid}: {w}.words[{j}] needs jp, reading, en")
                continue
            if kj not in plain(x["jp"]):
                errs.append(f"{lid}: {w}.words[{j}] does not contain {kj}")
            if not KANA.match(x["reading"]):
                errs.append(f"{lid}: {w}.words[{j}].reading must be kana")
        d = k.get("decoys") or {}
        for f, right in (("meanings", k.get("meaning")), ("readings", words[0].get("reading") if words and isinstance(words[0], dict) else None)):
            opts = d.get(f)
            if not isinstance(opts, list) or len(opts) != 3 or len(set(opts)) != 3 or right in opts:
                errs.append(f"{lid}: {w}.decoys.{f} needs 3 different wrong answers")


FORMATS = {}
FUNCTIONS = set()
FIELDS = set()
CAST_IDS = set()
GRAMMAR_IDS = set()


def init_refs():
    T, _ = load_topics()
    FORMATS.clear(); FORMATS.update({f["id"]: f for f in T["formats"]})
    FUNCTIONS.clear(); FUNCTIONS.update(f["id"] for f in T["functions"])
    FIELDS.clear(); FIELDS.update(f["id"] for f in T["fields"])
    CAST_IDS.clear(); CAST_IDS.update(c["id"] for c in load_cast().get("cast", []))
    GRAMMAR_IDS.clear(); GRAMMAR_IDS.update(g["id"] for g in load_grammar())


def line_at(L, ref):
    m = SRC.match(str(ref))
    if not m:
        return None
    lst = L.get("phrases" if m.group(1) == "p" else "dialogue") or []
    i = int(m.group(2))
    return lst[i] if i < len(lst) and isinstance(lst[i], dict) else None


def check_new(lid, L, errs):
    cat = L.get("category")
    if cat not in FIELDS | {"news", "review"}:
        errs.append(f"{lid}: category must be a field id from topics.json (or news/review), not '{cat}'")
    if L.get("function") not in FUNCTIONS:
        errs.append(f"{lid}: function must be one of topics.json functions")
    cast = L.get("cast")
    if not isinstance(cast, list):
        errs.append(f"{lid}: cast must be a list of character ids (can be empty only with a guest or on news)")
        cast = []
    for c in cast:
        if c not in CAST_IDS:
            errs.append(f"{lid}: cast '{c}' is not in cast.json")
    g = L.get("guest")
    if g is not None and (not isinstance(g, dict) or not all(isinstance(g.get(k), str) and g[k].strip() for k in ("name", "role"))):
        errs.append(f"{lid}: guest needs name and role")
    if not cast and not g and cat != "news":
        errs.append(f"{lid}: needs at least one cast member or a guest")
    G = L.get("grammar")
    if not isinstance(G, dict):
        errs.append(f"{lid}: grammar section missing")
        return
    for k in ("id", "pattern", "level", "meaning", "form", "explanation"):
        if not isinstance(G.get(k), str) or not G[k].strip():
            errs.append(f"{lid}: grammar.{k} missing or empty")
    if G.get("id") not in GRAMMAR_IDS:
        errs.append(f"{lid}: grammar.id '{G.get('id')}' is not in curriculum/grammar.json")
    src = G.get("src")
    if not isinstance(src, list) or not src:
        errs.append(f"{lid}: grammar.src must list the lines (p0.., d0..) that use the pattern")
    else:
        for r in src:
            if not line_at(L, r):
                errs.append(f"{lid}: grammar.src '{r}' is not a real line")
    ex = G.get("examples")
    if not isinstance(ex, list) or not 1 <= len(ex) <= 3 or not all(isinstance(x, dict) and x.get("jp") and x.get("en") for x in ex):
        errs.append(f"{lid}: grammar.examples needs 1-3 {{jp, en}} extra examples")
    q = G.get("quiz")
    if not isinstance(q, dict):
        errs.append(f"{lid}: grammar.quiz missing")
    else:
        if "＿＿" not in str(q.get("question", "")):
            errs.append(f"{lid}: grammar.quiz.question must contain ＿＿ where the answer goes")
        opts = q.get("options")
        if not isinstance(opts, list) or len(opts) != 4 or len(set(opts)) != 4:
            errs.append(f"{lid}: grammar.quiz.options needs 4 different options, the right one first")
        for k in ("en", "explain"):
            if not isinstance(q.get(k), str) or not q[k].strip():
                errs.append(f"{lid}: grammar.quiz.{k} missing")


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
    fmt = FORMATS.get(L.get("format"), FORMATS["dialogue"]) if is_new(L) else {"id": "dialogue", "lines": [4, 6], "me": True}
    if is_new(L) and L.get("format") not in FORMATS:
        errs.append(f"{lid}: format must be one of {', '.join(FORMATS)}")
    lo, hi = fmt["lines"]
    dl = L.get("dialogue")
    if not isinstance(dl, list) or not lo <= len(dl) <= hi:
        errs.append(f"{lid}: a {fmt['id']} needs {lo}-{hi} lines in 'dialogue'")
    else:
        for i, d in enumerate(dl):
            need(d, ["speaker", "jp", "en"], f"dialogue[{i}]")
        if fmt["me"] and not any(isinstance(d, dict) and d.get("me") is True for d in dl):
            errs.append(f"{lid}: no dialogue line has \"me\": true")
    if is_new(L):
        check_new(lid, L, errs)
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

    check_words(lid, L, load_track(), errs)

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
        _, topic_ids = load_topics()
        init_refs()
        cast_data = load_cast()
    except Exception as e:
        print(f"FAIL topics.json / cast.json: {e}")
        return 1
    log_dates = {e.get("date") for e in cast_data.get("log", []) if isinstance(e, dict)}
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
    taught_k, taught_v, taught_g, guests = {}, {}, {}, {}
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
        if is_new(L):
            for k in ("function", "format"):
                if L.get(k) != by_id[lid].get(k):
                    errs.append(f"{lid}: {k} differs between lesson file and index.json")
            if lid not in log_dates:
                errs.append(f"{lid}: add a story-so-far entry for this date to the log in cast.json")
            gid = (L.get("grammar") or {}).get("id") if isinstance(L.get("grammar"), dict) else None
            if gid and L.get("category") == "review":
                if gid not in taught_g:
                    errs.append(f"{lid}: a review lesson can only revisit grammar already taught ({gid} wasn't)")
            elif gid in taught_g:
                errs.append(f"{lid}: grammar {gid} was already taught on {taught_g[gid]}")
            elif gid:
                taught_g[gid] = lid
            gn = (L.get("guest") or {}).get("name") if isinstance(L.get("guest"), dict) else None
            if gn and gn in guests:
                errs.append(f"{lid}: guest {gn} already appeared on {guests[gn]}; invent a new one")
            elif gn:
                guests[gn] = lid
        for k in L.get("kanji_study") or []:
            kj = k.get("kanji") if isinstance(k, dict) else None
            if kj in taught_k:
                errs.append(f"{lid}: kanji {kj} was already taught on {taught_k[kj]}")
            elif kj:
                taught_k[kj] = lid
        for v in L.get("vocab") or []:
            word = plain(str(v.get("jp", ""))) if isinstance(v, dict) else None
            if word in taught_v:
                errs.append(f"{lid}: vocab '{word}' was already taught on {taught_v[word]}")
            elif word:
                taught_v[word] = lid
    if errs:
        print("FAIL\n- " + "\n- ".join(errs))
        return 1
    print(f"OK: {len(ids)} lessons, index valid.")
    return 0


def cmd_status(args):
    today = today_str(args.today)
    idx = load_json(INDEX)
    T, _ = load_topics()
    cast_data = load_cast()
    grammar = load_grammar()
    ids = [e["id"] for e in idx]
    past = [e for e in idx if e["id"] <= today]
    before = [e for e in idx if e["id"] < today]
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

    reviews = [i for i, e in enumerate(before) if e.get("category") == "review"]
    since_review = len(before) - (reviews[-1] + 1) if reviews else len(before)
    review_ok = since_review >= REVIEW_EVERY

    # --- field: one in three regular lessons is practical (legacy topics all count as practical)
    fields = T["fields"]
    practical_ids = {f["id"] for f in fields if f["practical"]} | {x["id"] for x in T.get("legacy", [])}
    regular = [e for e in before if e.get("category") not in ("news", "review")]
    recent = regular[-(PRACTICAL_EVERY - 1):]
    practical_due = len(recent) == PRACTICAL_EVERY - 1 and not any(e.get("category") in practical_ids for e in recent)
    last_field = {}
    for e in before:
        last_field[e.get("category")] = e["id"]
    order = {f["id"]: i for i, f in enumerate(fields)}
    group = [f for f in fields if f["practical"] == practical_due]
    group.sort(key=lambda f: (last_field.get(f["id"], ""), order[f["id"]]))

    # --- function and format
    last_fn = {}
    for e in before:
        if e.get("function"):
            last_fn[e["function"]] = e["id"]
    fns = sorted(T["functions"], key=lambda f: (last_fn.get(f["id"], ""), [x["id"] for x in T["functions"]].index(f["id"])))
    new_before = [e for e in before if e.get("format")]
    fmt = FORMAT_CYCLE[len(new_before) % len(FORMAT_CYCLE)]
    last_fmt = new_before[-1]["format"] if new_before else None
    if fmt == last_fmt:
        fmt = FORMAT_CYCLE[(len(new_before) + 1) % len(FORMAT_CYCLE)]

    # --- what's been taught
    track = load_track()
    taught_k, taught_v, taught_g, appear, guests = [], [], [], {}, []
    for e in before:
        try:
            L = load_json(LESSONS / f"{e['id']}.json")
        except Exception:
            continue
        taught_k += [k.get("kanji") for k in L.get("kanji_study") or [] if isinstance(k, dict)]
        taught_v += [plain(str(v.get("jp", ""))) for v in L.get("vocab") or [] if isinstance(v, dict)]
        G = L.get("grammar")
        if isinstance(G, dict) and G.get("id") and L.get("category") != "review":
            taught_g.append(G["id"])
        for c in L.get("cast") or []:
            appear[c] = e["id"]
        if isinstance(L.get("guest"), dict):
            guests.append((e["id"], L["guest"].get("name", "?")))
    new_count = len(new_before)
    last_guest_pos = max((i for i, e in enumerate(new_before) if e["id"] in {g[0] for g in guests}), default=-1)
    since_guest = new_count - (last_guest_pos + 1)
    guest_due = since_guest >= GUEST_EVERY - 1 or (not guests and new_count >= GUEST_EVERY - 1)

    print(f"Today: {today} ({dt.date.fromisoformat(today).strftime('%A')}; Sōta is only at the farm on weekends and school holidays)")
    print(f"Today's lesson: {'exists (' + today_entry['topic'] + ')' if today_entry else 'not written yet'}")
    print(f"Pre-written upcoming lessons: {len(upcoming)}" + (f" (last {upcoming[-1]['id']})" if upcoming else ""))
    print(f"Last news lesson: {news[-1] if news else 'none yet'} -> {days} days ago -> news {news_state}")
    print(f"Review allowed: {'yes' if review_ok else 'no'} ({since_review} lessons since last review)")
    print()
    print(f"FIELD: {'PRACTICAL day' if practical_due else 'wide day (not practical)'}. Least recently used: "
          + "; ".join(f"{f['id']} ({last_field.get(f['id'], 'never')}) angles: {' / '.join(f['angles'])}" for f in group[:3]))
    print("FUNCTION: least recently used: " + ", ".join(f"{f['id']} ({last_fn.get(f['id'], 'never')})" for f in fns[:3]))
    print(f"FORMAT: suggested {fmt} (yesterday: {last_fmt or 'none'}). Another is fine if it suits the field much better, but not {last_fmt or 'the same'} twice in a row.")
    nxt_g = [g for g in grammar if g["id"] not in taught_g]
    print(f"GRAMMAR track: {len(taught_g)}/{len(grammar)} taught. Next: "
          + (" | ".join(f"{g['id']} {g['pattern']} = {g['meaning']}" for g in nxt_g[:3]) if nxt_g else "track finished (pick any point as a review)")
          + (" (use the first; one of the other two only if the first really doesn't fit)" if len(nxt_g) > 1 else ""))
    nxt = [c for c in track if c not in taught_k]
    print(f"N3 kanji track: {len(track) - len(nxt)}/{len(track)} taught. Next n3 kanji: {nxt[0] if nxt else 'track finished'}"
          + (f" (then {''.join(nxt[1:6])})" if len(nxt) > 1 else ""))
    print()
    print("CAST last appearances: " + ", ".join(f"{c['id']} ({appear.get(c['id'], 'not met yet')})" for c in cast_data.get("cast", [])))
    print(f"GUEST: {'DUE: bring a new one-off guest today' if guest_due else 'not today'} ({since_guest} lessons since the last guest)."
          + (f" Used guest names (never reuse): {', '.join(g[1] for g in guests)}" if guests else ""))
    log = [e for e in cast_data.get("log", []) if e.get("date", "") < today]
    print("STORY SO FAR (last 8):")
    for e in log[-8:]:
        print(f"  {e['date']} [{', '.join(e.get('cast') or []) or '-'}] {e.get('summary', '')}")
    facts = [f for e in log for f in e.get("new_facts") or []]
    if facts:
        print("CANON from earlier lessons: " + " | ".join(facts))
    print()
    print("Kanji already taught (never teach again): " + ("".join(taught_k) or "none"))
    print(f"Vocab already taught ({len(taught_v)}, never list again): " + ("、".join(taught_v) or "none"))
    print()
    regular_pick = f"field '{group[0]['id']}', function '{fns[0]['id']}', format '{fmt}'"
    if news_state == "DUE":
        if today_entry:
            print(f"DECISION: write a NEWS lesson for {today}. First run: python3 scripts/lessons.py bump {today}")
        else:
            print(f"DECISION: write a NEWS lesson for {today} (function '{fns[0]['id']}', format '{fmt}').")
    elif today_entry:
        print("DECISION: today's lesson already exists. Write nothing; just report its topic.")
    elif news_state == "OPTIONAL":
        print(f"DECISION: write a NEWS lesson if you find a good story from the last 10 days; otherwise a regular lesson: {regular_pick}.")
    elif review_ok:
        print(f"DECISION: write a REVIEW lesson (category 'review', revisit grammar already taught), function '{fns[0]['id']}', format '{fmt}'.")
    else:
        print(f"DECISION: write a regular lesson: {regular_pick}." + (" With a new guest." if guest_due else ""))
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
