"""Tests for groups of objects, fractions of a set."""

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.object_groups import ObjectGroup, group_fraction
from core.written_numbers import UnreducedFraction


@pytest.mark.parametrize(
    ("group", "fraction"),
    [
        (ObjectGroup(DrawnObject.BASEBALL, 8, 4, frozenset({0, 1, 2})), UnreducedFraction(3, 8)),
        (ObjectGroup(DrawnObject.COUNTER, 6, 6), UnreducedFraction(0, 6)),
    ],
)
def test_group_fraction(group: ObjectGroup, fraction: UnreducedFraction) -> None:
    """The objects filled in over all of them, as written."""
    assert group_fraction(group) == fraction


@pytest.mark.parametrize(
    ("count", "per_row", "shaded", "message"),
    [
        (0, 4, frozenset(), "A group has at least 1 object, and 1 in a row, not 0 in rows of 4."),
        (8, 0, frozenset(), "A group has at least 1 object, and 1 in a row, not 8 in rows of 0."),
        (8, 4, frozenset({8}), "A group of 8 has no object 8 to fill in."),
        (8, 4, frozenset({-1}), "A group of 8 has no object -1 to fill in."),
    ],
)
def test_object_group_errors(
    count: int, per_row: int, shaded: frozenset[int], message: str
) -> None:
    """A group has objects in rows, and only its own objects are filled in."""
    with pytest.raises(ValueError) as error:
        ObjectGroup(DrawnObject.STAR, count, per_row, shaded)
    assert str(error.value) == message
