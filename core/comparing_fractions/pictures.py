"""
The pictures comparing fractions questions show: one for each fraction, all the same shape and
size, or a fraction wall; and wholes left uncut for the student to divide.

Every picture shades its parts from the first, as compared models are: a strip from the left, a
circle clockwise from the top, a grid along its rows from the top left. Each is small enough to
be one of several side by side.
"""

import random
from collections.abc import Collection, Sequence
from math import ceil

from core.comparing_fractions.data import Picture, Representation
from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    CIRCLE_LIMITS,
    GRID_LIMITS,
    STRIP_LIMITS,
    WALL_LIMITS,
    AreaModel,
    Circle,
    ConcaveOctagon,
    FractionWall,
    Grid,
    RadialPartition,
    RegularPolygon,
    Split,
    Strip,
    equal_sizes,
    same_shape_parts,
)
from core.fraction_models.number_lines import (
    LINE_LIMITS,
    FractionLine,
    LengthUnit,
    LinePoint,
)
from core.fraction_models.object_groups import GROUP_LIMITS, ObjectGroup
from core.fraction_models.splits import POLYGONS
from core.written_numbers import UnreducedFraction

GROUP_ROW = 8  # the most objects in a row of a group
WALL_MOST_ROWS = 6  # the most rows of parts a fraction wall shows, below its whole
# Objects a group shows: all but the musical triangle, whose name would read as the shape
GROUP_KINDS = tuple(kind for kind in DrawnObject if kind is not DrawnObject.MUSICAL_TRIANGLE)
# The shapes other than circles that compared models can be, cut from their centres into parts
# of one shape
OTHER_OUTLINES: tuple[RegularPolygon | ConcaveOctagon, ...] = (*POLYGONS, ConcaveOctagon())
# The representations that draw a whole as an area model, which a student can divide
AREA_REPRESENTATIONS = (
    Representation.STRIP,
    Representation.GRID,
    Representation.CIRCLE,
    Representation.OTHER_SHAPE,
)


def can_show(rep: Representation, denominators: Collection[int]) -> bool:
    """
    Return whether ``rep`` can show a fraction over each of ``denominators``, the pictures the
    same shape and size: as many parts as one of several pictures side by side shows easily, a
    grid of at least 2 rows and 2 columns, other shapes one outline cut into each number of
    parts. A wall shows two or more different denominators as its rows, and no picture shows
    anything.
    """
    match rep:
        case Representation.STRIP:
            return max(denominators) <= STRIP_LIMITS.in_a_choice
        case Representation.GRID:
            return all(_grid_shapes(parts) for parts in denominators)
        case Representation.CIRCLE:
            return max(denominators) <= CIRCLE_LIMITS.in_a_choice
        case Representation.OTHER_SHAPE:
            return bool(_outlines(denominators))
        case Representation.GROUP:
            return max(denominators) <= GROUP_LIMITS.in_a_choice
        case Representation.LINE:
            return max(denominators) <= LINE_LIMITS.in_a_choice
        case Representation.WALL:
            return len(set(denominators)) >= 2 and max(denominators) <= WALL_LIMITS.alone
        case _:
            return True


def show(
    rep: Representation,
    fractions: Sequence[UnreducedFraction],
    *,
    kind: DrawnObject | None = None,
    look: DrawnObject | None = None,
    unit: LengthUnit | None = None,
    marking: str | None = None,
) -> tuple[Picture, ...]:
    """
    Return a picture of each of ``fractions`` in ``rep``, which ``can_show`` them and isn't a wall
    or no picture: groups of objects of ``kind``, or of one drawn at random, the same number in a
    row, so that their objects are the same size; area models drawn as ``look``; number lines
    measured in ``unit``, all marked the same way, with ``marking``, "jumps", "bar" or "dot", or
    one of them at random.
    """
    if rep is Representation.GROUP:
        kind = kind or random.choice(GROUP_KINDS)
        per_row = _per_row(max(each.denominator for each in fractions))
        return tuple(
            ObjectGroup(kind, each.denominator, per_row, frozenset(range(each.numerator)))
            for each in fractions
        )
    if rep is Representation.LINE:
        marking = marking or random.choice(("jumps", "bar", "dot"))
        return tuple(_line(each, marking, unit) for each in fractions)
    if rep is Representation.OTHER_SHAPE:
        outline = random.choice(_outlines([each.denominator for each in fractions]))
        return tuple(
            AreaModel(
                RadialPartition(outline, equal_sizes(each.denominator)),
                frozenset(range(each.numerator)),
                look=look,
            )
            for each in fractions
        )
    return tuple(
        AreaModel(_split(rep, each.denominator), frozenset(range(each.numerator)), look=look)
        for each in fractions
    )


def model_options(rep: Representation, fraction: UnreducedFraction) -> list[AreaModel]:
    """Return the ways an area representation shows ``fraction`` alone, shaded from the first
    part: for other shapes, one for each outline that ``can_show`` it; else one."""
    shaded = frozenset(range(fraction.numerator))
    if rep is Representation.OTHER_SHAPE:
        parts = fraction.denominator
        return [
            AreaModel(RadialPartition(outline, equal_sizes(parts)), shaded)
            for outline in _outlines([parts])
        ]
    return [AreaModel(_split(rep, fraction.denominator), shaded)]


def blank(rep: Representation, denominators: Collection[int]) -> Picture:
    """
    Return a whole in ``rep`` left uncut, for the student to divide into each of
    ``denominators``: a strip, a rectangle, a circle, an outline that can be cut into each number
    of parts from its centre into parts of one shape, or a number line showing only 0 and 1.
    ``rep`` is an area representation or a number line that ``can_show`` them.
    """
    match rep:
        case Representation.STRIP:
            return AreaModel(Strip(equal_sizes(1)))
        case Representation.GRID:
            return AreaModel(Grid(1, 1))
        case Representation.CIRCLE:
            return AreaModel(RadialPartition(Circle(), equal_sizes(1)))
        case Representation.OTHER_SHAPE:
            return AreaModel(
                RadialPartition(random.choice(_outlines(denominators)), equal_sizes(1))
            )
        case _:
            return FractionLine(1)


def blank_like(model: AreaModel) -> AreaModel:
    """Return ``model``'s whole uncut: a strip, a rectangle, or its outline."""
    split = model.split
    if isinstance(split, Strip):
        return AreaModel(Strip(equal_sizes(1)))
    if isinstance(split, Grid):
        return AreaModel(Grid(1, 1))
    if isinstance(split, RadialPartition):
        return AreaModel(RadialPartition(split.outline, equal_sizes(1)))
    raise ValueError(f"A compared model is a strip, a grid or cut from its centre, not {split}.")


def can_draw_like(model: AreaModel, parts: int) -> bool:
    """Return whether ``model``'s whole can be cut into ``parts`` equal parts as it's cut, small
    enough to be one picture of several: a grid of at least 2 rows and 2 columns, an outline
    into parts of one shape."""
    split = model.split
    if isinstance(split, Strip):
        return parts <= STRIP_LIMITS.in_a_choice
    if isinstance(split, Grid):
        return bool(_grid_shapes(parts))
    if isinstance(split, RadialPartition):
        if isinstance(split.outline, Circle):
            return parts <= CIRCLE_LIMITS.in_a_choice
        return parts <= CIRCLE_LIMITS.in_a_choice and parts in same_shape_parts(split.outline)
    return False


def like(model: AreaModel, fraction: UnreducedFraction) -> AreaModel:
    """Return ``model``'s whole cut into ``fraction``'s parts as ``model`` is cut, shaded from
    the first part to show it. ``can_draw_like`` must allow the parts."""
    split = model.split
    parts = fraction.denominator
    shaded = frozenset(range(fraction.numerator))
    if isinstance(split, Grid):
        rows, columns = random.choice(_grid_shapes(parts))
        return AreaModel(Grid(rows, columns), shaded)
    if isinstance(split, RadialPartition):
        return AreaModel(RadialPartition(split.outline, equal_sizes(parts)), shaded)
    return AreaModel(Strip(equal_sizes(parts)), shaded)


def largest_showable(rep: Representation, denominators: Collection[int]) -> list[int]:
    """
    Return the most of ``denominators`` that ``rep`` shows together, in order: those it shows
    alone, or for other shapes, those the outline that takes the most of them is cut into. A
    wall shows any it has a row for, and no picture shows them all.
    """
    if rep is Representation.OTHER_SHAPE:
        best: list[int] = []
        for outline in OTHER_OUTLINES:
            fitting = [
                each
                for each in sorted(denominators)
                if each <= CIRCLE_LIMITS.in_a_choice and each in same_shape_parts(outline)
            ]
            if len(fitting) > len(best):
                best = fitting
        return best
    if rep is Representation.WALL:
        return [each for each in sorted(denominators) if each <= WALL_LIMITS.alone]
    return [each for each in sorted(denominators) if can_show(rep, [each])]


def wall(needed: Collection[int], denominators: Sequence[int]) -> FractionWall:
    """
    Return an unlabelled fraction wall: the whole, then a row for each of ``needed``, the
    denominators the question uses, and others of the sheet's ``denominators`` that fit, chosen at
    random, up to ``WALL_MOST_ROWS`` rows of parts, smallest denominator at the top.
    """
    rows = set(needed)
    others = [each for each in denominators if each not in rows and 2 <= each <= WALL_LIMITS.alone]
    room = max(WALL_MOST_ROWS - len(rows), 0)
    rows.update(random.sample(others, min(room, len(others))))
    return FractionWall((1, *sorted(rows)), labelled=False)


def _grid_shapes(parts: int) -> list[tuple[int, int]]:
    """Return the ways ``parts`` equal parts make a grid of at least 2 rows and 2 columns, small
    enough to be one picture of several, as (rows, columns), no more rows than columns."""
    if parts > GRID_LIMITS.in_a_choice:
        return []
    return [
        (rows, parts // rows)
        for rows in range(2, parts + 1)
        if parts % rows == 0 and parts // rows >= rows
    ]


def _outlines(denominators: Collection[int]) -> list[RegularPolygon | ConcaveOctagon]:
    """Return the outlines that can each be cut from their centres into every one of
    ``denominators`` parts of one shape, few enough for one picture of several."""
    if max(denominators) > CIRCLE_LIMITS.in_a_choice:
        return []
    return [
        outline
        for outline in OTHER_OUTLINES
        if all(parts in same_shape_parts(outline) for parts in denominators)
    ]


def _split(rep: Representation, parts: int) -> Split:
    """Return a strip, a grid or a circle cut into ``parts`` equal parts, as ``rep`` is."""
    match rep:
        case Representation.STRIP:
            return Strip(equal_sizes(parts))
        case Representation.GRID:
            rows, columns = random.choice(_grid_shapes(parts))
            return Grid(rows, columns)
        case _:
            return RadialPartition(Circle(), equal_sizes(parts))


def _line(fraction: UnreducedFraction, marking: str, unit: LengthUnit | None) -> FractionLine:
    """Return a number line in ``fraction``'s parts, showing it with ``marking``: jumps from 0,
    a shaded bar from 0, or a dot."""
    parts, count = fraction.denominator, fraction.numerator
    match marking:
        case "jumps":
            return FractionLine(parts, unit=unit, jumps=count)
        case "bar":
            return FractionLine(parts, unit=unit, bar_to=count)
        case _:
            return FractionLine(parts, unit=unit, points=(LinePoint(count),))


def _per_row(count: int) -> int:
    """Return how many objects go in a row of a group of up to ``count``: one row of up to 4,
    else rows of up to ``GROUP_ROW``, as even as they can be."""
    rows = 1 if count <= 4 else max(2, ceil(count / GROUP_ROW))
    return ceil(count / rows)
