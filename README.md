# Nihongo Line

Daily Japanese micro-lessons for life in Japan, as an installable phone web app: one situation a day at N3 level, step by step, with toggleable furigana, audio, a vocab and kanji quiz and a short challenge. Star what you want to learn and it comes back in a quick spaced-repetition warm-up the next day.

Live: https://albertroca29.github.io/nihongo-daily/

## How it works
- Each lesson is `lessons/YYYY-MM-DD.json`, listed in `lessons/index.json`. The app shows every lesson up to today.
- A scheduled Claude task runs every morning at 7:25 (Madrid) and follows [`CLAUDE.md`](CLAUDE.md).
- Every lesson combines a **field** (what it's about: food, love, history, work…), a **function** (what you do with the language: narrate, compare, give opinions, report hearsay…) and a **format** (dialogue, LINE chat, story, or a real text to decode). All three rotate on their own, from [`topics.json`](topics.json); one day in three is a practical field.
- A recurring cast lives in a small mountain town in Nagano, defined in [`cast.json`](cast.json): Tanaka-san your host, Yuki in Tokyo, Kenta at the guesthouse, Sato-sensei and Mio at the high school, Hana-obāchan, Sōta, Ren, and the samurai Kurogane Hayato in the legends. Its `log` is the story so far, so the story moves on day by day. About one lesson in eight brings a one-off guest.
- Each lesson teaches one grammar point from the ordered N4 + N3 track in [`curriculum/grammar.json`](curriculum/grammar.json), 8–10 words from its own sentences, and 2 kanji: one from those words, one from the N3 track in [`curriculum/n3-kanji.json`](curriculum/n3-kanji.json). About three times a month it's built around a real recent news story instead.
- The app opens on a **home screen**: your study streak (a day counts when you finish a lesson or review cards), today's lesson, and tiles for Review (due cards any time, or a practice round), Saved cards, Kanji learned and All lessons. Earlier lessons show their Japanese title, date and who's in them; The gear on the top right opens Settings (theme, app title, title and text fonts, furigana). New features go in as new tiles.
- Your stars, review schedule and streak are saved in the app on your phone (browser storage), not in the repo.
- [`scripts/lessons.py`](scripts/lessons.py) keeps it safe: `status` says what today's run should do, `check` validates every lesson before a push, `bump` moves a lesson to a later day.

## Changing what you learn
- Fields, angles, functions and formats: `topics.json`.
- Characters, the world and the story so far: `cast.json`.
- How lessons are written: `CLAUDE.md`.
- Edits can be made straight from GitHub; the next morning's run picks them up.
