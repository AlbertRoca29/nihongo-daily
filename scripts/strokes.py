#!/usr/bin/env python3
"""Save stroke-order data for every kanji the lessons teach.

For each kanji in kanji_study (and the spotted-kanji word), downloads its
KanjiVG drawing and saves strokes/<hex>.json = {"d": [path per stroke, in
order], "n": [[x, y] of each stroke number]} on a 109x109 grid. The app uses it
to animate the stroke order and direction on the drawing pad.
Existing files are kept, so only new kanji are fetched.

  python3 scripts/strokes.py

Stroke data: KanjiVG (c) Ulrich Apel, CC BY-SA 3.0, https://kanjivg.tagaini.net
"""
import glob, json, os, re, sys, time, urllib.request

URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{}.svg"
KANJI = re.compile(r"[一-鿿㐀-䶿々]")
OUT = "strokes"


def wanted():
    ks = set()
    for f in glob.glob("lessons/*.json"):
        if f.endswith("index.json"):
            continue
        try:
            L = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for k in L.get("kanji_study") or []:
            ks.update(KANJI.findall(str(k.get("kanji", ""))))
        ks.update(KANJI.findall(str((L.get("kanji") or {}).get("kanji", ""))))
    return sorted(ks)


def parse(svg):
    paths = re.findall(r'<path[^>]*id="kvg:[0-9a-f]+-s(\d+)"[^>]*\sd="([^"]+)"', svg)
    if not paths:  # attribute order can differ
        paths = [(re.search(r'-s(\d+)"', p).group(1), re.search(r'\sd="([^"]+)"', p).group(1))
                 for p in re.findall(r"<path[^>]*>", svg) if re.search(r'id="kvg:[0-9a-f]+-s\d+"', p)]
    paths = [d for _, d in sorted(paths, key=lambda x: int(x[0]))]
    nums = [[float(x), float(y)] for x, y in
            re.findall(r'<text transform="matrix\(1 0 0 1 ([\d.]+) ([\d.]+)\)">\d+</text>', svg)]
    return {"d": paths, "n": nums}


def main():
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for k in wanted():
        h = format(ord(k), "05x")
        dst = os.path.join(OUT, h + ".json")
        if os.path.exists(dst):
            continue
        try:
            with urllib.request.urlopen(URL.format(h), timeout=30) as r:
                data = parse(r.read().decode("utf-8"))
        except Exception as e:
            print(f"{k}: {e}", file=sys.stderr)
            continue
        if not data["d"]:
            print(f"{k}: no strokes found", file=sys.stderr)
            continue
        json.dump(data, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        made += 1
        time.sleep(0.2)
    print(f"strokes: {made} new")


if __name__ == "__main__":
    main()
