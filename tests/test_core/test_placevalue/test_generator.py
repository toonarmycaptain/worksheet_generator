"""
Tests for the place-value question generator.

Numbers are drawn from the requested range, a mixed form never equals the other form, and a
multiple-choice question's wrong answers come from the same range. ``random`` is scripted in
most tests, so each case lists the question that must be produced; the no-repeats test uses
real random draws.
"""

import random
from collections.abc import Sequence
from typing import Any

import pytest

from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.placevalue.generator import (
    generate_place_value_question,
    generate_place_value_questions,
)
from tests.data import EXPANDED, EXPANDED_NOTATION, STANDARD, UNIT, WORD
from tests.helpers import randint_returns, randint_returns_low, reverse_shuffle, sample_first


@pytest.mark.parametrize(
    ("given", "asked", "expected", "chosen_from"),
    [
        # both forms fixed: nothing is picked
        (STANDARD, EXPANDED, PlaceValueQuestionData(35043, STANDARD, EXPANDED), []),
        (WORD, STANDARD, PlaceValueQuestionData(35043, WORD, STANDARD), []),
        # one mixed: picked from the forms other than the fixed one
        (
            STANDARD,
            None,
            PlaceValueQuestionData(35043, STANDARD, EXPANDED),
            [[EXPANDED, UNIT, EXPANDED_NOTATION, WORD]],
        ),
        (
            WORD,
            None,
            PlaceValueQuestionData(35043, WORD, STANDARD),
            [[STANDARD, EXPANDED, UNIT, EXPANDED_NOTATION]],
        ),
        (
            None,
            STANDARD,
            PlaceValueQuestionData(35043, EXPANDED, STANDARD),
            [[EXPANDED, UNIT, EXPANDED_NOTATION, WORD]],
        ),
        (
            None,
            UNIT,
            PlaceValueQuestionData(35043, STANDARD, UNIT),
            [[STANDARD, EXPANDED, EXPANDED_NOTATION, WORD]],
        ),
        # both mixed: the shown form from all five, then the asked form from the other four
        (
            None,
            None,
            PlaceValueQuestionData(35043, STANDARD, EXPANDED),
            [
                [STANDARD, EXPANDED, UNIT, EXPANDED_NOTATION, WORD],
                [EXPANDED, UNIT, EXPANDED_NOTATION, WORD],
            ],
        ),
    ],
)
def test_a_mixed_form_is_picked_from_the_forms_other_than_the_other_one(
    given: PlaceValueForm | None,
    asked: PlaceValueForm | None,
    expected: PlaceValueQuestionData,
    chosen_from: list[list[PlaceValueForm]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A mixed form is chosen only from the forms other than the fixed one.

    ``random.choice`` takes the first form offered, so only excluding the other form from the
    offer keeps a question from asking for the form it shows.
    """
    offered: list[list[PlaceValueForm]] = []

    def first(population: Sequence[Any]) -> Any:
        offered.append(list(population))
        return population[0]

    randint_returns(monkeypatch, [35043])
    monkeypatch.setattr(random, "choice", first)

    assert generate_place_value_question(given, asked).data == expected
    assert offered == chosen_from


@pytest.mark.parametrize(
    ("wrong_answer_count", "low", "high", "drawn", "expected"),
    [
        # written: no wrong answers, so the answer is the only option
        (0, 1000, 99_999, 35043, (PlaceValueQuestionData(35043, STANDARD, EXPANDED), (), (35043,))),
        # sample takes the bottom of the range, and shuffle reverses the options
        (
            3,
            1000,
            99_999,
            35043,
            (
                PlaceValueQuestionData(35043, STANDARD, EXPANDED),
                (1000, 1001, 1002),
                (1002, 1001, 1000, 35043),
            ),
        ),
        # the correct answer is left out of the wrong answers
        (
            3,
            10,
            13,
            10,
            (PlaceValueQuestionData(10, STANDARD, EXPANDED), (11, 12, 13), (13, 12, 11, 10)),
        ),
        (
            3,
            10,
            13,
            12,
            (PlaceValueQuestionData(12, STANDARD, EXPANDED), (10, 11, 13), (13, 11, 10, 12)),
        ),
    ],
)
def test_wrong_answers_come_from_the_range(
    wrong_answer_count: int,
    low: int,
    high: int,
    drawn: int,
    expected: tuple[PlaceValueQuestionData, tuple[int, ...], tuple[int, ...]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each case is the complete question: its data, wrong answers and options, in order."""
    randint_returns(monkeypatch, [drawn])
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    question = generate_place_value_question(
        STANDARD, EXPANDED, low=low, high=high, wrong_answer_count=wrong_answer_count
    )

    assert (question.data, question.wrong_answers, question.options) == expected


@pytest.mark.parametrize(
    ("limits", "expected"),
    [
        ({}, [(1000, 99_999)]),  # 4 and 5 digits by default
        ({"low": 10, "high": 500}, [(10, 500)]),
        ({"low": 1, "high": 999_999}, [(1, 999_999)]),
    ],
)
def test_the_number_is_drawn_from_low_to_high(
    limits: dict[str, int], expected: list[tuple[int, int]], monkeypatch: pytest.MonkeyPatch
) -> None:
    bounds = randint_returns_low(monkeypatch)
    generate_place_value_question(STANDARD, EXPANDED, **limits)
    assert bounds == expected


@pytest.mark.parametrize(
    ("given", "asked", "low", "high", "message"),
    [
        # a fixed form asked for in the form it is shown
        (STANDARD, STANDARD, 1000, 99_999, "A question cannot ask for the form it shows."),
        (EXPANDED, EXPANDED, 1000, 99_999, "A question cannot ask for the form it shows."),
        (UNIT, UNIT, 1000, 99_999, "A question cannot ask for the form it shows."),
        (
            EXPANDED_NOTATION,
            EXPANDED_NOTATION,
            1000,
            99_999,
            "A question cannot ask for the form it shows.",
        ),
        (WORD, WORD, 1000, 99_999, "A question cannot ask for the form it shows."),
        # 0 has no place-value forms
        (
            STANDARD,
            EXPANDED,
            0,
            100,
            "The numbers must be from 1 to 999,999, with low no more than high, not 0 to 100.",
        ),
        # past the hundred thousands
        (
            STANDARD,
            EXPANDED,
            1,
            1_000_000,
            "The numbers must be from 1 to 999,999, with low no more than high, "
            "not 1 to 1,000,000.",
        ),
        # low above high
        (
            STANDARD,
            EXPANDED,
            500,
            10,
            "The numbers must be from 1 to 999,999, with low no more than high, not 500 to 10.",
        ),
    ],
)
def test_place_value_question_errors(
    given: PlaceValueForm, asked: PlaceValueForm, low: int, high: int, message: str
) -> None:
    """
    Asking for the form shown, or a range the forms cannot write, raises ``ValueError``.

    The forms represent 1 to 999,999, and the check is made before any draw.
    """
    with pytest.raises(ValueError) as error:
        generate_place_value_question(given, asked, low=low, high=high)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("count", "given", "asked", "low", "high", "message"),
    [
        # a fixed form asked for in the form it is shown
        (1, STANDARD, STANDARD, 1000, 99_999, "A question cannot ask for the form it shows."),
        (1, EXPANDED, EXPANDED, 1000, 99_999, "A question cannot ask for the form it shows."),
        (1, UNIT, UNIT, 1000, 99_999, "A question cannot ask for the form it shows."),
        (
            1,
            EXPANDED_NOTATION,
            EXPANDED_NOTATION,
            1000,
            99_999,
            "A question cannot ask for the form it shows.",
        ),
        (1, WORD, WORD, 1000, 99_999, "A question cannot ask for the form it shows."),
        # 0 has no place-value forms
        (
            1,
            STANDARD,
            EXPANDED,
            0,
            100,
            "The numbers must be from 1 to 999,999, with low no more than high, not 0 to 100.",
        ),
        # past the hundred thousands
        (
            1,
            STANDARD,
            EXPANDED,
            1,
            1_000_000,
            "The numbers must be from 1 to 999,999, with low no more than high, "
            "not 1 to 1,000,000.",
        ),
        # low above high
        (
            1,
            STANDARD,
            EXPANDED,
            500,
            10,
            "The numbers must be from 1 to 999,999, with low no more than high, not 500 to 10.",
        ),
        # more questions than numbers in the range
        (
            6,
            STANDARD,
            EXPANDED,
            1,
            5,
            "Cannot make 6 questions with different numbers: only 5 possible.",
        ),
    ],
)
def test_place_value_sheet_errors(
    count: int, given: PlaceValueForm, asked: PlaceValueForm, low: int, high: int, message: str
) -> None:
    """
    A sheet raises ``ValueError`` as a question does, and when its range has too few numbers.

    The numbers are drawn without replacement, so a range of 5 numbers makes at most 5 questions.
    """
    with pytest.raises(ValueError) as error:
        generate_place_value_questions(count, given, asked, low=low, high=high)
    assert str(error.value) == message


def test_a_sheet_s_numbers_are_drawn_together_so_none_repeats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ``random.sample`` draws a sheet's numbers at once, and the questions use them in order.

    Its later calls are for wrong answers, which these questions do not have.
    """
    draws: list[tuple[range, int]] = []

    def sample(population: range, k: int) -> list[int]:
        draws.append((population, k))
        return [35043, 50421, 10000][:k]

    monkeypatch.setattr(random, "sample", sample)

    questions = generate_place_value_questions(3, STANDARD, EXPANDED)

    assert [question.data for question in questions] == [
        PlaceValueQuestionData(35043, STANDARD, EXPANDED),
        PlaceValueQuestionData(50421, STANDARD, EXPANDED),
        PlaceValueQuestionData(10000, STANDARD, EXPANDED),
    ]
    assert draws[0] == (range(1000, 100_000), 3)


def test_random_questions_have_different_numbers_and_forms() -> None:
    """Five questions from 1 to 5 use every number once, and none asks for the form it shows."""
    questions = generate_place_value_questions(5, None, None, low=1, high=5)

    assert sorted(question.data.answer for question in questions) == [1, 2, 3, 4, 5]
    assert all(question.data.given != question.data.asked for question in questions)
