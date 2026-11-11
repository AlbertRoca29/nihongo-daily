# 一日一歩 (Nihongo Line)

Daily Japanese micro-lessons for life in Japan, as an installable phone web app: one situation a day at N3 level, step by step, with toggleable furigana, audio, a vocab and kanji quiz and a short challenge. Star what you want to learn and it comes back in a quick spaced-repetition warm-up the next day.

Live: https://albertroca29.github.io/nihongo-daily/

## How it works
- Each lesson is `lessons/YYYY-MM-DD.json`, listed in `lessons/index.json`. The app shows every lesson up to today.
- A scheduled Claude task runs every morning at 7:25 (Madrid) and follows [`CLAUDE.md`](CLAUDE.md).
- Every lesson combines a **field** (what it's about: food, love, history, work…), a **function** (what you do with the language: narrate, compare, give opinions, report hearsay…) and a **format** (dialogue, LINE chat, story, or a real text to decode). All three rotate on their own, from [`topics.json`](topics.json); one day in three is a practical field.
- A recurring cast lives in a small mountain town in Nagano, defined in [`cast.json`](cast.json): Tanaka-san your host, Yuki in Tokyo, Kenta at the guesthouse, Sato-sensei and Mio at the high school, Hana-obāchan, Sōta, Ren, and the samurai Kurogane Hayato in the legends. Its `log` is the story so far, so the story moves on day by day. About one lesson in eight brings a one-off guest.
- Each lesson teaches one grammar point from the ordered N4 + N3 track in [`curriculum/grammar.json`](curriculum/grammar.json), 8–10 words from its own sentences, and 2 kanji: one from those words, one from the N3 track in [`curriculum/n3-kanji.json`](curriculum/n3-kanji.json). About three times a month it's built around a real recent news story instead.
- The app opens on a **home screen**: today's lesson first (who it's with, grammar, kanji, steps, or where you left off), then your study streak (a day counts when you finish a lesson or review cards), and tiles for Review (due cards any time, or a practice round), Saved cards, Kanji learned and All lessons. Earlier lessons show their Japanese title, date and who's in them; The gear on the top right opens Settings, with a live preview: theme, font for titles and big kanji, text font, English letters, furigana. The app title is 一日一歩. Fonts load from Google Fonts only when chosen. New features go in as new tiles.
- Each lesson: the scene (a LINE chat plays out one message per Next; ↑ sends your line), a listening activity, the 5 phrases, grammar, words, kanji, and a challenge (one tap most days, free writing on Tuesdays and Saturdays, always skippable). Once a month, on the first Saturday, a JLPT-style mock exam.
- Everything a lesson teaches goes into a review deck (☆ = more often): audio-only, reading, fill-the-gap and English→Japanese cards, spaced by how well you know each one (at most 8 new and 40 reviews a day).
- Audio: every sound is a Gemini 3.8 Flash-Lite voice (颯太: VOICEVOX), including single words for review, slow versions and a radio track per lesson. A ledger in `audio/_ledger.json` caps spending at $3 a month; past that, Google's free Chirp voice.
- Furigana can be adaptive: it disappears on N5/N4 kanji whose reading you got right 3 times in a row.
- Look (日の丸): white cards on near-white paper (black in dark mode), black ink and one red sun on today's lesson card. Red only marks three things: the sun, today, and words you can tap (a thin faint underline). Your own chat messages are a light red tint.
- Works offline: the last 7 lessons and their audio are kept on the phone. Fonts are self-hosted in `fonts/`.
- Your stars, review schedule and streak are saved in the app on your phone (browser storage), not in the repo. Settings → Your data exports a backup.
- [`scripts/lessons.py`](scripts/lessons.py) keeps it safe: `status` says what today's run should do, `check` validates every lesson before a push, `bump` moves a lesson to a later day.

## Changing what you learn
- Fields, angles, functions and formats: `topics.json`.
- Characters, the world and the story so far: `cast.json`.
- How lessons are written: `CLAUDE.md`.
- Edits can be made straight from GitHub; the next morning's run picks them up.

## Page rules (for anyone changing the app)

He reads on a phone, so every lesson step follows these:
1. **One page ≈ one screen.** A step fits without scrolling (a little over is fine). Anything more goes behind a tap.
2. **Japanese first, English on tap.** English shows only where he needs it to act (a quiz question, the task); translations and notes open on tap.
3. **One thing per card.** A card has one job: a word, a rule, a question.
4. **One way forward.** The big button at the bottom is the only "next". It walks a step's own pages too (each chat message, each phrase, each grammar tab, each quiz question, then the quiz after the word list or kanji) before going to the next step; Back does the reverse. Never put a second "Next…" button on the page.
5. **No instructions on screen.** If a control needs a sentence explaining it, redesign the control. No "tap here to…", no mode pickers, no hint lines under content.
6. **Every option earns its place.** Only show a button when tapping it does something he'd want on that screen. Skipping is the bottom button, not a separate "skip". Rare settings live in Settings, not in the lesson.
7. **One tap, one meaning, everywhere.** Tapping a Japanese line always shows its English (and ▶ 🐢 ☆ for that line). No double-taps or long-presses. Toggles show their state in their look (furigana: struck through when off).
Whole sentences only: never show half a line of the lesson.
