"""
Number lines for fractions: a line from 0, each whole cut into equal parts by ticks, and what's
marked on it.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.fraction_models.area_models import PartLimits
from core.written_numbers import UnreducedFraction

# The parts in each whole of a line from 0 to 1, with its ticks labelled only at 0 and 1
LINE_LIMITS = PartLimits(alone=24, in_a_choice=12)
# The same with every tick labelled, which needs room for a fraction under each
LABELLED_LINE_LIMITS = PartLimits(alone=16, in_a_choice=8)


class LengthUnit(StrEnum):
    """A unit of length that a number line can measure in. Values are stable identifiers for the
    API and storage."""

    INCH = "inch"
    FOOT = "foot"
    YARD = "yard"
    MILE = "mile"
    CENTIMETER = "centimeter"
    METER = "meter"
    KILOMETER = "kilometer"


# Each unit's name, singular and plural
UNIT_NAMES: dict[LengthUnit, tuple[str, str]] = {
    LengthUnit.INCH: ("inch", "inches"),
    LengthUnit.FOOT: ("foot", "feet"),
    LengthUnit.YARD: ("yard", "yards"),
    LengthUnit.MILE: ("mile", "miles"),
    LengthUnit.CENTIMETER: ("centimeter", "centimeters"),
    LengthUnit.METER: ("meter", "meters"),
    LengthUnit.KILOMETER: ("kilometer", "kilometers"),
}


class Mark(StrEnum):
    """How a point on a number line is drawn. Values are stable identifiers for the API and
    storage."""

    DOT = "dot"
    STAR = "star"


class TickLabels(StrEnum):
    """Which of a number line's ticks have numbers under them. Values are stable identifiers for
    the API and storage."""

    WHOLES = "wholes"  # 0 and each whole number: 0 and 1
    EVERY_TICK = "every_tick"  # 0, 1/4, 2/4, 3/4 and 1


@dataclass(frozen=True)
class LinePoint:
    """A point on a number line's tick ``tick``, counted from 0, drawn as ``mark``, with
    ``letter`` over it, or no letter."""

    tick: int
    letter: str | None = None
    mark: Mark = Mark.DOT


@dataclass(frozen=True)
class FractionLine:
    """
    A number line from 0 to ``wholes``, each whole cut into ``parts`` equal parts by ticks,
    counted from 0 at the left: a line of fourths from 0 to 1 has ticks 0 to 4.

    ``labels`` says which ticks have numbers under them, and the last whole's number is followed
    by ``unit``'s name, if there's a unit: "1 foot". ``points`` are marked on ticks. Above the
    line, ``jumps`` arcs of one part each go from 0, and an arrow goes from 0 to the tick
    ``arrow_to``, if any. A shaded bar runs along the line from 0 to the tick ``bar_to``, if any.

    Raises ``ValueError`` for fewer than 1 part or whole, fewer than 0 jumps, an arrow or bar
    that doesn't leave 0, or a point, jump, arrow or bar past the last tick.
    """

    parts: int
    wholes: int = 1
    labels: TickLabels = TickLabels.WHOLES
    unit: LengthUnit | None = None
    points: tuple[LinePoint, ...] = ()
    jumps: int = 0
    arrow_to: int | None = None
    bar_to: int | None = None

    def __post_init__(self) -> None:
        if self.parts < 1 or self.wholes < 1:
            raise ValueError(
                "A number line has at least 1 whole of at least 1 part, not "
                f"{self.wholes} of {self.parts}."
            )
        last = self.last_tick
        ends = [point.tick for point in self.points] + [self.jumps]
        if any(not 0 <= end <= last for end in ends):
            raise ValueError(f"A point or jump is past the number line's last tick, {last}.")
        if any(end is not None and not 0 < end <= last for end in (self.arrow_to, self.bar_to)):
            raise ValueError(f"An arrow or bar goes from 0 to a tick from 1 to {last}.")

    @property
    def last_tick(self) -> int:
        """The rightmost tick's number: the parts in every whole."""
        return self.parts * self.wholes


def tick_fraction(line: FractionLine, tick: int) -> UnreducedFraction:
    """Return the fraction at ``line``'s tick ``tick``, as written: tick 3 of fourths is 3/4."""
    return UnreducedFraction(tick, line.parts)
