"""Cast portraits as used in the app (small-size readable style) and LINE selfies.

Builds on chibi.py (the base drawings): zoomed-in head and shoulders, a thin ink
outline, one signature background colour + ring per person, a few clean props.
LINE profile pictures are the same portrait tilted like a phone selfie in front
of the person's place.

Run: python3 scripts/portraits.py  -> icons/cast/<id>.svg and icons/line/<id>.svg
"""
import os, re, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chibi as C

IDS = ["tanaka", "keiko", "yuki", "kenta", "sato", "hana", "ren", "sota", "mio", "hayato", "you"]

# signature colours: one hue per person, all distinct
SIG = {
    "tanaka": "#9fd36a",  # orchard lime
    "keiko": "#ff9a7d",   # coral
    "yuki": "#ff8cc0",    # pink
    "kenta": "#ffb03b",   # orange
    "sato": "#6f9bf2",    # blue
    "hana": "#b38cf0",    # violet
    "ren": "#48b8a6",     # teal
    "sota": "#ffd84a",    # yellow
    "mio": "#78d4ef",     # cyan
    "hayato": "#34406e",  # night indigo
    "you": "#f2e9d8",     # warm paper (the neutral one: you)
}

ORIG = {}
_svg = C.svg


def capture(cid, bg, iris, layers, deco=""):
    ORIG[cid] = dict(bg=bg, iris=iris, layers=layers, deco=deco)
    return _svg(cid, bg, iris, layers, deco)


C.svg = capture
C.build()

SPARK = [C.sparkles(), C.sparkles("#fff", .6), C.sparkles("#fff", .5)]


def strip_sparkles(d):
    for s in SPARK:
        d = d.replace(s, "")
    return d


def shade(c, f):
    return C.shade(c, f)


def render(cid, *, dy=0, zoom=1.0, outline=0, bg=None, sparkle=True, ring=False, layers=None, extra="", under="", deco=None):
    o = ORIG[cid]
    L = layers if layers is not None else o["layers"]
    D = o["deco"] if deco is None else deco
    if not sparkle:
        D = strip_sparkles(D)
    bgc = bg or o["bg"]
    iris = o["iris"]
    dark = sum(int(bgc[i:i + 2], 16) for i in (1, 3, 5)) < 300
    top = shade(bgc, 1.25 if dark else 1.45)
    defs = (f'<clipPath id="c"><circle cx="50" cy="50" r="50"/></clipPath>'
            f'<radialGradient id="bg" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bgc}"/></radialGradient>'
            f'<linearGradient id="iris" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{shade(iris, .55)}"/><stop offset=".6" stop-color="{iris}"/><stop offset="1" stop-color="{shade(iris, 1.35)}"/></linearGradient>')
    filt = ""
    if outline:
        defs += (f'<filter id="ol" x="-10%" y="-10%" width="120%" height="120%">'
                 f'<feMorphology in="SourceAlpha" operator="dilate" radius="{outline}" result="d"/>'
                 f'<feFlood flood-color="{C.INK}" flood-opacity=".9"/><feComposite in2="d" operator="in" result="o"/>'
                 f'<feMerge><feMergeNode in="o"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
        filt = ' filter="url(#ol)"'
    if zoom != 1:
        # scale around the face, keep the top of the hair inside
        body = f'<g transform="translate(50 {55+dy}) scale({zoom}) translate(-50 -47)">{L}</g>'
    else:
        body = L
    ringsvg = f'<circle cx="50" cy="50" r="48.6" fill="none" stroke="{shade(bgc, .72)}" stroke-width="2.8"/>' if ring else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="{cid}"><defs>{defs}</defs>'
            f'<g clip-path="url(#c)"><rect width="100" height="100" fill="url(#bg)"/>{under}'
            f'<g{filt}>{body}{D}{extra}</g>{ringsvg}</g></svg>')


# ---------------------------------------------------------------- personality options
# Props are drawn in final (circle) coordinates, after the zoom. Visible face area with zoom 1.25:
# head ~ x 16..84, y 14..77. Free corners: lower-left (8..26, 55..92) and lower-right (74..92, 55..92).
INK = C.INK
Z = 1.25


def zt(x, y):
    """original chibi coordinate -> final coordinate under zoom Z"""
    return 50 + Z * (x - 50), 55 + Z * (y - 47)


def inzoom(svg):
    return f'<g transform="translate(50 55) scale({Z}) translate(-50 -47)">{svg}</g>'


def remove(layers, *parts):
    for p in parts:
        assert p in layers, p[:60]
        layers = layers.replace(p, "")
    return layers


P = {}  # cid -> {"A": (label, desc, kwargs), "B": ...}

# --- Tanaka-san -------------------------------------------------------------
tan = ORIG["tanaka"]["layers"]
towel = ('<path d="M22 36 C34 28 66 28 78 36 L78 42 C66 34 34 34 22 42Z" fill="#f7f5ef" stroke="#cfcac0" stroke-width=".8"/>'
         '<path d="M26 37 C38 31 62 31 74 37" stroke="#3d6fb3" stroke-width="1.6" fill="none" stroke-dasharray="3.2 2.4"/>'
         '<path d="M77 38 l9 -5 l-2 7 l6 1 l-9 4Z" fill="#f7f5ef" stroke="#cfcac0" stroke-width=".8"/>')
cap = ('<path d="M22 38 C21 21 34 14 50 14 C66 14 79 21 78 38Z" fill="#1d1a1a" stroke="#000" stroke-width="1.2"/>'
       '<path d="M32 19 L35 36 M42 15.4 L43 36 M58 15.4 L57 36 M68 19 L65 36" stroke="#ffd21f" stroke-width="2.2"/>'
       '<path d="M24 36 C34 33 66 33 76 36 C80 40 74 46 50 46 C26 46 20 40 24 36Z" fill="#ffd21f" stroke="#1d1a1a" stroke-width="1.3"/>'
       '<path d="M30 40 C40 42.6 60 42.6 70 40" stroke="#c9a10f" stroke-width="1" fill="none"/>'
       '<circle cx="50" cy="14.6" r="2.2" fill="#ffd21f" stroke="#1d1a1a" stroke-width=".8"/>')
P["tanaka"] = {
    "A": ("Baseball cap", "Tiger-striped cap (his secret Hanshin fandom, no logo)",
          dict(layers=remove(tan, towel) + cap)),
    "B": ("Towel + big apple", "Keeps the farm towel, a dry half-smile and a real apple, not a speck",
          dict(layers=tan.replace(C.mouth("smile"), '<path d="M45 62.6 Q50 65.4 55 61.6" stroke="#7a2e35" stroke-width="1.8" fill="none" stroke-linecap="round"/>'),
               deco="",
               extra='<g transform="translate(83 78)"><circle r="11" fill="#e5484d" stroke="#9e2a2e" stroke-width="1.4"/><path d="M0 -11 q1.5 -5 5 -7" stroke="#5b3a1a" stroke-width="2.2" fill="none"/>'
                     '<ellipse cx="7" cy="-15" rx="5" ry="2.4" fill="#4c9a44" transform="rotate(-20 7 -15)"/><ellipse cx="-4" cy="-4" rx="2.4" ry="3.6" fill="#fff" opacity=".45"/></g>')),
}

# --- Keiko ------------------------------------------------------------------
kei = ORIG["keiko"]["layers"]
scarf = ('<path d="M21 40 C21 20 34 13 50 13 C66 13 79 20 79 40 C70 33 30 33 21 40Z" fill="#ffffff" stroke="#c9c2b8" stroke-width="1.1"/>'
         '<g fill="#e5484d"><circle cx="34" cy="24" r="1.8"/><circle cx="46" cy="19" r="1.8"/><circle cx="58" cy="20" r="1.8"/><circle cx="68" cy="27" r="1.8"/><circle cx="40" cy="30" r="1.8"/><circle cx="54" cy="28" r="1.8"/><circle cx="28" cy="33" r="1.6"/><circle cx="72" cy="35" r="1.6"/></g>'
         '<path d="M77 36 l8 -4 l-1 8 l5 3 l-9 1Z" fill="#ffffff" stroke="#c9c2b8" stroke-width="1"/>')
shamoji = ('<g transform="translate(19 76) rotate(-28) scale(1.2)"><rect x="-1.8" y="-4" width="3.6" height="18" rx="1.6" fill="#d9a066" stroke="#9a6a38" stroke-width="1"/>'
           '<ellipse cx="0" cy="-11" rx="7" ry="9" fill="#e8bc84" stroke="#9a6a38" stroke-width="1.2"/><g fill="#fff"><circle cx="-2" cy="-13" r="1.6"/><circle cx="2" cy="-9" r="1.6"/><circle cx="1.4" cy="-14" r="1.3"/></g></g>')
onigiri = ('<g transform="translate(81 74)"><path d="M0 -13 C4 -13 13 4 11 8 C9 11 -9 11 -11 8 C-13 4 -4 -13 0 -13Z" fill="#ffffff" stroke="#bdb6aa" stroke-width="1.3"/>'
           '<rect x="-7.4" y="1" width="14.8" height="9" rx="1.6" fill="#22303a"/><ellipse cx="-3" cy="-6" rx="1.6" ry="2.4" fill="#fff" opacity=".9"/></g>')
P["keiko"] = {
    "A": ("Kitchen headscarf + shamoji", "Polka-dot sankaku-kin and a rice paddle: she's the one who feeds everyone",
          dict(extra=shamoji, _scarf=scarf)),
    "B": ("Onigiri", "Keeps her curls, holds out an onigiri she made for you",
          dict(extra=onigiri)),
}

# --- Yuki -------------------------------------------------------------------
penlight = ('<g transform="translate(82 70) rotate(18) scale(1.15)"><rect x="-3.4" y="-20" width="6.8" height="22" rx="3.4" fill="#fff6a8" stroke="#ff5c93" stroke-width="1.4"/>'
            '<rect x="-3.4" y="-20" width="6.8" height="22" rx="3.4" fill="#ffe14d" opacity=".5"/><rect x="-3.8" y="2" width="7.6" height="12" rx="2" fill="#3a2f48"/>'
            '<path d="M-9 -24 l-3 -3 M9 -24 l3 -3 M0 -27 v-4" stroke="#ffe14d" stroke-width="2" stroke-linecap="round"/></g>')
mic = ('<g transform="translate(81 72) rotate(20) scale(1.15)"><path d="M-2.6 0 L-1.6 16 H1.6 L2.6 0Z" fill="#2b2b33"/><circle cy="-5" r="7" fill="#c7cad4" stroke="#6b6f7c" stroke-width="1.3"/>'
       '<path d="M-5 -7 H5 M-6 -4 H6 M-5 -1 H5" stroke="#8a8e9b" stroke-width=".9"/><rect x="-3.4" y="1" width="6.8" height="3" fill="#ff5c93"/></g>'
       '<path d="M69 66 l3 -2 M72 70 l4 -1" stroke="#fff" stroke-width="2" stroke-linecap="round"/>'
       '<g fill="#fff"><path d="M70 60 c0 -3 3 -3 3 -6 v8 c0 2 -3 2 -3 -2Z"/></g>')
P["yuki"] = {
    "A": ("Idol penlight", "Glowing concert penlight: events in Akihabara every weekend",
          dict(extra=penlight)),
    "B": ("Karaoke mic", "Karaoke addict, mid-song",
          dict(extra=mic)),
}

# --- Kenta ------------------------------------------------------------------
goggles = ('<rect x="20" y="25" width="60" height="6" fill="#1f2430"/>'
           '<rect x="27" y="19" width="46" height="15" rx="7.5" fill="#2b2f3a" stroke="#14161c" stroke-width="1.2"/>'
           '<rect x="29.5" y="21" width="41" height="11" rx="5.5" fill="url(#gog)"/>'
           '<path d="M33 23.4 L39 23.4" stroke="#fff" stroke-width="1.6" stroke-linecap="round" opacity=".85"/>')
gogdef = '<linearGradient id="gog" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd166"/><stop offset=".5" stop-color="#ff7a3d"/><stop offset="1" stop-color="#b03ad9"/></linearGradient>'
spatula = ('<g transform="translate(81 70) rotate(25) scale(1.1)"><rect x="-1.8" y="2" width="3.6" height="14" rx="1.4" fill="#8a5a2b" stroke="#5a3a1a" stroke-width="1"/>'
           '<path d="M-7 -12 H7 L6 2 H-6Z" fill="#d7dce3" stroke="#7d8591" stroke-width="1.2"/><path d="M-4 -9 v8" stroke="#fff" stroke-width="1.2" opacity=".8"/></g>'
           '<g transform="translate(19 76)"><ellipse rx="10" ry="6.4" fill="#c27a3a" stroke="#7a4a1c" stroke-width="1.2"/><path d="M-7 -1 q3 -3 6 0 t6 0" stroke="#5a2e1a" stroke-width="1.6" fill="none"/>'
           '<path d="M-6 2 q2 2 4 0 M2 2 q2 2 4 0" stroke="#f3e9c9" stroke-width="1.2" fill="none"/><circle cx="-2" cy="-3" r="1" fill="#6db35a"/><circle cx="3" cy="-2.6" r="1" fill="#6db35a"/></g>')
P["kenta"] = {
    "A": ("Snowboard goggles", "Goggles on the beanie: he came for the snow and never left",
          dict(_inhead=goggles, _defs=gogdef)),
    "B": ("Okonomiyaki", "Spatula and an okonomiyaki: \"Osaka food is better\"",
          dict(extra=spatula)),
}

# --- Sato-sensei ------------------------------------------------------------
sat = ORIG["sato"]["layers"]
bun = ('<circle cx="50" cy="14" r="9.5" fill="#2a1c1c" stroke="#140c0c" stroke-width="1"/><path d="M44 12 q6 -5 12 0" stroke="#4a3434" stroke-width="1.2" fill="none"/>')
redpen = ('<g transform="translate(14 40) rotate(-35)"><rect x="-2" y="-14" width="4" height="26" rx="2" fill="#e5484d" stroke="#a52a2e" stroke-width="1"/>'
          '<path d="M-2 12 L0 17 L2 12Z" fill="#f2e6d8"/><rect x="1.4" y="-12" width="1.6" height="8" fill="#a52a2e"/></g>')
lanyard = ('<path d="M33 79 L42 92 M67 79 L58 92" stroke="#e5484d" stroke-width="2.2"/>'
           '<rect x="40" y="90" width="20" height="13" rx="2" fill="#fff" stroke="#9aa3b8" stroke-width="1"/><rect x="42.5" y="92.5" width="6" height="7" rx="1" fill="#c9dcfa"/><path d="M51 94 h6 M51 97 h5" stroke="#9aa3b8" stroke-width="1.2"/>')
bob = ('<path d="M20 50 C18 25 33 15 50 15 C67 15 82 25 80 50 C80 58 79 64 76 68 L68 68 L68 46 L32 46 L32 68 L24 68 C21 64 20 58 20 50Z" fill="#2a1c1c" stroke="#140c0c" stroke-width="1"/>')
P["sato"] = {
    "A": ("Red pen + staff ID", "Bun stays; a red marking pen and a school lanyard: precise, organised",
          dict(_lanyard=lanyard, extra=redpen)),
    "B": ("Neat bob + red pen", "Swap the bun for a sharp bob so she no longer reads like Hana at small size",
          dict(_bob=True, extra=redpen)),
}

# --- Hana-obāchan -----------------------------------------------------------
tama = ('<g transform="translate(79 72) scale(1.15)">'
        '<path d="M-10 6 C-11 -6 -6 -12 0 -12 C6 -12 11 -6 10 6 C8 12 -8 12 -10 6Z" fill="#fffaf2" stroke="#3a2a22" stroke-width="1.3"/>'
        '<path d="M-9 -4 L-10 -16 L-3 -11Z M9 -4 L10 -16 L3 -11Z" fill="#fffaf2" stroke="#3a2a22" stroke-width="1.3" stroke-linejoin="round"/>'
        '<path d="M1 -12 C5 -12 9 -9 10 -4 L10 -16 L3 -11Z" fill="#f2a144"/><path d="M-10 -16 L-3 -11 L-6 -8 C-9 -8 -9.6 -10 -10 -16Z" fill="#3a2a22"/>'
        '<path d="M-5.5 -2 q1.6 -1.6 3.2 0 M2.3 -2 q1.6 -1.6 3.2 0" stroke="#3a2a22" stroke-width="1.3" fill="none" stroke-linecap="round"/>'
        '<path d="M-1 1.4 h2 l-1 1.2Z" fill="#ef7f8a"/><path d="M-1 3 q-1.4 1.4 -2.8 .2 M1 3 q1.4 1.4 2.8 .2" stroke="#3a2a22" stroke-width=".9" fill="none"/>'
        '<path d="M-12 1 h-5 M-12 3.4 h-5 M12 1 h5 M12 3.4 h5" stroke="#3a2a22" stroke-width=".7"/></g>')
ohagi = ('<g transform="translate(80 76)"><ellipse cy="5" rx="13" ry="4.6" fill="#f7f1e6" stroke="#a69a86" stroke-width="1.1"/>'
         '<ellipse cx="-4.6" cy="-1" rx="6.4" ry="5.4" fill="#5a2a32" stroke="#3a1a20" stroke-width="1"/><ellipse cx="5" cy="-.4" rx="6.4" ry="5.4" fill="#5a2a32" stroke="#3a1a20" stroke-width="1"/>'
         '<g fill="#7a3a44"><circle cx="-6" cy="-3" r="1"/><circle cx="-3" cy="0" r="1"/><circle cx="4" cy="-3" r="1"/><circle cx="7" cy="0" r="1"/></g></g>')
P["hana"] = {
    "A": ("Tama the cat", "Her calico cat on her shoulder (Tama is canon)",
          dict(extra=tama)),
    "B": ("Ohagi", "A plate of her festival ohagi",
          dict(extra=ohagi)),
}

# --- Ren --------------------------------------------------------------------
ren = ORIG["ren"]["layers"]
ren_gl = C.glasses("round", "#6b4a33")
camera = ('<path d="M24 64 L36 86 M76 64 L64 86" stroke="#7a4a2a" stroke-width="2.4"/>'
          '<g transform="translate(50 92)"><rect x="-17" y="-9" width="34" height="20" rx="3" fill="#2c2c30" stroke="#121214" stroke-width="1.2"/>'
          '<rect x="-17" y="-9" width="34" height="6" rx="2" fill="#c9c9cc"/><rect x="-13" y="-13" width="7" height="5" rx="1" fill="#c9c9cc"/>'
          '<circle cy="2" r="7.6" fill="#1a1a1d" stroke="#9a9aa0" stroke-width="1.6"/><circle cy="2" r="4" fill="#26304a"/><circle cx="-1.4" cy=".6" r="1.4" fill="#7f8db0"/></g>')
coffee = ('<g transform="translate(81 72)"><path d="M-7 -8 H7 L5.6 10 H-5.6Z" fill="#f2ede4" stroke="#8a7a66" stroke-width="1.2"/>'
          '<rect x="-7.6" y="-3" width="15.2" height="7" fill="#8a5a3a"/><rect x="-8.4" y="-11" width="16.8" height="4" rx="1.4" fill="#3a3e48"/>'
          '<path d="M-2 -15 q-2 -3 0 -6 M3 -15 q-2 -3 0 -6" stroke="#fff" stroke-width="1.4" fill="none" stroke-linecap="round" opacity=".85"/></g>')
P["ren"] = {
    "A": ("Film camera, no glasses", "Drops the glasses (so he stops looking like you) and wears his film camera",
          dict(layers=remove(ren, ren_gl), extra=camera)),
    "B": ("Glasses + coffee + camera", "Keeps the round glasses, adds his coffee and the camera",
          dict(extra=camera + coffee)),
}

# --- Sōta -------------------------------------------------------------------
beetle = ('<g transform="translate(80 24) rotate(30) scale(1.15)"><ellipse rx="8" ry="10" fill="#5a3418" stroke="#2a160a" stroke-width="1.2"/><path d="M0 -10 V10" stroke="#2a160a" stroke-width="1"/>'
          '<ellipse cx="-3" cy="-3" rx="1.6" ry="3.6" fill="#fff" opacity=".35"/><path d="M0 -10 C-1 -15 -4 -18 -7 -18 M-7 -18 l-1 3 M-7 -18 l3 0" stroke="#2a160a" stroke-width="2" fill="none" stroke-linecap="round"/>'
          '<path d="M-8 -2 l-4 -2 M8 -2 l4 -2 M-8 4 l-4 2 M8 4 l4 2" stroke="#2a160a" stroke-width="1.4" stroke-linecap="round"/></g>')
ball = ('<g transform="translate(81 74)"><circle r="10.5" fill="#fff" stroke="#2a1e24" stroke-width="1.3"/>'
        '<path d="M0 -4 L4 -1.2 L2.4 3.6 H-2.4 L-4 -1.2Z" fill="#2a1e24"/><path d="M0 -4 V-10.5 M4 -1.2 L10 -3 M2.4 3.6 L6 9 M-2.4 3.6 L-6 9 M-4 -1.2 L-10 -3" stroke="#2a1e24" stroke-width="1.1"/></g>')
sota = ORIG["sota"]["layers"]
stripes_old = '<path d="M26 90 H74 M25 98 H75" stroke="#fff" stroke-width="3.2"/>'
blaugrana = ('<path d="M30 80 V104 M42 77 V104 M58 77 V104 M70 80 V104" stroke="#c4224a" stroke-width="5"/>')
P["sota"] = {
    "A": ("Beetle on his head", "A rhinoceros beetle riding his spikes: instantly him",
          dict(extra=beetle)),
    "B": ("Football + blue-red kit", "Football in hand and a blue-and-red striped shirt (Barcelona dream)",
          dict(_sota_kit=True, extra=ball)),
}

# --- Mio --------------------------------------------------------------------
trumpet = ('<g transform="translate(77 74) rotate(-30) scale(1.2)"><path d="M-16 -1.6 H6 V1.6 H-16Z" fill="#f5c84c" stroke="#b8902a" stroke-width=".9"/>'
           '<path d="M6 -2 L16 -8 V8 L6 2Z" fill="#f5c84c" stroke="#b8902a" stroke-width="1.1"/><ellipse cx="16" cy="0" rx="2" ry="8" fill="#ffe08a" stroke="#b8902a" stroke-width="1"/>'
           '<rect x="-8" y="-6" width="2.4" height="5" fill="#d9a92e"/><rect x="-4" y="-6" width="2.4" height="5" fill="#d9a92e"/><rect x="0" y="-6" width="2.4" height="5" fill="#d9a92e"/>'
           '<path d="M-16 -2.4 v4.8" stroke="#b8902a" stroke-width="2.4"/></g>')
phone = ('<path d="M20 58 C18 68 20 78 24 86 M80 58 C82 68 80 78 76 86" stroke="#fff" stroke-width="1.6" fill="none"/>'
         '<circle cx="20" cy="57" r="2.6" fill="#fff" stroke="#9aa3b8" stroke-width=".8"/><circle cx="80" cy="57" r="2.6" fill="#fff" stroke="#9aa3b8" stroke-width=".8"/>'
         '<g transform="translate(81 74) rotate(12)"><rect x="-7" y="-12" width="14" height="24" rx="3" fill="#ffb3d1" stroke="#c4527e" stroke-width="1.2"/><rect x="-5" y="-9" width="10" height="16" rx="1.4" fill="#2b2f45"/><circle cx="-3" cy="-6" r="1.2" fill="#ff8cc0"/></g>')
P["mio"] = {
    "A": ("Trumpet", "Her brass band trumpet",
          dict(extra=trumpet)),
    "B": ("Phone + earbuds", "Always on her phone, indie band in her ears",
          dict(extra=phone)),
}

# --- Kurogane Hayato --------------------------------------------------------
hawk = ('<g transform="translate(80 72) scale(1.2)">'
        '<path d="M-6 14 C-9 4 -8 -6 -2 -10 C4 -13 9 -10 9 -4 C9 4 6 10 2 14Z" fill="#6b4220" stroke="#22140a" stroke-width="1.2"/>'
        '<path d="M-3 12 C-5 4 -4 -3 1 -5 C5 -4 6 2 5 8 C4 11 2 13 -3 12Z" fill="#f3e6cc"/>'
        '<path d="M-1 0 l3 0 M-2 4 l4 0 M-1 8 l3 0" stroke="#6b4220" stroke-width="1.2" stroke-linecap="round"/>'
        '<path d="M-4 -12 C-3 -18 6 -19 8 -13 C9 -10 6 -7 2 -7 C-1 -7 -4 -9 -4 -12Z" fill="#6b4220" stroke="#22140a" stroke-width="1.2"/>'
        '<path d="M7 -14 C11 -14 13 -11 11 -8 L10 -10 L7 -10Z" fill="#ffc83d" stroke="#22140a" stroke-width="1"/>'
        '<circle cx="3.6" cy="-13" r="2" fill="#ffc83d" stroke="#22140a" stroke-width=".6"/><circle cx="4" cy="-13" r=".9" fill="#121212"/>'
        '<path d="M1 -15.4 L7 -14.6" stroke="#22140a" stroke-width="1.2" stroke-linecap="round"/></g>')
soba = ('<g transform="translate(80 75)"><path d="M-12 -3 H12 C12 6 6 11 0 11 C-6 11 -12 6 -12 -3Z" fill="#2a2a3a" stroke="#121218" stroke-width="1.2"/>'
        '<path d="M-10 -1 H10" stroke="#c4224a" stroke-width="1.6"/><path d="M-9 -4 q4 -3 8 0 t8 0" stroke="#b49a6a" stroke-width="2.4" fill="none"/>'
        '<path d="M-3 -18 L4 -2 M1 -19 L7 -3" stroke="#c9a066" stroke-width="1.6" stroke-linecap="round"/></g>')
P["hayato"] = {
    "A": ("Hawk on his shoulder", "The hawk of the 鷹祭り festival that honours him",
          dict(extra=hawk)),
    "B": ("Soba bowl", "Loved buckwheat noodles more than poetry",
          dict(extra=soba)),
}

# --- You --------------------------------------------------------------------
scarf_you = ('<path d="M24 84 C34 92 66 92 76 84 L79 94 C66 103 34 103 21 94Z" fill="#c8102e" stroke="#7a0a1c" stroke-width="1.3"/>'
             '<path d="M23 89 C35 97 65 97 77 89" stroke="#ffc400" stroke-width="3.4" fill="none"/>')
hat = ('<ellipse cx="50" cy="31" rx="38" ry="7.4" fill="#e8c46a" stroke="#9a7a2a" stroke-width="1.2"/>'
       '<path d="M30 30 C30 14 40 9 50 9 C60 9 70 14 70 30Z" fill="#f0d27a" stroke="#9a7a2a" stroke-width="1.2"/>'
       '<path d="M30.6 25 C40 28 60 28 69.4 25 L69.8 29.6 C60 32 40 32 30.2 29.6Z" fill="#c8102e"/>'
       '<path d="M36 15 l2 12 M44 11 l1 15 M56 11 l-1 15 M64 15 l-2 12" stroke="#c9a54a" stroke-width=".8" opacity=".7"/>')
P["you"] = {
    "A": ("Red-and-yellow scarf", "A scarf in Spain's colours: you, the one from Spain",
          dict(_youscarf=True)),
    "B": ("Straw hat", "Mugiwara farm hat with a red band: the volunteer on the orchard",
          dict(_inhead=hat)),
}


def apply(cid, opt, base):
    """base: readability kwargs. opt: personality kwargs (with private _ keys)."""
    kw = dict(base)
    o = dict(opt)
    L = o.pop("layers", ORIG[cid]["layers"])
    if "_scarf" in o:
        L = L + o.pop("_scarf")
    if "_inhead" in o:
        L = L + o.pop("_inhead")
    if "_lanyard" in o:
        L = L + o.pop("_lanyard")
    if o.pop("_bob", False):
        sk = "#f6d9c4"
        L = L.replace(bun, "")
        # swap back hair for a bob silhouette (drawn before the body)
        old_back = '<path d="M21 52 C19 27 33 17 50 17 C67 17 81 27 79 52 C79 57 77 61 74 63 L26 63 C23 61 21 57 21 52Z" fill="#2a1c1c" stroke="#140c0c" stroke-width="1"/>'
        L = L.replace(old_back, bob)
        # side locks down to the jaw
        L = L + '<path d="M22 46 C21 56 22 63 25 68 L31 68 C28 61 27 54 28 45Z M78 46 C79 56 78 63 75 68 L69 68 C72 61 73 54 72 45Z" fill="#2a1c1c" stroke="#140c0c" stroke-width=".9"/>'
        L = L + C.glasses("rect", "#24305a")
    if o.pop("_sota_kit", False):
        L = L.replace('<path d="M24 104 C24 86 34 77 50 77 C66 77 76 86 76 104Z" fill="#2fa36b" stroke="#2a7a50" stroke-width="1.1"/>',
                      '<path d="M24 104 C24 86 34 77 50 77 C66 77 76 86 76 104Z" fill="#1f4fa8" stroke="#163a7a" stroke-width="1.1"/>')
        L = L.replace(stripes_old, blaugrana)
        L = L.replace('stroke="#23875a"', 'stroke="#ffc400"')
    if o.pop("_youscarf", False):
        kw["extra"] = scarf_you
    defs_extra = o.pop("_defs", "")
    kw.update(o)
    kw["layers"] = L
    s = render(cid, **kw)
    if defs_extra:
        s = s.replace("<defs>", "<defs>" + defs_extra, 1)
    return s


BASES = {
    "0-now": dict(),
    "1-zoom": dict(zoom=Z, sparkle=False),
    "2-zoom-outline": dict(zoom=Z, sparkle=False, outline=1.6),
}


def base_sig(cid, outline=1.6):
    return dict(zoom=Z, sparkle=False, outline=outline, bg=SIG[cid], ring=True)



PICK = {"tanaka": "B", "keiko": "A", "yuki": "A", "kenta": "A", "sato": "B", "hana": "A",
        "ren": "A", "sota": "A", "mio": "A", "hayato": "A", "you": "B"}

# ---------------------------------------------------------------- round 3: between 4 and 5
DY = {"kenta": 5, "hana": 4, "sota": 3, "hayato": 3}
camera2 = ('<path d="M34 80 L40 85 M66 80 L60 85" stroke="#7a4a2a" stroke-width="2.6" stroke-linecap="round"/>'
           '<g transform="translate(50 87)"><rect x="-14" y="-7" width="28" height="16" rx="3" fill="#2c2c30" stroke="#121214" stroke-width="1.2"/>'
           '<rect x="-14" y="-7" width="28" height="5" rx="2" fill="#c9c9cc"/><rect x="-10" y="-10.5" width="6" height="4" rx="1" fill="#c9c9cc"/>'
           '<circle cy="2" r="6" fill="#1a1a1d" stroke="#9a9aa0" stroke-width="1.4"/><circle cy="2" r="3" fill="#26304a"/><circle cx="-1" cy="1" r="1.1" fill="#7f8db0"/></g>')
goggles2 = ('<rect x="19" y="27" width="62" height="5" fill="#1f2430"/>'
            '<rect x="30" y="22" width="40" height="12" rx="6" fill="#2b2f3a" stroke="#14161c" stroke-width="1.1"/>'
            '<rect x="32.4" y="24" width="35.2" height="8" rx="4" fill="url(#gog)"/>'
            '<path d="M35.6 25.8 L40 25.8" stroke="#fff" stroke-width="1.4" stroke-linecap="round" opacity=".85"/>')

MID = {
    "tanaka": dict(),
    "keiko": dict(),
    "yuki": dict(),
    "kenta": dict(),
    "sato": dict(_bob=True),
    "hana": dict(),
    "ren": dict(layers=remove(ren, ren_gl), extra=camera2),
    "sota": dict(),
    "mio": dict(),
    "hayato": dict(),
    "you": dict(),
}
# small original props to keep (unzoomed corner props); others dropped
KEEP_DECO = {"tanaka"}


def mid(cid):
    b = base_sig(cid)
    b["dy"] = DY.get(cid, 0)
    o = dict(MID[cid])
    if cid not in KEEP_DECO:
        o.setdefault("deco", "")
    return apply(cid, o, b)



# ---------------------------------------------------------------- LINE B: selfies in their world
def bare(cid):
    """mid-style portrait with transparent background and no ring"""
    s = mid(cid)
    s = re.sub(r'<rect width="100" height="100" fill="url\(#bg\)"/>', "", s, count=1)
    s = re.sub(r'<circle cx="50" cy="50" r="48.6" fill="none"[^>]*/>', "", s)
    s = s.replace('<clipPath id="c"><circle cx="50" cy="50" r="50"/></clipPath>', '<clipPath id="c"><rect width="100" height="100"/></clipPath>')
    return s


def sky(top, bot, id_="sk"):
    return (f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>',
            f'<rect width="100" height="100" fill="url(#{id_})"/>')


def mountains(c1, c2, y=58):
    return (f'<path d="M0 {y} L14 {y-16} L26 {y-6} L42 {y-22} L58 {y-4} L72 {y-18} L88 {y-6} L100 {y-12} V100 H0Z" fill="{c1}"/>'
            f'<path d="M0 {y+10} L20 {y} L36 {y+8} L56 {y-2} L78 {y+8} L100 {y+2} V100 H0Z" fill="{c2}"/>')


def apple(x, y, r=4.4):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#e5484d" stroke="#9e2a2e" stroke-width=".7"/>'
            f'<ellipse cx="{x-1.4}" cy="{y-1.4}" rx="1" ry="1.5" fill="#fff" opacity=".45"/><path d="M{x} {y-r} v-2" stroke="#5b3a1a" stroke-width=".9"/>')


BGS = {}
d, b = sky("#8fd0f5", "#e8f6ff"); BGS["tanaka"] = (d, b + mountains("#8fb5a0", "#6fa35a")
    + '<path d="M-4 20 Q30 6 60 14 T104 8" stroke="#6b4a2a" stroke-width="3.4" fill="none"/>'
    + '<g fill="#4c9a44"><ellipse cx="18" cy="13" rx="6" ry="3" transform="rotate(-20 18 13)"/><ellipse cx="44" cy="10" rx="6" ry="3" transform="rotate(15 44 10)"/><ellipse cx="74" cy="12" rx="6" ry="3" transform="rotate(-10 74 12)"/><ellipse cx="94" cy="7" rx="5" ry="2.6"/></g>'
    + apple(10, 24) + apple(30, 20) + apple(84, 19) + apple(64, 22, 3.8))
d, b = sky("#cfe7d9", "#9cc8a8"); BGS["keiko"] = (d, b
    + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>' for x, y, r, c in [(8, 18, 12, "#8aa6f0"), (30, 6, 10, "#b18cf0"), (70, 6, 10, "#8aa6f0"), (93, 20, 12, "#b18cf0"), (4, 48, 9, "#b18cf0"), (97, 48, 9, "#8aa6f0")])
    + '<g fill="#fff" opacity=".55">' + "".join(f'<circle cx="{x}" cy="{y}" r=".9"/>' for x, y in [(6,14),(10,20),(28,4),(33,8),(68,4),(73,9),(90,17),(96,22),(3,46),(98,50)]) + '</g>'
    + '<g fill="#3f7a4e"><ellipse cx="18" cy="34" rx="9" ry="4" transform="rotate(30 18 34)"/><ellipse cx="84" cy="36" rx="9" ry="4" transform="rotate(-30 84 36)"/></g>')
d, b = sky("#1e1440", "#4a2a7a"); BGS["yuki"] = (d, b
    + '<rect x="2" y="4" width="16" height="44" fill="#2a1f55"/><rect x="82" y="2" width="18" height="50" fill="#2a1f55"/>'
    + '<rect x="4" y="8" width="12" height="9" rx="1.5" fill="#ff5c93"/><rect x="4" y="20" width="12" height="9" rx="1.5" fill="#4fd1ff"/><rect x="4" y="32" width="12" height="9" rx="1.5" fill="#ffe14d"/>'
    + '<rect x="85" y="6" width="12" height="10" rx="1.5" fill="#7cf29a"/><rect x="85" y="19" width="12" height="10" rx="1.5" fill="#ff5c93"/><rect x="85" y="32" width="12" height="10" rx="1.5" fill="#b18cf0"/>'
    + '<g fill="#1e1440" font-family="sans-serif" font-weight="700" font-size="6"><text x="7.4" y="15">ア</text><text x="7.4" y="27">ニ</text><text x="7.4" y="39">メ</text><text x="88" y="14">カ</text><text x="88" y="27">ラ</text><text x="88" y="40">オ</text></g>'
    + '<g fill="#fff"><circle cx="30" cy="8" r=".8"/><circle cx="52" cy="4" r=".6"/><circle cx="70" cy="10" r=".7"/></g>')
d, b = sky("#3f8de0", "#bfe3ff"); BGS["kenta"] = (d, b
    + '<path d="M0 50 L22 22 L34 34 L52 12 L70 32 L84 20 L100 40 V100 H0Z" fill="#f4f8ff"/><path d="M22 22 L28 30 L24 32Z M52 12 L58 22 L50 22Z M84 20 L90 28 L82 28Z" fill="#c9d9ef"/>'
    + '<path d="M0 64 Q50 50 100 66 V100 H0Z" fill="#ffffff"/><circle cx="86" cy="10" r="5" fill="#fff6c9"/>'
    )
d, b = sky("#3d5a4a", "#2f4a3c"); BGS["sato"] = (d, b
    + '<rect x="0" y="0" width="100" height="100" fill="#2f5240"/><rect x="0" y="64" width="100" height="4" fill="#8a6a4a"/>'
    + '<text x="16" y="20" font-family="Comic Sans MS, Chalkboard, cursive" font-size="9" fill="#f4f1e8" opacity=".92" transform="rotate(-4 16 20)">Hello!</text>'
    + '<path d="M70 14 h20 M70 20 h14" stroke="#f4f1e8" stroke-width="1.2" opacity=".6"/><path d="M80 8 l3 3 l5 -6" stroke="#ff8a8a" stroke-width="1.5" fill="none"/>'
    + '<rect x="12" y="66" width="6" height="2" fill="#f4f1e8"/><rect x="22" y="66" width="4" height="2" fill="#ffd166"/>')
d, b = sky("#c89a6a", "#a8784a"); BGS["hana"] = (d, b
    + '<rect width="100" height="40" fill="#e9dcc2"/><path d="M0 40 H100" stroke="#6b4a2a" stroke-width="2"/>'
    + '<path d="M8 0 V40 M50 0 V40 M92 0 V40" stroke="#c9b68e" stroke-width="1"/>'
    + '<rect x="0" y="0" width="100" height="16" fill="#5a3a7a"/><path d="M33 0 V16 M66 0 V16" stroke="#e9dcc2" stroke-width="1.4"/>'
    + '<text x="12" y="12" font-family="serif" font-size="9" fill="#f4ecd8" font-weight="700">和</text><text x="44" y="12" font-family="serif" font-size="9" fill="#f4ecd8" font-weight="700">菓</text><text x="77" y="12" font-family="serif" font-size="9" fill="#f4ecd8" font-weight="700">子</text>'
    + '<g transform="translate(10 52)"><ellipse rx="8" ry="2.6" fill="#f7f1e6"/><ellipse cx="-2.4" cy="-2" rx="3" ry="2.4" fill="#5a2a32"/><ellipse cx="2.4" cy="-2" rx="3" ry="2.4" fill="#5a2a32"/></g>')
d, b = sky("#f2c98a", "#8a5a3a"); BGS["ren"] = (d, b
    + '<rect x="0" y="0" width="100" height="60" fill="#f6dfb0"/><path d="M33 0 V60 M66 0 V60 M0 30 H100" stroke="#6b4a2a" stroke-width="2.4"/>'
    + '<circle cx="18" cy="16" r="9" fill="#fff3d0" opacity=".7"/><rect x="0" y="60" width="100" height="40" fill="#7a4a2a"/>'
    + '<g transform="translate(13 58)"><path d="M-5 -6 H5 L4 6 H-4Z" fill="#f2ede4" stroke="#8a7a66" stroke-width=".8"/><path d="M5 -3 q4 1 3 4 q-1 2 -4 1" stroke="#f2ede4" stroke-width="1.4" fill="none"/>'
    + '<path d="M-1 -9 q-1.4 -2 0 -4 M2 -9 q-1.4 -2 0 -4" stroke="#fff" stroke-width=".9" fill="none"/></g>')
d, b = sky("#a8d672", "#4c8a3a"); BGS["sota"] = (d, b
    + '<circle cx="12" cy="10" r="14" fill="#7cbf52"/><circle cx="88" cy="8" r="16" fill="#7cbf52"/><circle cx="50" cy="-4" r="14" fill="#8fcf60"/>'
    + '<rect x="2" y="20" width="12" height="80" fill="#7a5230"/><path d="M5 30 q2 4 0 8 M9 46 q2 4 0 8" stroke="#5a3a1c" stroke-width=".9" fill="none"/>'
    + '<g transform="translate(8 44) rotate(-10)"><ellipse rx="3.4" ry="4.4" fill="#5a3418" stroke="#2a160a" stroke-width=".6"/><path d="M0 -4.4 l-1 -3 l1.6 1" stroke="#2a160a" stroke-width=".9" fill="none"/></g>'
    + '<g transform="translate(90 50)"><circle r="6" fill="#fff" stroke="#2a1e24" stroke-width=".9"/><path d="M0 -2.2 L2.2 -.7 L1.3 2 H-1.3 L-2.2 -.7Z" fill="#2a1e24"/></g>')
d, b = sky("#ff9f7a", "#7a5ad9"); BGS["mio"] = (d, b
    + '<rect y="62" width="100" height="38" fill="#3a2f6a"/><g fill="#5a4a9a"><rect x="0" y="40" width="10" height="22"/><rect x="12" y="34" width="8" height="28"/><rect x="80" y="30" width="9" height="32"/><rect x="90" y="38" width="10" height="24"/></g>'
    + '<g fill="#ffe08a"><rect x="2" y="44" width="2" height="2"/><rect x="6" y="50" width="2" height="2"/><rect x="14" y="40" width="2" height="2"/><rect x="83" y="36" width="2" height="2"/><rect x="93" y="44" width="2" height="2"/></g>'
    + '<path d="M70 8 l1.2 3 l3 1.2 l-3 1.2 l-1.2 3 l-1.2 -3 l-3 -1.2 l3 -1.2Z" fill="#fff"/><circle cx="24" cy="12" r=".9" fill="#fff"/>')
d, b = sky("#1d2440", "#3a4a7a"); BGS["hayato"] = (d, b
    + '<circle cx="80" cy="16" r="9" fill="#fff6d6"/><circle cx="83" cy="14" r="8" fill="#1d2440" opacity=".0"/>'
    + mountains("#2a3358", "#202848", 56)
    + '<g transform="translate(16 36)"><path d="M-9 4 H9 L7 0 H-7Z" fill="#141a30"/><rect x="-6" y="4" width="12" height="6" fill="#141a30"/><path d="M-7 -1 H7 L4 -5 H-4Z" fill="#141a30"/><rect x="-3" y="5" width="2" height="2" fill="#ffd166"/></g>'
    + '<g fill="#fff"><circle cx="30" cy="8" r=".6"/><circle cx="50" cy="14" r=".5"/><circle cx="60" cy="5" r=".6"/><circle cx="8" cy="12" r=".5"/></g>')
d, b = sky("#6fb6ee", "#d8efff"); BGS["you"] = (d, b
    + '<circle cx="84" cy="14" r="6" fill="#fff6c9"/>'
    + '<path d="M-10 70 C6 58 14 40 22 26 L26 22 L31 21 L35 23 L40 28 C48 42 60 58 80 70Z" fill="#5a78b8"/>'
    + '<path d="M22 26 L26 22 L31 21 L35 23 L40 28 C38 32 36 30 34 34 C32 30 30 33 28 31 C26 34 24 31 21 35 C18 33 20 30 22 26Z" fill="#ffffff"/>'
    + '<path d="M26 22 L31 21 L35 23" stroke="#e6eef8" stroke-width=".8" fill="none"/>'
    + '<path d="M18 40 C22 38 24 44 30 42 M34 46 C38 44 40 50 46 48" stroke="#8aa4d6" stroke-width="1" fill="none" opacity=".7"/>'
    + '<g fill="#fff" opacity=".9"><ellipse cx="64" cy="30" rx="10" ry="3.4"/><ellipse cx="70" cy="27" rx="6" ry="3"/><ellipse cx="8" cy="18" rx="8" ry="2.6"/></g>'
    + '<path d="M0 72 Q50 64 100 72 V100 H0Z" fill="#3f7fc0"/><path d="M6 76 h10 M30 74 h14 M70 76 h12" stroke="#cfe6ff" stroke-width="1" opacity=".8"/>')


def selfie(cid):
    defs, back = BGS[cid]
    p = bare(cid)
    inner = p[p.index(">") + 1: p.rindex("</svg>")]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs>{defs}'
            f'<clipPath id="sc"><circle cx="50" cy="50" r="50"/></clipPath>'
            f'<radialGradient id="vg" cx="50%" cy="45%" r="62%"><stop offset="65%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".22"/></radialGradient></defs>'
            f'<g clip-path="url(#sc)">{back}'
            f'<g transform="rotate(-6 54 60)"><svg x="15" y="19" width="78" height="78" viewBox="0 0 100 100" overflow="visible">{inner}</svg></g>'
            f'<rect width="100" height="100" fill="url(#vg)"/></g></svg>')




if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")
    for cid in IDS:
        open(os.path.join(root, "cast", cid + ".svg"), "w").write(mid(cid))
        open(os.path.join(root, "line", cid + ".svg"), "w").write(selfie(cid))
    print("wrote", len(IDS), "portraits and", len(IDS), "LINE pictures")
