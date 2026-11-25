"""
Fraction pictures, as plain functions over a canvas: area models, groups of objects, number lines
and fraction walls, each drawn from its description in ``core.fraction_models``.

Each drawer takes the position of the picture's top-left corner and the room it has. Shading is
in ``COLOUR_FRACTIONS``, blue, or ``GREY_FRACTIONS``, for black-and-white copies.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from math import acos, ceil, cos, degrees, floor, radians, sin, sqrt, tan
from typing import assert_never

from reportlab.lib.colors import Color, HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfgen.pathobject import PDFPathObject

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    Circle,
    ConcaveOctagon,
    CutShape,
    FractionWall,
    Grid,
    Lattice,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Strip,
    TriangleGrid,
)
from core.fraction_models.number_lines import (
    UNIT_NAMES,
    FractionLine,
    Mark,
    TickLabels,
    tick_fraction,
    tick_positions,
)
from core.fraction_models.object_groups import ObjectGroup
from core.written_numbers import UnreducedFraction
from render.pdf.graphics.common import OUTLINE_COLOUR, draw_cake_from_the_side, draw_polygon
from render.pdf.graphics.number_lines import (
    EQUAL_JUMP_MOST_PULL,
    EQUAL_JUMP_PULL,
    EQUAL_JUMP_PULL_PER_POINT,
    JUMP_ARROWHEAD_LENGTH,
    JUMP_ARROWHEAD_WIDTH,
    LINE_ARROW_LENGTH,
    LINE_OVERHANG,
    draw_jump,
    draw_ticked_line,
)
from render.pdf.graphics.objects import FACING_LEFT, draw_object
from render.pdf.page import BOLD_FONT, FONT, draw_fraction, fraction_width

type Point = tuple[float, float]


@dataclass(frozen=True)
class FractionColours:
    """The colours of a fraction picture, apart from its dark outlines and black text."""

    shaded: Color  # a shaded part, a filled-in object, or a bar along a number line
    marks: Color  # a number line's jumps, arrow and stars


# The blue is dark enough to show as grey on a black-and-white copy.
COLOUR_FRACTIONS = FractionColours(shaded=HexColor("#7aaee0"), marks=HexColor("#2b6cb0"))
GREY_FRACTIONS = FractionColours(shaded=HexColor("#a8a8a8"), marks=HexColor("#444444"))

PART_LINE_WIDTH = 1.2
CRUST = 0.84  # a pizza's or a sandwich's crust, its inner edge as a share of the way to its edge
MOST_PEPPERONI_PARTS = 12  # a pizza cut into more slices has no pepperoni drawn
ROUND_CAKE_HEIGHT = 0.62  # a round cake seen from the side, its height as a share of its width

GROUP_MOST_SPACING = 40  # the most from one object's left edge to the next one's
GROUP_GAP = 0.2  # the gap between two objects, as a share of the spacing

# A number line: the line and its ticks are the word problems' number lines'.
LINE_LABEL_SIZE = 11  # the numbers under the ticks, unless they need shrinking to fit
LINE_WHOLES_DROP = 16  # from the line down to the baseline of whole numbers alone
LINE_FRACTIONS_DROP = 20  # from the line down to the baseline of the ticks' numbers, all labelled
LINE_DOT_RADIUS = 3.2
LINE_STAR_RADIUS = 6.5
LINE_LETTER_SIZE = 11
LINE_LETTER_GAP = 4  # from the top of what's on the line at a point up to its letter's baseline
LINE_ARROW_RAISE = 12  # from the line up to the arrow from 0
LINE_ARROWHEAD_LENGTH = 7
LINE_BAR_HEIGHT = 8  # a shaded bar along the line, centred on it
LINE_PICTURE_SIZE = 24  # an object over a tick, unless it needs shrinking to fit beside another
LINE_PICTURE_GAP = 3  # from the top of what's under an object over a tick up to the object
# A compact number line, small enough for a tiles answer bank's box
COMPACT_ARROW_LENGTH = 4
COMPACT_OVERHANG = 2  # the line runs this far past the end ticks, then ends in an arrowhead
COMPACT_TICK_HALF_HEIGHT = 3
COMPACT_DOT_RADIUS = 2.2
COMPACT_LABEL_SIZE = 9
COMPACT_WHOLES_DROP = 12  # from the line down to the baseline of its whole numbers
# How much of a fraction line is above the line: room for the stars, then for the jumps and the
# arrow, if any, and then for letters, if any; and below it, for the ticks' numbers
LINE_MARKS_ROOM = LINE_STAR_RADIUS + 1
LINE_ARCS_ROOM = LINE_ARROW_RAISE + 4
LINE_LETTER_ROOM = LINE_LETTER_SIZE + LINE_LETTER_GAP
LINE_WHOLES_ROOM = LINE_WHOLES_DROP + 3
LINE_FRACTIONS_ROOM = LINE_FRACTIONS_DROP + 8
LINE_PICTURE_ROOM = LINE_PICTURE_SIZE + LINE_PICTURE_GAP

WALL_ROW_HEIGHT = 24
WALL_LABEL_SIZE = 11  # each part's unit fraction, unless it needs shrinking to fit

ROW_LABEL_SIZE = 11  # a label under a model in a row, "Model R"
ROW_LABEL_ROOM = 18  # from the bottom of a model's room down to the bottom of its label
ROW_GAP = 16  # between two models' rooms in a row


def draw_area_model(
    pdf: Canvas,
    x: float,
    top: float,
    model: AreaModel,
    width: float,
    height: float,
    colours: FractionColours,
) -> None:
    """
    Draw ``model`` in a box ``width`` wide and ``height`` high with its top-left corner at
    (``x``, ``top``), its shaded parts in ``colours``, and the rest white.

    A strip, a grid or a rectangle cut from its centre fills the box. Every other model keeps its
    shape, as large as the box allows, in its middle. Parts left out aren't drawn, and the rest
    stay where they would be in the whole, at its size. A model with a look is drawn as that
    object, as ``_decorate`` describes: a round cake from the side, and a chocolate bar in one
    piece in its wrapper, in place of their parts.
    """
    pdf.saveState()
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(PART_LINE_WIDTH)
    pdf.setLineJoin(1)  # round, so that thin parts' corners don't spike
    # each part's fill, or None for a part left out
    fills = [
        None if part in model.removed else colours.shaded if part in model.shaded else white
        for part in range(model.split.parts)
    ]
    split = model.split
    if model.look is DrawnObject.ROUND_CAKE:
        _draw_round_cake(pdf, x, top, width, height, fills[0] or white)
        pdf.restoreState()
        return
    if model.look is DrawnObject.CHOCOLATE_BAR and split.parts == 1:
        _draw_wrapped_bar(pdf, x, top, width, height, fills[0] or white)
        pdf.restoreState()
        return
    match split:
        case Strip():
            _draw_strip(pdf, x, top, split, width, height, fills)
        case Grid():
            _draw_grid(pdf, x, top, split, width, height, fills)
        case RadialPartition():
            _draw_radial_partition(pdf, x, top, split, width, height, fills)
        case SlicedCircle():
            _draw_sliced_circle(pdf, x, top, split, width, height, fills)
        case TriangleGrid():
            _draw_triangle_grid(pdf, x, top, split, width, height, fills)
        case CutShape():
            _draw_cut_shape(pdf, x, top, split, width, height, fills)
        case _:
            assert_never(split)
    if model.look is not None:
        _decorate(pdf, x, top, model, width, height)
    pdf.restoreState()


def _decorate(
    pdf: Canvas, x: float, top: float, model: AreaModel, width: float, height: float
) -> None:
    """
    Draw what makes ``model``'s whole look like its object, over its parts: a pizza's crust and
    a pepperoni slice on each part, a sandwich's crust, a bead of icing round a square cake, and a
    chocolate bar's squares raised from their edges. Drawn as lines, so a part's shading shows.
    """
    pdf.setLineWidth(PART_LINE_WIDTH * 0.75)
    split = model.split
    match model.look:
        case DrawnObject.PIZZA if isinstance(split, RadialPartition):
            middle_x, middle_y = x + width / 2, top - height / 2
            radius = min(width, height) / 2
            pdf.circle(middle_x, middle_y, radius * CRUST, stroke=1, fill=0)
            if split.parts == 1:
                spots = [Fraction(turn, 5) for turn in range(5)]
            elif split.parts <= MOST_PEPPERONI_PARTS:
                spots = [(start + end) / 2 for start, end in _part_edges(split)]
            else:
                spots = []
            size = radius * min(0.12, 1.4 / max(len(spots), 1))
            for spot in spots:
                angle = radians(90 - 360 * float(spot))
                spot_x = middle_x + radius * 0.56 * cos(angle)
                spot_y = middle_y + radius * 0.56 * sin(angle)
                pdf.circle(spot_x, spot_y, size, stroke=1, fill=0)
        case DrawnObject.SANDWICH if isinstance(split, RadialPartition) and isinstance(
            split.outline, RegularPolygon
        ):
            corners, (centre_x, centre_y) = _corners(split.outline, x, top, width, height)
            inner = [
                (centre_x + (corner_x - centre_x) * CRUST, centre_y + (corner_y - centre_y) * CRUST)
                for corner_x, corner_y in corners
            ]
            _stroke_polygon(pdf, inner)
        case DrawnObject.SQUARE_CAKE:
            inset = min(width, height) * 0.08
            bead = min(width, height) * 0.025
            across, down = width - 2 * inset, height - 2 * inset
            beads_across = max(2, round(across / (bead * 3)))
            beads_down = max(2, round(down / (bead * 3)))
            left, right, upper, lower = (
                x + inset,
                x + width - inset,
                top - inset,
                top - height + inset,
            )
            for step in range(beads_across + 1):
                bead_x = left + across * step / beads_across
                for bead_y in (upper, lower):
                    pdf.circle(bead_x, bead_y, bead, stroke=1, fill=0)
            for step in range(1, beads_down):
                bead_y = upper - down * step / beads_down
                for bead_x in (left, right):
                    pdf.circle(bead_x, bead_y, bead, stroke=1, fill=0)
        case DrawnObject.CHOCOLATE_BAR if isinstance(split, Grid):
            part_width, part_height = width / split.columns, height / split.rows
            inset = min(part_width, part_height) * 0.18
            for row in range(split.rows):
                for column in range(split.columns):
                    if row * split.columns + column in model.removed:
                        continue
                    left = x + column * part_width + inset
                    bottom = top - (row + 1) * part_height + inset
                    pdf.rect(
                        left,
                        bottom,
                        part_width - 2 * inset,
                        part_height - 2 * inset,
                        stroke=1,
                        fill=0,
                    )


def _stroke_polygon(pdf: Canvas, points: Sequence[Point]) -> None:
    """Draw the closed outline through ``points``, unfilled."""
    path = pdf.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    pdf.drawPath(path, stroke=1, fill=0)


def _draw_round_cake(
    pdf: Canvas, x: float, top: float, width: float, height: float, fill: Color
) -> None:
    """Draw a round cake seen from the side, whole, as large as the box allows, in its middle, as
    ``draw_cake_from_the_side`` draws it."""
    cake_width = min(width, height / ROUND_CAKE_HEIGHT)
    cake_height = cake_width * ROUND_CAKE_HEIGHT
    pdf.setFillColor(fill)
    draw_cake_from_the_side(
        pdf, x + (width - cake_width) / 2, top - (height - cake_height) / 2, cake_width, cake_height
    )


def _draw_wrapped_bar(
    pdf: Canvas, x: float, top: float, width: float, height: float, fill: Color
) -> None:
    """Draw a chocolate bar in its wrapper, filling the box: a band round its middle and crimped
    ends."""
    crimp = min(width * 0.08, height * 0.3)
    pdf.setFillColor(fill)
    pdf.rect(x + crimp, top - height, width - 2 * crimp, height, stroke=1, fill=1)
    pdf.rect(x + width * 0.35, top - height, width * 0.3, height, stroke=1, fill=0)
    teeth = max(3, round(height / crimp))
    for side, edge in ((1, x + crimp), (-1, x + width - crimp)):
        points = [(edge, top)]
        for tooth in range(teeth):
            points.append((edge - side * crimp, top - height * (tooth + 0.5) / teeth))
            points.append((edge, top - height * (tooth + 1) / teeth))
        draw_polygon(pdf, points)


def row_height(height: float, labelled: bool) -> float:
    """Return how high ``draw_models_in_a_row`` draws models ``height`` high, with or without
    labels under them."""
    return height + (ROW_LABEL_ROOM if labelled else 0)


def draw_models_in_a_row(
    pdf: Canvas,
    x: float,
    top: float,
    width: float,
    height: float,
    models: Sequence[AreaModel],
    colours: FractionColours,
    labels: Sequence[str] | None = None,
    scales: Sequence[float] | None = None,
) -> None:
    """
    Draw ``models`` side by side, with the top-left corner at (``x``, ``top``), ``width`` wide
    and ``row_height(height, labels is not None)`` high: each in an equal share of the width,
    ``height`` high, with a gap between, and its label, if any, centred under its share.

    Each model fills its share, or with ``scales``, that share of it, in its middle, so that two
    wholes can be different sizes: 1 is full size and 0.6 smaller. A strip, a grid or a rectangle
    cut from its centre takes its share's shape, so a square grid beside another square needs a
    width that makes the shares square.
    """
    count = len(models)
    share = (width - (count - 1) * ROW_GAP) / count
    for index, model in enumerate(models):
        left = x + index * (share + ROW_GAP)
        scale = 1 if scales is None else scales[index]
        inset_x, inset_y = share * (1 - scale) / 2, height * (1 - scale) / 2
        draw_area_model(
            pdf, left + inset_x, top - inset_y, model, share * scale, height * scale, colours
        )
        if labels is not None:
            pdf.saveState()
            pdf.setFillColor("black")
            pdf.setFont(FONT, ROW_LABEL_SIZE)
            pdf.drawCentredString(
                left + share / 2, top - height - ROW_LABEL_ROOM + 4, labels[index]
            )
            pdf.restoreState()


def _draw_strip(
    pdf: Canvas,
    x: float,
    top: float,
    strip: Strip,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """Draw ``strip``'s parts left to right, filling the box, each as wide as its size."""
    left = x
    for size, fill in zip(strip.sizes, fills, strict=True):
        part = width * size
        if fill is not None:
            pdf.setFillColor(fill)
            pdf.rect(left, top - height, part, height, stroke=1, fill=1)
        left += part


def _draw_grid(
    pdf: Canvas,
    x: float,
    top: float,
    grid: Grid,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """Draw ``grid``'s parts row by row from the top left, filling the box."""
    part_width, part_height = width / grid.columns, height / grid.rows
    for index, fill in enumerate(fills):
        if fill is None:
            continue
        row, column = divmod(index, grid.columns)
        pdf.setFillColor(fill)
        left, bottom = x + column * part_width, top - (row + 1) * part_height
        pdf.rect(left, bottom, part_width, part_height, stroke=1, fill=1)


def _draw_radial_partition(
    pdf: Canvas,
    x: float,
    top: float,
    partition: RadialPartition,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """Draw ``partition``'s parts clockwise from its start, as large as the box allows, in its
    middle, or filling the box for a rectangle."""
    outline = partition.outline
    if isinstance(outline, Circle):
        middle_x, middle_y = x + width / 2, top - height / 2
        radius = min(width, height) / 2
        if partition.parts == 1:  # a whole, which can't leave out its only part
            pdf.setFillColor(fills[0] or white)
            pdf.circle(middle_x, middle_y, radius, stroke=1, fill=1)
            return
        box = (middle_x - radius, middle_y - radius, middle_x + radius, middle_y + radius)
        for (start, end), fill in zip(_part_edges(partition), fills, strict=True):
            if fill is None:
                continue
            pdf.setFillColor(fill)
            # angles go anticlockwise from 3 o'clock, and parts clockwise from 12
            pdf.wedge(*box, 90 - 360 * float(end), 360 * float(end - start), stroke=1, fill=1)
        return

    corners, centre = _corners(outline, x, top, width, height)
    if partition.parts == 1:
        pdf.setFillColor(fills[0] or white)
        draw_polygon(pdf, corners)
        return
    sides = len(corners)
    for (start, end), fill in zip(_part_edges(partition), fills, strict=True):
        if fill is None:
            continue
        # the part's corners are the centre, the edge at its start, the shape's corners passed
        # on the way, and the edge at its end
        passed = [
            corners[corner % sides] for corner in range(floor(start * sides) + 1, ceil(end * sides))
        ]
        pdf.setFillColor(fill)
        draw_polygon(pdf, [centre, _edge_point(corners, start), *passed, _edge_point(corners, end)])


def _part_edges(partition: RadialPartition) -> list[tuple[Fraction, Fraction]]:
    """
    Return where each of ``partition``'s parts starts and ends, as shares of the way clockwise
    round its edge from its first corner. A part may end past 1, going round past the first
    corner.
    """
    edges = []
    start = partition.start
    for size in partition.sizes:
        edges.append((start, start + size))
        start += size
    return edges


def _corners(
    outline: RegularPolygon | Rectangle | ConcaveOctagon,
    x: float,
    top: float,
    width: float,
    height: float,
) -> tuple[list[Point], Point]:
    """
    Return the corners of a shape with corners, clockwise from its first, and its centre, in a
    box ``width`` by ``height`` with its top-left corner at (``x``, ``top``): a rectangle fills
    the box, and any other shape is as large as fits, in its middle.
    """
    middle_x, middle_y = x + width / 2, top - height / 2
    if isinstance(outline, Rectangle):
        corners = [(x, top), (x + width, top), (x + width, top - height), (x, top - height)]
        return corners, (middle_x, middle_y)
    if isinstance(outline, ConcaveOctagon):
        half = min(width, height) / 2  # the points are a square's corners
        inner = half * float(outline.inner_corner)
        star = [
            (-half, half),
            (0, inner),
            (half, half),
            (inner, 0),
            (half, -half),
            (0, -inner),
            (-half, -half),
            (-inner, 0),
        ]
        return [(middle_x + dx, middle_y + dy) for dx, dy in star], (middle_x, middle_y)
    # a regular polygon's corners round a circle of radius 1, clockwise from the top one, or the
    # left of the two at the top, in degrees anticlockwise from 3 o'clock
    sides = outline.sides
    corner_on_top = (sides % 2 == 1) != outline.on_corner
    first = 90 if corner_on_top else 90 + 180 / sides
    angles = [radians(first - 360 * index / sides) for index in range(sides)]
    unit = [(cos(angle), sin(angle)) for angle in angles]
    lowest_x, highest_x = min(dx for dx, _ in unit), max(dx for dx, _ in unit)
    lowest_y, highest_y = min(dy for _, dy in unit), max(dy for _, dy in unit)
    scale = min(width / (highest_x - lowest_x), height / (highest_y - lowest_y))
    # the centre, where it puts the shape in the middle of the box: a triangle's is low
    centre_x = middle_x - scale * (lowest_x + highest_x) / 2
    centre_y = middle_y - scale * (lowest_y + highest_y) / 2
    corners = [(centre_x + scale * dx, centre_y + scale * dy) for dx, dy in unit]
    return corners, (centre_x, centre_y)


def _edge_point(corners: Sequence[Point], share: Fraction) -> Point:
    """Return the point ``share`` of the way clockwise round a shape's edge from its first
    corner, of ``corners``."""
    sides = len(corners)
    position = share % 1 * sides
    side = floor(position)
    along = float(position - side)
    (start_x, start_y), (end_x, end_y) = corners[side], corners[(side + 1) % sides]
    return start_x + along * (end_x - start_x), start_y + along * (end_y - start_y)


def _draw_sliced_circle(
    pdf: Canvas,
    x: float,
    top: float,
    circle: SlicedCircle,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """
    Draw ``circle``'s slices from the left, or from the top for horizontal ones, as large as the
    box allows, in its middle. Each slice is its own outline: a line down each side, if it has
    one, and the circle's edge over and under it.
    """
    radius = min(width, height) / 2
    pdf.saveState()
    pdf.translate(x + width / 2, top - height / 2)
    if circle.horizontal:
        pdf.rotate(-90)  # a quarter turn clockwise takes the slices from the left to the top
    for index, fill in enumerate(fills):
        if fill is None:
            continue
        left = -radius + 2 * radius * index / circle.parts
        right = left + 2 * radius / circle.parts
        # where the slice's sides meet the circle's top, anticlockwise from 3 o'clock
        left_angle = degrees(acos(max(left / radius, -1)))
        right_angle = degrees(acos(min(right / radius, 1)))
        outline = pdf.beginPath()
        outline.moveTo(left, radius * sin(radians(left_angle)))
        _add_arc(outline, radius, left_angle, right_angle - left_angle)  # over, clockwise
        outline.lineTo(right, -radius * sin(radians(right_angle)))
        _add_arc(outline, radius, -right_angle, right_angle - left_angle)  # and under
        outline.close()
        pdf.setFillColor(fill)
        pdf.drawPath(outline, stroke=1, fill=1)
    pdf.restoreState()


def _add_arc(path: PDFPathObject, radius: float, start: float, extent: float) -> None:
    """
    Continue ``path`` round the circle of ``radius`` centred on (0, 0), from the point ``start``
    degrees anticlockwise from 3 o'clock, where the path is, for ``extent`` degrees, anticlockwise,
    or clockwise if it's negative. It goes in curves of at most 90 degrees, each a cubic Bézier
    curve with its control points on the circle's tangents.
    """
    pieces = max(1, ceil(abs(extent) / 90))
    step = radians(extent / pieces)
    reach = 4 / 3 * tan(step / 4) * radius  # how far along each tangent its control point is
    angle = radians(start)
    for _ in range(pieces):
        end = angle + step
        path.curveTo(
            radius * cos(angle) - reach * sin(angle),
            radius * sin(angle) + reach * cos(angle),
            radius * cos(end) + reach * sin(end),
            radius * sin(end) - reach * cos(end),
            radius * cos(end),
            radius * sin(end),
        )
        angle = end


def _draw_triangle_grid(
    pdf: Canvas,
    x: float,
    top: float,
    grid: TriangleGrid,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """Draw ``grid``'s small triangles row by row from the top, as large as the box allows, in
    its middle."""
    side = min(width, height * 2 / sqrt(3))
    rise = side * sqrt(3) / 2
    middle_x, apex_y = x + width / 2, top - (height - rise) / 2
    small, small_rise = side / grid.rows, rise / grid.rows
    index = 0
    for row in range(grid.rows):
        upper_y, lower_y = apex_y - row * small_rise, apex_y - (row + 1) * small_rise
        upper_left, lower_left = middle_x - row * small / 2, middle_x - (row + 1) * small / 2
        for place in range(2 * row + 1):
            step = place // 2
            if place % 2 == 0:  # pointing up
                points = [
                    (lower_left + step * small, lower_y),
                    (upper_left + step * small, upper_y),
                    (lower_left + (step + 1) * small, lower_y),
                ]
            else:  # pointing down, between two that point up
                points = [
                    (upper_left + step * small, upper_y),
                    (upper_left + (step + 1) * small, upper_y),
                    (lower_left + (step + 1) * small, lower_y),
                ]
            fill = fills[index]
            if fill is not None:
                pdf.setFillColor(fill)
                draw_polygon(pdf, points)
            index += 1


def _draw_cut_shape(
    pdf: Canvas,
    x: float,
    top: float,
    cut: CutShape,
    width: float,
    height: float,
    fills: Sequence[Color | None],
) -> None:
    """
    Draw ``cut``'s pieces, keeping the whole's shape, as large as the box allows, in its middle.
    A corner on the triangle lattice is half its distance down further across, and its distance
    down is shortened to the height of a triangle with equal sides.
    """

    def placed(corner: tuple[Fraction | int, Fraction | int]) -> Point:  # across and down
        across, down = float(corner[0]), float(corner[1])
        if cut.outline.lattice is Lattice.TRIANGLE:
            return across + down / 2, down * sqrt(3) / 2
        return across, down

    outline = [placed(corner) for corner in cut.outline.corners]
    lowest_x, lowest_y = min(x for x, _ in outline), min(y for _, y in outline)
    span_x = max(x for x, _ in outline) - lowest_x
    span_y = max(y for _, y in outline) - lowest_y
    scale = min(width / span_x, height / span_y)
    left = x + (width - scale * span_x) / 2 - scale * lowest_x
    upper = top - (height - scale * span_y) / 2 + scale * lowest_y
    for piece, fill in zip(cut.pieces, fills, strict=True):
        if fill is not None:
            pdf.setFillColor(fill)
            corners = [placed(corner) for corner in piece]
            draw_polygon(
                pdf, [(left + across * scale, upper - down * scale) for across, down in corners]
            )


def draw_object_group(
    pdf: Canvas,
    x: float,
    top: float,
    group: ObjectGroup,
    width: float,
    height: float,
    colours: FractionColours,
) -> None:
    """
    Draw ``group``'s objects in rows from the top left, centred in a box ``width`` wide and
    ``height`` high with its top-left corner at (``x``, ``top``): each as large as the box
    allows, up to ``GROUP_MOST_SPACING`` apart, and those shaded filled in ``colours``.
    """
    rows = ceil(group.count / group.per_row)
    columns = min(group.count, group.per_row)
    spacing = min(width / columns, height / rows, GROUP_MOST_SPACING)
    size = spacing * (1 - GROUP_GAP)
    first_x = x + (width - spacing * columns) / 2 + (spacing - size) / 2
    first_top = top - (height - spacing * rows) / 2 - (spacing - size) / 2
    for index in range(group.count):
        row, column = divmod(index, group.per_row)
        fill = colours.shaded if index in group.shaded else None
        draw_object(
            pdf, group.kind, first_x + column * spacing, first_top - row * spacing, size, fill=fill
        )


def fraction_line_height(line: FractionLine, compact: bool = False) -> float:
    """Return how high ``draw_fraction_line`` draws ``line``, compact or not."""
    return _room_above(line, compact) + _room_below(line, compact)


def fraction_line_drop(line: FractionLine, compact: bool = False) -> float:
    """Return how far below the top of ``draw_fraction_line``'s picture of ``line`` the line
    itself is, compact or not."""
    return _room_above(line, compact)


def _room_above(line: FractionLine, compact: bool = False) -> float:
    """Return how much of ``line``'s picture is above the line."""
    return _room_under_pictures(line, compact) + (LINE_PICTURE_ROOM if line.pictures else 0)


def _room_under_pictures(line: FractionLine, compact: bool) -> float:
    """Return how much of ``line``'s picture above the line is under its pictures: its stars,
    jumps and arrow, and the points' letters."""
    if compact:
        room = COMPACT_DOT_RADIUS + 1
    elif line.jumps or line.arrow_to is not None:
        room = LINE_ARCS_ROOM
    else:
        room = LINE_MARKS_ROOM
    if any(point.letter for point in line.points):
        room += LINE_LETTER_ROOM
    return room


def _room_below(line: FractionLine, compact: bool = False) -> float:
    """Return how much of ``line``'s picture is below the line."""
    if compact:
        return COMPACT_WHOLES_DROP + 3
    return LINE_FRACTIONS_ROOM if line.labels is TickLabels.EVERY_TICK else LINE_WHOLES_ROOM


def draw_fraction_line(
    pdf: Canvas,
    x: float,
    top: float,
    line: FractionLine,
    width: float,
    colours: FractionColours,
    compact: bool = False,
) -> None:
    """
    Draw ``line`` with its top-left corner at (``x``, ``top``), ``width`` wide and
    ``fraction_line_height(line, compact)`` high, with arrowheads at both ends, and its jumps,
    arrow, stars and bar in ``colours``. ``compact`` draws it small enough for a tiles answer
    bank's box: smaller arrowheads, ticks, dots and numbers, closer to the line.

    The ticks' numbers are under them: whole numbers, and with every tick labelled, the rest as
    fractions, shrunk if they need to be to fit between the ticks. A unit's name follows the last
    whole number, "1 foot", with the ticks drawn closer if it needs the room. Each point's letter
    is over everything else at the point but its picture. Pictures are above everything,
    shrunk if two would touch, and an object drawn facing left is mirrored to face right, the way
    a distance goes.
    """
    line_y = top - _room_above(line, compact)
    ticks = _fraction_line_ticks(line, x, width, compact)
    pdf.saveState()
    if line.bar_to is not None:
        pdf.setFillColor(colours.shaded)
        bar_width = ticks[line.bar_to] - ticks[0]
        pdf.rect(
            ticks[0], line_y - LINE_BAR_HEIGHT / 2, bar_width, LINE_BAR_HEIGHT, stroke=0, fill=1
        )
    if compact:
        draw_ticked_line(
            pdf, x, width, line_y, ticks, COMPACT_ARROW_LENGTH, COMPACT_TICK_HALF_HEIGHT
        )
    else:
        draw_ticked_line(pdf, x, width, line_y, ticks)
    _draw_tick_labels(pdf, line, ticks, line_y, compact)

    pdf.setStrokeColor(colours.marks)
    pdf.setFillColor(colours.marks)
    pdf.setLineWidth(1)
    step = ticks[1] - ticks[0]
    pull = min(EQUAL_JUMP_PULL + EQUAL_JUMP_PULL_PER_POINT * step, EQUAL_JUMP_MOST_PULL)
    arrowhead = min(JUMP_ARROWHEAD_LENGTH, step / 3)
    for jump in range(line.jumps):
        draw_jump(pdf, ticks[jump], ticks[jump + 1], line_y, pull, "", line_y, arrowhead)
    if line.arrow_to is not None:
        _draw_arrow(pdf, ticks[0], ticks[line.arrow_to], line_y + LINE_ARROW_RAISE)

    letters_y = line_y + _room_under_pictures(line, compact) - LINE_LETTER_SIZE - 2
    for point in line.points:
        point_x = _x_at(ticks, point.tick)
        match point.mark:
            case Mark.DOT:
                pdf.setFillColor("black")
                radius = COMPACT_DOT_RADIUS if compact else LINE_DOT_RADIUS
                pdf.circle(point_x, line_y, radius, stroke=0, fill=1)
            case Mark.STAR:  # a star's middle is 0.47 of the way up its square
                size = 2 * LINE_STAR_RADIUS
                star_top = line_y + 0.53 * size
                draw_object(
                    pdf, DrawnObject.STAR, point_x - size / 2, star_top, size, fill=colours.marks
                )
            case _:
                assert_never(point.mark)
        if point.letter:
            pdf.setFillColor("black")
            pdf.setFont(BOLD_FONT, LINE_LETTER_SIZE)
            pdf.drawCentredString(point_x, letters_y, point.letter)
    if line.pictures:
        _draw_line_pictures(pdf, line, ticks, line_y + _room_under_pictures(line, compact))
    pdf.restoreState()


def _draw_line_pictures(
    pdf: Canvas, line: FractionLine, ticks: Sequence[float], bottom: float
) -> None:
    """Draw ``line``'s pictures, each centred over its tick, standing ``LINE_PICTURE_GAP`` above
    ``bottom``, ``LINE_PICTURE_SIZE`` wide or less, so that none touch."""
    places = [ticks[picture.tick] for picture in line.pictures]
    gaps = [abs(first - second) for first, second in combinations(places, 2)]
    size = min([LINE_PICTURE_SIZE, *(gap - 2 for gap in gaps)])
    picture_top = bottom + LINE_PICTURE_GAP + size
    for picture, place in zip(line.pictures, places, strict=True):
        draw_object(
            pdf,
            picture.kind,
            place - size / 2,
            picture_top,
            size,
            mirrored=picture.kind in FACING_LEFT,
        )


def _x_at(ticks: Sequence[float], tick: int | Fraction) -> float:
    """Return the x of ``tick``, which may be between two ticks, in proportion."""
    low = floor(tick)
    if low == tick:
        return ticks[low]
    return ticks[low] + float(tick - low) * (ticks[low + 1] - ticks[low])


def _fraction_line_ticks(
    line: FractionLine, x: float, width: float, compact: bool = False
) -> list[float]:
    """
    Return the x of each of ``line``'s ticks along a line ``width`` wide from ``x``, evenly
    spaced unless its parts are unequal, closer together if the last whole's number and unit need
    more room than the line runs past its last tick.
    """
    beyond = (
        COMPACT_ARROW_LENGTH + COMPACT_OVERHANG if compact else LINE_ARROW_LENGTH + LINE_OVERHANG
    )
    first, last = x + beyond, x + width - beyond
    if line.unit is not None:
        number, unit = _last_whole_label(line)
        needed = stringWidth(number, FONT, LINE_LABEL_SIZE) / 2 + stringWidth(
            unit, FONT, LINE_LABEL_SIZE
        )
        last -= max(needed - beyond, 0)
    return [first + float(place) / line.wholes * (last - first) for place in tick_positions(line)]


def _last_whole_label(line: FractionLine) -> tuple[str, str]:
    """Return the last whole's number and what follows it: its unit's name, singular for 1,
    after a space, or nothing."""
    number = f"{line.wholes:,}"
    if line.unit is None:
        return number, ""
    singular, plural = UNIT_NAMES[line.unit]
    return number, f" {singular if line.wholes == 1 else plural}"


def _draw_tick_labels(
    pdf: Canvas, line: FractionLine, ticks: Sequence[float], line_y: float, compact: bool = False
) -> None:
    """Draw the numbers under ``line``'s ticks: whole numbers, and with every tick labelled,
    fractions."""
    every_tick = line.labels is TickLabels.EVERY_TICK
    if compact:
        baseline = line_y - COMPACT_WHOLES_DROP
    else:
        baseline = line_y - (LINE_FRACTIONS_DROP if every_tick else LINE_WHOLES_DROP)
    size: float = COMPACT_LABEL_SIZE if compact else LINE_LABEL_SIZE
    if every_tick and line.parts > 1:
        widest = fraction_width(tick_fraction(line, line.last_tick - 1), LINE_LABEL_SIZE)
        size = min(LINE_LABEL_SIZE, LINE_LABEL_SIZE * (ticks[1] - ticks[0] - 2) / widest)
    pdf.setFillColor("black")
    for tick, tick_x in enumerate(ticks):
        whole, part = divmod(tick, line.parts)
        if part == 0:
            pdf.setFont(FONT, size)
            if whole == line.wholes:
                number, unit = _last_whole_label(line)
                pdf.drawCentredString(tick_x, baseline, number)
                pdf.drawString(tick_x + stringWidth(number, FONT, size) / 2, baseline, unit)
            else:
                pdf.drawCentredString(tick_x, baseline, f"{whole:,}")
        elif every_tick:
            fraction = tick_fraction(line, tick)
            draw_fraction(
                pdf, tick_x - fraction_width(fraction, size) / 2, baseline, fraction, size
            )


def _draw_arrow(pdf: Canvas, start_x: float, end_x: float, y: float) -> None:
    """Draw a straight arrow from ``start_x`` to ``end_x`` at height ``y``, in the pen's
    colours."""
    length = min(LINE_ARROWHEAD_LENGTH, (end_x - start_x) / 2)
    half_width = JUMP_ARROWHEAD_WIDTH / JUMP_ARROWHEAD_LENGTH * length / 2
    pdf.line(start_x, y, end_x - length, y)
    head = pdf.beginPath()
    head.moveTo(end_x, y)
    head.lineTo(end_x - length, y + half_width)
    head.lineTo(end_x - length, y - half_width)
    head.close()
    pdf.drawPath(head, stroke=0, fill=1)


def fraction_wall_height(wall: FractionWall) -> float:
    """Return how high ``draw_fraction_wall`` draws ``wall``."""
    return len(wall.denominators) * WALL_ROW_HEIGHT


def draw_fraction_wall(pdf: Canvas, x: float, top: float, wall: FractionWall, width: float) -> None:
    """
    Draw ``wall`` with its top-left corner at (``x``, ``top``), ``width`` wide and
    ``fraction_wall_height(wall)`` high: one row for each denominator, from the top, cut into
    that many equal white parts. When it's labelled, each part's unit fraction is in its middle,
    shrunk to fit if it needs to be, and the whole's 1.
    """
    pdf.saveState()
    pdf.setStrokeColor(OUTLINE_COLOUR)
    pdf.setLineWidth(PART_LINE_WIDTH)
    pdf.setFillColor(white)
    for row, denominator in enumerate(wall.denominators):
        bottom = top - (row + 1) * WALL_ROW_HEIGHT
        part = width / denominator
        for index in range(denominator):
            pdf.rect(x + index * part, bottom, part, WALL_ROW_HEIGHT, stroke=1, fill=1)
        if wall.labelled:
            _draw_wall_labels(pdf, x, bottom, part, denominator)
            pdf.setFillColor(white)
    pdf.restoreState()


def _draw_wall_labels(pdf: Canvas, x: float, bottom: float, part: float, denominator: int) -> None:
    """Draw a fraction wall's row's labels: 1 for the whole, else each part's unit fraction."""
    middle_y = bottom + WALL_ROW_HEIGHT / 2
    pdf.setFillColor("black")
    if denominator == 1:
        pdf.setFont(FONT, WALL_LABEL_SIZE)
        pdf.drawCentredString(x + part / 2, middle_y - WALL_LABEL_SIZE * 0.36, "1")
        return
    fraction = UnreducedFraction(1, denominator)
    size = min(
        WALL_LABEL_SIZE, WALL_LABEL_SIZE * (part - 4) / fraction_width(fraction, WALL_LABEL_SIZE)
    )
    width = fraction_width(fraction, size)
    for index in range(denominator):
        left = x + index * part + (part - width) / 2
        draw_fraction(pdf, left, middle_y - size * 0.3, fraction, size)  # the bar in the middle
