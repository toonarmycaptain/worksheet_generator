"""
Area models: a whole cut into parts, some of them shaded, and fraction walls.

A model's parts are numbered, so a question can shade any of them, side by side or scattered.
Some cuts make unequal parts, for a model that shows no fraction, such as one shaded part of 5
unequal parts that someone claims is 1/5. A model can also leave some of its whole's parts out,
showing part of a shape, such as 4 of a hexagon's 6 triangles, or be drawn as an object cut into
parts, such as a pizza cut into slices.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from itertools import pairwise

from core.drawn_objects import DrawnObject
from core.written_numbers import UnreducedFraction


@dataclass(frozen=True)
class PartLimits:
    """
    The most parts a picture shows while they stay easy to count: drawn ``alone``, as wide as the
    page's text, and drawn ``in_a_choice``, one of two choices side by side.
    """

    alone: int
    in_a_choice: int


STRIP_LIMITS = PartLimits(alone=48, in_a_choice=24)
GRID_LIMITS = PartLimits(alone=48, in_a_choice=24)
CIRCLE_LIMITS = PartLimits(alone=24, in_a_choice=16)  # a circle cut from its centre
SLICED_CIRCLE_LIMITS = PartLimits(alone=8, in_a_choice=6)
TRIANGLE_GRID_LIMITS = PartLimits(alone=16, in_a_choice=9)
WALL_LIMITS = PartLimits(alone=24, in_a_choice=12)  # the parts in one of a wall's rows
# A rhombus or a parallelogram cut into stripes parallel to a side, which are narrower than a
# strip's parts
STRIPED_SHAPE_LIMITS = PartLimits(alone=12, in_a_choice=8)
BANK_PICTURE_PARTS = 12  # the most parts of any picture small enough for a tiles answer bank


@dataclass(frozen=True)
class Circle:
    """A circle, as large as the room it's drawn in allows."""


@dataclass(frozen=True)
class RegularPolygon:
    """
    A shape of ``sides`` equal sides and equal angles, standing on a side, or ``on_corner``: a
    triangle standing on a side points up, and a hexagon on a corner points up and down.

    Raises ``ValueError`` for fewer than 3 sides.
    """

    sides: int
    on_corner: bool = False

    def __post_init__(self) -> None:
        if self.sides < 3:
            raise ValueError(f"A regular polygon has at least 3 sides, not {self.sides}.")


@dataclass(frozen=True)
class Rectangle:
    """A rectangle, as wide and as high as the room it's drawn in."""


@dataclass(frozen=True)
class ConcaveOctagon:
    """
    A four-pointed star: 4 kite-shaped arms pointing to a square's corners, its 8 sides the same
    length. Its inner corners are ``inner_corner`` of the way from its centre to the square's
    sides: near 0, its points are sharp, and near 1, it's nearly the square.

    Raises ``ValueError`` unless ``inner_corner`` is above 0 and below 1.
    """

    inner_corner: Fraction = Fraction(5, 8)

    def __post_init__(self) -> None:
        if not 0 < self.inner_corner < 1:
            raise ValueError(
                "A concave octagon's inner corners are above 0 and below 1 of the way to its "
                f"square's sides, not {self.inner_corner}."
            )


# The shape of a whole cut from its centre
type Outline = Circle | RegularPolygon | Rectangle | ConcaveOctagon


def same_shape_parts(outline: RegularPolygon | Rectangle | ConcaveOctagon) -> tuple[int, ...]:
    """
    Return the numbers of parts, 2 or more, that ``outline`` is cut into from its centre with
    every part the same shape, turned or flipped, when the first cut goes to a corner.

    For a regular polygon, that's every number that goes into twice its sides: a square makes 2,
    4 or 8 triangles; a hexagon makes 2 trapezoids, 3 rhombuses, 4 four-sided parts, 6 triangles
    or 12. A concave octagon makes 2 halves, 4 darts or 8 triangles, and a rectangle 2 or 8
    triangles. From a side's middle instead, a regular polygon's numbers are the same, and a
    rectangle's 4 are the same shape too, smaller rectangles. A circle cut into any number of
    equal parts has them the same shape.
    """
    if isinstance(outline, RegularPolygon):
        twice = 2 * outline.sides
        return tuple(count for count in range(2, twice + 1) if twice % count == 0)
    if isinstance(outline, ConcaveOctagon):
        return (2, 4, 8)
    return (2, 8)  # a rectangle: its diagonals make 4 triangles of two shapes


def equal_sizes(parts: int) -> tuple[Fraction, ...]:
    """
    Return the sizes of ``parts`` equal parts of a whole: 1/4 four times for 4.

    Raises ``ValueError`` for fewer than 1 part.
    """
    if parts < 1:
        raise ValueError(f"A whole has at least 1 part, not {parts}.")
    return (Fraction(1, parts),) * parts


def uneven_sizes(parts: int) -> tuple[Fraction, ...]:
    """
    Return the sizes of ``parts`` clearly unequal parts of a whole, smallest first, each larger
    than the one before, up to twice the smallest: 1/3 and 2/3 for 2, and for 5, 4/30, 5/30,
    6/30, 7/30 and 8/30, in lowest terms. A sheet may put them in any order.

    Raises ``ValueError`` for fewer than 2 parts.
    """
    if parts < 2:
        raise ValueError(f"Unequal parts need at least 2 parts, not {parts}.")
    weights = [parts - 1 + index for index in range(parts)]  # up to 2 * (parts - 1)
    total = sum(weights)
    return tuple(Fraction(weight, total) for weight in weights)


def _check_sizes(sizes: Sequence[Fraction]) -> None:
    """Raise ``ValueError`` unless ``sizes`` are above 0 and add up to 1."""
    if not sizes or any(size <= 0 for size in sizes) or sum(sizes) != 1:
        written = ", ".join(str(size) for size in sizes) or "none"
        raise ValueError(f"A whole's parts need sizes above 0 that add up to 1, not {written}.")


@dataclass(frozen=True)
class Strip:
    """
    A bar cut across into parts side by side, numbered from the left, each the share of the
    whole in ``sizes``: ``Strip(equal_sizes(4))`` is cut into fourths.

    Raises ``ValueError`` unless the sizes are above 0 and add up to 1.
    """

    sizes: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        _check_sizes(self.sizes)

    @property
    def parts(self) -> int:
        """How many parts the bar is cut into."""
        return len(self.sizes)

    @property
    def equal_parts(self) -> bool:
        """Whether every part is the same size."""
        return len(set(self.sizes)) == 1


@dataclass(frozen=True)
class Grid:
    """
    A rectangle cut into ``rows`` rows of ``columns`` equal parts, numbered along each row from
    the top left: 2 rows of 4 are eighths.

    Raises ``ValueError`` for fewer than 1 row or column.
    """

    rows: int
    columns: int

    def __post_init__(self) -> None:
        if self.rows < 1 or self.columns < 1:
            raise ValueError(
                f"A grid has at least 1 row and column, not {self.rows} by {self.columns}."
            )

    @property
    def parts(self) -> int:
        """How many parts the rectangle is cut into."""
        return self.rows * self.columns

    @property
    def equal_parts(self) -> bool:
        """Whether every part is the same size: always."""
        return True


@dataclass(frozen=True)
class RadialPartition:
    """
    A shape cut by straight lines from its centre to its edge, into parts numbered clockwise. On
    a regular polygon, a cut to a corner is a radius, and a cut to a side's middle is an apothem.

    The first cut meets the edge at ``start``, and going clockwise from there each part takes the
    share of the edge in ``sizes``. ``start`` is a share of the way clockwise round the edge from
    the shape's first corner: its top one, or the left of the two at the top, such as a square's
    top left or a concave octagon's top-left point. A circle's first corner is its top. A
    partition of one part is the whole shape, uncut.

    The sides take equal shares of the edge, whatever their lengths, so a square's corners are at
    0, 1/4, 1/2 and 3/4, and its sides' middles half way between. Each side of these shapes makes
    a triangle of the same area with the centre: a regular polygon's sides are the same length
    and the same distance from its centre, and so are a concave octagon's, each the mirror image
    of the next; a rectangle's longer sides are nearer its centre in the same proportion as
    they're longer. So each part's area is in proportion to the edge it takes, and equal sizes
    make equal parts. Cut into 4 from 0, a square is cut by its diagonals; into 8, by its radii
    and apothems; and into 4 from 1/8, the middle of its top, by its apothems, into 4 squares. A
    concave octagon's points are at 0, 1/4, 1/2 and 3/4 and its inner corners half way between,
    so cut into 8 from 0, each arm is cut down its middle.

    Raises ``ValueError`` unless the sizes are above 0 and add up to 1, and ``start`` is at
    least 0 and below 1.
    """

    outline: Outline
    sizes: tuple[Fraction, ...]
    start: Fraction = Fraction(0)

    def __post_init__(self) -> None:
        _check_sizes(self.sizes)
        if not 0 <= self.start < 1:
            raise ValueError(
                f"A radial partition's start is at least 0 and below 1, not {self.start}."
            )

    @property
    def parts(self) -> int:
        """How many parts the shape is cut into."""
        return len(self.sizes)

    @property
    def equal_parts(self) -> bool:
        """Whether every part is the same size."""
        return len(set(self.sizes)) == 1


@dataclass(frozen=True)
class SlicedCircle:
    """
    A circle cut by parallel lines, evenly spaced across it, into ``parts`` slices: lines down
    it, with the slices numbered from the left, or ``horizontal`` lines, numbered from the top.
    The slices look alike, but each one nearer the middle is larger, so the parts are equal only
    when there are 2, or 1, the whole circle.

    Raises ``ValueError`` for fewer than 1 part.
    """

    parts: int
    horizontal: bool = False

    def __post_init__(self) -> None:
        if self.parts < 1:
            raise ValueError(f"A whole has at least 1 part, not {self.parts}.")

    @property
    def equal_parts(self) -> bool:
        """Whether every part is the same size: only for 1 or 2 parts."""
        return self.parts <= 2


@dataclass(frozen=True)
class TriangleGrid:
    """
    A triangle with equal sides, pointing up, cut by lines parallel to its sides into ``rows``
    rows of equal small triangles. With 2 rows, joining its sides' middles makes 4.

    The small triangles are numbered along each row from the top, left to right. The top row has
    1, pointing up; the next has 3, pointing up, down and up; and so on: 4 in 2 rows, 9 in 3.

    Raises ``ValueError`` for fewer than 1 row.
    """

    rows: int

    def __post_init__(self) -> None:
        if self.rows < 1:
            raise ValueError(f"A triangle grid has at least 1 row, not {self.rows}.")

    @property
    def parts(self) -> int:
        """How many small triangles there are."""
        return self.rows * self.rows

    @property
    def equal_parts(self) -> bool:
        """Whether every part is the same size: always."""
        return True


class Lattice(StrEnum):
    """How a cut shape's corners are measured. Values are stable identifiers for the API and
    storage."""

    SQUARE = "square"  # across, and down at a right angle
    # across, and down a line 60 degrees from across, so whole numbers make triangles with equal
    # sides: rhombuses, hexagons and trapezoids made of them have corners at whole numbers
    TRIANGLE = "triangle"


# A corner: how far across from the left, and how far down from the top, on a lattice
type Corner = tuple[Fraction | int, Fraction | int]


def _cross(origin: Corner, first: Corner, second: Corner) -> Fraction:
    """Return the cross product of the lines from ``origin`` to ``first`` and to ``second``:
    positive, negative or 0 as ``second`` is to one side of the first line, the other, or on it."""
    (x, y), (x1, y1), (x2, y2) = origin, first, second
    return Fraction(x1 - x) * Fraction(y2 - y) - Fraction(y1 - y) * Fraction(x2 - x)


def _signed_area(corners: Sequence[Corner]) -> Fraction:
    """Return the area inside ``corners``, in order round a shape: positive one way round,
    negative the other."""
    origin = corners[0]
    return (
        sum(
            (_cross(origin, first, second) for first, second in pairwise(corners[1:])),
            Fraction(0),
        )
        / 2
    )


def _area(corners: Sequence[Corner]) -> Fraction:
    """Return the area inside ``corners``, in order round a piece, either way round."""
    return abs(_signed_area(corners))


@dataclass(frozen=True)
class Polygon:
    """
    A whole's outline: its ``corners`` in order round it, measured on ``lattice``. It has no
    dents, so a line between any two points inside it stays inside.

    Raises ``ValueError`` for fewer than 3 corners, no area, or a dent.
    """

    corners: tuple[Corner, ...]
    lattice: Lattice = Lattice.SQUARE

    def __post_init__(self) -> None:
        if len(self.corners) < 3 or _signed_area(self.corners) == 0:
            raise ValueError(
                f"An outline needs 3 or more corners round some area, not {self.corners}."
            )
        way = _signed_area(self.corners) > 0
        turns = zip(
            self.corners,
            (*self.corners[1:], *self.corners[:1]),
            (*self.corners[2:], *self.corners[:2]),
            strict=True,
        )
        if any(
            _cross(first, second, third) != 0 and (_cross(first, second, third) > 0) != way
            for first, second, third in turns
        ):
            raise ValueError(f"An outline has no dents, unlike {self.corners}.")

    def holds(self, corner: Corner) -> bool:
        """Whether ``corner`` is inside the outline or on its edge."""
        way = _signed_area(self.corners) > 0
        sides = zip(self.corners, (*self.corners[1:], self.corners[0]), strict=True)
        return all(
            _cross(start, end, corner) == 0 or (_cross(start, end, corner) > 0) == way
            for start, end in sides
        )


def rectangle(width: int, height: int) -> Polygon:
    """Return a rectangle ``width`` across and ``height`` down, from (0, 0)."""
    return Polygon(((0, 0), (width, 0), (width, height), (0, height)))


# Wholes made of triangles with equal sides, each as small as whole numbers allow
RHOMBUS = Polygon(((0, 0), (1, 0), (1, 1), (0, 1)), Lattice.TRIANGLE)  # 2 triangles, leaning right
PARALLELOGRAM = Polygon(((0, 0), (2, 0), (2, 1), (0, 1)), Lattice.TRIANGLE)  # 4 triangles
HALF_HEXAGON = Polygon(((1, 0), (2, 0), (2, 1), (0, 1)), Lattice.TRIANGLE)  # a trapezoid of 3
EQUILATERAL_TRIANGLE = Polygon(((2, 0), (2, 2), (0, 2)), Lattice.TRIANGLE)  # pointing up, of 4
REGULAR_HEXAGON = Polygon(  # flat at the top and bottom, of 6
    ((1, 0), (2, 0), (2, 1), (1, 2), (0, 2), (0, 1)), Lattice.TRIANGLE
)


@dataclass(frozen=True)
class CutShape:
    """
    A whole, ``outline``, cut by straight lines into ``pieces``, each given by its corners in
    order round it, measured as the outline's are. The pieces are numbered in the order given.
    Their areas come from their corners, exactly, so whether they're equal is worked out, not
    stated. On the triangle lattice, every area is in the same proportion to the page's, so the
    pieces' shares are exact there too.

    Halving a rectangle of two squares corner to corner makes two equal triangles, but the line
    between the squares then cuts each into a small triangle, 1/8 of the rectangle, and a piece 3
    times as large. Two such rectangles side by side make a square of 8 pieces that aren't
    eighths.

    Raises ``ValueError`` for a piece with fewer than 3 corners, no area, or a corner outside the
    outline, or for pieces whose areas don't add up to the outline's.
    """

    outline: Polygon
    pieces: tuple[tuple[Corner, ...], ...]

    def __post_init__(self) -> None:
        for piece in self.pieces:
            if len(piece) < 3 or _area(piece) == 0:
                raise ValueError(f"A piece needs 3 or more corners round some area, not {piece}.")
            if not all(self.outline.holds(corner) for corner in piece):
                raise ValueError(f"A piece's corners are in the outline, unlike {piece}'s.")
        if sum(_area(piece) for piece in self.pieces) != _area(self.outline.corners):
            raise ValueError("The pieces' areas add up to more or less than the outline's.")

    @property
    def parts(self) -> int:
        """How many pieces the whole is cut into."""
        return len(self.pieces)

    @property
    def sizes(self) -> tuple[Fraction, ...]:
        """Each piece's share of the whole, in order."""
        whole = _area(self.outline.corners)
        return tuple(_area(piece) / whole for piece in self.pieces)

    @property
    def equal_parts(self) -> bool:
        """Whether every piece has the same area."""
        return len(set(self.sizes)) == 1


def tiled(tile: CutShape, columns: int, rows: int) -> CutShape:
    """
    Return ``rows`` rows of ``columns`` copies of ``tile``, a cut rectangle from (0, 0), side by
    side as one cut rectangle, numbered tile by tile along each row from the top left: 4 squares,
    each cut corner to corner, make a square of 8 triangles.

    Raises ``ValueError`` for fewer than 1 row or column, or a tile that isn't a rectangle from
    (0, 0) on the square lattice.
    """
    if rows < 1 or columns < 1:
        raise ValueError(f"Tiles go in at least 1 row and column, not {rows} by {columns}.")
    width, height = tile.outline.corners[2]
    if tile.outline != rectangle(int(width), int(height)):
        raise ValueError("Only a rectangle from (0, 0) on the square lattice is tiled.")
    pieces = tuple(
        tuple((x + column * width, y + row * height) for x, y in piece)
        for row in range(rows)
        for column in range(columns)
        for piece in tile.pieces
    )
    return CutShape(rectangle(int(width) * columns, int(height) * rows), pieces)


def _four_corners(outline: Polygon) -> tuple[Corner, Corner, Corner, Corner]:
    """Return ``outline``'s corners, which must be 4."""
    if len(outline.corners) != 4:
        raise ValueError(f"Diagonals cut a shape of 4 corners, not {len(outline.corners)}.")
    first, second, third, fourth = outline.corners
    return first, second, third, fourth


def halved_by_diagonal(outline: Polygon) -> CutShape:
    """
    Return ``outline``, a shape of 4 corners, cut from its first corner to its third: two
    triangles, equal for a rectangle, a rhombus or a parallelogram.

    Raises ``ValueError`` for a shape without 4 corners.
    """
    first, second, third, fourth = _four_corners(outline)
    return CutShape(outline, ((first, second, third), (first, third, fourth)))


def quartered_by_diagonals(outline: Polygon) -> CutShape:
    """
    Return ``outline``, a shape of 4 corners, cut by both its diagonals into 4 triangles meeting
    where they cross, numbered from its first side round. A parallelogram's diagonals halve each
    other, so its 4 have equal areas, in two shapes unless it's a rhombus or a square.

    Raises ``ValueError`` for a shape without 4 corners.
    """
    first, second, third, fourth = _four_corners(outline)
    meet = _crossing(first, third, second, fourth)
    corners = (first, second, third, fourth)
    return CutShape(
        outline,
        tuple((corners[index], corners[(index + 1) % 4], meet) for index in range(4)),
    )


def _crossing(start: Corner, end: Corner, other_start: Corner, other_end: Corner) -> Corner:
    """Return where the line from ``start`` to ``end`` crosses the one from ``other_start`` to
    ``other_end``."""
    (x, y), (x2, y2), (u, v), (u2, v2) = start, end, other_start, other_end
    run, rise = Fraction(x2 - x), Fraction(y2 - y)
    other_run, other_rise = Fraction(u2 - u), Fraction(v2 - v)
    along = (Fraction(u - x) * other_rise - Fraction(v - y) * other_run) / (
        run * other_rise - rise * other_run
    )
    return x + along * run, y + along * rise


def striped(outline: Polygon, count: int, side: int = 0) -> CutShape:
    """
    Return ``outline`` cut by lines parallel to its side from corner ``side`` to the next, evenly
    spaced across it, into ``count`` stripes, numbered from that side. A rectangle's, a
    rhombus's or a parallelogram's stripes are equal; a triangle's, a trapezoid's or a hexagon's
    aren't, though they look as if they might be.

    Raises ``ValueError`` for fewer than 1 stripe or a side the outline doesn't have.
    """
    corners = outline.corners
    if count < 1 or not 0 <= side < len(corners):
        raise ValueError(
            f"Stripes need a count of 1 or more and a side of the outline, not {count} and {side}."
        )
    start, end = corners[side], corners[(side + 1) % len(corners)]
    way = 1 if _signed_area(corners) > 0 else -1

    def height(corner: Corner) -> Fraction:  # how far from the side, in its own units
        return way * _cross(start, end, corner)

    top = max(height(corner) for corner in corners)
    pieces = []
    for index in range(count):
        low, high = top * index / count, top * (index + 1) / count
        piece = _clip(_clip(list(corners), height, low, above=True), height, high, above=False)
        pieces.append(tuple(piece))
    return CutShape(outline, tuple(pieces))


def _clip(
    corners: list[Corner], height: Callable[[Corner], Fraction], level: Fraction, above: bool
) -> list[Corner]:
    """
    Return the part of the shape inside ``corners`` where ``height`` is at least ``level``, if
    ``above``, or at most it, its corners in the same order round it.
    """

    def inside(corner: Corner) -> bool:
        return height(corner) >= level if above else height(corner) <= level

    kept: list[Corner] = []
    for corner, following in zip(corners, (*corners[1:], corners[0]), strict=True):
        if inside(corner):
            kept.append(corner)
        if inside(corner) != inside(following):
            share = (level - height(corner)) / (height(following) - height(corner))
            (x, y), (x2, y2) = corner, following
            kept.append((x + share * (x2 - x), y + share * (y2 - y)))
    # a corner on the level is kept once, not again as the crossing beside it
    unique = [corner for index, corner in enumerate(kept) if corner != kept[index - 1]]
    return unique or kept[:1]


def lattice_triangles(outline: Polygon) -> CutShape:
    """
    Return ``outline``, on the triangle lattice with its corners at whole numbers, cut into the
    lattice's triangles, numbered row by row from the top, left to right: a half hexagon's 3, a
    hexagon's 6.

    Raises ``ValueError`` for an outline on the square lattice, or with a corner off the whole
    numbers.
    """
    if outline.lattice is not Lattice.TRIANGLE or any(
        Fraction(value).denominator != 1 for corner in outline.corners for value in corner
    ):
        raise ValueError(
            "Lattice triangles cut a triangle-lattice outline with whole-number corners."
        )
    xs = [int(x) for x, _ in outline.corners]
    ys = [int(y) for _, y in outline.corners]
    pieces = []
    for row in range(min(ys), max(ys)):
        # each row's triangles, by where their middles fall across the page, left to right
        found = []
        for across in range(min(xs) - (max(ys) - min(ys)), max(xs) + 1):
            pointing_down = ((across, row), (across + 1, row), (across, row + 1))
            pointing_up = ((across + 1, row), (across + 1, row + 1), (across, row + 1))
            for triangle, middle in (
                (pointing_down, (across + Fraction(1, 3), row + Fraction(1, 3))),
                (pointing_up, (across + Fraction(2, 3), row + Fraction(2, 3))),
            ):
                if outline.holds(middle):
                    found.append((middle[0] + middle[1] / 2, triangle))
        pieces += [triangle for _, triangle in sorted(found)]
    return CutShape(outline, tuple(pieces))


# How a whole is cut into parts
type Split = Strip | Grid | RadialPartition | SlicedCircle | TriangleGrid | CutShape


@dataclass(frozen=True)
class AreaModel:
    """
    A whole cut by ``split``, with the parts numbered in ``shaded`` shaded.

    The parts numbered in ``removed`` are left out: the model is the rest of the whole, drawn
    where it would be in the whole and at its size, so that a part is as large as the same part
    of the whole drawn beside it. 4 of a hexagon's 6 triangles, 1 shaded, show 1/4.

    With ``look``, the whole is drawn as that object, cut by ``split``: a pizza is a circle cut
    into slices from its centre, a sandwich a square cut from its centre, a square cake or a
    chocolate bar a grid, its pieces or squares, and a round cake, seen from the side, only
    whole. Without, it's a plain shape.

    Raises ``ValueError`` for a shaded or left-out part the split doesn't have, a part both shaded
    and left out, every part left out, or a look that isn't one of those objects or doesn't suit
    the split.
    """

    split: Split
    shaded: frozenset[int] = frozenset()
    removed: frozenset[int] = frozenset()
    look: DrawnObject | None = None

    def __post_init__(self) -> None:
        if self.look is not None and not _suits(self.look, self.split):
            needs = _LOOK_SPLITS.get(self.look)
            name = self.look.replace("_", " ")
            if needs is None:
                raise ValueError(f"A {name} isn't drawn as a whole cut into parts.")
            raise ValueError(f"A {name} is drawn as {needs}, not {type(self.split).__name__}.")
        for part in self.shaded | self.removed:
            if not 0 <= part < self.split.parts:
                raise ValueError(f"A whole of {self.split.parts} parts has no part {part}.")
        if self.shaded & self.removed:
            raise ValueError(
                f"A part left out can't be shaded: {sorted(self.shaded & self.removed)}."
            )
        if len(self.removed) == self.split.parts:
            raise ValueError("A model leaves out some of its whole's parts, not all of them.")

    @property
    def parts(self) -> int:
        """How many parts the model shows: the whole's, less any left out."""
        return self.split.parts - len(self.removed)


# What each object drawn as a whole is cut as
_LOOK_SPLITS = {
    DrawnObject.PIZZA: "a circle cut from its centre",
    DrawnObject.ROUND_CAKE: "a circle, uncut",
    DrawnObject.SANDWICH: "a square cut from its centre",
    DrawnObject.SQUARE_CAKE: "a grid",
    DrawnObject.CHOCOLATE_BAR: "a grid",
}


def _suits(look: DrawnObject, split: Split) -> bool:
    """Return whether an area model can be drawn as ``look``, cut by ``split``."""
    circle = isinstance(split, RadialPartition) and isinstance(split.outline, Circle)
    match look:
        case DrawnObject.PIZZA:
            return circle
        case DrawnObject.ROUND_CAKE:
            return circle and split.parts == 1
        case DrawnObject.SANDWICH:
            return isinstance(split, RadialPartition) and split.outline == RegularPolygon(4)
        case DrawnObject.SQUARE_CAKE | DrawnObject.CHOCOLATE_BAR:
            return isinstance(split, Grid)
        case _:
            return False


def shaded_fraction(model: AreaModel) -> UnreducedFraction:
    """
    Return the fraction of ``model`` that's shaded, as written: 2 of 8 equal parts is 2/8, and 1
    of 4 parts left of 6 is 1/4.

    Raises ``ValueError`` when the whole's parts aren't equal, because then the shading shows no
    fraction.
    """
    if not model.split.equal_parts:
        raise ValueError("A whole cut into unequal parts shows no fraction.")
    return UnreducedFraction(len(model.shaded), model.parts)


@dataclass(frozen=True)
class FractionWall:
    """
    A fraction wall, called a fraction strip chart in the US: bars of the same width one under
    another, each cut into equal parts: one row for each of ``denominators``, from the top, where
    1 is the whole. With ``labelled``, each part shows its unit fraction, and the whole shows 1.

    Raises ``ValueError`` for no rows, or a denominator below 1.
    """

    denominators: tuple[int, ...]
    labelled: bool = True

    def __post_init__(self) -> None:
        if not self.denominators or min(self.denominators) < 1:
            written = ", ".join(str(denominator) for denominator in self.denominators) or "none"
            raise ValueError(f"A fraction wall needs rows of 1 part or more, not {written}.")
