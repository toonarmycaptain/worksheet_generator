"""
Diagrams drawn with word problems, as plain functions over a canvas.

Each drawer takes a diagram description from the core and the position of its top-left corner.
Its colours and sizes are module constants, so a worksheet can measure a diagram before drawing
it.
"""

from collections.abc import Mapping, Sequence
from itertools import pairwise
from math import ceil, hypot
from typing import assert_never

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.base_ten_blocks import BLOCK_NAMES, BaseTenBlocks, BlocksDiagram
from core.basic_operations.data import Operation
from core.basic_operations.multiplication_models import Array, EqualJumpLine
from core.basic_operations.representation import (
    SYMBOLS,
    EqualStripDiagram,
    StripDiagram,
    TwoJumpLine,
    TwoStepStripDiagram,
)
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
PART_LABEL_SIZE = 12  # a part's number, unless the part is too narrow for it
PART_LABEL_PADDING = 4  # the least room left beside a narrow part's number
# A two-step strip's whole is in a box over its bar, where a strip's whole label and bracket are.
WHOLE_BOX_HEIGHT = STRIP_HEIGHT - STRIP_BAR_HEIGHT
TWO_STEP_PART_WIDTH = 24  # the least width of a two-step strip's part, while there's room

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
# A number line to choose from: two jumps from 0, with its three ticks labelled
TWO_JUMP_LINE_HEIGHT = 55  # from the top of the higher jump's label to the bottom of the numbers
TWO_JUMP_LINE_DROP = 40  # from the top down to the line
# How far above the line a jump's arc is pulled, for a jump to the next tick, and for one past it.
# A jump past the next tick arcs over the other jump, whose label stays under it.
SHORT_JUMP_HEIGHT = 10
LONG_JUMP_HEIGHT = 40
TWO_JUMP_LABEL_SIZE = 9  # the jumps' labels and the ticks' numbers
TWO_JUMP_LABEL_RAISE = 3  # from the top of a jump's arc up to its label's baseline
TWO_JUMP_NUMBER_DROP = 13  # from the line down to the ticks' numbers' baseline
# A number line of equal jumps from 0, numbered as the two-jump line's are
EQUAL_JUMP_LINE_HEIGHT = 42  # from the top of the jumps' numbers to the bottom of the ticks'
EQUAL_JUMP_LINE_DROP = 26  # from the top down to the line
# How far above the line each jump's arc is pulled: a little more for a longer jump, up to a most
EQUAL_JUMP_PULL = 8
EQUAL_JUMP_PULL_PER_POINT = 0.09  # of the jump's length
EQUAL_JUMP_MOST_PULL = 16

ARRAY_DOT_SPACING = 13  # the most from one dot's centre to the next
ARRAY_DOT_RADIUS = 0.36  # each dot's radius, as a share of the spacing
ARRAY_DOT_COLOUR = HexColor("#2b6cb0")  # blue

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


def draw_strip_diagram(
    pdf: Canvas,
    x: float,
    top: float,
    diagram: StripDiagram | EqualStripDiagram | TwoStepStripDiagram,
    width: float = STRIP_WIDTH,
) -> None:
    """
    Draw ``diagram`` with ``draw_strip``, ``draw_equal_strip`` or ``draw_two_step_strip``,
    whichever kind it is. Each is ``STRIP_HEIGHT`` high, with its bar at the bottom.
    """
    match diagram:
        case StripDiagram():
            draw_strip(pdf, x, top, diagram, width)
        case EqualStripDiagram():
            draw_equal_strip(pdf, x, top, diagram, width)
        case TwoStepStripDiagram():
            draw_two_step_strip(pdf, x, top, diagram, width)
        case _:
            assert_never(diagram)


def draw_strip(
    pdf: Canvas, x: float, top: float, strip: StripDiagram, width: float = STRIP_WIDTH
) -> None:
    """
    Draw ``strip`` with its top-left corner at (``x``, ``top``), ``width`` wide and
    ``STRIP_HEIGHT`` high.

    The whole is labelled above a bracket spanning the bar, and the bar is split into the two
    parts in proportion to their values, within ``SMALLEST_SPLIT`` and ``LARGEST_SPLIT``. The
    unknown value is shown as "?", and an unknown part is filled with ``UNKNOWN_FILL``.
    """
    left, right = strip.parts
    # An unknown whole is the parts' total.
    whole = left + (right or 0) if strip.whole is None else strip.whole
    split_x = x + width * min(max(left / whole, SMALLEST_SPLIT), LARGEST_SPLIT)
    end_x = x + width
    pdf.saveState()
    _draw_whole(pdf, x, top, _label(strip.whole), width)

    # the two parts, side by side
    bottom = top - STRIP_HEIGHT
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(KNOWN_FILL)
    pdf.rect(x, bottom, split_x - x, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor(UNKNOWN_FILL if right is None else KNOWN_FILL)
    pdf.rect(split_x, bottom, end_x - split_x, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, PART_LABEL_SIZE)
    label_y = bottom + STRIP_BAR_HEIGHT / 2 - PART_LABEL_SIZE / 3
    pdf.drawCentredString((x + split_x) / 2, label_y, str(left))
    pdf.drawCentredString((split_x + end_x) / 2, label_y, _label(right))

    pdf.restoreState()


def draw_equal_strip(
    pdf: Canvas, x: float, top: float, strip: EqualStripDiagram, width: float = STRIP_WIDTH
) -> None:
    """
    Draw ``strip`` with its top-left corner at (``x``, ``top``), ``width`` wide and
    ``STRIP_HEIGHT`` high.

    The whole is labelled above a bracket spanning the bar, as in ``draw_strip``, and the bar is
    split into ``strip.groups`` equal parts, each labelled with the size, smaller than
    ``PART_LABEL_SIZE`` if a part is too narrow for it. An unknown whole is shown as "?". An
    unknown size is shown as "?" in every part, and every part is filled with ``UNKNOWN_FILL``.
    """
    part_label = _label(strip.size)
    part_width = width / strip.groups
    pdf.saveState()
    _draw_whole(pdf, x, top, _label(strip.whole), width)

    # the equal parts, side by side
    bottom = top - STRIP_HEIGHT
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(UNKNOWN_FILL if strip.size is None else KNOWN_FILL)
    for index in range(strip.groups):
        pdf.rect(x + index * part_width, bottom, part_width, STRIP_BAR_HEIGHT, stroke=1, fill=1)
    pdf.setFillColor("black")
    size = _label_size(part_label, part_width)
    pdf.setFont(BOLD_FONT, size)
    label_y = bottom + STRIP_BAR_HEIGHT / 2 - size / 3
    for index in range(strip.groups):
        pdf.drawCentredString(x + (index + 0.5) * part_width, label_y, part_label)

    pdf.restoreState()


def draw_two_step_strip(
    pdf: Canvas, x: float, top: float, strip: TwoStepStripDiagram, width: float = STRIP_WIDTH
) -> None:
    """
    Draw ``strip`` with its top-left corner at (``x``, ``top``), ``width`` wide and
    ``STRIP_HEIGHT`` high: its whole in a box ``WHOLE_BOX_HEIGHT`` high, over a bar of its parts
    ``STRIP_BAR_HEIGHT`` high.

    Each part is as wide as ``_part_widths`` makes it. An unknown value is shown as "?", and
    filled with ``UNKNOWN_FILL``. A known part is filled with ``KNOWN_FILL``, and a known whole
    is left white. Each number is ``PART_LABEL_SIZE``, or smaller if its box is too narrow for it.
    """
    bottom = top - STRIP_HEIGHT
    pdf.saveState()
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.setFillColor(UNKNOWN_FILL if strip.whole is None else "white")
    pdf.rect(x, bottom + STRIP_BAR_HEIGHT, width, WHOLE_BOX_HEIGHT, stroke=1, fill=1)
    _draw_centred_label(pdf, x + width / 2, top - WHOLE_BOX_HEIGHT / 2, _label(strip.whole), width)

    # the parts, side by side
    left = x
    for value, part_width in zip(strip.parts, _part_widths(strip, width), strict=True):
        pdf.setFillColor(UNKNOWN_FILL if value is None else KNOWN_FILL)
        pdf.rect(left, bottom, part_width, STRIP_BAR_HEIGHT, stroke=1, fill=1)
        middle = bottom + STRIP_BAR_HEIGHT / 2
        _draw_centred_label(pdf, left + part_width / 2, middle, _label(value), part_width)
        left += part_width

    pdf.restoreState()


def _part_widths(strip: TwoStepStripDiagram, width: float) -> list[float]:
    """
    Return the widths of a two-step strip's parts, ``width`` in all.

    Each part's width is in proportion to its value. An unknown part's value is what the whole
    leaves after the known parts, shared among the unknown parts, or 0 if the whole leaves none,
    as in an impossible wrong choice. No part is narrower than ``TWO_STEP_PART_WIDTH``, or than an
    equal share of ``width`` if there are too many parts for that: the room for a narrow part is
    taken from the others, in proportion.
    """
    known = [value for value in strip.parts if value is not None]
    unknowns = len(strip.parts) - len(known)
    left_over = 0 if strip.whole is None else max(strip.whole - sum(known), 0)
    values = [left_over / unknowns if value is None else value for value in strip.parts]
    narrowest = min(TWO_STEP_PART_WIDTH, width / len(values))
    narrow: set[int] = set()
    while True:
        # The parts that aren't narrow share what the narrow ones leave, in proportion.
        others = [index for index in range(len(values)) if index not in narrow]
        room = width - narrowest * len(narrow)
        total = sum(values[index] for index in others)
        widths = [
            narrowest
            if index in narrow
            else room * values[index] / total
            if total
            else room / len(others)
            for index in range(len(values))
        ]
        too_narrow = {index for index in others if widths[index] < narrowest}
        if not too_narrow:
            return widths
        narrow |= too_narrow


def _label_size(label: str, room: float) -> float:
    """Return the size of ``label`` that fits ``room``: ``PART_LABEL_SIZE``, or smaller."""
    full_width = stringWidth(label, BOLD_FONT, PART_LABEL_SIZE)
    return min(PART_LABEL_SIZE, PART_LABEL_SIZE * (room - PART_LABEL_PADDING) / full_width)


def _draw_centred_label(
    pdf: Canvas, centre_x: float, middle_y: float, label: str, room: float
) -> None:
    """Draw ``label`` in black, centred on (``centre_x``, ``middle_y``), sized to fit ``room``."""
    size = _label_size(label, room)
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, size)
    pdf.drawCentredString(centre_x, middle_y - size / 3, label)


def _label(value: int | None) -> str:
    """Return how a strip shows a value: the number, or "?" if it's unknown."""
    return UNKNOWN_LABEL if value is None else str(value)


def _draw_whole(pdf: Canvas, x: float, top: float, label: str, width: float) -> None:
    """Draw a strip's whole, labelled ``label``, above a bracket ``width`` wide."""
    end_x = x + width
    bracket_y = top - 12
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 11)
    pdf.drawCentredString(x + width / 2, top - 8, f"whole: {label}")
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
    ticks = _ticks(x, NUMBER_LINE_WIDTH, len(jumps) + 1)
    if jumps[0] < 0:
        ticks.reverse()  # start at the right, and jump left
    pdf.saveState()
    _draw_line(pdf, x, NUMBER_LINE_WIDTH, line_y, ticks)

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
        _draw_jump(pdf, start_x, end_x, line_y, JUMP_HEIGHT, _jump_label(jump), line_y + 29)

    pdf.restoreState()


def draw_two_jump_line(
    pdf: Canvas, x: float, top: float, line: TwoJumpLine, width: float = NUMBER_LINE_WIDTH
) -> None:
    """
    Draw a number line to choose from, from 0 with two jumps, with its top-left corner at
    (``x``, ``top``), ``width`` wide and ``TWO_JUMP_LINE_HEIGHT`` high.

    Its three ticks are 0, the first jump's landing and the line's end, evenly spaced in order of
    value, not to scale, each with its number under it. The jumps are labelled arcs from 0 to the
    first landing, and from there to the end, whichever way that is, even against the second
    jump's sign, as a wrong landing can be.
    """
    line_y = top - TWO_JUMP_LINE_DROP
    values = sorted({0, line.first, line.end})
    ticks = _ticks(x, width, len(values))
    tick_of = dict(zip(values, ticks, strict=True))
    pdf.saveState()
    _draw_line(pdf, x, width, line_y, ticks)

    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, TWO_JUMP_LABEL_SIZE)
    for value, tick in tick_of.items():
        pdf.drawCentredString(tick, line_y - TWO_JUMP_NUMBER_DROP, str(value))

    pdf.setStrokeColor(JUMP_COLOUR)
    pdf.setFillColor(JUMP_COLOUR)
    pdf.setLineWidth(1.3)
    for start, end, jump in ((0, line.first, line.first), (line.first, line.end, line.second)):
        start_x, end_x = tick_of[start], tick_of[end]
        long = abs(values.index(end) - values.index(start)) > 1
        pull = LONG_JUMP_HEIGHT if long else SHORT_JUMP_HEIGHT
        label_y = line_y + 0.75 * pull + TWO_JUMP_LABEL_RAISE  # 3/4 of the pull is the arc's top
        _draw_jump(pdf, start_x, end_x, line_y, pull, _jump_label(jump), label_y)

    pdf.restoreState()


def draw_equal_jump_line(
    pdf: Canvas, x: float, top: float, line: EqualJumpLine, width: float, jump_labels: bool
) -> None:
    """
    Draw a number line of equal jumps from 0, with its top-left corner at (``x``, ``top``),
    ``width`` wide and ``EQUAL_JUMP_LINE_HEIGHT`` high.

    Its ticks are evenly spaced: one for 0 and one for each jump's landing, each with its number
    under it, except the last, the total, which is "?". Each jump is an arc to the next tick,
    numbered 1, 2, 3 and so on above it with ``jump_labels``, and otherwise left for the student
    to count. The ticks' numbers and the jumps' shrink to fit between the ticks.
    """
    line_y = top - EQUAL_JUMP_LINE_DROP
    ticks = _ticks(x, width, line.jumps + 1)
    step = ticks[1] - ticks[0]
    numbers = [str(line.size * index) for index in range(line.jumps)] + [UNKNOWN_LABEL]
    labels = [str(jump) if jump_labels else "" for jump in range(1, line.jumps + 1)]
    widest = max(stringWidth(text, BOLD_FONT, TWO_JUMP_LABEL_SIZE) for text in numbers + labels)
    number_size = min(TWO_JUMP_LABEL_SIZE, TWO_JUMP_LABEL_SIZE * (step - 3) / widest)
    pdf.saveState()
    _draw_line(pdf, x, width, line_y, ticks)

    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, number_size)
    for tick, number in zip(ticks, numbers, strict=True):
        pdf.drawCentredString(tick, line_y - TWO_JUMP_NUMBER_DROP, number)

    pdf.setStrokeColor(JUMP_COLOUR)
    pdf.setFillColor(JUMP_COLOUR)
    pdf.setLineWidth(1)
    pdf.setFont(BOLD_FONT, number_size)
    pull = min(EQUAL_JUMP_PULL + EQUAL_JUMP_PULL_PER_POINT * step, EQUAL_JUMP_MOST_PULL)
    label_y = line_y + 0.75 * pull + TWO_JUMP_LABEL_RAISE  # 3/4 of the pull is the arc's top
    arrowhead = min(JUMP_ARROWHEAD_LENGTH, step / 3)
    for label, (start_x, end_x) in zip(labels, pairwise(ticks), strict=True):
        _draw_jump(pdf, start_x, end_x, line_y, pull, label, label_y, arrowhead)

    pdf.restoreState()


def _ticks(x: float, width: float, count: int) -> list[float]:
    """
    Return ``count`` evenly spaced ticks along a number line ``width`` wide from ``x``, from
    left to right, leaving room for its overhang and arrowheads.
    """
    first_tick = x + LINE_ARROW_LENGTH + LINE_OVERHANG
    step = (width - 2 * (LINE_ARROW_LENGTH + LINE_OVERHANG)) / (count - 1)
    return [first_tick + index * step for index in range(count)]


def _draw_line(pdf: Canvas, x: float, width: float, line_y: float, ticks: Sequence[float]) -> None:
    """Draw a number line ``width`` wide from ``x``, with arrowheads at both ends, and ``ticks``."""
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setFillColor(OUTLINE_COLOUR)
    pdf.setLineWidth(1.2)
    pdf.line(x + LINE_ARROW_LENGTH, line_y, x + width - LINE_ARROW_LENGTH, line_y)
    for tip, back in ((x, LINE_ARROW_LENGTH), (x + width, -LINE_ARROW_LENGTH)):
        arrowhead = pdf.beginPath()
        arrowhead.moveTo(tip, line_y)
        arrowhead.lineTo(tip + back, line_y + 4)
        arrowhead.lineTo(tip + back, line_y - 4)
        arrowhead.close()
        pdf.drawPath(arrowhead, stroke=0, fill=1)
    for tick in ticks:
        pdf.line(tick, line_y - TICK_HALF_HEIGHT, tick, line_y + TICK_HALF_HEIGHT)


def _jump_label(jump: int) -> str:
    """Return a jump's label, its sign and size: "+ 25", or "- 25" for a jump back."""
    sign = SYMBOLS[Operation.ADD if jump > 0 else Operation.SUBTRACT]
    return f"{sign} {abs(jump)}"


def _draw_jump(
    pdf: Canvas,
    start_x: float,
    end_x: float,
    line_y: float,
    pull: float,
    label: str,
    label_y: float,
    arrowhead_length: float = JUMP_ARROWHEAD_LENGTH,
) -> None:
    """
    Draw a jump along a number line: an arc from ``start_x`` to ``end_x``, pulled ``pull`` above
    the line, with an arrowhead ``arrowhead_length`` long pointing the way it goes, and ``label``
    centred over it at ``label_y``. The arrowhead keeps the shape of a full-size one. The pen's
    colours, width and font are the caller's.
    """
    quarter = (end_x - start_x) / 4
    pull_y = line_y + pull
    # The arc ends travelling from its last control point towards the tick, so the arrowhead
    # points that way, with its tip on the line. The arc stops at the arrowhead's base, so its
    # end doesn't show beside the tip.
    length = hypot(quarter, pull)
    along_x, along_y = quarter / length, -pull / length
    base_x = end_x - arrowhead_length * along_x
    base_y = line_y - arrowhead_length * along_y
    arc = pdf.beginPath()
    arc.moveTo(start_x, line_y)
    arc.curveTo(start_x + quarter, pull_y, end_x - quarter, pull_y, base_x, base_y)
    pdf.drawPath(arc, stroke=1, fill=0)
    half_width = JUMP_ARROWHEAD_WIDTH / JUMP_ARROWHEAD_LENGTH * arrowhead_length / 2
    arrowhead = pdf.beginPath()
    arrowhead.moveTo(end_x, line_y)
    arrowhead.lineTo(base_x - half_width * along_y, base_y + half_width * along_x)
    arrowhead.lineTo(base_x + half_width * along_y, base_y - half_width * along_x)
    arrowhead.close()
    pdf.drawPath(arrowhead, stroke=0, fill=1)
    pdf.drawCentredString((start_x + end_x) / 2, label_y, label)


def draw_array(
    pdf: Canvas, x: float, top: float, array: Array, width: float, height: float
) -> None:
    """
    Draw ``array``'s dots, ``array.rows`` rows of ``array.columns``, centred in a box ``width``
    wide and ``height`` high with its top-left corner at (``x``, ``top``). The dots are evenly
    spaced, ``ARRAY_DOT_SPACING`` apart, or closer if the box needs it.
    """
    spacing = min(ARRAY_DOT_SPACING, height / array.rows, width / array.columns)
    first_x = x + (width - spacing * array.columns) / 2 + spacing / 2
    first_y = top - (height - spacing * array.rows) / 2 - spacing / 2
    pdf.saveState()
    pdf.setFillColor(ARRAY_DOT_COLOUR)
    for row in range(array.rows):
        for column in range(array.columns):
            centre_x, centre_y = first_x + column * spacing, first_y - row * spacing
            pdf.circle(centre_x, centre_y, ARRAY_DOT_RADIUS * spacing, stroke=0, fill=1)
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
