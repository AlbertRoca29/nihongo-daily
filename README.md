# Nihongo Line

Daily Japanese micro-lessons for life in Japan, as an installable phone web app: one situation a day, step by step, with toggleable furigana, audio and a short challenge.

Live: https://albertroca29.github.io/nihongo-daily/

## How it works
- Each lesson is `lessons/YYYY-MM-DD.json`, listed in `lessons/index.json`. The app shows every lesson up to today.
- A scheduled Claude task runs every morning at 7:41 (Madrid). It follows [`CLAUDE.md`](CLAUDE.md): it picks the least recently covered topic from [`topics.json`](topics.json), and about three times a month writes a lesson around a real recent news story instead.
- [`scripts/lessons.py`](scripts/lessons.py) keeps it safe: `status` says what today's run should do, `check` validates every lesson before a push, `bump` moves a lesson to a later day.

## Changing what you learn
- Add or edit topics in `topics.json`.
- Change how lessons are written in `CLAUDE.md`.
- Edits can be made straight from GitHub; the next morning's run picks them up.
