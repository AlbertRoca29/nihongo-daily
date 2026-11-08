#!/usr/bin/env python3
"""The voice guide page: samples/lab/index.html.

Explains which voice every character uses now (from voices.json), what each engine and
model is, what it costs, and lets you compare candidate voices per character (from
samples/lab/results.json, written by scripts/voice_lab.py).

  python3 scripts/voice_page.py      # rebuild the page from the saved results (no API calls)
"""
import glob, html, json, os, re

OUT = "samples/lab"
ICON = "../../icons/cast/{}.svg"
e = html.escape

PEOPLE = {  # id: (Japanese name, English line)
    "you": ("アルちゃん", "You · 23, the learner"),
    "tanaka": ("田中さん", "67 · apple farmer, your host"),
    "keiko": ("恵子さん", "early 60s · Tanaka-san's wife"),
    "hana": ("ハナおばあちゃん", "84 · retired wagashi maker"),
    "sota": ("颯太", "11 · Tanaka-san's grandson"),
    "mio": ("澪", "16 · high-school brass band"),
    "sato": ("佐藤先生", "41 · English teacher"),
    "kenta": ("健太", "24 · guesthouse, from Osaka"),
    "yuki": ("由紀", "25 · office worker in Tokyo"),
    "ren": ("蓮", "26 · designer in Nagano city"),
    "hayato": ("黒鉄隼人", "samurai in Hana's legends"),
}

# What each engine is. Prices from Google's Cloud TTS pricing page (checked Nov 2026).
ENGINES = [
    dict(id="chirp", name="Google Chirp 3 HD", tag="Google Cloud Text-to-Speech",
         what="Google's realistic voices (30 voices, the same names as Gemini: Leda, Puck, Charon…). Very natural, "
              "but each voice has one fixed personality: you can change the speed, not the age, mood or accent.",
         runs="Google's servers, called by the GitHub workflow with your key GOOGLE_TTS_KEY.",
         price="First 1 million characters every month free, then $30 per million characters.",
         you="Used now for Hana (8% slower), Yuki, Kenta, Ren, Sato-sensei, Hayato, Keiko, you and the narrator.",
         cost="free"),
    dict(id="voicevox", name="VOICEVOX", tag="Free, open source (Japan)",
         what="A Japanese text-to-speech program with ~45 characters voiced by real voice actors, many styles "
              "each (normal, happy, whisper…). The only free engine with convincing kids and old men. A bit "
              "anime-like next to Google's voices.",
         runs="Inside the GitHub workflow (a Docker container), nothing to pay. GitHub Actions is free for public repos.",
         price="Free, including commercial use. Each character's terms require a credit line "
               "(“VOICEVOX:name”), shown at the bottom of Settings in the app.",
         you="Used now for Sōta (白上虎太郎, ふつう), Tanaka-san (ちび式じい) and Mio (春日部つむぎ).",
         cost="free"),
    dict(id="gemini", name="Google Gemini-TTS", tag="Directed voices",
         what="The same 30 Google voices, but the model reads a description of the speaker before reading the line "
              "(“a 24-year-old from Osaka, strong Kansai accent, teasing, fast”). So it can act: age, mood, accent, pace. "
              "Each reading comes out a little different.",
         runs="Google's servers. Through the Gemini API with your key GEMINI_API_KEY (AI Studio).",
         price="Gemini 2.5 Flash TTS: $0.50 per million text tokens + $10 per million audio tokens (25 tokens = 1 s), "
               "about $0.015 per minute of speech. Gemini 3.1 Flash TTS (preview) and 2.5 Pro TTS: about $0.03 per "
               "minute. Free tier on an AI Studio key without billing: 10 clips a day, too few for daily lessons.",
         you="Not used in the app yet. Tested here on the free tier (cards marked “directed”).",
         cost="paid"),
    dict(id="gemini38", name="Google Gemini 3.8 Flash TTS / Flash-Lite TTS", tag="Newest (Sept 2026) · voice design",
         what="Google's newest speech models. Besides directing a voice, they can DESIGN a brand-new voice from a "
              "description (age, timbre, accent) and keep it as a reusable voice id, and they have a library of 115 "
              "native Japanese voices with age and accent (Tokyo, Osaka, Fukuoka; ages 21–74, no children). Flash = best "
              "acting; Flash-Lite = cheaper and faster. Google refuses to design voices of minors, so Sōta and Mio can't "
              "get one.",
         runs="Google's servers, through the Gemini API with your key GEMINI_API_KEY.",
         price="Flash TTS: $0.50 per million text tokens + $9 per million audio tokens (≈ $0.0135 per minute) until 31 Dec "
               "2026, then $1 + $18 (≈ $0.027/min). Flash-Lite TTS: $0.50 + $6 (≈ $0.009/min), then $1 + $12 (≈ $0.018/min). "
               "Free tier without billing: 10 clips a day per model; with billing (Tier 1): 100 clips a day per model, plenty for a daily lesson.",
         you="Not used in the app yet. Designed voices for 9 characters are stored in your Google project (voices38.json); "
             "samples are in each character's comparison below, marked “3.8”.",
         cost="paid"),
    dict(id="aivis", name="AivisSpeech + AivisHub", tag="Free, open source (Japan)",
         what="A newer free Japanese engine with very natural voices made by the community (AivisHub has 77). "
              "Scanned all of them: no child or grandmother, a few middle-aged men.",
         runs="Inside the GitHub workflow, like VOICEVOX.",
         price="Free. Each model has its own licence.",
         you="Not used. Every voice is on the audition page.",
         cost="free"),
]


def chars_per_lesson():
    """Average characters per lesson read by Google Chirp (for the cost estimate)."""
    try:
        import importlib.util
        os.environ.setdefault("GOOGLE_TTS_KEY", "x")
        sp = importlib.util.spec_from_file_location("tts", "scripts/tts.py")
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        files = sorted(glob.glob("lessons/2*.json"))
        tot = sum(len(t) for f in files for _, t, v in m.items(json.load(open(f, encoding="utf-8")))
                  if not str(m.tag(v)).startswith("voicevox"))
        return round(tot / max(len(files), 1)), len(files)
    except Exception:
        return 350, 0


def describe(v):
    """voices.json entry -> (engine id, voice name, details)."""
    if isinstance(v, str):
        return "chirp", v, "Chirp 3 HD"
    if v.get("engine") == "voicevox":
        return "voicevox", f'{v["speaker"]}（{v.get("style", "ノーマル")}）', "VOICEVOX"
    if v.get("model"):
        return "gemini", v["voice"], f'Gemini-TTS · {v["model"]} · directed'
    rate = v.get("rate")
    return "chirp", v["voice"], "Chirp 3 HD" + (f" · {round((1 - rate) * 100)}% slower" if rate and rate < 1 else
                                                 f" · {round((rate - 1) * 100)}% faster" if rate and rate > 1 else "")


def in_use(cand, v):
    eng, name, _ = describe(v)
    if cand["engine"] == "voicevox":
        return eng == "voicevox" and cand["voice"] == name
    if cand["engine"] == "chirp":
        return eng == "chirp" and cand["voice"] == (v if isinstance(v, str) else v.get("voice")) and \
            not cand.get("shift", 1) != 1 and not cand.get("fx")
    return eng == "gemini" and cand["voice"] == v.get("voice")


CSS = """
:root{--bg:#faf7f2;--fg:#1f1d1a;--mut:#77706a;--line:#e7e0d4;--card:#fff;--acc:#c0392b;--soft:#f3ece2;
--ok:#2e7d4f;--okbg:#e5f3ea;--pay:#9a5b00;--paybg:#fcefd9}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--fg:#ececec;--mut:#9a958f;--line:#2e2e34;--card:#1d1d22;
--acc:#ff7b6b;--soft:#25252b;--ok:#7fd3a0;--okbg:#1d3326;--pay:#f0b45a;--paybg:#3a2c16}}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,sans-serif;margin:0 auto;padding:18px 16px 40px;max-width:780px}
h1{font-size:23px;margin:0 0 4px} h2{font-size:19px;margin:34px 0 8px;padding-top:6px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:0}
p{margin:6px 0} a{color:var(--acc)} small,.mut{color:var(--mut)}
nav{position:sticky;top:0;background:var(--bg);padding:8px 0;margin:10px 0;font-size:13px;z-index:2;
  display:flex;gap:6px;overflow-x:auto;white-space:nowrap;border-bottom:1px solid var(--line)}
nav a{padding:4px 10px;border-radius:99px;background:var(--soft);text-decoration:none;color:var(--fg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
.badge{display:inline-block;font-size:11px;font-weight:600;border-radius:99px;padding:1px 8px;margin-left:4px;vertical-align:2px}
.free{background:var(--okbg);color:var(--ok)} .paid{background:var(--paybg);color:var(--pay)}
.use{background:var(--acc);color:#fff}
.cast{display:grid;grid-template-columns:1fr;gap:8px}
@media(min-width:620px){.cast{grid-template-columns:1fr 1fr}}
.who{display:flex;gap:10px;align-items:center}
.who img{width:52px;height:52px;border-radius:50%;flex:none;background:var(--soft)}
.who .nm{font-weight:700} .who .sub{font-size:12px;color:var(--mut)}
.vline{font-size:13px;margin-top:2px}
dl{margin:6px 0 0;display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:14px}
dt{color:var(--mut)} dd{margin:0}
table{border-collapse:collapse;width:100%;font-size:14px} td,th{border-bottom:1px solid var(--line);padding:6px 4px;text-align:left;vertical-align:top}
th{font-size:12px;color:var(--mut);font-weight:600}
.total{font-size:20px;font-weight:700}
.char{scroll-margin-top:50px}
.chead{display:flex;gap:12px;align-items:center;margin-bottom:4px}
.chead img{width:64px;height:64px;border-radius:50%;background:var(--soft)}
.lines{margin:6px 0;padding-left:20px} .lines li{margin:2px 0}
details{font-size:13px;color:var(--mut);margin:4px 0 8px}
.cand{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;margin:8px 0}
.cand.inuse{border:2px solid var(--acc)} .cand.g38{background:var(--soft)} .cand.before{opacity:.8;border-style:dashed}
.tag{color:var(--acc);font-family:ui-monospace,monospace;font-weight:700}
.kind{font-size:12px;color:var(--mut)} .hz{float:right;font-size:12px;color:var(--mut)}
audio{width:100%;height:36px;display:block;margin:5px 0 0}
.miss{font-size:12px;color:var(--mut);margin-top:4px}
footer{margin-top:36px;font-size:12px;color:var(--mut)}
"""


def page(results):
    V = json.load(open("voices.json", encoding="utf-8"))
    current = dict(V["cast"])
    current["you"] = V["you"]
    current["keiko"] = V.get("others", {}).get("Keiko")
    cpl, nles = chars_per_lesson()
    month_chars = cpl * 30

    # 1 · who speaks with which voice now
    cards = []
    for cid, (jp, sub) in PEOPLE.items():
        v = current.get(cid)
        if not v:
            continue
        eng, name, detail = describe(v)
        badge = '<span class="badge free">free</span>' if eng != "gemini" else '<span class="badge paid">paid</span>'
        link = f' · <a href="#{cid}">compare</a>' if cid in results else ""
        cards.append(f'<div class="card who"><img src="{ICON.format(cid)}" alt=""><div><div class=nm>{e(jp)}</div>'
                     f'<div class=sub>{e(sub)}</div><div class=vline><b>{e(name)}</b> · {e(detail)} {badge}{link}</div>'
                     f'</div></div>')
    narr = describe(V["narrator"])
    cards.append(f'<div class="card who"><img src="../../icons/icon-192.png" alt=""><div><div class=nm>Narrator</div>'
                 f'<div class=sub>texts, signs, grammar examples, extras, staff and guests without a voice</div>'
                 f'<div class=vline><b>{e(narr[1])}</b> · {e(narr[2])} <span class="badge free">free</span></div></div></div>')
    pool = V.get("pool", {})
    guests = f'Guests and staff get a Chirp 3 HD voice from a pool ({len(pool.get("f", []))} women, {len(pool.get("m", []))} men).'

    # 2 · engines
    eng_html = "".join(
        f'<div class=card id="eng-{x["id"]}"><h3>{e(x["name"])} <span class="badge {"free" if x["cost"] == "free" else "paid"}">'
        f'{"free" if x["cost"] == "free" else "pay per use"}</span></h3><div class=mut style="font-size:13px">{e(x["tag"])}</div>'
        f'<p>{e(x["what"])}</p><dl><dt>Runs on</dt><dd>{e(x["runs"])}</dd><dt>Price</dt><dd>{e(x["price"])}</dd>'
        f'<dt>In your app</dt><dd>{e(x["you"])}</dd></dl></div>' for x in ENGINES)

    # 3 · costs
    gem_all = 23 * 0.015  # ~45 s of directed speech per lesson x 30 days ≈ 23 min
    costs = f"""
<div class=card><div class=mut>What you pay now</div><div class=total>$0 a month</div>
<table><tr><th>Part</th><th>Your use</th><th>Cost</th></tr>
<tr><td>Google Chirp 3 HD</td><td>~{cpl} characters a lesson × 30 ≈ {month_chars:,} a month
 ({month_chars / 10000:.1f}% of the free million)</td><td>$0</td></tr>
<tr><td>VOICEVOX</td><td>Sōta, Tanaka-san, Mio</td><td>$0</td></tr>
<tr><td>GitHub Actions + Pages</td><td>the audio workflow (~3 min a day) and hosting</td><td>$0 (public repo)</td></tr>
<tr><td>Gemini-TTS</td><td>not used in lessons</td><td>$0</td></tr></table>
<p class=mut style="font-size:13px">Audio is made once per line and kept in the repo, so lessons you re-open cost nothing.
Estimate from your {nles} lessons so far.</p></div>
<div class=card><div class=mut>If you add directed Gemini voices (2.5 Flash TTS, billing on)</div>
<table><tr><th>Option</th><th>Speech a month</th><th>Cost</th></tr>
<tr><td>Only Kenta (Osaka accent)</td><td>~2 min</td><td>≈ $0.05</td></tr>
<tr><td>Everyone not on VOICEVOX (Kenta, Yuki, Ren, Sato, Hayato, Keiko, you)</td><td>~23 min</td><td>≈ ${gem_all:.2f}</td></tr>
<tr><td>Same with Gemini 3.1 Flash / 2.5 Pro TTS</td><td>~23 min</td><td>≈ ${gem_all * 2:.2f}</td></tr>
<tr><td><b>Gemini 3.8 Flash-Lite</b>, designed voices for the 9 adults</td><td>~30 min</td><td>≈ $0.27 (≈ $0.54 from 2027)</td></tr>
<tr><td><b>Gemini 3.8 Flash</b>, designed voices for the 9 adults</td><td>~30 min</td><td>≈ $0.41 (≈ $0.81 from 2027)</td></tr></table>
<p class=mut style="font-size:13px">Without billing, an AI Studio key gives 10 clips a day: enough to test here, not for daily lessons.
A budget alert in Google Cloud can cap any surprise.</p></div>"""

    # 4 · compare per character (+ Gemini 3.8 samples from samples/lab38)
    lab38 = {}
    if os.path.exists("samples/lab38/results.json"):
        lab38 = json.load(open("samples/lab38/results.json", encoding="utf-8"))
    lib = {}
    if os.path.exists("samples/lab38/library.json"):
        lib = {x["id"]: x for x in json.load(open("samples/lab38/library.json", encoding="utf-8")) if isinstance(x, dict)}
    secs = []
    for cid, r in results.items():
        jp, sub = PEOPLE.get(cid, (r["label"], ""))
        v = current.get(cid)
        rows, missing = [], 0
        for c in r["cands"]:
            if not any(c["clips"]):
                missing += 1
                continue
            use = bool(v) and in_use(c, v)
            if c["engine"] == "chirp" and c.get("now"):
                kind = "Before · Chirp 3 HD, no direction"
                cls = "inuse" if use else "before"
            elif c["engine"] == "chirp":
                t = [f"speed ×{c['rate']}"] if c.get("rate", 1) != 1 else []
                if c.get("shift", 1) != 1:
                    t.append(("smaller, higher voice" if c["shift"] > 1 else "deeper voice") + f" ×{c['shift']}")
                if c.get("fx"):
                    t.append("age tremor")
                kind, cls = "Chirp 3 HD · " + (", ".join(t) or "as is") + " · free", ""
            elif c["engine"] == "gemini":
                kind, cls = "Gemini 2.5 Flash TTS · directed by the description above · ≈ $0.015/min", ""
            else:
                kind, cls = "VOICEVOX · free · credit line needed", ""
            if use:
                cls = "inuse"
                if isinstance(v, dict) and v.get("rate") and c["engine"] == "chirp" and c.get("rate", 1) != v["rate"]:
                    kind += f" · in the app: {describe(v)[2]}"
            ps = [p for p in c["pitch"] if p]
            hz = f'<span class=hz>~{round(sum(ps) / len(ps))} Hz</span>' if ps else ""
            clips = "".join(f'<audio controls preload="none" src="{e(f)}"></audio>' if f else
                            '<div class=miss>(line not made: free daily quota ran out)</div>' for f in c["clips"])
            mark = '<span class="badge use">in use</span>' if use else ""
            rows.append(f'<div class="cand {cls}"><b class=tag>{cid}-{c["tag"]}</b> <b>{e(c["voice"])}</b>{mark}{hz}'
                        f'<div class=kind>{e(kind)}</div>{clips}</div>')
        g = lab38.get(cid)
        waiting38 = 0
        if g:
            for w in g["rows"]:
                if not any(w["clips"]):
                    waiting38 += 1
                    continue
                lite = "lite" in w["model"]
                model = "Gemini 3.8 Flash-Lite TTS" if lite else "Gemini 3.8 Flash TTS"
                price = "≈ $0.009/min" if lite else "≈ $0.0135/min"
                if w["kind"] == "designed":
                    kind = f"{model} · voice designed from the description below · {price}"
                    name = "Designed voice"
                else:
                    info = lib.get(w["voice"], {})
                    kind = f"{model} · Japanese voice library: {info.get('description', w['voice'])} · {price}"
                    name = "Library voice"
                clips = "".join(f'<audio controls preload="none" src="../lab38/{e(f)}"></audio>' if f else
                                '<div class=miss>(line made tomorrow: daily limit)</div>' for f in w["clips"])
                tag = w["tag"].replace("-", "-38")
                rows.append(f'<div class="cand g38"><b class=tag>{tag}</b> <b>{e(name)}</b> <span class="badge paid">3.8</span>'
                            f'<div class=kind>{e(kind)}</div>{clips}</div>')
        lines = "".join(f"<li>{e(l)}</li>" for l in r["lines"])
        if g:
            lines_extra = (f'<details><summary>Voice design description (Gemini 3.8)</summary><p>{e(g["design"])}</p>'
                           f'<p>Style per line: {e(g["style"])}</p></details>')
        elif cid in ("sota", "mio"):
            lines_extra = '<p class=mut style="font-size:13px">Gemini 3.8 refuses to design voices of minors, so no designed voice here.</p>'
        else:
            lines_extra = ""
        if waiting38:
            lines_extra += f'<p class=mut style="font-size:13px">{waiting38} more Gemini 3.8 candidates are made tomorrow (100 clips a day per model).</p>'
        note = (f'<p class=mut style="font-size:13px">{missing} more directed voices wait for quota (free tier: 10 clips a day).</p>'
                if missing else "")
        now = describe(v) if v else None
        nowline = f'<p style="font-size:14px">Now: <b>{e(now[1])}</b> · {e(now[2])}</p>' if now else ""
        secs.append(f'<section class=char id={cid} style="border-top:1px solid var(--line);margin-top:26px;padding-top:14px"><div class=chead><img src="{ICON.format(cid)}" alt="">'
                    f'<div><h3 style="font-size:18px">{e(jp)}</h3><div class=mut style="font-size:13px">{e(sub)}</div></div></div>'
                    f'{nowline}<ol class=lines>{lines}</ol><details><summary>Description given to the directed voices</summary>'
                    f'<p>{e(r["prompt"])}</p></details>{lines_extra}{"".join(rows)}{note}</section>')
    nav = "".join(f'<a href="#{cid}">{e(PEOPLE.get(cid, (cid,))[0])}</a>' for cid in results)

    return f"""<!doctype html><html lang=ja><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Voices · Nihongo Line</title><style>{CSS}</style></head><body>
<h1>Voices of Nihongo Line</h1>
<p class=mut>Who speaks with which voice, what each engine is, what it costs, and every candidate side by side.</p>
<nav><a href="#now">Now</a><a href="#engines">Engines</a><a href="#cost">Cost</a><a href="#compare">Compare</a>{nav}</nav>

<h2 id=now>Who speaks with which voice now</h2>
<p>The daily lesson is read line by line, each line in the voice of whoever says it. The casting lives in <code>voices.json</code>;
change it there and the audio for every lesson is remade automatically.</p>
<div class=cast>{"".join(cards)}</div>
<p class=mut style="font-size:13px">{e(guests)} When a character writes a text (Sōta's essay), they read it themselves.</p>

<h2 id=engines>The engines and models</h2>
{eng_html}

<h2 id=cost>What it costs</h2>
{costs}

<h2 id=compare>Compare voices per character</h2>
<p>Each character reads the same two lines with every candidate. The red card is the voice in use; the dashed card is the voice
before this round. <b>Hz</b> is the average pitch: a man ~100–150, a woman ~180–250, an 11-year-old ~220–300.
To change a voice, send the tag (e.g. <b>kenta-B</b>).</p>
<p class=mut style="font-size:13px">Want more? <a href="../audition/">The audition</a> has every free voice (128 VOICEVOX + AivisHub) for Sōta, Hana and Tanaka-san.</p>
{"".join(secs)}

<footer>Prices: <a href="https://cloud.google.com/text-to-speech/pricing">Google Cloud Text-to-Speech pricing</a> ·
<a href="https://ai.google.dev/gemini-api/docs/pricing">Gemini API pricing</a> · <a href="https://ai.google.dev/gemini-api/docs/voice-design">Gemini voice design</a> · <a href="https://voicevox.hiroshiba.jp/">VOICEVOX</a> ·
<a href="https://hub.aivis-project.com/">AivisHub</a>.<br>VOICEVOX:白上虎太郎 · VOICEVOX:ちび式じい · VOICEVOX:春日部つむぎ</footer>
</body></html>"""


def write(results):
    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/index.html", "w", encoding="utf-8") as fh:
        fh.write(page(results))


if __name__ == "__main__":
    write(json.load(open(f"{OUT}/results.json", encoding="utf-8")))
    print("->", f"{OUT}/index.html")
