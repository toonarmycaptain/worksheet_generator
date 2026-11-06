"""
Tests for the arithmetic and missing-number question generators.

The ``..._from_scripted_draws`` tests pin the exact output: ``random`` is scripted, so each case
lists the questions that must be produced. The no-repeats tests and
``test_missing_number_sheets_can_always_be_finished`` use real random draws.
"""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.basic_operations.generator import (
    count_possible_answers,
    count_possible_missing_number_questions,
    count_possible_questions,
    generate_basic_operation_questions,
    generate_missing_number_questions,
)
from tests.helpers import (
    choose_last,
    randint_returns,
    randint_returns_low,
    reverse_shuffle,
    sample_first,
    sample_last,
)

# one question: (data, wrong answers, options)
Made = tuple[BasicOperationQuestionData, tuple[int, ...], tuple[int, ...]]


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
            [(BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20), (20, 19, 18, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [4, 3],
            [(BasicOperationQuestionData(Operation.ADD, (4, 3), 7), (18, 19, 20), (20, 19, 18, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [0, 0],
            [(BasicOperationQuestionData(Operation.ADD, (0, 0), 0), (18, 19, 20), (20, 19, 18, 0))],
        ),
        # the correct answer 20 is left out of the wrong answers
        (
            Operation.ADD,
            0,
            10,
            3,
            [10, 10],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (10, 10), 20),
                    (17, 18, 19),
                    (19, 18, 17, 20),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [7, 3],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (7, 3), 4),
                    (8, 9, 10),
                    (10, 9, 8, 4),
                )
            ],
        ),
        # drawn smaller first: swapped, so the answer is not negative
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [3, 7],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (7, 3), 4),
                    (8, 9, 10),
                    (10, 9, 8, 4),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [5, 5],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (5, 5), 0),
                    (8, 9, 10),
                    (10, 9, 8, 0),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [0, 9],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (9, 0), 9),
                    (7, 8, 10),
                    (10, 8, 7, 9),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            0,
            10,
            3,
            [9, 0],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (9, 0), 9),
                    (7, 8, 10),
                    (10, 8, 7, 9),
                )
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            10,
            3,
            [6, 7],
            [
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42),
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
                    BasicOperationQuestionData(Operation.MULTIPLY, (7, 6), 42),
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
                    BasicOperationQuestionData(Operation.MULTIPLY, (0, 9), 0),
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
                    BasicOperationQuestionData(Operation.MULTIPLY, (10, 10), 100),
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
            [(BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (20,), (20, 7))],
        ),
        (
            Operation.ADD,
            0,
            10,
            5,
            [3, 4],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
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
            [(BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (8, 9, 10), (10, 9, 8, 7))],
        ),
        (
            Operation.ADD,
            7,
            7,
            3,
            [7, 7],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (7, 7), 14),
                    (11, 12, 13),
                    (13, 12, 11, 14),
                )
            ],
        ),
        (
            Operation.ADD,
            1,
            12,
            3,
            [5, 8],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (5, 8), 13),
                    (22, 23, 24),
                    (24, 23, 22, 13),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            2,
            5,
            3,
            [5, 3],
            [(BasicOperationQuestionData(Operation.SUBTRACT, (5, 3), 2), (3, 4, 5), (5, 4, 3, 2))],
        ),
        (
            Operation.MULTIPLY,
            2,
            5,
            3,
            [3, 4],
            [
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
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
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
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
            [(BasicOperationQuestionData(Operation.ADD, (1, 1), 2), (0, 1, 3), (3, 1, 0, 2))],
        ),
        (
            Operation.ADD,
            0,
            0,
            3,
            [0, 0],
            [(BasicOperationQuestionData(Operation.ADD, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        (
            Operation.SUBTRACT,
            0,
            0,
            3,
            [0, 0],
            [(BasicOperationQuestionData(Operation.SUBTRACT, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        (
            Operation.MULTIPLY,
            0,
            0,
            3,
            [0, 0],
            [(BasicOperationQuestionData(Operation.MULTIPLY, (0, 0), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        # the answer 0 is not repeated as a wrong answer
        (
            Operation.MULTIPLY,
            0,
            1,
            3,
            [0, 1],
            [(BasicOperationQuestionData(Operation.MULTIPLY, (0, 1), 0), (1, 2, 3), (3, 2, 1, 0))],
        ),
        # a pair that was already used, in either order, is drawn again: 4 + 3 flips 3 + 4
        (
            Operation.ADD,
            0,
            10,
            3,
            [3, 4, 4, 3, 5, 6],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    (18, 19, 20),
                    (20, 19, 18, 7),
                ),
                (
                    BasicOperationQuestionData(Operation.ADD, (5, 6), 11),
                    (18, 19, 20),
                    (20, 19, 18, 11),
                ),
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
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (7, 3), 4),
                    (8, 9, 10),
                    (10, 9, 8, 4),
                ),
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (9, 2), 7),
                    (8, 9, 10),
                    (10, 9, 8, 7),
                ),
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
                    BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42),
                    (98, 99, 100),
                    (100, 99, 98, 42),
                ),
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 8), 16),
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
                (
                    BasicOperationQuestionData(Operation.ADD, (5, 5), 10),
                    (18, 19, 20),
                    (20, 19, 18, 10),
                ),
                (
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    (18, 19, 20),
                    (20, 19, 18, 3),
                ),
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
    """
    A sheet is determined by the operands drawn, the limits and the operation.

    ``randint`` returns the scripted ``drawn`` operands and records the bounds of each call,
    ``sample`` takes the top of the wrong-answer pool, and ``shuffle`` reverses the options. The
    sheet requests as many questions as ``expected`` has. Each question's data, wrong answers
    and options must match exactly, and every draw must span ``low`` to ``high``; a generator
    that drew more or fewer times than scripted records different bounds.
    """
    bounds = randint_returns(monkeypatch, drawn)
    sample_last(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_basic_operation_questions(
        len(expected), operation, low=low, high=high, wrong_answer_count=wrong_answer_count
    )

    assert bounds == [(low, high)] * len(drawn)
    assert [(q.data, q.wrong_answers, q.options) for q in questions] == expected


def test_the_default_operands_are_0_to_10(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    With no limits given, each operand is drawn from 0 to 10.

    ``randint_returns_low`` records the bounds of each draw. This cannot be a row of the test above,
    whose columns always pass the limits.
    """
    bounds = randint_returns_low(monkeypatch)
    generate_basic_operation_questions(1, Operation.ADD)
    assert bounds == [(0, 10), (0, 10)]


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
        (Operation.DIVIDE, 37, 0, 10),  # every division fact with a dividend up to 10
        (Operation.DIVIDE, 27, 2, 20),  # every one with a divisor and quotient of at least 2
    ],
)
def test_random_questions_have_no_repeats_even_when_flipped(
    operation: Operation, count: int, low: int, high: int
) -> None:
    """
    A sheet of the requested size is always produced, with no pair repeated in either order.

    This uses real random draws, including sheets that need every possible pair and so finish
    only once the last unused pair is drawn.
    """
    questions = generate_basic_operation_questions(count, operation, low=low, high=high)
    pairs = [tuple(sorted(question.data.operands)) for question in questions]
    assert len(questions) == count
    assert len(set(pairs)) == count


@pytest.mark.parametrize(
    ("operation", "count", "low", "high", "largest_divisor", "distinct_answers", "message"),
    [
        # 3 numbers make only 6 different pairs
        (
            Operation.MULTIPLY,
            7,
            1,
            3,
            None,
            False,
            "Cannot make 7 different questions: only 6 possible.",
        ),
        (
            Operation.MULTIPLY,
            22,
            0,
            5,
            None,
            False,
            "Cannot make 22 different questions: only 21 possible.",
        ),
        (
            Operation.MULTIPLY,
            2,
            3,
            3,
            None,
            False,
            "Cannot make 2 different questions: only 1 possible.",
        ),
        (
            Operation.DIVIDE,
            38,
            0,
            10,
            None,
            False,
            "Cannot make 38 different questions: only 37 possible.",
        ),
        (
            Operation.DIVIDE,
            18,
            0,
            10,
            2,
            False,
            "Cannot make 18 different questions: only 17 possible.",
        ),
        (
            Operation.DIVIDE,
            3,
            0,
            1,
            1,
            False,
            "Cannot make 3 different questions: only 2 possible.",
        ),
        # distinct answers: 11 sums
        (
            Operation.ADD,
            12,
            0,
            5,
            None,
            True,
            "Cannot make 12 questions with different answers: only 11 possible.",
        ),
        # 11 differences
        (
            Operation.SUBTRACT,
            12,
            0,
            10,
            None,
            True,
            "Cannot make 12 questions with different answers: only 11 possible.",
        ),
        # 15 products
        (
            Operation.MULTIPLY,
            16,
            0,
            5,
            None,
            True,
            "Cannot make 16 questions with different answers: only 15 possible.",
        ),
        # 0 1 2 3 4 6 9
        (
            Operation.MULTIPLY,
            8,
            0,
            3,
            None,
            True,
            "Cannot make 8 questions with different answers: only 7 possible.",
        ),
        (
            Operation.DIVIDE,
            12,
            0,
            10,
            None,
            True,
            "Cannot make 12 questions with different answers: only 11 possible.",
        ),
    ],
)
def test_basic_operation_sheet_errors(
    operation: Operation,
    count: int,
    low: int,
    high: int,
    largest_divisor: int | None,
    distinct_answers: bool,
    message: str,
) -> None:
    """
    Requesting more questions than the settings allow raises ``ValueError`` saying how many.

    Without that check, generation would loop forever looking for a pair or an answer that does
    not exist. The cases request one more than are possible, or two from a range with one pair.
    """
    with pytest.raises(ValueError) as error:
        generate_basic_operation_questions(
            count,
            operation,
            low=low,
            high=high,
            largest_divisor=largest_divisor,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("operation", "high", "drawn", "expected"),
    [
        # 2 + 5 is skipped: its answer 7 is already used by 3 + 4
        (
            Operation.ADD,
            10,
            [3, 4, 2, 5, 1, 2],
            [
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
            ],
        ),
        # 9 - 5 is skipped: its answer 4 is already used by 7 - 3
        (
            Operation.SUBTRACT,
            10,
            [7, 3, 9, 5, 8, 2],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (7, 3), 4),
                BasicOperationQuestionData(Operation.SUBTRACT, (8, 2), 6),
            ],
        ),
        # 3 x 4 is skipped: its answer 12 is already used by 2 x 6
        (
            Operation.MULTIPLY,
            10,
            [2, 6, 3, 4, 1, 5],
            [
                BasicOperationQuestionData(Operation.MULTIPLY, (2, 6), 12),
                BasicOperationQuestionData(Operation.MULTIPLY, (1, 5), 5),
            ],
        ),
        # a repeated pair is still skipped, even with a different answer order
        (
            Operation.ADD,
            10,
            [3, 4, 4, 3, 1, 2],
            [
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
            ],
        ),
    ],
)
def test_distinct_answers_from_scripted_draws(
    operation: Operation,
    high: int,
    drawn: list[int],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    With ``distinct_answers``, a pair whose answer is already used is redrawn.

    No wrong answers are requested, so only operands are drawn. Every scripted draw must be
    made, from 0 to ``high``.
    """
    bounds = randint_returns(monkeypatch, drawn)

    questions = generate_basic_operation_questions(
        len(expected), operation, high=high, wrong_answer_count=0, distinct_answers=True
    )

    assert bounds == [(0, high)] * len(drawn)
    assert [question.data for question in questions] == expected


@pytest.mark.parametrize(
    ("operation", "count", "high"),
    [
        (Operation.ADD, 11, 5),  # the sums 0 to 10, each once
        (Operation.SUBTRACT, 11, 10),  # the differences 0 to 10
        (Operation.MULTIPLY, 15, 5),  # 0 1 2 3 4 5 6 8 9 10 12 15 16 20 25
        (Operation.ADD, 12, 10),
        (Operation.DIVIDE, 11, 10),  # the quotients 0 to 10
        (Operation.DIVIDE, 12, 11),  # 0 to 11, where 6 to 11 come only from dividing by 1
    ],
)
def test_random_questions_have_distinct_answers(
    operation: Operation, count: int, high: int
) -> None:
    """A sheet is produced even when it needs every possible answer, with no answer repeated."""
    questions = generate_basic_operation_questions(
        count, operation, high=high, wrong_answer_count=0, distinct_answers=True
    )
    answers = [question.data.answer for question in questions]
    assert len(answers) == count
    assert len(set(answers)) == count


@pytest.mark.parametrize(
    ("operation", "low", "high", "up_to", "count"),
    [
        (Operation.ADD, 0, 2, 100, 5),  # 0 1 2 3 4
        (Operation.ADD, 3, 4, 100, 3),  # 6 7 8
        (Operation.SUBTRACT, 0, 3, 100, 4),  # 0 1 2 3
        (Operation.SUBTRACT, 5, 7, 100, 3),  # 0 1 2
        (Operation.MULTIPLY, 0, 3, 100, 7),  # 0 1 2 3 4 6 9
        (Operation.MULTIPLY, 2, 3, 100, 3),  # 4 6 9
        (Operation.ADD, 0, 2, 5, 5),  # exactly up_to
        (Operation.MULTIPLY, 0, 3, 7, 7),
        (Operation.ADD, 0, 2, 3, 3),  # more than up_to stops at up_to
        (Operation.SUBTRACT, 0, 3, 3, 3),
        (Operation.MULTIPLY, 0, 3, 3, 3),
        (Operation.ADD, 0, 999999, 12, 12),  # a huge range is quick: it stops at up_to
        (Operation.SUBTRACT, 0, 999999, 12, 12),
        (Operation.MULTIPLY, 0, 999999, 12, 12),
        (Operation.DIVIDE, 0, 10, 100, 11),  # the quotients 0 to 10
        (Operation.DIVIDE, 2, 20, 100, 9),  # 2 to 10: divisors of at least 2 into 20
        (Operation.DIVIDE, 0, 999, 12, 12),
    ],
)
def test_count_possible_answers(
    operation: Operation, low: int, high: int, up_to: int, count: int
) -> None:
    assert count_possible_answers(operation, low=low, high=high, up_to=up_to) == count


@pytest.mark.parametrize(
    ("low", "high", "largest_divisor", "drawn", "bounds", "expected"),
    [
        # a divisor, then a quotient that keeps the dividend within high
        (
            0,
            100,
            10,
            [4, 7],
            [(1, 10), (0, 25)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (28, 4), 7),
                    (98, 99, 100),
                    (100, 99, 98, 7),
                )
            ],
        ),
        # a quotient of 0
        (
            0,
            100,
            10,
            [3, 0],
            [(1, 10), (0, 33)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (0, 3), 0),
                    (98, 99, 100),
                    (100, 99, 98, 0),
                )
            ],
        ),
        # with no largest divisor, the divisor goes up to high
        (
            0,
            12,
            None,
            [12, 1],
            [(1, 12), (0, 1)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (12, 12), 1),
                    (10, 11, 12),
                    (12, 11, 10, 1),
                )
            ],
        ),
        # a largest divisor above high is held to high
        (
            0,
            6,
            10,
            [6, 1],
            [(1, 6), (0, 1)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (6, 6), 1),
                    (4, 5, 6),
                    (6, 5, 4, 1),
                )
            ],
        ),
        # low is the smallest divisor and quotient, so a dividend of 20 allows divisors up to 10
        (
            2,
            20,
            None,
            [5, 4],
            [(2, 10), (2, 4)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (20, 5), 4),
                    (18, 19, 20),
                    (20, 19, 18, 4),
                )
            ],
        ),
        # a fact already used is drawn again
        (
            0,
            100,
            10,
            [4, 7, 4, 7, 2, 3],
            [(1, 10), (0, 25), (1, 10), (0, 25), (1, 10), (0, 50)],
            [
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (28, 4), 7),
                    (98, 99, 100),
                    (100, 99, 98, 7),
                ),
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (6, 2), 3),
                    (98, 99, 100),
                    (100, 99, 98, 3),
                ),
            ],
        ),
    ],
)
def test_division_from_scripted_draws(
    low: int,
    high: int,
    largest_divisor: int | None,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[Made],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A division sheet is determined by the divisors and quotients drawn and the limits.

    ``randint`` returns the scripted ``drawn`` values, a divisor then a quotient, and records the
    bounds of each draw. Wrong answers range from 0 to ``high``; ``sample`` takes the top of them
    and ``shuffle`` reverses the options.
    """
    asked = randint_returns(monkeypatch, drawn)
    sample_last(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_basic_operation_questions(
        len(expected), Operation.DIVIDE, low=low, high=high, largest_divisor=largest_divisor
    )

    assert asked == bounds
    assert [(q.data, q.wrong_answers, q.options) for q in questions] == expected


@pytest.mark.parametrize(
    ("operation", "low", "high", "largest_divisor", "up_to", "count"),
    [
        # pairs of operands, ignoring their order
        (Operation.ADD, 0, 10, None, 100, 66),
        (Operation.SUBTRACT, 0, 5, None, 100, 21),
        (Operation.MULTIPLY, 1, 3, None, 100, 6),
        (Operation.MULTIPLY, 0, 10, None, 20, 20),  # more than up_to stops at up_to
        # division facts: 11 dividing by 1 (the quotients 0 to 10), 6 by 2, 4 by 3, 3 each by 4
        # and 5, and 2 each by 6 to 10
        (Operation.DIVIDE, 0, 10, None, 100, 37),
        (Operation.DIVIDE, 0, 10, 2, 100, 17),  # dividing by 1 and 2 only
        (Operation.DIVIDE, 0, 100, 10, 1000, 301),  # the basic operations page's defaults
        (Operation.DIVIDE, 2, 20, None, 100, 27),  # divisors and quotients of at least 2
        (Operation.DIVIDE, 0, 1, 1, 100, 2),  # 0 ÷ 1 and 1 ÷ 1
        (Operation.DIVIDE, 0, 100, 10, 20, 20),
    ],
)
def test_count_possible_questions(
    operation: Operation,
    low: int,
    high: int,
    largest_divisor: int | None,
    up_to: int,
    count: int,
) -> None:
    possible = count_possible_questions(
        operation, low=low, high=high, largest_divisor=largest_divisor, up_to=up_to
    )
    assert possible == count


@pytest.mark.parametrize(
    ("unknown", "distinct_answers", "high", "largest_divisor", "drawn", "bounds", "expected"),
    [
        # a divisor, then a quotient of at least 1 that keeps the dividend within high
        (
            Unknown.FIRST,
            False,
            100,
            10,
            [4, 7],
            [(1, 10), (1, 25)],
            [MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28)],
        ),
        (
            Unknown.SECOND,
            False,
            100,
            10,
            [4, 7],
            [(1, 10), (1, 25)],
            [MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4)],
        ),
        # □ ÷ 7 = 4 is from the family of □ ÷ 4 = 7, so it is drawn again; the sheet is reversed
        (
            Unknown.FIRST,
            False,
            100,
            10,
            [4, 7, 7, 4, 2, 3],
            [(1, 10), (1, 25), (1, 10), (1, 14), (1, 10), (1, 50)],
            [
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 2, 3, 6),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
            ],
        ),
        # mixed: the missing divisor is made first, then the missing dividend
        (
            None,
            False,
            100,
            10,
            [4, 7, 3, 5],
            [(1, 10), (1, 25), (1, 10), (1, 33)],
            [
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 3, 5, 15),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4),
            ],
        ),
        # with distinct answers, □ ÷ 2 = 14 is drawn again: its answer is 28, like □ ÷ 4 = 7
        (
            Unknown.FIRST,
            True,
            100,
            10,
            [4, 7, 2, 14, 3, 5],
            [(1, 10), (1, 25), (1, 10), (1, 50), (1, 10), (1, 33)],
            [
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 3, 5, 15),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
            ],
        ),
        # Every divisor from 1 to 10, which drawing one at a time could deadlock on. From 10
        # down, each divisor takes its largest quotient whose family is still free, so 2 takes
        # 3 rather than 5 or 4, and 1 takes 5 rather than 10 to 6. Nothing is drawn by randint.
        (
            Unknown.SECOND,
            True,
            10,
            10,
            [],
            [],
            [
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 5, 5, 1),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 6, 3, 2),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 9, 3, 3),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 8, 2, 4),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 10, 2, 5),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 6, 1, 6),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 7, 1, 7),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 8, 1, 8),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 9, 1, 9),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 10, 1, 10),
            ],
        ),
        # mixed with distinct answers: the missing divisor 1 (100 ÷ □ = 100) rules out the
        # answer 1, so □ ÷ 1 = 1 is drawn again
        (
            None,
            True,
            100,
            10,
            [1, 1, 4, 7],
            [(1, 10), (1, 100), (1, 10), (1, 25)],
            [
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
                MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 100, 100, 1),
            ],
        ),
    ],
)
def test_missing_number_questions_from_scripted_draws(
    unknown: Unknown | None,
    distinct_answers: bool,
    high: int,
    largest_divisor: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[MissingNumberQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A missing-number sheet is determined by the facts drawn, the limits and the missing number.

    ``randint`` returns the scripted ``drawn`` values, a divisor then a quotient, and records the
    bounds of each draw. Missing divisors with distinct answers are generated differently:
    ``sample`` takes the first divisors and ``choice`` the largest quotient whose family is
    free. ``shuffle`` reverses the finished sheet.
    """
    asked = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    choose_last(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_missing_number_questions(
        len(expected),
        Operation.DIVIDE,
        unknown,
        high=high,
        largest_divisor=largest_divisor,
        distinct_answers=distinct_answers,
    )

    assert asked == bounds
    assert [question.data for question in questions] == expected


@pytest.mark.parametrize(
    ("unknown", "distinct_answers", "high", "largest_divisor", "count"),
    [
        # every divisor: drawing one at a time deadlocked on about a third of these sheets
        (Unknown.SECOND, True, 10, 10, 10),
        (Unknown.SECOND, True, 12, 12, 12),
        (Unknown.SECOND, True, 20, 10, 10),
        (Unknown.SECOND, True, 100, 10, 10),
        (Unknown.FIRST, True, 10, 10, 10),  # every dividend from 1 to 10
        (None, True, 10, 10, 7),  # 3 missing divisors and 4 missing dividends
        # every fact family
        (Unknown.SECOND, False, 10, 10, 15),
        (Unknown.FIRST, False, 10, 10, 15),
        (None, False, 10, 10, 15),
    ],
)
def test_missing_number_sheets_can_always_be_finished(
    unknown: Unknown | None,
    distinct_answers: bool,
    high: int,
    largest_divisor: int,
    count: int,
) -> None:
    """
    A sheet needing every question its settings allow always completes, with no family repeated.

    Each sheet is generated 50 times with real random draws. Before missing divisors with
    distinct answers were generated together, the first row's sheets deadlocked about a third
    of the time.
    """
    sheets = [
        generate_missing_number_questions(
            count,
            Operation.DIVIDE,
            unknown,
            high=high,
            largest_divisor=largest_divisor,
            distinct_answers=distinct_answers,
        )
        for _ in range(50)
    ]
    families = [
        {
            frozenset(
                (
                    q.data.known if q.data.unknown is Unknown.FIRST else q.data.answer,
                    q.data.result,
                )
            )
            for q in sheet
        }
        for sheet in sheets
    ]

    assert [len(sheet) for sheet in sheets] == [count] * 50
    assert [len(family) for family in families] == [count] * 50


@pytest.mark.parametrize(
    ("unknown", "distinct_answers", "high", "largest_divisor", "up_to", "count"),
    [
        # the fact families, whichever number is missing
        (Unknown.FIRST, False, 10, 10, 100, 15),
        (Unknown.SECOND, False, 10, 10, 100, 15),
        (None, False, 10, 10, 100, 15),
        (Unknown.SECOND, False, 1, 1, 100, 1),  # 1 ÷ 1 only
        (Unknown.SECOND, False, 100, 10, 12, 12),  # more than up_to stops at up_to
        # with distinct answers: the divisors, or the dividends
        (Unknown.SECOND, True, 10, 10, 100, 10),
        (Unknown.SECOND, True, 100, 3, 100, 3),
        (Unknown.FIRST, True, 10, 10, 100, 10),
        # mixed: 3 missing divisors can use up 6 of the 10 dividends, which leaves 4
        (None, True, 10, 10, 100, 7),
        # mixed with only 2 divisors: 2 missing divisors and 3 missing dividends
        (None, True, 100, 2, 100, 5),
    ],
)
def test_count_possible_missing_number_questions(
    unknown: Unknown | None,
    distinct_answers: bool,
    high: int,
    largest_divisor: int,
    up_to: int,
    count: int,
) -> None:
    possible = count_possible_missing_number_questions(
        Operation.DIVIDE,
        unknown,
        high=high,
        largest_divisor=largest_divisor,
        distinct_answers=distinct_answers,
        up_to=up_to,
    )
    assert possible == count


@pytest.mark.parametrize(
    ("operation", "unknown", "distinct_answers", "count", "exception", "message"),
    [
        # one equation more than dividends and divisors up to 10 allow
        (
            Operation.DIVIDE,
            Unknown.SECOND,
            True,
            11,
            ValueError,
            "Cannot make 11 questions with different answers: only 10 possible.",
        ),
        (
            Operation.DIVIDE,
            None,
            True,
            8,
            ValueError,
            "Cannot make 8 questions with different answers: only 7 possible.",
        ),
        (
            Operation.DIVIDE,
            Unknown.FIRST,
            False,
            16,
            ValueError,
            "Cannot make 16 different questions: only 15 possible.",
        ),
        # an operation other than division
        (
            Operation.ADD,
            Unknown.FIRST,
            False,
            1,
            NotImplementedError,
            "Missing numbers are built for division only.",
        ),
        (
            Operation.SUBTRACT,
            Unknown.FIRST,
            False,
            1,
            NotImplementedError,
            "Missing numbers are built for division only.",
        ),
        (
            Operation.MULTIPLY,
            Unknown.FIRST,
            False,
            1,
            NotImplementedError,
            "Missing numbers are built for division only.",
        ),
    ],
)
def test_missing_number_sheet_errors(
    operation: Operation,
    unknown: Unknown | None,
    distinct_answers: bool,
    count: int,
    exception: type[Exception],
    message: str,
) -> None:
    """
    A missing-number sheet the settings cannot produce raises an error naming the reason.

    The limits are dividends and divisors up to 10. Missing numbers are built only for division,
    and any other operation raises ``NotImplementedError`` before the count is checked.
    """
    with pytest.raises(exception) as error:
        generate_missing_number_questions(
            count,
            operation,
            unknown,
            high=10,
            largest_divisor=10,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message
