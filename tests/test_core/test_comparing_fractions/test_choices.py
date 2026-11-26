"""
Tests for comparing fractions questions' multiple-choice options.

Each test scripts ``random``: ``random.choice`` returns the last item, ``random.shuffle``
reverses the list, ``random.sample`` takes the first items, and ``random.random`` returns the
case's number: 0.0 makes every "one time in n" happen (a comparison kept as written, another
pair shown twice, the grid of explanations, a part-size reason, an answer that stands out), and
0.99 none of them.
"""

from collections.abc import Sequence

import pytest

from core.comparing_fractions.choices import (
    bare_comparisons,
    either_way,
    explanation,
    explanation_choices,
    is_true,
    less_greater_choices,
    less_greater_shows_choices,
    less_greater_ways,
    pick_choices,
    pictured_comparisons,
    reason_choices,
    right_reason,
    story_choices,
    symbol,
    true_comparison,
)
from core.comparing_fractions.data import (
    CANT_TELL,
    SAME,
    BiggerNumber,
    Comparison,
    Explanation,
    PartSize,
    PartsOf,
    Pick,
    Picture,
    Reason,
    SameCount,
    Shared,
    StoryChoice,
    StoryForm,
    StoryReason,
    Verdict,
)
from core.fraction_models.area_models import AreaModel, Strip, equal_sizes
from core.fraction_models.number_lines import FractionLine
from core.written_numbers import UnreducedFraction
from tests.helpers import choose_last, random_always_returns, reverse_shuffle, sample_first

NUMERATOR, DENOMINATOR = Shared
REASONS, WHO_SYMBOL, PLAIN = StoryForm
AHEAD, SAME_VERDICT, CANT_TELL_VERDICT = Verdict
AREA = (AreaModel(Strip(equal_sizes(6))),)
JUMPS = (FractionLine(6, jumps=3), FractionLine(6, jumps=1))
DOTS = (FractionLine(6), FractionLine(6))
NAMES = ("Ana", "Ben")


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


def _c(left: UnreducedFraction, mark: str, right: UnreducedFraction) -> Comparison:
    """Return ``left`` compared with ``right`` by ``mark``."""
    return Comparison(left, mark, right)


def _script(monkeypatch: pytest.MonkeyPatch, drawn: float) -> None:
    """Script ``random`` as the module docstring says."""
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    random_always_returns(monkeypatch, drawn)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(_f(1, 2), _f(1, 3), ">"), (_f(1, 3), _f(2, 6), "="), (_f(3, 8), _f(5, 8), "<")],
)
def test_symbol(left: UnreducedFraction, right: UnreducedFraction, expected: str) -> None:
    assert symbol(left, right) == expected


@pytest.mark.parametrize(
    ("comparison", "expected"),
    [(_c(_f(1, 2), ">", _f(1, 3)), True), (_c(_f(1, 2), "=", _f(1, 3)), False)],
)
def test_is_true(comparison: Comparison, expected: bool) -> None:
    assert is_true(comparison) is expected


@pytest.mark.parametrize(
    ("drawn", "expected_either", "expected_true"),
    [
        # kept as written, and the pair's own order
        (0.0, _c(_f(1, 2), ">", _f(1, 3)), _c(_f(1, 2), ">", _f(1, 3))),
        # the other way round, the symbol mirrored
        (0.99, _c(_f(1, 3), "<", _f(1, 2)), _c(_f(1, 3), "<", _f(1, 2))),
    ],
)
def test_either_way_and_true_comparison(
    drawn: float,
    expected_either: Comparison,
    expected_true: Comparison,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    assert (
        either_way(_c(_f(1, 2), ">", _f(1, 3))),
        true_comparison((_f(1, 2), _f(1, 3))),
    ) == (expected_either, expected_true)


@pytest.mark.parametrize(
    ("pair", "pictures", "expected"),
    [
        # flipped, "=", and the unshaded parts of 1/6 read as 5/6
        (
            (_f(3, 6), _f(1, 6)),
            AREA,
            (_c(_f(3, 6), "<", _f(1, 6)), _c(_f(3, 6), "=", _f(1, 6)), _c(_f(3, 6), ">", _f(5, 6))),
        ),
        # equal fractions: both > and < are wrong
        (
            (_f(3, 8), _f(3, 8)),
            AREA,
            (_c(_f(3, 8), "<", _f(3, 8)), _c(_f(3, 8), ">", _f(3, 8)), _c(_f(3, 8), ">", _f(5, 8))),
        ),
        # a whole has no unshaded parts and a half's are 1/2 again, so the ticks are counted
        (
            (_f(2, 2), _f(1, 2)),
            AREA,
            (_c(_f(2, 2), "<", _f(1, 2)), _c(_f(2, 2), "=", _f(1, 2)), _c(_f(2, 2), "<", _f(1, 3))),
        ),
        # jumps counted as wholes: 3 jumps and 1, "1/3 > 1/1"
        (
            (_f(3, 6), _f(1, 6)),
            JUMPS,
            (_c(_f(3, 6), "<", _f(1, 6)), _c(_f(3, 6), "=", _f(1, 6)), _c(_f(1, 3), ">", _f(1, 1))),
        ),
        # dots: the ticks counted instead of the parts
        (
            (_f(3, 6), _f(1, 6)),
            DOTS,
            (_c(_f(3, 6), "<", _f(1, 6)), _c(_f(3, 6), "=", _f(1, 6)), _c(_f(3, 6), "<", _f(1, 7))),
        ),
        # 2/3's ticks would read as 2/4, the other fraction, so 2/4's are counted: 2/5
        (
            (_f(2, 4), _f(2, 3)),
            DOTS,
            (_c(_f(2, 4), ">", _f(2, 3)), _c(_f(2, 4), "=", _f(2, 3)), _c(_f(2, 5), ">", _f(2, 3))),
        ),
    ],
)
def test_pictured_comparisons(
    pair: tuple[UnreducedFraction, UnreducedFraction],
    pictures: Sequence[Picture],
    expected: tuple[Comparison, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, 0.99)
    assert pictured_comparisons(pair, pictures) == expected


@pytest.mark.parametrize(
    ("drawn", "pair", "shared", "denominators", "expected"),
    [
        # another pair shown twice: 3/4 and 3/3, the larger denominator taken for the larger
        # fraction and taken for equal; then a same-numerator pair taken for equal
        (
            0.0,
            (_f(2, 3), _f(2, 4)),
            (NUMERATOR,),
            (2, 3, 4),
            (_c(_f(3, 4), ">", _f(3, 3)), _c(_f(3, 4), "=", _f(3, 3)), _c(_f(1, 4), "=", _f(1, 3))),
        ),
        # the answer's pair the wrong way round
        (
            0.99,
            (_f(2, 3), _f(2, 4)),
            (NUMERATOR,),
            (2, 3, 4),
            (_c(_f(2, 4), ">", _f(2, 3)), _c(_f(3, 4), "=", _f(3, 3)), _c(_f(1, 4), ">", _f(1, 3))),
        ),
        # a shared denominator's mistakes: taken for equal, a larger numerator for smaller
        (
            0.0,
            (_f(2, 3), _f(2, 4)),
            (NUMERATOR, DENOMINATOR),
            (2, 3, 4),
            (_c(_f(3, 4), "=", _f(4, 4)), _c(_f(4, 4), "<", _f(3, 4)), _c(_f(4, 4), "<", _f(2, 4))),
        ),
        # equal fractions are never shown twice by another pair
        (
            0.0,
            (_f(3, 8), _f(3, 8)),
            (NUMERATOR, DENOMINATOR),
            (8,),
            (_c(_f(3, 8), "<", _f(3, 8)), _c(_f(8, 8), "<", _f(7, 8)), _c(_f(6, 8), "=", _f(8, 8))),
        ),
        # halves and thirds run out of pairs: fifths fill in
        (
            0.0,
            (_f(1, 2), _f(1, 3)),
            (NUMERATOR,),
            (2, 3),
            (_c(_f(2, 3), ">", _f(2, 2)), _c(_f(2, 3), "=", _f(2, 2)), _c(_f(4, 5), "=", _f(5, 5))),
        ),
        # more than 12 denominators: pairs from 12 of them, the first 12
        (
            0.0,
            (_f(1, 2), _f(1, 3)),
            (NUMERATOR,),
            tuple(range(2, 40)),
            (
                _c(_f(12, 13), ">", _f(12, 12)),
                _c(_f(12, 13), "=", _f(12, 12)),
                _c(_f(11, 13), "=", _f(11, 12)),
            ),
        ),
    ],
)
def test_bare_comparisons(
    drawn: float,
    pair: tuple[UnreducedFraction, UnreducedFraction],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    expected: tuple[Comparison, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    assert bare_comparisons(pair, shared, denominators) == expected


@pytest.mark.parametrize(
    ("comparison", "expected"),
    [
        (_c(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, larger=True)),
        (_c(_f(5, 8), "<", _f(5, 6)), PartSize(6, 8, larger=True)),
        (_c(_f(6, 8), "<", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), greater=False)),
    ],
)
def test_right_reason(comparison: Comparison, expected: Reason) -> None:
    assert right_reason(comparison) == expected


@pytest.mark.parametrize(
    ("drawn", "pair", "expected"),
    [
        (0.0, (_f(5, 6), _f(5, 8)), Explanation(_c(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, True))),
        (
            0.99,
            (_f(6, 8), _f(8, 8)),
            Explanation(_c(_f(8, 8), ">", _f(6, 8)), PartsOf(_f(8, 8), _f(6, 8), greater=True)),
        ),
    ],
)
def test_explanation(
    drawn: float,
    pair: tuple[UnreducedFraction, UnreducedFraction],
    expected: Explanation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    assert explanation(pair, pictured=False) == expected


FIVE_SIXTHS = Explanation(_c(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, larger=True))
SIX_EIGHTHS = Explanation(_c(_f(6, 8), "<", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), greater=False))
ONE_EIGHTH = Explanation(_c(_f(1, 8), "<", _f(3, 8)), PartsOf(_f(1, 8), _f(3, 8), greater=False))


@pytest.mark.parametrize(
    ("drawn", "answer", "pictures", "expected"),
    [
        # the grid: the other parts called larger, and the flipped symbol with each reason
        (
            0.0,
            FIVE_SIXTHS,
            (),
            (
                Explanation(_c(_f(5, 6), ">", _f(5, 8)), PartSize(8, 6, larger=True)),
                Explanation(_c(_f(5, 6), "<", _f(5, 8)), PartSize(8, 6, larger=True)),
                Explanation(_c(_f(5, 6), "<", _f(5, 8)), PartSize(6, 8, larger=True)),
            ),
        ),
        # the mix: the mistaken reason, the denominators compared, "=" for the same numerator
        (
            0.99,
            FIVE_SIXTHS,
            (),
            (
                Explanation(_c(_f(5, 6), ">", _f(5, 8)), PartSize(8, 6, larger=True)),
                Explanation(_c(_f(5, 8), ">", _f(5, 6)), BiggerNumber(8, 6, greater=True)),
                Explanation(_c(_f(5, 6), "=", _f(5, 8)), SameCount(5, total=False, pictured=False)),
            ),
        ),
        # pictured: the unshaded parts, 1/6 and 3/8, with a true-sounding reason
        (
            0.99,
            FIVE_SIXTHS,
            AREA,
            (
                Explanation(_c(_f(5, 6), ">", _f(5, 8)), PartSize(8, 6, larger=True)),
                Explanation(_c(_f(1, 6), ">", _f(3, 8)), PartSize(6, 8, larger=True)),
                Explanation(_c(_f(5, 8), ">", _f(5, 6)), BiggerNumber(8, 6, greater=True)),
            ),
        ),
        # the grid for a shared denominator: numerators read as part sizes
        (
            0.0,
            SIX_EIGHTHS,
            (),
            (
                Explanation(_c(_f(6, 8), "<", _f(8, 8)), PartSize(6, 8, larger=False)),
                Explanation(_c(_f(6, 8), ">", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), True)),
                Explanation(_c(_f(6, 8), ">", _f(8, 8)), PartSize(6, 8, larger=True)),
            ),
        ),
        # the mix on number lines: "=" for the same parts in all, unpictured; a whole has no
        # unshaded parts
        (
            0.99,
            SIX_EIGHTHS,
            DOTS,
            (
                Explanation(_c(_f(6, 8), "<", _f(8, 8)), PartSize(6, 8, larger=False)),
                Explanation(_c(_f(6, 8), "=", _f(8, 8)), SameCount(8, total=True, pictured=False)),
                Explanation(_c(_f(6, 8), ">", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), True)),
            ),
        ),
        # a numerator of 1 names no parts, so no mistaken reason: the mix, with the pictures'
        # unshaded parts, 7/8 and 5/8
        (
            0.0,
            ONE_EIGHTH,
            AREA,
            (
                Explanation(_c(_f(7, 8), "<", _f(5, 8)), PartsOf(_f(7, 8), _f(5, 8), False)),
                Explanation(_c(_f(1, 8), "=", _f(3, 8)), SameCount(8, total=True, pictured=True)),
                Explanation(_c(_f(1, 8), ">", _f(3, 8)), PartsOf(_f(1, 8), _f(3, 8), True)),
            ),
        ),
    ],
)
def test_explanation_choices(
    drawn: float,
    answer: Explanation,
    pictures: Sequence[Picture],
    expected: tuple[Explanation, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    assert explanation_choices(answer, pictures) == expected


def _s(
    verdict: Verdict,
    who: str | None,
    reason: StoryReason,
    claim: Comparison | None = None,
    brief: bool = False,
) -> StoryChoice:
    """Return a word problem's statement."""
    return StoryChoice(verdict, who, reason, claim, brief)


THIRD, FOURTH = _f(1, 3), _f(1, 4)


@pytest.mark.parametrize(
    ("drawn", "form", "pair", "answer", "winner", "same_size", "greater", "expected"),
    [
        (
            # Ana, because thirds are larger; Ben with the denominators compared, can't tell,
            # equal
            0.0,
            REASONS,
            (THIRD, FOURTH),
            "Ana",
            "Ana",
            True,
            True,
            (
                _s(AHEAD, "Ana", StoryReason.PART_SIZE, _c(THIRD, ">", FOURTH)),
                (
                    _s(AHEAD, "Ben", StoryReason.DENOMINATOR, _c(FOURTH, ">", THIRD)),
                    _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                    _s(SAME_VERDICT, None, StoryReason.EQUAL, _c(THIRD, "=", FOURTH)),
                ),
            ),
        ),
        (
            # a shared denominator: the fractions compared, Ben's the greater
            0.99,
            REASONS,
            (_f(3, 8), _f(5, 8)),
            "Ben",
            "Ben",
            True,
            True,
            (
                _s(AHEAD, "Ben", StoryReason.FRACTION, _c(_f(5, 8), ">", _f(3, 8))),
                (
                    _s(AHEAD, "Ana", StoryReason.FRACTION, _c(_f(3, 8), ">", _f(5, 8))),
                    _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                    _s(SAME_VERDICT, None, StoryReason.EQUAL, _c(_f(3, 8), "=", _f(5, 8))),
                ),
            ),
        ),
        (
            # the same: each person ahead, or can't tell, are wrong
            0.99,
            REASONS,
            (_f(3, 8), _f(3, 8)),
            SAME,
            None,
            True,
            True,
            (
                _s(SAME_VERDICT, None, StoryReason.EQUAL, _c(_f(3, 8), "=", _f(3, 8))),
                (
                    _s(AHEAD, "Ana", StoryReason.NONE),
                    _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                    _s(AHEAD, "Ben", StoryReason.NONE),
                ),
            ),
        ),
        (
            # wholes of different sizes: the greater fraction taken for more is wrong
            0.99,
            REASONS,
            (_f(5, 8), _f(3, 8)),
            CANT_TELL,
            "Ana",
            False,
            True,
            (
                _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                (
                    _s(AHEAD, "Ben", StoryReason.FRACTION, _c(_f(3, 8), ">", _f(5, 8))),
                    _s(AHEAD, "Ana", StoryReason.FRACTION, _c(_f(5, 8), ">", _f(3, 8))),
                    _s(SAME_VERDICT, None, StoryReason.EQUAL, _c(_f(5, 8), "=", _f(3, 8))),
                ),
            ),
        ),
        (
            # who and symbol, "Who eats less?": Ben, because Ana's 1/3 > Ben's 1/4
            0.99,
            WHO_SYMBOL,
            (THIRD, FOURTH),
            "Ben",
            "Ana",
            True,
            False,
            (
                _s(AHEAD, "Ben", StoryReason.FRACTION, _c(THIRD, ">", FOURTH), True),
                (
                    _s(AHEAD, "Ana", StoryReason.FRACTION, _c(THIRD, ">", FOURTH), True),
                    _s(AHEAD, "Ana", StoryReason.FRACTION, _c(THIRD, "<", FOURTH), True),
                    _s(AHEAD, "Ben", StoryReason.FRACTION, _c(THIRD, "<", FOURTH), True),
                ),
            ),
        ),
        (
            # plain, can't tell
            0.99,
            PLAIN,
            (_f(5, 8), _f(3, 8)),
            CANT_TELL,
            "Ana",
            False,
            True,
            (
                _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                (
                    _s(AHEAD, "Ana", StoryReason.NONE),
                    _s(AHEAD, "Ben", StoryReason.NONE),
                    _s(SAME_VERDICT, None, StoryReason.NONE),
                ),
            ),
        ),
        (
            # plain, the same
            0.99,
            PLAIN,
            (_f(3, 8), _f(3, 8)),
            SAME,
            None,
            True,
            True,
            (
                _s(SAME_VERDICT, None, StoryReason.NONE),
                (
                    _s(AHEAD, "Ana", StoryReason.NONE),
                    _s(AHEAD, "Ben", StoryReason.NONE),
                    _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                ),
            ),
        ),
        (
            # plain, Ana ahead
            0.99,
            PLAIN,
            (THIRD, FOURTH),
            "Ana",
            "Ana",
            True,
            True,
            (
                _s(AHEAD, "Ana", StoryReason.NONE),
                (
                    _s(AHEAD, "Ben", StoryReason.NONE),
                    _s(SAME_VERDICT, None, StoryReason.NONE),
                    _s(CANT_TELL_VERDICT, None, StoryReason.NONE),
                ),
            ),
        ),
    ],
)
def test_story_choices(
    drawn: float,
    form: StoryForm,
    pair: tuple[UnreducedFraction, UnreducedFraction],
    answer: str,
    winner: str | None,
    same_size: bool,
    greater: bool,
    expected: tuple[StoryChoice, tuple[StoryChoice, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    assert story_choices(form, NAMES, pair, answer, winner, same_size, greater) == expected


@pytest.mark.parametrize(
    ("fraction", "greater", "shared", "expected"),
    [
        (
            # fewer shaded of sixths, 4 of more parts up to 12; not: itself, more of sixths, 4
            # of fewer parts
            _f(4, 6),
            False,
            (NUMERATOR, DENOMINATOR),
            (
                [_f(1, 6), _f(2, 6), _f(3, 6), *(_f(4, parts) for parts in range(7, 13))],
                [_f(4, 6), _f(5, 6), _f(6, 6), _f(4, 4), _f(4, 5)],
            ),
        ),
        (
            _f(4, 6),
            True,
            (DENOMINATOR,),
            ([_f(5, 6), _f(6, 6)], [_f(4, 6), _f(1, 6), _f(2, 6), _f(3, 6)]),
        ),
        (
            # past 12 parts, up to the fraction's own: none smaller than 1/14 that way
            _f(1, 14),
            False,
            (NUMERATOR,),
            ([], [_f(1, 14), *(_f(1, parts) for parts in range(2, 14))]),
        ),
    ],
)
def test_less_greater_ways(
    fraction: UnreducedFraction,
    greater: bool,
    shared: Sequence[Shared],
    expected: tuple[list[UnreducedFraction], list[UnreducedFraction]],
) -> None:
    assert less_greater_ways(fraction, greater, shared) == expected


@pytest.mark.parametrize(
    ("drawn", "greater", "shared", "expected"),
    [
        # the answer may stand out: the last way that isn't, 4/5, beside the first three ways
        (0.0, False, (NUMERATOR, DENOMINATOR), (_f(4, 5), (_f(1, 6), _f(2, 6), _f(3, 6)))),
        # its 4 shaded parts tied by 4/12; never 4/6 itself
        (0.99, False, (NUMERATOR, DENOMINATOR), (_f(4, 5), (_f(4, 12), _f(1, 6), _f(2, 6)))),
        # for "greater", tied by as few: 4/12 beside 4/5
        (0.99, True, (NUMERATOR, DENOMINATOR), (_f(4, 12), (_f(4, 5), _f(5, 6), _f(6, 6)))),
        # sixths alone: nothing can tie, so any
        (0.99, False, (DENOMINATOR,), (_f(6, 6), (_f(1, 6), _f(2, 6), _f(3, 6)))),
    ],
)
def test_less_greater_choices(
    drawn: float,
    greater: bool,
    shared: Sequence[Shared],
    expected: tuple[UnreducedFraction, tuple[UnreducedFraction, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    ways, nots = less_greater_ways(_f(4, 6), greater, shared)
    assert less_greater_choices(_f(4, 6), ways, nots, greater) == expected


def test_either_way_keeps_a_fraction_with_itself(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turned round, 3/8 > 3/8 would read 3/8 < 3/8, another choice, so it stays as written."""
    _script(monkeypatch, 0.99)
    assert either_way(_c(_f(3, 8), ">", _f(3, 8))) == _c(_f(3, 8), ">", _f(3, 8))


@pytest.mark.parametrize(
    ("drawn", "greater", "shared", "expected"),
    [
        # the answer may stand out: the last way, 4/12, beside the first three that aren't
        (0.0, False, (NUMERATOR, DENOMINATOR), (_f(4, 12), (_f(4, 6), _f(5, 6), _f(6, 6)))),
        # its 4 shaded parts tied by 4/5, not by 4/6, the model's twin
        (0.99, False, (NUMERATOR, DENOMINATOR), (_f(4, 12), (_f(4, 5), _f(4, 6), _f(5, 6)))),
        # for "greater", tied by as many: 4/5 beside 4/12
        (0.99, True, (NUMERATOR, DENOMINATOR), (_f(4, 5), (_f(4, 12), _f(4, 6), _f(1, 6)))),
        # sixths alone: nothing can tie, so any
        (0.99, False, (DENOMINATOR,), (_f(3, 6), (_f(4, 6), _f(5, 6), _f(6, 6)))),
    ],
)
def test_less_greater_shows_choices(
    drawn: float,
    greater: bool,
    shared: Sequence[Shared],
    expected: tuple[UnreducedFraction, tuple[UnreducedFraction, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _script(monkeypatch, drawn)
    ways, nots = less_greater_ways(_f(4, 6), greater, shared)
    assert less_greater_shows_choices(_f(4, 6), ways, nots, greater) == expected


@pytest.mark.parametrize(
    ("answer", "pictured", "expected"),
    [
        # the other parts called larger, the same parts shaded, the denominators compared
        (
            FIVE_SIXTHS,
            True,
            (
                PartSize(8, 6, larger=True),
                SameCount(5, total=False, pictured=True),
                BiggerNumber(8, 6, greater=True),
            ),
        ),
        # the numerators read as part sizes, the same parts in all, the parts counted backwards
        (
            SIX_EIGHTHS,
            False,
            (
                PartSize(6, 8, larger=False),
                SameCount(8, total=True, pictured=False),
                PartsOf(_f(6, 8), _f(8, 8), greater=True),
            ),
        ),
    ],
)
def test_reason_choices(answer: Explanation, pictured: bool, expected: tuple[Reason, ...]) -> None:
    assert reason_choices(answer, pictured) == expected


@pytest.mark.parametrize(
    ("greater", "expected"),
    [
        (
            True,
            (
                Pick(_f(2, 3), _c(_f(2, 3), ">", _f(2, 4))),
                (
                    Pick(_f(2, 3), _c(_f(2, 3), "<", _f(2, 4))),
                    Pick(_f(2, 4), _c(_f(2, 3), ">", _f(2, 4))),
                    Pick(_f(2, 4), _c(_f(2, 3), "<", _f(2, 4))),
                ),
            ),
        ),
        (
            False,
            (
                Pick(_f(2, 4), _c(_f(2, 3), ">", _f(2, 4))),
                (
                    Pick(_f(2, 3), _c(_f(2, 3), ">", _f(2, 4))),
                    Pick(_f(2, 3), _c(_f(2, 3), "<", _f(2, 4))),
                    Pick(_f(2, 4), _c(_f(2, 3), "<", _f(2, 4))),
                ),
            ),
        ),
    ],
)
def test_pick_choices(greater: bool, expected: tuple[Pick, tuple[Pick, ...]]) -> None:
    """Each fraction, picked because the pair compares one way or the other: the one asked
    for, with the true comparison, is right."""
    assert pick_choices((_f(2, 3), _f(2, 4)), greater) == expected
