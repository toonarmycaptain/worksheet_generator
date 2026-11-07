"""
Diagrams drawn with word problems, as plain functions over a canvas.

Each drawer takes a diagram description from the core and the position of its top-left corner.
Its colours and sizes are module constants, so a worksheet can measure a diagram before drawing
it.
"""

from collections.abc import Mapping, Sequence
from itertools import pairwise
from math import ceil, hypot

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.data import Operation
from core.basic_operations.representation import (
    SYMBOLS,
    BlocksDiagram,
    EqualStripDiagram,
    StripDiagram,
    StripUnknown,
)
from core.placevalue.representation import BLOCK_NAMES, BaseTenBlocks
from render.pdf.page import BOLD_FONT, FONT, ITALIC_FONT, TEXT_INDENT, TEXT_WIDTH

UNKNOWN_LABEL = "?"

STRIP_WIDTH = 360
STRIP_HEIGHT = 54  # from the top of the whole's label to the bottom of the bar
STRIP_BAR_HEIGHT = 34
# Each part's share of the bar's width is kept within these, so that a small part still has
# room for its number.
SMALLEST_SPLIT = 0.32
LARGEST_SPLIT = 0.68
KNOWN_FILL = HexColor("#cfe3f7")  # light blue
UNKNOWN_FILL = HexColor("#fef3c7")  # light yellow
BRACKET_COLOUR = HexColor("#718096")
OUTLINE_COLOUR = HexColor("#2d3748")

NUMBER_LINE_WIDTH = TEXT_WIDTH
NUMBER_LINE_HEIGHT = 74  # from the top of the jump labels to the bottom of the answer caption
NUMBER_LINE_DROP = 38  # from the top down to the line
LINE_OVERHANG = 8  # the line runs this far past the end ticks, then ends in an arrowhead
LINE_ARROW_LENGTH = 7
TICK_HALF_HEIGHT = 4
JUMP_HEIGHT = 26  # how far above the line each jump's arc is pulled
JUMP_ARROWHEAD_LENGTH = 8
JUMP_ARROWHEAD_WIDTH = 7
JUMP_COLOUR = HexColor("#2b6cb0")  # blue
LANDING_BOX_WIDTH = 44
LANDING_BOX_HEIGHT = 18
LANDING_BOX_DROP = 9  # from the line down to the top of the boxes
LANDING_BOX_COLOUR = HexColor("#4a5568")  # dark grey
ANSWER_CAPTION = "answer"
CAPTION_COLOUR = HexColor("#718096")  # grey

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


def draw_strip(pdf: Canvas, x: float, top: float, strip: StripDiagram) -> None:
    """
    Draw ``strip`` with its top-left corner at (``x``, ``top``), ``STRIP_HEIGHT`` high.

    The whole is labelled above a bracket spanning the bar, and the bar is split into the two
    parts in proportion to their values, within ``SMALLEST_SPLIT`` and ``LARGEST_SPLIT``. The
    unknown value is shown as "?", and an unknown part is filled with ``UNKNOWN_FILL``.
    """
    left, right = strip.parts
    split_x = x + STRIP_WIDTH * min(max(left / strip.whole, SMALLEST_SPLIT), LARGEST_SPLIT)
    end_x = x + STRIP_WIDTH
    whole_label = UNKNOWN_LABEL if strip.unknown is StripUnknown.WHOLE else str(strip.whole)
    right_label = UNKNOWN_LABEL if strip.unknown is StripUnknown.RIGHT else str(right)
    pdf.saveState()
    _draw_whole(pdf, x, top, whole_label)

    # the two parts, side by side
    bottom = top - STRIP_HEIGHT
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(KNOWN_FILL)
    pdf.rect(x, bottom, split_x - x, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor(UNKNOWN_FILL if strip.unknown is StripUnknown.RIGHT else KNOWN_FILL)
    pdf.rect(split_x, bottom, end_x - split_x, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 12)
    label_y = bottom + STRIP_BAR_HEIGHT / 2 - 4
    pdf.drawCentredString((x + split_x) / 2, label_y, str(left))
    pdf.drawCentredString((split_x + end_x) / 2, label_y, right_label)

    pdf.restoreState()


def draw_equal_strip(pdf: Canvas, x: float, top: float, strip: EqualStripDiagram) -> None:
    """
    Draw ``strip`` with its top-left corner at (``x``, ``top``), ``STRIP_HEIGHT`` high.

    The whole is labelled above a bracket spanning the bar, as in ``draw_strip``, and the bar is
    split into ``strip.groups`` equal parts, each labelled with the size. An unknown whole is
    shown as "?". An unknown size is shown as "?" in every part, and every part is filled with
    ``UNKNOWN_FILL``.
    """
    whole_label = UNKNOWN_LABEL if strip.unknown is StripUnknown.WHOLE else str(strip.whole)
    size_unknown = strip.unknown is StripUnknown.SIZE
    part_label = UNKNOWN_LABEL if size_unknown else str(strip.size)
    part_width = STRIP_WIDTH / strip.groups
    pdf.saveState()
    _draw_whole(pdf, x, top, whole_label)

    # the equal parts, side by side
    bottom = top - STRIP_HEIGHT
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(UNKNOWN_FILL if size_unknown else KNOWN_FILL)
    for index in range(strip.groups):
        pdf.rect(x + index * part_width, bottom, part_width, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 12)
    label_y = bottom + STRIP_BAR_HEIGHT / 2 - 4
    for index in range(strip.groups):
        pdf.drawCentredString(x + (index + 0.5) * part_width, label_y, part_label)

    pdf.restoreState()


def _draw_whole(pdf: Canvas, x: float, top: float, label: str) -> None:
    """Draw a strip's whole, labelled ``label``, above a bracket as wide as the strip."""
    end_x = x + STRIP_WIDTH
    bracket_y = top - 12
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 11)
    pdf.drawCentredString(x + STRIP_WIDTH / 2, top - 8, f"whole: {label}")
    pdf.setStrokeColor(BRACKET_COLOUR)
    pdf.setLineWidth(1)
    pdf.line(x, bracket_y, end_x, bracket_y)
    pdf.line(x, bracket_y, x, bracket_y - 4)
    pdf.line(end_x, bracket_y, end_x, bracket_y - 4)


def draw_number_line(pdf: Canvas, x: float, top: float, start: int, jumps: Sequence[int]) -> None:
    """
    Draw an open number line from ``start``, with ``jumps`` as labelled arcs, with its top-left
    corner at (``x``, ``top``), ``NUMBER_LINE_WIDTH`` wide and ``NUMBER_LINE_HEIGHT`` high.

    The ticks are evenly spaced, not to scale: one for the start, labelled with it, and one for
    each jump's landing, with an empty box under it to write the number in. The last box is
    captioned "answer". Positive jumps go right from the leftmost tick, and negative jumps go
    left from the rightmost tick.
    """
    line_y = top - NUMBER_LINE_DROP
    first_tick = x + LINE_ARROW_LENGTH + LINE_OVERHANG
    step = (NUMBER_LINE_WIDTH - 2 * (LINE_ARROW_LENGTH + LINE_OVERHANG)) / len(jumps)
    ticks = [first_tick + index * step for index in range(len(jumps) + 1)]
    if jumps[0] < 0:
        ticks.reverse()  # start at the right, and jump left
    pdf.saveState()

    # the line, with an arrowhead at each end, and the ticks
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setFillColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.line(x + LINE_ARROW_LENGTH, line_y, x + NUMBER_LINE_WIDTH - LINE_ARROW_LENGTH, line_y)
    for tip, back in ((x, LINE_ARROW_LENGTH), (x + NUMBER_LINE_WIDTH, -LINE_ARROW_LENGTH)):
        arrowhead = pdf.beginPath()
        arrowhead.moveTo(tip, line_y)
        arrowhead.lineTo(tip + back, line_y + 4)
        arrowhead.lineTo(tip + back, line_y - 4)
        arrowhead.close()
        pdf.drawPath(arrowhead, stroke=0, fill=1)
    for tick in ticks:
        pdf.line(tick, line_y - TICK_HALF_HEIGHT, tick, line_y + TICK_HALF_HEIGHT)

    # the start under its tick, and a box under each landing
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 11)
    pdf.drawCentredString(ticks[0], line_y - 17, str(start))
    pdf.setStrokeColor(LANDING_BOX_COLOUR)
    pdf.setLineWidth(1)
    box_bottom = line_y - LANDING_BOX_DROP - LANDING_BOX_HEIGHT
    for tick in ticks[1:]:
        pdf.roundRect(
            tick - LANDING_BOX_WIDTH / 2,
            box_bottom,
            LANDING_BOX_WIDTH,
            LANDING_BOX_HEIGHT,
            3,
            stroke=1,
            fill=0,
        )
    pdf.setFont(ITALIC_FONT, 8)
    pdf.setFillColor(CAPTION_COLOUR)
    pdf.drawCentredString(ticks[-1], box_bottom - 9, ANSWER_CAPTION)

    # each jump: an arc from tick to tick, an arrowhead pointing the way it goes, and its label
    pdf.setStrokeColor(JUMP_COLOUR)
    pdf.setFillColor(JUMP_COLOUR)
    pdf.setLineWidth(1.3)
    pdf.setFont(BOLD_FONT, 10)
    for jump, (start_x, end_x) in zip(jumps, pairwise(ticks), strict=True):
        quarter = (end_x - start_x) / 4
        pull_y = line_y + JUMP_HEIGHT
        # The arc ends travelling from its last control point towards the tick, so the arrowhead
        # points that way, with its tip on the line. The arc stops at the arrowhead's base, so
        # its end doesn't show beside the tip.
        length = hypot(quarter, JUMP_HEIGHT)
        along_x, along_y = quarter / length, -JUMP_HEIGHT / length
        base_x = end_x - JUMP_ARROWHEAD_LENGTH * along_x
        base_y = line_y - JUMP_ARROWHEAD_LENGTH * along_y
        arc = pdf.beginPath()
        arc.moveTo(start_x, line_y)
        arc.curveTo(start_x + quarter, pull_y, end_x - quarter, pull_y, base_x, base_y)
        pdf.drawPath(arc, stroke=1, fill=0)
        half_width = JUMP_ARROWHEAD_WIDTH / 2
        arrowhead = pdf.beginPath()
        arrowhead.moveTo(end_x, line_y)
        arrowhead.lineTo(base_x - half_width * along_y, base_y + half_width * along_x)
        arrowhead.lineTo(base_x + half_width * along_y, base_y - half_width * along_x)
        arrowhead.close()
        pdf.drawPath(arrowhead, stroke=0, fill=1)
        sign = SYMBOLS[Operation.ADD if jump > 0 else Operation.SUBTRACT]
        pdf.drawCentredString((start_x + end_x) / 2, line_y + 29, f"{sign} {abs(jump)}")

    pdf.restoreState()


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
