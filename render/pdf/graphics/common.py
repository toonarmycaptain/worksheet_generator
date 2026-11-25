"""
What the graphics share: the dark outline colour, the label for an unknown number, and
drawing a polygon and a round cake seen from the side.
"""

from collections.abc import Sequence
from math import sqrt

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


SIDE_CAKE_TOP = 0.3  # a round cake's top, an oval, its height as a share of the cake's width
# Each drip of icing down a round cake's side, left to right, its length as a share of the side's
# height, short and long by turns, all ending above the line between the layers
SIDE_CAKE_DRIPS = (0.18, 0.3, 0.22, 0.34, 0.24, 0.3, 0.2)


def draw_cake_from_the_side(
    pdf: Canvas, left: float, top: float, width: float, height: float
) -> None:
    """
    Draw a round cake seen from the side, in a box ``width`` by ``height`` with its top-left
    corner at (``left``, ``top``), filled with the fill colour: its side, with a line round it
    between its two layers, its top an oval, and icing dripping from the top's front edge.
    """
    half = width * SIDE_CAKE_TOP / 2  # half the top's height
    right, middle = left + width, left + width / 2
    rim = top - half  # the middle of the top, where the side starts
    base = top - height + half  # the middle of the base
    # control points this far below a curve's ends make its middle sag ``half``, like the front
    # of an oval as wide
    sag = half * 4 / 3
    side = pdf.beginPath()
    side.moveTo(left, rim)
    side.lineTo(left, base)
    side.curveTo(left, base - sag, right, base - sag, right, base)
    side.lineTo(right, rim)
    side.close()
    pdf.drawPath(side, stroke=1, fill=1)
    layer = (rim + base) / 2
    between = pdf.beginPath()
    between.moveTo(left, layer)
    between.curveTo(left, layer - sag, right, layer - sag, right, layer)
    pdf.drawPath(between, stroke=1, fill=0)
    pdf.ellipse(left, top - 2 * half, right, top, stroke=1, fill=1)

    def front(across: float) -> float:  # the top's front edge, below ``across``
        return rim - half * sqrt(max(0.0, 1 - ((across - middle) / (width / 2)) ** 2))

    step = width / len(SIDE_CAKE_DRIPS)
    gap = half * 0.25  # from the top's edge down to the icing's, between drips
    drips = pdf.beginPath()
    drips.moveTo(left, rim)
    for index, length in enumerate(SIDE_CAKE_DRIPS):
        start, end = left + index * step, left + (index + 1) * step
        start_y = front(start) - gap if index else rim
        end_y = front(end) - gap if index < len(SIDE_CAKE_DRIPS) - 1 else rim
        tip_x = (start + end) / 2
        tip_y = front(tip_x) - gap - length * (rim - base)
        drips.curveTo(start + step * 0.15, start_y, tip_x - step * 0.45, tip_y, tip_x, tip_y)
        drips.curveTo(tip_x + step * 0.45, tip_y, end - step * 0.15, end_y, end, end_y)
    pdf.drawPath(drips, stroke=1, fill=0)
