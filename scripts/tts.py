#!/usr/bin/env python3
"""Make the lesson audio (Gemini 3.8 Flash-Lite TTS, VOICEVOX for 颯太).

For each lesson, everything the app can play is voiced and saved under audio/<lesson>/<hash>.mp3:
  - every main-text line, phrase, grammar example, extra and the sign kanji (as before)
  - the review bank: each vocab word, each kanji-study word, the challenge's model answer,
    the grammar quiz with its gap filled ("w:<word>", "quiz")
  - slow versions: the 5 phrases read slowly by the AI; everything else slowed for free with ffmpeg
    (a little slower plus a pause at each comma) under "slow:<key>"
  - a radio track (dialogue, phrases with a gap to repeat, dialogue again) under "_radio"
audio/<lesson>.json maps keys to files. Keys: the line id ("d3", "p1"), the plain text (older app
versions), "w:<word>", "slow:<key>", "_radio" and "_radio_tl" (timeline).

Files are named by voice + text, so unchanged lines are never remade. When a voice only changes
model (Flash -> Lite), the old file is kept. Newest lessons go first; older lessons are back-filled
up to BACKFILL clips per run, so the daily limit stays free for today's lesson.

  python3 scripts/tts.py               # all lessons (today's first)
  python3 scripts/tts.py 2026-11-05    # just these
Env: GEMINI_API_KEY, GOOGLE_TTS_KEY (Chirp fallback), BACKFILL (default 0), VOICEVOX_URL.
"""
import base64, datetime as dt, glob, hashlib, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

KEY = os.environ.get("GOOGLE_TTS_KEY", "").strip()
GKEY = os.environ.get("GEMINI_API_KEY", "").strip()
API = "https://texttospeech.googleapis.com/v1/text:synthesize"
GAPI = "https://generativelanguage.googleapis.com/v1beta/models"
VV = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
BACKFILL = int(os.environ.get("BACKFILL", "0") or 0)
MARK = re.compile(r"\{([^|{}]+)\|([^|{}]*)(?:\|([^|{}]+)(?:\|([1-4]))?)?\}")  # same as index.html
VOICES = json.load(open("voices.json", encoding="utf-8"))
CASTJ = json.load(open("cast.json", encoding="utf-8"))
PEOPLE = {c["id"]: c for c in CASTJ["cast"] + CASTJ.get("others", [])}
BY_NAME = {}
for c in PEOPLE.values():
    for n in [c["name"], *c.get("aliases", [])]:
        BY_NAME[n] = c
LEDGER = "audio/_ledger.json"
MONTH = dt.date.today().strftime("%Y-%m")
LEGACY_MODEL = "gemini-3.8-flash-tts"
RADIO_DAYS = 14


def plain(s):
    """What the app uses as the key: furigana markup removed."""
    return MARK.sub(r"\1", str(s or ""))


def names(lesson):
    out = {}
    for c in list(PEOPLE.values()) + ([lesson["guest"]] if lesson.get("guest") else []):
        for m in MARK.finditer(c.get("name_jp", "")):
            if m.group(2):
                out[m.group(1)] = m.group(2)
    return out


def spoken(text, lesson, override=None):
    """The text sent to the engine: proper nouns as kana, chat noise removed."""
    if override:
        return override
    nm = names(lesson)

    def sub(m):
        base, reading = m.group(1), m.group(2)
        is_name = reading and ("鷹ノ原" in base or base in nm or any(len(base) >= 2 and base in b for b in nm))
        return reading if is_name else base

    s = MARK.sub(sub, str(text))
    s = re.sub(r"[（(]スタンプ[：:][^）)]*[）)]", "", s)      # LINE stickers written as text
    s = re.sub(r"(?<=[^A-Za-z0-9])[ｗw]+(?=[\s。、！？!?]|$)", "", s)  # ｗｗ = lol
    s = re.sub(r"[\U0001F000-\U0001FAFF☀-➿]", "", s)  # emoji
    return re.sub(r"\s+", " ", s).strip()


# ---------- money: a ledger of what Gemini cost this month ----------
_ledger = json.load(open(LEDGER, encoding="utf-8")) if os.path.exists(LEDGER) else {}


def spent():
    return _ledger.get(MONTH, {}).get("usd", 0.0)


def over_cap():
    return spent() >= float(VOICES.get("monthly_cap_usd", 3))


def charge(model, usage):
    year = "2026" if dt.date.today() < dt.date(2027, 1, 1) else "2027"
    p = VOICES.get("prices", {}).get(model, {}).get(year, [1, 18])
    usd = (usage.get("promptTokenCount", 0) * p[0] + usage.get("candidatesTokenCount", 0) * p[1]) / 1e6
    m = _ledger.setdefault(MONTH, {"usd": 0.0, "clips": 0, "seconds": 0.0})
    m["usd"] = round(m["usd"] + usd, 5)
    m["clips"] += 1
    m["seconds"] = round(m["seconds"] + usage.get("candidatesTokenCount", 0) / 25, 1)


def save_ledger():
    os.makedirs("audio", exist_ok=True)
    json.dump(_ledger, open(LEDGER, "w", encoding="utf-8"), indent=1, sort_keys=True)


# ---------- engines ----------
class Later(Exception):
    """Gemini daily limit / cap: keep the old audio for this line and try again next run."""


_gemini_off = []


def to_mp3(raw, pcm):
    return subprocess.run(["ffmpeg", "-loglevel", "error"] + (["-f", "s16le", "-ar", "24000", "-ac", "1"] if pcm else [])
                          + ["-i", "-", "-f", "mp3", "-b:a", "64k", "-"], input=raw, capture_output=True, check=True).stdout


def gemini(text, v):
    if _gemini_off or not GKEY:
        raise Later("gemini unavailable")
    if over_cap():
        raise Later("monthly cap")
    part = {"text": text}
    if v.get("style"):
        part["speech_metadata"] = {"style": v["style"]}
    body = {"contents": [{"role": "user", "parts": [part]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"voice": v["voice"]}}}}
    req = urllib.request.Request(f"{GAPI}/{v['model']}:generateContent", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "x-goog-api-key": GKEY})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            p = d["candidates"][0]["content"]["parts"][0]["inlineData"]
            charge(v["model"], d.get("usageMetadata", {}))
            return to_mp3(base64.b64decode(p["data"]), "wav" not in p.get("mimeType", "wav").lower())
        except urllib.error.HTTPError as e:
            txt = e.read().decode()
            if e.code == 402 or (e.code == 429 and ("per_day" in txt or "PerDay" in txt or "limit: 0" in txt)):
                _gemini_off.append(1)
                print(f"Gemini stopped for today ({e.code}): {txt[:200]}")
                raise Later(txt[:100])
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(2 ** attempt * 5)
                continue
            print(f"Gemini TTS error {e.code} for {v['voice']}: {txt[:300]}")
            raise Later(txt[:100])
        except (KeyError, IndexError):
            if attempt < 3:
                time.sleep(3)
                continue
            raise Later("empty answer")


_VV_IDS = {}


def voicevox(text, v):
    if not _VV_IDS:
        with urllib.request.urlopen(VV + "/speakers", timeout=60) as r:
            for sp in json.load(r):
                for st in sp["styles"]:
                    _VV_IDS[(sp["name"], st["name"])] = st["id"]
    sid = _VV_IDS.get((v["speaker"], v.get("style", "ノーマル")))
    if sid is None:
        raise SystemExit(f"VOICEVOX voice not found: {v['speaker']} / {v.get('style')}")
    post = lambda url, data: urllib.request.urlopen(urllib.request.Request(
        url, data, {"Content-Type": "application/json"}, method="POST"), timeout=300).read()
    q = json.loads(post(f"{VV}/audio_query?text={urllib.parse.quote(text)}&speaker={sid}", b""))
    q["speedScale"] = v.get("rate", 1.0)
    wav = post(f"{VV}/synthesis?speaker={sid}", json.dumps(q).encode())
    return to_mp3(wav, False)


def chirp(text, name):
    if not KEY:
        raise Later("no Google TTS key")
    body = {"input": {"text": text}, "voice": {"languageCode": "ja-JP", "name": f"ja-JP-Chirp3-HD-{name}"},
            "audioConfig": {"audioEncoding": "MP3"}}
    req = urllib.request.Request(f"{API}?key={KEY}", json.dumps(body).encode(), {"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(2 ** attempt * 4)
                continue
            raise Later(f"Chirp {e.code}")


def spec(v):
    return v if isinstance(v, dict) else {"voice": v}


def synth(text, voice):
    v = spec(voice)
    if v.get("engine") == "voicevox":
        try:
            return voicevox(text, v)
        except (urllib.error.URLError, OSError) as e:
            raise Later(f"VOICEVOX not running: {e}")
    if v.get("engine") == "gemini":
        return gemini(text, v)
    return chirp(text, v["voice"])


def tag(voice, model=None):
    v = spec(voice)
    if v.get("engine") == "voicevox":
        return f"voicevox|{v['speaker']}|{v.get('style', '')}|{v.get('rate', 1.0)}"
    if v.get("engine") == "gemini":
        return f"gemini|{model or v['model']}|{v['voice']}|{v.get('style', '')}"
    return f"Chirp3-HD|{v['voice']}" + (f"|{v['rate']}" if v.get("rate") else "")


def fname(voice, text, model=None):
    return hashlib.sha1(f"{tag(voice, model)}|{text}".encode()).hexdigest()[:12] + ".mp3"


# ---------- who speaks ----------
def pick(pool, name):
    return pool[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(pool)]


def library_voice(gender, age, name):
    """A Gemini library voice for a guest or staff: same gender, closest age, picked by name among the 3 closest."""
    pool = [p for p in VOICES.get("guest_pool", []) if p["g"] == gender] or VOICES.get("guest_pool", [])
    if not pool:
        return VOICES["narrator"]
    near = sorted(pool, key=lambda p: (abs(p["age"] - age), p["id"]))[:3]
    p = pick(near, name or "guest")
    return {"engine": "gemini", "voice": p["id"], "model": VOICES.get("guest_model", "gemini-3.8-flash-lite-tts"),
            "style": "natural, conversational"}


def cast_voice(cid):
    return VOICES["cast"].get(cid) or VOICES.get("others", {}).get(cid)


def voice_for(line, lesson):
    who, sp = line.get("who"), line.get("speaker", "")
    if line.get("me") or who == "you" or sp == "You":
        return VOICES["you"]
    if lesson.get("format") == "text":
        r = lesson.get("reader")
        r = (BY_NAME.get(r) or PEOPLE.get(r) or {}).get("id", r)
        return cast_voice(r) or VOICES["narrator"]
    if who and who != "guest" and cast_voice(who):
        return cast_voice(who)
    c = BY_NAME.get(sp)
    if c and cast_voice(c["id"]):
        return cast_voice(c["id"])
    g = lesson.get("guest") or {}
    if who == "guest" or (g.get("name") and g.get("name") == sp):
        return library_voice(g.get("voice") or line.get("voice") or "f", int(g.get("age") or 40), g.get("name", sp))
    if line.get("voice") in ("f", "m"):
        return library_voice(line["voice"], int(line.get("age") or 35), sp)
    return VOICES["narrator"]


def items(lesson):
    """(keys, spoken text, voice, slow kind) for everything the app can play. slow: 'ai', 'smart' or None."""
    out, seen = [], set()

    def add(keys, jp, voice, override=None, slow="smart", text=None):
        keys = [k for k in keys if k]
        k0 = keys[0]
        if k0 in seen:
            return
        seen.update(keys)
        out.append((keys, text or spoken(jp, lesson, override), voice, slow))

    for i, d in enumerate(lesson.get("dialogue", [])):
        add([f"d{i}", plain(d["jp"])], d["jp"], voice_for(d, lesson), d.get("tts"))
    for i, p in enumerate(lesson.get("phrases", [])):
        add([f"p{i}", plain(p["jp"])], p["jp"], VOICES["you"], p.get("tts"), slow="ai")
    for x in (lesson.get("grammar") or {}).get("examples", []):
        add([plain(x["jp"])], x["jp"], VOICES["narrator"], x.get("tts"))
    for ex in lesson.get("extras", []):
        for it in ex.get("items", []):
            add([plain(it["jp"])], it["jp"], VOICES["narrator"], it.get("tts"))
    k = lesson.get("kanji") or {}
    if k.get("reading"):
        add([k["reading"]], k["reading"], VOICES["narrator"], slow=None)
    # review bank
    for v in lesson.get("vocab", []):
        if v.get("reading"):
            add(["w:" + plain(v["jp"])], v["reading"], VOICES["narrator"], text=v["reading"])
    for ks in lesson.get("kanji_study", []):
        for w in ks.get("words", []):
            if w.get("reading"):
                add(["w:" + plain(w["jp"])], w["reading"], VOICES["narrator"], text=w["reading"])
    ch = lesson.get("challenge") or {}
    if ch.get("model_answer"):
        add(["model", plain(ch["model_answer"])], ch["model_answer"], VOICES["you"])
    q = (lesson.get("grammar") or {}).get("quiz") or {}
    if q.get("question") and q.get("options"):
        add(["quiz"], q["question"].replace("＿＿", q["options"][0]), VOICES["narrator"])
    for i, li in enumerate((lesson.get("listening") or {}).get("lines", []) if isinstance(lesson.get("listening"), dict) else []):
        add([f"l{i}", plain(li["jp"])], li["jp"], voice_for(li, lesson))
    return out


# ---------- free slow versions and the radio track ----------
def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def smart_slow(src, dst):
    """88% speed (pitch kept) and an extra pause at each comma-length silence inside the line."""
    d = dur(src)
    det = subprocess.run(["ffmpeg", "-i", src, "-af", "silencedetect=noise=-30dB:d=0.08", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", det)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", det)]
    cuts = [round((a + b) / 2, 3) for a, b in zip(st, en) if 0.25 < a and b < d - 0.25]
    stretch = "rubberband=tempo=0.88:formant=preserved:pitchq=quality:window=long" if d > 1.2 else "rubberband=tempo=0.8:formant=preserved:pitchq=quality"
    edges = [0] + cuts + [d]
    parts, chains = [], []
    for i in range(len(edges) - 1):
        chains.append(f"[0:a]atrim={edges[i]}:{edges[i + 1]},asetpts=PTS-STARTPTS,aresample=24000,{stretch}[a{i}]")
        parts.append(f"[a{i}]")
        if i < len(edges) - 2:
            chains.append(f"anullsrc=r=24000:cl=mono,atrim=0:0.4[s{i}]")
            parts.append(f"[s{i}]")
    fc = ";".join(chains) + ";" + "".join(parts) + f"concat=n={len(parts)}:v=0:a=1"
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-filter_complex", fc, "-ac", "1", "-b:a", "48k", dst],
                       capture_output=True)
    if r.returncode:  # no rubberband in this ffmpeg: plain atempo
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af", "atempo=0.85", "-b:a", "48k", dst], check=True)


def radio(lesson, mp, folder):
    """Dialogue, the 5 phrases with a gap to repeat each, dialogue again. Built from existing clips only."""
    tmp = folder + "/_radio"
    os.makedirs(tmp, exist_ok=True)
    segs, tl, t = [], [], 0.0

    def wav(src):
        out = f"{tmp}/{os.path.basename(src)}.wav"
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-ar", "24000", "-ac", "1", out], check=True)
        return out

    def sil(sec):
        out = f"{tmp}/sil{int(sec * 100)}.wav"
        if not os.path.exists(out):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{sec:.2f}", out], check=True)
        return out

    chime = f"{tmp}/chime.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=f=880:d=0.18", "-f", "lavfi", "-i", "sine=f=1318:d=0.35",
                    "-filter_complex", "[0][1]concat=n=2:v=0:a=1,afade=t=out:st=0.3:d=0.23,volume=0.25,aresample=24000", "-ac", "1", chime], check=True)

    def add(f, label=None):
        nonlocal t
        if label:
            tl.append([round(t, 2), label])
        segs.append(f)
        t += dur(f)

    def section(label, keys, gap, repeat=False):
        add(chime, label)
        add(sil(0.5))
        for k, who, line in keys:
            p = mp.get(k)
            if not p or not os.path.exists(p):
                continue
            w = wav(p)
            add(w, f"{who}|{line}")
            add(sil(dur(w) + 1.0 if repeat else gap))

    dl = [(f"d{i}", d.get("speaker", ""), plain(d["jp"])) for i, d in enumerate(lesson.get("dialogue", []))]
    ph = [(f"p{i}", "フレーズ", plain(p["jp"])) for i, p in enumerate(lesson.get("phrases", []))]
    if not any(mp.get(k) for k, _, _ in dl):
        return None
    section("会話", dl, 0.7)
    section("フレーズ · repeat after each one", ph, 0, repeat=True)
    section("もう一度", dl, 0.5)
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    out = f"{folder}/radio.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-ac", "1", "-ar", "22050", "-b:a", "32k", out], check=True)
    subprocess.run(["rm", "-rf", tmp])
    return out, tl


# ---------- build one lesson ----------
budget = {"left": None}


def build(lid, backfill):
    lesson = json.load(open(f"lessons/{lid}.json", encoding="utf-8"))
    folder = f"audio/{lid}"
    os.makedirs(folder, exist_ok=True)
    old = json.load(open(f"audio/{lid}.json", encoding="utf-8")) if os.path.exists(f"audio/{lid}.json") else {}
    mp, made, later = {}, 0, 0
    for keys, text, voice, slow in items(lesson):
        path = f"{folder}/{fname(voice, text)}"
        legacy = f"{folder}/{fname(voice, text, LEGACY_MODEL)}" if spec(voice).get("engine") == "gemini" else None
        if not os.path.exists(path) and legacy and os.path.exists(legacy):
            path = legacy  # same voice, made with Flash: keep it
        if not os.path.exists(path):
            if backfill and budget["left"] is not None and budget["left"] <= 0:
                later += 1
                prev = next((old[k] for k in keys if isinstance(old.get(k), str) and os.path.exists(old[k])), None)
                if prev:
                    for k in keys:
                        mp[k] = prev
                continue
            try:
                audio = synth(text, voice)
            except Later:
                later += 1
                prev = next((old[k] for k in keys if isinstance(old.get(k), str) and os.path.exists(old[k])), None)
                if prev and spec(voice).get("engine") == "gemini" and over_cap():
                    pass
                if not prev and over_cap() and spec(voice).get("engine") == "gemini":
                    try:  # past the monthly cap: free Chirp voice, never the robot
                        audio = chirp(text, VOICES.get("chirp_narrator", "Kore"))
                        path = f"{folder}/{fname(VOICES.get('chirp_narrator', 'Kore'), text)}"
                        open(path, "wb").write(audio)
                        prev = path
                    except Later:
                        pass
                if prev:
                    for k in keys:
                        mp[k] = prev
                continue
            open(path, "wb").write(audio)
            made += 1
            if backfill and budget["left"] is not None:
                budget["left"] -= 1
        for k in keys:
            mp[k] = path
        # slow version
        sk = "slow:" + keys[0]
        if slow == "ai" and spec(voice).get("engine") == "gemini":
            sv = dict(spec(voice), style=VOICES.get("slow_style", "slowly and clearly"))
            spath = f"{folder}/{fname(sv, text)}"
            if not os.path.exists(spath) and not (backfill and budget["left"] is not None and budget["left"] <= 0):
                try:
                    open(spath, "wb").write(synth(text, sv))
                    made += 1
                    if backfill and budget["left"] is not None:
                        budget["left"] -= 1
                except Later:
                    spath = None
            if spath and os.path.exists(spath):
                for k in keys:
                    mp["slow:" + k] = spath
                continue
        if slow:
            spath = path[:-4] + "_s.mp3"
            if not os.path.exists(spath):
                try:
                    smart_slow(path, spath)
                except Exception as e:
                    print("slow failed", path, e)
                    continue
            for k in keys:
                mp["slow:" + k] = spath
    sig = hashlib.sha1("|".join(str(mp.get(k)) for k in sorted(mp) if re.match(r"^[dp]\d+$", k)).encode()).hexdigest()[:8]
    if (dt.date.today() - dt.date.fromisoformat(lid)).days > RADIO_DAYS:
        pass  # radio tracks are kept for the last RADIO_DAYS days only (they're the biggest files)
    elif old.get("_radio_sig") == sig and old.get("_radio") and os.path.exists(old["_radio"]):
        mp["_radio"], mp["_radio_tl"], mp["_radio_sig"] = old["_radio"], old.get("_radio_tl", []), sig
    else:
        r = radio(lesson, mp, folder)
        if r:
            mp["_radio"], mp["_radio_tl"], mp["_radio_sig"] = r[0], r[1], sig
    keep = {v for k, v in mp.items() if isinstance(v, str) and not k.startswith("_radio_")} | ({mp["_radio"]} if mp.get("_radio") else set())
    for f in glob.glob(f"{folder}/*.mp3"):
        if f not in keep:
            os.remove(f)
    json.dump(mp, open(f"audio/{lid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"{lid}: {len(keep)} files, {made} new" + (f", {later} left for the next run" if later else ""))


def main():
    if not GKEY:
        print("GEMINI_API_KEY is not set: only VOICEVOX and Chirp lines can be made.")
    ids = sys.argv[1:] or sorted((os.path.basename(f)[:-5] for f in glob.glob("lessons/2*.json")), reverse=True)
    today = dt.date.today()
    budget["left"] = BACKFILL
    for lid in ids:
        recent = (today - dt.date.fromisoformat(lid)).days <= 1
        build(lid, backfill=not recent and not sys.argv[1:])
    save_ledger()
    print(f"Gemini this month: ${spent():.3f} of ${VOICES.get('monthly_cap_usd', 3)} cap")


if __name__ == "__main__":
    main()
