"""Tests for fraction number lines: their ticks, what's marked on them, and their units."""

from fractions import Fraction

import pytest

from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import (
    UNIT_NAMES,
    FractionLine,
    LengthUnit,
    LinePicture,
    LinePoint,
    tick_fraction,
    tick_positions,
)
from core.written_numbers import UnreducedFraction

UNEQUAL_FOURTHS = (Fraction(1, 6), Fraction(2, 9), Fraction(5, 18), Fraction(1, 3))


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
        # unequal parts: what the tick would be if they were equal
        (FractionLine(4, sizes=UNEQUAL_FOURTHS), 3, UnreducedFraction(3, 4)),
    ],
)
def test_tick_fraction(line: FractionLine, tick: int, fraction: UnreducedFraction) -> None:
    """A tick's fraction is written in the line's parts, not reduced."""
    assert tick_fraction(line, tick) == fraction


@pytest.mark.parametrize(
    ("line", "positions"),
    [
        (FractionLine(4), [Fraction(each, 4) for each in range(5)]),
        (FractionLine(1), [Fraction(0), Fraction(1)]),
        (
            FractionLine(4, sizes=UNEQUAL_FOURTHS),
            [Fraction(0), Fraction(1, 6), Fraction(7, 18), Fraction(2, 3), Fraction(1)],
        ),
        (
            # each whole cut the same unequal way
            FractionLine(2, wholes=2, sizes=(Fraction(1, 3), Fraction(2, 3))),
            [Fraction(0), Fraction(1, 3), Fraction(1), Fraction(4, 3), Fraction(2)],
        ),
    ],
)
def test_tick_positions(line: FractionLine, positions: list[Fraction]) -> None:
    """Each tick is as far along the line as the parts before it, in wholes."""
    assert tick_positions(line) == positions


@pytest.mark.parametrize(
    ("parts", "wholes", "points", "jumps", "arrow_to", "bar_to", "sizes", "pictures", "message"),
    [
        (
            0,
            1,
            (),
            0,
            None,
            None,
            None,
            (),
            "A number line has at least 1 whole of at least 1 part, not 1 of 0.",
        ),
        (
            4,
            0,
            (),
            0,
            None,
            None,
            None,
            (),
            "A number line has at least 1 whole of at least 1 part, not 0 of 4.",
        ),
        (
            4,
            1,
            (LinePoint(5),),
            0,
            None,
            None,
            None,
            (),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (LinePoint(-1),),
            0,
            None,
            None,
            None,
            (),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            # between the last tick and the next
            4,
            1,
            (LinePoint(Fraction(9, 2)),),
            0,
            None,
            None,
            None,
            (),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (),
            5,
            None,
            None,
            None,
            (),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (),
            -1,
            None,
            None,
            None,
            (),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (),
            0,
            None,
            None,
            None,
            (LinePicture(5, DrawnObject.ANT),),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (),
            0,
            None,
            None,
            None,
            (LinePicture(-1, DrawnObject.HOUSE),),
            "A point, jump or picture is past the number line's last tick, 4.",
        ),
        (
            4,
            1,
            (),
            0,
            0,
            None,
            None,
            (),
            "An arrow or bar goes from 0 to a tick from 1 to 4.",
        ),
        (
            4,
            1,
            (),
            0,
            5,
            None,
            None,
            (),
            "An arrow or bar goes from 0 to a tick from 1 to 4.",
        ),
        (
            4,
            1,
            (),
            0,
            None,
            5,
            None,
            (),
            "An arrow or bar goes from 0 to a tick from 1 to 4.",
        ),
        (
            # three sizes for four parts
            4,
            1,
            (),
            0,
            None,
            None,
            (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)),
            (),
            "A line's sizes are 4 shares above 0 making 1.",
        ),
        (
            # making 3/4
            4,
            1,
            (),
            0,
            None,
            None,
            (Fraction(1, 8), Fraction(1, 8), Fraction(1, 4), Fraction(1, 4)),
            (),
            "A line's sizes are 4 shares above 0 making 1.",
        ),
        (
            # a share of 0
            2,
            1,
            (),
            0,
            None,
            None,
            (Fraction(0), Fraction(1)),
            (),
            "A line's sizes are 2 shares above 0 making 1.",
        ),
    ],
)
def test_fraction_line_errors(
    parts: int,
    wholes: int,
    points: tuple[LinePoint, ...],
    jumps: int,
    arrow_to: int | None,
    bar_to: int | None,
    sizes: tuple[Fraction, ...] | None,
    pictures: tuple[LinePicture, ...],
    message: str,
) -> None:
    """A line has a part and a whole, everything on it is on it, and unequal parts make 1."""
    with pytest.raises(ValueError) as error:
        FractionLine(
            parts,
            wholes,
            points=points,
            jumps=jumps,
            arrow_to=arrow_to,
            bar_to=bar_to,
            sizes=sizes,
            pictures=pictures,
        )
    assert str(error.value) == message


def test_every_unit_has_its_names() -> None:
    """Each unit has its singular and plural names, in order."""
    assert list(UNIT_NAMES) == list(LengthUnit)
