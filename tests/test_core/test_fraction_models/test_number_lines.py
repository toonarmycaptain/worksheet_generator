"""Tests for fraction number lines: their ticks, what's marked on them, and their units."""

import pytest

from core.fraction_models.number_lines import (
    UNIT_NAMES,
    FractionLine,
    LengthUnit,
    LinePoint,
    tick_fraction,
)
from core.written_numbers import UnreducedFraction


@pytest.mark.parametrize(
    ("line", "last_tick"),
    [
        (FractionLine(4), 4),
        (FractionLine(1), 1),
        (FractionLine(2, wholes=3), 6),
    ],
)
def test_last_tick(line: FractionLine, last_tick: int) -> None:
    """A line has a tick for each part of every whole, after the one at 0."""
    assert line.last_tick == last_tick


@pytest.mark.parametrize(
    ("line", "tick", "fraction"),
    [
        (FractionLine(4), 3, UnreducedFraction(3, 4)),
        (FractionLine(8), 2, UnreducedFraction(2, 8)),
        (FractionLine(2, wholes=2), 4, UnreducedFraction(4, 2)),
    ],
)
def test_tick_fraction(line: FractionLine, tick: int, fraction: UnreducedFraction) -> None:
    """A tick's fraction is written in the line's parts, not reduced."""
    assert tick_fraction(line, tick) == fraction


@pytest.mark.parametrize(
    ("parts", "wholes", "points", "jumps", "arrow_to", "bar_to", "message"),
    [
        (
            0,
            1,
            (),
            0,
            None,
            None,
            "A number line has at least 1 whole of at least 1 part, not 1 of 0.",
        ),
        (
            4,
            0,
            (),
            0,
            None,
            None,
            "A number line has at least 1 whole of at least 1 part, not 0 of 4.",
        ),
        (
            4,
            1,
            (LinePoint(5),),
            0,
            None,
            None,
            "A point or jump is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (LinePoint(-1),),
            0,
            None,
            None,
            "A point or jump is past the number line's last tick, 4.",
        ),
        (4, 1, (), 5, None, None, "A point or jump is past the number line's last tick, 4."),
        (4, 1, (), -1, None, None, "A point or jump is past the number line's last tick, 4."),
        (4, 1, (), 0, 0, None, "An arrow or bar goes from 0 to a tick from 1 to 4."),
        (4, 1, (), 0, 5, None, "An arrow or bar goes from 0 to a tick from 1 to 4."),
        (4, 1, (), 0, None, 5, "An arrow or bar goes from 0 to a tick from 1 to 4."),
    ],
)
def test_fraction_line_errors(
    parts: int,
    wholes: int,
    points: tuple[LinePoint, ...],
    jumps: int,
    arrow_to: int | None,
    bar_to: int | None,
    message: str,
) -> None:
    """A line has a part and a whole, and everything on it is on its ticks."""
    with pytest.raises(ValueError) as error:
        FractionLine(parts, wholes, points=points, jumps=jumps, arrow_to=arrow_to, bar_to=bar_to)
    assert str(error.value) == message


def test_every_unit_has_its_names() -> None:
    """Each unit has its singular and plural names, in order."""
    assert list(UNIT_NAMES) == list(LengthUnit)
