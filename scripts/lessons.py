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

RUBY = re.compile(r"\{([^|{}]+)\|([^|{}]*)(?:\|([^|{}]+)(?:\|([^|{}]*))?)?\}")  # {base|reading} or {base|reading|gloss|freq}
FREQS = {"1", "2", "3", "4"}  # how common the glossed word is: 4 everyday ... 1 rare
# a gloss that stops at the kanji while the word goes on in kana: {寂|さび|lonely}しい, {頼|たの|to ask}まれて
STEM_ONLY = re.compile(r"^(?:い(?![぀-ゟ])|いな|く[てな]|かっ|しい|しく|しかっ|しさ)")
PARTICLE = re.compile(r"^(?:を|が|は|に|の|も|と|や|へ|か[らな]|けど|って)")
KANJI = re.compile(r"[\u3400-\u9fff々]")
# Where tap-to-see glosses are not allowed (the word itself is being taught or quizzed there)
NO_GLOSS = re.compile(r"^(vocab|kanji_study|kanji\.|grammar\.(quiz\.options|pattern|form))")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REGISTERS = {"polite", "casual", "neutral", "dialect", "slang", "archaic"}
LEVELS = {"N5", "N4", "N3", "N2", "N1"}
KANA = re.compile(r"^[\u3040-\u30ff・ー（）()\s]+$")
HIRA = re.compile(r"^[\u3040-\u309fー（）()・\s]+$")
KATA = re.compile(r"^[\u30a0-\u30ff・\s]+$")
SRC = re.compile(r"^([pd])(\d+)$")
V2_FROM = "2026-11-12"   # lessons from this date on use the v2 rules below (who, listening, challenge types, stickers)
CHALLENGE_TYPES = ["pick", "order", "fix", "sticker"]   # rotate on most days; "write" on Tuesdays and Saturdays
WRITE_DAYS = {1, 5}                                     # Monday=0: Tuesday, Saturday
LISTENING_TYPES = ["voicemail", "announcement", "dictation", "ladder"]
STICKERS = ROOT / "stickers.json"
LATIN = re.compile(r"[A-Za-z]")


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

    if L.get("format") == "mock":
        need(L, ["topic", "title_jp", "context", "category"], "lesson")
        if L.get("category") != "mock":
            errs.append(f"{lid}: a mock lesson needs category 'mock'")
        check_mock(lid, L, errs)
        return
    if lid >= V2_FROM:
        check_v2(lid, L, errs)

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
    need(L.get("challenge"), ["prompt", "hint", "model_answer", "explanation"], "challenge")
    need(L.get("kanji"), ["breakdown"], "kanji")
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
        for m in RUBY.finditer(s):
            base, reading, gloss, freq = m.groups()
            if gloss and freq not in FREQS:
                errs.append(f"{lid}: gloss '{base}' in {path} needs a commonness level 1-4 at the end: {{{base}|{reading}|{gloss}|3}}")
            after = s[m.end():m.end() + 3]
            verb = gloss and gloss.startswith("to ") and re.match(r"[\u3040-\u309f]", after) and not PARTICLE.match(after)
            if gloss and KANJI.search(base[-1:]) and (verb or STEM_ONLY.match(after)):
                errs.append(f"{lid}: gloss '{base}' in {path} covers only part of the word; put the whole word in the block: "
                            f"{{{base}{s[m.end():m.end() + 2]}…|{reading}…|{gloss}|{freq}}}")
            if gloss and NO_GLOSS.match(path):
                errs.append(f"{lid}: no gloss allowed in {path} ('{base}')")
            if not reading:
                if not gloss:
                    errs.append(f"{lid}: empty reading for '{base}' in {path}")
                elif KANJI.search(base):
                    errs.append(f"{lid}: '{base}' in {path} has kanji, so it needs a reading")
            elif not re.search(r"[぀-ヿ]", reading):
                errs.append(f"{lid}: reading '{reading}' for '{base}' in {path} should be kana")
            if gloss and not gloss.strip():
                errs.append(f"{lid}: empty gloss for '{base}' in {path}")
    main = [str(x.get("jp", "")) for x in (L.get("phrases") or []) + (L.get("dialogue") or []) if isinstance(x, dict)]
    if sum(1 for t in main for m in RUBY.finditer(t) if m.group(3)) < 6:
        errs.append(f"{lid}: gloss the hard words in phrases and the main text ({{word|reading|meaning}}): fewer than 6 found")
    # every vocab word must be tappable (glossed) in the line it comes from
    for v in L.get("vocab") or []:
        if not isinstance(v, dict):
            continue
        line, sf = line_at(L, v.get("src")), str(v.get("surface", ""))
        if not line or not sf:
            continue
        glossed = [m.group(1) for m in RUBY.finditer(str(line.get("jp", ""))) if m.group(3)]
        if not any(b and (b in sf or sf in b) for b in glossed):
            errs.append(f"{lid}: vocab '{sf}' is not glossed in {v.get('src')} (add {{word|reading|meaning}} there)")


def people():
    C = load_cast()
    return {c["id"]: c for c in C.get("cast", []) + C.get("others", [])}


def sticker_ids():
    try:
        return {x["id"]: x for x in load_json(STICKERS)["stickers"]}
    except Exception:
        return {}


def check_v2(lid, L, errs):
    """Rules for lessons written from V2_FROM on: who speaks, stickers, voice messages, listening, challenge types."""
    P, S, fmt = people(), sticker_ids(), L.get("format")
    g = L.get("guest") or {}
    voices = 0
    for i, d in enumerate(L.get("dialogue") or []):
        if not isinstance(d, dict):
            continue
        where = f"dialogue[{i}]"
        if fmt == "text":
            continue
        who, sp = d.get("who"), str(d.get("speaker", ""))
        if who == "you" or d.get("me"):
            if who != "you" or not d.get("me"):
                errs.append(f"{lid}: {where}: the learner's lines need both \"me\": true and \"who\": \"you\"")
            if sp != "アルちゃん":
                errs.append(f"{lid}: {where}: the learner's speaker label is アルちゃん")
        elif who in P:
            if sp != P[who]["name"]:
                errs.append(f"{lid}: {where}: speaker must be {P[who]['name']} (cast.json name for '{who}')")
        elif who == "guest":
            if not g or sp != g.get("name"):
                errs.append(f"{lid}: {where}: a guest line needs the lesson's guest and speaker = guest.name")
        elif who == "extra":
            if d.get("voice") not in ("f", "m"):
                errs.append(f"{lid}: {where}: an 'extra' speaker (staff, shopkeeper) needs \"voice\": \"f\" or \"m\"")
        else:
            errs.append(f"{lid}: {where}: \"who\" must be a cast/others id from cast.json, \"you\", \"guest\" or \"extra\"")
        if LATIN.search(sp):
            errs.append(f"{lid}: {where}: speaker '{sp}' has romaji; use the Japanese name")
        if "スタンプ" in str(d.get("jp", "")):
            errs.append(f"{lid}: {where}: stickers are no longer written as text; use \"sticker\": \"<id>\" from stickers.json")
        if d.get("sticker") is not None:
            st = S.get(d["sticker"])
            if not st:
                errs.append(f"{lid}: {where}: sticker '{d['sticker']}' is not in stickers.json")
            elif plain(str(d.get("jp", ""))) != st["text"]:
                errs.append(f"{lid}: {where}: a sticker line's jp must be the sticker's text: {st['text']}")
        if d.get("kind") == "voice":
            voices += 1
            if fmt != "line":
                errs.append(f"{lid}: {where}: voice messages only exist in LINE chats")
    if voices > 1:
        errs.append(f"{lid}: at most one voice message per chat")
    X = L.get("listening")
    if not isinstance(X, dict) or X.get("type") not in LISTENING_TYPES:
        errs.append(f"{lid}: listening section missing (type one of {', '.join(LISTENING_TYPES)}; status says which)")
    else:
        lines = X.get("lines")
        if not isinstance(lines, list) or not 1 <= len(lines) <= 3 or not all(isinstance(x, dict) and x.get("jp") and x.get("en") and x.get("who") for x in lines):
            errs.append(f"{lid}: listening.lines needs 1-3 {{who, jp, en}} lines")
            lines = []
        for x in lines:
            if x.get("who") not in set(P) | {"you", "guest", "extra"}:
                errs.append(f"{lid}: listening line who '{x.get('who')}' is not a cast id, you, guest or extra")
            if x.get("who") == "extra" and x.get("voice") not in ("f", "m"):
                errs.append(f"{lid}: listening 'extra' line needs \"voice\": \"f\" or \"m\"")
        if X["type"] in ("voicemail", "announcement"):
            opts = X.get("options")
            if not X.get("question") or not isinstance(opts, list) or len(opts) != 4 or len(set(opts)) != 4 or not X.get("explain"):
                errs.append(f"{lid}: listening {X['type']} needs question, 4 different options (right one first) and explain")
        if X["type"] == "dictation" and sum(len(plain(x.get("jp", ""))) for x in lines) > 40:
            errs.append(f"{lid}: dictation must be short (40 characters at most)")
        if X["type"] == "ladder" and len(lines) != 1:
            errs.append(f"{lid}: a ladder listening has exactly one line")
    c = L.get("challenge") or {}
    t = c.get("type")
    if t not in CHALLENGE_TYPES + ["write"]:
        errs.append(f"{lid}: challenge.type must be one of pick, order, fix, sticker, write (status says which)")
    elif t == "pick":
        o = c.get("options")
        if not isinstance(o, list) or not 3 <= len(o) <= 4 or sum(1 for x in o if isinstance(x, dict) and x.get("ok") is True) != 1 or not all(isinstance(x, dict) and x.get("jp") and x.get("why") for x in o):
            errs.append(f"{lid}: challenge pick needs 3-4 options {{jp, ok, why}}, exactly one with ok: true")
    elif t == "order":
        pc = c.get("pieces")
        strip = lambda s: re.sub(r"[。！？!?、\s]", "", plain(s))
        if not isinstance(pc, list) or not 3 <= len(pc) <= 6 or len(set(map(plain, pc))) != len(pc):
            errs.append(f"{lid}: challenge order needs 3-6 different pieces, in the right order")
        elif strip("".join(pc)) != strip(c.get("model_answer", "")):
            errs.append(f"{lid}: challenge order pieces joined must equal the model answer (punctuation aside)")
    elif t == "fix":
        pt = c.get("parts")
        if not isinstance(pt, list) or not 3 <= len(pt) <= 6 or sum(1 for x in pt if isinstance(x, dict) and x.get("wrong")) != 1:
            errs.append(f"{lid}: challenge fix needs 3-6 parts {{jp}}, exactly one with wrong: true and a why")
        elif not next(x for x in pt if x.get("wrong")).get("why"):
            errs.append(f"{lid}: challenge fix: the wrong part needs a why")
    elif t == "sticker":
        st = c.get("stickers")
        if not isinstance(st, list) or not 3 <= len(st) <= 4 or len(set(st)) != len(st) or not all(x in S for x in st):
            errs.append(f"{lid}: challenge sticker needs 3-4 different ids from stickers.json, the right one first")
    if t == "write" and not c.get("hint"):
        errs.append(f"{lid}: a write challenge needs a hint")
    check_length(lid, L, errs)


# Length limits (from V2_FROM on): lessons must stay short and easy to read on a phone.
LINE_MAX = {"line": 40, "dialogue": 50, "story": 60, "text": 60}
SCENE_WORDS, NOTE_WORDS, GRAMMAR_WORDS = 30, 20, 50
FMT_LINE = {"line": "a LINE bubble", "dialogue": "a spoken line", "story": "a story line", "text": "a text part"}


def nwords(s):
    return len(plain(str(s or "")).split())


def check_length(lid, L, errs):
    fmt = L.get("format")
    cap = LINE_MAX.get(fmt)
    for i, d in enumerate(L.get("dialogue") or []):
        if cap and isinstance(d, dict) and not d.get("sticker"):
            n = len(plain(str(d.get("jp", ""))))
            if n > cap:
                errs.append(f"{lid}: dialogue[{i}] is {n} characters; {FMT_LINE[fmt]} has at most {cap}" + (" (split it into two bubbles)" if fmt == "line" else ""))
    sc = L.get("scene")
    if not isinstance(sc, str) or not sc.strip():
        errs.append(f"{lid}: scene missing: one English line (at most {SCENE_WORDS} words) shown on the start page")
    elif nwords(sc) > SCENE_WORDS:
        errs.append(f"{lid}: scene is {nwords(sc)} words; at most {SCENE_WORDS}")
    for i, v in enumerate(L.get("vocab") or []):
        if isinstance(v, dict) and nwords(v.get("note")) > NOTE_WORDS:
            errs.append(f"{lid}: vocab[{i}] note is {nwords(v.get('note'))} words; at most {NOTE_WORDS}")
    g = L.get("grammar") or {}
    if nwords(g.get("explanation")) > GRAMMAR_WORDS:
        errs.append(f"{lid}: grammar.explanation is {nwords(g.get('explanation'))} words; at most {GRAMMAR_WORDS}")
    k = L.get("keep")
    if k is not None:
        n = len(L.get("phrases") or [])
        if not isinstance(k, list) or not 1 <= len(k) <= 2 or not all(isinstance(x, str) and re.fullmatch(r"p\d", x) and int(x[1:]) < n for x in k):
            errs.append(f"{lid}: keep must be 1-2 phrase refs like [\"p2\"]")


def check_mock(lid, L, errs):
    M = L.get("mock") or {}
    Q = M.get("questions")
    if not isinstance(Q, list) or not 8 <= len(Q) <= 12:
        errs.append(f"{lid}: mock.questions needs 8-12 questions")
        return
    lines = (L.get("listening") or {}).get("lines") or []
    for i, q in enumerate(Q):
        w = f"mock.questions[{i}]"
        if not isinstance(q, dict) or not q.get("section"):
            errs.append(f"{lid}: {w} needs a section (漢字読み, 文脈規定, 言い換え, 文法 ★, 読解, 聴解)")
            continue
        if q.get("order"):
            o = q["order"]
            if not isinstance(o.get("pieces"), list) or len(o["pieces"]) != 4 or o.get("star") not in (0, 1, 2, 3):
                errs.append(f"{lid}: {w}.order needs 4 pieces in the right order and star 0-3")
            continue
        opts = q.get("options")
        if not q.get("prompt") or not isinstance(opts, list) or len(opts) != 4 or len(set(opts)) != 4 or not q.get("explain"):
            errs.append(f"{lid}: {w} needs prompt, 4 different options (right one first) and explain")
        if q.get("listen"):
            m = re.match(r"^l(\d+)$", str(q["listen"]))
            if not m or int(m.group(1)) >= len(lines):
                errs.append(f"{lid}: {w}.listen must point to a listening line (l0, l1…)")


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
    regular = [e for e in before if e.get("category") not in ("news", "review", "mock")]
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

    # --- v2: challenge type, listening type, monthly mock
    v2_before = [e for e in before if e["id"] >= V2_FROM and e.get("category") != "mock"]
    wd = dt.date.fromisoformat(today).weekday()
    ch_type = "write" if wd in WRITE_DAYS else CHALLENGE_TYPES[len(v2_before) % len(CHALLENGE_TYPES)]
    li_type = LISTENING_TYPES[len(v2_before) % len(LISTENING_TYPES)]
    d0 = dt.date.fromisoformat(today)
    first_sat = d0.weekday() == 5 and d0.day <= 7
    mock_month = any(e.get("category") == "mock" and e["id"][:7] == today[:7] for e in idx)
    mock_due = first_sat and not mock_month and not today_entry

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
    print(f"CHALLENGE type: {ch_type}" + (" (Tuesday/Saturday: free writing)" if ch_type == "write" else " (one tap; free writing is only on Tuesdays and Saturdays)"))
    print(f"LISTENING type: {li_type}")
    print("STICKERS (ids for \"sticker\" lines and sticker challenges): " + ", ".join(f"{k} {v['text']}" for k, v in sticker_ids().items()))
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
    regular_pick = f"field '{group[0]['id']}', function '{fns[0]['id']}', format '{fmt}', challenge '{ch_type}', listening '{li_type}'"
    if mock_due:
        print(f"DECISION: first Saturday of the month: write the MONTHLY MOCK for {today} (format 'mock', category 'mock'; see CLAUDE.md). No regular lesson or news today.")
    elif news_state == "DUE":
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
