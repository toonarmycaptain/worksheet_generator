"""
Diagrams drawn with word problems, as plain functions over a canvas.

Each drawer takes a diagram description from the core and the position of its top-left corner.
Its colours and sizes are module constants, so a worksheet can measure a diagram before drawing
it.
"""

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.representation import EqualStripDiagram, StripDiagram, StripUnknown
from render.pdf.page import BOLD_FONT

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
