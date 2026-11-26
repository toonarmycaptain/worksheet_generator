"""
Tests for a tiles sheet's groups of fractions.

``plan_groups`` is scripted: ``random.sample`` takes the first items, so the kinds of sharing are
tried in the order given, a pair's size before a three's, and the lists of fractions in order;
``random.shuffle`` reverses a list's fractions, so its largest come first.
"""

from collections.abc import Sequence

import pytest

from core.comparing_fractions.data import Representation, Shared
from core.comparing_fractions.tiles import (
    Group,
    Pool,
    capacity,
    fills,
    make_pool,
    plan_groups,
    tops,
)
from core.written_numbers import UnreducedFraction
from tests.helpers import reverse_shuffle, sample_first, sample_last

STRIP, GRID, CIRCLE, OTHER, GROUP, LINE, WALL, NONE = Representation
NUMERATOR, DENOMINATOR = Shared


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


def _over(parts: int) -> Group:
    """Return every fraction over ``parts``, from the least."""
    return tuple(_f(top, parts) for top in range(1, parts + 1))


@pytest.mark.parametrize(
    ("parts", "expected"),
    [
        (2, [1, 2]),
        (24, list(range(1, 25))),
        (30, [*range(1, 24), 30]),  # past 24, 1 to 23 and the whole
    ],
)
def test_tops(parts: int, expected: list[int]) -> None:
    assert tops(parts) == expected


@pytest.mark.parametrize(
    ("reps", "shared", "denominators", "expected"),
    [
        (
            (NONE,),
            (DENOMINATOR,),
            (2, 3),
            Pool((DENOMINATOR,), (_over(2), _over(3)), ()),
        ),
        (
            # by numerator, each from the least
            (NONE,),
            (NUMERATOR,),
            (2, 3),
            Pool(
                (NUMERATOR,),
                (),
                ((_f(1, 3), _f(1, 2)), (_f(2, 3), _f(2, 2)), (_f(3, 3),)),
            ),
        ),
        (
            # a wall shows no single denominator, but any it has a row for together
            (WALL,),
            (NUMERATOR, DENOMINATOR),
            (2, 3),
            Pool(
                (NUMERATOR, DENOMINATOR),
                (),
                ((_f(1, 3), _f(1, 2)), (_f(2, 3), _f(2, 2)), (_f(3, 3),)),
            ),
        ),
        (
            # grids have no halves
            (GRID,),
            (DENOMINATOR,),
            (2, 4),
            Pool((DENOMINATOR,), (_over(4),), ()),
        ),
        (
            # the most of each numerator's fractions one outline shows: a triangle cuts 2 and 3,
            # a square 2 and 8, and the first found is kept, so 1/8 and 3/8 are left out
            (OTHER,),
            (NUMERATOR,),
            (2, 3, 8),
            Pool(
                (NUMERATOR,),
                (),
                (
                    (_f(1, 3), _f(1, 2)),
                    (_f(2, 3), _f(2, 2)),
                    (_f(3, 3),),
                    *((_f(top, 8),) for top in range(4, 9)),
                ),
            ),
        ),
    ],
)
def test_make_pool(
    reps: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    expected: Pool,
) -> None:
    assert make_pool(reps, shared, denominators, sample=False) == expected


@pytest.mark.parametrize(
    ("sample", "drawn_last", "expected"),
    [
        (False, False, list(range(2, 14))),  # the smallest 12, every time
        (True, False, list(range(2, 14))),  # drawn: the first 12
        (True, True, list(range(8, 20))),  # drawn: the last 12
    ],
)
def test_make_pool_takes_twelve_denominators(
    sample: bool, drawn_last: bool, expected: list[int], monkeypatch: pytest.MonkeyPatch
) -> None:
    if drawn_last:
        sample_last(monkeypatch)
    else:
        sample_first(monkeypatch)
    pool = make_pool((NONE,), (DENOMINATOR,), tuple(range(2, 20)), sample)
    assert [group[0].denominator for group in pool.by_denominator] == expected


@pytest.mark.parametrize(
    ("shared", "denominators", "fewest", "expected"),
    [
        ((DENOMINATOR,), (2, 3), 2, 5),
        ((DENOMINATOR,), (2, 3), 4, 0),  # no denominator has four fractions
        ((NUMERATOR,), (2, 3), 2, 4),  # 3/3 has no partner
        ((NUMERATOR, DENOMINATOR), (2, 3), 2, 5),  # by denominator
    ],
)
def test_capacity(
    shared: Sequence[Shared], denominators: Sequence[int], fewest: int, expected: int
) -> None:
    assert capacity(make_pool((NONE,), shared, denominators, sample=False), fewest) == expected


@pytest.mark.parametrize(
    ("shared", "denominators", "total", "fewest", "unused", "expected"),
    [
        ((NUMERATOR,), (2, 3), 0, 2, None, True),
        ((NUMERATOR,), (2, 3), 2, 2, None, True),
        ((NUMERATOR,), (2, 3), 3, 2, None, False),  # two pairs and no three
        ((NUMERATOR,), (2, 3), 4, 2, None, True),
        ((DENOMINATOR,), (4, 6), 7, 4, None, False),  # 4, or 4 to 6, not 7
        ((DENOMINATOR,), (4, 6), 9, 4, None, True),  # 4 and 5
        ((DENOMINATOR,), (2, 3), 2, 2, {_f(1, 2), _f(2, 2), _f(1, 3)}, True),
        ((DENOMINATOR,), (2, 3), 3, 2, {_f(1, 2), _f(2, 2), _f(1, 3)}, False),
    ],
)
def test_fills(
    shared: Sequence[Shared],
    denominators: Sequence[int],
    total: int,
    fewest: int,
    unused: set[UnreducedFraction] | None,
    expected: bool,
) -> None:
    pool = make_pool((NONE,), shared, denominators, sample=False)
    assert fills(pool, total, fewest, unused) is expected


@pytest.mark.parametrize(
    ("shared", "denominators", "total", "fewest", "want_three", "expected"),
    [
        (
            # a pair from halves, then thirds' three
            (DENOMINATOR,),
            (2, 3),
            5,
            2,
            False,
            [_over(2), _over(3)],
        ),
        (
            # a three first when it can be
            (DENOMINATOR,),
            (3, 4),
            5,
            2,
            True,
            [_over(3), (_f(3, 4), _f(4, 4))],
        ),
        (
            # numerator pairs tried first are turned down, since what's left by denominator
            # couldn't then make 3 more
            (NUMERATOR, DENOMINATOR),
            (2, 3),
            5,
            2,
            False,
            [_over(2), _over(3)],
        ),
        (
            # a numerator pair, from the two largest of 1/4, 1/3 and 1/2
            (NUMERATOR, DENOMINATOR),
            (2, 3, 4),
            2,
            2,
            False,
            [(_f(1, 3), _f(1, 2))],
        ),
        (
            # Greatest and least alone: four, then six
            (DENOMINATOR,),
            (4, 6),
            10,
            4,
            False,
            [_over(4), _over(6)],
        ),
    ],
)
def test_plan_groups(
    shared: Sequence[Shared],
    denominators: Sequence[int],
    total: int,
    fewest: int,
    want_three: bool,
    expected: list[Group],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    pool = make_pool((NONE,), shared, denominators, sample=False)
    assert plan_groups(pool, total, fewest, want_three) == expected


def test_plan_groups_error() -> None:
    pool = make_pool((NONE,), (NUMERATOR,), (2, 3), sample=False)
    with pytest.raises(ValueError) as error:
        plan_groups(pool, 3, 2, want_three=False)
    assert str(error.value) == "No groups of at least 2 fractions make 3."
