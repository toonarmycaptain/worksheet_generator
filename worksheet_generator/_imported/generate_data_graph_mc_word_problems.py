#!/usr/bin/env python3
"""Data and graphs MULTIPLE-CHOICE worksheets: pick the matching graph (Grade 3).

Each problem shows one data set with 4 categories in one model (frequency table,
pictograph, bar graph or dot plot). The student picks which of four choices
(A-D), all drawn as one DIFFERENT model, shows the same data. The three wrong
choices are classic errors:
  * swap:  two categories' values are switched
  * off:   one category is off by a step of the scale (or half a step: a bar
           ending on a line instead of between, a whole star for a half star),
           or by 1 or 2 on a dot plot
  * scale: the picture is right but the key / axis counts by the wrong number,
           or a table lists the number of stars / grid steps instead of the data
Once per 4 problems the given data is instead a scrambled list of numbers
(class sizes, coin values in cents, ...) and the choices are dot plots on a
number line. Their wrong choices: one number miscounted by 1, two numbers'
X's switched, one X per number that appears (instead of one per item), or
every X one place over.
Every model is the one to pick once on a 4-problem sheet, and is never paired
with itself. Data sets come from generate_data_graph_word_problems.py.

Texas TEKS 3.8(A): summarize a data set with multiple categories using a
frequency table, dot plot, pictograph, or bar graph with scaled intervals.

Usage (no install needed, via uv):
    uv run --with reportlab generate_data_graph_mc_word_problems.py --seed 1 --label "Sheet A" --out A.pdf
"""

from __future__ import annotations

import argparse
import os
import random

from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import generate_data_graph_word_problems as dg
from . import wp_common as wp

CELL_BORDER = HexColor("#e2e8f0")
GRAY = dg.GRAY
LETTERS = "ABCD"
CELL_H = 170
GIVEN_W = 260


# ---------------------------------------------------------------- problem bank
def build_problems(rng, n, list_style="mix"):
    decks, problems = {}, []
    for given_model, target_model in dg.model_pairs(rng, n):
        dataset = dg.make_dataset(rng, given_model, target_model, decks)
        if given_model == "list" and list_style != "mix":
            dataset["list_style"] = list_style
        dataset["text"] += f" Which {dg.MODEL_NAME[target_model]} shows the same data?"
        problems.append(dataset)
    return problems


# ------------------------------------------------------------ option building
# A wrong choice is (kind, counts, scale, reason): the counts and scale it is drawn
# with, and the answer-key reason it doesn't match.
def _wrong_number_line_choices(dataset):
    """Wrong dot plots for a list of numbers: miscounts, switched columns, one X per
    number that appears, every X one place over on the number line."""
    counts, labels, ticks = dataset["counts"], dataset["labels"], dataset["ticks"]
    possible = [i for i, tick in enumerate(ticks) if tick in dataset["possible_values"]]
    choices = []
    for x in range(len(possible)):
        for y in range(x + 1, len(possible)):
            first, second = possible[x], possible[y]
            if counts[first] != counts[second]:
                wrong_counts = list(counts)
                wrong_counts[first], wrong_counts[second] = counts[second], counts[first]
                choices.append(
                    (
                        "swap",
                        wrong_counts,
                        1,
                        f"the X's for {labels[first]} and {labels[second]} are switched",
                    )
                )
    for i in possible:
        for wrong_count in (counts[i] - 1, counts[i] + 1):
            if 0 <= wrong_count <= 10:
                wrong_counts = list(counts)
                wrong_counts[i] = wrong_count
                x_marks = "1 X" if wrong_count == 1 else f"{wrong_count} X's"
                choices.append(
                    ("off", wrong_counts, 1, f"{x_marks} above {labels[i]} instead of {counts[i]}")
                )
    choices.append(
        ("once", [min(count, 1) for count in counts], 1, "only one X for each number in the list")
    )
    if len(possible) == len(ticks):  # every tick is a possible value
        if counts[-1] == 0:
            choices.append(("shift", [0] + counts[:-1], 1, "every X is one place too far right"))
        if counts[0] == 0:
            choices.append(("shift", counts[1:] + [0], 1, "every X is one place too far left"))
    return choices


def _wrong_choices(dataset):
    """Every wrong choice for this data set (see the comment above)."""
    if dataset["kind"] == "numbers":
        return _wrong_number_line_choices(dataset)
    counts, scale, labels = dataset["counts"], dataset["scale"], dataset["labels"]
    given_model, target_model = dataset["given_model"], dataset["target_model"]
    has_dot_plot = "dot_plot" in (given_model, target_model)
    choices = []
    for i in range(4):
        for j in range(i + 1, 4):
            wrong_counts = list(counts)
            wrong_counts[i], wrong_counts[j] = counts[j], counts[i]
            choices.append(
                ("swap", wrong_counts, scale, f"{labels[i]} and {labels[j]} are switched")
            )

    smallest_step = scale // 2 if scale % 2 == 0 else scale
    step_sizes = [1, 2] if has_dot_plot else sorted({smallest_step, scale})
    max_count = 10 if has_dot_plot else 9 * scale  # dot plot column / pictograph row still fits
    for i in range(4):
        for step in step_sizes:
            for wrong_count in (counts[i] - step, counts[i] + step):
                if 0 < wrong_count <= max_count:
                    wrong_counts = list(counts)
                    wrong_counts[i] = wrong_count
                    choices.append(
                        (
                            "off",
                            wrong_counts,
                            scale,
                            f"{labels[i]} shows {wrong_count} instead of {counts[i]}",
                        )
                    )

    for wrong_scale in (1, 2, 5, 10):  # same picture, wrong count per star / step
        if wrong_scale == scale or any(count * wrong_scale % scale for count in counts):
            continue
        wrong_counts = [count * wrong_scale // scale for count in counts]
        if target_model == "pictograph":
            reason = f"the key says each star = {wrong_scale}, not {scale}"
        elif target_model == "bar_graph":
            reason = f"the scale counts by {wrong_scale}, not by {scale}"
        elif given_model == "pictograph":
            reason = (
                "counts each star as 1"
                if wrong_scale == 1
                else f"uses a key of {wrong_scale}, not {scale}"
            )
        elif given_model == "bar_graph":
            reason = f"reads the scale as counting by {wrong_scale}, not by {scale}"
        else:
            continue  # table <-> dot plot: no scale to misread
        if target_model == "dot_plot" and max(wrong_counts) > 10:
            continue
        shown_scale = wrong_scale if target_model in ("bar_graph", "pictograph") else scale
        choices.append(("scale", wrong_counts, shown_scale, reason))
    return choices


def make_options(rng, dataset):
    """Return 4 options: the correct one + 3 wrong ones of different kinds when possible."""
    shows_scale = dataset["target_model"] in ("bar_graph", "pictograph")
    appearance = lambda counts, scale: (tuple(counts), scale if shows_scale else None)
    options = [
        {
            "counts": list(dataset["counts"]),
            "scale": dataset["scale"],
            "correct": True,
            "kind": "correct",
        }
    ]
    seen = {appearance(dataset["counts"], dataset["scale"])}
    pool = _wrong_choices(dataset)
    rng.shuffle(pool)
    for new_kind_only in (True, False):
        for kind, wrong_counts, wrong_scale, reason in pool:
            if len(options) == 4:
                break
            if appearance(wrong_counts, wrong_scale) in seen or (
                new_kind_only and any(option["kind"] == kind for option in options)
            ):
                continue
            seen.add(appearance(wrong_counts, wrong_scale))
            options.append(
                {
                    "counts": wrong_counts,
                    "scale": wrong_scale,
                    "correct": False,
                    "kind": kind,
                    "reason": reason,
                }
            )
    rng.shuffle(options)
    return options


# -------------------------------------------------------------------- drawing
def draw_option(c, x, y_top, w, choice_letter, dataset, option):
    c.setStrokeColor(CELL_BORDER)
    c.setLineWidth(1)
    c.roundRect(x, y_top - CELL_H + 4, w, CELL_H - 8, 5, stroke=1, fill=0)
    radius = 8
    center_x, center_y = x + 6 + radius, y_top - 6 - radius
    c.setStrokeColor(HexColor("#4a5568"))
    c.setFillColor(HexColor("#ffffff"))
    c.circle(center_x, center_y, radius, stroke=1, fill=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(center_x, center_y - 3.5, choice_letter)
    shown = {**dataset, "counts": option["counts"], "scale": option["scale"]}
    dg.DRAW_MODEL[dataset["target_model"]](c, x + 10, y_top - 10, w - 20, CELL_H - 22, shown, set())


# ----------------------------------------------------------------- rendering
def render(problems, path, title, label, teks, seed):
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
        "Each problem shows data one way. Find the choice that shows the SAME data another way.",
    )

    content_w = wp.CONTENT_W - wp.TEXT_INDENT
    column_w = content_w / 2
    for number, dataset in enumerate(problems, 1):
        dataset["options"] = make_options(random.Random(f"{seed}-{number}"), dataset)
        intro_lines = len(wp.wrap(c, dataset["text"], "Helvetica", 12, content_w))
        ensure(intro_lines * 15 + 4 + dg.PANEL_H + 8 + 16 + 2 * CELL_H + 10)
        wp.draw_problem_text(c, st, number, dataset, None)
        st["y"] -= 4
        given_x = wp.LMARGIN + wp.TEXT_INDENT + (content_w - GIVEN_W) / 2
        dg.DRAW_MODEL[dataset["given_model"]](
            c, given_x, st["y"], GIVEN_W, dg.PANEL_H, dataset, set()
        )
        st["y"] -= dg.PANEL_H + 8
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(GRAY)
        c.drawString(
            wp.LMARGIN + wp.TEXT_INDENT,
            st["y"] - 10,
            f"Circle the letter of the {dg.MODEL_NAME[dataset['target_model']]} that matches.",
        )
        st["y"] -= 16
        grid_top = st["y"]
        for i, option in enumerate(dataset["options"]):
            row, column = divmod(i, 2)
            option_x = wp.LMARGIN + wp.TEXT_INDENT + column * column_w
            draw_option(
                c, option_x, grid_top - row * CELL_H, column_w - 8, LETTERS[i], dataset, option
            )
        st["y"] = grid_top - 2 * CELL_H - 10

    new_page()
    st["show_seed"] = True
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(wp.LMARGIN, st["y"], f"Answer Key — {label}")
    st["y"] -= 28
    for number, dataset in enumerate(problems, 1):
        options = dataset["options"]
        right = next(LETTERS[i] for i, option in enumerate(options) if option["correct"])
        reasons = " · ".join(
            f"Not {LETTERS[i]}: {option['reason']}"
            for i, option in enumerate(options)
            if not option["correct"]
        )
        reason_lines = wp.wrap(c, reasons, "Helvetica", 9, wp.CONTENT_W - wp.TEXT_INDENT)
        head_lines = wp.wrap(
            c, f"{number})  {right}   ({dg.data_summary(dataset)})", "Helvetica", 12, wp.CONTENT_W
        )
        ensure(14 * len(head_lines) + 6 + 12 * len(reason_lines) + 10)
        c.setFillColor(black)
        c.setFont("Helvetica", 12)
        for i, line in enumerate(head_lines):  # wide number lines: long data line
            c.drawString(wp.LMARGIN + (wp.TEXT_INDENT if i else 0), st["y"], line)
            st["y"] -= 14
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 9)
        for line in reason_lines:
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
    ap.add_argument("--out", default="data-graph-mc-word-problems.pdf")
    ap.add_argument("--label", default="Sheet A")
    ap.add_argument("--problems", type=int, default=4)
    ap.add_argument("--title", default="Data and Graphs — Pick the Matching Graph")
    ap.add_argument(
        "--list-style",
        choices=["mix", *dg.LIST_STYLES],
        default="mix",
        help="how a list of numbers is shown: grid of boxes, commas, or mix (default)",
    )
    args = ap.parse_args()
    args.out = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)  # e.g. --out sheets/A.pdf
    rng = random.Random(args.seed)
    problems = build_problems(rng, args.problems, args.list_style)
    render(problems, args.out, args.title, args.label, "Texas TEKS 3.8(A)", args.seed)
    print(f"Wrote {args.out}  ({len(problems)} problems + answer key)")


if __name__ == "__main__":
    main()
