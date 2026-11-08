#!/usr/bin/env python3
"""Voice audition: one line per role, read by every free Japanese voice we can run.

Engines (both run locally in GitHub Actions, no key needed):
  - VOICEVOX engine on :50021 — every speaker and style it ships.
  - AivisSpeech engine on :10101 — natural voice models from AivisHub, found by
    searching AivisHub for child / elderly keywords and installed on the fly.
Writes samples/audition/index.html, sorted by measured pitch, plus results.json
(and aivishub.json with what the search returned, for debugging).
"""
import html, json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

OUT = "samples/audition"
VV = "http://127.0.0.1:50021"
AV = "http://127.0.0.1:10101"
HUB = "https://api.aivis-project.com/v1"

ROLES = {
    "sota": ("颯太 Sōta · 11-year-old boy", "ねえねえ、アルちゃん！カブトムシって、なんで夜しか出てこないの？"),
    "hana": ("ハナおばあちゃん · 84-year-old grandma", "子どもの頃は、毎日この坂を歩かされたもんじゃよ。のう、アルちゃん。"),
    "tanaka": ("田中さん · 67-year-old farmer", "明日は五時に起きるぞ。遅れたら妻に怒られるからな。"),
}
KEYWORDS = ["少年", "男の子", "子供", "ショタ", "おばあちゃん", "おばあさん", "老婆", "老人",
            "おじいちゃん", "おじいさん", "高齢", "シニア", "老年"]
PER_KEYWORD = 3
MAX_MODELS = 24


def http(url, data=None, method=None, headers=None, timeout=300):
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data is not None else "GET"),
                                 headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def up(base):
    try:
        http(base + "/version", timeout=5)
        return True
    except Exception:
        return False


def synth(base, text, sid):
    q = http(f"{base}/audio_query?text={urllib.parse.quote(text)}&speaker={sid}", b"")
    wav = http(f"{base}/synthesis?speaker={sid}", q, headers={"Content-Type": "application/json"})
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "-", "-f", "mp3", "-b:a", "64k", "-"],
                       input=wav, capture_output=True, check=True)
    return p.stdout


def pitch(path):
    try:
        import librosa, numpy as np
        y, sr = librosa.load(path, sr=16000)
        f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=700, sr=sr)
        f = f0[voiced]
        return round(float(np.median(f))) if len(f) else None
    except Exception:
        return None


import re
WANT = re.compile(r"少年|男の子|男児|ショタ|子ども|子供|こども|キッズ|小学生|幼い|幼児|園児|おばあ|お婆|婆|祖母|ばあば|老婆|老女|お年寄り|"
                  r"高齢|シニア|老人|老年|長老|おじい|お爺|爺|祖父|じいじ|老紳士|初老|熟年|嗄れ|しわがれ|ハスキー|"
                  r"おかん|おかあ|母|主婦|関西|大阪|方言|おじさん|中年|おとん|バリトン|せっかち", re.I)


def hub_catalogue(log):
    """Every public AivisHub model (paged), then the ones whose name/description/tags fit our roles."""
    allm, seen = [], set()
    for page in range(1, 40):
        url = f"{HUB}/aivm-models/search?" + urllib.parse.urlencode(
            {"sort": "download", "page_size": 30, "page": page})
        try:
            data = json.loads(http(url, timeout=30))
        except Exception as e:
            log.append({"page": page, "error": str(e)[:200]})
            break
        ms = data.get("aivm_models") or []
        new = [m for m in ms if m.get("aivm_model_uuid") not in seen]
        if not new:
            break
        for m in new:
            seen.add(m.get("aivm_model_uuid"))
            tags = [t.get("name", t) if isinstance(t, dict) else t for t in m.get("tags", [])]
            spk = " ".join(f'{x.get("name","")} {x.get("description","") if isinstance(x, dict) else ""}'
                           for x in (m.get("speakers") or []) if isinstance(x, dict))
            allm.append(dict(uuid=m.get("aivm_model_uuid"), name=m.get("name", "?"),
                             description=(m.get("description") or "")[:400], tags=tags,
                             speakers=spk[:300], downloads=m.get("total_download_count"),
                             license=m.get("license_type")))
        log.append({"page": page, "got": len(new), "total": data.get("total")})
    json.dump(allm, open(f"{OUT}/aivishub_catalogue.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    hits = []
    for m in allm:
        blob = " ".join([m["name"], m["description"], " ".join(map(str, m["tags"])), m["speakers"]])
        found = WANT.findall(blob)
        if found:
            hits.append((m["uuid"], m["name"], m["description"][:160], m["tags"], "/".join(sorted(set(found)))))
    log.append({"catalogue": len(allm), "hits": [(h[1], h[4]) for h in hits]})
    return hits[:MAX_MODELS]


def hub_models(log):
    """Search AivisHub for child / elderly models. Returns [(uuid, name, description)]."""
    found, seen = [], set()
    for kw in KEYWORDS:
        url = f"{HUB}/aivm-models/search?" + urllib.parse.urlencode(
            {"keyword": kw, "sort": "download", "page_size": 10})
        try:
            data = json.loads(http(url, timeout=30))
        except Exception as e:
            log.append({"keyword": kw, "error": str(e)[:200]})
            continue
        models = data.get("aivm_models") or data.get("models") or data.get("items") or []
        log.append({"keyword": kw, "total": data.get("total"), "keys": list(data)[:10],
                    "names": [m.get("name") for m in models][:10]})
        n = 0
        for m in models:
            uid = m.get("aivm_model_uuid") or m.get("uuid") or m.get("id")
            if not uid or uid in seen:
                continue
            seen.add(uid)
            desc = (m.get("description") or "")[:160]
            tags = [t.get("name", t) if isinstance(t, dict) else t for t in m.get("tags", [])]
            found.append((uid, m.get("name", "?"), desc, tags, kw))
            n += 1
            if n >= PER_KEYWORD:
                break
    return found[:MAX_MODELS]


def install(uid, log):
    url = f"{HUB}/aivm-models/{uid}/download?model_type=AIVMX"
    try:
        body = urllib.parse.urlencode({"url": url}).encode()
        http(f"{AV}/aivm_models/install", body,
             headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=900)
        return True
    except urllib.error.HTTPError as e:
        log.append({"install": uid, "error": f"{e.code} {e.read().decode()[:200]}"})
    except Exception as e:
        log.append({"install": uid, "error": str(e)[:200]})
    # fallback: download the file ourselves and upload it
    try:
        data = http(url, timeout=900)
        boundary = "----lab" + str(int(time.time()))
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{uid}.aivmx\"\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
        http(f"{AV}/aivm_models/install", body,
             headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=900)
        return True
    except Exception as e:
        log.append({"install-upload": uid, "error": str(e)[:200]})
        return False


def styles(base):
    out = []
    for s in json.loads(http(base + "/speakers")):
        for st in s["styles"]:
            out.append((st["id"], s["name"], st["name"], s.get("speaker_uuid", "")))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    keep_vv = os.environ.get("AIVIS_ONLY") == "1"
    prev = json.load(open(f"{OUT}/results.json", encoding="utf-8")) if keep_vv and os.path.exists(f"{OUT}/results.json") else {}
    for f in os.listdir(OUT):
        if f.endswith(".mp3") and not (keep_vv and "_V" in f):
            os.remove(os.path.join(OUT, f))
    log, voices = [], []
    if not keep_vv and up(VV):
        for sid, sp, st, _ in styles(VV):
            voices.append(dict(engine="VOICEVOX", base=VV, sid=sid, name=sp, style=st))
    elif not keep_vv:
        log.append("VOICEVOX not running")
    hub = []
    if up(AV):
        before = {x[3] for x in styles(AV)}
        hub = hub_catalogue(log) or hub_models(log)
        for uid, name, desc, tags, kw in hub:
            ok = install(uid, log)
            log.append({"model": name, "uuid": uid, "keyword": kw, "installed": ok})
        info = {h[1]: h for h in hub}
        for sid, sp, st, suid in styles(AV):
            h = info.get(sp)
            voices.append(dict(engine="AivisSpeech", base=AV, sid=sid, name=sp, style=st,
                               about=(h[2] if h else ""), tags=(h[3] if h else []),
                               keyword=(h[4] if h else "bundled")))
    else:
        log.append("AivisSpeech not running")
    json.dump(log, open(f"{OUT}/aivishub.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(voices), "voices")

    results = {}
    for rid, (label, text) in ROLES.items():
        rows = []
        for n, v in enumerate(voices):
            fn = f"{rid}_{v['engine'][0]}{v['sid']}.mp3"
            try:
                audio = synth(v["base"], text, v["sid"])
            except Exception as e:
                print("fail", rid, v["name"], v["style"], str(e)[:100])
                continue
            with open(os.path.join(OUT, fn), "wb") as fh:
                fh.write(audio)
            rows.append(dict({k: v[k] for k in v if k != "base"}, file=fn, hz=pitch(os.path.join(OUT, fn))))
        if keep_vv and rid in prev:
            rows += [x for x in prev[rid]["rows"] if x["engine"] == "VOICEVOX"]
        print(rid, len(rows))
        results[rid] = dict(label=label, text=text, rows=rows)
    json.dump(results, open(f"{OUT}/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_page(results)


def write_page(results):
    e = html.escape
    secs = []
    for rid, r in results.items():
        rows = sorted(r["rows"], key=lambda x: (x["hz"] or 0))
        items = "".join(
            f'<div class=c><div class=hd><b class=tag>{rid}-{x["engine"][0]}{x["sid"]}</b> '
            f'<b>{e(x["name"])}</b> <span class=st>{e(x["style"])}</span>'
            f'<span class=hz>{x["hz"] or "?"} Hz</span><div class=k>{e(x["engine"])}'
            f'{(" · " + e(x.get("about", ""))) if x.get("about") else ""}</div></div>'
            f'<audio controls preload="none" src="{e(x["file"])}"></audio></div>' for x in rows)
        secs.append(f'<section id={rid}><h2>{e(r["label"])}</h2><p class=line>{e(r["text"])}</p>'
                    f'<p class=k>{len(rows)} voices, from lowest to highest pitch.</p>{items}</section>')
    nav = " · ".join(f'<a href="#{rid}">{e(r["label"].split(" · ")[0])}</a>' for rid, r in results.items())
    page = f"""<!doctype html><html lang=ja><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Voice audition</title><style>
:root{{--bg:#faf7f2;--fg:#222;--mut:#777;--line:#e5dfd5;--card:#fff;--acc:#c0392b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16161a;--fg:#eee;--mut:#999;--line:#333;--card:#202026;--acc:#ff7b6b}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;padding:16px;max-width:760px}}
h1{{font-size:21px;margin:0 0 6px}} h2{{font-size:18px;margin:28px 0 4px}} a{{color:var(--acc)}}
.line{{font-size:17px;margin:4px 0}} .k{{font-size:12px;color:var(--mut)}}
.c{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin:6px 0}}
.tag{{color:var(--acc);font-family:ui-monospace,monospace}} .st{{color:var(--mut);font-size:13px}}
.hz{{float:right;font-size:12px;color:var(--mut)}} audio{{width:100%;height:34px;display:block;margin-top:4px}}
</style></head><body><h1>Voice audition · free engines</h1>
<p class=k>Every voice of VOICEVOX and of AivisSpeech (with child / elderly models found on AivisHub) reads one line per role.
Sorted by pitch: a real 11-year-old boy is roughly 220–300 Hz; an elderly woman roughly 160–220 Hz; an older man 90–140 Hz.
Send the tags you like (e.g. sota-V12). VOICEVOX voices need a credit line (VOICEVOX:name) in the app; AivisHub models follow their own licence.</p>
<nav>{nav}</nav>{"".join(secs)}</body></html>"""
    open(f"{OUT}/index.html", "w", encoding="utf-8").write(page)


if __name__ == "__main__":
    main()
