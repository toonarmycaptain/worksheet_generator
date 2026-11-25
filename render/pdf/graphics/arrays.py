"""
Arrays of dots, drawn with multiplication and division.
"""

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from core.basic_operations.multiplication_models import Array

ARRAY_DOT_SPACING = 13  # the most from one dot's centre to the next
ARRAY_DOT_RADIUS = 0.36  # each dot's radius, as a share of the spacing
ARRAY_DOT_COLOUR = HexColor("#2b6cb0")  # blue


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
