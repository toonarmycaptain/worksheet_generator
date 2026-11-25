"""
The self-check tiles case as drawn on a PDF worksheet: the answer bank, laid out as the case's
slots, and the pattern the tiles make on the back of the closed case.

Any worksheet can draw these, below its questions or on a page of their own. Which answer goes in
which slot, and the pattern itself, come from ``core.self_check_tiles``. Answers that are
pictures, such as graphs, are too big for the slots' boxes, so they're drawn lettered, two to a
row, as ``draw_picture_tiles_pages`` lays them out.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from string import ascii_uppercase

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
from core.written_numbers import Piece, Pieces
from render.pdf.page import (
    BOLD_FONT,
    CONTENT_WIDTH,
    FONT,
    FRACTION_ROOM,
    MARGIN,
    PAGE_WIDTH,
    TEXT_SIZE,
    Header,
    draw_pieces,
    pieces_width,
    stacked,
    start_page,
    wrap,
)

BANK_TOP = 400  # the default top edge of the answer bank's top row
BANK_HEADING_HEIGHT = 56  # from the bank's top edge up to its heading's baseline
BOX_WIDTH = CONTENT_WIDTH / SLOTS_PER_ROW
BOX_HEIGHT = 44  # minimum; boxes grow when an answer needs more lines than the smallest size fits
BOX_PADDING = 6  # inner padding around each answer
BANK_SIZES = (TEXT_SIZE + 2, 14, 12, 10, 9)  # the largest size at which every answer fits is used
PATTERN_DROP = 150  # from the bank's top edge to the pattern's, for boxes BOX_HEIGHT high
PATTERN_TILE = 40
PICTURES_PER_ROW = 2
PICTURE_LETTER_DROP = 8  # from a picture's letter's baseline down to the picture's top
PICTURE_ROW_GAP = 22  # from the bottom of a row of pictures down to the next row's letters
PATTERN_HEIGHT = 2 * PATTERN_TILE + 24  # the pattern, with room above it
CAPTION = "Close the case and flip it over. If every answer is right, the back looks like this."
INSTRUCTION = "Put each numbered tile in the slot whose letter matches the answer to its question."
BLOCKED_NOTE = " Shaded boxes are not used."
MISSING_NOTE = " Letters that aren't shown are not used."

# An answer in the bank: text, wrapped to fit its box, or pieces drawn on one line, each fraction
# stacked (see ``draw_pieces``)
type BankAnswer = str | Pieces

COLORS = {"yellow": HexColor("#f0be00"), "red": HexColor("#d9262c"), "blue": HexColor("#003cc8")}
BLOCKED = HexColor("#d9d9d9")  # fill for a slot that no question uses


def draw_tiles(
    pdf: Canvas, answers: Sequence[BankAnswer], slot_of: Sequence[int], top: float = BANK_TOP
) -> None:
    """
    Draw the answer bank with its top edge at ``top``, under its heading, and the pattern below.

    ``slot_of[i]`` is the slot of ``answers[i]``, as in ``core.self_check_tiles``, and unused
    slots are blocked out. The answers must be distinct. Answers can be long, such as numbers in
    word form, so all are drawn at the largest size at which every one fits, on as many lines as
    needed; at the smallest size, the boxes grow taller to fit, pushing the pattern down.
    """
    box_height = _draw_answer_bank(pdf, answer_bank(answers, slot_of), top)
    _draw_pattern(pdf, pattern(slot_of), top - PATTERN_DROP - 2 * (box_height - BOX_HEIGHT))


def draw_tiles_page(
    pdf: Canvas, header: Header, answers: Sequence[BankAnswer], slot_of: Sequence[int]
) -> None:
    """
    Start a new page with ``header`` and draw the answer bank and pattern on it, as
    ``draw_tiles`` does, with the bank's heading where the page's content starts.
    """
    pdf.showPage()
    draw_tiles(pdf, answers, slot_of, start_page(pdf, header) - BANK_HEADING_HEIGHT)


@dataclass(frozen=True)
class BankPicture:
    """
    An answer in the bank drawn as a picture, ``width`` by ``height``, by ``draw``, which takes
    the canvas and the picture's top-left corner.
    """

    width: float
    height: float
    draw: Callable[[Canvas, float, float], None]


def draw_picture_tiles_pages(
    pdf: Canvas, header: Header, pictures: Sequence[BankPicture], slot_of: Sequence[int]
) -> None:
    """
    Start a new page with ``header`` and draw the answer bank as pictures, each under its slot's
    letter, ``PICTURES_PER_ROW`` to a row in slot order, starting new pages as needed, then the
    pattern below them, or on a page of its own if it doesn't fit. ``slot_of[i]`` is the slot of
    ``pictures[i]``, as in ``core.self_check_tiles``; an unused slot's letter isn't shown.
    """
    pdf.showPage()
    top = start_page(pdf, header) - BANK_HEADING_HEIGHT
    bank = answer_bank(pictures, slot_of)
    _draw_bank_heading(pdf, top, MISSING_NOTE if None in bank else "")
    shown = [(slot, picture) for slot, picture in enumerate(bank) if picture is not None]
    baseline = top
    column_width = CONTENT_WIDTH / PICTURES_PER_ROW
    for start in range(0, len(shown), PICTURES_PER_ROW):
        row = shown[start : start + PICTURES_PER_ROW]
        height = PICTURE_LETTER_DROP + max(picture.height for _, picture in row)
        if baseline - height < MARGIN:
            pdf.showPage()
            baseline = start_page(pdf, header)
        for column, (slot, picture) in enumerate(row):
            left = MARGIN + column * column_width
            pdf.setFont(BOLD_FONT, 12)
            pdf.drawString(left, baseline, ascii_uppercase[slot])
            picture.draw(pdf, left, baseline - PICTURE_LETTER_DROP)
        baseline -= height + PICTURE_ROW_GAP
    if baseline - PATTERN_HEIGHT < MARGIN:
        pdf.showPage()
        baseline = start_page(pdf, header)
    _draw_pattern(pdf, pattern(slot_of), baseline)


def tile_solutions(questions: Sequence[TileQuestion], slot_of: Sequence[int]) -> list[str]:
    """Return each question's solution for the answer key, followed by its answer's slot letter."""
    return [
        f"{question.solution}    ({ascii_uppercase[slot]})"
        for question, slot in zip(questions, slot_of, strict=True)
    ]


def _bank_lines(
    answers: Sequence[BankAnswer],
) -> tuple[int, dict[BankAnswer, list[BankAnswer]], float]:
    """
    Return the font size for every answer, each answer's lines, and the box height. Text is
    wrapped as ``wrap`` does, and pieces after a comma.

    The size is the largest of ``BANK_SIZES`` at which every answer fits within its box's
    padding at ``BOX_HEIGHT``. If none does, the smallest size is used and the boxes grow to fit
    the tallest answer. A line with a stacked fraction is taller, as ``_line_height`` says.
    """
    width = BOX_WIDTH - 2 * BOX_PADDING
    for size in BANK_SIZES:
        lines: dict[BankAnswer, list[BankAnswer]] = {
            answer: list(wrap(answer, size, width))
            if isinstance(answer, str)
            else list(_wrap_pieces(answer, size, width))
            for answer in answers
        }
        widest = max(_width(line, size) for each in lines.values() for line in each)
        tallest = max(sum(_line_height(line, size) for line in each) for each in lines.values())
        if widest <= width and tallest <= BOX_HEIGHT - 2 * BOX_PADDING:
            return size, lines, BOX_HEIGHT
    return size, lines, max(BOX_HEIGHT, tallest + 2 * BOX_PADDING)


def _line_height(line: BankAnswer, size: float) -> float:
    """
    Return the height of a line of an answer in the bank: the size and a gap of 2, with room
    above and below for a stacked fraction, in proportion to ``FRACTION_ROOM`` at ``TEXT_SIZE``.
    """
    if isinstance(line, str) or not any(stacked(piece) for piece in line):
        return size + 2
    return size + 2 + 2 * FRACTION_ROOM * size / TEXT_SIZE


def _wrap_pieces(pieces: Pieces, size: float, width: float) -> list[Pieces]:
    """
    Split ``pieces`` after each comma into lines no wider than ``width``, as far as those breaks
    allow: "m = -3/4, b = 2" can become "m = -3/4," over "b = 2".
    """
    segments: list[list[Piece]] = [[]]
    for piece in pieces:
        if isinstance(piece, str) and ", " in piece:
            first, *rest = piece.split(", ")
            segments[-1].append(f"{first},")
            segments += [[part] for part in rest]
        else:
            segments[-1].append(piece)
    lines: list[list[Piece]] = []
    for segment in segments:
        if lines and pieces_width([*lines[-1], " ", *segment], size) <= width:
            lines[-1] += [" ", *segment]
        else:
            lines.append(segment)
    return [tuple(line) for line in lines]


def _width(line: BankAnswer, size: float) -> float:
    """Return the width of a line of an answer in the bank: text, or pieces."""
    return stringWidth(line, FONT, size) if isinstance(line, str) else pieces_width(line, size)


def _draw_answer_bank(pdf: Canvas, bank: Sequence[BankAnswer | None], top: float) -> float:
    """
    Draw the answer bank as the case's slots: two rows of boxes, lettered along the outer edges.

    A slot with no answer is drawn as a shaded, empty box. Returns the box height.
    """
    size, lines_of, height = _bank_lines([answer for answer in bank if answer is not None])
    _draw_bank_heading(pdf, top, BLOCKED_NOTE if None in bank else "")

    for slot, answer in enumerate(bank):
        row, column = divmod(slot, SLOTS_PER_ROW)
        x = MARGIN + column * BOX_WIDTH
        y = top - (row + 1) * height
        pdf.saveState()
        pdf.setFillColor(BLOCKED)
        pdf.rect(x, y, BOX_WIDTH, height, stroke=1, fill=int(answer is None))
        pdf.restoreState()
        if answer is not None:
            lines = lines_of[answer]
            pdf.setFont(FONT, size)
            # centre the block of lines vertically in the box, each line in the middle of its
            # own height
            heights = [_line_height(line, size) for line in lines]
            baseline = y + height / 2 + (sum(heights) - heights[0]) / 2 - size * 5 / 16
            for number, line in enumerate(lines):
                if isinstance(line, str):
                    pdf.drawCentredString(x + BOX_WIDTH / 2, baseline, line)
                else:
                    left = x + (BOX_WIDTH - pieces_width(line, size)) / 2
                    draw_pieces(pdf, left, baseline, line, size)
                if number + 1 < len(lines):
                    baseline -= (heights[number] + heights[number + 1]) / 2
        pdf.setFont(BOLD_FONT, 12)
        # slot letters go above the top row and below the bottom row
        slot_letter_y = y + height + 4 if row == 0 else y - 14
        pdf.drawCentredString(x + BOX_WIDTH / 2, slot_letter_y, ascii_uppercase[slot])
    return height


def _draw_bank_heading(pdf: Canvas, top: float, note: str) -> None:
    """
    Draw the answer bank's heading and instruction, with ``note`` after it, above the bank's top
    edge at ``top``.
    """
    pdf.setFont(BOLD_FONT, TEXT_SIZE)
    pdf.drawString(MARGIN, top + BANK_HEADING_HEIGHT, "Answer bank")
    pdf.setFont(FONT, 11)
    for number, line in enumerate(simpleSplit(INSTRUCTION + note, FONT, 11, CONTENT_WIDTH)):
        pdf.drawString(MARGIN, top + 40 - number * 13, line)


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
