"""
Diagrams drawn with word problems, as plain functions over a canvas.

Each drawer takes a diagram description from the core and the position of its top-left corner.
Its colours and sizes are module constants, so a worksheet can measure a diagram before drawing
it.
"""

from collections.abc import Sequence
from itertools import pairwise
from math import hypot

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.data import Operation
from core.basic_operations.representation import (
    SYMBOLS,
    EqualStripDiagram,
    StripDiagram,
    StripUnknown,
)
from render.pdf.page import BOLD_FONT, ITALIC_FONT, TEXT_WIDTH

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
