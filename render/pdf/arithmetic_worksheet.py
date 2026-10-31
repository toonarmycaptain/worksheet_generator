"""A PDF worksheet of multiple-choice arithmetic questions, with an optional answer key page."""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.lib.colors import gray  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.utils import simpleSplit  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]

from core.arithmetic import Operation
from core.question import Question

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 54
TEXT_INDENT = 28  # the question text hangs to the right of its number
TEXT_WIDTH = PAGE_WIDTH - 2 * MARGIN - TEXT_INDENT
FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
TEXT_SIZE = 14
LINE_HEIGHT = 20
OPTIONS_HEIGHT = 56  # the row of choices, and the space under it
FIRST_LINE_Y: float = PAGE_HEIGHT - MARGIN - 60

SYMBOLS = {
    Operation.ADD: "+",
    Operation.SUBTRACT: "\N{MINUS SIGN}",
    Operation.MULTIPLY: "\N{MULTIPLICATION SIGN}",
    Operation.DIVIDE: "\N{DIVISION SIGN}",
}

# What a sheet of each operation is called, so its title unless one is given
OPERATION_NAMES = {
    Operation.ADD: "Addition",
    Operation.SUBTRACT: "Subtraction",
    Operation.MULTIPLY: "Multiplication",
    Operation.DIVIDE: "Division",
}


def render_arithmetic_worksheet(
    questions: Sequence[Question],
    path: str | BinaryIO,
    title: str,
    label: str,
    answer_key: bool,
) -> None:
    """Draw the questions, and the answer key page if asked, into ``path``.

    ``path`` can be a filename or a file-like object.
    """
    pdf = Canvas(path, pagesize=letter)
    pdf.setTitle(title)

    y = _start_page(pdf, title, label, with_name_line=True)
    for number, question in enumerate(questions, start=1):
        lines = simpleSplit(_stem(question), FONT, TEXT_SIZE, TEXT_WIDTH)
        if y - len(lines) * LINE_HEIGHT - OPTIONS_HEIGHT < MARGIN:
            pdf.showPage()
            y = _start_page(pdf, title, label, with_name_line=True)
        y = _draw_question(pdf, number, question, lines, y)

    if answer_key:
        pdf.showPage()
        y = _start_page(pdf, f"{title}: Answer Key", label, with_name_line=False)
        for number, question in enumerate(questions, start=1):
            if y < MARGIN + LINE_HEIGHT:
                pdf.showPage()
                y = _start_page(pdf, f"{title}: Answer Key", label, with_name_line=False)
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(MARGIN, y, f"{number}.")
            pdf.drawString(MARGIN + TEXT_INDENT, y, _solution(question))
            y -= LINE_HEIGHT

    pdf.save()


def _equation(question: Question) -> str:
    first, second = question.data.operands
    return f"{first} {SYMBOLS[question.data.operation]} {second}"


def _stem(question: Question) -> str:
    """What the student reads: the question's own wording, or its equation with a gap."""
    if question.data.question_text is not None:
        return question.data.question_text
    return f"{_equation(question)} = ?"


def _solution(question: Question) -> str:
    letter = ascii_uppercase[question.options.index(question.data.answer)]
    return f"{_equation(question)} = {question.data.answer}    ({letter})"


def _start_page(pdf: Canvas, title: str, label: str, *, with_name_line: bool) -> float:
    """Draw the header and footer of a new page. Returns the y to start drawing at."""
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 18)
    pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN, title)
    if with_name_line:
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(MARGIN, PAGE_HEIGHT - MARGIN - 30, "Name: " + "_" * 28)
        pdf.drawString(PAGE_WIDTH / 2 + 40, PAGE_HEIGHT - MARGIN - 30, "Date: " + "_" * 16)
    pdf.setFont(FONT, 9)
    pdf.setFillColor(gray)
    pdf.drawString(MARGIN, MARGIN / 2, label)
    pdf.setFillColor("black")
    return FIRST_LINE_Y


def _draw_question(
    pdf: Canvas, number: int, question: Question, lines: list[str], y: float
) -> float:
    """Draw one question with its lettered choices in a row. Returns the y below it."""
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
