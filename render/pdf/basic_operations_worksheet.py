"""
PDF worksheets of arithmetic questions, with an optional answer key page.

Questions are either multiple choice or missing-number equations to fill in.
"""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
)
from core.basic_operations.representation import equation, missing_number_equation, stem
from core.question import Question
from render.pdf.page import (
    FONT,
    LINE_HEIGHT,
    MARGIN,
    PAGE_WIDTH,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    draw_answer_key,
    draw_text,
    new_pdf,
    start_page,
)

OPTIONS_HEIGHT = 56  # the row of options and the space below it
EQUATION_SIZE = 20  # missing-number equations, large enough to leave writing room in the square
BLANK_SIDE = 36  # room for a 3-digit number
FILL_IN_ROW = 56  # vertical distance between rows of missing-number equations
FILL_IN_DROP = 12  # lowers the first row's baseline so its square clears the name line
FILL_IN_COLUMNS = 2


def render_basic_operations_worksheet(
    questions: Sequence[Question[BasicOperationQuestionData]],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
) -> None:
    """
    Render multiple-choice arithmetic questions, and the answer key if requested, to ``path``.

    ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)

    y = start_page(pdf, header)
    for number, question in enumerate(questions, start=1):
        lines = simpleSplit(stem(question.data), FONT, TEXT_SIZE, TEXT_WIDTH)
        if y - len(lines) * LINE_HEIGHT - OPTIONS_HEIGHT < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header)
        y = _draw_question(pdf, number, question, lines, y)

    if answer_key:
        draw_answer_key(pdf, header, [_solution(question) for question in questions])

    pdf.save()


def render_missing_number_worksheet(
    questions: Sequence[Question[MissingNumberQuestionData]],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
) -> None:
    """
    Render missing-number equations, and the answer key if requested, to ``path``.

    Each equation has an empty square for its missing number. The equations are laid out in two
    columns, numbered across the rows. ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)

    column_width = (PAGE_WIDTH - 2 * MARGIN) / FILL_IN_COLUMNS
    y = start_page(pdf, header) - FILL_IN_DROP
    for row_start in range(0, len(questions), FILL_IN_COLUMNS):
        if y - BLANK_SIDE / 2 < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header) - FILL_IN_DROP
        row = questions[row_start : row_start + FILL_IN_COLUMNS]
        for column, question in enumerate(row):
            x = MARGIN + column * column_width
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(x, y, f"{row_start + column + 1}.")
            text = missing_number_equation(question.data)
            pdf.setFont(FONT, EQUATION_SIZE)
            draw_text(pdf, x + TEXT_INDENT, y, text, EQUATION_SIZE, BLANK_SIDE)
        y -= FILL_IN_ROW

    if answer_key:
        solutions = [
            f"{data.answer}    ({missing_number_equation(data, data.answer)})"
            for data in (question.data for question in questions)
        ]
        draw_answer_key(pdf, header, solutions)

    pdf.save()


def _solution(question: Question[BasicOperationQuestionData]) -> str:
    letter = ascii_uppercase[question.options.index(question.data.answer)]
    return f"{equation(question.data)} = {question.data.answer}    ({letter})"


def _draw_question(
    pdf: Canvas,
    number: int,
    question: Question[BasicOperationQuestionData],
    lines: list[str],
    y: float,
) -> float:
    """Draw one question with its lettered options in a row, and return the y below it."""
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= LINE_HEIGHT

    column_width = TEXT_WIDTH / len(question.options)
    for column, value in enumerate(question.options):
        x = MARGIN + TEXT_INDENT + column * column_width
        pdf.drawString(x, y - 6, f"{ascii_uppercase[column]}) {value}")
    return y - OPTIONS_HEIGHT
