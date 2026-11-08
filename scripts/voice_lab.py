#!/usr/bin/env python3
"""Voice lab: compare voices with more personality for each character.

For every character it reads the same two lines with:
  - the voice used now (Chirp 3 HD, no style control),
  - Gemini-TTS (same Google voice names, but directed by a prompt that
    describes the person: age, mood, accent, pace),
  - for a few characters, a VOICEVOX character voice (free Japanese engine
    with real child / elderly / teen voices; needs a local engine on :50021).
Writes samples/lab/index.html (+ results.json with the measured pitch).

  python3 scripts/voice_lab.py            # everything
  python3 scripts/voice_lab.py sota hana  # just these characters
Needs GOOGLE_TTS_KEY. VOICEVOX rows are skipped if no engine is running.
"""
import base64, html, json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

KEY = os.environ.get("GOOGLE_TTS_KEY", "").strip()
API = "https://texttospeech.googleapis.com/v1/text:synthesize"
VV = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021")
OUT = "samples/lab"
CURRENT = json.load(open("voices.json", encoding="utf-8"))
NEW = "gemini-3.1-flash-tts-preview"
PRO = "gemini-2.5-pro-tts"

BASE = ("Read the Japanese line exactly as written, in natural native Japanese "
        "pronunciation, as a line of dialogue in a slice-of-life TV drama set in a "
        "small town in Nagano. Do not add or skip any words. ")

# id: label, who, prompt, lines, gemini voices (first one is also tried with 2.5 Pro), voicevox
CHARS = {
    "sota": dict(
        label="颯太 Sōta · 11, boy",
        prompt="You are Sōta, an 11-year-old Japanese boy in 5th grade. Speak with a real "
               "child's voice: high, light and bright, before his voice has broken. He is "
               "energetic, impatient and endlessly curious, talks fast, a bit breathless, "
               "with big excited rises in pitch, like a kid talking to an older friend he "
               "thinks is cool.",
        lines=["ねえねえ、アルちゃん！カブトムシって、なんで夜しか出てこないの？",
               "すげー！じゃあさ、いつか一緒にバルセロナの試合、見に行こうよ！"],
        gemini=["Leda", "Autonoe", "Fenrir", "Puck"],
        chirp=[("Leda", 1.1, 1.0), ("Autonoe", 1.1, 1.0), ("Leda", 1.08, 1.12), ("Autonoe", 1.08, 1.15),
               ("Laomedeia", 1.08, 1.14), ("Puck", 1.05, 1.35)],
        voicevox=[("白上虎太郎", "わーい"), ("白上虎太郎", "ふつう")]),
    "hana": dict(
        label="ハナおばあちゃん Hana · 84, grandma",
        prompt="You are Hana, an 84-year-old Japanese grandmother from a mountain village. "
               "Speak with a genuinely old woman's voice: thin, soft, slightly husky and "
               "a little shaky, slow and unhurried, warm and amused, with gentle pauses, "
               "like a grandmother telling an old story by the kotatsu.",
        lines=["停留所に、背の高い外国の子がおってのう。時刻表をじーっと見て、困った顔をしとったんじゃ。",
               "子どもの頃は、毎日この坂を歩かされたもんじゃよ。"],
        gemini=["Gacrux", "Sulafat", "Vindemiatrix", "Achernar"],
        chirp=[("Gacrux", 0.85, 1.0), ("Sulafat", 0.85, 1.0),
               ("Gacrux", 0.8, 0.96, "vibrato=f=5.5:d=0.12"), ("Sulafat", 0.8, 0.95, "vibrato=f=5:d=0.1"),
               ("Vindemiatrix", 0.8, 0.94, "vibrato=f=6:d=0.14"), ("Achernar", 0.8, 0.95, "vibrato=f=5.5:d=0.1")],
        voicevox=[]),
    "tanaka": dict(
        label="田中さん Tanaka-san · 67, farmer",
        prompt="You are Tanaka, a 67-year-old Japanese apple farmer from rural Nagano. "
               "Speak with an older man's low, slightly gravelly voice. He is quiet, "
               "practical and gruff, says few words, with a dry humour and hidden warmth; "
               "relaxed, unhurried, a little rough, slight rural Nagano intonation.",
        lines=["鷹ノ原のりんごは甘いずら。遠慮しないで食べな。",
               "明日は五時に起きるぞ。遅れたら妻に怒られるからな。"],
        gemini=["Algenib", "Charon", "Schedar", "Rasalgethi"],
        chirp=[("Algenib", 0.9, 1.0), ("Charon", 0.9, 0.93)],
        voicevox=[("ちび式じい", "")]),
    "keiko": dict(
        label="恵子 Keiko · Tanaka's wife",
        prompt="You are Keiko, a Japanese farmer's wife in her early sixties. Speak with a "
               "mature woman's voice, cheerful, chatty and motherly, a little teasing about "
               "her husband, brisk and warm.",
        lines=["主人に頼まれて、今日はりんご鍋にしたのよ。",
               "ほら、遠慮しないで。たくさん食べなきゃ、畑で倒れちゃうわよ。"],
        gemini=["Sulafat", "Callirrhoe", "Gacrux", "Vindemiatrix"],
        voicevox=[]),
    "mio": dict(
        label="澪 Mio · 16, high-school girl",
        prompt="You are Mio, a 16-year-old Japanese high-school girl. Speak with a young "
               "teenage girl's voice: bright, quick, a bit dramatic and expressive, "
               "casual teen slang delivery, rising and falling a lot, laughing a little, "
               "talking to a friend after school.",
        lines=["え、マジで？それウケるんだけど！",
               "明日の数学のテスト、ガチでやばい…もう無理すぎ。"],
        gemini=["Leda", "Zephyr", "Laomedeia", "Achernar"],
        chirp=[("Leda", 1.08, 1.0), ("Zephyr", 1.08, 1.0)],
        voicevox=[("春日部つむぎ", "")]),
    "yuki": dict(
        label="由紀 Yuki · 25, Tokyo office worker",
        prompt="You are Yuki, a 25-year-old office worker in Tokyo and an anime otaku. "
               "Speak with a young woman's lively, bubbly voice, very casual Tokyo speech, "
               "excited and teasing, fast, lots of energy, like voice-messaging a close friend.",
        lines=["アル〜！農家生活一日目、どうだった？？",
               "マジ！？いい人じゃん。でも夜とか寂しくない？"],
        gemini=["Laomedeia", "Aoede", "Zephyr", "Leda"],
        voicevox=[]),
    "kenta": dict(
        label="健太 Kenta · 24, from Osaka",
        prompt="You are Kenta, a 24-year-old guy from Osaka who works at a guesthouse. Speak "
               "with a strong, natural Osaka Kansai-ben accent and Kansai pitch accent. He is "
               "loud, funny and friendly, teasing, quick-witted, laughs easily, fast tempo.",
        lines=["日本はな、まず「告白」すんねん。「好きです、付き合ってください」って。そこから恋人になるんや。",
               "そこはめっちゃ違うな。俺の彼女、長野市で看護師やねん。"],
        gemini=["Puck", "Fenrir", "Sadachbia", "Zubenelgenubi"],
        voicevox=[]),
    "ren": dict(
        label="蓮 Ren · 26, designer",
        prompt="You are Ren, a 26-year-old graphic designer. Speak with a young man's soft, "
               "calm, gentle voice, a bit shy, warm and quiet, slightly hesitant, with small "
               "pauses, like talking to someone he likes and feeling a little nervous.",
        lines=["あ、ごめん、返事遅くなって。…今度の土曜日、空いてる？",
               "今日、フィルムで紅葉を撮ってきたんだ。アルちゃんにも見せたいな。"],
        gemini=["Algieba", "Enceladus", "Umbriel", "Iapetus"],
        voicevox=[]),
    "sato": dict(
        label="佐藤先生 Sato-sensei · 41, teacher",
        prompt="You are Sato-sensei, a 41-year-old Japanese high-school teacher. Speak with a "
               "mature woman's clear, composed, precise voice, polite and formal keigo, "
               "kind but businesslike, neat articulation, measured pace.",
        lines=["おはようございます。本日の職員会議は、三時半からでございます。",
               "校長先生がお見えになりましたら、ご挨拶をお願いいたします。"],
        gemini=["Kore", "Erinome", "Despina", "Gacrux"],
        voicevox=[]),
    "hayato": dict(
        label="黒鉄隼人 Hayato · samurai legend",
        prompt="You are Kurogane Hayato, a samurai in a classic jidaigeki period drama. Speak "
               "in a deep, strong, dignified male voice with theatrical samurai delivery: "
               "proud, earnest, a little stiff, resonant, with dramatic pauses.",
        lines=["拙者、くろがねはやとと申す。この峠は、拙者が命に代えても守り申す！",
               "かたじけない…そばの一杯で、生き返ったでござる。"],
        gemini=["Alnilam", "Orus", "Algenib", "Charon"],
        voicevox=[]),
    "you": dict(
        label="アルちゃん (You) · 23",
        prompt="You are a friendly 23-year-old man living in Japan. Speak with a young man's "
               "warm, open, cheerful voice, clear and natural, a little excited, casual.",
        lines=["疲れた〜。5時に起きて、一日中りんご畑にいた。でも景色がめっちゃきれい。",
               "すみません、松本まで行きたいんですが。"],
        gemini=["Achird", "Umbriel", "Iapetus", "Puck"],
        voicevox=[]),
}


def current_voice(cid):
    if cid == "you":
        return CURRENT["you"]
    return CURRENT["cast"].get(cid) or CURRENT.get("others", {}).get(cid.capitalize())


def google(text, voice, model=None, prompt=None, rate=1.0, shift=1.0, fx=""):
    audio, err = _google(text, voice, model, prompt, rate)
    if audio and (shift != 1.0 or fx):
        # raise/lower pitch and formants together (a smaller/larger voice), keep the tempo
        p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "-", "-af",
                            f"aresample=24000,asetrate=24000*{shift},aresample=24000,atempo={1/shift:.4f}" + (f",{fx}" if fx else ""),
                            "-f", "mp3", "-b:a", "64k", "-"], input=audio, capture_output=True)
        audio = p.stdout if p.returncode == 0 else audio
    return audio, err


def _google(text, voice, model=None, prompt=None, rate=1.0):
    v = {"languageCode": "ja-JP"}
    inp = {"text": text}
    if model:
        v.update(name=voice, modelName=model)
        inp["prompt"] = prompt
    else:
        v["name"] = f"ja-JP-Chirp3-HD-{voice}"
    cfg = {"audioEncoding": "MP3"}
    if rate != 1.0:
        cfg["speakingRate"] = rate
    body = {"input": inp, "voice": v, "audioConfig": cfg}
    req = urllib.request.Request(f"{API}?key={KEY}", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return base64.b64decode(json.load(r)["audioContent"]), None
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(2 ** attempt * 4)
                continue
            return None, f"{e.code}: {msg}"
        except Exception as e:  # timeouts
            if attempt < 4:
                time.sleep(5)
                continue
            return None, str(e)[:300]


def vv_get(path, data=None, method="GET"):
    req = urllib.request.Request(VV + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def vv_speakers():
    try:
        return json.loads(vv_get("/speakers"))
    except Exception:
        return None


def vv_style_id(speakers, name, style):
    for s in speakers:
        if s["name"] == name:
            for st in s["styles"]:
                if not style or st["name"] == style:
                    return st["id"], st["name"]
    return None, None


def voicevox(text, sid):
    try:
        q = vv_get(f"/audio_query?text={urllib.parse.quote(text)}&speaker={sid}", b"", "POST")
        wav = vv_get(f"/synthesis?speaker={sid}", q, "POST")
        p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "-", "-f", "mp3", "-b:a", "64k", "-"],
                           input=wav, capture_output=True, check=True)
        return p.stdout, None
    except Exception as e:
        return None, str(e)[:300]


def pitch(path):
    """Median F0 (Hz) of a clip, or None."""
    try:
        import librosa, numpy as np
        y, sr = librosa.load(path, sr=16000)
        f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=700, sr=sr)
        f = f0[voiced]
        return round(float(np.median(f))) if len(f) else None
    except Exception:
        return None


def main():
    if not KEY:
        sys.exit("GOOGLE_TTS_KEY is not set.")
    os.makedirs(OUT, exist_ok=True)
    if not sys.argv[1:]:
        for f in os.listdir(OUT):
            if f.endswith(".mp3"):
                os.remove(os.path.join(OUT, f))
    want = sys.argv[1:] or list(CHARS)
    speakers = vv_speakers()
    print("VOICEVOX:", "running" if speakers else "not running")
    results = {}
    for cid in want:
        c = CHARS[cid]
        prompt = BASE + c["prompt"]
        cands = []
        cur = current_voice(cid)
        if cur:
            cands.append(dict(engine="chirp", voice=cur, now=True))
        for v, rate, shift, *fx in c.get("chirp", []):
            cands.append(dict(engine="chirp", voice=v, rate=rate, shift=shift, fx=(fx[0] if fx else "")))
        for i, v in enumerate(c["gemini"]):
            cands.append(dict(engine="gemini", voice=v, model=NEW))
            if i == 0:
                cands.append(dict(engine="gemini", voice=v, model=PRO))
        for name, style in c["voicevox"]:
            if speakers:
                sid, sname = vv_style_id(speakers, name, style)
                if sid is not None:
                    cands.append(dict(engine="voicevox", voice=f"{name}（{sname}）", sid=sid))
        for n, cand in enumerate(cands):
            cand["tag"] = chr(65 + n)
            cand["clips"], cand["errors"], cand["pitch"] = [], [], []
            for li, text in enumerate(c["lines"]):
                fn = f"{cid}_{cand['tag']}_{li}.mp3"
                if cand["engine"] == "voicevox":
                    audio, err = voicevox(text, cand["sid"])
                elif cand["engine"] == "gemini":
                    audio, err = google(text, cand["voice"], cand["model"], prompt)
                else:
                    audio, err = google(text, cand["voice"], rate=cand.get("rate", 1.0),
                                        shift=cand.get("shift", 1.0), fx=cand.get("fx", ""))
                if audio:
                    with open(os.path.join(OUT, fn), "wb") as fh:
                        fh.write(audio)
                    cand["clips"].append(fn)
                    cand["pitch"].append(pitch(os.path.join(OUT, fn)))
                else:
                    cand["clips"].append(None)
                    cand["errors"].append(err)
                    cand["pitch"].append(None)
            print(cid, cand["tag"], cand["engine"], cand["voice"], cand.get("model", ""),
                  "pitch", cand["pitch"], "ERR " + cand["errors"][0] if cand["errors"] else "")
        results[cid] = dict(label=c["label"], prompt=c["prompt"], lines=c["lines"], cands=cands)
    old = {}
    if os.path.exists(f"{OUT}/results.json") and sys.argv[1:]:
        old = json.load(open(f"{OUT}/results.json", encoding="utf-8"))
    old.update(results)
    results = {k: old[k] for k in CHARS if k in old}
    json.dump(results, open(f"{OUT}/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_page(results)


def write_page(results):
    e = html.escape
    secs, waiting = [], 0
    for cid, r in results.items():
        rows = []
        for c in r["cands"]:
            if not any(c["clips"]):
                waiting += 1
                continue
            if c["engine"] == "chirp" and c.get("now"):
                what, kind = f"{c['voice']}", "now · Chirp 3 HD (no direction)"
            elif c["engine"] == "chirp":
                tweaks = [f"speed ×{c['rate']}"] if c.get("rate", 1) != 1 else []
                if c.get("shift", 1) != 1:
                    tweaks.append(("smaller, higher" if c["shift"] > 1 else "deeper") + f" voice ×{c['shift']}")
                if c.get("fx"):
                    tweaks.append("age tremor")
                what, kind = c["voice"], "Chirp 3 HD · " + (", ".join(tweaks) or "as is")
            elif c["engine"] == "gemini":
                what = c["voice"]
                kind = "Gemini 3.1 Flash TTS · directed" if c["model"] == NEW else "Gemini 2.5 Pro TTS · directed"
            else:
                what, kind = c["voice"], "VOICEVOX"
            clips = "".join(
                f'<audio controls preload="none" src="{e(f)}"></audio>' if f else
                '' for f in c["clips"])
            ps = [p for p in c["pitch"] if p]
            hz = f'<span class=hz>~{round(sum(ps)/len(ps))} Hz</span>' if ps else ""
            msg = c["errors"][0] if c["errors"] else ""
            if "aiplatform" in msg or "Agent Platform" in msg:
                msg = "Not available yet: the Google project needs the Agent Platform (Vertex AI) API enabled."
            err = f'<div class=err>{e(msg)}</div>' if msg else ""
            rows.append(f'<div class="cand{" now" if c.get("now") else ""}"><div class=hd>'
                        f'<b class=tag>{cid}-{c["tag"]}</b> <b>{e(what)}</b> {hz}'
                        f'<div class=kind>{e(kind)}</div></div>{clips}{err}</div>')
        lines = "".join(f"<li>{e(l)}</li>" for l in r["lines"])
        secs.append(f'<section id={cid}><h2>{e(r["label"])}</h2><ol class=lines>{lines}</ol>'
                    f'<details><summary>Direction given to Gemini</summary><p>{e(r["prompt"])}</p></details>'
                    f'{"".join(rows)}</section>')
    nav = " · ".join(f'<a href="#{cid}">{e(r["label"].split(" · ")[0])}</a>' for cid, r in results.items())
    wait = (f'<p class=err>{waiting} directed Gemini voices are not shown yet: the Google project needs the '
            'Agent Platform (Vertex AI) API enabled. They appear here after the next run.</p>') if waiting else ""
    page = f"""<!doctype html><html lang=ja><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Voice lab</title><style>
:root{{--bg:#faf7f2;--fg:#222;--mut:#777;--line:#e5dfd5;--card:#fff;--acc:#c0392b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16161a;--fg:#eee;--mut:#999;--line:#333;--card:#202026;--acc:#ff7b6b}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;padding:16px;max-width:760px}}
h1{{font-size:21px;margin:0 0 6px}} h2{{font-size:18px;margin:28px 0 6px}}
.intro{{color:var(--mut)}} nav{{font-size:13px;line-height:2}} a{{color:var(--acc)}}
.lines{{margin:0 0 6px;padding-left:22px;font-size:15px}}
details{{font-size:13px;color:var(--mut);margin-bottom:8px}}
.cand{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;margin:8px 0}}
.cand.now{{border-style:dashed;opacity:.85}}
.hd{{margin-bottom:6px}} .tag{{color:var(--acc);font-family:ui-monospace,monospace}}
.kind{{font-size:12px;color:var(--mut)}} .hz{{font-size:12px;color:var(--mut);float:right}}
audio{{width:100%;height:36px;display:block;margin:4px 0}} .err{{color:var(--acc);font-size:12px}}
footer{{color:var(--mut);font-size:12px;margin:30px 0}}
</style></head><body><h1>Voice lab · Nihongo Line</h1>
<p class=intro>Each character reads the same two lines (in order) with several voices. The dashed card is the voice
the app uses now. “Directed” voices were given a description of the character (age, mood, accent) to act from.
Pick your favourite per character and send the tags (e.g. <b>sota-C, hana-B</b>). Gemini voices act a little differently
each time, so the same pick can sound slightly different line to line.</p>
{wait}<nav>{nav}</nav>{"".join(secs)}
<footer>VOICEVOX voices: VOICEVOX:白上虎太郎, VOICEVOX:ちび式じい, VOICEVOX:春日部つむぎ.</footer></body></html>"""
    with open(f"{OUT}/index.html", "w", encoding="utf-8") as fh:
        fh.write(page)
    print("->", f"{OUT}/index.html")


if __name__ == "__main__":
    main()
