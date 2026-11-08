#!/usr/bin/env python3
"""Make the lesson audio with Google Cloud Text-to-Speech.

For each lesson, every line the app can play (main text, phrases, grammar
examples, extras, the kanji word) is read in the voice of whoever says it
(see voices.json) and saved as audio/<lesson>/<hash>.mp3. audio/<lesson>.json
maps the line's plain text (furigana removed, as the app does) to its file.
Files are named by voice + text, so unchanged lines are never remade.

  python3 scripts/tts.py            # lessons missing audio or changed
  python3 scripts/tts.py 2026-11-05  # just these lessons
Needs GOOGLE_TTS_KEY in the environment.
"""
import base64, glob, hashlib, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

KEY = os.environ.get("GOOGLE_TTS_KEY", "").strip()
API = "https://texttospeech.googleapis.com/v1/text:synthesize"
MARK = re.compile(r"\{([^|{}]+)\|([^|{}]*)(?:\|([^|{}]+)(?:\|([1-4]))?)?\}")  # same as index.html
VOICES = json.load(open("voices.json", encoding="utf-8"))
CAST = json.load(open("cast.json", encoding="utf-8"))["cast"]
BY_NAME = {c["name"]: c for c in CAST}


def plain(s):
    """What the app uses as the key: furigana markup removed."""
    return MARK.sub(r"\1", str(s or ""))


def names(lesson):
    """Bases of proper nouns, read from their kana so the engine never guesses."""
    out = {}
    for c in CAST + ([lesson["guest"]] if lesson.get("guest") else []):
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
        is_name = reading and ("鷹ノ原" in base or base in nm or
                               any(len(base) >= 2 and base in b for b in nm))
        return reading if is_name else base

    s = MARK.sub(sub, str(text))
    s = re.sub(r"[（(]スタンプ[：:][^）)]*[）)]", "", s)      # LINE stickers
    s = re.sub(r"(?<=[^A-Za-z0-9])[ｗw]+(?=[\s。、！？!?]|$)", "", s)  # ｗｗ = lol
    s = re.sub(r"[\U0001F000-\U0001FAFF☀-➿]", "", s)  # emoji
    return re.sub(r"\s+", " ", s).strip()


VV = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
_VV_IDS = {}


def spec(v):
    """A voices.json entry. "Leda" = Chirp 3 HD; {"voice", "rate"} = Chirp at another speed;
    {"voice", "model", "prompt"} = directed Gemini-TTS; {"engine": "voicevox", "speaker", "style"} = VOICEVOX."""
    return v if isinstance(v, dict) else {"voice": v}


def voicevox(text, v):
    """Synthesize with a local VOICEVOX engine (started by the workflow), as MP3."""
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
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "-", "-f", "mp3", "-b:a", "64k", "-"],
                       input=wav, capture_output=True, check=True)
    return p.stdout


def pick(pool, name):
    return pool[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(pool)]


def voice_for(line, lesson):
    """Voice name for a main-text line."""
    sp = line.get("speaker", "")
    if line.get("me") or sp == "You":
        return VOICES["you"]
    if lesson.get("format") == "text":
        r = lesson.get("reader")  # a text written by a character is read in their voice
        if r in VOICES["cast"]:
            return VOICES["cast"][r]
        if r in VOICES.get("others", {}):
            return VOICES["others"][r]
        return VOICES["narrator"]
    if sp in VOICES.get("others", {}):
        return VOICES["others"][sp]
    c = BY_NAME.get(sp)
    if c and c["id"] in VOICES["cast"]:
        return VOICES["cast"][c["id"]]
    g = line.get("voice") or ((lesson.get("guest") or {}).get("voice")
                              if (lesson.get("guest") or {}).get("name") == sp else None)
    if g in ("f", "m"):
        return pick(VOICES["pool"][g], sp or "guest")
    return VOICES["narrator"]


def items(lesson):
    """(key, spoken text, voice) for everything the app can play, first wins."""
    out, seen = [], set()

    def add(jp, voice, override=None):
        k = plain(jp)
        if k and k not in seen:
            seen.add(k)
            out.append((k, spoken(jp, lesson, override), voice))

    for d in lesson.get("dialogue", []):
        add(d["jp"], voice_for(d, lesson), d.get("tts"))
    for p in lesson.get("phrases", []):
        add(p["jp"], VOICES["you"] if p.get("me", True) else VOICES["narrator"], p.get("tts"))
    for x in (lesson.get("grammar") or {}).get("examples", []):
        add(x["jp"], VOICES["narrator"], x.get("tts"))
    for ex in lesson.get("extras", []):
        for it in ex.get("items", []):
            add(it["jp"], VOICES["narrator"], it.get("tts"))
    k = lesson.get("kanji") or {}
    if k.get("reading"):
        add(k["reading"], VOICES["narrator"])
    return out


def synth(text, voice):
    v = spec(voice)
    if v.get("engine") == "voicevox":
        return voicevox(text, v)
    inp = {"text": text}
    if v.get("model"):  # Gemini-TTS: same voice names, steered by a description of the speaker
        sel = {"languageCode": "ja-JP", "name": v["voice"], "modelName": v["model"]}
        inp["prompt"] = VOICES.get("direction", "") + v.get("prompt", "")
    else:
        sel = {"languageCode": "ja-JP", "name": f"ja-JP-{VOICES['model']}-{v['voice']}"}
    cfg = {"audioEncoding": "MP3"}
    if v.get("rate") and not v.get("model"):
        cfg["speakingRate"] = v["rate"]
    body = {"input": inp, "voice": sel, "audioConfig": cfg}
    req = urllib.request.Request(f"{API}?key={KEY}", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(2 ** attempt * 4)
                continue
            raise SystemExit(f"Google TTS error {e.code} for {v['voice']}: {e.read().decode()[:300]}")


def tag(voice):
    """What identifies a voice in the file name (unchanged for plain Chirp voices)."""
    v = spec(voice)
    if v.get("engine") == "voicevox":
        return f"voicevox|{v['speaker']}|{v.get('style', '')}|{v.get('rate', 1.0)}"
    if not v.get("model"):
        return f"{VOICES['model']}|{v['voice']}" + (f"|{v['rate']}" if v.get("rate") else "")
    return f"{v['model']}|{v['voice']}|{VOICES.get('direction', '')}{v.get('prompt', '')}"


def build(lid):
    lesson = json.load(open(f"lessons/{lid}.json", encoding="utf-8"))
    folder = f"audio/{lid}"
    os.makedirs(folder, exist_ok=True)
    mp, made = {}, 0
    for key, text, voice in items(lesson):
        h = hashlib.sha1(f"{tag(voice)}|{text}".encode()).hexdigest()[:12]
        path = f"{folder}/{h}.mp3"
        if not os.path.exists(path):
            with open(path, "wb") as fh:
                fh.write(synth(text, voice))
            made += 1
        mp[key] = path
    keep = set(mp.values())
    for f in glob.glob(f"{folder}/*.mp3"):
        if f not in keep:
            os.remove(f)
    with open(f"audio/{lid}.json", "w", encoding="utf-8") as fh:
        json.dump(mp, fh, ensure_ascii=False, indent=0, sort_keys=True)
    print(f"{lid}: {len(mp)} lines, {made} new")


def main():
    if not KEY:
        sys.exit("GOOGLE_TTS_KEY is not set (add it as a repository secret).")
    ids = sys.argv[1:] or sorted(os.path.basename(f)[:-5] for f in glob.glob("lessons/2*.json"))
    for lid in ids:
        build(lid)


if __name__ == "__main__":
    main()
