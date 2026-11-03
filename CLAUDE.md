# Writing lessons for Nihongo Line

You add one short Japanese lesson per day to this app. The learner's goals come from whoever runs you (the task prompt). If none is given, assume a learner studying for JLPT N3 who is preparing to volunteer and travel in Japan.

Only touch `lessons/` and, when a new topic is truly needed, `topics.json`. Never change `index.html`, `sw.js`, the manifest, icons or `curriculum/` unless the user asks.

Write **only today's lesson**. Never write lessons for future dates: each lesson follows the kanji track and avoids words already taught, so it must be written on the day.

## Level: N3, without assuming it's known

- Lessons are pitched at N3: N3 grammar and vocabulary used naturally in the phrases and dialogue.
- Assume N5 is known and N4 mostly known. Treat every N3 word and kanji as new: it gets furigana everywhere and is explained the first time.
- Keep it short and spoken. N3 does not mean long or formal sentences.

## The daily run

1. `python3 scripts/lessons.py status` and follow its DECISION line. It tells you whether today's lesson already exists, whether a news lesson is due, which topics were used least recently, the next kanji on the N3 track, and every kanji and word already taught.
2. Write the lesson (rules below) as `lessons/YYYY-MM-DD.json` and add `{"id", "topic", "category"}` to `lessons/index.json`, keeping it sorted.
3. `python3 scripts/lessons.py check` must print `OK`. Never push while it fails: a broken `index.json` takes down the whole app.
4. Commit `Lesson YYYY-MM-DD: <topic>` and push to `master`. If the push is rejected, `git pull --rebase origin master` and push again.
5. Report the day's topic, and whether it was a news lesson.

If today's lesson already exists and no news is due, write nothing.

## Choosing the topic

- Pick the least recently used topic from `topics.json` (status lists them). Take a fresh angle if it was covered before: new situation, new phrases, new sign kanji. Read the last ~10 lessons so you don't repeat phrases.
- `review`: only when status says it's allowed. Mix the most useful phrases from recent lessons into a new situation.
- A new topic is fine if it's clearly useful for life in Japan: add it to `topics.json` with a short kebab-case id.

## News lessons

About three a month, on no fixed day. The status line decides:
- **OPTIONAL** (8–9 days since the last one): write a news lesson only if you find a good story; otherwise a regular lesson.
- **DUE** (10+ days): always write one. If a regular lesson was already written for today, run `python3 scripts/lessons.py bump <today>` first: it moves that lesson to the first free day after the last lesson, so nothing is lost.

Rules for the story:
- Real Japan news from the **last 10 days**, found with web search in Japanese and English. Never pre-write news lessons for future dates.
- Useful or interesting for someone about to live and travel in Japan: daily life, travel, transport, prices, seasons, culture, safety, rules for visitors. Nothing tragic or graphic.
- Confirmed by at least **two reliable sources** (NHK, Kyodo, Jiji, Asahi, Mainichi, Yomiuri, Japan Times, Nippon.com, official sites). Fetch them; get dates, numbers and names exactly right. Never invent facts.
- `"news": true`, `"category": "news"`, topic starts with `News:`. `context` summarises the story in 2–3 English sentences with its date and ends with `Source: <outlet>`. Phrases, dialogue, kanji, tip and challenge all relate to the story.

## Lesson format

Follow `lessons/2026-11-02.json` as the reference. Fields:

| Field | Content |
|---|---|
| `topic` | Short English name (same as in index.json) |
| `category` | A topic id from `topics.json` (same as in index.json) |
| `title_jp` | Short Japanese title |
| `context` | 1–2 English sentences setting the scene for the trip |
| `phrases` | Exactly 5 × `{jp, en, register, note?}`; register is `polite`, `casual` or `neutral`. Usually 4 polite + 1 casual |
| `dialogue_setting` | One English line: where the dialogue happens |
| `dialogue` | 4–6 × `{speaker, jp, en, me?}`; `"me": true` on the learner's lines; speaker is `You` or a short role (`Staff`, `Host`, `Friend`) |
| `kanji` | `{kanji, reading, romaji, meaning, where, related?}`: a word seen on real signs or labels for this topic |
| `tip` | `{mark, title, body}`: `mark` is one kanji shown as a stamp; body is 2–4 sentences textbooks don't teach |
| `challenge` | `{prompt, hint, model_answer}`: a short task to answer in Japanese |
| `vocab` | 8–10 words to learn, taken from today's phrases and dialogue (see below) |
| `kanji_study` | Exactly 2 kanji to learn (see below) |
| `extras` | Optional bonus sections `{title, title_jp, intro, items: [{jp, en, note?}]}`; 2–3 of them, for the learner who wants more |
| `news` | `true` only on news lessons |

## Vocab

The learner stars the words he wants; starred words come back in the app's warm-up, inside their sentence. So every word must come from a real line of today's lesson.

Each item: `{jp, reading, en, level, src, surface, note?}`
- `jp`: dictionary form with furigana, e.g. `{渡|わた}る`. `reading`: the whole word in kana.
- `level`: `N5`–`N1`. Mostly `N3` (at least half), the rest `N4`. `N5` only if truly key.
- `src`: the line it comes from, `p0`–`p4` (phrases) or `d0`… (dialogue lines).
- `surface`: the exact form in that line without furigana, e.g. `渡った`. The check verifies it's there.
- Never repeat a word taught in an earlier lesson (status lists them; the check refuses repeats).

## Kanji study

Exactly 2 kanji, recognition only (reading and meaning):
- `track: "lesson"`: a kanji from one of today's vocab words, not taught before. Prefer N3 kanji.
- `track: "n3"`: the next kanji on the N3 track (status names it). If it's very awkward for today, you may take one of the next five it lists.

Each: `{kanji, track, on, kun, meaning, words, decoys}`
- `on` in katakana, `kun` in hiragana with okurigana in brackets (`ま(がる)`); several readings joined with `・`. Leave one empty only if the kanji truly has none in common use.
- `words`: 2–3 common words using it `{jp, reading, en}`. Put the most useful first: the quiz asks its reading. Use today's word for the `lesson` kanji.
- `decoys`: `{meanings: [3 wrong meanings], readings: [3 wrong readings of words[0]]}`. Make them plausible: related meanings, readings a learner might really guess (wrong voicing, long vs short vowel, the other on-reading).
- Never teach a kanji twice (the check refuses repeats).

## Furigana markup

Every Japanese string (except `kanji.kanji` and `kanji.reading`) marks each kanji word with its reading: `{漢字|かんじ}`.
- Okurigana stays outside: `{乗|の}り{換|か}え`, `{行|い}きます`.
- Readings are in kana. Kana, katakana, numbers and Latin letters need no markup.
- Counters can be one block: `{3日分|みっかぶん}`.

## Writing quality

- Natural spoken Japanese, the kind people really say in that situation, not textbook sentences.
- Notes explain nuance in one line: when to use it, what you'll hear back, a common mistake.
- English is plain and short. Core lesson (warm-up, phrases, dialogue, sign kanji, tip, words, kanji quiz, challenge) under 10 minutes; extras are on top.
