# Writing lessons for Nihongo Line

You add one short Japanese lesson per day to this app. The learner's level and goals come from whoever runs you (the task prompt). If none is given, assume a JLPT N4–N3 learner preparing to volunteer and travel in Japan.

Only touch `lessons/` and, when a new topic is truly needed, `topics.json`. Never change `index.html`, `sw.js`, the manifest or icons unless the user asks.

## The daily run

1. `python3 scripts/lessons.py status` and follow its DECISION line. It tells you whether today's lesson already exists, whether a news lesson is due, and which topics were used least recently.
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
| `news` | `true` only on news lessons |

## Furigana markup

Every Japanese string (except `kanji.kanji` and `kanji.reading`) marks each kanji word with its reading: `{漢字|かんじ}`.
- Okurigana stays outside: `{乗|の}り{換|か}え`, `{行|い}きます`.
- Readings are in kana. Kana, katakana, numbers and Latin letters need no markup.
- Counters can be one block: `{3日分|みっかぶん}`.

## Writing quality

- Natural spoken Japanese, the kind people really say in that situation, not textbook sentences.
- Notes explain nuance in one line: when to use it, what you'll hear back, a common mistake.
- English is plain and short. The whole lesson should take under 10 minutes.
