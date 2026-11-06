"""PDF worksheets for the self-check tiles case, with an optional answer key page."""

from collections.abc import Sequence
from string import ascii_uppercase
from typing import BinaryIO

from reportlab.lib.colors import HexColor, gray, white
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.self_check_tiles import (
    SLOTS_PER_ROW,
    TILES,
    TileQuestion,
    answer_bank,
    pattern,
    tile_outline,
)
from render.pdf.page import (
    BOLD_FONT,
    FONT,
    MARGIN,
    PAGE_WIDTH,
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

CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
COLUMN_GAP = 12  # between the left column's questions and the right column's numbers
QUESTION_WIDTH = CONTENT_WIDTH / 2 - TEXT_INDENT - COLUMN_GAP  # available to each question
SMALLER_SIZES = (12, 10)  # for a question too long for one line at TEXT_SIZE
QUESTION_ROW = 34
QUESTIONS_PER_COLUMN = 6
BANK_TOP = 400  # the top edge of the answer bank's top row
BOX_WIDTH = CONTENT_WIDTH / SLOTS_PER_ROW
BOX_HEIGHT = 44  # minimum; boxes grow when an answer needs more lines than the smallest size fits
BOX_PADDING = 6  # inner padding around each answer
BANK_SIZES = (TEXT_SIZE + 2, 14, 12, 10, 9)  # the largest size at which every answer fits is used
PATTERN_TOP = 250  # for boxes BOX_HEIGHT high; taller boxes push it down
PATTERN_TILE = 40
CAPTION = "Close the case and flip it over. If every answer is right, the back looks like this."
INSTRUCTION = "Put each numbered tile in the slot whose letter matches the answer to its question."
BLOCKED_NOTE = " Shaded boxes are not used."

COLORS = {"yellow": HexColor("#f0be00"), "red": HexColor("#d9262c"), "blue": HexColor("#003cc8")}
BLOCKED = HexColor("#d9d9d9")  # fill for a slot that no question uses


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
    be distinct. Answers can be long, such as numbers in word form, so all are drawn at the
    largest size at which every one fits, on as many lines as needed; at the smallest size, the
    boxes grow taller to fit. A question too long for one line of its column is drawn smaller,
    on up to two lines. ``path`` is a filename or a binary file-like object.
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
    bank = answer_bank([question.answer for question in questions], slot_of)
    box_height = _draw_answer_bank(pdf, bank)
    _draw_pattern(pdf, pattern(slot_of), PATTERN_TOP - 2 * (box_height - BOX_HEIGHT))

    if answer_key:
        solutions = [
            f"{question.solution}    ({ascii_uppercase[slot]})"
            for question, slot in zip(questions, slot_of, strict=True)
        ]
        draw_answer_key(pdf, header, solutions)

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


def _bank_lines(answers: Sequence[str]) -> tuple[int, dict[str, list[str]], float]:
    """
    Return the font size for every answer, each answer's lines, and the box height.

    The size is the largest of ``BANK_SIZES`` at which every answer fits within its box's
    padding at ``BOX_HEIGHT``. If none does, the smallest size is used and the boxes grow to fit
    the answer with the most lines.
    """
    width = BOX_WIDTH - 2 * BOX_PADDING
    for size in BANK_SIZES:
        lines = {answer: wrap(answer, size, width) for answer in answers}
        widest = max(stringWidth(line, FONT, size) for each in lines.values() for line in each)
        most_lines = max(len(each) for each in lines.values())
        if widest <= width and most_lines * (size + 2) <= BOX_HEIGHT - 2 * BOX_PADDING:
            return size, lines, BOX_HEIGHT
    return size, lines, max(BOX_HEIGHT, most_lines * (size + 2) + 2 * BOX_PADDING)


def _draw_answer_bank(pdf: Canvas, bank: Sequence[str | None]) -> float:
    """
    Draw the answer bank as the case's slots: two rows of boxes, lettered along the outer edges.

    A slot with no answer is drawn as a shaded, empty box. Returns the box height.
    """
    size, lines_of, height = _bank_lines([answer for answer in bank if answer is not None])
    pdf.setFont(BOLD_FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, BANK_TOP + 56, "Answer bank")
    pdf.setFont(FONT, 11)
    instruction = INSTRUCTION + (BLOCKED_NOTE if None in bank else "")
    for number, line in enumerate(simpleSplit(instruction, FONT, 11, CONTENT_WIDTH)):
        pdf.drawString(MARGIN, BANK_TOP + 40 - number * 13, line)

    for slot, answer in enumerate(bank):
        row, column = divmod(slot, SLOTS_PER_ROW)
        x = MARGIN + column * BOX_WIDTH
        y = BANK_TOP - (row + 1) * height
        pdf.saveState()
        pdf.setFillColor(BLOCKED)
        pdf.rect(x, y, BOX_WIDTH, height, stroke=1, fill=int(answer is None))
        pdf.restoreState()
        if answer is not None:
            lines = lines_of[answer]
            pdf.setFont(FONT, size)
            # centre the block of lines vertically in the box
            baseline = y + height / 2 + (len(lines) - 1) * (size + 2) / 2 - size * 5 / 16
            for line in lines:
                pdf.drawCentredString(x + BOX_WIDTH / 2, baseline, line)
                baseline -= size + 2
        pdf.setFont(BOLD_FONT, 12)
        # slot letters go above the top row and below the bottom row
        slot_letter_y = y + height + 4 if row == 0 else y - 14
        pdf.drawCentredString(x + BOX_WIDTH / 2, slot_letter_y, ascii_uppercase[slot])
    return height


def _draw_pattern(pdf: Canvas, grid: Sequence[Sequence[int | None]], top: float) -> None:
    """Draw the pattern at the right of the page from ``top`` down, with its caption at the left."""
    left = PAGE_WIDTH - MARGIN - SLOTS_PER_ROW * PATTERN_TILE
    for row, tiles in enumerate(grid):
        for column, tile in enumerate(tiles):
            x = left + column * PATTERN_TILE
            _draw_tile(pdf, x, top - (row + 1) * PATTERN_TILE, PATTERN_TILE, tile)

    pdf.setFont(FONT, 12)
    for number, line in enumerate(simpleSplit(CAPTION, FONT, 12, left - MARGIN - 20)):
        pdf.drawString(MARGIN, top - 14 - number * 15, line)


def _draw_tile(pdf: Canvas, x: float, y: float, size: float, tile: int | None) -> None:
    """
    Draw a tile's back, a white square with its colored shape, with its bottom-left at ``x, y``.

    ``None`` (no tile) is drawn as a shaded square.
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
