"""A PDF worksheet for the self-check tiles answer case, with an optional answer key page."""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.lib.colors import HexColor, gray, white  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
from reportlab.lib.utils import simpleSplit  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]

from core.arithmetic import ArithmeticQuestionData
from core.self_check_tiles import SLOTS_PER_ROW, TILES, answer_bank, pattern, tile_outline
from render.pdf.arithmetic_worksheet import (
    BOLD_FONT,
    FONT,
    LINE_HEIGHT,
    MARGIN,
    PAGE_WIDTH,
    TEXT_INDENT,
    TEXT_SIZE,
    equation,
    start_page,
    stem,
)

CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
QUESTION_ROW = 34
QUESTIONS_PER_COLUMN = 6
BANK_TOP = 400  # the top edge of the answer bank's top row
BOX_WIDTH = CONTENT_WIDTH / SLOTS_PER_ROW
BOX_HEIGHT = 44
PATTERN_TOP = 250
PATTERN_TILE = 40
CAPTION = "Close the case and flip it over. If every answer is right, the back looks like this."
INSTRUCTION = "Put each numbered tile in the slot whose letter matches the answer to its question."
BLOCKED_NOTE = " Shaded boxes are not used."

COLORS = {"yellow": HexColor("#f0be00"), "red": HexColor("#d9262c"), "blue": HexColor("#003cc8")}
BLOCKED = HexColor("#d9d9d9")  # a slot no question uses


def render_self_check_tiles_worksheet(
    questions: Sequence[ArithmeticQuestionData],
    slot_of: Sequence[int],
    path: str | BinaryIO,
    title: str,
    label: str,
    answer_key: bool,
) -> None:
    """Draw the questions, the answer bank and the pattern, and the answer key if asked.

    There are up to 12 questions, one for each tile, and ``slot_of[n]`` is the slot of question
    n+1's answer, as in ``core.self_check_tiles``. The slots left over are blocked out. The
    questions are short equations, since each is drawn on one line. ``path`` can be a filename or
    a file-like object.
    """
    pdf = Canvas(path, pagesize=letter)
    pdf.setTitle(title)

    y = start_page(pdf, title, label, with_name_line=True)
    for index, data in enumerate(questions):
        column, row = divmod(index, QUESTIONS_PER_COLUMN)
        x = MARGIN + column * CONTENT_WIDTH / 2
        pdf.setFont(FONT, TEXT_SIZE)
        pdf.drawString(x, y - row * QUESTION_ROW, f"{index + 1}.")
        pdf.drawString(x + TEXT_INDENT, y - row * QUESTION_ROW, stem(data))
    _draw_answer_bank(pdf, answer_bank([data.answer for data in questions], slot_of))
    _draw_pattern(pdf, pattern(slot_of))

    if answer_key:
        pdf.showPage()
        y = start_page(pdf, f"{title}: Answer Key", label, with_name_line=False)
        for index, data in enumerate(questions):
            slot_letter = ascii_uppercase[slot_of[index]]
            pdf.setFont(FONT, TEXT_SIZE)
            pdf.drawString(MARGIN, y, f"{index + 1}.")
            pdf.drawString(
                MARGIN + TEXT_INDENT, y, f"{equation(data)} = {data.answer}    ({slot_letter})"
            )
            y -= LINE_HEIGHT

    pdf.save()


def _draw_answer_bank(pdf: Canvas, bank: Sequence[int | None]) -> None:
    """Draw the bank as the case's slots: two rows of boxes, letters on the edges.

    A slot with no answer is a shaded, empty box.
    """
    pdf.setFont(BOLD_FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, BANK_TOP + 56, "Answer bank")
    pdf.setFont(FONT, 11)
    instruction = INSTRUCTION + (BLOCKED_NOTE if None in bank else "")
    for number, line in enumerate(simpleSplit(instruction, FONT, 11, CONTENT_WIDTH)):
        pdf.drawString(MARGIN, BANK_TOP + 40 - number * 13, line)

    for slot, answer in enumerate(bank):
        row, column = divmod(slot, SLOTS_PER_ROW)
        x = MARGIN + column * BOX_WIDTH
        y = BANK_TOP - (row + 1) * BOX_HEIGHT
        pdf.saveState()
        pdf.setFillColor(BLOCKED)
        pdf.rect(x, y, BOX_WIDTH, BOX_HEIGHT, stroke=1, fill=int(answer is None))
        pdf.restoreState()
        if answer is not None:
            pdf.setFont(FONT, TEXT_SIZE + 2)
            pdf.drawCentredString(x + BOX_WIDTH / 2, y + BOX_HEIGHT / 2 - 5, str(answer))
        pdf.setFont(BOLD_FONT, 12)
        # the letters sit above the top row of boxes and below the bottom row
        slot_letter_y = y + BOX_HEIGHT + 4 if row == 0 else y - 14
        pdf.drawCentredString(x + BOX_WIDTH / 2, slot_letter_y, ascii_uppercase[slot])


def _draw_pattern(pdf: Canvas, grid: Sequence[Sequence[int | None]]) -> None:
    """Draw the pattern at the right of the page, and its caption at the left."""
    left = PAGE_WIDTH - MARGIN - SLOTS_PER_ROW * PATTERN_TILE
    for row, tiles in enumerate(grid):
        for column, tile in enumerate(tiles):
            x = left + column * PATTERN_TILE
            _draw_tile(pdf, x, PATTERN_TOP - (row + 1) * PATTERN_TILE, PATTERN_TILE, tile)

    pdf.setFont(FONT, 12)
    for number, line in enumerate(simpleSplit(CAPTION, FONT, 12, left - MARGIN - 20)):
        pdf.drawString(MARGIN, PATTERN_TOP - 14 - number * 15, line)


def _draw_tile(pdf: Canvas, x: float, y: float, size: float, tile: int | None) -> None:
    """Draw a tile's back: a white square with its colored shape. ``x``, ``y`` is bottom left.

    No tile (``None``) is a shaded square.
    """
    pdf.saveState()
    pdf.setFillColor(BLOCKED if tile is None else white)
    pdf.rect(x, y, size, size, stroke=0, fill=1)
    if tile is not None:
        color, _, _ = TILES[tile]
        (start_x, start_y), *corners = tile_outline(tile)
        shape = pdf.beginPath()
        shape.moveTo(x + start_x * size, y + (1 - start_y) * size)
        for corner_x, corner_y in corners:
            shape.lineTo(x + corner_x * size, y + (1 - corner_y) * size)
        shape.close()
        pdf.setFillColor(COLORS[color])
        pdf.drawPath(shape, stroke=0, fill=1)
    pdf.setStrokeColor(gray)
    pdf.setLineWidth(0.5)
    pdf.rect(x, y, size, size, stroke=1, fill=0)
    pdf.restoreState()
