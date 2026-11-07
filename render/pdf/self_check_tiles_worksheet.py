"""PDF worksheets for the self-check tiles case, with an optional answer key page."""

from collections.abc import Sequence
from typing import BinaryIO

from core.self_check_tiles import TileQuestion
from render.pdf.page import (
    CONTENT_WIDTH,
    FONT,
    MARGIN,
    TEXT_INDENT,
    TEXT_SIZE,
    Header,
    draw_answer_key,
    draw_text,
    new_pdf,
    start_page,
    text_width,
    wrap,
)
from render.pdf.tiles import draw_tiles, tile_solutions

COLUMN_GAP = 12  # between the left column's questions and the right column's numbers
QUESTION_WIDTH = CONTENT_WIDTH / 2 - TEXT_INDENT - COLUMN_GAP  # available to each question
SMALLER_SIZES = (12, 10)  # for a question too long for one line at TEXT_SIZE
QUESTION_ROW = 34
QUESTIONS_PER_COLUMN = 6


def render_self_check_tiles_worksheet(
    questions: Sequence[TileQuestion],
    slot_of: Sequence[int],
    path: str | BinaryIO,
    header: Header,
    answer_key: bool,
) -> None:
    """
    Render the questions, answer bank and pattern, and the answer key if requested, to ``path``.

    There are at most 12 questions, one per tile; ``slot_of[i]`` is the slot of question i + 1's
    answer, as in ``core.self_check_tiles``, and unused slots are blocked out. The answers must
    be distinct; ``draw_tiles`` describes how the bank fits them. A question too long for one
    line of its column is drawn smaller, on up to two lines. ``path`` is a filename or a binary
    file-like object.
    """
    pdf = new_pdf(path, header.title)

    y = start_page(pdf, header)
    for index, question in enumerate(questions):
        column, row = divmod(index, QUESTIONS_PER_COLUMN)
        x = MARGIN + column * CONTENT_WIDTH / 2
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(x, y - row * QUESTION_ROW, f"{index + 1}.")
        size, lines = _fit(question.prompt)
        if size != TEXT_SIZE:
            pdf.setFont(FONT, size)
        for number, line in enumerate(lines):
            line_y = y - row * QUESTION_ROW - number * (size + 2)
            draw_text(pdf, x + TEXT_INDENT, line_y, line, size)
    draw_tiles(pdf, [question.answer for question in questions], slot_of)

    if answer_key:
        draw_answer_key(pdf, header, tile_solutions(questions, slot_of))

    pdf.save()


def _fit(text: str) -> tuple[int, list[str]]:
    """
    Return the font size and lines for a question.

    The question is drawn on one line at ``TEXT_SIZE`` if it fits; otherwise at the largest of
    ``SMALLER_SIZES`` at which it takes at most two lines, or the smallest if none does.
    """
    if text_width(text, TEXT_SIZE) <= QUESTION_WIDTH:
        return TEXT_SIZE, [text]
    for size in SMALLER_SIZES:
        lines = wrap(text, size, QUESTION_WIDTH)
        if len(lines) <= 2:
            return size, lines
    # Not reached by any current question: the longest place-value prompts, such as 777,777 in
    # word form or expanded notation, take two lines at the smallest size. A prompt that needs
    # three would draw its last line into the next question's row.
    return size, lines
