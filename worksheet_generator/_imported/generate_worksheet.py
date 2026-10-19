#!/usr/bin/env python3
"""Base-ten block worksheet generator: 3-digit addition & subtraction.

Draws real base-ten blocks (hundreds = flat, tens = rod, ones = unit) as
vector graphics and lays out a printable worksheet + answer key as a PDF.

Aligned to Texas TEKS:
  * 2.2(A)  compose/decompose numbers up to 1,200 with concrete & pictorial models
  * 2.4(C)  add & subtract within 1,000 using strategies based on place value

Usage (needs no install, via uv):
    uv run --with reportlab generate_worksheet.py --seed 7 --out demo.pdf
    uv run --with reportlab generate_worksheet.py --seed 8 --add 4 --sub 4 --bw

Tweak the knobs below or the CLI flags to churn out as many variants as you like.
"""

from __future__ import annotations

import argparse
import math
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Geometry (points; 1pt = 1/72in). UNIT is the edge of a single "ones" cube.
# ---------------------------------------------------------------------------
UNIT = 6.5
BLOCK_GAP = UNIT * 0.5  # gap between individual blocks
GROUP_GAP = UNIT * 2.2  # gap between hundreds / tens / ones groups
FLATS_PER_ROW = 5  # wrap flats so wide numbers still fit the page
ONES_PER_ROW = 5

PAGE_W, PAGE_H = letter
LMARGIN = RMARGIN = TMARGIN = BMARGIN = 54
CONTENT_W = PAGE_W - LMARGIN - RMARGIN

# Two palettes: gentle colour for kids, or toner-friendly grayscale.
COLOR = {
    "flat_fill": HexColor("#cfe3f7"),
    "flat_line": HexColor("#2b6cb0"),
    "rod_fill": HexColor("#d6efd6"),
    "rod_line": HexColor("#2f855a"),
    "one_fill": HexColor("#fde3c8"),
    "one_line": HexColor("#c05621"),
}
BW = {
    "flat_fill": HexColor("#e8e8e8"),
    "flat_line": HexColor("#444444"),
    "rod_fill": HexColor("#f0f0f0"),
    "rod_line": HexColor("#444444"),
    "one_fill": HexColor("#ffffff"),
    "one_line": HexColor("#444444"),
}


def digits(n: int) -> tuple[int, int, int]:
    return n // 100, (n // 10) % 10, n % 10


# ---------------------------------------------------------------------------
# Block drawing.  (x, y) is the bottom-left corner (reportlab origin).
# ---------------------------------------------------------------------------
def draw_flat(c, x, y, col):
    s = 10 * UNIT
    c.setFillColor(col["flat_fill"])
    c.setStrokeColor(col["flat_line"])
    c.setLineWidth(1)
    c.rect(x, y, s, s, stroke=1, fill=1)
    c.setLineWidth(0.4)
    for i in range(1, 10):
        c.line(x + i * UNIT, y, x + i * UNIT, y + s)
        c.line(x, y + i * UNIT, x + s, y + i * UNIT)


def draw_rod(c, x, y, col):
    h = 10 * UNIT
    c.setFillColor(col["rod_fill"])
    c.setStrokeColor(col["rod_line"])
    c.setLineWidth(1)
    c.rect(x, y, UNIT, h, stroke=1, fill=1)
    c.setLineWidth(0.4)
    for i in range(1, 10):
        c.line(x, y + i * UNIT, x + UNIT, y + i * UNIT)


def draw_unit(c, x, y, col):
    c.setFillColor(col["one_fill"])
    c.setStrokeColor(col["one_line"])
    c.setLineWidth(1)
    c.rect(x, y, UNIT, UNIT, stroke=1, fill=1)


def group_height(h: int) -> float:
    """Vertical space a number's blocks occupy (flats may wrap into rows)."""
    flat = 10 * UNIT
    rows = max(math.ceil(h / FLATS_PER_ROW), 1) if h else 1
    return rows * flat + max(rows - 1, 0) * BLOCK_GAP


def draw_group(c, x, y_base, h, t, o, col) -> float:
    """Draw one number as blocks, bottom-aligned to y_base. Returns width used."""
    flat = 10 * UNIT
    cursor = x

    if h:
        cols = min(h, FLATS_PER_ROW)
        for i in range(h):
            r, cc = divmod(i, FLATS_PER_ROW)
            draw_flat(c, x + cc * (flat + BLOCK_GAP), y_base + r * (flat + BLOCK_GAP), col)
        cursor = x + cols * (flat + BLOCK_GAP) - BLOCK_GAP + GROUP_GAP

    if t:
        for i in range(t):
            draw_rod(c, cursor + i * (UNIT + BLOCK_GAP), y_base, col)
        cursor += t * (UNIT + BLOCK_GAP) - BLOCK_GAP + GROUP_GAP

    if o:
        cols = min(o, ONES_PER_ROW)
        for i in range(o):
            r, cc = divmod(i, ONES_PER_ROW)
            draw_unit(c, cursor + cc * (UNIT + BLOCK_GAP), y_base + r * (UNIT + BLOCK_GAP), col)
        cursor += cols * (UNIT + BLOCK_GAP) - BLOCK_GAP

    return cursor - x


def answer_box(c, x, y, w=70, h=26):
    c.setLineWidth(1)
    c.setStrokeColor(HexColor("#4a5568"))
    c.roundRect(x, y, w, h, 4, stroke=1, fill=0)


# ---------------------------------------------------------------------------
# Problem generation.  Each problem is a small dict, so it's easy to extend.
# ---------------------------------------------------------------------------
def build_problems(rng, n_rep, n_add, n_sub, regroup=True):
    problems = []

    for _ in range(n_rep):
        problems.append({"type": "represent", "n": rng.randint(102, 589)})

    made = 0
    while made < n_add:
        a, b = rng.randint(115, 385), rng.randint(120, 360)
        if a + b > 995:
            continue
        needs = (a % 10 + b % 10 >= 10) or ((a // 10 % 10) + (b // 10 % 10) >= 10)
        if regroup and not needs:
            continue
        problems.append({"type": "add", "a": a, "b": b})
        made += 1

    made = 0
    while made < n_sub:
        m, s = rng.randint(320, 879), rng.randint(105, 290)
        if m - s < 100:
            continue
        borrow = (m % 10 < s % 10) or ((m // 10 % 10) < (s // 10 % 10))
        if regroup and not borrow:
            continue
        problems.append({"type": "sub", "m": m, "s": s})
        made += 1

    return problems


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render(problems, path, title, subtitle, teks, seed, col):
    c = canvas.Canvas(path, pagesize=letter)
    st = {"y": 0.0, "page": 1}

    def footer():
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#718096"))
        c.drawString(LMARGIN, 30, f"Base-ten blocks  •  {teks}  •  seed {seed}")
        c.drawRightString(PAGE_W - RMARGIN, 30, f"Page {st['page']}")

    def new_page():
        footer()
        c.showPage()
        st["page"] += 1
        st["y"] = PAGE_H - TMARGIN

    def ensure(h):
        if st["y"] - h < BMARGIN + 24:
            new_page()

    def legend():
        y = st["y"]
        c.setFillColor(HexColor("#4a5568"))
        c.setFont("Helvetica", 9)
        c.drawString(LMARGIN, y + 3 * UNIT + 4, "Key:")
        x = LMARGIN + 34
        draw_flat(c, x, y, col)
        c.setFillColor(black)
        c.setFont("Helvetica", 9)
        c.drawString(x, y - 12, "flat = 100")
        x += 10 * UNIT + 40
        draw_rod(c, x, y, col)
        c.setFillColor(black)
        c.drawString(x - 6, y - 12, "rod = 10")
        x += UNIT + 66
        draw_unit(c, x, y + 9 * UNIT, col)
        c.setFillColor(black)
        c.drawString(x - 6, y - 12, "unit = 1")
        st["y"] = y - 26

    def header():
        st["y"] = PAGE_H - TMARGIN
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(LMARGIN, st["y"] - 4, title)
        st["y"] -= 20
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor("#4a5568"))
        c.drawString(LMARGIN, st["y"], subtitle)
        st["y"] -= 18
        c.setFillColor(black)
        c.setFont("Helvetica", 11)
        c.drawString(LMARGIN, st["y"], "Name: ______________________________")
        c.drawRightString(PAGE_W - RMARGIN, st["y"], "Date: ______________")
        st["y"] -= 16
        c.setStrokeColor(HexColor("#cbd5e0"))
        c.setLineWidth(1)
        c.line(LMARGIN, st["y"], PAGE_W - RMARGIN, st["y"])
        st["y"] -= 12 + 10 * UNIT
        legend()

    def instruction(text):
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(black)
        c.drawString(LMARGIN, st["y"], text)
        st["y"] -= 8

    def render_represent(idx, p):
        h, t, o = digits(p["n"])
        gh = group_height(h)
        ensure(gh + 44)
        instruction(f"{idx})  Write the number shown by the blocks.")
        base = st["y"] - gh
        w = draw_group(c, LMARGIN + 16, base, h, t, o, col)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(black)
        c.drawString(LMARGIN + 16 + w + 8, base + (gh - 26) / 2 + 7, "=")
        answer_box(c, LMARGIN + 16 + w + 26, base + (gh - 26) / 2)
        st["y"] = base - 20

    def render_add(idx, p):
        a, b = p["a"], p["b"]
        ha, hb = group_height(digits(a)[0]), group_height(digits(b)[0])
        ensure(ha + hb + 90)
        instruction(f"{idx})  Combine the blocks. Regroup if you can, then write the sum.")
        base_a = st["y"] - ha
        draw_group(c, LMARGIN + 24, base_a, *digits(a), col)
        base_b = base_a - 14 - hb
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(HexColor("#2d3748"))
        c.drawString(LMARGIN + 2, base_b + hb / 2 - 7, "+")
        draw_group(c, LMARGIN + 24, base_b, *digits(b), col)
        yr = base_b - 12
        c.setStrokeColor(HexColor("#2d3748"))
        c.setLineWidth(1.5)
        c.line(LMARGIN, yr, LMARGIN + 250, yr)
        ya = yr - 34
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(black)
        c.drawString(LMARGIN, ya + 8, "Sum =")
        answer_box(c, LMARGIN + 50, ya)
        st["y"] = ya - 18

    def render_sub(idx, p):
        m, s = p["m"], p["s"]
        hm = group_height(digits(m)[0])
        ensure(hm + 80)
        instruction(
            f"{idx})  Cross out blocks to subtract. Break a hundred or ten if needed; write the difference."
        )
        base_m = st["y"] - hm
        draw_group(c, LMARGIN + 24, base_m, *digits(m), col)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(HexColor("#2d3748"))
        c.drawString(LMARGIN + 2, base_m + hm / 2 - 7, "−")
        yr = base_m - 12
        c.setStrokeColor(HexColor("#2d3748"))
        c.setLineWidth(1.5)
        c.line(LMARGIN, yr, LMARGIN + 250, yr)
        ya = yr - 34
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(black)
        c.drawString(LMARGIN, ya + 8, f"{m} − {s} =")
        answer_box(c, LMARGIN + 96, ya)
        st["y"] = ya - 18

    dispatch = {"represent": render_represent, "add": render_add, "sub": render_sub}

    header()
    for idx, p in enumerate(problems, 1):
        dispatch[p["type"]](idx, p)

    # Answer key on its own page.
    new_page()
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(LMARGIN, st["y"], "Answer Key")
    st["y"] -= 28
    c.setFont("Helvetica", 12)
    for i, p in enumerate(problems, 1):
        if p["type"] == "represent":
            line = f"{i})  {p['n']}"
        elif p["type"] == "add":
            line = f"{i})  {p['a']} + {p['b']} = {p['a'] + p['b']}"
        else:
            line = f"{i})  {p['m']} − {p['s']} = {p['m'] - p['s']}"
        ensure(20)
        c.drawString(LMARGIN, st["y"], line)
        st["y"] -= 20

    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1, help="change for a fresh set of numbers")
    ap.add_argument("--out", default="demo.pdf")
    ap.add_argument("--represent", type=int, default=2, help="# 'write the number' problems")
    ap.add_argument("--add", type=int, default=2, help="# addition problems")
    ap.add_argument("--sub", type=int, default=2, help="# subtraction problems")
    ap.add_argument("--no-regroup", action="store_true", help="avoid problems that need regrouping")
    ap.add_argument("--bw", action="store_true", help="grayscale (toner-friendly)")
    ap.add_argument("--title", default="Base-Ten Blocks: 3-Digit Addition & Subtraction")
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf

    rng = random.Random(args.seed)
    problems = build_problems(rng, args.represent, args.add, args.sub, regroup=not args.no_regroup)
    render(
        problems,
        args.out,
        title=args.title,
        subtitle="Represent, add, and subtract numbers within 1,000 using base-ten blocks.",
        teks="Texas TEKS 2.2(A), 2.4(C)",
        seed=args.seed,
        col=BW if args.bw else COLOR,
    )
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
