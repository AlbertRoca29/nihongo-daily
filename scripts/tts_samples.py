#!/usr/bin/env python3
"""Make voice samples with Google Cloud Text-to-Speech.

Lists every Japanese voice of the premium types, reads the same few real
lesson lines with each one, and writes samples/index.html with players so
the voices can be compared by ear. Needs GOOGLE_TTS_KEY in the environment.
"""
import base64, html, json, os, re, sys, urllib.request, urllib.error

KEY = os.environ.get("GOOGLE_TTS_KEY", "").strip()
API = "https://texttospeech.googleapis.com/v1"
OUT = "samples"
TYPES = ["Chirp3-HD", "Neural2", "Wavenet"]  # best first

# (label, lesson file, line index): real lines in different registers
LINES = [
    ("Station staff · polite", "lessons/2026-11-02.json", 3),
    ("Tanaka-san · Nagano dialect", "lessons/2026-11-04.json", 2),
    ("Yuki · casual", "lessons/2026-11-05.json", 4),
]


def plain(s):
    """{漢字|かな|gloss} -> 漢字 ; {かな||gloss} -> かな"""
    return re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", s)


def call(path, body=None):
    url = f"{API}/{path}{'&' if '?' in path else '?'}key={KEY}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Google TTS error {e.code} on {path.split('?')[0]}: {e.read().decode()[:400]}")


def main():
    if not KEY:
        sys.exit("GOOGLE_TTS_KEY is not set (add it as a repository secret).")
    lines = []
    for label, f, i in LINES:
        d = json.load(open(f, encoding="utf-8"))["dialogue"][i]
        lines.append((label, plain(d["jp"]), d["en"]))

    voices = call("voices?languageCode=ja-JP")["voices"]
    pick = []
    for t in TYPES:
        pick += sorted((v for v in voices if f"-{t}-" in v["name"]), key=lambda v: v["name"])
    if not pick:
        sys.exit("No premium ja-JP voices returned: " + ", ".join(v["name"] for v in voices))

    os.makedirs(OUT, exist_ok=True)
    rows = []
    for v in pick:
        clips = []
        for n, (_, text, _) in enumerate(lines):
            r = call("text:synthesize", {
                "input": {"text": text},
                "voice": {"languageCode": "ja-JP", "name": v["name"]},
                "audioConfig": {"audioEncoding": "MP3"},
            })
            fn = f"{v['name']}_{n}.mp3"
            with open(os.path.join(OUT, fn), "wb") as fh:
                fh.write(base64.b64decode(r["audioContent"]))
            clips.append(fn)
        rows.append((v, clips))
        print("ok", v["name"], v.get("ssmlGender", ""))

    write_page(lines, rows)
    print(f"{len(rows)} voices x {len(lines)} lines -> {OUT}/index.html")


def write_page(lines, rows):
    e = html.escape
    head = "".join(f"<th>{e(l)}<div class=jp>{e(t)}</div><div class=en>{e(en)}</div></th>"
                   for l, t, en in lines)
    body = ""
    for v, clips in rows:
        kind = next(t for t in TYPES if f"-{t}-" in v["name"])
        g = v.get("ssmlGender", "").lower()
        cells = "".join(f'<td><audio controls preload="none" src="{c}"></audio></td>' for c in clips)
        body += (f'<tr><td class=v><b>{e(v["name"].split("-")[-1])}</b>'
                 f'<span class="tag {kind}">{kind}</span><span class=g>{g}</span></td>{cells}</tr>')
    page = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Voice samples</title><style>
:root{{--bg:#faf7f2;--fg:#222;--mut:#777;--line:#e5dfd5;--chip:#efe8dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16161a;--fg:#eee;--mut:#999;--line:#333;--chip:#2a2a30}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}} p{{color:var(--mut);margin:0 0 16px}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;min-width:720px}}
th,td{{border-bottom:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}}
th{{font-weight:600;font-size:13px;max-width:260px}} .jp{{font-weight:400;font-size:15px;margin-top:4px}}
.en{{font-weight:400;color:var(--mut)}} audio{{width:200px;height:36px}}
.v b{{display:block}} .tag{{font-size:11px;background:var(--chip);border-radius:4px;padding:1px 5px;margin-right:6px}}
.g{{font-size:12px;color:var(--mut)}}
</style></head><body><h1>Google voice samples</h1>
<p>The same three lesson lines in every Japanese voice. Note your favourites (and who they'd suit in the cast).</p>
<div class=wrap><table><tr><th>Voice</th>{head}</tr>{body}</table></div></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)


if __name__ == "__main__":
    main()
