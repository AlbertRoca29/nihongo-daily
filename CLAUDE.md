# Writing lessons for Nihongo Line

You add one short Japanese lesson per day to this app. The learner is studying for JLPT N3 and, in the story, lives for a few months in a small Japanese mountain town (see `cast.json`). His personal profile comes from the task prompt: it is private, never write it into the repo (lessons may use his name). He wants to learn **all of Japanese**, not only survival phrases: practical situations are one day in three, the rest covers every part of life, feelings, culture and ideas. The task prompt may add goals; follow it if it does.

Only touch `lessons/` and `cast.json` (the story log), and `topics.json` when a new angle is truly needed. Never change `index.html`, `sw.js`, the manifest, icons, `stickers.json` or `curriculum/` unless the user asks.

Write **only today's lesson**. Never write lessons for future dates: each lesson follows the kanji and grammar tracks, the story log, and avoids words already taught, so it must be written on the day.

## Level: N3, without assuming it's known

- Pitched at N3: N3 grammar and vocabulary used naturally.
- Assume N5 is known and N4 mostly known. Treat every N3 word and kanji as new: furigana everywhere, explained the first time.
- Keep it short. N3 does not mean long or formal sentences.

## Keep it short (the check enforces this)

He reads on a phone, often tired. Less text is better than more explanation. Limits count characters without furigana:
- **LINE bubble ≤ 40 字**. A longer message becomes two or three bubbles from the same person (same `time` is fine), the way people really type. Spoken line ≤ 50 字, story or text line ≤ 60 字.
- **`scene` ≤ 30 words**: one English line for the start page.
- **Vocab `note` ≤ 20 words**, **grammar `explanation` ≤ 50 words**, **tip** 2–3 sentences.
- Cut filler, not the learning: keep the vocab, the grammar lines and the story beat; drop repeated greetings, side remarks and second explanations.

## The daily run

1. `python3 scripts/lessons.py status` and follow its DECISION line. It gives: whether today's lesson exists, news and review state, today's **field**, **function** and **format**, the next **grammar** point, the next N3 kanji, which characters appeared when, whether a **guest** is due, the **story so far**, canon facts, and every kanji and word already taught.
2. Read `cast.json` (the characters and world) and the last ~5 lessons, so you continue the story and don't repeat phrases.
3. Write the lesson (rules below) as `lessons/YYYY-MM-DD.json`. Add `{"id", "topic", "category", "function", "format"}` to `lessons/index.json`, keeping it sorted.
4. Append today's entry to `log` in `cast.json` (and update a character's `status` if something changed for them): `{"date", "cast": [ids], "summary": "one or two sentences of what happened", "new_facts": ["anything you invented that must stay true"]}`. Add `"guest": "Name (role)"` when there was one.
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
- **Who speaks**: every line of a `dialogue`, `line` or `story` has `"who"`: a character id from cast.json (`cast` or `others`, e.g. `"kenta"`, `"keiko"`), `"you"` for the learner, `"guest"` for today's guest, or `"extra"` for staff, a shopkeeper, a passer-by (with `"voice": "f"` or `"m"`). Voice, portrait and LINE icon all come from `who`.
- **Speaker labels are Japanese**: `speaker` is exactly the character's `name` in cast.json (`田中さん`, `健太`, `ハナおばあちゃん`, `恵子さん`), the guest's `name`, or a Japanese label for extras (`店員さん`, `駅員さん`). Never romaji. The learner's lines: `"speaker": "アルちゃん", "who": "you", "me": true`. The check refuses anything else.
- Portraits: chibi portraits (`icons/cast/<id>.svg`) and LINE profile pictures (`icons/line/<id>.svg`) exist for the cast, 恵子さん and the learner; guests and extras get their initial.
- **Status messages**: each character in cast.json has a LINE `status` (a short Japanese line with furigana markup, like a real LINE profile) shown in the app's People page. When something changes for a character in today's lesson, update their `status` (and `where` if they moved). Keep it in their voice.
- Characters address the learner as described in `world.you` and the task prompt.

## Formats

All four keep their lines in `dialogue`, so vocab `src` (`d0`, `d1`…) works the same.

| Format | Lines | Rules |
|---|---|---|
| `dialogue` | 4–6 | Spoken conversation. `speaker` is the character's Japanese `name` (or `アルちゃん` with `"me": true` and `"who": "you"` on the learner's lines). |
| `line` | 4–10 | A LINE thread. Short written messages (each bubble ≤ 40 字), casual written style (abbreviations, ｗ, emoji words). Optional `time` per line (`"21:04"`). At least one `"me": true`. Stickers and voice messages: see below. |
| `story` | 4–6 | One or two narrators tell something: a memory, a legend, yesterday's disaster. Each line is 1–2 sentences, plain or です/ます past narration. No `me` needed. |
| `text` | 4–8 | A written text to decode: notice, menu, flyer, school letter, museum panel, shop sign, social media post, email. `speaker` is the part's label (`Title`, `Rule 1`, `Price`, `Note`). Add `"text_title"` (shown as the header, with furigana markup). No `me` needed. |

### LINE extras: stickers and voice messages

- **Stickers**: a line can be a sticker: `{"who": "kenta", "speaker": "健太", "sticker": "nandeyanen", "jp": "なんでやねん", "en": "Why on earth?!", "time": "21:05"}`. `sticker` is an id from `stickers.json` (status lists them) and `jp` is exactly that sticker's text. Use 0–2 per chat, where a real person would. Never write stickers as text (（スタンプ：…）): the check refuses it. Characters prefer their signature stickers (`who` in stickers.json). A sticker line gets no audio and no vocab.
- **Voice message**: at most one line per chat can be `"kind": "voice"`: the app shows a voice-message bubble and hides the text until he taps. Use it for a line worth hearing (a character outside, in a hurry, laughing). It's read in the character's voice like any line.

## Listening (every lesson)

`listening`: one short activity after the main text, type given by status (`LISTENING type`), always in the story's world:
- `voicemail`: someone leaves a 留守電 (1–3 lines). Give `question` (Japanese, furigana markup), `options` (4, right one first, plain Japanese), `explain` (one English line).
- `announcement`: a school, station, town or shop announcement (`title`, `place`), same question/options/explain.
- `dictation`: 1–2 short lines (40 characters at most in total) he types out.
- `ladder`: exactly one line he hears slow, then normal, then reads.
Fields: `{"type", "intro" (one English line), "who" (main speaker id), "lines": [{"who", "jp", "en"}], ...}`. Lines follow the same furigana and gloss rules and may reuse today's words; they're voiced automatically. An announcement by a stranger uses `"who": "extra"` with `"voice"`.

## Challenge types

`challenge.type` comes from status (`CHALLENGE type`): free writing only on Tuesdays and Saturdays, one-tap types the other days, because most days he won't write. Every type keeps `prompt` (the situation, ideally a character's message to reply to), `model_answer` and `explanation`.
- `pick`: `options`: 3–4 `{jp, ok, why}` replies, exactly one `ok: true`. The wrong ones are plausible mistakes (wrong register, the similar pattern, wrong tense). `why` is one English line.
- `order`: `pieces`: 3–6 chunks of the model answer in the right order (the app shuffles); joined they must equal the model answer, punctuation aside.
- `fix`: `parts`: 3–6 chunks of a reply "he" wrote, exactly one `{"jp", "wrong": true, "why"}` with a typical learner mistake; the model answer is the fixed reply.
- `sticker`: `stickers`: 3–4 ids from stickers.json, the right one first; the prompt makes clear which feeling to send.
- `write`: as before, with a `hint`.

## Monthly mock (first Saturday of the month)

When status says so, the lesson is a mock exam instead: `"format": "mock"`, `"category": "mock"`, `function` any id, `topic` (`Mock exam: December`), `title_jp` (`12月の模試`), `context` (one line), a `listening` section (its lines are what the 聴解 questions play), and `mock.questions`: 8–12 questions using **only** words, kanji and grammar already taught (status lists them), in JLPT N3 style, each with `section`:
- `漢字読み`, `表記`, `文脈規定`, `言い換え`, `読解` (with `text`), `聴解` (with `"listen": "l0"`): `{section, prompt, options (4, right first), explain}`.
- `文法 ★`: `{section, prompt?, order: {before, pieces (4, in the right order), after, star (0–3, which slot has the ★)}, explain}`.
Add the log entry as usual (the summary can be one line). No vocab, kanji study, grammar or challenge on mock days.

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
| `cast` | List of character ids from `cast.json` (`cast` or `others`) |
| `guest` | Optional `{name, name_jp, role}` |
| `title_jp` | Short Japanese title |
| `context` | 1–2 English sentences setting today's scene in the story (used by the radio and the story log) |
| `scene` | The start page's one line: the situation in at most 30 English words, e.g. `Day off tomorrow. You ask 千夏さん, a hiker you met at the guesthouse, for tips.` |
| `keep` | Optional: 1–2 phrase refs (`["p4"]`) shown on the お疲れ様 screen as the phrase(s) to keep. Default: the first phrase. Use two only when they belong together |
| `phrases` | Exactly 5 × `{jp, en, register, note?}`; register is `polite`, `casual`, `neutral`, `dialect`, `slang` or `archaic`. The mix follows the scene: casual with friends, polite with strangers and at work |
| `dialogue_setting` | One English line: where/how this happens |
| `dialogue` | The main text in today's format (see Formats). Each line: `{who, speaker, jp, en}` (+ `me`, `time`, `register`, `note`, `sticker`, `kind`) |
| `listening` | Today's listening activity (see Listening) |
| `text_title` | Only for `text` format |
| `grammar` | Today's grammar point (see below) |
| `kanji` | `{kanji, reading, romaji, meaning, where, breakdown, related?}`: a word you'd really see written in this world (sign, label, menu, scroll, app screen). `breakdown`: one line on how its kanji build the meaning, e.g. `{既読|きどく}: 既 already + 読 read → 'already read'.` (the app also shows each kanji's dictionary meaning; for a single kanji, say what its parts hint at) |
| `tip` | `{mark, title, body}`: `mark` is one kanji shown as a stamp; body is 2–3 sentences textbooks don't teach |
| `challenge` | `{type, prompt, model_answer, explanation, ...}` (see Challenge types): a short task, ideally replying to a character. `explanation`: 2–3 English sentences (furigana markup allowed) that walk through the model answer: which grammar does what, why that word or form, the register |
| `vocab` | 8–10 words from today's phrases and main text |
| `kanji_study` | Exactly 2 kanji to learn |
| `extras` | Optional bonus sections `{title, title_jp, intro, items: [{jp, en, note?}]}`; 2–3 of them |
| `news` | `true` only on news lessons |

## Grammar

`grammar`: `{id, pattern, level, meaning, form, explanation, src, mark, examples, quiz, quiz_more}`
- `id`, `pattern`, `level`, `meaning`: from `curriculum/grammar.json` (the `pattern` may get furigana markup).
- `form`: how to build it, one rule per case, rules separated by ` · ` (space, middle dot, space). Write each rule as `label: rule (example, example)`: the app shows the label as a chip, the rule in bold and each example on its own line under it. E.g. `う-verbs: -a + れる ({頼|たの}む → {頼|たの}まれる, {怒|おこ}る → {怒|おこ}られる) · る-verbs: + られる ({見|み}る → {見|み}られる) · する → される · {来|く}る → {来|こ}られる`. Short labels (`う-verbs`, `い-adj`, `noun`, `{動詞|どうし}ない{形|けい}`); an irregular can be just `する → される` (shown as chip + result). With a single rule the label can go: `{動詞|どうし}た{形|けい} + ばかり ({食|た}べたばかり)`. Examples are short forms, 1–3 per rule, no full sentences (those go in `examples`).
- `explanation`: at most 50 words, 2–3 plain English sentences: when people use it, the nuance, and the classic mistake (or how it differs from the point learners confuse it with).
- `src`: the lines of today's lesson that use it (`["d2", "p1"]`), at least one. Put the clearest first: the app shows the first two.
- `mark`: the grammar point exactly as it appears in the `src` lines and `examples`, as plain strings without furigana, e.g. `["迷っちゃって", "忘れてしまいました", "食べちゃった"]` (the verb with its ending). The app highlights them on the 今日の文 tab; every `src` line must contain one (the check enforces it).
- `examples`: 1–3 extra `{jp, en}` sentences in other situations, so the pattern isn't tied to one scene.
- `quiz`: `{question, en, options, explain}`. `question` is a Japanese sentence with `＿＿` where the answer goes; `en` its translation; `options` 4 forms, **the right one first** (the app shuffles), the wrong ones plausible (wrong conjugation, the similar pattern); `explain` one line on why.
- `quiz_more`: 2 more questions in the same shape, testing the point from other angles (another conjugation, the negative, telling it apart from the pattern learners confuse it with). チェック asks all three.
- Never teach the same grammar point twice (the check refuses it), except in review lessons.

## Vocab

Every vocab word, both kanji and the grammar point go into his review deck automatically (words rated commonness 1 stay out); stars mark the ones he wants more often. Cards come back inside their sentence, and as audio-only and fill-the-gap cards, so every word must come from a real line of today's lesson.

Each item: `{jp, reading, en, level, src, surface, note?}`
- `en`: the meaning, shortest form first (`to get lost; to hesitate`): the app's word list shows the part before the first `;` or `,`.
- `note`: at most 20 words, only what helps him remember or use it: how its kanji build it (`重ねる pile up + 着る wear`), if it's casual, polite or slang, a common pair (`道に迷う`). Don't repeat the lesson's sentence: the app no longer shows it on the word list.
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

A GitHub automation voices everything after each push (`scripts/tts.py`, Gemini 3.8 Flash-Lite TTS, casting in `voices.json`): every line, phrase, example and extra, plus each vocab word, the model answer, slow versions and a radio track. Don't run it yourself; just give it what it needs:
- Voices go by `who`. A `text` written by a character (颯太's essay, 由紀's blog post) is read in their voice: add `"reader": "<id>"` to the lesson. Without it, the narrator reads it.
- The guest object needs `"voice": "f"` or `"m"` and `"age"` (a number): the app picks a Gemini library voice of that gender and age. Extras need `"voice"` on their lines (and may give `"age"`).
- A side character who will come back (like 恵子さん) goes in cast.json `others` and gets a fixed voice in `voices.json` `others` (keyed by id). Don't change the casting unless the user asks.
- Names of people and places are read from their furigana automatically. If a line has another word the engine might misread (a rare reading, 今日 meaning こんにち), add `"tts"` to that line: the whole line as it should be read, with that word in kana.

## Furigana markup

Every Japanese string (except `kanji.kanji` and `kanji.reading`) marks each kanji word with its reading: `{漢字|かんじ}`.
- **Every kanji above simple N5/N4 gets furigana, wherever the learner sees it**: not only the Japanese lines but also Japanese words inside English fields (`en` translations, `context`, `scene`, `dialogue_setting`, notes, explanations, `explain`, `tip`, `intro`, guest `role`, LINE `status`). Write `I'm going up {鷹見岳|たかみだけ}`, `{千夏|ちなつ}さん said…`, `from {松本|まつもと}`. Names and place names count too. When unsure whether a kanji is simple N4, add the furigana.
- The only places without furigana are the ones that test or show the kanji itself: `kanji`, `kanji_study`, vocab `jp`/`surface`, `grammar.mark`, `tip.mark`, quiz `options`, and `speaker`/`name` labels (they must match cast.json). In a mock exam, only the reading questions go bare.
- `python3 scripts/lessons.py check` refuses any kanji above N4 outside a `{…|…}` block in the other fields.
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
