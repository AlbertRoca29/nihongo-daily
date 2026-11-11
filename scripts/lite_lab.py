#!/usr/bin/env python3
"""Flash vs Flash-Lite (Gemini 3.8 TTS): the same lines, same voices, both models.

  python3 scripts/lite_lab.py      # makes samples/lite/<scenario>_<model>.mp3 and samples/lite/results.json
Records each answer's token counts, so the cost per line is measured, not guessed. Needs GEMINI_API_KEY.
"""
import base64, json, os, subprocess, sys, time, urllib.error, urllib.request

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
API = "https://generativelanguage.googleapis.com/v1beta/models"
OUT = "samples/lite"
MODELS = {"flash": "gemini-3.8-flash-tts", "lite": "gemini-3.8-flash-lite-tts"}

# id, what it tests, voice, style, text (as sent to the engine: names in kana)
SCEN = [
    ("kenta", "Kansai-ben, fast and joking (designed voice)", "voice_fy8oio1yurjl", "joking, loud, fast",
     "セルフレジあるあるや。気にせんでええって。てか、たなかさんち農家やん？じゃがいもぐらいあるやろ"),
    ("hana", "84-year-old, old rural speech, slow storytelling", "ja-jp-csagent-4", "slow, gentle, amused, storytelling",
     "仕方ないから、あたしも一緒に降りて、坂をてくてく歩いて戻ったんじゃ。子どもの頃は、毎日この坂を歩かされたもんじゃよ。"),
    ("tanaka", "Gruff farmer, Nagano dialect, short", "ja-jp-podcaster-7", "gruff, dry, unhurried",
     "たかのはらのりんごは甘いずら。遠慮しないで食べな。"),
    ("ren", "Soft and shy, emotional", "ja-jp-storyteller-12", "soft, a little shy",
     "今日は、ありがとう。…また、会えるかな。"),
    ("sato", "Keigo, classroom announcement (designed voice)", "voice_q8ebkcksc90a", "polite, composed",
     "みなさん、今日から毎週火曜日に、アルちゃんが授業を手伝ってくれることになりました。今日は「もし〜たら」の質問タイムです。"),
    ("you", "Your voice, polite, numbers and times", "voice_c4fcfvc38ess", "friendly, relaxed",
     "わかりました！帰りのバスの便も少ないので、7時に出て、3時までに下りることにします。"),
    ("guest", "Guest from the voice library (59-year-old woman), long LINE message", "ja-jp-csagent-12", "warm, caring, a bit teasing",
     "この辺は出ることもあるよ。私も去年、道に迷っちゃって焦ったの。行き先はたなかさんに伝えておいてね。"),
    ("narrator", "Narrator for grammar examples (library voice)", "ja-jp-podcaster-10", "calm, clear, like a teacher reading an example",
     "電車で寝てしまって、終点まで行っちゃった。"),
    ("word", "One word alone, with two possible readings (こうよう / もみじ)", "ja-jp-podcaster-10", "clear, neutral",
     "紅葉"),
    ("strip", "Five vocab words in one request (to cut apart later)", "ja-jp-podcaster-10", "read each word clearly, with a long pause between words",
     "紅葉。　出発。　重ね着。　熊鈴。　絶対。"),
    ("slow", "Slow on purpose: a phrase read slowly for a learner", "voice_c4fcfvc38ess", "slowly and clearly, like reading to a language learner, with natural intonation",
     "無理しないで、疲れたら引き返したほうがいいよ。"),
    ("normal", "Same phrase at normal speed (to compare with slow)", "voice_c4fcfvc38ess", "friendly, relaxed",
     "無理しないで、疲れたら引き返したほうがいいよ。"),
]


def speak(text, voice, model, style):
    part = {"text": text, "speech_metadata": {"style": style}}
    body = {"contents": [{"role": "user", "parts": [part]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"voice": voice}}}}
    req = urllib.request.Request(f"{API}/{model}:generateContent", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "x-goog-api-key": KEY})
    for attempt in range(4):
        try:
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            secs = round(time.time() - t0, 1)
            p = d["candidates"][0]["content"]["parts"][0]["inlineData"]
            raw = base64.b64decode(p["data"])
            wav = "wav" in p.get("mimeType", "wav").lower()
            mp3 = subprocess.run(["ffmpeg", "-loglevel", "error"] + ([] if wav else ["-f", "s16le", "-ar", "24000", "-ac", "1"])
                                 + ["-i", "-", "-f", "mp3", "-b:a", "64k", "-"], input=raw, capture_output=True, check=True).stdout
            return mp3, d.get("usageMetadata", {}), secs, None
        except urllib.error.HTTPError as e:
            txt = e.read().decode()
            if e.code in (429, 500, 503) and attempt < 3 and "PerDay" not in txt and "per_day" not in txt:
                time.sleep(15 * (attempt + 1))
                continue
            return None, {}, 0, f"{e.code}: {txt[:300]}"
        except Exception as e:
            if attempt < 3:
                time.sleep(5)
                continue
            return None, {}, 0, str(e)[:300]


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out or 0), 2)


def main():
    if not KEY:
        sys.exit("GEMINI_API_KEY is not set.")
    os.makedirs(OUT, exist_ok=True)
    res_path = f"{OUT}/results.json"
    res = json.load(open(res_path, encoding="utf-8")) if os.path.exists(res_path) else {}
    for sid, what, voice, style, text in SCEN:
        for mk, model in MODELS.items():
            key, fn = f"{sid}_{mk}", f"{sid}_{mk}.mp3"
            if res.get(key, {}).get("file") and os.path.exists(f"{OUT}/{fn}"):
                continue
            audio, usage, secs, err = speak(text, voice, model, style)
            row = dict(scenario=sid, what=what, voice=voice, style=style, text=text, model=model, error=err, usage=usage, wait=secs)
            if audio:
                open(f"{OUT}/{fn}", "wb").write(audio)
                row.update(file=fn, seconds=dur(f"{OUT}/{fn}"))
            print(key, err or f"{row.get('seconds')}s {usage}")
            res[key] = row
            json.dump(res, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            time.sleep(2)


if __name__ == "__main__":
    main()
