"""
Number lines drawn with word problems and multiplication models: an open number line of jumps,
a line of two jumps to choose from, and a line of equal jumps; and the ticks and jump arcs that
other number lines reuse.
"""

from collections.abc import Sequence
from itertools import pairwise
from math import hypot

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.data import Operation
from core.basic_operations.multiplication_models import EqualJumpLine
from core.basic_operations.representation import (
    SYMBOLS,
    TwoJumpLine,
)
from render.pdf.graphics.common import OUTLINE_COLOUR, UNKNOWN_LABEL
from render.pdf.page import BOLD_FONT, ITALIC_FONT, TEXT_WIDTH

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
    ticks = line_ticks(x, NUMBER_LINE_WIDTH, len(jumps) + 1)
    if jumps[0] < 0:
        ticks.reverse()  # start at the right, and jump left
    pdf.saveState()
    draw_ticked_line(pdf, x, NUMBER_LINE_WIDTH, line_y, ticks)

    # the start under its tick, and a box under each landing
    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, 11)
    pdf.drawCentredString(ticks[0], line_y - 17, f"{start:,}")
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
        draw_jump(pdf, start_x, end_x, line_y, JUMP_HEIGHT, _jump_label(jump), line_y + 29)

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
    ticks = line_ticks(x, width, len(values))
    tick_of = dict(zip(values, ticks, strict=True))
    pdf.saveState()
    draw_ticked_line(pdf, x, width, line_y, ticks)

    pdf.setFillColor("black")
    pdf.setFont(BOLD_FONT, TWO_JUMP_LABEL_SIZE)
    for value, tick in tick_of.items():
        pdf.drawCentredString(tick, line_y - TWO_JUMP_NUMBER_DROP, f"{value:,}")

    pdf.setStrokeColor(JUMP_COLOUR)
    pdf.setFillColor(JUMP_COLOUR)
    pdf.setLineWidth(1.3)
    for start, end, jump in ((0, line.first, line.first), (line.first, line.end, line.second)):
        start_x, end_x = tick_of[start], tick_of[end]
        long = abs(values.index(end) - values.index(start)) > 1
        pull = LONG_JUMP_HEIGHT if long else SHORT_JUMP_HEIGHT
        label_y = line_y + 0.75 * pull + TWO_JUMP_LABEL_RAISE  # 3/4 of the pull is the arc's top
        draw_jump(pdf, start_x, end_x, line_y, pull, _jump_label(jump), label_y)

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
    ticks = line_ticks(x, width, line.jumps + 1)
    step = ticks[1] - ticks[0]
    numbers = [str(line.size * index) for index in range(line.jumps)] + [UNKNOWN_LABEL]
    labels = [str(jump) if jump_labels else "" for jump in range(1, line.jumps + 1)]
    widest = max(stringWidth(text, BOLD_FONT, TWO_JUMP_LABEL_SIZE) for text in numbers + labels)
    number_size = min(TWO_JUMP_LABEL_SIZE, TWO_JUMP_LABEL_SIZE * (step - 3) / widest)
    pdf.saveState()
    draw_ticked_line(pdf, x, width, line_y, ticks)

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
        draw_jump(pdf, start_x, end_x, line_y, pull, label, label_y, arrowhead)

    pdf.restoreState()


def line_ticks(x: float, width: float, count: int) -> list[float]:
    """
    Return ``count`` evenly spaced ticks along a number line ``width`` wide from ``x``, from
    left to right, leaving room for its overhang and arrowheads.
    """
    first_tick = x + LINE_ARROW_LENGTH + LINE_OVERHANG
    step = (width - 2 * (LINE_ARROW_LENGTH + LINE_OVERHANG)) / (count - 1)
    return [first_tick + index * step for index in range(count)]


def draw_ticked_line(
    pdf: Canvas, x: float, width: float, line_y: float, ticks: Sequence[float]
) -> None:
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
    return f"{sign} {abs(jump):,}"


def draw_jump(
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
