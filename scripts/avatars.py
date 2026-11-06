"""Draws the character portraits: python3 scripts/avatars.py -> icons/cast/<id>.svg (original flat SVGs, one per cast member, Keiko and You)."""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons", "cast")
os.makedirs(OUT, exist_ok=True)

SKIN = {"light": "#f6d3b8", "warm": "#eec19c", "tan": "#d9a274", "pale": "#f8dcc6"}
INK = "#2b2230"


def face(skin, eyes="open", mouth="smile", brows="soft", cheeks=True, eye_y=52, glasses=None, wrinkles=False, stubble=False):
    s = []
    # ears
    s.append(f'<ellipse cx="31" cy="{eye_y+1}" rx="3.6" ry="5" fill="{skin}"/><ellipse cx="69" cy="{eye_y+1}" rx="3.6" ry="5" fill="{skin}"/>')
    # head
    s.append(f'<ellipse cx="50" cy="50" rx="19" ry="22" fill="{skin}"/>')
    if stubble:
        s.append('<path d="M33 56 Q35 70 50 72 Q65 70 67 56 Q60 66 50 66 Q40 66 33 56Z" fill="#6b4a3a" opacity=".22"/>')
    # eyes
    if eyes == "open":
        s.append(f'<ellipse cx="42.5" cy="{eye_y}" rx="2.1" ry="2.6" fill="{INK}"/><ellipse cx="57.5" cy="{eye_y}" rx="2.1" ry="2.6" fill="{INK}"/>')
        s.append(f'<circle cx="43.2" cy="{eye_y-0.9}" r=".7" fill="#fff"/><circle cx="58.2" cy="{eye_y-0.9}" r=".7" fill="#fff"/>')
    elif eyes == "happy":
        s.append(f'<path d="M39.5 {eye_y+1} Q42.5 {eye_y-2.5} 45.5 {eye_y+1}M54.5 {eye_y+1} Q57.5 {eye_y-2.5} 60.5 {eye_y+1}" stroke="{INK}" stroke-width="1.8" fill="none" stroke-linecap="round"/>')
    elif eyes == "calm":
        s.append(f'<path d="M39.5 {eye_y} Q42.5 {eye_y+1.6} 45.5 {eye_y}M54.5 {eye_y} Q57.5 {eye_y+1.6} 60.5 {eye_y}" stroke="{INK}" stroke-width="1.8" fill="none" stroke-linecap="round"/>')
    elif eyes == "stern":
        s.append(f'<ellipse cx="42.5" cy="{eye_y}" rx="2.2" ry="1.7" fill="{INK}"/><ellipse cx="57.5" cy="{eye_y}" rx="2.2" ry="1.7" fill="{INK}"/>')
    # brows
    by = eye_y - 5
    if brows == "soft":
        s.append(f'<path d="M39 {by} Q42.5 {by-1.6} 46 {by}M54 {by} Q57.5 {by-1.6} 61 {by}" stroke="{INK}" stroke-width="1.3" fill="none" stroke-linecap="round" opacity=".75"/>')
    elif brows == "thick":
        s.append(f'<path d="M38.5 {by+.5} L46 {by-1}M54 {by-1} L61.5 {by+.5}" stroke="{INK}" stroke-width="2.4" fill="none" stroke-linecap="round"/>')
    elif brows == "stern":
        s.append(f'<path d="M38.5 {by-1.5} L46 {by+1}M54 {by+1} L61.5 {by-1.5}" stroke="{INK}" stroke-width="2.4" fill="none" stroke-linecap="round"/>')
    elif brows == "grey":
        s.append(f'<path d="M38.5 {by} Q42.5 {by-2} 46 {by}M54 {by} Q57.5 {by-2} 61.5 {by}" stroke="#9a9a9a" stroke-width="2.2" fill="none" stroke-linecap="round"/>')
    # nose
    s.append(f'<path d="M50 {eye_y+4} q-1.4 3 0 3.6" stroke="#c98e6c" stroke-width="1.2" fill="none" stroke-linecap="round"/>')
    # mouth
    my = eye_y + 11
    if mouth == "smile":
        s.append(f'<path d="M45 {my} Q50 {my+4} 55 {my}" stroke="#8a3b3b" stroke-width="1.7" fill="none" stroke-linecap="round"/>')
    elif mouth == "grin":
        s.append(f'<path d="M43.5 {my-1} Q50 {my+7} 56.5 {my-1}Z" fill="#8a3b3b"/><path d="M45 {my-0.3} Q50 {my+1.6} 55 {my-0.3}" stroke="#fff" stroke-width="1.4" fill="none"/>')
    elif mouth == "flat":
        s.append(f'<path d="M46 {my+1} Q50 {my+2} 54 {my+1}" stroke="#8a3b3b" stroke-width="1.7" fill="none" stroke-linecap="round"/>')
    elif mouth == "small":
        s.append(f'<path d="M47.5 {my+.5} Q50 {my+2.5} 52.5 {my+.5}" stroke="#8a3b3b" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    if cheeks:
        s.append(f'<ellipse cx="38" cy="{eye_y+7}" rx="3.2" ry="2" fill="#f08a8a" opacity=".35"/><ellipse cx="62" cy="{eye_y+7}" rx="3.2" ry="2" fill="#f08a8a" opacity=".35"/>')
    if wrinkles:
        s.append(f'<path d="M36 {eye_y+1} l-2 1.2M64 {eye_y+1} l2 1.2M44 {my+3} q6 2 12 0" stroke="#b77d5f" stroke-width=".9" fill="none" stroke-linecap="round" opacity=".7"/>')
    if glasses == "rect":
        s.append(f'<g stroke="{INK}" stroke-width="1.4" fill="none"><rect x="37" y="{eye_y-4}" width="11" height="8" rx="2"/><rect x="52" y="{eye_y-4}" width="11" height="8" rx="2"/><path d="M48 {eye_y-1} h4M37 {eye_y-1} l-5 -1M63 {eye_y-1} l5 -1"/></g>')
    elif glasses == "round":
        s.append(f'<g stroke="#3a2a20" stroke-width="1.4" fill="none"><circle cx="42.5" cy="{eye_y}" r="5.3"/><circle cx="57.5" cy="{eye_y}" r="5.3"/><path d="M47.8 {eye_y-.5} q2.2 -1.6 4.4 0M37.2 {eye_y-1} l-5 -1M62.8 {eye_y-1} l5 -1"/></g>')
    return "".join(s)


def body(color, collar=None, neck_skin="#eec19c"):
    s = [f'<rect x="44" y="66" width="12" height="12" fill="{neck_skin}"/>',
         f'<path d="M14 104 Q16 80 36 76 L64 76 Q84 80 86 104Z" fill="{color}"/>']
    if collar:
        s.append(collar)
    return "".join(s)


def svg(bg, inner, id_):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="{id_}">'
            f'<defs><clipPath id="c-{id_}"><circle cx="50" cy="50" r="50"/></clipPath></defs>'
            f'<g clip-path="url(#c-{id_})"><rect width="100" height="100" fill="{bg}"/>{inner}</g></svg>')


A = {}

# Tanaka-san: 67, apple farmer, short grey hair, towel headband, work jacket, dry smile
sk = SKIN["tan"]
A["tanaka"] = svg("#cfe7c4",
    '<circle cx="84" cy="22" r="7" fill="#e5484d"/><path d="M84 15 q1 -4 4 -5" stroke="#5b3a1a" stroke-width="1.5" fill="none"/><ellipse cx="88" cy="12" rx="3" ry="1.6" fill="#3f9a4a"/>'
    + body("#4d6b8a", '<path d="M40 76 L50 92 L60 76" fill="#3b5672"/><path d="M40 76 L50 88 L60 76" stroke="#e9e1cf" stroke-width="2" fill="none"/>', sk)
    + '<path d="M31 45 Q30 26 50 25 Q70 26 69 45 Q66 34 50 33 Q34 34 31 45Z" fill="#b8b8b8"/>'
    + face(sk, eyes="calm", mouth="flat", brows="grey", wrinkles=True, cheeks=False)
    + '<path d="M30 38 Q50 30 70 38 L70 43 Q50 35 30 43Z" fill="#f2f2f2"/><path d="M30 38 Q50 30 70 38" stroke="#4f7fb3" stroke-width="1.4" fill="none" stroke-dasharray="3 2"/>'
    + '<path d="M69 40 l7 -3 l-2 6Z" fill="#f2f2f2"/>', "tanaka")

# Yuki: 25, Tokyo office worker & otaku, brown bob with bangs, headphones, pink
sk = SKIN["light"]
A["yuki"] = svg("#ffd6e4",
    '<path d="M27 50 Q26 24 50 23 Q74 24 73 50 L74 70 Q66 74 62 66 L38 66 Q34 74 26 70Z" fill="#6a3f2c"/>'
    + body("#ffffff", '<path d="M38 76 L50 86 L62 76" fill="#f3f3f7"/><rect x="14" y="88" width="72" height="20" fill="#2f3a56"/>', sk)
    + face(sk, eyes="happy", mouth="grin", brows="soft")
    + '<path d="M31 46 Q30 26 50 25 Q70 26 69 46 Q63 38 58 37 Q55 43 49 41 Q44 44 38 40 Q34 42 31 46Z" fill="#6a3f2c"/>'
    + '<path d="M28 50 Q28 22 50 21 Q72 22 72 50" stroke="#ff5c8a" stroke-width="3.2" fill="none"/><rect x="23" y="45" width="8" height="13" rx="4" fill="#ff5c8a"/><rect x="69" y="45" width="8" height="13" rx="4" fill="#ff5c8a"/>'
    + '<path d="M33 30 l1 -9 l7 5Z" fill="#ff5c8a"/><path d="M67 30 l-1 -9 l-7 5Z" fill="#ff5c8a"/><path d="M35 27 l.6 -4 l3 2.2Z M65 27 l-.6 -4 l-3 2.2Z" fill="#ffd0de"/>', "yuki")

# Kenta: 24, from Osaka, snowboarder, beanie, dyed brown hair, big grin, orange hoodie
sk = SKIN["warm"]
A["kenta"] = svg("#ffe1b8",
    body("#f07f2e", '<path d="M38 76 Q50 90 62 76" fill="#d96a1d"/><path d="M46 80 v10M54 80 v10" stroke="#fff" stroke-width="1.5"/>', sk)
    + '<path d="M31 46 L28 54 L32 52Z M69 46 L72 54 L68 52Z" fill="#a8652c"/>'
    + face(sk, eyes="happy", mouth="grin", brows="thick")
    + '<path d="M30 44 Q29 20 50 19 Q71 20 70 44 L66 40 Q50 34 34 40Z" fill="#2c7a7b"/><rect x="29" y="38" width="42" height="7" rx="3.5" fill="#22605f"/><circle cx="50" cy="17" r="4" fill="#ffd166"/>'
    + '<path d="M33 45 l3 -2 l1 3 l3 -2 M67 45 l-3 -2 l-1 3 l-3 -2" stroke="#a8652c" stroke-width="2" fill="none"/>', "kenta")

# Sato-sensei: 41, English teacher, low bun, rectangular glasses, navy blazer
sk = SKIN["light"]
A["sato"] = svg("#d4e3fb",
    '<circle cx="50" cy="73" r="0" />'
    + '<ellipse cx="50" cy="27" rx="0" ry="0"/>'
    + '<circle cx="50" cy="24" r="8" fill="#2b1d1a"/>'
    + body("#2e3f6e", '<path d="M42 76 L50 90 L58 76Z" fill="#ffffff"/><path d="M40 76 L50 98 M60 76 L50 98" stroke="#22305a" stroke-width="2"/>', sk)
    + '<path d="M30 52 Q28 26 50 25 Q72 26 70 52 Q68 38 50 36 Q32 38 30 52Z" fill="#2b1d1a"/>'
    + face(sk, eyes="open", mouth="small", brows="soft", glasses="rect", cheeks=False)
    + '<path d="M31 47 Q31 28 50 27 Q69 28 69 47 Q62 34 50 33 Q40 33 31 47Z" fill="#2b1d1a"/><path d="M50 27 Q44 35 33 44" stroke="#4a3530" stroke-width="1" fill="none"/>'
    , "sato")

# Hana-obaachan: 84, white hair bun, kind closed-eye smile, purple kappogi apron
sk = SKIN["pale"]
A["hana"] = svg("#e6dcf7",
    body("#8a6fc4", '<path d="M36 76 Q50 84 64 76 L66 104 L34 104Z" fill="#f7f3ea"/><path d="M40 76 L50 86 L60 76" stroke="#6b52a3" stroke-width="2" fill="none"/>', sk)
    + '<circle cx="50" cy="24" r="9" fill="#ededed"/><path d="M44 22 q6 -4 12 0" stroke="#cfcfcf" stroke-width="1" fill="none"/><path d="M58 18 l9 -5" stroke="#b5651d" stroke-width="1.6"/>'
    + face(sk, eyes="happy", mouth="smile", brows="grey", wrinkles=True)
    + '<path d="M31 50 Q29 29 50 28 Q71 29 69 50 Q66 38 56 36 Q50 40 44 36 Q34 38 31 50Z" fill="#ededed"/><path d="M38 36 Q44 40 50 37 M50 37 Q56 40 62 36" stroke="#cfcfcf" stroke-width="1" fill="none"/>', "hana")

# Ren: 26, graphic designer, black hair with soft fringe, round glasses, turtleneck, camera strap
sk = SKIN["light"]
A["ren"] = svg("#cdeee8",
    body("#3b3f47", '<rect x="40" y="70" width="20" height="10" rx="4" fill="#3b3f47"/><path d="M36 78 L60 104" stroke="#a0522d" stroke-width="3"/>', sk)
    + face(sk, eyes="calm", mouth="small", brows="soft", glasses="round")
    + '<path d="M30 50 Q27 24 50 23 Q73 24 70 50 Q69 42 66 38 Q60 44 50 41 Q46 46 38 44 Q34 44 30 50Z" fill="#1d1b22"/><path d="M50 41 Q55 37 66 38" stroke="#3a3744" stroke-width="1" fill="none"/>', "ren")

# Sota: 11, Tanaka's grandson, short black hair with cowlick, gap-tooth grin, striped tee, beetle
sk = SKIN["warm"]
A["sota"] = svg("#fff1a8",
    body("#2fa36b", '<path d="M14 88 H86 M14 96 H86" stroke="#ffffff" stroke-width="3"/>', sk)
    + face(sk, eyes="open", mouth="grin", brows="thick", eye_y=53)
    + '<path d="M31 46 Q30 26 50 26 Q70 26 69 46 Q64 36 56 36 Q50 40 44 36 Q36 38 31 46Z" fill="#191419"/><path d="M50 26 q-2 -7 4 -9" stroke="#191419" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    + '<ellipse cx="82" cy="78" rx="6" ry="8" fill="#5a3418"/><path d="M82 70 v16M82 70 l-3 -6M82 70 l3 -6M76 76 l-4 -2M88 76 l4 -2M76 82 l-4 2M88 82 l4 2" stroke="#3a2210" stroke-width="1.3"/>', "sota")

# Mio: 16, high-school student, long black hair, hair clip, sailor uniform
sk = SKIN["light"]
A["mio"] = svg("#e3dbff",
    '<path d="M28 50 Q26 24 50 23 Q74 24 72 50 L75 90 L25 90Z" fill="#141018"/>'
    + body("#1f2a4a", '<path d="M30 78 L50 94 L70 78 L64 76 L50 86 L36 76Z" fill="#ffffff"/><path d="M45 88 l5 7 l5 -7Z" fill="#e5484d"/>', sk)
    + face(sk, eyes="open", mouth="smile", brows="soft")
    + '<path d="M31 50 Q30 26 50 25 Q70 26 69 50 Q67 40 64 36 Q56 40 50 36 Q44 41 36 37 Q33 42 31 50Z" fill="#141018"/>'
    + '<rect x="58" y="33" width="9" height="3" rx="1.5" fill="#ffd166" transform="rotate(-20 62 34)"/>', "mio")

# Kurogane Hayato: samurai (Edo period), topknot, stern, dark kimono with crest
sk = SKIN["tan"]
A["hayato"] = svg("#f3d2c7",
    body("#2a2a36", '<path d="M38 76 L50 98 L62 76" fill="#e9e1cf"/><path d="M41 76 L50 94 L59 76" fill="#2a2a36"/><circle cx="74" cy="88" r="4" fill="none" stroke="#e9e1cf" stroke-width="1.2"/>', sk)
    + face(sk, eyes="stern", mouth="flat", brows="stern", cheeks=False, stubble=True)
    + '<path d="M31 50 Q30 32 36 30 L36 40 Q34 44 31 50Z M69 50 Q70 32 64 30 L64 40 Q66 44 69 50Z" fill="#141018"/>'
    + '<path d="M36 33 Q50 27 64 33 L64 31 Q50 25 36 31Z" fill="#141018"/>'
    + '<path d="M44 29 Q50 15 60 22 Q54 22 50 28Z" fill="#141018"/><rect x="47" y="25" width="5" height="4" fill="#e9e1cf" transform="rotate(-25 49 27)"/>', "hayato")

# Keiko: 64, Tanaka's wife, warm and talkative, short permed hair, cooking apron
sk = SKIN["light"]
A["keiko"] = svg("#ffe3cc",
    body("#c7684a", '<path d="M38 78 Q50 84 62 78 L64 104 L36 104Z" fill="#f2c94c"/><path d="M42 78 L40 70 M58 78 L60 70" stroke="#f2c94c" stroke-width="2"/>', sk)
    + '<circle cx="34" cy="38" r="7" fill="#6e5448"/><circle cx="66" cy="38" r="7" fill="#6e5448"/><circle cx="31" cy="48" r="6" fill="#6e5448"/><circle cx="69" cy="48" r="6" fill="#6e5448"/>'
    + face(sk, eyes="happy", mouth="grin", brows="soft", wrinkles=True)
    + '<path d="M31 44 Q31 26 50 26 Q69 26 69 44 Q64 36 57 38 Q52 33 46 37 Q39 34 31 44Z" fill="#6e5448"/><circle cx="42" cy="29" r="6" fill="#6e5448"/><circle cx="52" cy="27" r="6.5" fill="#6e5448"/><circle cx="61" cy="30" r="6" fill="#6e5448"/>'
    + '<path d="M40 30 q3 -3 6 0 M50 27 q3 -3 6 0" stroke="#8a6e60" stroke-width="1" fill="none"/>', "keiko")

# You (the learner): from Spain, brown wavy hair, light stubble, green jacket
sk = SKIN["warm"]
A["you"] = svg("#c9f2d9",
    body("#1e7a52", '<path d="M40 76 L50 86 L60 76" fill="#f4efe6"/>', sk)
    + face(sk, eyes="open", mouth="smile", brows="thick", stubble=True)
    + '<path d="M30 48 Q27 22 50 22 Q74 22 70 48 Q68 38 63 35 Q61 39 56 37 Q52 41 46 37 Q40 40 37 36 Q32 40 30 48Z" fill="#5a3a24"/>'
    + '<path d="M37 30 q4 -6 10 -3 q4 -5 10 -1 q6 -2 8 4" stroke="#6e4a30" stroke-width="2" fill="none" stroke-linecap="round"/>', "you")

for k, v in A.items():
    open(os.path.join(OUT, k + ".svg"), "w").write(v)
print("wrote", len(A))
