"""Tests for area models: how a whole is cut, which parts are shaded or left out, and walls."""

from collections.abc import Callable
from fractions import Fraction

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    EQUILATERAL_TRIANGLE,
    HALF_HEXAGON,
    PARALLELOGRAM,
    REGULAR_HEXAGON,
    RHOMBUS,
    AreaModel,
    Circle,
    ConcaveOctagon,
    CutShape,
    FractionWall,
    Grid,
    Lattice,
    Polygon,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Split,
    Strip,
    TriangleGrid,
    equal_sizes,
    halved_by_diagonal,
    lattice_triangles,
    quartered_by_diagonals,
    rectangle,
    same_shape_parts,
    shaded_fraction,
    striped,
    tiled,
    uneven_sizes,
)
from core.written_numbers import UnreducedFraction

HALF, THIRD, QUARTER = Fraction(1, 2), Fraction(1, 3), Fraction(1, 4)
# a square cut corner to corner, top left to bottom right: the lower triangle, then the upper
DIAGONAL_SQUARE = CutShape(rectangle(1, 1), (((0, 0), (1, 1), (0, 1)), ((0, 0), (1, 0), (1, 1))))
# a rectangle of two squares, one over the other, cut corner to corner and between the squares
TWO_SQUARES = CutShape(
    rectangle(1, 2),
    (
        ((0, 0), (HALF, 1), (0, 1)),
        ((0, 0), (1, 0), (1, 1), (HALF, 1)),
        ((0, 1), (HALF, 1), (1, 2), (0, 2)),
        ((HALF, 1), (1, 1), (1, 2)),
    ),
)
HEXAGON = RadialPartition(RegularPolygon(6, on_corner=True), equal_sizes(6))


@pytest.mark.parametrize(
    ("parts", "sizes"),
    [
        (1, (Fraction(1),)),
        (4, (Fraction(1, 4),) * 4),
    ],
)
def test_equal_sizes(parts: int, sizes: tuple[Fraction, ...]) -> None:
    """Each of the parts is the same share of the whole."""
    assert equal_sizes(parts) == sizes


@pytest.mark.parametrize(
    ("parts", "sizes"),
    [
        (2, (Fraction(1, 3), Fraction(2, 3))),
        (5, (Fraction(4, 30), Fraction(5, 30), Fraction(6, 30), Fraction(7, 30), Fraction(8, 30))),
    ],
)
def test_uneven_sizes(parts: int, sizes: tuple[Fraction, ...]) -> None:
    """The parts grow from the smallest to twice it."""
    assert uneven_sizes(parts) == sizes


@pytest.mark.parametrize(
    ("make", "arguments", "message"),
    [
        (equal_sizes, (0,), "A whole has at least 1 part, not 0."),
        (uneven_sizes, (1,), "Unequal parts need at least 2 parts, not 1."),
        (Strip, ((),), "A whole's parts need sizes above 0 that add up to 1, not none."),
        (
            Strip,
            ((Fraction(1, 2), Fraction(1, 4)),),
            "A whole's parts need sizes above 0 that add up to 1, not 1/2, 1/4.",
        ),
        (
            RadialPartition,
            (Circle(), (Fraction(1), Fraction(0))),
            "A whole's parts need sizes above 0 that add up to 1, not 1, 0.",
        ),
        (
            RadialPartition,
            (RegularPolygon(4), equal_sizes(4), Fraction(1)),
            "A radial partition's start is at least 0 and below 1, not 1.",
        ),
        (
            RadialPartition,
            (RegularPolygon(4), equal_sizes(4), Fraction(-1, 8)),
            "A radial partition's start is at least 0 and below 1, not -1/8.",
        ),
        (Grid, (0, 4), "A grid has at least 1 row and column, not 0 by 4."),
        (Grid, (2, 0), "A grid has at least 1 row and column, not 2 by 0."),
        (SlicedCircle, (0,), "A whole has at least 1 part, not 0."),
        (TriangleGrid, (0,), "A triangle grid has at least 1 row, not 0."),
        (RegularPolygon, (2,), "A regular polygon has at least 3 sides, not 2."),
        (
            ConcaveOctagon,
            (Fraction(0),),
            "A concave octagon's inner corners are above 0 and below 1 of the way to its "
            "square's sides, not 0.",
        ),
        (
            ConcaveOctagon,
            (Fraction(1),),
            "A concave octagon's inner corners are above 0 and below 1 of the way to its "
            "square's sides, not 1.",
        ),
        (FractionWall, ((),), "A fraction wall needs rows of 1 part or more, not none."),
        (FractionWall, ((1, 0),), "A fraction wall needs rows of 1 part or more, not 1, 0."),
    ],
)
def test_split_errors(
    make: Callable[..., object], arguments: tuple[object, ...], message: str
) -> None:
    """Sizes are above 0 and add up to 1, a radial partition starts within its edge, and every
    count is 1 or more, or 2 or more for unequal parts."""
    with pytest.raises(ValueError) as error:
        make(*arguments)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("split", "parts", "equal"),
    [
        (Strip(equal_sizes(4)), 4, True),
        (Strip(uneven_sizes(3)), 3, False),
        (Grid(2, 4), 8, True),
        (RadialPartition(Circle(), equal_sizes(7)), 7, True),
        (RadialPartition(RegularPolygon(4), uneven_sizes(4)), 4, False),
        (RadialPartition(ConcaveOctagon(), equal_sizes(8)), 8, True),
        (RadialPartition(RegularPolygon(5), equal_sizes(10)), 10, True),
        (RadialPartition(Rectangle(), uneven_sizes(4), Fraction(1, 8)), 4, False),
        # slices look alike but are equal only as halves
        (SlicedCircle(1), 1, True),
        (SlicedCircle(2, horizontal=True), 2, True),
        (SlicedCircle(4), 4, False),
        (TriangleGrid(3), 9, True),
        # worked out from the pieces' corners: 4 squares cut corner to corner, and 8 pieces that
        # aren't eighths
        (tiled(DIAGONAL_SQUARE, 2, 2), 8, True),
        (tiled(TWO_SQUARES, 2, 1), 8, False),
        (halved_by_diagonal(RHOMBUS), 2, True),
        (striped(EQUILATERAL_TRIANGLE, 3, 1), 3, False),
    ],
)
def test_parts_and_whether_they_are_equal(split: Split, parts: int, equal: bool) -> None:
    """Every split says how many parts it has and whether they're all the same size."""
    assert (split.parts, split.equal_parts) == (parts, equal)


@pytest.mark.parametrize(
    ("outline", "counts"),
    [
        (RegularPolygon(3), (2, 3, 6)),
        (RegularPolygon(4), (2, 4, 8)),
        (RegularPolygon(5), (2, 5, 10)),
        # 4 four-sided parts, each the mirror image of the next, and 12 triangles
        (RegularPolygon(6, on_corner=True), (2, 3, 4, 6, 12)),
        (ConcaveOctagon(Fraction(1, 4)), (2, 4, 8)),
        # its diagonals make 4 triangles of two shapes
        (Rectangle(), (2, 8)),
    ],
)
def test_same_shape_parts(
    outline: RegularPolygon | Rectangle | ConcaveOctagon, counts: tuple[int, ...]
) -> None:
    """The numbers of parts, cut from the centre with the first cut to a corner, that are all
    the same shape: for a regular polygon, every number that goes into twice its sides."""
    assert same_shape_parts(outline) == counts


def test_a_cut_rectangle_works_out_each_piece_s_size() -> None:
    """Two rectangles of two squares, side by side and each cut corner to corner, make a square
    of 8 pieces: 1/16 and 3/16, not eighths."""
    sixteenth, three_sixteenths = Fraction(1, 16), Fraction(3, 16)
    halves = (sixteenth, three_sixteenths, three_sixteenths, sixteenth)
    assert tiled(TWO_SQUARES, 2, 1).sizes == halves * 2


@pytest.mark.parametrize(
    ("cut", "sizes"),
    [
        (halved_by_diagonal(rectangle(2, 1)), (HALF, HALF)),
        # a rectangle of two squares: both diagonals make equal areas of two shapes
        (quartered_by_diagonals(rectangle(2, 1)), (QUARTER,) * 4),
        (halved_by_diagonal(RHOMBUS), (HALF, HALF)),
        (quartered_by_diagonals(PARALLELOGRAM), (QUARTER,) * 4),
        (striped(RHOMBUS, 3), (THIRD,) * 3),
        (striped(PARALLELOGRAM, 2, 1), (HALF, HALF)),
        (lattice_triangles(HALF_HEXAGON), (THIRD,) * 3),
        (lattice_triangles(REGULAR_HEXAGON), (Fraction(1, 6),) * 6),
        (lattice_triangles(EQUILATERAL_TRIANGLE), (QUARTER,) * 4),
        # stripes look even on any shape, but are only on a parallelogram
        (striped(EQUILATERAL_TRIANGLE, 3, 1), (Fraction(5, 9), THIRD, Fraction(1, 9))),
        (striped(HALF_HEXAGON, 2), (Fraction(5, 12), Fraction(7, 12))),
        (striped(REGULAR_HEXAGON, 3), (Fraction(8, 27), Fraction(11, 27), Fraction(8, 27))),
        (
            quartered_by_diagonals(HALF_HEXAGON),
            (Fraction(1, 9), Fraction(2, 9), Fraction(4, 9), Fraction(2, 9)),
        ),
    ],
)
def test_cut_shape_sizes(cut: CutShape, sizes: tuple[Fraction, ...]) -> None:
    """Each piece's share of the whole, worked out exactly from its corners."""
    assert cut.sizes == sizes


@pytest.mark.parametrize(
    ("cut", "expected"),
    [
        (
            tiled(DIAGONAL_SQUARE, 2, 1),
            CutShape(
                rectangle(2, 1),
                (
                    ((0, 0), (1, 1), (0, 1)),
                    ((0, 0), (1, 0), (1, 1)),
                    ((1, 0), (2, 1), (1, 1)),
                    ((1, 0), (2, 0), (2, 1)),
                ),
            ),
        ),
        (
            quartered_by_diagonals(rectangle(2, 1)),
            CutShape(
                rectangle(2, 1),
                (
                    ((0, 0), (2, 0), (1, HALF)),
                    ((2, 0), (2, 1), (1, HALF)),
                    ((2, 1), (0, 1), (1, HALF)),
                    ((0, 1), (0, 0), (1, HALF)),
                ),
            ),
        ),
        (
            striped(RHOMBUS, 2),
            CutShape(
                RHOMBUS,
                (((0, 0), (1, 0), (1, HALF), (0, HALF)), ((1, HALF), (1, 1), (0, 1), (0, HALF))),
            ),
        ),
        # row by row from the top, left to right: up, down, up
        (
            lattice_triangles(HALF_HEXAGON),
            CutShape(
                HALF_HEXAGON,
                (
                    ((1, 0), (1, 1), (0, 1)),
                    ((1, 0), (2, 0), (1, 1)),
                    ((2, 0), (2, 1), (1, 1)),
                ),
            ),
        ),
    ],
)
def test_cut_shape_pieces(cut: CutShape, expected: CutShape) -> None:
    """Tiles go side by side tile by tile, and each cut numbers its pieces in order."""
    assert cut == expected


@pytest.mark.parametrize(
    ("make", "arguments", "message"),
    [
        (
            Polygon,
            (((0, 0), (1, 0)),),
            "An outline needs 3 or more corners round some area, not ((0, 0), (1, 0)).",
        ),
        (
            Polygon,
            (((0, 0), (1, 0), (2, 0)),),
            "An outline needs 3 or more corners round some area, not ((0, 0), (1, 0), (2, 0)).",
        ),
        (
            Polygon,
            (((0, 0), (2, 0), (1, 1), (2, 2), (0, 2)),),
            "An outline has no dents, unlike ((0, 0), (2, 0), (1, 1), (2, 2), (0, 2)).",
        ),
        (
            CutShape,
            (rectangle(1, 1), (((0, 0), (1, 1)),)),
            "A piece needs 3 or more corners round some area, not ((0, 0), (1, 1)).",
        ),
        (
            CutShape,
            (rectangle(2, 1), (((0, 0), (1, 0), (2, 0)),)),
            "A piece needs 3 or more corners round some area, not ((0, 0), (1, 0), (2, 0)).",
        ),
        (
            CutShape,
            (rectangle(1, 1), (((0, 0), (2, 0), (0, 1)),)),
            "A piece's corners are in the outline, unlike ((0, 0), (2, 0), (0, 1))'s.",
        ),
        (
            CutShape,
            (rectangle(1, 1), (((0, 0), (1, 0), (0, 1)),)),
            "The pieces' areas add up to more or less than the outline's.",
        ),
        (tiled, (DIAGONAL_SQUARE, 0, 1), "Tiles go in at least 1 row and column, not 1 by 0."),
        (tiled, (DIAGONAL_SQUARE, 1, 0), "Tiles go in at least 1 row and column, not 0 by 1."),
        (
            tiled,
            (halved_by_diagonal(RHOMBUS), 2, 1),
            "Only a rectangle from (0, 0) on the square lattice is tiled.",
        ),
        (halved_by_diagonal, (EQUILATERAL_TRIANGLE,), "Diagonals cut a shape of 4 corners, not 3."),
        (quartered_by_diagonals, (REGULAR_HEXAGON,), "Diagonals cut a shape of 4 corners, not 6."),
        (
            striped,
            (RHOMBUS, 0),
            "Stripes need a count of 1 or more and a side of the outline, not 0 and 0.",
        ),
        (
            striped,
            (RHOMBUS, 2, 4),
            "Stripes need a count of 1 or more and a side of the outline, not 2 and 4.",
        ),
        (
            lattice_triangles,
            (rectangle(1, 1),),
            "Lattice triangles cut a triangle-lattice outline with whole-number corners.",
        ),
        (
            lattice_triangles,
            (Polygon(((0, 0), (HALF, 0), (0, 1)), Lattice.TRIANGLE),),
            "Lattice triangles cut a triangle-lattice outline with whole-number corners.",
        ),
    ],
)
def test_cut_shape_errors(
    make: Callable[..., object], arguments: tuple[object, ...], message: str
) -> None:
    """An outline has area and no dents; each piece has area inside it, and the pieces fill it;
    tiles are rectangles in rows; diagonals cut 4 corners; stripes come from a side; lattice
    triangles need a triangle lattice."""
    with pytest.raises(ValueError) as error:
        make(*arguments)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("model", "fraction"),
    [
        (AreaModel(Grid(2, 4), frozenset({0, 1})), UnreducedFraction(2, 8)),
        (AreaModel(Strip(equal_sizes(4))), UnreducedFraction(0, 4)),
        (
            AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(8)), frozenset(range(6))),
            UnreducedFraction(6, 8),
        ),
        # 4 of a hexagon's 6 triangles, 1 shaded
        (AreaModel(HEXAGON, frozenset({2}), frozenset({4, 5})), UnreducedFraction(1, 4)),
    ],
)
def test_shaded_fraction(model: AreaModel, fraction: UnreducedFraction) -> None:
    """The shaded parts over the parts shown, as written."""
    assert shaded_fraction(model) == fraction


def test_unequal_parts_show_no_fraction() -> None:
    """One shaded part of 5 unequal parts isn't 1/5."""
    with pytest.raises(ValueError) as error:
        shaded_fraction(AreaModel(Strip(uneven_sizes(5)), frozenset({0})))
    assert str(error.value) == "A whole cut into unequal parts shows no fraction."


@pytest.mark.parametrize(
    ("shaded", "removed", "message"),
    [
        (frozenset({6}), frozenset(), "A whole of 6 parts has no part 6."),
        (frozenset(), frozenset({-1}), "A whole of 6 parts has no part -1."),
        (frozenset({1, 2}), frozenset({2, 3}), "A part left out can't be shaded: [2]."),
        (
            frozenset(),
            frozenset(range(6)),
            "A model leaves out some of its whole's parts, not all of them.",
        ),
    ],
)
def test_area_model_errors(shaded: frozenset[int], removed: frozenset[int], message: str) -> None:
    """Shaded and left-out parts are the whole's, never both, and some part is left in."""
    with pytest.raises(ValueError) as error:
        AreaModel(HEXAGON, shaded, removed)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("split", "look", "message"),
    [
        (
            Strip(equal_sizes(4)),
            DrawnObject.PIZZA,
            "A pizza is drawn as a circle cut from its centre, not Strip.",
        ),
        (
            RadialPartition(Circle(), equal_sizes(4)),
            DrawnObject.ROUND_CAKE,
            "A round cake is drawn as a circle, uncut, not RadialPartition.",
        ),
        (
            RadialPartition(RegularPolygon(6), equal_sizes(6)),
            DrawnObject.SANDWICH,
            "A sandwich is drawn as a square cut from its centre, not RadialPartition.",
        ),
        (
            Strip(equal_sizes(4)),
            DrawnObject.SQUARE_CAKE,
            "A square cake is drawn as a grid, not Strip.",
        ),
        (
            RadialPartition(Circle(), equal_sizes(8)),
            DrawnObject.CHOCOLATE_BAR,
            "A chocolate bar is drawn as a grid, not RadialPartition.",
        ),
        (Grid(2, 4), DrawnObject.BOOK, "A book isn't drawn as a whole cut into parts."),
    ],
)
def test_area_model_look_errors(split: Split, look: DrawnObject, message: str) -> None:
    """A whole drawn as an object is one of those cut into parts, cut as that object is."""
    with pytest.raises(ValueError) as error:
        AreaModel(split, look=look)
    assert str(error.value) == message
