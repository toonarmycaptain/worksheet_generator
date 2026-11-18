"""
Coordinate grids as plain functions over a canvas: the grid itself, with its axes and numbers,
drawn apart from what is plotted on it (lines, points, segments and rays, with open or closed
ends), so any sheet can plot what it needs on one.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import hypot, inf

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from render.pdf.page import FONT, ITALIC_FONT

GRIDLINE_COLOUR = HexColor("#cbd5e0")  # light grey
AXIS_COLOUR = HexColor("#2d3748")  # near black, as table outlines
GRIDLINE_WIDTH = 0.5
AXIS_WIDTH = 1
PLOT_WIDTH = 1.5  # a line, segment or ray plotted on the grid
NUMBER_SIZE = 7  # the axes' numbers
NUMBER_GAP = 2  # from an axis to its numbers, and the least gap between two numbers
AXIS_LABEL_SIZE = 10  # the italic x and y at the axes' ends
ARROW_LENGTH = 7
ARROW_HALF_WIDTH = 3
AXIS_OVERHANG = 8  # an axis runs this far past the grid, ending in an arrowhead
DOT_RADIUS = 2.6  # a plotted point
POINT_LABEL_SIZE = 8
POINT_LABEL_GAP = 4  # from a point to the nearest edge of its label
LABEL_PADDING = 1  # the white behind a number or label, past its text
# How many gridlines apart the axes' numbers can be, as a share of every gridline: the first
# whose numbers don't run into each other
NUMBER_INTERVALS = (1, 2, 5, 10)


@dataclass(frozen=True)
class Plane:
    """
    Where a grid is drawn on the page: its left edge and bottom, ``unit``, the length of one
    coordinate unit, and how far it runs, x from -``largest_x`` to ``largest_x`` and y from
    -``largest_y`` to ``largest_y``.
    """

    left: float
    bottom: float
    unit: float
    largest_x: float
    largest_y: float

    def at(self, x: float, y: float) -> tuple[float, float]:
        """Return the page position of the point (``x``, ``y``)."""
        return (
            self.left + (x + self.largest_x) * self.unit,
            self.bottom + (y + self.largest_y) * self.unit,
        )

    @property
    def width(self) -> float:
        return 2 * self.largest_x * self.unit

    @property
    def height(self) -> float:
        return 2 * self.largest_y * self.unit


def plane_height(width: float, largest_x: float, largest_y: float) -> float:
    """Return the height of a grid ``width`` wide that runs as ``draw_coordinate_plane`` says."""
    return width * largest_y / largest_x


def draw_coordinate_plane(
    pdf: Canvas, left: float, top: float, width: float, largest_x: int, largest_y: int, step: int
) -> Plane:
    """
    Draw a grid ``width`` wide with its top-left corner at (``left``, ``top``), x from
    -``largest_x`` to ``largest_x`` and y from -``largest_y`` to ``largest_y``, one square per
    unit both ways, so its height is ``plane_height``. Gridlines are ``step`` units apart, in
    ``GRIDLINE_COLOUR``. Each axis runs a little past the grid at both ends, with an arrowhead,
    and is labelled x or y at its positive end. The axes' numbers sit beside them, below the
    x-axis and left of the y-axis, at every gridline when they fit, otherwise at every second,
    fifth or tenth, as ``NUMBER_INTERVALS`` has it; 0 isn't numbered.

    Returns the ``Plane`` to plot on.
    """
    unit = width / (2 * largest_x)
    height = 2 * largest_y * unit
    plane = Plane(left, top - height, unit, largest_x, largest_y)
    right, bottom = left + width, top - height

    pdf.setStrokeColor(GRIDLINE_COLOUR)
    pdf.setLineWidth(GRIDLINE_WIDTH)
    for x in range(-largest_x, largest_x + 1, step):
        page_x, _ = plane.at(x, 0)
        pdf.line(page_x, bottom, page_x, top)
    for y in range(-largest_y, largest_y + 1, step):
        _, page_y = plane.at(0, y)
        pdf.line(left, page_y, right, page_y)

    origin_x, origin_y = plane.at(0, 0)
    pdf.setStrokeColor(AXIS_COLOUR)
    pdf.setFillColor(AXIS_COLOUR)
    pdf.setLineWidth(AXIS_WIDTH)
    pdf.line(left - AXIS_OVERHANG, origin_y, right + AXIS_OVERHANG, origin_y)
    pdf.line(origin_x, bottom - AXIS_OVERHANG, origin_x, top + AXIS_OVERHANG)
    for tip, direction in (
        ((right + AXIS_OVERHANG, origin_y), (1, 0)),
        ((left - AXIS_OVERHANG, origin_y), (-1, 0)),
        ((origin_x, top + AXIS_OVERHANG), (0, 1)),
        ((origin_x, bottom - AXIS_OVERHANG), (0, -1)),
    ):
        _arrowhead(pdf, tip, direction)
    pdf.setFont(ITALIC_FONT, AXIS_LABEL_SIZE)
    pdf.drawString(right + AXIS_OVERHANG - AXIS_LABEL_SIZE / 2, origin_y + NUMBER_GAP + 2, "x")
    pdf.drawString(origin_x + NUMBER_GAP + 2, top + AXIS_OVERHANG - AXIS_LABEL_SIZE, "y")

    every = _number_interval(pdf, largest_x, step, unit)
    pdf.setFont(FONT, NUMBER_SIZE)
    for x in range(-largest_x + step, largest_x, step):
        if x and (x // step) % every == 0:
            page_x, _ = plane.at(x, 0)
            _number(pdf, page_x, origin_y - NUMBER_GAP - NUMBER_SIZE, _signed(x), "centre")
    every = max(every, _number_interval(pdf, largest_y, step, unit, across=False))
    for y in range(-largest_y + step, largest_y, step):
        if y and (y // step) % every == 0:
            _, page_y = plane.at(0, y)
            _number(pdf, origin_x - NUMBER_GAP - 1, page_y - NUMBER_SIZE / 3, _signed(y), "right")
    pdf.setStrokeColor("black")
    pdf.setFillColor("black")
    return plane


def draw_line(pdf: Canvas, plane: Plane, a: float, b: float, c: float) -> None:
    """
    Draw the line ax + by = c across ``plane``, with an arrowhead at each end where it leaves
    the grid. ``a`` and ``b`` mustn't both be 0. Draws nothing if the line misses the grid.
    """
    x0, y0 = (c / a, 0.0) if a else (0.0, c / b)
    span = _span(plane, (x0, y0), (b, -a))
    if span is None:
        return
    low, high = span
    start, end = plane.at(x0 + b * low, y0 - a * low), plane.at(x0 + b * high, y0 - a * high)
    _plot_segment(pdf, start, end)
    _arrowhead(pdf, end, (end[0] - start[0], end[1] - start[1]))
    _arrowhead(pdf, start, (start[0] - end[0], start[1] - end[1]))


def draw_segment(
    pdf: Canvas,
    plane: Plane,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    start_closed: bool = True,
    end_closed: bool = True,
) -> None:
    """
    Draw the segment from ``start`` to ``end`` on ``plane``, each end a closed (filled) or an
    open (hollow) circle, as ``start_closed`` and ``end_closed`` say.
    """
    first, last = plane.at(*start), plane.at(*end)
    _plot_segment(pdf, first, last)
    _end(pdf, first, start_closed)
    _end(pdf, last, end_closed)


def draw_ray(
    pdf: Canvas,
    plane: Plane,
    start: tuple[float, float],
    through: tuple[float, float],
    *,
    closed: bool = True,
) -> None:
    """
    Draw the ray from ``start`` through ``through`` on ``plane`` to the grid's edge, ending in
    an arrowhead, its start a closed (filled) or an open (hollow) circle, as ``closed`` says.
    """
    direction = (through[0] - start[0], through[1] - start[1])
    span = _span(plane, start, direction)
    first = plane.at(*start)
    if span is not None and span[1] > 0:
        _, high = span
        last = plane.at(start[0] + direction[0] * high, start[1] + direction[1] * high)
        _plot_segment(pdf, first, last)
        _arrowhead(pdf, last, (last[0] - first[0], last[1] - first[1]))
    _end(pdf, first, closed)


def draw_point(
    pdf: Canvas,
    plane: Plane,
    point: tuple[float, float],
    label: str | None = None,
    away: tuple[float, float] = (-1, 1),
) -> None:
    """
    Draw ``point`` as a dot on ``plane``, with ``label`` beside it if given, on a white ground
    so the gridlines don't cross it. The label goes ``away`` from the point, a direction on the
    page, such as away from the line the point is on, and is kept inside the grid.
    """
    x, y = plane.at(*point)
    pdf.circle(x, y, DOT_RADIUS, stroke=0, fill=1)
    if label is None:
        return
    pdf.setFont(FONT, POINT_LABEL_SIZE)
    width = pdf.stringWidth(label, FONT, POINT_LABEL_SIZE)
    height = POINT_LABEL_SIZE
    length = hypot(*away) or 1
    dx, dy = away[0] / length, away[1] / length
    # how far from the point to the label's centre, so its nearest edge is POINT_LABEL_GAP away
    reach = POINT_LABEL_GAP + DOT_RADIUS + abs(dx) * width / 2 + abs(dy) * height / 2
    centre_x = min(
        max(x + dx * reach, plane.left + width / 2), plane.left + plane.width - width / 2
    )
    centre_y = min(
        max(y + dy * reach, plane.bottom + height / 2), plane.bottom + plane.height - height / 2
    )
    _number(pdf, centre_x, centre_y - height / 3, label, "centre", POINT_LABEL_SIZE)


def _number_interval(
    pdf: Canvas, largest: int, step: int, unit: float, *, across: bool = True
) -> int:
    """
    Return how many gridlines apart an axis's numbers go: the first of ``NUMBER_INTERVALS`` at
    which the widest number, across the x-axis, or the font's height, up the y-axis, fits
    between neighbours with ``NUMBER_GAP`` to spare.
    """
    size = pdf.stringWidth(_signed(-largest), FONT, NUMBER_SIZE) if across else NUMBER_SIZE
    for every in NUMBER_INTERVALS:
        if size + NUMBER_GAP <= every * step * unit:
            return every
    return NUMBER_INTERVALS[-1]


def _signed(value: int) -> str:
    """Return ``value`` as text, with the minus sign rather than a hyphen."""
    return f"\N{MINUS SIGN}{-value}" if value < 0 else str(value)


def _number(
    pdf: Canvas,
    x: float,
    baseline: float,
    text: str,
    align: str,
    size: float = NUMBER_SIZE,
) -> None:
    """
    Draw ``text`` at ``baseline``, centred on ``x`` or ending at it, as ``align`` says, on a
    white ground so the gridlines don't cross it.
    """
    width = pdf.stringWidth(text, FONT, size)
    left = x - width / 2 if align == "centre" else x - width
    pdf.saveState()
    pdf.setFillColor("white")
    pdf.rect(
        left - LABEL_PADDING,
        baseline - size / 4 - LABEL_PADDING,
        width + 2 * LABEL_PADDING,
        size + 2 * LABEL_PADDING,
        stroke=0,
        fill=1,
    )
    pdf.restoreState()
    pdf.setFont(FONT, size)
    pdf.drawString(left, baseline, text)


def _span(
    plane: Plane, start: tuple[float, float], direction: Sequence[float]
) -> tuple[float, float] | None:
    """
    Return the range of t for which ``start`` + t * ``direction`` lies on ``plane``'s grid, or
    ``None`` if it never does.
    """
    low, high = -inf, inf
    for origin, change, largest in (
        (start[0], direction[0], plane.largest_x),
        (start[1], direction[1], plane.largest_y),
    ):
        if change == 0:
            if abs(origin) > largest:
                return None
            continue
        first, second = (-largest - origin) / change, (largest - origin) / change
        low, high = max(low, min(first, second)), min(high, max(first, second))
    return (low, high) if low < high else None


def _plot_segment(pdf: Canvas, start: tuple[float, float], end: tuple[float, float]) -> None:
    """Draw a plotted line from ``start`` to ``end``, page positions, in black."""
    pdf.setStrokeColor("black")
    pdf.setLineWidth(PLOT_WIDTH)
    pdf.line(*start, *end)


def _end(pdf: Canvas, at: tuple[float, float], closed: bool) -> None:
    """Draw a segment's or ray's end at ``at``: a filled circle if ``closed``, else hollow."""
    pdf.setLineWidth(1)
    pdf.setStrokeColor("black")
    pdf.setFillColor("black" if closed else "white")
    pdf.circle(*at, DOT_RADIUS + 0.4, stroke=1, fill=1)
    pdf.setFillColor("black")


def _arrowhead(pdf: Canvas, tip: tuple[float, float], direction: Sequence[float]) -> None:
    """Draw a filled arrowhead with its point at ``tip``, pointing along ``direction``."""
    length = hypot(*direction) or 1
    dx, dy = direction[0] / length, direction[1] / length
    back_x, back_y = tip[0] - dx * ARROW_LENGTH, tip[1] - dy * ARROW_LENGTH
    path = pdf.beginPath()
    path.moveTo(*tip)
    path.lineTo(back_x - dy * ARROW_HALF_WIDTH, back_y + dx * ARROW_HALF_WIDTH)
    path.lineTo(back_x + dy * ARROW_HALF_WIDTH, back_y - dx * ARROW_HALF_WIDTH)
    path.close()
    pdf.drawPath(path, stroke=0, fill=1)
