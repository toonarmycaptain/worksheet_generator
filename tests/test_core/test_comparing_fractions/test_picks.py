"""
Tests for choosing what a comparing fractions question compares.

``pick`` is scripted: ``random.choice`` returns the last item (the last way to choose a set,
then its last set), ``random.shuffle`` reverses the set, and ``random.sample`` takes the first
items (the first denominators or numerators of a long range).
"""

from collections.abc import Sequence

import pytest

from core.comparing_fractions.data import Representation, Shared
from core.comparing_fractions.picks import Need, can_pick, pick, showing
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.helpers import choose_last, reverse_shuffle, sample_first

STRIP, GRID, CIRCLE, OTHER, GROUP, LINE, WALL, NONE = Representation
NUMERATOR, DENOMINATOR = Shared
STACKED, SLASH, SLANTED = FractionStyle


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


@pytest.mark.parametrize(
    ("rep", "denominators", "expected"),
    [
        (GRID, (2, 4, 6, 7), [4, 6]),  # those with a grid of 2 rows or more
        (WALL, (2, 24, 25), [2, 24]),  # those it has a row for
        (NONE, (2, 1_000), [2, 1_000]),
    ],
)
def test_showing(rep: Representation, denominators: Sequence[int], expected: list[int]) -> None:
    assert showing(rep, denominators) == expected


@pytest.mark.parametrize(
    ("rep", "shared", "denominators", "need", "expected"),
    [
        (STRIP, DENOMINATOR, (2,), Need(), True),  # 1/2 and 2/2
        (STRIP, DENOMINATOR, (2,), Need(size=3), False),
        (STRIP, DENOMINATOR, (2,), Need(least_top=2), False),  # only 2/2
        (STRIP, DENOMINATOR, (3,), Need(least_top=2), True),  # 2/3 and 3/3
        (STRIP, NUMERATOR, (2,), Need(), False),  # one denominator
        (STRIP, NUMERATOR, (2, 3), Need(size=3), False),
        (STRIP, NUMERATOR, (30, 40), Need(), False),  # too many parts to show
        (NONE, NUMERATOR, (30, 40), Need(), True),
        (OTHER, NUMERATOR, (3, 8), Need(), False),  # no outline cuts both
        (WALL, NUMERATOR, (2, 3), Need(), True),
        (WALL, DENOMINATOR, (2, 3), Need(), False),  # a wall shows different denominators
        (STRIP, NUMERATOR, (3,), Need(equal=True), True),  # a fraction with itself, 1/3 = 1/3
        (STRIP, NUMERATOR, (1,), Need(equal=True), False),  # short of a whole
        (WALL, DENOMINATOR, (2, 3), Need(equal=True), False),
    ],
)
def test_can_pick(
    rep: Representation, shared: Shared, denominators: Sequence[int], need: Need, expected: bool
) -> None:
    assert can_pick(rep, shared, denominators, need) is expected


@pytest.mark.parametrize(
    ("rep", "shared", "denominators", "need", "used", "expected"),
    [
        # fourths, the last denominator, then 3/4 and 4/4, the last pair, reversed
        (STRIP, DENOMINATOR, (2, 3, 4), Need(), set(), (_f(4, 4), _f(3, 4))),
        # that pair used, the last of the others
        (
            STRIP,
            DENOMINATOR,
            (2, 3, 4),
            Need(),
            {frozenset((_f(3, 4), _f(4, 4)))},
            (_f(4, 4), _f(2, 4)),
        ),
        # every pair used, so any: the last
        (
            STRIP,
            DENOMINATOR,
            (2,),
            Need(),
            {frozenset((_f(1, 2), _f(2, 2)))},
            (_f(2, 2), _f(1, 2)),
        ),
        # thirds and fourths, the last pair of denominators, then numerators up to 3
        (STRIP, NUMERATOR, (2, 3, 4), Need(), set(), (_f(3, 4), _f(3, 3))),
        (
            STRIP,
            NUMERATOR,
            (2, 3, 4, 6),
            Need(size=3),
            set(),
            (_f(3, 6), _f(3, 4), _f(3, 3)),
        ),
        # numerators from 2, for the numerator-as-part-size mistake
        (STRIP, DENOMINATOR, (3,), Need(least_top=2), set(), (_f(3, 3), _f(2, 3))),
        # a fraction with itself, short of a whole: sixths, then 5/6
        (CIRCLE, NUMERATOR, (2, 6), Need(equal=True), set(), (_f(5, 6), _f(5, 6))),
        # more than 12 denominators: two drawn from them, the first two
        (NONE, NUMERATOR, tuple(range(2, 20)), Need(), set(), (_f(2, 3), _f(2, 2))),
        # past 12 parts: two numerators drawn, the first two
        (NONE, DENOMINATOR, (20,), Need(), set(), (_f(2, 20), _f(1, 20))),
    ],
)
def test_pick(
    rep: Representation,
    shared: Shared,
    denominators: Sequence[int],
    need: Need,
    used: set[frozenset[UnreducedFraction]],
    expected: tuple[UnreducedFraction, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The set is picked, in the style asked for, and added to those used."""
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)

    picked = pick(rep, shared, denominators, need, SLASH, used)

    assert (picked, {each.style for each in picked}) == (expected, {SLASH})
    assert frozenset(expected) in used


def test_pick_error() -> None:
    with pytest.raises(ValueError) as error:
        pick(STRIP, NUMERATOR, (2,), Need(), STACKED, set())
    assert str(error.value) == (
        "No fractions fit Need(size=2, equal=False, least_top=1) for strip sharing a numerator."
    )
