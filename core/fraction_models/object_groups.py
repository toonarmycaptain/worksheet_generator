"""
Groups of objects for fractions of a set: 3 of 8 balls filled in show 3/8.
"""

from dataclasses import dataclass

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import PartLimits
from core.written_numbers import UnreducedFraction

GROUP_LIMITS = PartLimits(alone=40, in_a_choice=24)


@dataclass(frozen=True)
class ObjectGroup:
    """
    ``count`` objects of one ``kind`` in rows of ``per_row``, numbered along each row from the
    top left, with those numbered in ``shaded`` filled in. The last row may be shorter: 7 in rows
    of 4 are 4 over 3.

    Raises ``ValueError`` for fewer than 1 object, or 1 in a row, or a shaded object the group
    doesn't have.
    """

    kind: DrawnObject
    count: int
    per_row: int
    shaded: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if self.count < 1 or self.per_row < 1:
            raise ValueError(
                f"A group has at least 1 object, and 1 in a row, not {self.count} in rows of "
                f"{self.per_row}."
            )
        for each in self.shaded:
            if not 0 <= each < self.count:
                raise ValueError(f"A group of {self.count} has no object {each} to fill in.")


def group_fraction(group: ObjectGroup) -> UnreducedFraction:
    """Return the fraction of ``group`` that's filled in, as written: 3 of 8 is 3/8."""
    return UnreducedFraction(len(group.shaded), group.count)
