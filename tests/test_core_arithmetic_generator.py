"""The arithmetic generator makes correct, in-range, non-repeating questions.

``test_questions_from_scripted_draws`` holds the exact expectations: ``random`` is scripted, so
each case spells out the questions that must come out. The no-repeats test uses the real random
generation.
"""

import random

import pytest

from core.arithmetic import ArithmeticQuestionData, Operation
from core.arithmetic_generator import generate_arithmetic_questions

# one question: (data, wrong answers, options)
Made = tuple[ArithmeticQuestionData, tuple[int, ...], tuple[int, ...]]


@pytest.mark.parametrize(
    ("operation", "low", "high", "wrong_answer_count", "drawn", "expected"),
    [
        # operands are kept in the order drawn, and sample takes the top of the wrong answers
        (
            Operation.ADD,
            0,
            10,
            3,
            [3, 4],
            [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20), (20, 19, 18, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [4, 3],
            [(ArithmeticQuestionData(Operation.ADD, (4, 3), 7), (18, 19, 20), (20, 19, 18, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [0, 0],
            [(ArithmeticQuestionData(Operation.ADD, (0, 0), 0), (18, 19, 20), (20, 19, 18, 0))],
        ),
        # the correct answer 20 is left out of the wrong answers
        (
            Operation.ADD,
            0,
            10,
            3,
            [10, 10],
            [(ArithmeticQuestionData(Operation.ADD, (10, 10), 20), (17, 18, 19), (19, 18, 17, 20))],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [7, 3],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10), (10, 9, 8, 4))],
        ),
        # drawn smaller first: swapped, so the answer is not negative
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [3, 7],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10), (10, 9, 8, 4))],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [5, 5],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (5, 5), 0), (8, 9, 10), (10, 9, 8, 0))],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [0, 9],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (9, 0), 9), (7, 8, 10), (10, 8, 7, 9))],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [9, 0],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (9, 0), 9), (7, 8, 10), (10, 8, 7, 9))],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [6, 7],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42),
                    (98, 99, 100),
                    (100, 99, 98, 42),
                ),
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [7, 6],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (7, 6), 42),
                    (98, 99, 100),
                    (100, 99, 98, 42),
                ),
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [0, 9],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (0, 9), 0),
                    (98, 99, 100),
                    (100, 99, 98, 0),
                ),
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [10, 10],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (10, 10), 100),
                    (97, 98, 99),
                    (99, 98, 97, 100),
                ),
            ],
        ),
        # the number of wrong answers
        (
            Operation.ADD,
            0,
            10,
            1,
            [3, 4],
            [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (20,), (20, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            5,
            [3, 4],
            [
                (
                    ArithmeticQuestionData(Operation.ADD, (3, 4), 7),
                    (16, 17, 18, 19, 20),
                    (20, 19, 18, 17, 16, 7),
                ),
            ],
        ),
        # low and high reach every draw, and the top of the wrong answers follows the operation:
        # twice high for sums, high for differences, high squared for products
        (
            Operation.ADD,
            2,
            5,
            3,
            [3, 4],
            [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (8, 9, 10), (10, 9, 8, 7))],
        ),
        (
            Operation.ADD,
            7,
            7,
            3,
            [7, 7],
            [(ArithmeticQuestionData(Operation.ADD, (7, 7), 14), (11, 12, 13), (13, 12, 11, 14))],
        ),
        (
            Operation.ADD,
            1,
            12,
            3,
            [5, 8],
            [(ArithmeticQuestionData(Operation.ADD, (5, 8), 13), (22, 23, 24), (24, 23, 22, 13))],
        ),
        (
            Operation.SUBTRACT,
            2,
            5,
            3,
            [5, 3],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (5, 3), 2), (3, 4, 5), (5, 4, 3, 2))],
        ),
        (
            Operation.MULTIPLY,
            2,
            5,
            3,
            [3, 4],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (3, 4), 12),
                    (23, 24, 25),
                    (25, 24, 23, 12),
                ),
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            24,
            3,
            [2, 3],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (2, 3), 6),
                    (574, 575, 576),
                    (576, 575, 574, 6),
                ),
            ],
        ),
        # tiny ranges: the top is raised to 3, the number of wrong answers, so there are enough
        (
            Operation.ADD,
            1,
            1,
            3,
            [1, 1],
            [(ArithmeticQuestionData(Operation.ADD, (1, 1), 2), (0, 1, 3), (3, 1, 0, 2))],
        ),
        (
            Operation.ADD,
            0,
            0,
            3,
            [0, 0],
            [(ArithmeticQuestionData(Operation.ADD, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        (
            Operation.SUBTRACT,
            0,
            0,
            3,
            [0, 0],
            [(ArithmeticQuestionData(Operation.SUBTRACT, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        (
            Operation.MULTIPLY,
            0,
            0,
            3,
            [0, 0],
            [(ArithmeticQuestionData(Operation.MULTIPLY, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        # the answer 0 is not repeated as a wrong answer
        (
            Operation.MULTIPLY,
            0,
            1,
            3,
            [0, 1],
            [(ArithmeticQuestionData(Operation.MULTIPLY, (0, 1), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        # a pair that was already used, in either order, is drawn again: 4 + 3 flips 3 + 4
        (
            Operation.ADD,
            0,
            10,
            3,
            [3, 4, 4, 3, 5, 6],
            [
                (ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20), (20, 19, 18, 7)),
                (ArithmeticQuestionData(Operation.ADD, (5, 6), 11), (18, 19, 20), (20, 19, 18, 11)),
            ],
        ),
        # 3 - 7 is drawn the other way round but makes the same pair as 7 - 3
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [7, 3, 3, 7, 9, 2],
            [
                (ArithmeticQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10), (10, 9, 8, 4)),
                (ArithmeticQuestionData(Operation.SUBTRACT, (9, 2), 7), (8, 9, 10), (10, 9, 8, 7)),
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [6, 7, 7, 6, 6, 7, 2, 8],
            [
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42),
                    (98, 99, 100),
                    (100, 99, 98, 42),
                ),
                (
                    ArithmeticQuestionData(Operation.MULTIPLY, (2, 8), 16),
                    (98, 99, 100),
                    (100, 99, 98, 16),
                ),
            ],
        ),
        # the same pair twice in a row
        (
            Operation.ADD,
            0,
            10,
            3,
            [5, 5, 5, 5, 1, 2],
            [
                (ArithmeticQuestionData(Operation.ADD, (5, 5), 10), (18, 19, 20), (20, 19, 18, 10)),
                (ArithmeticQuestionData(Operation.ADD, (1, 2), 3), (18, 19, 20), (20, 19, 18, 3)),
            ],
        ),
    ],
)
def test_questions_from_scripted_draws(
    operation: Operation,
    low: int,
    high: int,
    wrong_answer_count: int,
    drawn: list[int],
    expected: list[Made],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sheet is fixed by the operands drawn, the limits and the operation.

    ``randint`` hands out the scripted ``drawn`` operands and records the bounds it is asked for,
    ``sample`` takes the top of the pool of wrong answers, and ``shuffle`` reverses the options.
    The sheet asks for as many questions as ``expected`` has. Each question's data, wrong answers
    and options must then match exactly, and every draw must have been made from ``low`` to
    ``high``. If the generator drew fewer or more times than scripted, the recorded bounds differ.
    """
    values = iter(drawn)
    bounds: list[tuple[int, int]] = []

    def randint(first: int, last: int) -> int:
        bounds.append((first, last))
        return next(values)

    monkeypatch.setattr(random, "randint", randint)
    monkeypatch.setattr(random, "sample", lambda population, k: list(population[-k:]))
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())

    questions = generate_arithmetic_questions(
        len(expected), operation, low=low, high=high, wrong_answer_count=wrong_answer_count
    )

    assert bounds == [(low, high)] * len(drawn)
    assert [(q.data, q.wrong_answers, q.options) for q in questions] == expected


def test_the_default_operands_are_0_to_10(randint_ranges: list[tuple[int, int]]) -> None:
    """With no limits given, each operand is drawn from 0 to 10.

    ``randint_ranges`` records the bounds each draw is asked for. A call with no limits can't be
    a row of the test above, since its columns always pass them.
    """
    generate_arithmetic_questions(1, Operation.ADD)
    assert randint_ranges == [(0, 10), (0, 10)]


@pytest.mark.parametrize(
    ("operation", "count", "low", "high"),
    [
        (Operation.ADD, 10, 0, 10),
        (Operation.SUBTRACT, 10, 0, 10),
        (Operation.MULTIPLY, 10, 0, 10),
        (Operation.ADD, 21, 0, 5),  # every possible pair, in either order, used once
        (Operation.SUBTRACT, 21, 0, 5),
        (Operation.MULTIPLY, 21, 0, 5),
        (Operation.MULTIPLY, 1, 3, 3),
    ],
)
def test_random_questions_have_no_repeats_even_when_flipped(
    operation: Operation, count: int, low: int, high: int
) -> None:
    """A sheet of the requested size is always made, with no pair repeated in either order.

    This uses real random draws, including sheets that need every possible pair, which can
    only be finished by drawing until the last unused pair turns up.
    """
    questions = generate_arithmetic_questions(count, operation, low=low, high=high)
    pairs = [tuple(sorted(question.data.operands)) for question in questions]
    assert len(questions) == count
    assert len(set(pairs)) == count


@pytest.mark.parametrize(
    ("count", "low", "high"),
    [
        (7, 1, 3),  # 3 numbers make only 6 different pairs
        (22, 0, 5),
        (2, 3, 3),
    ],
)
def test_asking_for_more_different_questions_than_exist_fails(
    count: int, low: int, high: int
) -> None:
    """Asking for more questions than there are different pairs raises a ValueError.

    Without that check the sheet would draw forever, looking for a pair that does not exist. The
    cases ask for one more than the pairs available, or for two from a range with one pair.
    """
    with pytest.raises(ValueError, match="only"):
        generate_arithmetic_questions(count, Operation.MULTIPLY, low=low, high=high)
