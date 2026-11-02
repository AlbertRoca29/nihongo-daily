# Nihongo Line

Daily Japanese micro-lessons for life in Japan (N4–N3), as an installable phone web app.

Live: https://albertroca29.github.io/nihongo-daily/

## How lessons are added
Each lesson is one file, `lessons/YYYY-MM-DD.json`, plus an entry `{"id": "YYYY-MM-DD", "topic": "..."}` in `lessons/index.json`.
A scheduled Claude task adds one every morning.

Japanese strings use `{漢字|かんじ}` markup for furigana.

## Lesson plan
- Most days follow the life-in-Japan topic list (konbini, trains, host, farm, hostel…), written in batches.
- **News days: the 7th, 17th and 27th of each month.** That day's lesson is written ON the day, from real Japan news of the previous 10 days, in easy Japanese (lesson JSON has `"news": true`). Never pre-write news lessons.
