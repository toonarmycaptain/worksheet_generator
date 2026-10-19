#!/usr/bin/env python3
"""Number-line MULTIPLE-CHOICE word-problem worksheets (Grade 3).

The student reads a single-step add/subtract word problem, then chooses which
number line correctly represents its solution (A-D). Every number line starts
at 0 and shows BOTH numbers as jumps:
      0  --(+ a)-->  a  --(± b)-->  answer

The three distractors are the classic errors:
  * wrong operation / direction (second jump goes the wrong way)
  * correct setup but wrong result (landing value miscounted)
  * misread second number (second jump is the wrong amount)

Mixed 2- and 3-digit numbers within 1,000.
Texas TEKS 3.4(A) / 3.5(A): add/subtract within 1,000 with number-line/place-value models.

Usage (no install needed, via uv):
    uv run --with reportlab generate_number_line_mc_word_problems.py --seed 1 --label "Day 3 · Sheet A" --out A.pdf
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
LETTERS = "ABCD"
CELL_H = 50


def _swap_tens_ones(b):
    h, t, o = b // 100, b // 10 % 10, b % 10
    return h * 100 + o * 10 + t


def make_options(rng, p):
    """Return (options, correct_index). Each option: sign, amt2, end (first jump is always +a)."""
    a, b, op, ans = p["a"], p["b"], p["op"], p["answer"]
    sign = "+" if op == "add" else "−"
    opp = "−" if op == "add" else "+"
    opp_end = a - b if op == "add" else a + b  # reversed operation
    bad = {0, a}  # endpoints that would collide with 0 / a ticks

    correct = {"sign": sign, "amt2": b, "end": ans, "tag": "correct"}
    d_dir = {"sign": opp, "amt2": b, "end": opp_end, "tag": "dir"}

    wrong_end = ans
    for delta in (10, -10, 100, -100, 20, -20, 30, -30):
        cand = ans + delta
        if cand > 0 and cand not in bad and cand not in (ans, opp_end):
            wrong_end = cand
            break
    d_end = {"sign": sign, "amt2": b, "end": wrong_end, "tag": "end"}

    bprime, end3 = None, None
    for cb in (_swap_tens_ones(b), b + 11, b - 11, b + 9, b - 9, b + 2, b - 2):
        if cb and cb > 0 and cb != b:
            e = a + cb if op == "add" else a - cb
            if e > 0 and e not in bad and e not in (ans, opp_end, wrong_end):
                bprime, end3 = cb, e
                break
    if bprime is None:  # last-resort fallback
        bprime = b + 3
        end3 = a + bprime if op == "add" else a - bprime
    d_amt = {"sign": sign, "amt2": bprime, "end": end3, "tag": "amt"}

    options = [correct, d_dir, d_end, d_amt]
    rng.shuffle(options)
    correct_index = next(i for i, o in enumerate(options) if o["tag"] == "correct")
    return options, correct_index


def _arc(c, x0, x1, y, label):
    dx = x1 - x0
    h = min(10 + 0.09 * abs(dx), 20)
    c.setStrokeColor(ARC)
    c.setLineWidth(1.2)
    arc = c.beginPath()
    arc.moveTo(x0, y + 2)
    arc.curveTo(x0 + dx * 0.25, y + h, x1 - dx * 0.25, y + h, x1, y + 2)
    c.drawPath(arc, stroke=1, fill=0)
    d = 1 if dx > 0 else -1
    c.setFillColor(ARC)
    ah = c.beginPath()
    ah.moveTo(x1, y + 2)
    ah.lineTo(x1 - d * 6, y + 6)
    ah.lineTo(x1 - d * 6, y - 2)
    ah.close()
    c.drawPath(ah, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ARC)
    c.drawCentredString((x0 + x1) / 2, y + h + 2, label)


def draw_two_jump_line(c, x, y, width, a, opt):
    """0 --(+a)--> a --(sign amt2)--> end. Ticks placed by value order (schematic, open line)."""
    left, right = x + 8, x + width - 8
    end = opt["end"]
    vals = sorted({0, a, end})  # always 3 distinct (guarded in make_options)
    xpos = {v: px for v, px in zip(vals, (left, (left + right) / 2, right))}

    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(left - 4, y, right + 4, y)
    c.setFont("Helvetica-Bold", 8)
    for v in vals:
        tx = xpos[v]
        c.setStrokeColor(LINE)
        c.line(tx, y - 4, tx, y + 4)
        c.setFillColor(black)
        c.drawCentredString(tx, y - 13, str(v))

    _arc(c, xpos[0], xpos[a], y, f"+ {a}")
    _arc(c, xpos[a], xpos[end], y, f"{opt['sign']} {opt['amt2']}")


def draw_option(c, x, y_top, width, letter, a, opt):
    r = 7
    c.setStrokeColor(HexColor("#4a5568"))
    c.setLineWidth(1)
    c.setFillColor(HexColor("#ffffff"))
    c.circle(x + r, y_top - 18, r, stroke=1, fill=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + r, y_top - 21, letter)
    draw_two_jump_line(c, x + 2 * r + 6, y_top - 30, width - 2 * r - 8, a, opt)


def render(problems, path, title, label, teks, seed):
    c = canvas.Canvas(path, pagesize=letter)
    st = {"y": 0.0, "page": 1}
    footer, new_page, ensure = wp.make_page(c, st, label, teks, seed)
    wp.draw_header(
        c,
        st,
        title,
        label,
        "Each number line starts at 0 and shows both numbers as jumps. Circle the correct one.",
    )

    colw = (wp.CONTENT_W - wp.TEXT_INDENT) / 2
    for idx, p in enumerate(problems, 1):
        options, correct = make_options(random.Random(f"{seed}-{idx}"), p)
        p["correct_letter"] = LETTERS[correct]
        ensure(2 * 15 + 16 + 2 * CELL_H + 8)
        wp.draw_problem_text(c, st, idx, p, None)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(HexColor("#718096"))
        c.drawString(
            wp.LMARGIN + wp.TEXT_INDENT, st["y"] - 10, "Which number line shows the solution?"
        )
        st["y"] -= 16
        grid_top = st["y"]
        for i, opt in enumerate(options):
            row, col = divmod(i, 2)
            ox = wp.LMARGIN + wp.TEXT_INDENT + col * colw
            draw_option(c, ox, grid_top - row * CELL_H, colw - 10, LETTERS[i], p["a"], opt)
        st["y"] = grid_top - 2 * CELL_H - 8

    new_page()
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(wp.LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    c.setFont("Helvetica", 12)
    for i, p in enumerate(problems, 1):
        sign = "+" if p["op"] == "add" else "−"
        c.drawString(
            wp.LMARGIN,
            st["y"],
            f"{i})  {p['correct_letter']}   ({p['a']} {sign} {p['b']} = {p['answer']})",
        )
        st["y"] -= 20

    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="number-line-mc-word-problems.pdf")
    ap.add_argument("--label", default="Day 3 · Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Word Problems — Number Lines (Multiple Choice)")
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = wp.build_problems(rng, args.problems, hundreds_cap=9, add_sorted=True)
    render(problems, args.out, args.title, args.label, "Texas TEKS 3.4(A), 3.5(A)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
