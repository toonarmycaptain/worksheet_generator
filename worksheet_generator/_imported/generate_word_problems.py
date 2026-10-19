#!/usr/bin/env python3
"""Single-step addition & subtraction word-problem worksheet generator (Grade 3).

Mixed 2- and 3-digit numbers within 1,000, one operation per problem, with a
work-space box, an answer line, and a separate answer key.

Aligned to Texas TEKS 3.4(A): solve one-step problems involving addition and
subtraction within 1,000 using strategies based on place value, properties of
operations, and the relationship between addition and subtraction.

Usage (no install needed, via uv):
    uv run --with reportlab generate_word_problems.py --seed 1 --label "Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = letter
LMARGIN = RMARGIN = TMARGIN = BMARGIN = 54
CONTENT_W = PAGE_W - LMARGIN - RMARGIN
TEXT_INDENT = 22  # text hangs to the right of the problem number

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
    "trading cards",
    "seashells",
    "buttons",
    "beads",
    "crayons",
    "stamps",
    "acorns",
    "pennies",
    "books",
    "apples",
    "cookies",
    "pencils",
    "bottle caps",
    "leaves",
    "coins",
]

# Each template uses {n1} {n2} {a} {b} {obj}. Templates may ignore keys they
# don't need (e.g. ones that hardcode "points" or "miles").
ADD_TEMPLATES = [
    "{n1} collected {a} {obj}. {n2} collected {b} {obj}. How many {obj} did they collect altogether?",
    "There were {a} {obj} in the bin. {n1} put in {b} more. How many {obj} are in the bin now?",
    "The library had {a} books. It received {b} more books. How many books does the library have now?",
    "{n1} scored {a} points in the first game and {b} points in the second game. How many points in all?",
    "{n1} read {a} pages on Monday and {b} pages on Tuesday. How many pages did {n1} read in all?",
    "A farm gathered {a} {obj} and then gathered {b} more. How many {obj} were gathered in all?",
]
SUB_TEMPLATES = [
    "{n1} had {a} {obj}. {n1} gave away {b} of them. How many {obj} does {n1} have left?",
    "There were {a} {obj} on the shelf. {b} of them were sold. How many {obj} are left?",
    "{n1} has {a} {obj} and {n2} has {b} {obj}. How many more {obj} does {n1} have than {n2}?",
    "{n1} wants to collect {a} {obj} in all. So far {n1} has {b}. How many more {obj} are needed?",
    "A book has {a} pages. {n1} has already read {b} pages. How many pages are left to read?",
    "{n1} had {a} points and lost {b} points. How many points does {n1} have now?",
]

# Digit profiles (len_a, len_b), cycled + shuffled so every sheet mixes 2- & 3-digit.
PROFILES = [(2, 2), (2, 3), (3, 2), (3, 3)]


def _num(rng, d):
    return rng.randint(11, 99) if d == 2 else rng.randint(101, 999)


def build_problems(rng, n):
    profiles = [PROFILES[i % len(PROFILES)] for i in range(n)]
    rng.shuffle(profiles)
    problems = []
    for da, db in profiles:
        op = rng.choice(["add", "sub"])
        n1, n2 = rng.sample(NAMES, 2)
        obj = rng.choice(OBJECTS)
        if op == "add":
            while True:
                a, b = _num(rng, da), _num(rng, db)
                if a + b <= 999:
                    break
            template = rng.choice(ADD_TEMPLATES)
            answer = a + b
        else:
            a, b = _num(rng, da), _num(rng, db)
            a, b = max(a, b), min(a, b)
            if a == b:  # keep a genuine difference
                a += rng.randint(1, 9)
            template = rng.choice(SUB_TEMPLATES)
            answer = a - b
        text = template.format(n1=n1, n2=n2, a=a, b=b, obj=obj)
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
        c.drawString(
            LMARGIN,
            st["y"],
            "Read each problem. Show your work in the box, then write your answer.",
        )
        st["y"] -= 16
        c.setFillColor(black)
        c.setFont("Helvetica", 11)
        c.drawString(LMARGIN, st["y"], "Name: ______________________________")
        c.drawRightString(PAGE_W - RMARGIN, st["y"], "Date: ______________")
        st["y"] -= 12
        c.setStrokeColor(HexColor("#cbd5e0"))
        c.setLineWidth(1)
        c.line(LMARGIN, st["y"], PAGE_W - RMARGIN, st["y"])
        st["y"] -= 18

    def render_problem(idx, p):
        lines = wrap(c, p["text"], "Helvetica", 12, CONTENT_W - TEXT_INDENT)
        box_h = 44
        block_h = len(lines) * 15 + 8 + box_h + 20 + 14
        ensure(block_h)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(black)
        c.drawString(LMARGIN, st["y"] - 11, f"{idx})")
        c.setFont("Helvetica", 12)
        for line in lines:
            c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 11, line)
            st["y"] -= 15
        st["y"] -= 8
        # work space
        c.setStrokeColor(HexColor("#cbd5e0"))
        c.setLineWidth(1)
        c.roundRect(
            LMARGIN + TEXT_INDENT,
            st["y"] - box_h,
            CONTENT_W - TEXT_INDENT,
            box_h,
            4,
            stroke=1,
            fill=0,
        )
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(HexColor("#a0aec0"))
        c.drawString(LMARGIN + TEXT_INDENT + 5, st["y"] - 11, "Show your work")
        st["y"] -= box_h + 6
        # answer line
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(LMARGIN + TEXT_INDENT, st["y"] - 4, "Answer: ______________________")
        st["y"] -= 22

    header()
    for idx, p in enumerate(problems, 1):
        render_problem(idx, p)

    # Answer key page.
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
    ap.add_argument("--out", default="word-problems.pdf")
    ap.add_argument("--label", default="Sheet A")
    ap.add_argument("--problems", type=int, default=6)
    ap.add_argument("--title", default="Addition & Subtraction Word Problems")
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf

    rng = random.Random(args.seed)
    problems = build_problems(rng, args.problems)
    render(problems, args.out, args.title, args.label, "Texas TEKS 3.4(A)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
