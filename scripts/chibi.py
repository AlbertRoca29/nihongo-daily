#!/usr/bin/env python3
"""Draws the chibi character portraits -> icons/cast/<id>.svg

Original flat-vector chibi portraits (big head, small body, big eyes), one per
cast member, Keiko and You. Run: python3 scripts/chibi.py
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons", "cast")

INK = "#2a1e24"


def shade(hexc, f):
    """Darken (f<1) or lighten (f>1) a #rrggbb colour."""
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if f < 1:
        r, g, b = (int(c * f) for c in (r, g, b))
    else:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------- face parts (head: x 23..77, top 21, chin 70; eyes at y 50) ----------
HEAD = "M23 46 C23 29 35 20 50 20 C65 20 77 29 77 46 C77 61 66 71 50 71 C34 71 23 61 23 46Z"
EY = 50
EX = (38.5, 61.5)


def head(skin):
    line = shade(skin, .78)
    return (f'<ellipse cx="22.5" cy="51" rx="4" ry="5.2" fill="{skin}" stroke="{line}" stroke-width="1"/>'
            f'<ellipse cx="77.5" cy="51" rx="4" ry="5.2" fill="{skin}" stroke="{line}" stroke-width="1"/>'
            f'<path d="{HEAD}" fill="{skin}" stroke="{line}" stroke-width="1.1"/>'
            f'<path d="M30 62 C36 69 44 71 50 71" stroke="{shade(skin, .9)}" stroke-width="2" fill="none" opacity=".5"/>')


def eye_open(cx, iris, sharp=False, look=0):
    cy = EY
    x = cx + look
    s = [f'<ellipse cx="{cx}" cy="{cy}" rx="5.4" ry="6.6" fill="#fff"/>',
         f'<ellipse cx="{x}" cy="{cy+.6}" rx="4.6" ry="5.8" fill="url(#iris)"/>',
         f'<ellipse cx="{x}" cy="{cy+1}" rx="2.3" ry="3.1" fill="#1a1218"/>',
         f'<ellipse cx="{x}" cy="{cy+3.6}" rx="3" ry="1.4" fill="{shade(iris, 1.6)}" opacity=".55"/>',
         f'<circle cx="{x+1.7}" cy="{cy-2.2}" r="1.7" fill="#fff"/>',
         f'<circle cx="{x-1.8}" cy="{cy+2.4}" r=".8" fill="#fff"/>']
    # upper lash line with a small outer flick
    side = 1 if cx > 50 else -1
    o = cx + 5.9 * side
    lash = f'M{cx - 6*side} {cy-2.4} Q{cx} {cy-9.2} {o} {cy-3}'
    flick = f'M{o} {cy-3} l{1.8*side} -1.6' if not sharp else f'M{o} {cy-3} l{2.4*side} -2.6'
    s.append(f'<path d="{lash}" stroke="{INK}" stroke-width="{2.3 if sharp else 1.9}" fill="none" stroke-linecap="round"/>')
    s.append(f'<path d="{flick}" stroke="{INK}" stroke-width="1.5" fill="none" stroke-linecap="round"/>')
    return "".join(s)


def eye_calm(cx, iris, skin):
    """Half-lidded, relaxed (Ren, Tanaka-san)."""
    cy = EY
    i = int(cx)
    s = [f'<clipPath id="lid{i}"><rect x="{cx-7}" y="{cy-2.2}" width="14" height="12"/></clipPath>',
         f'<g clip-path="url(#lid{i})"><ellipse cx="{cx}" cy="{cy}" rx="5.2" ry="6.2" fill="#fff"/>'
         f'<ellipse cx="{cx}" cy="{cy+.8}" rx="4.4" ry="5.4" fill="url(#iris)"/>'
         f'<ellipse cx="{cx}" cy="{cy+1.2}" rx="2.2" ry="2.8" fill="#1a1218"/>'
         f'<circle cx="{cx+1.6}" cy="{cy+.2}" r="1.3" fill="#fff"/></g>',
         f'<path d="M{cx-6} {cy-2} Q{cx} {cy-3.6} {cx+6} {cy-2}" stroke="{INK}" stroke-width="2" fill="none" stroke-linecap="round"/>']
    return "".join(s)


def eye_happy(cx):
    cy = EY + 1
    return f'<path d="M{cx-5} {cy+1.5} Q{cx} {cy-5} {cx+5} {cy+1.5}" stroke="{INK}" stroke-width="2.3" fill="none" stroke-linecap="round"/>'


def eye_wink(cx):
    cy = EY + 1
    return (f'<path d="M{cx-5} {cy-2} L{cx+3} {cy} L{cx-5} {cy+2.4}" stroke="{INK}" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def brows(kind, color=INK):
    y = EY - 10.5
    L, R = EX
    if kind == "soft":
        d = f"M{L-4.5} {y+.6} Q{L} {y-1.6} {L+4.5} {y+.2} M{R-4.5} {y+.2} Q{R} {y-1.6} {R+4.5} {y+.6}"
        return f'<path d="{d}" stroke="{color}" stroke-width="1.6" fill="none" stroke-linecap="round" opacity=".85"/>'
    if kind == "up":  # cheerful, raised
        d = f"M{L-4.5} {y} Q{L} {y-3} {L+4.5} {y-.6} M{R-4.5} {y-.6} Q{R} {y-3} {R+4.5} {y}"
        return f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round"/>'
    if kind == "stern":
        d = f"M{L-5} {y-2} L{L+5} {y+1.6} M{R-5} {y+1.6} L{R+5} {y-2}"
        return f'<path d="{d}" stroke="{color}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    if kind == "bushy":
        d = f"M{L-5} {y+.5} Q{L} {y-2.4} {L+5} {y+.5} M{R-5} {y+.5} Q{R} {y-2.4} {R+5} {y+.5}"
        return f'<path d="{d}" stroke="{color}" stroke-width="3.4" fill="none" stroke-linecap="round"/>'
    return ""


def mouth(kind):
    y = 62.5
    if kind == "smile":
        return f'<path d="M46 {y} Q50 {y+3.6} 54 {y}" stroke="#7a2e35" stroke-width="1.7" fill="none" stroke-linecap="round"/>'
    if kind == "small":
        return f'<path d="M47.6 {y+.6} Q50 {y+2.2} 52.4 {y+.6}" stroke="#7a2e35" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    if kind == "open":
        return (f'<path d="M45 {y-.6} Q50 {y-1.4} 55 {y-.6} Q54.4 {y+6.4} 50 {y+6.6} Q45.6 {y+6.4} 45 {y-.6}Z" fill="#7a2e35"/>'
                f'<ellipse cx="50" cy="{y+4.6}" rx="2.8" ry="1.6" fill="#ef7f8a"/>')
    if kind == "grin":
        return (f'<path d="M43.5 {y-1.4} Q50 {y-2.4} 56.5 {y-1.4} Q55.4 {y+6.8} 50 {y+7} Q44.6 {y+6.8} 43.5 {y-1.4}Z" fill="#7a2e35"/>'
                f'<path d="M44.4 {y-.9} Q50 {y-1.6} 55.6 {y-.9} L55 {y+1.4} Q50 {y+.8} 45 {y+1.4}Z" fill="#fff"/>'
                f'<ellipse cx="50" cy="{y+5}" rx="3.2" ry="1.6" fill="#ef7f8a"/>')
    if kind == "gap":  # kid grin with a missing tooth
        return (f'<path d="M43.5 {y-1.4} Q50 {y-2.4} 56.5 {y-1.4} Q55.4 {y+6.8} 50 {y+7} Q44.6 {y+6.8} 43.5 {y-1.4}Z" fill="#7a2e35"/>'
                f'<path d="M44.4 {y-.9} Q47 {y-1.4} 48.6 {y-1.5} L48.6 {y+1} Q46.5 {y+1} 45 {y+1.4}Z M51.6 {y-1.5} Q53 {y-1.4} 55.6 {y-.9} L55 {y+1.4} Q53.5 {y+1} 51.6 {y+1}Z" fill="#fff"/>'
                f'<ellipse cx="50" cy="{y+5}" rx="3.2" ry="1.6" fill="#ef7f8a"/>')
    if kind == "cat":
        return f'<path d="M45.4 {y} Q47.7 {y+2.6} 50 {y} Q52.3 {y+2.6} 54.6 {y}" stroke="#7a2e35" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    if kind == "firm":
        return f'<path d="M46.2 {y+1.2} Q50 {y+.2} 53.8 {y+1.2}" stroke="#7a2e35" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
    return ""


def blush(strength=.42):
    return (f'<ellipse cx="31.5" cy="59" rx="4.6" ry="2.6" fill="#ff8a95" opacity="{strength}"/>'
            f'<ellipse cx="68.5" cy="59" rx="4.6" ry="2.6" fill="#ff8a95" opacity="{strength}"/>'
            f'<path d="M29.5 58.4 l1.4 -1.6 M32.5 58.4 l1.4 -1.6 M66.5 58.4 l1.4 -1.6 M69.5 58.4 l1.4 -1.6" stroke="#fff" stroke-width=".8" stroke-linecap="round" opacity=".7"/>')


def nose(skin):
    return f'<path d="M49.4 56.6 q.8 .9 1.8 .2" stroke="{shade(skin, .7)}" stroke-width="1.2" fill="none" stroke-linecap="round"/>'


def glasses(shape, color):
    L, R = EX
    if shape == "round":
        return (f'<g fill="none" stroke="{color}" stroke-width="1.6"><circle cx="{L}" cy="{EY+.5}" r="8.2"/><circle cx="{R}" cy="{EY+.5}" r="8.2"/>'
                f'<path d="M{L+8} {EY-.5} Q50 {EY-3} {R-8} {EY-.5} M{L-8.2} {EY-1} L23 {EY-3} M{R+8.2} {EY-1} L77 {EY-3}"/></g>'
                f'<path d="M{L-5} {EY-4} l3 -2.4 M{R-5} {EY-4} l3 -2.4" stroke="#fff" stroke-width="1.2" stroke-linecap="round" opacity=".8"/>')
    if shape in ("bold", "tort", "browline"):
        top = shade(color, .6)
        g = [f'<g fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round">'
             f'<rect x="{L-8.8}" y="{EY-6.8}" width="17.6" height="13.4" rx="3.6"/><rect x="{R-8.8}" y="{EY-6.8}" width="17.6" height="13.4" rx="3.6"/>'
             f'<path d="M{L+8.8} {EY-2} Q50 {EY-4.4} {R-8.8} {EY-2}"/><path d="M{L-8.8} {EY-3} L23 {EY-4.6} M{R+8.8} {EY-3} L77 {EY-4.6}" stroke-width="2"/></g>']
        if shape == "tort":
            g.append(f'<g fill="none" stroke="#c9873f" stroke-width="1" stroke-dasharray="1.6 2.4" opacity=".75"><rect x="{L-8.8}" y="{EY-6.8}" width="17.6" height="13.4" rx="3.6"/><rect x="{R-8.8}" y="{EY-6.8}" width="17.6" height="13.4" rx="3.6"/></g>')
        if shape == "browline":
            g.append(f'<path d="M{L-9.4} {EY-5.4} Q{L} {EY-8.6} {L+9.4} {EY-5.4} M{R-9.4} {EY-5.4} Q{R} {EY-8.6} {R+9.4} {EY-5.4}" stroke="{top}" stroke-width="3.6" fill="none" stroke-linecap="round"/>')
        g.append(f'<path d="M{L-5.4} {EY-3} l3 -2.2 M{R-5.4} {EY-3} l3 -2.2" stroke="#fff" stroke-width="1.2" stroke-linecap="round" opacity=".8"/>')
        return "".join(g)
    if shape == "thin":
        return (f'<g fill="none" stroke="{color}" stroke-width="1.1"><ellipse cx="{L}" cy="{EY+.5}" rx="8.4" ry="6.8"/><ellipse cx="{R}" cy="{EY+.5}" rx="8.4" ry="6.8"/>'
                f'<path d="M{L+8.4} {EY-.6} Q50 {EY-2.6} {R-8.4} {EY-.6} M{L-8.4} {EY-1} L23 {EY-3} M{R+8.4} {EY-1} L77 {EY-3}"/></g>'
                f'<path d="M{L-5} {EY-3} l2.6 -2 M{R-5} {EY-3} l2.6 -2" stroke="#fff" stroke-width="1.1" stroke-linecap="round" opacity=".8"/>')
    # rounded rectangle
    return (f'<g fill="none" stroke="{color}" stroke-width="1.7"><rect x="{L-8.6}" y="{EY-6.6}" width="17.2" height="13.6" rx="4.4"/>'
            f'<rect x="{R-8.6}" y="{EY-6.6}" width="17.2" height="13.6" rx="4.4"/>'
            f'<path d="M{L+8.6} {EY-1.6} Q50 {EY-3.6} {R-8.6} {EY-1.6} M{L-8.6} {EY-2} L23 {EY-4} M{R+8.6} {EY-2} L77 {EY-4}"/></g>'
            f'<path d="M{L-5.4} {EY-3.4} l3 -2.2 M{R-5.4} {EY-3.4} l3 -2.2" stroke="#fff" stroke-width="1.2" stroke-linecap="round" opacity=".8"/>')


def body(color, skin, detail=""):
    line = shade(color, .75)
    return (f'<rect x="45" y="66" width="10" height="10" fill="{shade(skin, .9)}"/>'
            f'<path d="M24 104 C24 86 34 77 50 77 C66 77 76 86 76 104Z" fill="{color}" stroke="{line}" stroke-width="1.1"/>'
            + detail)


def hair_shine(d):
    return f'<path d="{d}" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round" opacity=".38"/>'


def svg(cid, bg, iris, layers, deco=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="{cid}">'
            f'<defs><clipPath id="c"><circle cx="50" cy="50" r="50"/></clipPath>'
            f'<radialGradient id="bg" cx="50%" cy="38%" r="70%"><stop offset="0" stop-color="{shade(bg, 1.45)}"/><stop offset="1" stop-color="{bg}"/></radialGradient>'
            f'<linearGradient id="iris" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{shade(iris, .55)}"/><stop offset=".6" stop-color="{iris}"/><stop offset="1" stop-color="{shade(iris, 1.35)}"/></linearGradient>'
            f'</defs><g clip-path="url(#c)"><rect width="100" height="100" fill="url(#bg)"/>{deco}{layers}</g></svg>')


def sparkles(color="#fff", op=.85):
    return (f'<g fill="{color}" opacity="{op}"><path d="M13 24 l1.6 -4.6 l1.6 4.6 l4.6 1.6 l-4.6 1.6 l-1.6 4.6 l-1.6 -4.6 l-4.6 -1.6Z"/>'
            f'<path d="M86 66 l1.1 -3.2 l1.1 3.2 l3.2 1.1 l-3.2 1.1 l-1.1 3.2 l-1.1 -3.2 l-3.2 -1.1Z"/><circle cx="84" cy="22" r="1.3"/><circle cx="14" cy="70" r="1"/></g>')


# Your look (the learner). Change and rerun to update icons/cast/you.svg.
YOU = {"hair": "messy", "gl": "rect", "hr": "#3a2518"}

YOU_HAIR = {
    # short crop, natural hairline with a slight dip at the temples
    "crop": ('M23 46 C22 29 32 18 50 18 C68 18 78 29 77 46 C76 40 74 36 70.5 33.5 C68 31.5 66 29 63 27.6 C58.5 28.6 54 30 50 30.6 C46 30 41.5 28.6 37 27.6 C34 29 32 31.5 29.5 33.5 C26 36 24 40 23 46Z', ""),
    # short with a side parting, swept to the right
    "part": ('M23 46 C22 28 32 17 50 17 C68 17 79 28 77 46 C75 39 72 34 67 32 C60 30.5 52 30 45 30.4 L40 25 C37 28.4 33 32 30 34.4 C26.6 37.4 24.4 41 23 46Z',
             '<path d="M40 25 C41 22 43 19.6 45 18.4" stroke="{d}" stroke-width="1.2" fill="none"/><path d="M47 22 C55 21 64 23 70 28" stroke="{d}" stroke-width="1" fill="none" opacity=".6"/>'),
    # textured quiff pushed up at the front
    "quiff": ('M23 46 C21 29 29 17 41 13.4 C49 11 61 11.4 68 16 C76 21 79 32 77 46 C75 39 72 34.4 67.4 31.6 C60 29.6 52 30 46 30.4 C40 30.6 35 31.4 31 33.4 C27 36 24.4 41 23 46Z',
              '<path d="M40 15.6 C46 13 54 13 60 15.4 M38 21 C45 18 55 18 63 21" stroke="{d}" stroke-width="1" fill="none" opacity=".6"/>'),
    # soft fringe swept across the forehead
    "fringe": ('M23 46 C22 28 33 17 50 17 C67 17 78 27 77 46 C75 38.4 71 33.6 64 31 C57 35.6 45 39 34 39.4 C29.6 39.8 25.6 42 23 46Z',
               '<path d="M62 31.4 C55 34.6 46 36.8 38 37.6 M58 27 C52 30 45 32 38 33" stroke="{d}" stroke-width="1" fill="none" opacity=".6"/>'),
    # messy textured top
    "messy": ('M23 46 C21.5 31 28 21.5 37 19 L39 16 L43 18.4 L47 15.4 L51 18 L56 15.6 L59 18.6 L64 17 C73 21 79 31 77 46 C76 40.5 74 37 70.5 34 C67.5 31 64.5 28 61.5 27 L57.5 28.6 L53.5 26.4 L49.5 28.8 L45.5 26.6 L41.5 28.4 L38.5 26.4 C35 27.6 32 30.6 29.5 33 C26 36 24 40 23 46Z', ""),
    # very short buzz cut
    "buzz": ('M24 44 C23 29 34 20 50 20 C66 20 77 29 76 44 C74.6 37.6 71.6 32.6 66.6 30.6 C60 29.4 40 29.4 33.4 30.6 C28.4 32.6 25.4 37.6 24 44Z',
             '<g fill="{d}" opacity=".35"><circle cx="40" cy="25" r=".6"/><circle cx="46" cy="23.4" r=".6"/><circle cx="53" cy="23.4" r=".6"/><circle cx="60" cy="25" r=".6"/><circle cx="35" cy="28" r=".6"/><circle cx="65" cy="28" r=".6"/><circle cx="50" cy="26.4" r=".6"/></g>'),
}


def make_you(hair="crop", gl="rect", hr="#5b3b26"):
    """You (the learner): from Spain, clean-shaven, glasses."""
    sk, d = "#ecc4a0", shade(hr, .72)
    path, extra = YOU_HAIR[hair]
    gcol = {"thin": "#8a6d3b", "bold": "#6b4226", "tort": "#5a3418", "browline": "#7a4a2a"}.get(gl, "#2b2230")
    return svg("you", "#bff0d2", "#5a3a22",
        body("#1e7a52", sk,
             '<path d="M40 78 L50 88 L60 78Z" fill="#f4efe6" stroke="#d9d2c4" stroke-width="1"/><path d="M36 79 L44 90 L41 79Z M64 79 L56 90 L59 79Z" fill="#17603f"/>'
             '<path d="M50 88 V104" stroke="#17603f" stroke-width="1.2"/><circle cx="58" cy="95" r="1.2" fill="#d9e8df"/>')
        + head(sk)
        + f'<path d="{path}" fill="{hr}" stroke="{d}" stroke-width="1" stroke-linejoin="round"/>'
        + extra.replace("{d}", d)
        + f'<path d="M23 46 C23 50 24 53 25 55 L27 53 C26 50 26 47 27 44Z M77 46 C77 50 76 53 75 55 L73 53 C74 50 74 47 73 44Z" fill="{hr}"/>'
        + hair_shine("M36 22 Q42 19.4 48 19.8")
        + eye_open(EX[0], "#7a4a28") + eye_open(EX[1], "#7a4a28") + brows("soft", shade(hr, .8))
        + glasses(gl, gcol) + nose(sk) + mouth("smile") + blush(.3),
        sparkles())


def build():
    A = {}

    # ---------------- Tanaka-san: 67, apple farmer, towel headband, kind squint ----------------
    sk, hr = "#e3b48c", "#a9a6a2"
    A["tanaka"] = svg("tanaka", "#bfe3b0", "#4a3226",
        '<path d="M21 52 C20 38 24 30 30 26 L34 46Z M79 52 C80 38 76 30 70 26 L66 46Z" fill="#8f8c88"/>'
        + body("#3f5f80", sk,
               '<path d="M38 79 L50 96 L62 79" fill="none" stroke="#e8e2d2" stroke-width="3"/><path d="M41 78 L50 92 L59 78" fill="#2f4a66"/>'
               '<path d="M30 92 h8 M62 92 h8" stroke="#2f4a66" stroke-width="1.5"/>')
        + head(sk)
        + f'<path d="M23 44 C22 34 25 28 30 25 C29 31 29 37 31 43Z M77 44 C78 34 75 28 70 25 C71 31 71 37 69 43Z" fill="{hr}" stroke="#86837f" stroke-width=".8"/>'
        + '<path d="M28 27 C36 20 64 20 72 27" stroke="#c7c4bf" stroke-width="3" fill="none" stroke-linecap="round"/>'
        + eye_calm(EX[0], "#4a3226", sk) + eye_calm(EX[1], "#4a3226", sk) + brows("soft", "#8f8b86") + brows("soft", "#b3afa9")
        + f'<path d="M30 52 l-2.4 1.2 M70 52 l2.4 1.2" stroke="{shade(sk,.72)}" stroke-width=".9" stroke-linecap="round"/>'
        + nose(sk) + mouth("smile") + blush(.32)
        # hachimaki towel
        + '<path d="M22 36 C34 28 66 28 78 36 L78 42 C66 34 34 34 22 42Z" fill="#f7f5ef" stroke="#cfcac0" stroke-width=".8"/>'
        + '<path d="M26 37 C38 31 62 31 74 37" stroke="#3d6fb3" stroke-width="1.6" fill="none" stroke-dasharray="3.2 2.4"/>'
        + '<path d="M77 38 l9 -5 l-2 7 l6 1 l-9 4Z" fill="#f7f5ef" stroke="#cfcac0" stroke-width=".8"/>',
        sparkles("#fff", .6) + '<g transform="translate(83 78)"><circle r="6" fill="#e5484d"/><path d="M0 -6 q1 -3 3 -4" stroke="#5b3a1a" stroke-width="1.3" fill="none"/><ellipse cx="3.6" cy="-8.6" rx="2.6" ry="1.3" fill="#4c9a44"/><ellipse cx="-2" cy="-2.4" rx="1.3" ry="2" fill="#fff" opacity=".45"/></g>')

    # ---------------- Keiko: 64, warm, permed curls, apron, laughing ----------------
    sk, hr = "#f2cfb2", "#7b6155"
    curls = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{hr}" stroke="#634c42" stroke-width=".8"/>' for x, y, r in
                    [(25, 50, 6.5), (75, 50, 6.5), (24, 40, 7), (76, 40, 7), (28, 30, 7.5), (72, 30, 7.5), (37, 22, 8), (63, 22, 8), (50, 19, 8.5)])
    A["keiko"] = svg("keiko", "#ffd9bf", "#5a3a2a",
        curls
        + body("#d9694a", sk, '<path d="M36 82 Q50 88 64 82 L66 104 L34 104Z" fill="#f5c84c" stroke="#d9a92e" stroke-width="1"/>'
               '<path d="M40 82 L37 77 M60 82 L63 77" stroke="#f5c84c" stroke-width="2.4"/><rect x="45" y="92" width="10" height="7" rx="2" fill="#e8b83a"/>')
        + head(sk)
        + f'<g fill="{hr}" stroke="#634c42" stroke-width=".8"><circle cx="31" cy="31" r="6.5"/><circle cx="41" cy="27" r="6.5"/><circle cx="51" cy="26" r="6.5"/><circle cx="61" cy="27" r="6.5"/><circle cx="69" cy="31" r="6.5"/><circle cx="25" cy="40" r="4.5"/><circle cx="75" cy="40" r="4.5"/></g>'
        + hair_shine("M37 23 Q42 20 47 21")
        + eye_happy(EX[0]) + eye_happy(EX[1]) + brows("up", "#5f4a40")
        + nose(sk) + mouth("open") + blush(.5)
        + f'<path d="M29 54 l-2.2 1 M71 54 l2.2 1" stroke="{shade(sk,.72)}" stroke-width=".9" stroke-linecap="round"/>',
        sparkles())

    # ---------------- Yuki: 25, Tokyo, bob + cat-ear headphones, otaku ----------------
    sk, hr = "#f8dcc8", "#6b3e2b"
    A["yuki"] = svg("yuki", "#ffc9de", "#7a4a30",
        f'<path d="M19 48 C17 25 32 13 50 13 C68 13 83 25 81 48 L82 70 C82 75 75 77 71 72 L29 72 C25 77 18 75 18 70Z" fill="{hr}" stroke="#552f20" stroke-width="1"/>'
        + body("#ffffff", sk, '<path d="M24 104 C24 86 34 77 50 77 C66 77 76 86 76 104Z" fill="none" stroke="#d9d6e3" stroke-width="1"/>'
               '<path d="M42 78 L50 86 L58 78" fill="#eceaf3" stroke="#d0cde0" stroke-width="1"/><circle cx="50" cy="90" r="1.3" fill="#c9c5da"/><circle cx="50" cy="97" r="1.3" fill="#c9c5da"/>'
               '<rect x="58" y="88" width="8" height="10" rx="1.5" fill="#ff7aa8"/><path d="M60 90 h4" stroke="#fff" stroke-width="1"/>')
        + head(sk)
        + f'<path d="M22 46 C21 52 22 63 27 70 L31 68 C27 60 27 52 28 45Z M78 46 C79 52 78 63 73 70 L69 68 C73 60 73 52 72 45Z" fill="{hr}" stroke="#552f20" stroke-width=".9"/>'
        + f'<path d="M22 45 C21 26 34 16 50 16 C66 16 79 26 78 45 C75 38 71 33 66 30 C64 37 58 39 54 33 C51 39 45 40 42 33 C38 38 32 40 22 45Z" fill="{hr}" stroke="#552f20" stroke-width="1"/>'
        + hair_shine("M33 23 Q40 19 47 19.5")
        + eye_open(EX[0], "#8a5234") + eye_open(EX[1], "#8a5234") + brows("soft", "#5a3424")
        + nose(sk) + mouth("cat") + blush(.5)
        # cat-ear headphones
        + '<path d="M17 47 C16 12 84 12 83 47" stroke="#ff5c93" stroke-width="4.2" fill="none" stroke-linecap="round"/>'
        + '<path d="M30 22 L29 9 L40 16Z M70 22 L71 9 L60 16Z" fill="#ff5c93" stroke="#d93f75" stroke-width="1" stroke-linejoin="round"/>'
        + '<path d="M31.6 18.6 L31.2 13 L36 16Z M68.4 18.6 L68.8 13 L64 16Z" fill="#ffd0e0"/>'
        + '<rect x="11" y="42" width="11" height="17" rx="5.5" fill="#ff5c93" stroke="#d93f75" stroke-width="1"/><rect x="78" y="42" width="11" height="17" rx="5.5" fill="#ff5c93" stroke="#d93f75" stroke-width="1"/>'
        + '<rect x="13.5" y="45" width="3" height="9" rx="1.5" fill="#ffd0e0"/><rect x="83.5" y="45" width="3" height="9" rx="1.5" fill="#ffd0e0"/>',
        sparkles() + '<path d="M84 82 q-3 -4 0 -6 q2 -1 3 1 q1 -2 3 -1 q3 2 0 6 l-3 3Z" fill="#ff5c93"/>')

    # ---------------- Kenta: 24, Osaka, beanie, wink + big grin, hoodie ----------------
    sk, hr = "#eabf98", "#9a5a2a"
    A["kenta"] = svg("kenta", "#ffd9a6", "#4a2e1e",
        body("#f07f2e", sk,
             '<path d="M33 80 Q50 92 67 80 Q60 77 50 77 Q40 77 33 80Z" fill="#d9661a" stroke="#b9541a" stroke-width="1"/>'
             '<path d="M45 85 l-1 12 M55 85 l1 12" stroke="#fff3e6" stroke-width="1.6" stroke-linecap="round"/><circle cx="44" cy="97.5" r="1.4" fill="#fff3e6"/><circle cx="56" cy="97.5" r="1.4" fill="#fff3e6"/>')
        + head(sk)
        + f'<path d="M22 43 C20 48 20 53 22 57 C24 54 26 50 28 47Z M78 43 C80 48 80 53 78 57 C76 54 74 50 72 47Z" fill="{hr}" stroke="#7a431c" stroke-width=".9"/>'
        + f'<path d="M27 40 L30 47 L34 41 L38 48 L42 41 L46 47 L50 41 L54 47 L58 41 L62 48 L66 41 L70 47 L73 40Z" fill="{hr}" stroke="#7a431c" stroke-width=".9" stroke-linejoin="round"/>'
        + eye_wink(EX[0]) + eye_open(EX[1], "#6a4028") + brows("up", "#6a3a1c")
        + nose(sk) + mouth("grin") + blush(.4)
        # beanie
        + '<path d="M20 42 C19 17 33 8 50 8 C67 8 81 17 80 42Z" fill="#2b8c8c" stroke="#1f6b6b" stroke-width="1.1"/>'
        + '<path d="M30 16 C32 24 33 32 33 40 M40 11 C41 20 42 30 42 40 M50 9 V40 M60 11 C59 20 58 30 58 40 M70 16 C68 24 67 32 67 40" stroke="#237777" stroke-width="1.2" fill="none"/>'
        + '<rect x="18" y="34" width="64" height="10" rx="5" fill="#1f6b6b"/><path d="M22 39 H78" stroke="#2b8c8c" stroke-width="1" stroke-dasharray="2 2"/>'
        + '<circle cx="50" cy="8" r="6.5" fill="#ffd166" stroke="#e5b23c" stroke-width="1"/><path d="M46 6 q2 -2 4 0" stroke="#fff" stroke-width="1" fill="none" opacity=".7"/>',
        sparkles())

    # ---------------- Sato-sensei: 41, teacher, top bun, glasses, blazer ----------------
    sk, hr = "#f6d9c4", "#2a1c1c"
    A["sato"] = svg("sato", "#c9dcfa", "#3a2a26",
        f'<circle cx="50" cy="14" r="9.5" fill="{hr}" stroke="#140c0c" stroke-width="1"/><path d="M44 12 q6 -5 12 0" stroke="#4a3434" stroke-width="1.2" fill="none"/>'
        + f'<path d="M21 52 C19 27 33 17 50 17 C67 17 81 27 79 52 C79 57 77 61 74 63 L26 63 C23 61 21 57 21 52Z" fill="{hr}" stroke="#140c0c" stroke-width="1"/>'
        + body("#2e3f6e", sk,
               '<path d="M42 78 L50 92 L58 78Z" fill="#fff"/><path d="M37 79 L50 101 M63 79 L50 101" stroke="#22305a" stroke-width="2.2"/>'
               '<path d="M38 79 L45 88 L42 79Z M62 79 L55 88 L58 79Z" fill="#3a4f86"/><circle cx="64" cy="93" r="1.6" fill="#ffd166"/>')
        + head(sk)
        + f'<path d="M22 47 C21 27 34 18 50 18 C66 18 79 27 78 47 C75 37 67 29 57 28 C51 34 39 39 22 47Z" fill="{hr}" stroke="#140c0c" stroke-width="1"/>'
        + f'<path d="M78 47 C79 53 78 58 76 61 L73 58 C75 54 75 50 75 46Z" fill="{hr}"/>'
        + hair_shine("M40 21 Q48 18 56 20")
        + eye_open(EX[0], "#5a3a2a") + eye_open(EX[1], "#5a3a2a") + brows("soft", "#2a1c1c")
        + glasses("rect", "#24305a") + nose(sk) + mouth("smile") + blush(.32)
        + '<circle cx="23" cy="58" r="1.6" fill="#e8e2f4" stroke="#bdb5d4" stroke-width=".6"/>',
        sparkles())

    # ---------------- Hana-obaachan: 84, white bun + kanzashi, happy closed eyes ----------------
    sk, hr = "#f8e0cc", "#f1efec"
    A["hana"] = svg("hana", "#ded2f5", "#4a3226",
        f'<circle cx="50" cy="15" r="10" fill="{hr}" stroke="#c9c5c0" stroke-width="1"/><path d="M43 13 q7 -5 14 0" stroke="#d8d4cf" stroke-width="1.2" fill="none"/>'
        + '<path d="M58 12 L73 3" stroke="#a0522d" stroke-width="2" stroke-linecap="round"/><circle cx="73" cy="3.4" r="3" fill="#e5484d"/><circle cx="73" cy="3.4" r="1.1" fill="#ffd166"/>'
        + f'<path d="M21 54 C19 29 33 19 50 19 C67 19 81 29 79 54 L76 60 L24 60Z" fill="{hr}" stroke="#c9c5c0" stroke-width="1"/>'
        + body("#7f62bf", sk,
               '<path d="M36 79 L50 97 L64 79" fill="#f7f1e6" stroke="#d8cfbf" stroke-width="1"/><path d="M40 79 L50 92 L60 79" fill="#7f62bf"/>'
               '<path d="M24 98 H76" stroke="#5f449c" stroke-width="3"/><circle cx="34" cy="88" r="1.6" fill="#fff" opacity=".6"/><circle cx="68" cy="90" r="1.6" fill="#fff" opacity=".6"/>')
        + head(sk)
        + f'<path d="M22 50 C21 29 34 20 50 20 C66 20 79 29 78 50 C76 38 66 27 50 27 C34 27 24 38 22 50Z" fill="{hr}" stroke="#c9c5c0" stroke-width="1"/>'
        + '<path d="M50 20 Q49 24 50 27" stroke="#c9c5c0" stroke-width="1" fill="none"/><path d="M33 24 Q40 22 46 23" stroke="#d8d4cf" stroke-width="1.2" fill="none"/>'
        + eye_happy(EX[0]) + eye_happy(EX[1]) + brows("soft", "#bdb8b2")
        + f'<path d="M29 53 l-2.4 1.2 M71 53 l2.4 1.2 M44 67.4 q6 1.6 12 0" stroke="{shade(sk,.74)}" stroke-width=".9" fill="none" stroke-linecap="round"/>'
        + nose(sk) + mouth("smile") + blush(.55),
        sparkles())

    # ---------------- Ren: 26, designer, messy black fringe, round glasses, calm ----------------
    sk, hr = "#f4d6c0", "#1c1a22"
    A["ren"] = svg("ren", "#bfe8e0", "#2e2420",
        f'<path d="M20 54 C17 26 32 14 50 14 C68 14 83 26 80 54 L78 62 L22 62Z" fill="{hr}" stroke="#08070a" stroke-width="1"/>'
        + body("#3a3e48", sk,
               '<rect x="38" y="72" width="24" height="10" rx="5" fill="#4a4f5c" stroke="#2c2f37" stroke-width="1"/><path d="M42 74 v6 M47 74 v6 M53 74 v6 M58 74 v6" stroke="#3a3e48" stroke-width="1"/>'
               '<path d="M34 81 L64 104" stroke="#a0522d" stroke-width="3.2"/><path d="M34 81 L64 104" stroke="#c26a3e" stroke-width="1" opacity=".7"/>')
        + head(sk)
        + f'<path d="M21 50 C19 27 33 16 50 16 C67 16 81 27 79 50 L77 42 L74 47 L71 38 L66 44 L62 36 L57 43 L52 35 L47 43 L42 36 L37 44 L33 37 L29 45 L25 39Z" fill="{hr}" stroke="#08070a" stroke-width="1" stroke-linejoin="round"/>'
        + hair_shine("M35 22 Q44 18 53 19")
        + eye_calm(EX[0], "#3a2a22", sk) + eye_calm(EX[1], "#3a2a22", sk) + brows("soft", "#1c1a22")
        + glasses("round", "#6b4a33") + nose(sk) + mouth("small") + blush(.3),
        sparkles())

    # ---------------- Sota: 11, spiky hair, gap-tooth grin, plaster, striped tee ----------------
    sk, hr = "#efc49c", "#1d161c"
    A["sota"] = svg("sota", "#fff0a0", "#4a2e1e",
        body("#2fa36b", sk, '<path d="M26 90 H74 M25 98 H75" stroke="#fff" stroke-width="3.2"/><path d="M42 78 Q50 83 58 78" stroke="#23875a" stroke-width="2" fill="none"/>')
        + head(sk)
        + f'<path d="M22 46 C20 27 32 17 50 17 C68 17 80 27 78 46 L74 36 L70 41 L66 31 L60 38 L54 29 L48 37 L42 29 L36 38 L31 32 L27 40Z" fill="{hr}" stroke="#000" stroke-width="1" stroke-linejoin="round"/>'
        + f'<path d="M28 24 L22 13 L35 19Z M43 19 L44 6 L53 17Z M59 18 L70 8 L68 22Z" fill="{hr}" stroke="#000" stroke-width="1" stroke-linejoin="round"/>'
        + f'<path d="M50 17 C48 9 55 6 58 10 C55 9 52 11 53 16" fill="{hr}"/>'
        + hair_shine("M36 24 Q43 21 50 22")
        + eye_open(EX[0], "#6a4028") + eye_open(EX[1], "#6a4028") + brows("up", "#1d161c")
        + nose(sk) + mouth("gap") + blush(.4)
        + '<g transform="rotate(-20 69 60)"><rect x="63.5" y="57.6" width="11" height="4.8" rx="2.2" fill="#f4d3a8" stroke="#d9b07c" stroke-width=".7"/><path d="M68 58.6 v2.8 M70 58.6 v2.8" stroke="#d9b07c" stroke-width=".6"/></g>',
        sparkles() + '<g transform="translate(84 80) rotate(-15)"><ellipse rx="5" ry="6.6" fill="#5a3418"/><path d="M0 -6.6 V6.6" stroke="#3a2210" stroke-width=".8"/><path d="M0 -6.6 l-2 -5 l3 2" stroke="#3a2210" stroke-width="1.4" fill="none"/><path d="M-5 -1 l-3 -1.6 M5 -1 l3 -1.6 M-5 3 l-3 1.6 M5 3 l3 1.6" stroke="#3a2210" stroke-width="1.1"/></g>')

    # ---------------- Mio: 16, long straight hair, hime bangs, sailor uniform ----------------
    sk, hr = "#f8dcc8", "#17121c"
    A["mio"] = svg("mio", "#ddd3ff", "#3a2a3a",
        f'<path d="M19 48 C17 24 32 13 50 13 C68 13 83 24 81 48 L84 100 L16 100Z" fill="{hr}" stroke="#000" stroke-width="1"/>'
        + body("#22305a", sk,
               '<path d="M27 84 L50 98 L73 84 L66 79 L50 89 L34 79Z" fill="#fff" stroke="#d8dbe6" stroke-width="1"/><path d="M30 86 L50 98 L70 86" stroke="#22305a" stroke-width="1.2" fill="none"/>'
               '<path d="M44 92 L50 101 L56 92 L50 95Z" fill="#e5484d"/>')
        + head(sk)
        + f'<path d="M22 42 C20 60 22 80 25 96 L32 94 C28 78 28 58 29 42Z M78 42 C80 60 78 80 75 96 L68 94 C72 78 72 58 71 42Z" fill="{hr}" stroke="#000" stroke-width=".9"/>'
        + f'<path d="M22 46 C20 24 35 15 50 15 C65 15 80 24 78 46 L77 38 Q64 42 50 39 Q36 42 23 38Z" fill="{hr}" stroke="#000" stroke-width="1"/>'
        + hair_shine("M32 24 Q41 19 50 19") + hair_shine("M55 19.6 Q62 20 67 23")
        + eye_open(EX[0], "#5a3a5a") + eye_open(EX[1], "#5a3a5a") + brows("soft", "#17121c")
        + nose(sk) + mouth("smile") + blush(.5)
        + '<g transform="rotate(-25 66 28)"><rect x="60" y="26" width="12" height="3.6" rx="1.8" fill="#ffd166" stroke="#e5b23c" stroke-width=".7"/><path d="M73.5 27.8 l1.4 -3 l1.4 3 l3 .9 l-3 .9 l-1.4 3 l-1.4 -3 l-3 -.9Z" fill="#ffd166"/></g>',
        sparkles())

    # ---------------- Kurogane Hayato: Edo samurai, topknot, stern ----------------
    sk, hr = "#e6b48a", "#16121a"
    A["hayato"] = svg("hayato", "#f3c9b8", "#3a2418",
        body("#2a2a3a", sk,
             '<path d="M37 79 L50 99 L63 79" fill="#ede5d2" stroke="#cfc4aa" stroke-width="1"/><path d="M41 79 L50 94 L59 79" fill="#2a2a3a"/>'
             '<circle cx="34" cy="90" r="3.8" fill="none" stroke="#ede5d2" stroke-width="1.1"/><circle cx="66" cy="90" r="3.8" fill="none" stroke="#ede5d2" stroke-width="1.1"/>'
             '<path d="M34 86.6 v6.8 M30.6 90 h6.8 M66 86.6 v6.8 M62.6 90 h6.8" stroke="#ede5d2" stroke-width=".7"/>')
        + head(sk)
        + f'<path d="M30 30 C38 25 62 25 70 30 C64 28 56 27 50 27 C44 27 36 28 30 30Z" fill="{shade(sk,.88)}" opacity=".7"/>'
        + f'<path d="M23 50 C21 36 27 26 36 22 L37 34 C30 37 26 43 25 50Z M77 50 C79 36 73 26 64 22 L63 34 C70 37 74 43 75 50Z" fill="{hr}" stroke="#000" stroke-width="1"/>'
        + f'<path d="M36 22 C42 19 58 19 64 22 L63 25 C57 23 43 23 37 25Z" fill="{hr}"/>'
        + f'<path d="M45 22 C44 11 54 6 62 12 C57 11 53 14 53 22Z" fill="{hr}" stroke="#000" stroke-width="1"/><rect x="46" y="17.6" width="7" height="3.4" rx="1" fill="#f1ead6" transform="rotate(-10 49 19)"/>'
        + eye_open(EX[0], "#5a3020", sharp=True) + eye_open(EX[1], "#5a3020", sharp=True) + brows("stern")
        + nose(sk) + mouth("firm") + blush(.2)
        + f'<path d="M73 56 l-3 5" stroke="{shade(sk,.7)}" stroke-width="1" stroke-linecap="round"/>',
        sparkles("#fff", .5) + '<path d="M84 60 L96 30" stroke="#2a2a3a" stroke-width="3" stroke-linecap="round"/><path d="M84 60 L80 70" stroke="#a0522d" stroke-width="4" stroke-linecap="round"/><rect x="81" y="57" width="6" height="2.4" rx="1" fill="#c9a227" transform="rotate(20 84 58)"/>')

    # ---------------- You: from Spain, short thinning hair, glasses, clean-shaven ----------------
    sk, hr = "#ecc4a0", "#5b3b26"
    A["you"] = make_you(**YOU)
    return A


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    A = build()
    for k, v in A.items():
        open(os.path.join(OUT, k + ".svg"), "w").write(v)
    print("wrote", len(A))
