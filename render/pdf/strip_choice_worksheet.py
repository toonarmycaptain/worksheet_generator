"""
PDF worksheets of problems, each with lettered strip diagrams to choose its own from, with an
optional answer key page.

The first page has the sheet's instruction under its header. Each problem has its number, what
the sheet shows of it (its wording, its equation, or both), and its strip diagrams in rows of
two, each with its letter.
"""

from collections.abc import Sequence
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.representation import (
    STRIP_CHOICE_INSTRUCTION,
    EqualStripDiagram,
    Prompt,
    StripChoiceQuestion,
    StripDiagram,
    prompt_texts,
    solved_equation,
)
from render.pdf.diagrams import STRIP_BAR_HEIGHT, STRIP_HEIGHT, draw_strip_diagram
from render.pdf.page import (
    BOLD_FONT,
    LINE_HEIGHT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    choice_label,
    correct_letters,
    draw_answer_key,
    draw_instruction,
    draw_numbered_lines,
    make_room,
    new_pdf,
    start_page,
    wrap,
)

CHOICE_COLUMNS = 2
CHOICE_LETTER_WIDTH = 26  # room for "A)" left of each strip
CHOICE_GAP = 24  # between a strip and the next choice's letter
CHOICE_WIDTH = (TEXT_WIDTH - CHOICE_GAP) / CHOICE_COLUMNS - CHOICE_LETTER_WIDTH  # each strip
CHOICE_ROW_HEIGHT = STRIP_HEIGHT + 14  # from the top of one row of strips to the top of the next
CHOICES_RAISE = 6  # the strips' top is this far above the next text baseline
PROBLEM_GAP = 22  # from the last row of strips down to the next problem's baseline


def render_strip_choice_worksheet(
    questions: Sequence[StripChoiceQuestion],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
    prompt: Prompt,
) -> None:
    """
    Render problems, each showing what ``prompt`` says with its strip diagrams to choose from,
    and the answer key if requested, to ``path``.

    A problem that would run past the bottom margin starts on the next page. The answer key gives
    each problem's equation, answer and correct letter. ``path`` is a filename or a binary
    file-like object.
    """
    pdf = new_pdf(path, header.title)
    y = draw_instruction(pdf, STRIP_CHOICE_INSTRUCTION, start_page(pdf, header))
    for number, question in enumerate(questions, start=1):
        lines = [
            line
            for text in prompt_texts(question.data, prompt)
            for line in wrap(text, TEXT_SIZE, TEXT_WIDTH)
        ]
        options = question.response.options
        rows = -(-len(options) // CHOICE_COLUMNS)  # rounded up
        height = len(lines) * LINE_HEIGHT - CHOICES_RAISE + rows * CHOICE_ROW_HEIGHT
        y = make_room(pdf, header, y, height)
        y = draw_numbered_lines(pdf, number, lines, y)
        y = _draw_choices(pdf, options, y + CHOICES_RAISE)

    if answer_key:
        solutions = [
            f"{solved_equation(question.data)}    ({correct_letters(question.response)})"
            for question in questions
        ]
        draw_answer_key(pdf, header, solutions)
    pdf.save()


def _draw_choices(
    pdf: Canvas, options: Sequence[StripDiagram | EqualStripDiagram], top: float
) -> float:
    """
    Draw the strips to choose from, ``CHOICE_COLUMNS`` to a row, each with its letter, from
    ``top`` down, and return the next problem's baseline.
    """
    for index, strip in enumerate(options):
        row, column = divmod(index, CHOICE_COLUMNS)
        x = MARGIN + TEXT_INDENT + column * (CHOICE_LETTER_WIDTH + CHOICE_WIDTH + CHOICE_GAP)
        row_top = top - row * CHOICE_ROW_HEIGHT
        # the letter level with the strip's numbers, in the middle of its bar
        pdf.setFont(BOLD_FONT, TEXT_SIZE)
        pdf.drawString(x, row_top - STRIP_HEIGHT + STRIP_BAR_HEIGHT / 2 - 5, choice_label(index))
        draw_strip_diagram(pdf, x + CHOICE_LETTER_WIDTH, row_top, strip, CHOICE_WIDTH)
    last_row = (len(options) - 1) // CHOICE_COLUMNS
    return top - last_row * CHOICE_ROW_HEIGHT - STRIP_HEIGHT - PROBLEM_GAP
