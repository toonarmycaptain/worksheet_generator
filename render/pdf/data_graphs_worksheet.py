"""
PDF worksheets of data sets, each with a display to complete and two problems, with an optional
answer key page.

The first page has the sheet's instruction under its header. Each problem has its number and
introduction, then part a: its task, with the given display beside the display to complete.
Parts b and c are the one-step and two-step problems, each with an answer box on the right.
"""

from collections.abc import Sequence
from typing import BinaryIO

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.discrete_data.data import (
    CategoricalDataProblemData,
    DataDisplay,
    DiscreteDataProblem,
    NumericalDataProblemData,
)
from core.discrete_data.representation import (
    DISPLAY_NAMES,
    INSTRUCTION,
    blank_counts,
    intro,
    stem,
    work,
)
from render.pdf.data_displays import NumberListStyle, draw_display
from render.pdf.page import (
    BOLD_FONT,
    FONT,
    MARGIN,
    PAGE_WIDTH,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    draw_answer_key,
    draw_instruction,
    make_room,
    new_pdf,
    start_page,
    wrap,
)

INTRO_SIZE = 12
INTRO_LINE_HEIGHT = 15
PART_SIZE = 11
PART_LINE_HEIGHT = 14
PART_INDENT = 18  # from a part's letter to its text
PART_GAP = 8  # below a part's lines, which take at least two lines' room, for its answer box
PANEL_HEIGHT = 150
PANEL_GAP = 16  # between the given display and the display to complete
PANEL_RAISE = 6  # the panels' top is this far above the next text baseline
PANEL_DROP = 22  # from the bottom of the panels down to part b's baseline
LIST_PANEL_WIDTH = 180  # a list is narrow, leaving its number line room for the Xs
BOX_WIDTH = 74
BOX_HEIGHT = 22
BOX_CORNER_RADIUS = 4
BOX_COLOUR = HexColor("#4a5568")  # dark grey
BOX_DROP = 7  # from a part's first baseline down to the bottom of its box
ANSWER_LABEL = "Answer:"
ANSWER_LABEL_GAP = 6  # from the label to the box
QUESTION_GAP = 12  # at least, from a part's text to its "Answer:" label
QUESTION_WIDTH = (
    TEXT_WIDTH
    - PART_INDENT
    - QUESTION_GAP
    - stringWidth(ANSWER_LABEL, BOLD_FONT, PART_SIZE)
    - ANSWER_LABEL_GAP
    - BOX_WIDTH
)
PROBLEM_GAP = 22  # from the end of a problem down to the next problem's baseline


def render_data_graphs_worksheet(
    problems: Sequence[DiscreteDataProblem],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    list_style: NumberListStyle,
) -> None:
    """
    Render data-set problems, and the answer key if requested, to ``path``.

    A list of numbers is shown in ``list_style``. A problem that would run past the bottom
    margin starts on the next page. The answer key gives each problem's blank counts, then its
    two answers with their work. ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)
    y = draw_instruction(pdf, INSTRUCTION, start_page(pdf, header))
    for number, problem in enumerate(problems, start=1):
        intro_lines = wrap(intro(problem.summarize.data), INTRO_SIZE, TEXT_WIDTH)
        task_lines = wrap(stem(problem.summarize.data), PART_SIZE, TEXT_WIDTH - PART_INDENT)
        part_lines = [
            wrap(stem(question.data), PART_SIZE, QUESTION_WIDTH)
            for question in (problem.one_step, problem.two_step)
        ]
        height = (
            len(intro_lines) * INTRO_LINE_HEIGHT
            + len(task_lines) * PART_LINE_HEIGHT
            - PANEL_RAISE
            + PANEL_HEIGHT
            + PANEL_DROP
            + sum(_part_height(lines) for lines in part_lines)
        )
        y = make_room(pdf, header, y, height)
        y = _draw_problem(pdf, number, problem, intro_lines, task_lines, part_lines, list_style, y)

    if answer_key:
        draw_answer_key(pdf, header, [_solution(problem) for problem in problems])
    pdf.save()


def _part_height(lines: Sequence[str]) -> float:
    """Return the room a part takes: at least two lines, so its answer box fits beside them."""
    return max(2, len(lines)) * PART_LINE_HEIGHT + PART_GAP


def _draw_problem(
    pdf: Canvas,
    number: int,
    problem: DiscreteDataProblem,
    intro_lines: Sequence[str],
    task_lines: Sequence[str],
    part_lines: Sequence[Sequence[str]],
    list_style: NumberListStyle,
    y: float,
) -> float:
    """Draw one problem from its number down, and return the next problem's baseline."""
    x = MARGIN + TEXT_INDENT
    pdf.setFillColor("black")
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    pdf.setFont(FONT, INTRO_SIZE)
    for line in intro_lines:
        pdf.drawString(x, y, line)
        y -= INTRO_LINE_HEIGHT

    y = _draw_part_text(pdf, "a", task_lines, y)
    summarize = problem.summarize.data
    top = y + PANEL_RAISE
    given_width = (
        LIST_PANEL_WIDTH if summarize.given is DataDisplay.LIST else (TEXT_WIDTH - PANEL_GAP) / 2
    )
    target_width = TEXT_WIDTH - PANEL_GAP - given_width
    draw_display(
        pdf, summarize.given, summarize.dataset, x, top, given_width, PANEL_HEIGHT, (), list_style
    )
    draw_display(
        pdf,
        summarize.target,
        summarize.dataset,
        x + given_width + PANEL_GAP,
        top,
        target_width,
        PANEL_HEIGHT,
        summarize.blanks,
        list_style,
    )

    y = top - PANEL_HEIGHT - PANEL_DROP
    for letter, lines in zip("bc", part_lines, strict=True):
        _draw_part_text(pdf, letter, lines, y)
        _draw_answer_box(pdf, y)
        y -= _part_height(lines)
    return y - PROBLEM_GAP


def _draw_part_text(pdf: Canvas, letter: str, lines: Sequence[str], y: float) -> float:
    """Draw a part's letter and text from baseline ``y``, and return the baseline below them."""
    x = MARGIN + TEXT_INDENT
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, PART_SIZE)
    pdf.drawString(x, y, f"{letter}.")
    pdf.setFont(FONT, PART_SIZE)
    for line in lines:
        pdf.drawString(x + PART_INDENT, y, line)
        y -= PART_LINE_HEIGHT
    return y


def _draw_answer_box(pdf: Canvas, y: float) -> None:
    """Draw "Answer:" and its box at the right margin, beside a part's first baseline ``y``."""
    box_x = PAGE_WIDTH - MARGIN - BOX_WIDTH
    pdf.saveState()
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, PART_SIZE)
    pdf.drawRightString(box_x - ANSWER_LABEL_GAP, y, ANSWER_LABEL)
    pdf.setStrokeColor(BOX_COLOUR)
    pdf.setLineWidth(1)
    pdf.roundRect(box_x, y - BOX_DROP, BOX_WIDTH, BOX_HEIGHT, BOX_CORNER_RADIUS, fill=0)
    pdf.restoreState()


def _solution(problem: DiscreteDataProblem) -> str:
    """Return the problem's answer key entry: a line for each part."""
    summarize = problem.summarize.data
    target = DISPLAY_NAMES[summarize.target].capitalize()
    rows = [f"a.  {target} \N{EM DASH} {blank_counts(summarize)}"]
    parts: Sequence[CategoricalDataProblemData | NumericalDataProblemData] = (
        problem.one_step.data,
        problem.two_step.data,
    )
    rows += [
        f"{letter}.  {data.answer}   ({work(data)})"
        for letter, data in zip("bc", parts, strict=True)
    ]
    return "\n".join(rows)
