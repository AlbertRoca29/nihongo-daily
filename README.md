# Nihongo Line

Daily Japanese micro-lessons for life in Japan, as an installable phone web app: one situation a day at N3 level, step by step, with toggleable furigana, audio, a vocab and kanji quiz and a short challenge. Star what you want to learn and it comes back in a quick spaced-repetition warm-up the next day.

Live: https://albertroca29.github.io/nihongo-daily/

## How it works
- Each lesson is `lessons/YYYY-MM-DD.json`, listed in `lessons/index.json`. The app shows every lesson up to today.
- A scheduled Claude task runs every morning at 7:41 (Madrid). It follows [`CLAUDE.md`](CLAUDE.md): it picks the least recently covered topic from [`topics.json`](topics.json), and about three times a month writes a lesson around a real recent news story instead.
- Each lesson teaches 8–10 words from its own sentences and 2 kanji: one from those words, one from the ordered N3 track in [`curriculum/n3-kanji.json`](curriculum/n3-kanji.json).
- Your stars and review schedule are saved in the app on your phone (browser storage), not in the repo.
- [`scripts/lessons.py`](scripts/lessons.py) keeps it safe: `status` says what today's run should do, `check` validates every lesson before a push, `bump` moves a lesson to a later day.

## Changing what you learn
- Add or edit topics in `topics.json`.
- Change how lessons are written in `CLAUDE.md`.
- Edits can be made straight from GitHub; the next morning's run picks them up.
