"""
Tests for the pictures comparing fractions questions show.

Where a picture is chosen at random, ``random.choice`` returns the last item: the xylophone of
the objects a group shows, a dot of the ways a line marks a fraction, the last outline that cuts
every count, the grid with the most rows, and the last other denominators a wall adds
(``random.sample`` takes the first).
"""

from collections.abc import Collection, Sequence

import pytest

from core.comparing_fractions.data import Picture, Representation
from core.comparing_fractions.pictures import (
    blank,
    blank_like,
    can_draw_like,
    can_show,
    largest_showable,
    like,
    model_options,
    show,
    wall,
)
from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    Circle,
    ConcaveOctagon,
    FractionWall,
    Grid,
    RadialPartition,
    RegularPolygon,
    SlicedCircle,
    Strip,
    equal_sizes,
)
from core.fraction_models.number_lines import FractionLine, LengthUnit, LinePoint
from core.fraction_models.object_groups import ObjectGroup
from core.written_numbers import UnreducedFraction
from tests.helpers import choose_last, sample_first

STRIP, GRID, CIRCLE, OTHER, GROUP, LINE, WALL, NONE = Representation
HEXAGON_ON_CORNER = RegularPolygon(6, on_corner=True)


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


def _shaded(count: int) -> frozenset[int]:
    """Return the first ``count`` parts, shaded."""
    return frozenset(range(count))


@pytest.mark.parametrize(
    ("rep", "denominators", "expected"),
    [
        (STRIP, (8, 24), True),
        (STRIP, (25,), False),  # too many parts for one of several pictures
        (GRID, (4, 6, 8), True),  # 2 by 2, 2 by 3, 2 by 4
        (GRID, (2,), False),  # one row
        (GRID, (7,), False),  # one row
        (GRID, (25,), False),
        (CIRCLE, (16,), True),
        (CIRCLE, (17,), False),
        (OTHER, (3, 6), True),  # a triangle or a hexagon
        (OTHER, (3, 8), False),  # no outline cuts both into parts of one shape
        (OTHER, (24,), False),  # too many parts, though a hexagon cuts 12
        (GROUP, (24,), True),
        (GROUP, (25,), False),
        (LINE, (12,), True),
        (LINE, (13,), False),
        (WALL, (2, 3), True),
        (WALL, (3, 3), False),  # a wall shows different denominators
        (WALL, (2, 25), False),
        (NONE, (1_000,), True),
    ],
)
def test_can_show(rep: Representation, denominators: Collection[int], expected: bool) -> None:
    assert can_show(rep, denominators) is expected


@pytest.mark.parametrize(
    ("rep", "fractions", "kind", "look", "unit", "marking", "expected"),
    [
        (
            STRIP,
            (_f(1, 3), _f(2, 6)),
            None,
            None,
            None,
            None,
            (
                AreaModel(Strip(equal_sizes(3)), _shaded(1)),
                AreaModel(Strip(equal_sizes(6)), _shaded(2)),
            ),
        ),
        (
            # 12 parts as 3 rows of 4, the grid with the most rows
            GRID,
            (_f(5, 12),),
            None,
            None,
            None,
            None,
            (AreaModel(Grid(3, 4), _shaded(5)),),
        ),
        (
            # drawn as a story's pizza
            CIRCLE,
            (_f(3, 8), _f(3, 6)),
            None,
            DrawnObject.PIZZA,
            None,
            None,
            (
                AreaModel(
                    RadialPartition(Circle(), equal_sizes(8)), _shaded(3), look=DrawnObject.PIZZA
                ),
                AreaModel(
                    RadialPartition(Circle(), equal_sizes(6)), _shaded(3), look=DrawnObject.PIZZA
                ),
            ),
        ),
        (
            # one outline for both, the last of those that cut 2 and 3
            OTHER,
            (_f(1, 2), _f(1, 3)),
            None,
            None,
            None,
            None,
            (
                AreaModel(RadialPartition(HEXAGON_ON_CORNER, equal_sizes(2)), _shaded(1)),
                AreaModel(RadialPartition(HEXAGON_ON_CORNER, equal_sizes(3)), _shaded(1)),
            ),
        ),
        (
            # the same number in a row, from the larger group: 2 rows of 4
            GROUP,
            (_f(3, 6), _f(3, 8)),
            None,
            None,
            None,
            None,
            (
                ObjectGroup(DrawnObject.XYLOPHONE, 6, 4, _shaded(3)),
                ObjectGroup(DrawnObject.XYLOPHONE, 8, 4, _shaded(3)),
            ),
        ),
        (
            # a story's objects, up to 4 in one row
            GROUP,
            (_f(1, 3), _f(1, 4)),
            DrawnObject.COOKIE,
            None,
            None,
            None,
            (
                ObjectGroup(DrawnObject.COOKIE, 3, 4, _shaded(1)),
                ObjectGroup(DrawnObject.COOKIE, 4, 4, _shaded(1)),
            ),
        ),
        (
            # a dot, the last way to mark
            LINE,
            (_f(3, 4),),
            None,
            None,
            None,
            None,
            (FractionLine(4, points=(LinePoint(3),)),),
        ),
        (
            LINE,
            (_f(1, 2), _f(2, 2)),
            None,
            None,
            LengthUnit.FOOT,
            "jumps",
            (
                FractionLine(2, unit=LengthUnit.FOOT, jumps=1),
                FractionLine(2, unit=LengthUnit.FOOT, jumps=2),
            ),
        ),
        (
            LINE,
            (_f(5, 8),),
            None,
            None,
            None,
            "bar",
            (FractionLine(8, bar_to=5),),
        ),
    ],
)
def test_show(
    rep: Representation,
    fractions: Sequence[UnreducedFraction],
    kind: DrawnObject | None,
    look: DrawnObject | None,
    unit: LengthUnit | None,
    marking: str | None,
    expected: tuple[Picture, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choose_last(monkeypatch)
    assert show(rep, fractions, kind=kind, look=look, unit=unit, marking=marking) == expected


@pytest.mark.parametrize(
    ("rep", "denominators", "expected"),
    [
        (STRIP, (3, 4), AreaModel(Strip(equal_sizes(1)))),
        (GRID, (4, 6), AreaModel(Grid(1, 1))),
        (CIRCLE, (3, 4), AreaModel(RadialPartition(Circle(), equal_sizes(1)))),
        # the last outline that cuts both 2 and 4 into parts of one shape
        (OTHER, (2, 4), AreaModel(RadialPartition(ConcaveOctagon(), equal_sizes(1)))),
        (LINE, (3, 4), FractionLine(1)),
    ],
)
def test_blank(
    rep: Representation,
    denominators: Collection[int],
    expected: Picture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choose_last(monkeypatch)
    assert blank(rep, denominators) == expected


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (AreaModel(Strip(equal_sizes(6)), _shaded(4)), AreaModel(Strip(equal_sizes(1)))),
        (AreaModel(Grid(2, 3), _shaded(4)), AreaModel(Grid(1, 1))),
        (
            AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(8)), _shaded(4)),
            AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(1))),
        ),
    ],
)
def test_blank_like(model: AreaModel, expected: AreaModel) -> None:
    assert blank_like(model) == expected


def test_blank_like_error() -> None:
    model = AreaModel(SlicedCircle(4))
    with pytest.raises(ValueError) as error:
        blank_like(model)
    assert str(error.value).startswith("A compared model is a strip, a grid or cut from its")


@pytest.mark.parametrize(
    ("model", "parts", "expected"),
    [
        (AreaModel(Strip(equal_sizes(6))), 24, True),
        (AreaModel(Strip(equal_sizes(6))), 25, False),
        (AreaModel(Grid(2, 3)), 8, True),  # 2 by 4
        (AreaModel(Grid(2, 3)), 5, False),  # one row
        (AreaModel(RadialPartition(Circle(), equal_sizes(6))), 16, True),
        (AreaModel(RadialPartition(Circle(), equal_sizes(6))), 17, False),
        (AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(6))), 4, True),
        (AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(6))), 5, False),  # odd shapes
        (AreaModel(RadialPartition(RegularPolygon(8), equal_sizes(8))), 16, True),
        (AreaModel(RadialPartition(RegularPolygon(8), equal_sizes(8))), 32, False),  # too many
        (AreaModel(SlicedCircle(4)), 2, False),  # not a compared model
    ],
)
def test_can_draw_like(model: AreaModel, parts: int, expected: bool) -> None:
    assert can_draw_like(model, parts) is expected


@pytest.mark.parametrize(
    ("model", "fraction", "expected"),
    [
        (
            AreaModel(Strip(equal_sizes(6)), _shaded(4)),
            _f(3, 8),
            AreaModel(Strip(equal_sizes(8)), _shaded(3)),
        ),
        (
            # 12 parts as 3 rows of 4, the grid with the most rows
            AreaModel(Grid(2, 3), _shaded(4)),
            _f(5, 12),
            AreaModel(Grid(3, 4), _shaded(5)),
        ),
        (
            AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(6)), _shaded(4)),
            _f(1, 3),
            AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(3)), _shaded(1)),
        ),
    ],
)
def test_like(
    model: AreaModel,
    fraction: UnreducedFraction,
    expected: AreaModel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    choose_last(monkeypatch)
    assert like(model, fraction) == expected


@pytest.mark.parametrize(
    ("rep", "denominators", "expected"),
    [
        (STRIP, (24, 2, 30), [2, 24]),  # in order, those one of several pictures shows
        (GRID, (2, 4, 6, 7), [4, 6]),
        (OTHER, (2, 3, 4, 6, 8), [2, 3, 4, 6]),  # the hexagon's, which takes the most
        (OTHER, (17, 20), []),
        (WALL, (2, 24, 25), [2, 24]),  # any it has a row for
        (NONE, (2, 1_000), [2, 1_000]),
    ],
)
def test_largest_showable(
    rep: Representation, denominators: Collection[int], expected: list[int]
) -> None:
    assert largest_showable(rep, denominators) == expected


@pytest.mark.parametrize(
    ("rep", "fraction", "expected"),
    [
        (STRIP, _f(3, 4), [AreaModel(Strip(equal_sizes(4)), _shaded(3))]),
        (
            # every outline that cuts 3 into parts of one shape
            OTHER,
            _f(2, 3),
            [
                AreaModel(RadialPartition(outline, equal_sizes(3)), _shaded(2))
                for outline in (RegularPolygon(3), RegularPolygon(6), HEXAGON_ON_CORNER)
            ],
        ),
    ],
)
def test_model_options(
    rep: Representation, fraction: UnreducedFraction, expected: list[AreaModel]
) -> None:
    assert model_options(rep, fraction) == expected


@pytest.mark.parametrize(
    ("needed", "denominators", "expected"),
    [
        # the rows asked for, then others of the sheet's, smallest at the top
        ((3, 2), (2, 3, 4, 6, 8), FractionWall((1, 2, 3, 4, 6, 8), labelled=False)),
        # at most 6 rows of parts, the others taken in the sheet's order; none past 24
        (
            (5,),
            (2, 3, 4, 6, 8, 10, 12, 30),
            FractionWall((1, 2, 3, 4, 5, 6, 8), labelled=False),
        ),
        # no room left
        ((2, 3, 4, 5, 6, 7), (8,), FractionWall((1, 2, 3, 4, 5, 6, 7), labelled=False)),
    ],
)
def test_wall(
    needed: Collection[int],
    denominators: Sequence[int],
    expected: FractionWall,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_first(monkeypatch)
    assert wall(needed, denominators) == expected
