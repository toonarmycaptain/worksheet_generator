"""
Equal splits of the shapes that fraction pictures show besides strips, rectangle grids and
circles: regular polygons, rectangles and concave octagons cut from their centres, rhombuses and
parallelograms cut by their diagonals or into stripes, a trapezoid and a hexagon of triangles,
triangles of small triangles, and a square of 4 squares each cut corner to corner.
"""

from fractions import Fraction
from functools import cache

from core.fraction_models.area_models import (
    CIRCLE_LIMITS,
    HALF_HEXAGON,
    PARALLELOGRAM,
    REGULAR_HEXAGON,
    RHOMBUS,
    STRIPED_SHAPE_LIMITS,
    TRIANGLE_GRID_LIMITS,
    ConcaveOctagon,
    PartLimits,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    Split,
    TriangleGrid,
    equal_sizes,
    halved_by_diagonal,
    lattice_triangles,
    quartered_by_diagonals,
    rectangle,
    same_shape_parts,
    striped,
    tiled,
)

# The regular polygons cut from their centres: a triangle pointing up, a square, a pentagon, a
# hexagon flat at the top and one pointing up, and an octagon
POLYGONS = (
    RegularPolygon(3),
    RegularPolygon(4),
    RegularPolygon(5),
    RegularPolygon(6),
    RegularPolygon(6, on_corner=True),
    RegularPolygon(8),
)
# How deep a concave octagon's inner corners are: its points sharper, as in a common four-pointed
# star, or blunter
CONCAVE_DEPTHS = (Fraction(1, 2), Fraction(5, 8), Fraction(3, 4))


@cache  # each split's areas are worked out exactly when it's made, which is slow
def other_shape_splits(parts: int, in_a_choice: bool) -> tuple[Split, ...]:
    """
    Return every split in the catalogue that cuts a whole into ``parts`` equal parts, easy to
    count drawn alone, or with ``in_a_choice``, as one of two pictures side by side. None for
    fewer than 2 parts.

    A regular polygon or a concave octagon is cut from its centre into parts of the same shape,
    first to a corner, and a regular polygon also first to a side's middle: a square into 2
    triangles or 2 rectangles, 4 triangles or 4 squares, or 8 triangles; a triangle into 3
    triangles or 3 kites. A rectangle cut by its diagonals makes 4 triangles of two shapes and
    equal areas. Rhombuses and parallelograms are cut by their diagonals or into stripes
    parallel to either of two sides.
    """
    if parts < 2:
        return ()

    def fits(limits: PartLimits) -> bool:
        return parts <= (limits.in_a_choice if in_a_choice else limits.alone)

    found: list[Split] = []
    if fits(CIRCLE_LIMITS):
        for polygon in POLYGONS:
            if parts in same_shape_parts(polygon):
                found.append(RadialPartition(polygon, equal_sizes(parts)))
                if parts < 2 * polygon.sides:  # with as many parts, the same cuts
                    side_middle = Fraction(1, 2 * polygon.sides)
                    found.append(RadialPartition(polygon, equal_sizes(parts), side_middle))
        if parts in same_shape_parts(ConcaveOctagon()):
            for depth in CONCAVE_DEPTHS:
                found.append(RadialPartition(ConcaveOctagon(depth), equal_sizes(parts)))
                if parts == 4:  # kites, from the inner corners
                    found.append(
                        RadialPartition(ConcaveOctagon(depth), equal_sizes(4), Fraction(1, 8))
                    )
        if parts in (2, 4, 8):
            found.append(RadialPartition(Rectangle(), equal_sizes(parts)))
        if parts == 4:  # by its apothems, into 4 smaller rectangles
            found.append(RadialPartition(Rectangle(), equal_sizes(4), Fraction(1, 8)))
    if parts == 2:
        found += [halved_by_diagonal(RHOMBUS), halved_by_diagonal(PARALLELOGRAM)]
    if parts == 3:
        found.append(lattice_triangles(HALF_HEXAGON))
    if parts == 4:
        found += [quartered_by_diagonals(RHOMBUS), quartered_by_diagonals(PARALLELOGRAM)]
    if parts == 6:
        found.append(lattice_triangles(REGULAR_HEXAGON))
    if parts == 8:
        found.append(tiled(halved_by_diagonal(rectangle(1, 1)), 2, 2))
    if fits(STRIPED_SHAPE_LIMITS):
        for whole in (RHOMBUS, PARALLELOGRAM):
            found += [striped(whole, parts), striped(whole, parts, side=1)]
    rows = round(parts**0.5)
    if rows * rows == parts and fits(TRIANGLE_GRID_LIMITS):
        found.append(TriangleGrid(rows))
    return tuple(found)
