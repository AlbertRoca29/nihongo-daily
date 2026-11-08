# Writing lessons for Nihongo Line

You add one short Japanese lesson per day to this app. The learner is studying for JLPT N3 and, in the story, lives for a few months in a small Japanese mountain town (see `cast.json`). His personal profile comes from the task prompt: it is private, never write it into the repo (lessons may use his name). He wants to learn **all of Japanese**, not only survival phrases: practical situations are one day in three, the rest covers every part of life, feelings, culture and ideas. The task prompt may add goals; follow it if it does.

Only touch `lessons/` and `cast.json` (the story log), and `topics.json` when a new angle is truly needed. Never change `index.html`, `sw.js`, the manifest, icons or `curriculum/` unless the user asks.

Write **only today's lesson**. Never write lessons for future dates: each lesson follows the kanji and grammar tracks, the story log, and avoids words already taught, so it must be written on the day.

## Level: N3, without assuming it's known

- Pitched at N3: N3 grammar and vocabulary used naturally.
- Assume N5 is known and N4 mostly known. Treat every N3 word and kanji as new: furigana everywhere, explained the first time.
- Keep it short. N3 does not mean long or formal sentences.

## The daily run

1. `python3 scripts/lessons.py status` and follow its DECISION line. It gives: whether today's lesson exists, news and review state, today's **field**, **function** and **format**, the next **grammar** point, the next N3 kanji, which characters appeared when, whether a **guest** is due, the **story so far**, canon facts, and every kanji and word already taught.
2. Read `cast.json` (the characters and world) and the last ~5 lessons, so you continue the story and don't repeat phrases.
3. Write the lesson (rules below) as `lessons/YYYY-MM-DD.json`. Add `{"id", "topic", "category", "function", "format"}` to `lessons/index.json`, keeping it sorted.
4. Append today's entry to `log` in `cast.json`: `{"date", "cast": [ids], "summary": "one or two sentences of what happened", "new_facts": ["anything you invented that must stay true"]}`. Add `"guest": "Name (role)"` when there was one.
5. `python3 scripts/lessons.py check` must print `OK`. Never push while it fails: a broken `index.json` takes down the whole app.
6. Commit `Lesson YYYY-MM-DD: <topic>` and push to `master`. If the push is rejected, `git pull --rebase origin master` and push again.
7. Report the topic, field, function, format, grammar point and who was in it.

If today's lesson already exists and no news is due, write nothing.

## What a lesson is about: field × function × format

Defined in `topics.json`. Status picks the least recently used of each; follow it.
- **Field** (`category`): the vocabulary world, e.g. `love-relationships`, `history-samurai`, `health-body`. Every third regular lesson is a practical field (status says "PRACTICAL day"). Each field lists `angles`; pick one not used recently, or a new one in the same spirit.
- **Function** (`function`): what you do with the language: narrating, comparing, giving opinions, reporting hearsay, keigo, etc. The phrases and dialogue must really practise it.
- **Format** (`format`): `dialogue`, `line`, `story` or `text` (rules below). Status suggests one; you may pick another if the field clearly suits it better (a legend → story), never the same as yesterday.
- **Grammar**: the next point on `curriculum/grammar.json` (status names it). The lesson must use it naturally in at least one or two lines. Combine it with the function; they don't have to be the same thing.

Make the combination feel like one real moment, not a checklist: "Yuki tells you on LINE that she heard her boss is quitting" (money-work × hearsay × line × 〜らしい).

## The cast and the story

`cast.json` is canon. Read each character's `about`, `speech`, `fixed` and the log before writing.
- Pick 1–2 characters whose `fits` include today's field (or who make sense in the scene). Rotate: prefer someone who hasn't appeared for a while. Respect where people are (Yuki is in Tokyo, Ren in Nagano city, Sōta only on weekends and school holidays, Hayato only in stories).
- Each character speaks in their own voice (Kenta in Kansai-ben, Tanaka-san with a bit of Nagano dialect, Mio with teen slang, Sato-sensei in keigo, Hayato in drama samurai speech). When a line uses dialect, slang or archaic forms, the `register` says so (`dialect`, `slang`, `archaic`) and the `note` gives the standard Japanese. Never let the learner's own lines use archaic speech.
- **Continuity**: the story moves forward with the real calendar. Small things carry over (a promise made, a cold Tanaka-san had, Ren's last message). Never contradict the log or `new_facts`; when you invent a fact (a name, a pet, a place) add it to `new_facts`.
- **Ren's storyline** follows his `arc` beats in order, one beat every few appearances, no faster. It's warm and real, like a TV drama: feelings, shyness, misunderstandings, being discreet in a small town. Nothing sexual.
- **Mio** (16): always school or group settings; no romance topics involving the learner.
- **Guests**: when status says a guest is due, invent a new one-off character (name, age, one clear speech style) who fits the field, and put `"guest": {"name", "name_jp", "role"}` in the lesson. Never reuse a guest's name.
- Portraits: the app shows a chibi portrait for each cast member, Keiko and You (`icons/cast/<id>.svg`), and in LINE chats their LINE profile picture instead, a selfie in their world (`icons/line/<id>.svg`). Both are drawn by `scripts/portraits.py` (on top of the base drawings in `scripts/chibi.py`). Both are matched by the speaker name, so always use the character's exact `name` as `speaker` (`Tanaka-san`, `Hana-obāchan`, `Keiko`). Guests and staff get their initial.
- The learner is "You" (`"me": true`). Characters address him by the name in the task prompt, as described in `world.you`.

## Formats

All four keep their lines in `dialogue`, so vocab `src` (`d0`, `d1`…) works the same.

| Format | Lines | Rules |
|---|---|---|
| `dialogue` | 4–6 | Spoken conversation. `speaker` is the character's `name` or `You`; `"me": true` on the learner's lines. |
| `line` | 4–8 | A LINE thread. Short written messages, casual written style (abbreviations, ｗ, emoji words, stamps written as （スタンプ：…）). Optional `time` per line (`"21:04"`). At least one `"me": true`. |
| `story` | 4–6 | One or two narrators tell something: a memory, a legend, yesterday's disaster. Each line is 1–2 sentences, plain or です/ます past narration. No `me` needed. |
| `text` | 4–8 | A written text to decode: notice, menu, flyer, school letter, museum panel, shop sign, social media post, email. `speaker` is the part's label (`Title`, `Rule 1`, `Price`, `Note`). Add `"text_title"` (shown as the header, with furigana markup). No `me` needed. |

## News lessons

About three a month, on no fixed day. The status line decides:
- **OPTIONAL** (8–9 days since the last one): write a news lesson only if you find a good story; otherwise the regular lesson.
- **DUE** (10+ days): always write one. If a regular lesson was already written for today, run `python3 scripts/lessons.py bump <today>` first.

Rules for the story:
- Real Japan news from the **last 10 days**, found with web search in Japanese and English.
- Interesting for someone living in Japan: daily life, travel, prices, seasons, culture, technology, sport, society, rules. Nothing tragic or graphic.
- Confirmed by at least **two reliable sources** (NHK, Kyodo, Jiji, Asahi, Mainichi, Yomiuri, Japan Times, Nippon.com, official sites). Fetch them; get dates, numbers and names exactly right. Never invent facts.
- `"news": true`, `"category": "news"`, topic starts with `News:`. `context` summarises the story in 2–3 English sentences with its date and ends with `Source: <outlet>`.
- It still has a function, format and the next grammar point. A cast member can bring up the news (Kenta reading it at reception, Yuki on LINE), or use the `text` format for a simplified article.

## Review lessons

When status allows: `"category": "review"`, a new scene with the cast that reuses the most useful phrases from recent lessons. Its `grammar` section revisits one point already taught (the check requires that). Vocab and kanji are still new.

## Lesson format

`lessons/2026-11-02.json` shows the old core fields; new lessons add `function`, `format`, `cast` and `grammar` (the field goes in `category`). Fields:

| Field | Content |
|---|---|
| `topic` | Short English name (same as in index.json), e.g. `Yuki's terrible date` |
| `category` | The field id (or `news` / `review`), same as in index.json |
| `function` | A function id from `topics.json` |
| `format` | `dialogue`, `line`, `story` or `text` |
| `cast` | List of character ids from `cast.json` |
| `guest` | Optional `{name, name_jp, role}` |
| `title_jp` | Short Japanese title |
| `context` | 1–2 English sentences setting today's scene in the story |
| `phrases` | Exactly 5 × `{jp, en, register, note?}`; register is `polite`, `casual`, `neutral`, `dialect`, `slang` or `archaic`. The mix follows the scene: casual with friends, polite with strangers and at work |
| `dialogue_setting` | One English line: where/how this happens |
| `dialogue` | The main text in today's format (see Formats) |
| `text_title` | Only for `text` format |
| `grammar` | Today's grammar point (see below) |
| `kanji` | `{kanji, reading, romaji, meaning, where, breakdown, related?}`: a word you'd really see written in this world (sign, label, menu, scroll, app screen). `breakdown`: one line on how its kanji build the meaning, e.g. `{既読|きどく}: 既 already + 読 read → 'already read'.` (the app also shows each kanji's dictionary meaning; for a single kanji, say what its parts hint at) |
| `tip` | `{mark, title, body}`: `mark` is one kanji shown as a stamp; body is 2–4 sentences textbooks don't teach |
| `challenge` | `{prompt, hint, model_answer, explanation}`: a short task to answer in Japanese, ideally replying to a character. `explanation`: 2–3 English sentences (furigana markup allowed) that walk through the model answer: which grammar does what, why that word or form, the register. Shown with the model answer |
| `vocab` | 8–10 words from today's phrases and main text |
| `kanji_study` | Exactly 2 kanji to learn |
| `extras` | Optional bonus sections `{title, title_jp, intro, items: [{jp, en, note?}]}`; 2–3 of them |
| `news` | `true` only on news lessons |

## Grammar

`grammar`: `{id, pattern, level, meaning, form, explanation, src, examples, quiz}`
- `id`, `pattern`, `level`, `meaning`: from `curriculum/grammar.json` (the `pattern` may get furigana markup).
- `form`: how to build it, one rule per case, rules separated by ` · ` (space, middle dot, space). Write each rule as `label: rule (example, example)`: the app shows the label as a chip, the rule in bold and each example on its own line under it. E.g. `う-verbs: -a + れる ({頼|たの}む → {頼|たの}まれる, {怒|おこ}る → {怒|おこ}られる) · る-verbs: + られる ({見|み}る → {見|み}られる) · する → される · {来|く}る → {来|こ}られる`. Short labels (`う-verbs`, `い-adj`, `noun`, `{動詞|どうし}ない{形|けい}`); an irregular can be just `する → される` (shown as chip + result). With a single rule the label can go: `{動詞|どうし}た{形|けい} + ばかり ({食|た}べたばかり)`. Examples are short forms, 1–3 per rule, no full sentences (those go in `examples`).
- `explanation`: 2–3 plain English sentences: when people use it, the nuance, the classic mistake, how it differs from the similar point learners confuse it with.
- `src`: the lines of today's lesson that use it (`["d2", "p1"]`), at least one.
- `examples`: 1–3 extra `{jp, en}` sentences in other situations, so the pattern isn't tied to one scene.
- `quiz`: `{question, en, options, explain}`. `question` is a Japanese sentence with `＿＿` where the answer goes; `en` its translation; `options` 4 forms, **the right one first** (the app shuffles), the wrong ones plausible (wrong conjugation, the similar pattern); `explain` one line on why.
- Never teach the same grammar point twice (the check refuses it), except in review lessons.

## Vocab

The learner stars the words he wants; starred words come back in the app's warm-up, inside their sentence. So every word must come from a real line of today's lesson.

Each item: `{jp, reading, en, level, src, surface, note?}`
- `jp`: dictionary form with furigana, e.g. `{渡|わた}る`. `reading`: the whole word in kana.
- `level`: `N5`–`N1`. Mostly `N3` (at least half), the rest `N4`. `N5` only if truly key. An `N2` word is fine when the field needs it (history, feelings), at most one.
- `src`: the line it comes from, `p0`–`p4` (phrases) or `d0`… (main text lines).
- `surface`: the exact form in that line without furigana, e.g. `渡った`. The check verifies it's there.
- Never repeat a word taught in an earlier lesson (status lists them; the check refuses repeats). Don't pick archaic words as vocab.

## Kanji study

Exactly 2 kanji, recognition only (reading and meaning):
- `track: "lesson"`: a kanji from one of today's vocab words, not taught before. Prefer N3 kanji.
- `track: "n3"`: the next kanji on the N3 track (status names it). If it's very awkward for today, you may take one of the next five it lists.

Each: `{kanji, track, on, kun, meaning, words, decoys}`
- `on` in katakana, `kun` in hiragana with okurigana in brackets (`ま(がる)`); several readings joined with `・`. Leave one empty only if the kanji truly has none in common use.
- `words`: 2–3 common words using it `{jp, reading, en}`. Put the most useful first: the quiz asks its reading. Use today's word for the `lesson` kanji.
- `decoys`: `{meanings: [3 wrong meanings], readings: [3 wrong readings of words[0]]}`. Make them plausible.
- Never teach a kanji twice (the check refuses repeats).

## Audio (voices)

A GitHub automation reads every line with Google voices after each push (`scripts/tts.py`, casting in `voices.json`). Don't run it yourself; just give it what it needs:
- Cast members, `You` and `text`-format parts get their voice automatically. A `text` written by a character (Sōta's school essay, Yuki's blog post, a note from Hana) is read in their voice: add `"reader": "<cast id>"` to the lesson (or `"reader": "Keiko"` for a side character in `others`). Without it, the narrator reads it.
- Any other speaker (a guest, `Staff`, a shopkeeper) needs a gender: `"voice": "f"` or `"m"` on the guest object, or on each of their lines. Without it they get the narrator's voice.
- A side character who will come back (like Keiko) gets a fixed voice: add them to `others` in `voices.json` with a voice from the `pool` (remove it from the pool).
- An entry in `voices.json` is either a plain voice name (Chirp 3 HD) or a directed voice `{"voice", "model", "prompt"}`, where `prompt` describes the person (age, mood, accent). Don't change the casting unless the user asks.
- Names of people and places are read from their furigana automatically. If a line has another word the engine might misread (a rare reading, 今日 meaning こんにち), add `"tts"` to that line: the whole line as it should be read, with that word in kana.

## Furigana markup

Every Japanese string (except `kanji.kanji` and `kanji.reading`) marks each kanji word with its reading: `{漢字|かんじ}`.
- Okurigana stays outside: `{乗|の}り{換|か}え`, `{行|い}きます`.
- Readings are in kana. Kana, katakana, numbers and Latin letters need no markup.
- Counters can be one block: `{3日分|みっかぶん}`.

## Hard-word glosses (tap to see the meaning)

Words the learner probably doesn't know get two more parts, the meaning and how common the word is: `{遠慮|えんりょ|holding back, being reserved|3}`. The app underlines them and shows the meaning and the commonness when he taps. Kana-only words use an empty reading: `{どんどん||one after another, freely|3}`.
- **Commonness** (last part, required on every gloss): how often a Japanese person really says or writes this word in everyday life. `4` everyday, you'll hear it all the time (困る, 確かに, 結局) · `3` common, comes up regularly (景色, 遠慮, 恋人) · `2` occasional: specific situations, workplaces or more formal/written (停留所, 祖父, 尊敬語-only forms) · `1` rare: regional dialect, old-fashioned, technical or very formal (ずら, 乗り越す, 年齢確認). Rate the word in the sense used in the line, not the kanji. Be honest: not everything is 3.
- **Gloss generously.** The learner should never meet a word he can't look up. Gloss every N3, N2 or N1 word, every vocab word, every dialect, slang or archaic form, set expressions whose meaning isn't obvious from the parts, rare place or dish names, and also the less common N4 words (e.g. {畑|はたけ}, {坂|さか}, {箸|はし}, {整理券|せいりけん}, {宅急便|たっきゅうびん}, {千円札|せんえんさつ}). Rule of thumb: if someone who knows N5 and everyday N4 might pause on it, gloss it; a missing gloss is worse than an extra one. **Phrase cards** (`phrases[].jp`) get the same care as the main text. **Don't gloss** N5 or everyday N4 words ({電車|でんしゃ}, {友達|ともだち}, {大丈夫|だいじょうぶ}), names of the cast, or grammar endings (the grammar step teaches those).
- Before finishing, reread every phrase and main-text line word by word and ask of each kanji word and katakana loanword: would he know this? If not, gloss it.
- Gloss every occurrence, also when the word is in today's vocab (the popover then offers the vocab note and the ☆).
- Where: `phrases[].jp`, `dialogue[].jp`, `text_title`, `grammar.examples`, `grammar.quiz.question`, `challenge.prompt`/`model_answer`, `extras` items. **Never** in `vocab`, `kanji_study`, `kanji`, `grammar.pattern`, `grammar.form` or quiz `options` (the check refuses it).
- **The block holds the whole word**, okurigana and conjugation included, so the underline covers all of it: write the full reading too, and the app puts furigana over the kanji only. `{寂しくない|さびしくない|lonely|3}`, `{頼まれて|たのまれて|to ask (a favour)|3}`, `{落ち着く|おちつく|to calm down|4}` (one block, not `{落|お}ち{着|つ|…}く`), `{お腹|おなか|belly|4}`. Never stop at the kanji: `{寂|さび|lonely}しい` underlines only 寂 (the check refuses it). Include the verb's own ending (て/た/ない/ます/れる/られる/たい forms); leave out separate words after it (いる, しまう, もらう, particles, です): `{温めて|あたためて|to heat up|3}もらえますか`. Suru-nouns keep する outside: `{遠慮|えんりょ|holding back|3}しない`. Give the dictionary meaning.
- The meaning is short plain English (2–6 words), the sense used in this line; for dialect or slang add the standard form: `{ずら||(Nagano dialect) = でしょう, right?|1}`. No `{`, `}` or `|` inside it.
- The check needs at least 6 glosses across phrases and the main text (most lessons have 10–20), and every vocab word must be glossed in the line it comes from.

## Writing quality

- Natural Japanese, the kind these people really say or write, not textbook sentences. Each character sounds like themselves.
- Notes explain nuance in one line: when to use it, what you'll hear back, a common mistake, the standard form of dialect or slang.
- English is plain and short. Core lesson under 12 minutes; extras are on top.
- Vary everything: openings, scenes, who speaks first, the kind of challenge. If it feels like yesterday's lesson with new nouns, change the angle.
