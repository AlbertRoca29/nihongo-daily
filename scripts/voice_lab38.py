#!/usr/bin/env python3
"""Gemini 3.8 voice lab: designed voices + the Japanese voice library, per character.

  python3 scripts/voice_lab38.py library   # list the ja-JP voices of the Extended Voice Library (no audio, free)
  python3 scripts/voice_lab38.py design    # design one voice per character (stored in the project), save ids
  python3 scripts/voice_lab38.py samples   # read each character's two lines with their candidates
Writes samples/lab38/ (library.json, designed.json, results.json). Needs GEMINI_API_KEY (AI Studio).
Designed voice ids also go to voices38.json at the repo root, so scripts/tts.py can use them.
"""
import base64, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
API = "https://generativelanguage.googleapis.com/v1beta"
OUT = "samples/lab38"
FLASH, LITE = "gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"
PACE = float(os.environ.get("GEMINI_PACE", "0"))

sys.path.insert(0, "scripts")
from voice_lab import CHARS  # same characters and lines as the first lab  # noqa: E402

# Permanent traits go in the designed voice; mood goes in the per-line style (Google's advice).
DESIGN = {
    "sota": "A real 11-year-old Japanese boy from Nagano, before his voice has broken: high, light, bright and a "
            "little raspy from shouting outdoors. Energetic, curious, talks fast and slightly breathless. Native Japanese.",
    "hana": "A frail, warm 84-year-old Japanese grandmother from a rural mountain village in Nagano. Thin, soft, slightly "
            "husky and a little shaky old woman's voice, slow and gentle, with a smile in it. Native Japanese.",
    "tanaka": "A 67-year-old Japanese apple farmer from rural Nagano. Low, gravelly, weathered older man's voice, few "
              "words, gruff but kind, relaxed rural intonation. Native Japanese.",
    "keiko": "A cheerful Japanese farmer's wife in her early sixties. Warm, chatty, motherly mature woman's voice, brisk "
             "and a bit teasing. Native Japanese.",
    "mio": "A 16-year-old Japanese high-school girl. Bright, quick, expressive teenage girl's voice, a little dramatic, "
           "casual and playful. Native Japanese.",
    "yuki": "A 25-year-old Tokyo office worker and anime fan. Lively, bubbly young woman's voice, fast casual Tokyo "
            "speech, lots of energy. Native Japanese.",
    "kenta": "A 24-year-old man from Osaka. Loud, friendly, funny young man's voice with a strong natural Osaka "
             "Kansai-ben accent and Kansai pitch accent, quick tempo. Native Japanese.",
    "ren": "A 26-year-old Japanese graphic designer. Soft, calm, gentle young man's voice, slightly low and warm, "
           "a bit shy and quiet. Native Japanese.",
    "sato": "A 41-year-old Japanese high-school teacher. Clear, composed, precise mature woman's voice, polite and "
            "formal, neat articulation. Native Japanese.",
    "hayato": "A samurai in his thirties from a classic Japanese period drama. Deep, strong, resonant, dignified male "
              "voice, theatrical and proud. Native Japanese.",
    "you": "A friendly 23-year-old young man. Warm, open, cheerful voice, clear and natural, casual. Native Japanese.",
}
STYLE = {
    "sota": "excited, curious, fast", "hana": "slow, gentle, amused, storytelling", "tanaka": "gruff, dry, unhurried",
    "keiko": "cheerful, chatty", "mio": "playful, dramatic", "yuki": "bubbly, teasing", "kenta": "joking, loud, fast",
    "ren": "soft, a little shy", "sato": "polite, composed", "hayato": "proud, theatrical", "you": "friendly, relaxed",
}


def call(path, body=None, method=None, params=None):
    url = f"{API}/{path}" + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data, {"Content-Type": "application/json", "x-goog-api-key": KEY},
                                 method=method or ("POST" if data else "GET"))
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r), None
        except urllib.error.HTTPError as e:
            txt = e.read().decode()
            if e.code in (429, 500, 503) and attempt < 3 and "limit: 0" not in txt and "PerDay" not in txt:
                m = re.search(r'"retryDelay":\s*"(\d+)', txt)
                time.sleep(min(int(m.group(1)) + 2 if m else 20, 70))
                continue
            return None, f"{e.code}: {txt[:500]}"
        except Exception as e:
            if attempt < 3:
                time.sleep(5)
                continue
            return None, str(e)[:300]


def library():
    voices, token = [], None
    for _ in range(40):
        p = {"language_code": "ja-JP", "page_size": 1000}
        if token:
            p["page_token"] = token
        d, err = call("voices", params=p)
        if err:
            print("library error", err)
            json.dump({"error": err}, open(f"{OUT}/library.json", "w"), indent=1)
            return
        voices += d.get("voices", [])
        token = d.get("nextPageToken") or d.get("next_page_token")
        if not token:
            break
    json.dump(voices, open(f"{OUT}/library.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(voices), "ja-JP voices")


def to_mp3(b64, wav=True):
    raw = base64.b64decode(b64)
    args = ["ffmpeg", "-loglevel", "error"] + ([] if wav else ["-f", "s16le", "-ar", "24000", "-ac", "1"]) + \
           ["-i", "-", "-f", "mp3", "-b:a", "64k", "-"]
    return subprocess.run(args, input=raw, capture_output=True, check=True).stdout


def design():
    path = "voices38.json"
    saved = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    log = {}
    for cid, desc in DESIGN.items():
        if cid in saved and saved[cid].get("description") == desc:
            continue
        d, err = call("voices", {"voice": {"type": "prompted", "model": FLASH, "display_name": f"nihongo-{cid}",
                                           "prompted": {"input": desc}}, "store": True})
        if err:
            log[cid] = err
            print(cid, err[:200])
            continue
        v = d.get("voice", d)
        vid = (v.get("name") or v.get("id") or "").split("/")[-1]
        saved[cid] = {"voice": vid, "description": desc}
        sa = (v.get("sampleAudio") or v.get("sample_audio") or {}).get("data")
        if sa:
            open(f"{OUT}/{cid}_designed_sample.mp3", "wb").write(to_mp3(sa))
        print(cid, vid)
        json.dump(saved, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(log, open(f"{OUT}/design_errors.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def speak(text, voice, model, style):
    part = {"text": text}
    if style:
        part["speech_metadata"] = {"style": style}
    d, err = call(f"models/{model}:generateContent", {
        "contents": [{"role": "user", "parts": [part]}],
        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"voice": voice}}}})
    if err:
        return None, err
    try:
        p = d["candidates"][0]["content"]["parts"][0]["inlineData"]
        return to_mp3(p["data"], wav="wav" in p.get("mimeType", "wav").lower()), None
    except Exception as e:
        return None, f"bad response: {str(e)[:200]} {json.dumps(d)[:300]}"


def samples(only):
    designed = json.load(open("voices38.json", encoding="utf-8")) if os.path.exists("voices38.json") else {}
    picks = json.load(open(f"{OUT}/library_picks.json", encoding="utf-8")) if os.path.exists(f"{OUT}/library_picks.json") else {}
    res_path = f"{OUT}/results.json"
    results = json.load(open(res_path, encoding="utf-8")) if os.path.exists(res_path) else {}
    for cid in only or list(DESIGN):
        cands = []
        if cid in designed:
            cands += [("designed", designed[cid]["voice"], FLASH), ("designed", designed[cid]["voice"], LITE)]
        for lv in picks.get(cid, []):
            cands.append(("library", lv, FLASH))
        rows = []
        for n, (kind, voice, model) in enumerate(cands):
            clips, errs = [], []
            for li, text in enumerate(CHARS[cid]["lines"]):
                fn = f"{cid}_{n}_{li}.mp3"
                audio, err = speak(text, voice, model, STYLE[cid])
                if audio:
                    open(f"{OUT}/{fn}", "wb").write(audio)
                    clips.append(fn)
                else:
                    clips.append(None)
                    errs.append(err)
                    print(cid, voice, model, err[:200])
                if PACE:
                    time.sleep(PACE)
            rows.append(dict(tag=f"{cid}-{chr(65 + n)}", kind=kind, voice=voice, model=model, clips=clips, errors=errs))
        results[cid] = dict(lines=CHARS[cid]["lines"], design=DESIGN[cid], style=STYLE[cid], rows=rows)
        json.dump(results, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(cid, "done")


if __name__ == "__main__":
    if not KEY:
        sys.exit("GEMINI_API_KEY is not set.")
    os.makedirs(OUT, exist_ok=True)
    step = sys.argv[1] if len(sys.argv) > 1 else "library"
    if step == "library":
        library()
    elif step == "design":
        design()
    elif step == "samples":
        samples(sys.argv[2:])
    elif step == "all":
        library(); design(); samples(sys.argv[2:])
