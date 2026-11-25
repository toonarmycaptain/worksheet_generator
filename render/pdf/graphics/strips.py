"""
Strip diagrams, drawn with word problems and strip choice questions: a whole over two parts, a
bar of equal groups, and a two-step strip.
"""

from typing import assert_never

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.representation import (
    EqualStripDiagram,
    StripDiagram,
    TwoStepStripDiagram,
)
from render.pdf.graphics.common import OUTLINE_COLOUR, UNKNOWN_LABEL
from render.pdf.page import BOLD_FONT

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

PART_LABEL_SIZE = 12  # a part's number, unless the part is too narrow for it
PART_LABEL_PADDING = 4  # the least room left beside a narrow part's number
# A two-step strip's whole is in a box over its bar, where a strip's whole label and bracket are.
WHOLE_BOX_HEIGHT = STRIP_HEIGHT - STRIP_BAR_HEIGHT
TWO_STEP_PART_WIDTH = 24  # the least width of a two-step strip's part, while there's room


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
    pdf.drawCentredString((x + split_x) / 2, label_y, f"{left:,}")
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
    return UNKNOWN_LABEL if value is None else f"{value:,}"


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
