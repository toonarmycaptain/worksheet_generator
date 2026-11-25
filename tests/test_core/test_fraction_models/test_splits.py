"""Tests for the catalogue of equal splits of shapes besides strips, grids and circles."""

from fractions import Fraction

import pytest

from core.fraction_models.area_models import (
    HALF_HEXAGON,
    PARALLELOGRAM,
    REGULAR_HEXAGON,
    RHOMBUS,
    ConcaveOctagon,
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
    striped,
    tiled,
)
from core.fraction_models.splits import other_shape_splits


def _radial(
    outline: RegularPolygon | Rectangle | ConcaveOctagon, parts: int, start: Fraction = Fraction(0)
) -> RadialPartition:
    """Return ``outline`` cut from its centre into ``parts`` equal parts from ``start``."""
    return RadialPartition(outline, equal_sizes(parts), start)


@pytest.mark.parametrize(
    ("parts", "in_a_choice", "expected"),
    [
        (1, False, ()),
        (
            3,
            False,
            (
                _radial(RegularPolygon(3), 3),
                _radial(RegularPolygon(3), 3, Fraction(1, 6)),  # kites
                _radial(RegularPolygon(6), 3),
                _radial(RegularPolygon(6), 3, Fraction(1, 12)),
                _radial(RegularPolygon(6, on_corner=True), 3),
                _radial(RegularPolygon(6, on_corner=True), 3, Fraction(1, 12)),
                lattice_triangles(HALF_HEXAGON),
                striped(RHOMBUS, 3),
                striped(RHOMBUS, 3, side=1),
                striped(PARALLELOGRAM, 3),
                striped(PARALLELOGRAM, 3, side=1),
            ),
        ),
        (
            5,
            False,
            (
                _radial(RegularPolygon(5), 5),
                _radial(RegularPolygon(5), 5, Fraction(1, 10)),
                striped(RHOMBUS, 5),
                striped(RHOMBUS, 5, side=1),
                striped(PARALLELOGRAM, 5),
                striped(PARALLELOGRAM, 5, side=1),
            ),
        ),
        (
            4,
            True,
            (
                _radial(RegularPolygon(4), 4),
                _radial(RegularPolygon(4), 4, Fraction(1, 8)),
                _radial(RegularPolygon(6), 4),
                _radial(RegularPolygon(6), 4, Fraction(1, 12)),
                _radial(RegularPolygon(6, on_corner=True), 4),
                _radial(RegularPolygon(6, on_corner=True), 4, Fraction(1, 12)),
                _radial(RegularPolygon(8), 4),
                _radial(RegularPolygon(8), 4, Fraction(1, 16)),
                _radial(ConcaveOctagon(Fraction(1, 2)), 4),
                _radial(ConcaveOctagon(Fraction(1, 2)), 4, Fraction(1, 8)),
                _radial(ConcaveOctagon(Fraction(5, 8)), 4),
                _radial(ConcaveOctagon(Fraction(5, 8)), 4, Fraction(1, 8)),
                _radial(ConcaveOctagon(Fraction(3, 4)), 4),
                _radial(ConcaveOctagon(Fraction(3, 4)), 4, Fraction(1, 8)),
                _radial(Rectangle(), 4),
                _radial(Rectangle(), 4, Fraction(1, 8)),
                quartered_by_diagonals(RHOMBUS),
                quartered_by_diagonals(PARALLELOGRAM),
                striped(RHOMBUS, 4),
                striped(RHOMBUS, 4, side=1),
                striped(PARALLELOGRAM, 4),
                striped(PARALLELOGRAM, 4, side=1),
                TriangleGrid(2),
            ),
        ),
        (
            6,
            False,
            (
                _radial(RegularPolygon(3), 6),  # all three heights
                _radial(RegularPolygon(6), 6),
                _radial(RegularPolygon(6), 6, Fraction(1, 12)),
                _radial(RegularPolygon(6, on_corner=True), 6),
                _radial(RegularPolygon(6, on_corner=True), 6, Fraction(1, 12)),
                lattice_triangles(REGULAR_HEXAGON),
                striped(RHOMBUS, 6),
                striped(RHOMBUS, 6, side=1),
                striped(PARALLELOGRAM, 6),
                striped(PARALLELOGRAM, 6, side=1),
            ),
        ),
        (
            # 8 from the side's middle are the same cuts as from the corner, so only once
            8,
            False,
            (
                _radial(RegularPolygon(4), 8),
                _radial(RegularPolygon(8), 8),
                _radial(RegularPolygon(8), 8, Fraction(1, 16)),
                _radial(ConcaveOctagon(Fraction(1, 2)), 8),
                _radial(ConcaveOctagon(Fraction(5, 8)), 8),
                _radial(ConcaveOctagon(Fraction(3, 4)), 8),
                _radial(Rectangle(), 8),
                tiled(halved_by_diagonal(rectangle(1, 1)), 2, 2),
                striped(RHOMBUS, 8),
                striped(RHOMBUS, 8, side=1),
                striped(PARALLELOGRAM, 8),
                striped(PARALLELOGRAM, 8, side=1),
            ),
        ),
        (
            # stripes stop at 8 in a choice, and triangle grids at 9
            9,
            True,
            (TriangleGrid(3),),
        ),
        (
            16,
            False,
            (_radial(RegularPolygon(8), 16), TriangleGrid(4)),
        ),
        (
            # a circle's limit, in a choice
            16,
            True,
            (_radial(RegularPolygon(8), 16),),
        ),
        (13, False, ()),
    ],
)
def test_other_shape_splits(parts: int, in_a_choice: bool, expected: tuple[Split, ...]) -> None:
    assert other_shape_splits(parts, in_a_choice) == expected
