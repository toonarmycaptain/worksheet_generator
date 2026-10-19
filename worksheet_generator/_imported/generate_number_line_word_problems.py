#!/usr/bin/env python3
"""Number-line WORD-PROBLEM worksheets: single-step add/subtract (Grade 3).

Each word problem comes with an open number line. The starting number is
labeled; the second number is broken into place-value jumps (hundreds, tens,
ones) drawn as labeled arcs. The student fills the box under each landing tick;
the last box is the answer.
  * addition    -> jumps go right (+100, +40, +9, ...)
  * subtraction -> jumps go left  (-100, -40, -9, ...)

Mixed 2- and 3-digit numbers within 1,000.
Texas TEKS 3.4(A) / 3.5(A): add/subtract within 1,000 using place-value
strategies represented on a number line.

Usage (no install needed, via uv):
    uv run --with reportlab generate_number_line_word_problems.py --seed 1 --label "Day 3 · Sheet A" --out A.pdf
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


def draw_number_line(c, x, y, width, start_val, chunks, op):
    """Open number line with place-value jump arcs. Returns nothing; draws at baseline y."""
    ticks = max(len(chunks) + 1, 2)
    step = width / (ticks - 1)
    xs = [x + i * step for i in range(ticks)]

    # baseline + end arrows
    c.setStrokeColor(LINE)
    c.setLineWidth(1.2)
    c.line(x - 8, y, x + width + 8, y)
    c.setFillColor(LINE)
    for ax, d in ((x - 8, -1), (x + width + 8, 1)):
        p = c.beginPath()
        p.moveTo(ax + d * 7, y)
        p.lineTo(ax, y + 4)
        p.lineTo(ax, y - 4)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    # ticks
    for tx in xs:
        c.line(tx, y - 4, tx, y + 4)

    # start value under the first tick
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(xs[0], y - 17, str(start_val))

    # answer boxes under every landing tick
    bw, bh = 44, 18
    c.setStrokeColor(HexColor("#4a5568"))
    c.setLineWidth(1)
    for tx in xs[1:]:
        c.roundRect(tx - bw / 2, y - 9 - bh, bw, bh, 3, stroke=1, fill=0)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#718096"))
    c.drawCentredString(xs[-1], y - 9 - bh - 9, "answer")

    # jump arcs + labels
    sign = "+" if op == "add" else "−"
    for i, ch in enumerate(chunks):
        x0, x1 = xs[i], xs[i + 1]
        c.setStrokeColor(ARC)
        c.setLineWidth(1.3)
        arc = c.beginPath()
        arc.moveTo(x0, y + 3)
        arc.curveTo(x0 + (x1 - x0) * 0.25, y + 26, x1 - (x1 - x0) * 0.25, y + 26, x1, y + 3)
        c.drawPath(arc, stroke=1, fill=0)
        c.setFillColor(ARC)
        ah = c.beginPath()
        ah.moveTo(x1, y + 3)
        ah.lineTo(x1 - 5, y + 9)
        ah.lineTo(x1 + 2, y + 8)
        ah.close()
        c.drawPath(ah, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString((x0 + x1) / 2, y + 29, f"{sign} {ch}")


def render(problems, path, title, label, teks, seed):
    c = canvas.Canvas(path, pagesize=letter)
    st = {"y": 0.0, "page": 1}
    footer, new_page, ensure = wp.make_page(c, st, label, teks, seed)

    wp.draw_header(
        c,
        st,
        title,
        label,
        "Use the number line. Start at the first number and jump by hundreds, tens, and ones.",
    )

    x = wp.LMARGIN + wp.TEXT_INDENT + 8
    width = wp.CONTENT_W - wp.TEXT_INDENT - 24
    for idx, p in enumerate(problems, 1):
        chunks = wp.place_chunks(p["b"])
        hint = (
            "Jump forward to add." if p["op"] == "add" else "Jump backward to subtract."
        ) + " Fill in each box; the last box is your answer."
        ensure(2 * 15 + 16 + 44 + 40 + 24)
        wp.draw_problem_text(c, st, idx, p, hint)
        y_line = st["y"] - 42  # room for arcs above the line
        draw_number_line(c, x, y_line, width, p["a"], chunks, p["op"])
        st["y"] = y_line - 42  # below the boxes/caption
        st["y"] -= 10

    wp.answer_key_page(c, st, new_page, label, problems)
    footer()
    c.showPage()
    c.save()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="number-line-word-problems.pdf")
    ap.add_argument("--label", default="Day 3 · Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Word Problems — Number Lines")
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = wp.build_problems(rng, args.problems, hundreds_cap=9)
    render(problems, args.out, args.title, args.label, "Texas TEKS 3.4(A), 3.5(A)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
