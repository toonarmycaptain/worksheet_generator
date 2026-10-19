#!/usr/bin/env python3
"""Strip-diagram (bar-model) WORD-PROBLEM worksheets: single-step add/subtract.

Each word problem comes with a part-part-whole strip diagram:
  * addition    -> the two parts (a, b) are shown; the whole is "?"
  * subtraction -> the whole (a) and one part (b) are shown; the other part is "?"

Mixed 2- and 3-digit numbers within 1,000. Grade 3.
Texas TEKS 3.5(A): represent one-step addition/subtraction problems to 1,000
using pictorial models such as strip diagrams.

Usage (no install needed, via uv):
    uv run --with reportlab generate_strip_word_problems.py --seed 1 --label "Day 2 · Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import wp_common as wp

PART_FILL = HexColor("#cfe3f7")  # known parts
UNKNOWN_FILL = HexColor("#fef3c7")  # the "?" part


def _clamp(v, lo=0.32, hi=0.68):
    return max(lo, min(hi, v))


def draw_strip(c, x, y_top, width, left_label, right_label, whole_label, split, unknown_side):
    """Part-part-whole bar. unknown_side in {'whole','right'}. Returns height used."""
    bar_h = 34
    brace_y = y_top - 12
    bar_top = brace_y - 8
    dx = x + width * split

    # whole label + brace across the top
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + width / 2, y_top - 8, f"whole: {whole_label}")
    c.setStrokeColor(HexColor("#718096"))
    c.setLineWidth(1)
    c.line(x, brace_y, x + width, brace_y)
    c.line(x, brace_y, x, brace_y - 4)
    c.line(x + width, brace_y, x + width, brace_y - 4)

    # cells (shade the unknown one)
    c.setLineWidth(1.2)
    c.setStrokeColor(HexColor("#2d3748"))
    left_fill = PART_FILL
    right_fill = UNKNOWN_FILL if unknown_side == "right" else PART_FILL
    c.setFillColor(left_fill)
    c.rect(x, bar_top - bar_h, dx - x, bar_h, stroke=1, fill=1)
    c.setFillColor(right_fill)
    c.rect(dx, bar_top - bar_h, x + width - dx, bar_h, stroke=1, fill=1)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(x + (dx - x) / 2, bar_top - bar_h / 2 - 4, left_label)
    c.drawCentredString(dx + (x + width - dx) / 2, bar_top - bar_h / 2 - 4, right_label)
    return y_top - (bar_top - bar_h)


def render(problems, path, title, label, teks, seed, answer_key):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle(f"{title} — {label}")  # shown by PDF viewers instead of "untitled"
    c.setSubject(teks)
    c.setCreator("TEKS worksheet generator")
    st = {"y": 0.0, "page": 1}
    footer, new_page, ensure = wp.make_page(c, st, label, teks, seed)

    wp.draw_header(
        c,
        st,
        title,
        label,
        "Use the strip diagram (bar model): two parts make a whole. Shaded box = what to find.",
    )

    width = 360
    x = wp.LMARGIN + wp.TEXT_INDENT
    for idx, p in enumerate(problems, 1):
        a, b = p["a"], p["b"]
        if p["op"] == "add":
            left, right, whole = str(a), str(b), "?"
            split, unknown = _clamp(a / (a + b)), "whole"
            hint = "Both parts are shown. Add the parts to find the whole."
        else:
            left, right, whole = str(b), "?", str(a)
            split, unknown = _clamp(b / a), "right"
            hint = "The whole and one part are shown. Subtract to find the missing part."
        ensure(2 * 15 + 16 + 54 + 40)
        wp.draw_problem_text(c, st, idx, p, hint)
        h = draw_strip(c, x, st["y"], width, left, right, whole, split, unknown)
        st["y"] -= h + 6
        wp.draw_answer_row(c, st)
        st["y"] -= 8

    if answer_key:
        wp.answer_key_page(c, st, new_page, label, problems)
    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="strip-word-problems.pdf")
    ap.add_argument("--label", default="Day 2 · Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Word Problems — Strip Diagrams")
    ap.add_argument(
        "--answer-key", action="store_true", help="also generate an answer-key page (default: off)"
    )
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = wp.build_problems(rng, args.problems, hundreds_cap=9)
    render(
        problems, args.out, args.title, args.label, "Texas TEKS 3.5(A)", args.seed, args.answer_key
    )
    print(
        f"Wrote {args.out}  ({len(problems)} problems{' + answer key' if args.answer_key else ''})"
    )


if __name__ == "__main__":
    main()
