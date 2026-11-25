"""
What the graphics share: the dark outline colour, the label for an unknown number, and
drawing a polygon.
"""

from collections.abc import Sequence

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

type Point = tuple[float, float]

UNKNOWN_LABEL = "?"

OUTLINE_COLOUR = HexColor("#2d3748")


def draw_polygon(pdf: Canvas, points: Sequence[tuple[float, float]]) -> None:
    """Draw the closed outline through ``points``, filled with the fill colour."""
    path = pdf.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    pdf.drawPath(path, stroke=1, fill=1)
