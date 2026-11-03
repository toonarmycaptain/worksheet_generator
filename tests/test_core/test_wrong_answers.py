"""Wrong answers: exact picks when sampling is predictable."""

import pytest

from core.wrong_answers import random_wrong_answers


@pytest.mark.usefixtures("predictable_choices")
@pytest.mark.parametrize(
    ("correct_answer", "count", "low", "high", "allow_negatives", "expected"),
    [
        (7, 3, 0, 100, False, (0, 1, 2)),
        (1, 3, 0, 100, False, (0, 2, 3)),  # the correct answer is skipped
        (0, 3, 0, 100, False, (1, 2, 3)),
        (7, 3, 5, 9, False, (5, 6, 8)),  # only 5 to 9, and not 7
        (7, 1, 0, 100, False, (0,)),
        (7, 5, 0, 100, False, (0, 1, 2, 3, 4)),
        (4, 3, 0, 10, True, (-10, -9, -8)),  # negatives come first when allowed
        (-4, 3, 0, 10, True, (-10, -9, -8)),
        (-8, 3, 0, 10, True, (-10, -9, -7)),  # a negative correct answer is skipped too
        (5, 5, 3, 8, False, (3, 4, 6, 7, 8)),  # every possible wrong answer is used
    ],
)
def test_picks_from_the_possible_answers(
    correct_answer: int,
    count: int,
    low: int,
    high: int,
    allow_negatives: bool,
    expected: tuple[int, ...],
) -> None:
    """The wrong answers come from a pool of every number in the range, minus the answer.

    ``sample`` is made to take the first candidates, so each expected tuple shows the start of
    the pool: ``low`` to ``high`` without the correct answer, and with the negatives first when
    they are allowed.
    """
    assert (
        random_wrong_answers(
            correct_answer, count=count, low=low, high=high, allow_negatives=allow_negatives
        )
        == expected
    )


@pytest.mark.usefixtures("predictable_choices")
def test_defaults_are_0_to_100_without_negatives() -> None:
    """With only the answer and a count, the pool starts at 0 and has no negatives.

    For an answer of 2 the first three candidates are 0, 1 and 3. Only the start of the pool is
    visible this way, so the top of the default range (100) is not checked here.
    """
    assert random_wrong_answers(2, count=3) == (0, 1, 3)


@pytest.mark.parametrize(
    ("correct_answer", "count", "low", "high", "allow_negatives", "possible"),
    [
        (2, 3, 1, 3, False, 2),
        (0, 101, 0, 100, False, 100),
        (4, 11, 0, 5, True, 10),  # 0 to 5 and -5 to -1, without the 4
        (5, 1, 5, 5, False, 0),
    ],
)
def test_asking_for_more_than_exist_fails(
    correct_answer: int,
    count: int,
    low: int,
    high: int,
    allow_negatives: bool,
    possible: int,
) -> None:
    """Asking for more wrong answers than the pool holds raises a ValueError saying how many.

    The pool is the range without the correct answer, and with the negatives if they are
    allowed. The message counts those, where ``random.sample`` would fail without explanation.
    """
    with pytest.raises(ValueError, match=f"only {possible} possible"):
        random_wrong_answers(
            correct_answer, count=count, low=low, high=high, allow_negatives=allow_negatives
        )
