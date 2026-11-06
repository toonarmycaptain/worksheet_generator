"""
PDF worksheets of place-value questions, with an optional answer key page.

Each question shows a number in one form, to be written in another form or chosen in that form
from multiple-choice options.
"""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.pdfgen.canvas import Canvas

from core.placevalue.data import PlaceValueQuestionData
from core.placevalue.representation import format_number, in_asked_form, in_given_form, instruction
from core.question import Question
from render.pdf.page import (
    FONT,
    LINE_HEIGHT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    TEXT_WIDTH,
    Header,
    draw_answer_key,
    new_pdf,
    start_page,
    wrap,
)

ANSWER_LINE_DROP = 14  # offset of the answer line below the next text baseline
ANSWER_HEIGHT = 38  # answer line plus the gap below it, sized so the default 8 fit on a page
CHOICE_INDENT = 22  # offset of an option's text from its letter
CHOICES_GAP = 18  # gap between a question's last option and the next question


def render_place_value_worksheet(
    questions: Sequence[Question[PlaceValueQuestionData]],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
) -> None:
    """
    Render place-value questions, and the answer key if requested, to ``path``.

    Each question states the form to write the number in, followed by the number in its given
    form on its own line. A question with wrong answers is multiple choice, with lettered options
    in the asked form listed below it; one without has an answer line. The answer key gives each
    number in the asked form, prefixed by the correct letter for a multiple-choice question.
    ``path`` is a filename or a binary file-like object.
    """
    pdf = new_pdf(path, header.title)

    y = start_page(pdf, header)
    for number, question in enumerate(questions, start=1):
        lines = _question_lines(question)
        choices = _choice_lines(question)
        space_under = CHOICES_GAP if choices else ANSWER_HEIGHT
        if y - (len(lines) + len(choices)) * LINE_HEIGHT - space_under < MARGIN:
            pdf.showPage()
            y = start_page(pdf, header)
        y = _draw_question(pdf, number, lines, choices, y)

    if answer_key:
        draw_answer_key(pdf, header, [_solution(question) for question in questions])

    pdf.save()


def _question_lines(question: Question[PlaceValueQuestionData]) -> list[str]:
    """Return the instruction line, followed by the number in its given form, wrapped."""
    return [instruction(question), *wrap(in_given_form(question.data), TEXT_SIZE, TEXT_WIDTH)]


def _choice_lines(question: Question[PlaceValueQuestionData]) -> list[tuple[str, str]]:
    """
    Return each option's lines as (letter, text) pairs; continuation lines have no letter.

    A question with no wrong answers has no options, and is drawn with an answer line instead.
    """
    if not question.wrong_answers:
        return []
    lines: list[tuple[str, str]] = []
    for index, option in enumerate(question.options):
        text = format_number(option, question.data.asked)
        first, *more = wrap(text, TEXT_SIZE, TEXT_WIDTH - CHOICE_INDENT)
        lines.append((f"{ascii_uppercase[index]})", first))
        lines += [("", line) for line in more]
    return lines


def _solution(question: Question[PlaceValueQuestionData]) -> str:
    data = question.data
    answer = in_asked_form(data)
    if not question.wrong_answers:
        return answer
    return f"{ascii_uppercase[question.options.index(data.answer)]}) {answer}"


def _draw_question(
    pdf: Canvas, number: int, lines: list[str], choices: list[tuple[str, str]], y: float
) -> float:
    """Draw one question, followed by its options or an answer line, and return the y below it."""
    pdf.setFont(FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, y, f"{number}.")
    for line in lines:
        pdf.drawString(MARGIN + TEXT_INDENT, y, line)
        y -= LINE_HEIGHT
    if not choices:
        line_y = y - ANSWER_LINE_DROP
        pdf.line(MARGIN + TEXT_INDENT, line_y, MARGIN + TEXT_INDENT + TEXT_WIDTH, line_y)
        return y - ANSWER_HEIGHT
    for choice_letter, line in choices:
        if choice_letter:
            pdf.drawString(MARGIN + TEXT_INDENT, y, choice_letter)
        pdf.drawString(MARGIN + TEXT_INDENT + CHOICE_INDENT, y, line)
        y -= LINE_HEIGHT
    return y - CHOICES_GAP
