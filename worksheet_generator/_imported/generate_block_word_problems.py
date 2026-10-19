#!/usr/bin/env python3
"""Base-ten-block WORD-PROBLEM worksheets: single-step add/subtract (Grade 3).

Each word problem shows its numbers as base-ten blocks (flat=100, rod=10,
unit=1): addition shows both quantities to combine; subtraction shows the
starting quantity to cross out. Mixed 2- and 3-digit numbers within 1,000.
3-digit numbers are kept to hundreds <= 5 so each stays on one clean row.

Texas TEKS: 2.2(A)/3.4(A) — represent & solve add/subtract within 1,000 using
concrete/pictorial (base-ten) models and place value.

Usage (no install needed, via uv):
    uv run --with reportlab generate_block_word_problems.py --seed 1 --label "Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import math
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- block geometry (smaller than the pure-block sheet, to leave room for text)
UNIT = 5.5
BLOCK_GAP = UNIT * 0.5
GROUP_GAP = UNIT * 2.2
FLATS_PER_ROW = 5
ONES_PER_ROW = 5

PAGE_W, PAGE_H = letter
LMARGIN = RMARGIN = TMARGIN = BMARGIN = 54
CONTENT_W = PAGE_W - LMARGIN - RMARGIN
TEXT_INDENT = 22
GROUP_X = LMARGIN + 24  # blocks hang right of the +/- sign

COL = {
    "flat_fill": HexColor("#cfe3f7"),
    "flat_line": HexColor("#2b6cb0"),
    "rod_fill": HexColor("#d6efd6"),
    "rod_line": HexColor("#2f855a"),
    "one_fill": HexColor("#fde3c8"),
    "one_line": HexColor("#c05621"),
}

NAMES = [
    "Maria",
    "Jamal",
    "Priya",
    "Liam",
    "Sofia",
    "Chen",
    "Aisha",
    "Diego",
    "Emma",
    "Noah",
    "Zoe",
    "Omar",
    "Ava",
    "Kai",
    "Lucia",
    "Malik",
    "Hana",
    "Leo",
    "Nina",
    "Theo",
    "Rosa",
    "Sam",
    "Ivy",
    "Dev",
]
OBJECTS = [
    "stickers",
    "marbles",
    "seashells",
    "buttons",
    "beads",
    "crayons",
    "stamps",
    "acorns",
    "pennies",
    "books",
    "apples",
    "pencils",
    "bottle caps",
    "leaves",
    "coins",
    "blocks",
]

ADD_TEMPLATES = [
    "{n1} collected {a} {obj}. {n2} collected {b} {obj}. How many {obj} did they collect altogether?",
    "There were {a} {obj} in the bin. {n1} put in {b} more. How many {obj} are in the bin now?",
    "{n1} had {a} {obj} and found {b} more. How many {obj} does {n1} have now?",
    "A basket held {a} {obj}. {n1} added {b} more. How many {obj} are in the basket now?",
]
SUB_TEMPLATES = [
    "{n1} had {a} {obj}. {n1} gave away {b} of them. How many {obj} does {n1} have left?",
    "There were {a} {obj} on the shelf. {b} of them were sold. How many {obj} are left?",
    "{n1} had {a} {obj} and used {b} of them. How many {obj} are left?",
    "{n1} started with {a} {obj} and lost {b}. How many {obj} does {n1} have now?",
]

PROFILES = [(2, 2), (2, 3), (3, 2), (3, 3)]


def digits(n):
    return n // 100, (n // 10) % 10, n % 10


def _num(rng, d):
    return rng.randint(11, 99) if d == 2 else rng.randint(101, 599)  # hundreds <= 5


# ---------------------------------------------------------------- block drawing
def draw_flat(c, x, y):
    s = 10 * UNIT
    c.setFillColor(COL["flat_fill"])
    c.setStrokeColor(COL["flat_line"])
    c.setLineWidth(1)
    c.rect(x, y, s, s, stroke=1, fill=1)
    c.setLineWidth(0.4)
    for i in range(1, 10):
        c.line(x + i * UNIT, y, x + i * UNIT, y + s)
        c.line(x, y + i * UNIT, x + s, y + i * UNIT)


def draw_rod(c, x, y):
    h = 10 * UNIT
    c.setFillColor(COL["rod_fill"])
    c.setStrokeColor(COL["rod_line"])
    c.setLineWidth(1)
    c.rect(x, y, UNIT, h, stroke=1, fill=1)
    c.setLineWidth(0.4)
    for i in range(1, 10):
        c.line(x, y + i * UNIT, x + UNIT, y + i * UNIT)


def draw_unit(c, x, y):
    c.setFillColor(COL["one_fill"])
    c.setStrokeColor(COL["one_line"])
    c.setLineWidth(1)
    c.rect(x, y, UNIT, UNIT, stroke=1, fill=1)


def group_height(h):
    flat = 10 * UNIT
    rows = max(math.ceil(h / FLATS_PER_ROW), 1) if h else 1
    return rows * flat + max(rows - 1, 0) * BLOCK_GAP


def draw_group(c, x, y_base, h, t, o):
    flat = 10 * UNIT
    cursor = x
    if h:
        cols = min(h, FLATS_PER_ROW)
        for i in range(h):
            r, cc = divmod(i, FLATS_PER_ROW)
            draw_flat(c, x + cc * (flat + BLOCK_GAP), y_base + r * (flat + BLOCK_GAP))
        cursor = x + cols * (flat + BLOCK_GAP) - BLOCK_GAP + GROUP_GAP
    if t:
        for i in range(t):
            draw_rod(c, cursor + i * (UNIT + BLOCK_GAP), y_base)
        cursor += t * (UNIT + BLOCK_GAP) - BLOCK_GAP + GROUP_GAP
    if o:
        cols = min(o, ONES_PER_ROW)
        for i in range(o):
            r, cc = divmod(i, ONES_PER_ROW)
            draw_unit(c, cursor + cc * (UNIT + BLOCK_GAP), y_base + r * (UNIT + BLOCK_GAP))
        cursor += cols * (UNIT + BLOCK_GAP) - BLOCK_GAP
    return cursor - x


def answer_box(c, x, y, w=70, h=24):
    c.setLineWidth(1)
    c.setStrokeColor(HexColor("#4a5568"))
    c.roundRect(x, y, w, h, 4, stroke=1, fill=0)


# --------------------------------------------------------------------- problems
def build_problems(rng, n):
    profiles = [PROFILES[i % len(PROFILES)] for i in range(n)]
    rng.shuffle(profiles)
    ops = ["add"] * ((n + 1) // 2) + ["sub"] * (n // 2)
    rng.shuffle(ops)
    problems = []
    for (da, db), op in zip(profiles, ops):
        n1, n2 = rng.sample(NAMES, 2)
        obj = rng.choice(OBJECTS)
        if op == "add":
            while True:
                a, b = _num(rng, da), _num(rng, db)
                if a + b <= 999:
                    break
            text = rng.choice(ADD_TEMPLATES).format(n1=n1, n2=n2, a=a, b=b, obj=obj)
            answer = a + b
        else:
            a, b = _num(rng, da), _num(rng, db)
            a, b = max(a, b), min(a, b)
            if a == b:
                a += rng.randint(1, 9)
            text = rng.choice(SUB_TEMPLATES).format(n1=n1, n2=n2, a=a, b=b, obj=obj)
            answer = a - b
        problems.append({"op": op, "a": a, "b": b, "answer": answer, "text": text})
    return problems


def wrap(c, text, font, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if c.stringWidth(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------------- render
def render(problems, path, title, label, teks, seed):
    c = canvas.Canvas(path, pagesize=letter)
    st = {"y": 0.0, "page": 1}

    def footer():
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#718096"))
        c.drawString(LMARGIN, 30, f"{label}  •  {teks}  •  seed {seed}")
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
        y = st["y"] - 10 * UNIT
        c.setFillColor(HexColor("#4a5568"))
        c.setFont("Helvetica", 9)
        c.drawString(LMARGIN, y + 3 * UNIT + 4, "Key:")
        x = LMARGIN + 30
        draw_flat(c, x, y)
        c.setFillColor(black)
        c.setFont("Helvetica", 9)
        c.drawString(x, y - 11, "flat = 100")
        x += 10 * UNIT + 40
        draw_rod(c, x, y)
        c.setFillColor(black)
        c.drawString(x - 6, y - 11, "rod = 10")
        x += UNIT + 60
        draw_unit(c, x, y)
        c.setFillColor(black)
        c.drawString(x - 6, y - 11, "unit = 1")
        st["y"] = y - 24

    def header():
        st["y"] = PAGE_H - TMARGIN
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(LMARGIN, st["y"] - 2, title)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(HexColor("#2b6cb0"))
        c.drawRightString(PAGE_W - RMARGIN, st["y"] - 2, label)
        st["y"] -= 18
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor("#4a5568"))
        c.drawString(LMARGIN, st["y"], "Use the base-ten blocks to help you solve each problem.")
        st["y"] -= 16
        c.setFillColor(black)
        c.setFont("Helvetica", 11)
        c.drawString(LMARGIN, st["y"], "Name: ______________________________")
        c.drawRightString(PAGE_W - RMARGIN, st["y"], "Date: ______________")
        st["y"] -= 12
        c.setStrokeColor(HexColor("#cbd5e0"))
        c.setLineWidth(1)
        c.line(LMARGIN, st["y"], PAGE_W - RMARGIN, st["y"])
        st["y"] -= 6
        legend()

    def draw_text_block(idx, p):
        lines = wrap(c, p["text"], "Helvetica", 12, CONTENT_W - TEXT_INDENT)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(black)
        c.drawString(LMARGIN, st["y"] - 11, f"{idx})")
        c.setFont("Helvetica", 12)
        for line in lines:
            c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 11, line)
            st["y"] -= 15
        hint = (
            "Combine the blocks to find the total."
            if p["op"] == "add"
            else f"Cross out {p['b']} blocks to subtract."
        )
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(HexColor("#718096"))
        c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 10, hint)
        st["y"] -= 18

    def answer_row():
        ya = st["y"] - 26
        c.setStrokeColor(HexColor("#2d3748"))
        c.setLineWidth(1.4)
        c.line(LMARGIN + TEXT_INDENT, ya + 30, LMARGIN + 300, ya + 30)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(black)
        c.drawString(LMARGIN + TEXT_INDENT, ya + 7, "Answer:")
        answer_box(c, LMARGIN + TEXT_INDENT + 58, ya)
        st["y"] = ya - 16

    def render_add(idx, p):
        ha, hb = group_height(digits(p["a"])[0]), group_height(digits(p["b"])[0])
        ensure(2 * 15 + 18 + ha + 14 + hb + 12 + 42)
        draw_text_block(idx, p)
        base_a = st["y"] - ha
        draw_group(c, GROUP_X, base_a, *digits(p["a"]))
        base_b = base_a - 14 - hb
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(HexColor("#2d3748"))
        c.drawString(LMARGIN + 2, base_b + hb / 2 - 7, "+")
        draw_group(c, GROUP_X, base_b, *digits(p["b"]))
        st["y"] = base_b - 12
        answer_row()
        st["y"] -= 8

    def render_sub(idx, p):
        hm = group_height(digits(p["a"])[0])
        ensure(2 * 15 + 18 + hm + 12 + 42)
        draw_text_block(idx, p)
        base_m = st["y"] - hm
        w = draw_group(c, GROUP_X, base_m, *digits(p["a"]))
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(HexColor("#2d3748"))
        c.drawString(LMARGIN + 2, base_m + hm / 2 - 7, "−")
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor("#4a5568"))
        c.drawString(GROUP_X + w + 12, base_m + hm / 2 - 6, f"(cross out {p['b']})")
        st["y"] = base_m - 12
        answer_row()
        st["y"] -= 8

    header()
    for idx, p in enumerate(problems, 1):
        (render_add if p["op"] == "add" else render_sub)(idx, p)

    new_page()
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    c.setFont("Helvetica", 12)
    for i, p in enumerate(problems, 1):
        sign = "+" if p["op"] == "add" else "−"
        c.drawString(LMARGIN, st["y"], f"{i})  {p['a']} {sign} {p['b']} = {p['answer']}")
        st["y"] -= 20

    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="block-word-problems.pdf")
    ap.add_argument("--label", default="Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Base-Ten Block Word Problems")
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = build_problems(rng, args.problems)
    render(problems, args.out, args.title, args.label, "Texas TEKS 2.2(A), 3.4(A)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
