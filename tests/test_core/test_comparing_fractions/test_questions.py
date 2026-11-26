"""
Tests for making a "Which of these are greater than 3/8?" question, where the generator's tests
don't reach: no fractions to ask about, and every set already used.

Where it's scripted, ``random.sample`` takes the first items, ``random.shuffle`` reverses the
list, and ``random.random`` returns 0.99.
"""

import pytest

from core.comparing_fractions.data import EveryQuestionData, Shared
from core.comparing_fractions.questions import every_question
from core.question import FreeResponse, Question
from core.written_numbers import FractionStyle, UnreducedFraction
from tests.helpers import random_always_returns, reverse_shuffle, sample_first

NUMERATOR, DENOMINATOR = Shared


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


def test_every_question_with_no_fractions() -> None:
    """Halves alone share a numerator with nothing."""
    assert every_question((NUMERATOR,), (2,), FractionStyle.STACKED, set(), False) is None


def test_every_question_repeats_a_used_set_when_it_must(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fourths make one set of four for "all of them", 1/4 with the rest or 4/4 with the rest;
    used already, it comes again, rather than no question."""
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    random_always_returns(monkeypatch, 0.99)
    used = {frozenset((_f(1, 4), _f(2, 4), _f(3, 4), _f(4, 4)))}

    question = every_question((DENOMINATOR,), (4,), FractionStyle.STACKED, used, False, True)

    assert question == Question(
        EveryQuestionData(
            _f(1, 4), True, (_f(4, 4), _f(3, 4), _f(2, 4)), (_f(4, 4), _f(3, 4), _f(2, 4))
        ),
        FreeResponse(),
    )
