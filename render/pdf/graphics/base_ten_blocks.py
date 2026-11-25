"""
Base-ten blocks: numbers drawn as flats, rods and units, and the key to them.
"""

from collections.abc import Mapping
from math import ceil

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import BLOCK_NAMES, BaseTenBlocks, BlocksDiagram
from core.basic_operations.data import Operation
from core.basic_operations.representation import (
    SYMBOLS,
)
from render.pdf.graphics.common import OUTLINE_COLOUR
from render.pdf.page import BOLD_FONT, FONT, TEXT_INDENT

BLOCK_UNIT = 5.5  # a unit's edge: a rod is 1 by 10 units, and a flat 10 by 10
FLAT_SIZE = 10 * BLOCK_UNIT
BLOCK_GAP = BLOCK_UNIT * 0.5  # between two blocks
BLOCK_GROUP_GAP = BLOCK_UNIT * 2.2  # between a number's flats, rods and units
FLATS_PER_ROW = 5
UNITS_PER_ROW = 5
BLOCKS_NUMBER_GAP = 14  # between two numbers, one under the other
BLOCKS_SIGN_SIZE = 18
BLOCKS_SIGN_INSET = 2  # from the problem number's column's left edge to the sign
BLOCKS_NOTE = "(cross out {})"
BLOCKS_NOTE_GAP = 12  # from the last block to the note
BLOCKS_NOTE_COLOUR = HexColor("#4a5568")  # dark grey
BLOCKS_KEY_LABEL = "Key:"
BLOCKS_KEY_SIZE = 10
BLOCKS_KEY_INDENT = 30  # from the key's left edge to its first block
BLOCKS_KEY_SPACING = 50  # from one block's right edge to the next
BLOCKS_KEY_NAME_DROP = 11  # from the blocks' bottoms down to their names' baseline
BLOCKS_KEY_HEIGHT = FLAT_SIZE + BLOCKS_KEY_NAME_DROP + 3  # down to the bottom of the names

# Each block's fill and outline colours, keyed by its value
BlockColours = Mapping[int, tuple[Color, Color]]
COLOUR_BLOCKS: BlockColours = {
    100: (HexColor("#cfe3f7"), HexColor("#2b6cb0")),  # blue flats
    10: (HexColor("#d6efd6"), HexColor("#2f855a")),  # green rods
    1: (HexColor("#fde3c8"), HexColor("#c05621")),  # orange units
}
GREY_BLOCKS: BlockColours = {  # black and white, for photocopying
    100: (HexColor("#e8e8e8"), HexColor("#444444")),
    10: (HexColor("#f0f0f0"), HexColor("#444444")),
    1: (HexColor("#ffffff"), HexColor("#444444")),
}


def blocks_height(diagram: BlocksDiagram) -> float:
    """Return how high ``draw_blocks`` draws ``diagram``."""
    heights = [_number_height(blocks) for blocks in diagram.numbers]
    return sum(heights) + (len(heights) - 1) * BLOCKS_NUMBER_GAP


def draw_blocks(
    pdf: Canvas,
    x: float,
    top: float,
    diagram: BlocksDiagram,
    colours: BlockColours,
    note: bool,
) -> float:
    """
    Draw ``diagram``'s numbers as base-ten blocks in ``colours``, one under another, with the
    top-left corner at (``x``, ``top``), ``blocks_height(diagram)`` high, and return the x of
    the right edge of the last number's blocks.

    When some are crossed out, there is no sign, because the one number drawn is the starting
    amount, not the amount taken away; with ``note``, the amount to cross out is written right of
    it, "(cross out 25)". Otherwise, when there are two numbers, a plus sign sits beside the
    second, in the problem number's column left of ``x``. A single number has no sign.
    """
    pdf.saveState()
    bottom = top + BLOCKS_NUMBER_GAP
    for blocks in diagram.numbers:
        height = _number_height(blocks)
        bottom -= BLOCKS_NUMBER_GAP + height
        right = _draw_number(pdf, x, bottom, blocks, colours)

    middle = bottom + height / 2
    if diagram.cross_out is not None:
        if note:
            pdf.setFillColor(BLOCKS_NOTE_COLOUR)
            pdf.setFont(FONT, 12)
            note_text = BLOCKS_NOTE.format(diagram.cross_out)
            pdf.drawString(right + BLOCKS_NOTE_GAP, middle - 4, note_text)
    elif len(diagram.numbers) > 1:
        pdf.setFillColor(OUTLINE_COLOUR)
        pdf.setFont(BOLD_FONT, BLOCKS_SIGN_SIZE)
        pdf.drawString(x - TEXT_INDENT + BLOCKS_SIGN_INSET, middle - 6, SYMBOLS[Operation.ADD])

    pdf.restoreState()
    return right


def draw_blocks_key(pdf: Canvas, x: float, top: float, colours: BlockColours) -> None:
    """
    Draw the key to the base-ten blocks in ``colours``, with its top-left corner at (``x``,
    ``top``), ``BLOCKS_KEY_HEIGHT`` high: "Key:", then each block with its name and value under
    it, "flat = 100".
    """
    bottom = top - FLAT_SIZE
    pdf.saveState()
    pdf.setFillColor("black")
    pdf.setFont(FONT, BLOCKS_KEY_SIZE)
    pdf.drawString(x, bottom + FLAT_SIZE / 2 - 3, BLOCKS_KEY_LABEL)
    block_x = x + BLOCKS_KEY_INDENT
    for value, name in BLOCK_NAMES.items():
        width = _draw_block(pdf, block_x, bottom, value, colours)
        pdf.setFillColor("black")
        pdf.setFont(FONT, BLOCKS_KEY_SIZE)
        label = f"{name} = {value}"
        pdf.drawCentredString(block_x + width / 2, bottom - BLOCKS_KEY_NAME_DROP, label)
        block_x += width + BLOCKS_KEY_SPACING
    pdf.restoreState()


def _number_height(blocks: BaseTenBlocks) -> float:
    """
    Return how high ``_draw_number`` draws ``blocks``: a rod's height for each row of flats, or
    one rod's height for rods, or else the height of the rows of units.
    """
    if blocks.hundreds or blocks.tens:
        rows = max(ceil(blocks.hundreds / FLATS_PER_ROW), 1)
        size = FLAT_SIZE
    else:
        rows = ceil(blocks.ones / UNITS_PER_ROW)
        size = BLOCK_UNIT
    return rows * size + (rows - 1) * BLOCK_GAP


def _draw_number(
    pdf: Canvas, x: float, bottom: float, blocks: BaseTenBlocks, colours: BlockColours
) -> float:
    """
    Draw ``blocks`` from (``x``, ``bottom``), and return the x of their right edge.

    The flats come first, in rows of ``FLATS_PER_ROW`` from the bottom up, then the rods side by
    side, then the units in rows of ``UNITS_PER_ROW`` from the bottom up.
    """
    right = x - BLOCK_GROUP_GAP
    for value, count, per_row in (
        (100, blocks.hundreds, FLATS_PER_ROW),
        (10, blocks.tens, blocks.tens),  # the rods in one row
        (1, blocks.ones, UNITS_PER_ROW),
    ):
        if not count:
            continue
        left = right + BLOCK_GROUP_GAP
        width, height = _block_size(value)
        for index in range(count):
            row, column = divmod(index, per_row)
            block_x = left + column * (width + BLOCK_GAP)
            _draw_block(pdf, block_x, bottom + row * (height + BLOCK_GAP), value, colours)
        right = left + min(count, per_row) * (width + BLOCK_GAP) - BLOCK_GAP
    return right


def _block_size(value: int) -> tuple[float, float]:
    """Return the width and height of the block worth ``value``: 100, 10 or 1."""
    return (FLAT_SIZE if value == 100 else BLOCK_UNIT, BLOCK_UNIT if value == 1 else FLAT_SIZE)


def _draw_block(pdf: Canvas, x: float, y: float, value: int, colours: BlockColours) -> float:
    """
    Draw the block worth ``value`` (100, 10 or 1) with its bottom-left corner at (``x``, ``y``),
    marked into units by thin lines, and return its width.
    """
    width, height = _block_size(value)
    fill, outline = colours[value]
    pdf.setFillColor(fill)
    pdf.setStrokeColor(outline)
    pdf.setLineWidth(1)
    pdf.rect(x, y, width, height, stroke=1, fill=1)
    pdf.setLineWidth(0.4)
    for index in range(1, round(width / BLOCK_UNIT)):
        pdf.line(x + index * BLOCK_UNIT, y, x + index * BLOCK_UNIT, y + height)
    for index in range(1, round(height / BLOCK_UNIT)):
        pdf.line(x, y + index * BLOCK_UNIT, x + width, y + index * BLOCK_UNIT)
    return width
