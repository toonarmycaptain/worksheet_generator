#!/usr/bin/env python3
"""Multiplication MULTIPLE-CHOICE model worksheets (Grade 3).

The student reads a one-step multiplication word problem ("g groups of s"),
then picks the THREE models (out of six, A-F) that represent it. Each choice
is one of four models, with the total always shown as "?":
  * array                       (g rows of s dots; flipped s x g also counts)
  * number line with equal jumps (0, s, 2s, ... ?; arcs numbered 1, 2, 3 ...,
                                  or unnumbered with --no-jump-labels)
  * tape / strip diagram         (g equal parts labeled s, "?" over the whole)
  * repeated addition            (s + s + ... + s = ?)

Rules: exactly 3 choices are correct and they are 3 different models; a model
may appear more than once, but only one of each model is ever correct; all four
models appear in every problem. The three wrong choices are classic errors:
  * number line: g jumps of g or s jumps of s (the jumps are numbered, so
    both the count and the jump size come from the story)
  * tape / repeated addition: only numbers from the story --
    g +/- 1 groups of s, g groups of g, s groups of s, or g + s
  * array: g +/- 1 rows, s +/- 1 columns, or g rows of g
Flipped versions (s groups of g) are never drawn except as a correct array.

Factors 2-12, products within 100 (2 x 2 excluded).
Texas TEKS 3.4(K): solve one-step multiplication problems within 100 using
pictorial models such as arrays, strip diagrams, and equal jumps.

Usage (no install needed, via uv):
    uv run --with reportlab generate_multiplication_mc_word_problems.py --seed 1 --label "Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import wp_common as wp

LINE = HexColor("#2d3748")
ARC = HexColor("#2b6cb0")
DOT = HexColor("#2b6cb0")
PART_FILL = HexColor("#cfe3f7")
CELL_BORDER = HexColor("#e2e8f0")
GRAY = HexColor("#718096")
LETTERS = "ABCDEF"
TYPES = ["array", "numline", "tape", "repeat"]
CELL_H = 76

TEMPLATES = [
    "{n1} has {g} bags of {obj}. Each bag has {s} {obj}. How many {obj} does {n1} have in all?",
    "There are {g} rows of chairs. Each row has {s} chairs. How many chairs are there in all?",
    "A pack has {s} {obj}. {n1} buys {g} packs. How many {obj} does {n1} buy in all?",
    "There are {g} tables in the classroom. {s} students sit at each table. How many students are there in all?",
    "{n1} reads {s} pages every day for {g} days. How many pages does {n1} read in all?",
    "A frog hops {s} spaces each time it jumps. It jumps {g} times. How many spaces does the frog move in all?",
    "{n1} saves ${s} each week for {g} weeks. How many dollars does {n1} save in all?",
    "{n1} puts {s} {obj} in each of {g} boxes. How many {obj} does {n1} put in the boxes?",
    "{n1} plants {g} rows of flowers with {s} flowers in each row. How many flowers does {n1} plant?",
]


# ---------------------------------------------------------------- problem bank
def build_problems(rng, n, max_factor=12, max_product=100):
    """One-step 'g groups of s'; no (g, s) pair or its flip repeats on a sheet."""
    pool = [
        (g, s)
        for g in range(2, max_factor + 1)
        for s in range(2, max_factor + 1)
        if g * s <= max_product and (g, s) != (2, 2)
    ]
    rng.shuffle(pool)
    templates = []
    problems = []
    for _ in range(n):
        if not pool:  # tiny ranges: allow repeats
            pool = [
                (g, s)
                for g in range(2, max_factor + 1)
                for s in range(2, max_factor + 1)
                if g * s <= max_product and (g, s) != (2, 2)
            ]
            rng.shuffle(pool)
        g, s = pool.pop()
        pool = [ps for ps in pool if ps != (s, g)]
        if not templates:
            templates = rng.sample(TEMPLATES, len(TEMPLATES))
        n1 = rng.choice(wp.NAMES)
        text = templates.pop().format(n1=n1, g=g, s=s, obj=rng.choice(wp.OBJECTS))
        problems.append({"groups": g, "size": s, "answer": g * s, "text": text})
    return problems


# ------------------------------------------------------------ option building
def _spec(kind, typ, g2, s2, addends, correct, transpose=False):
    return {
        "kind": kind,
        "type": typ,
        "g": g2,
        "s": s2,
        "addends": addends,
        "correct": correct,
        "transpose": transpose,
    }


def _key(o):
    """What the student actually sees, so two choices never look identical."""
    if o["type"] == "array":
        return "array", tuple(sorted((o["g"], o["s"])))
    return o["type"], tuple(o["addends"])


def _wrong_pool(typ, g, s):
    right = {(s,) * g, (g,) * s}  # faithful and flipped models
    count = [("count", g + 1, s), ("count", g - 1, s)]
    if typ == "array":
        cands = count + [("size", g, s + 1), ("size", g, s - 1), ("same", g, g)]
    elif typ == "numline":  # numbered jumps: count = jump size, both from the story
        cands = [("same", g, g), ("same_s", s, s)]
    else:  # tape / repeat: only numbers from the story
        cands = count + [("same", g, g), ("same_s", s, s)]
    out = []
    for kind, g2, s2 in cands:
        if g2 < 2 or s2 < 2 or (s2,) * g2 in right:
            continue
        out.append(_spec(kind, typ, g2, s2, [s2] * g2, False))
    if typ in ("tape", "repeat") and g != s:  # for squares g + s just looks like 2 groups
        out.append(_spec("factors", typ, g, s, [g, s], False))
    return out


def _orient(rng, g2, s2):
    """Arrays may be flipped; long arrays always go landscape so rows stay countable."""
    if max(g2, s2) > 7:
        return g2 > s2  # transpose -> rows = smaller factor
    return rng.random() < 0.5


def make_options(rng, p):
    """Return 6 option specs: 3 correct (distinct models) + 3 wrong."""
    g, s = p["groups"], p["size"]
    missing = rng.choice(
        [t for t in TYPES if _wrong_pool(t, g, s)]
    )  # squares: no wrong number line
    correct_types = [t for t in TYPES if t != missing]
    options = [
        _spec("correct", t, g, s, [s] * g, True, transpose=(t == "array" and _orient(rng, g, s)))
        for t in correct_types
    ]
    seen = {_key(o) for o in options}

    wrong_types = [missing] + rng.sample(TYPES, 2)
    for typ in wrong_types:
        for t in [typ] + rng.sample(TYPES, len(TYPES)):  # fall back to another model if exhausted
            cands = [o for o in _wrong_pool(t, g, s) if _key(o) not in seen]
            if cands:
                o = rng.choice(cands)
                if t == "array":
                    o["transpose"] = _orient(rng, o["g"], o["s"])
                options.append(o)
                seen.add(_key(o))
                break
    rng.shuffle(options)
    return options


def explain(o, g, s):
    """Short answer-key reason a wrong choice doesn't match."""
    if o["type"] == "array":
        rows, cols = (o["s"], o["g"]) if o["transpose"] else (o["g"], o["s"])
        return f"array has {rows} rows of {cols}"
    if o["kind"] == "factors":
        return {
            "numline": f"number line jumps to {g}, then {s} more",
            "tape": f"tape has parts {g} and {s}",
            "repeat": f"adds {g} + {s}",
        }[o["type"]]
    return {
        "numline": f"number line shows {o['g']} jumps of {o['s']}",
        "tape": f"tape shows {o['g']} parts of {o['s']}",
        "repeat": f"adds {o['s']} a total of {o['g']} times",
    }[o["type"]]


# -------------------------------------------------------------------- drawing
def draw_array(c, x, y_top, w, h, rows, cols):
    sp = min(13, (h - 6) / rows, (w - 8) / cols)
    r = sp * 0.36
    ax = x + (w - sp * cols) / 2 + sp / 2
    ay = y_top - (h - sp * rows) / 2 - sp / 2
    c.setFillColor(DOT)
    for i in range(rows):
        for j in range(cols):
            c.circle(ax + j * sp, ay - i * sp, r, stroke=0, fill=1)


def _arc(c, x0, x1, y, label=None):
    dx = x1 - x0
    h = min(8 + 0.09 * abs(dx), 16)
    c.setStrokeColor(ARC)
    c.setLineWidth(1)
    arc = c.beginPath()
    arc.moveTo(x0, y + 2)
    arc.curveTo(x0 + dx * 0.25, y + h, x1 - dx * 0.25, y + h, x1, y + 2)
    c.drawPath(arc, stroke=1, fill=0)
    c.setFillColor(ARC)
    ah = c.beginPath()
    ah.moveTo(x1, y + 2)
    ah.lineTo(x1 - 4, y + 5)
    ah.lineTo(x1 - 4, y - 1)
    ah.close()
    c.drawPath(ah, fill=1, stroke=0)
    if label:
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString((x0 + x1) / 2, y + h + 1, label)


def draw_numline(c, x, y_top, w, h, addends, jump_labels=True):
    y = y_top - h / 2 - 6
    left, right = x + 6, x + w - 12
    total = sum(addends)
    stops = [0]
    for a in addends:
        stops.append(stops[-1] + a)
    px = lambda v: left + (right - left) * v / total

    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(left - 4, y, right + 8, y)
    c.setFillColor(LINE)
    ah = c.beginPath()
    ah.moveTo(right + 10, y)
    ah.lineTo(right + 5, y + 3)
    ah.lineTo(right + 5, y - 3)
    ah.close()
    c.drawPath(ah, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7)
    for i, v in enumerate(stops):
        tx = px(v)
        c.setStrokeColor(LINE)
        c.line(tx, y - 3, tx, y + 3)
        c.setFillColor(black)
        c.drawCentredString(tx, y - 11, "?" if i == len(stops) - 1 else str(v))
    for n, (a, b) in enumerate(zip(stops, stops[1:]), 1):
        _arc(
            c, px(a), px(b), y, str(n) if jump_labels else None
        )  # label = jump number, not jump size


def draw_tape(c, x, y_top, w, h, addends):
    bar_h = 22
    width = w - 8
    x0 = x + 4
    top = y_top - h / 2 + 18  # "?" + brace above the bar
    brace_y = top - 12
    bar_top = brace_y - 6
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x0 + width / 2, top - 8, "?")
    c.setStrokeColor(GRAY)
    c.setLineWidth(1)
    c.line(x0, brace_y, x0 + width, brace_y)
    c.line(x0, brace_y, x0, brace_y - 4)
    c.line(x0 + width, brace_y, x0 + width, brace_y - 4)

    total = sum(addends)
    cx = x0
    c.setLineWidth(1.1)
    for a in addends:
        cw = width * a / total
        c.setStrokeColor(LINE)
        c.setFillColor(PART_FILL)
        c.rect(cx, bar_top - bar_h, cw, bar_h, stroke=1, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 10 if cw >= 14 else 8)
        c.drawCentredString(cx + cw / 2, bar_top - bar_h / 2 - 3.5, str(a))
        cx += cw


def draw_repeat(c, x, y_top, w, h, addends):
    text = " + ".join(map(str, addends)) + " = ?"
    yc = y_top - h / 2
    c.setFillColor(black)
    for size in (14, 13, 12, 11, 10, 9, 8):
        if c.stringWidth(text, "Helvetica-Bold", size) <= w - 6:
            c.setFont("Helvetica-Bold", size)
            c.drawCentredString(x + w / 2, yc - size / 3, text)
            return
    lines = wp.wrap(c, text, "Helvetica-Bold", 10, w - 6)
    c.setFont("Helvetica-Bold", 10)
    y = yc + (len(lines) - 1) * 7 - 3
    for line in lines:
        c.drawCentredString(x + w / 2, y, line)
        y -= 14


def draw_option(c, x, y_top, w, letter, o, jump_labels=True):
    c.setStrokeColor(CELL_BORDER)
    c.setLineWidth(1)
    c.roundRect(x, y_top - CELL_H + 3, w, CELL_H - 6, 5, stroke=1, fill=0)
    r = 7
    cy = y_top - CELL_H / 2
    c.setStrokeColor(HexColor("#4a5568"))
    c.setFillColor(HexColor("#ffffff"))
    c.circle(x + 6 + r, cy, r, stroke=1, fill=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + 6 + r, cy - 3, letter)

    mx, mw = x + 6 + 2 * r + 6, w - (6 + 2 * r + 6) - 6
    my, mh = y_top - 6, CELL_H - 12
    if o["type"] == "array":
        rows, cols = (o["s"], o["g"]) if o["transpose"] else (o["g"], o["s"])
        draw_array(c, mx, my, mw, mh, rows, cols)
    elif o["type"] == "numline":
        draw_numline(c, mx, my, mw, mh, o["addends"], jump_labels)
    elif o["type"] == "tape":
        draw_tape(c, mx, my, mw, mh, o["addends"])
    else:
        draw_repeat(c, mx, my, mw, mh, o["addends"])


# ----------------------------------------------------------------- rendering
def render(problems, path, title, label, teks, seed, jump_labels=True):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle(f"{title} — {label}")
    c.setSubject(teks)
    c.setCreator("TEKS worksheet generator")
    st = {"y": 0.0, "page": 1, "show_seed": False}  # seed only on the answer key
    footer, new_page, ensure = wp.make_page(c, st, label, teks, seed)
    wp.draw_header(
        c,
        st,
        title,
        label,
        "Each problem has 6 models. Exactly 3 match the story. The ? is the total.",
    )

    colw = (wp.CONTENT_W - wp.TEXT_INDENT) / 2
    for idx, p in enumerate(problems, 1):
        options = make_options(random.Random(f"{seed}-{idx}"), p)
        p["options"] = options
        n_lines = len(wp.wrap(c, p["text"], "Helvetica", 12, wp.CONTENT_W - wp.TEXT_INDENT))
        ensure(n_lines * 15 + 16 + 3 * CELL_H + 10)
        wp.draw_problem_text(c, st, idx, p, None)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(GRAY)
        c.drawString(
            wp.LMARGIN + wp.TEXT_INDENT,
            st["y"] - 10,
            "Which THREE models show this problem? Circle three letters.",
        )
        st["y"] -= 16
        grid_top = st["y"]
        for i, o in enumerate(options):
            row, col = divmod(i, 2)
            ox = wp.LMARGIN + wp.TEXT_INDENT + col * colw
            draw_option(c, ox, grid_top - row * CELL_H, colw - 8, LETTERS[i], o, jump_labels)
        st["y"] = grid_top - 3 * CELL_H - 10

    new_page()
    st["show_seed"] = True
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(wp.LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    for i, p in enumerate(problems, 1):
        g, s = p["groups"], p["size"]
        right = ", ".join(LETTERS[j] for j, o in enumerate(p["options"]) if o["correct"])
        why = " · ".join(
            f"Not {LETTERS[j]}: {explain(o, g, s)}"
            for j, o in enumerate(p["options"])
            if not o["correct"]
        )
        why_lines = wp.wrap(c, why, "Helvetica", 9, wp.CONTENT_W - wp.TEXT_INDENT)
        ensure(20 + 12 * len(why_lines) + 10)
        c.setFillColor(black)
        c.setFont("Helvetica", 12)
        c.drawString(
            wp.LMARGIN, st["y"], f"{i})  {right}   ({g} groups of {s}:  {g} × {s} = {p['answer']})"
        )
        st["y"] -= 14
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 9)
        for line in why_lines:
            c.drawString(wp.LMARGIN + wp.TEXT_INDENT, st["y"], line)
            st["y"] -= 12
        st["y"] -= 10

    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="multiplication-mc-word-problems.pdf")
    ap.add_argument("--label", default="Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Multiplication Word Problems — Pick the Models")
    ap.add_argument("--max-factor", type=int, default=12, help="largest factor (default 12)")
    ap.add_argument("--max-product", type=int, default=100, help="largest product (default 100)")
    ap.add_argument(
        "--no-jump-labels",
        dest="jump_labels",
        action="store_false",
        help="leave the number-line jumps unnumbered, so students count them (default: numbered)",
    )
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = build_problems(rng, args.problems, args.max_factor, args.max_product)
    render(
        problems, args.out, args.title, args.label, "Texas TEKS 3.4(K)", args.seed, args.jump_labels
    )
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
