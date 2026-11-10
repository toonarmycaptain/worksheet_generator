"""
Tests for the arithmetic, missing-number, word-problem, strip-choice, equation-choice and
number-line-choice generators, with one step or two.

The ``..._from_scripted_draws`` tests pin the exact output: ``random`` is scripted, so each case
lists the questions that must be produced. The no-repeats tests,
``test_missing_number_sheets_can_always_be_finished``,
``test_random_word_problems_have_distinct_answers``,
``test_random_strip_choice_sheets_can_always_be_finished``,
``test_random_equation_choice_sheets_can_always_be_finished``,
``test_random_number_line_choice_sheets_can_always_be_finished``,
``test_random_two_step_problems_have_distinct_answers`` and
``test_random_two_step_strip_choice_sheets_can_always_be_finished`` use real random draws.
"""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    TwoStepQuestionData,
    TwoStepShape,
    Unknown,
)
from core.basic_operations.generator import (
    count_possible_answers,
    count_possible_equation_choice_problems,
    count_possible_missing_number_questions,
    count_possible_number_line_choice_problems,
    count_possible_questions,
    count_possible_sheet_questions,
    count_possible_strip_choice_problems,
    count_possible_two_step_problems,
    count_possible_word_problems,
    generate_basic_operation_questions,
    generate_equation_choice_problems,
    generate_missing_number_questions,
    generate_number_line_choice_problems,
    generate_strip_choice_problems,
    generate_two_step_problems,
    generate_two_step_strip_choice_problems,
    generate_word_problems,
)
from core.basic_operations.representation import (
    STRIP_TWO_STEP_SHAPES,
    equation_choices,
    number_line_choices,
    strip_choices,
    two_step_strip_choices,
)
from core.basic_operations.word_problems import OBJECTS
from core.question import FreeResponse, MultipleChoice, Question
from tests.helpers import (
    choice_returns,
    choices_in_turn,
    choices_returns,
    choose_last,
    randint_returns,
    randint_returns_low,
    reverse_shuffle,
    sample_first,
    sample_last,
)

# one question: (data, response)
Made = tuple[BasicOperationQuestionData, MultipleChoice[int]]


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
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    MultipleChoice((20, 19, 18, 7), frozenset({3})),
                )
            ],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [4, 3],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (4, 3), 7),
                    MultipleChoice((20, 19, 18, 7), frozenset({3})),
                )
            ],
        ),
        (
            Operation.ADD,
            0,
            10,
            3,
            [0, 0],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (0, 0), 0),
                    MultipleChoice((20, 19, 18, 0), frozenset({3})),
                )
            ],
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
                    MultipleChoice((19, 18, 17, 20), frozenset({3})),
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
                    MultipleChoice((10, 9, 8, 4), frozenset({3})),
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
                    MultipleChoice((10, 9, 8, 4), frozenset({3})),
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
                    MultipleChoice((10, 9, 8, 0), frozenset({3})),
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
                    MultipleChoice((10, 8, 7, 9), frozenset({3})),
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
                    MultipleChoice((10, 8, 7, 9), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 42), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 42), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 0), frozenset({3})),
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
                    MultipleChoice((99, 98, 97, 100), frozenset({3})),
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
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    MultipleChoice((20, 7), frozenset({1})),
                )
            ],
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
                    MultipleChoice((20, 19, 18, 17, 16, 7), frozenset({5})),
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
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    MultipleChoice((10, 9, 8, 7), frozenset({3})),
                )
            ],
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
                    MultipleChoice((13, 12, 11, 14), frozenset({3})),
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
                    MultipleChoice((24, 23, 22, 13), frozenset({3})),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            2,
            5,
            3,
            [5, 3],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (5, 3), 2),
                    MultipleChoice((5, 4, 3, 2), frozenset({3})),
                )
            ],
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
                    MultipleChoice((25, 24, 23, 12), frozenset({3})),
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
                    MultipleChoice((576, 575, 574, 6), frozenset({3})),
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
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    MultipleChoice((3, 1, 0, 2), frozenset({3})),
                )
            ],
        ),
        (
            Operation.ADD,
            0,
            0,
            3,
            [0, 0],
            [
                (
                    BasicOperationQuestionData(Operation.ADD, (0, 0), 0),
                    MultipleChoice((3, 2, 1, 0), frozenset({3})),
                )
            ],
        ),
        (
            Operation.SUBTRACT,
            0,
            0,
            3,
            [0, 0],
            [
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (0, 0), 0),
                    MultipleChoice((3, 2, 1, 0), frozenset({3})),
                )
            ],
        ),
        (
            Operation.MULTIPLY,
            0,
            0,
            3,
            [0, 0],
            [
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (0, 0), 0),
                    MultipleChoice((3, 2, 1, 0), frozenset({3})),
                )
            ],
        ),
        # the answer 0 is not repeated as a wrong answer
        (
            Operation.MULTIPLY,
            0,
            1,
            3,
            [0, 1],
            [
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (0, 1), 0),
                    MultipleChoice((3, 2, 1, 0), frozenset({3})),
                )
            ],
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
                    MultipleChoice((20, 19, 18, 7), frozenset({3})),
                ),
                (
                    BasicOperationQuestionData(Operation.ADD, (5, 6), 11),
                    MultipleChoice((20, 19, 18, 11), frozenset({3})),
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
                    MultipleChoice((10, 9, 8, 4), frozenset({3})),
                ),
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (9, 2), 7),
                    MultipleChoice((10, 9, 8, 7), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 42), frozenset({3})),
                ),
                (
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 8), 16),
                    MultipleChoice((100, 99, 98, 16), frozenset({3})),
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
                    MultipleChoice((20, 19, 18, 10), frozenset({3})),
                ),
                (
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    MultipleChoice((20, 19, 18, 3), frozenset({3})),
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
    sheet requests as many questions as ``expected`` has. Each question's data and response
    must match exactly, and every draw must span ``low`` to ``high``; a generator
    that drew more or fewer times than scripted records different bounds.
    """
    bounds = randint_returns(monkeypatch, drawn)
    sample_last(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_basic_operation_questions(
        len(expected), [operation], low=low, high=high, wrong_answer_count=wrong_answer_count
    )

    assert bounds == [(low, high)] * len(drawn)
    assert [(q.data, q.response) for q in questions] == expected


def test_the_default_operands_are_0_to_10(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    With no limits given, each operand is drawn from 0 to 10.

    ``randint_returns_low`` records the bounds of each draw. This cannot be a row of the test above,
    whose columns always pass the limits.
    """
    bounds = randint_returns_low(monkeypatch)
    generate_basic_operation_questions(1, [Operation.ADD])
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
    questions = generate_basic_operation_questions(count, [operation], low=low, high=high)
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
            [operation],
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
        len(expected), [operation], high=high, wrong_answer_count=0, distinct_answers=True
    )

    assert bounds == [(0, high)] * len(drawn)
    assert [question.data for question in questions] == expected


@pytest.mark.parametrize(
    ("operations", "count", "high"),
    [
        ([Operation.ADD], 11, 5),  # the sums 0 to 10, each once
        ([Operation.SUBTRACT], 11, 10),  # the differences 0 to 10
        ([Operation.MULTIPLY], 15, 5),  # 0 1 2 3 4 5 6 8 9 10 12 15 16 20 25
        ([Operation.ADD], 12, 10),
        ([Operation.DIVIDE], 11, 10),  # the quotients 0 to 10
        ([Operation.DIVIDE], 12, 11),  # 0 to 11, where 6 to 11 come only from dividing by 1
        # every answer from 0 to 10, 5 of them differences up to 5
        ([Operation.ADD, Operation.SUBTRACT], 11, 5),
        # every answer from 0 to 4
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY], 5, 2),
        # 3 each: subtraction and division have only 11 answers, too few for 12 drawn at random
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 12, 10),
    ],
)
def test_random_questions_have_distinct_answers(
    operations: list[Operation], count: int, high: int
) -> None:
    """A sheet is produced even when it needs every possible answer, with no answer repeated."""
    questions = generate_basic_operation_questions(
        count, operations, high=high, wrong_answer_count=0, distinct_answers=True
    )
    answers = [question.data.answer for question in questions]
    assert len(answers) == count
    assert len(set(answers)) == count


@pytest.mark.parametrize(
    ("operations", "picks", "largest_dividend", "largest_divisor", "drawn", "bounds", "expected"),
    [
        # 3 + 4 and 4 - 3 share a pair, but not an operation, so both are kept
        (
            [Operation.ADD, Operation.SUBTRACT],
            [Operation.ADD, Operation.SUBTRACT],
            None,
            None,
            [3, 4, 4, 3],
            [(0, 10), (0, 10), (0, 10), (0, 10)],
            [
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                BasicOperationQuestionData(Operation.SUBTRACT, (4, 3), 1),
            ],
        ),
        # addition's operands are up to 10, and division's dividend up to 20: a divisor of 1 to
        # 5, then a quotient of up to 20 over it
        (
            [Operation.ADD, Operation.DIVIDE],
            [Operation.ADD, Operation.DIVIDE],
            20,
            5,
            [3, 4, 4, 5],
            [(0, 10), (0, 10), (1, 5), (0, 5)],
            [
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
            ],
        ),
    ],
)
def test_mixed_questions_from_scripted_draws(
    operations: list[Operation],
    picks: list[Operation],
    largest_dividend: int | None,
    largest_divisor: int | None,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each question's operation is drawn from those given, and its operands are drawn for it.

    ``picks`` are the operations drawn. No wrong answers are requested, so only operands are
    drawn, and every scripted draw must be made, within ``bounds``.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    choices_returns(monkeypatch, picks)

    questions = generate_basic_operation_questions(
        len(expected),
        operations,
        largest_dividend=largest_dividend,
        largest_divisor=largest_divisor,
        wrong_answer_count=0,
    )

    assert drawn_from == bounds
    assert [question.data for question in questions] == expected


@pytest.mark.parametrize(
    ("operations", "high", "drawn", "expected"),
    [
        # 10 - 3 is redrawn: 3 + 4 already has its answer, 7
        (
            [Operation.ADD, Operation.SUBTRACT],
            10,
            [3, 4, 10, 3, 9, 3],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (9, 3), 6),
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
            ],
        ),
        # subtraction up to 1 has 2 answers to addition's 3, so it is generated first, and
        # addition takes the extra question
        (
            [Operation.ADD, Operation.SUBTRACT],
            1,
            [1, 0, 1, 1, 0, 0],
            [
                BasicOperationQuestionData(Operation.ADD, (0, 0), 0),
                BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                BasicOperationQuestionData(Operation.SUBTRACT, (1, 0), 1),
            ],
        ),
        # all three have the 4 answers needed, a tie, so they keep the sampled order, and the
        # extra question goes to the last, multiplication
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY],
            10,
            [3, 4, 9, 5, 2, 3, 5, 1],
            [
                BasicOperationQuestionData(Operation.MULTIPLY, (5, 1), 5),
                BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                BasicOperationQuestionData(Operation.SUBTRACT, (9, 5), 4),
                BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
            ],
        ),
    ],
)
def test_dealt_questions_from_scripted_draws(
    operations: list[Operation],
    high: int,
    drawn: list[int],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    With ``distinct_answers``, the operations are dealt out evenly instead of drawn.

    They are generated from fewest possible answers to most, then the sheet is shuffled.
    ``sample`` keeps the operations' order, which decides between equal counts, and ``shuffle``
    reverses the sheet. No wrong answers are requested, so only operands are drawn, and every
    scripted draw must be made, from 0 to ``high``.
    """
    bounds = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_basic_operation_questions(
        len(expected), operations, high=high, wrong_answer_count=0, distinct_answers=True
    )

    assert bounds == [(0, high)] * len(drawn)
    assert [question.data for question in questions] == expected


@pytest.mark.parametrize(
    ("operations", "high", "largest_dividend", "distinct_answers", "up_to", "expected"),
    [
        # every pair from 0 to 10, as in count_possible_questions
        ([Operation.ADD], 10, None, False, 100, 66),
        # the fewer of addition's 66 and the 8 division facts with dividends up to 3
        ([Operation.ADD, Operation.DIVIDE], 10, 3, False, 100, 8),
        # dealt 5 and 6: subtraction has 6 answers (0 to 5), and addition 11 (0 to 10) for all
        ([Operation.ADD, Operation.SUBTRACT], 5, None, True, 100, 11),
        # dealt 2 and 3: subtraction's 2 answers (0 and 1) allow no more, so division takes the
        # extra question
        ([Operation.SUBTRACT, Operation.DIVIDE], 1, 100, True, 100, 5),
        # every answer from 0 to 4: subtraction has 3, multiplication 4 and addition 5
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY], 2, None, True, 100, 5),
        # the defaults with tiles: 3 each, though subtraction has only 11 answers
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            10,
            100,
            True,
            12,
            12,
        ),
        # capped
        ([Operation.ADD, Operation.SUBTRACT], 10, None, False, 4, 4),
    ],
)
def test_count_possible_sheet_questions(
    operations: list[Operation],
    high: int,
    largest_dividend: int | None,
    distinct_answers: bool,
    up_to: int,
    expected: int,
) -> None:
    """
    Without distinct answers, any one operation may be drawn for every question, so the count
    is the least of theirs. With them, it is the most questions that can be dealt out evenly.
    """
    possible = count_possible_sheet_questions(
        operations,
        high=high,
        largest_dividend=largest_dividend,
        distinct_answers=distinct_answers,
        up_to=up_to,
    )
    assert possible == expected


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
                    MultipleChoice((100, 99, 98, 7), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 0), frozenset({3})),
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
                    MultipleChoice((12, 11, 10, 1), frozenset({3})),
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
                    MultipleChoice((6, 5, 4, 1), frozenset({3})),
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
                    MultipleChoice((20, 19, 18, 4), frozenset({3})),
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
                    MultipleChoice((100, 99, 98, 7), frozenset({3})),
                ),
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (6, 2), 3),
                    MultipleChoice((100, 99, 98, 3), frozenset({3})),
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
        len(expected), [Operation.DIVIDE], low=low, high=high, largest_divisor=largest_divisor
    )

    assert asked == bounds
    assert [(q.data, q.response) for q in questions] == expected


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


GROUPS = (2, 6)  # a multiplication or division word problem's number of groups
GROUP_SIZES = (2, 20)  # and the size of each group


@pytest.mark.parametrize(
    (
        "count",
        "operations",
        "picks",
        "distinct_answers",
        "largest_number",
        "largest_operand",
        "drawn",
        "bounds",
        "expected",
    ),
    [
        # one addition, with the default limits: operands from 1 to 999
        (
            1,
            [Operation.ADD],
            [Operation.ADD],
            False,
            999,
            999,
            [1, 99],
            [(1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (1, 99),
                    100,
                    "A basket held 1 card. Maria added 99 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # The default 4. 305 - 305 is redrawn, as its difference is 0, and 300 and 645 are
        # swapped. 600 + 950 is redrawn, as its sum is over 999.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT],
            [Operation.SUBTRACT, Operation.SUBTRACT, Operation.ADD, Operation.ADD],
            False,
            999,
            999,
            [305, 305, 300, 645, 512, 48, 600, 950, 47, 925, 99, 99],
            [
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
            ],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (645, 300),
                    345,
                    "Maria needs 645 cards in all and has 300 so far. "
                    "How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (512, 48),
                    464,
                    "Maria had 512 points and lost 48 points. How many points does Maria have now?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 925),
                    972,
                    "A basket held 47 cards. Maria added 925 more. "
                    "How many cards are in the basket now?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (99, 99),
                    198,
                    "Maria scored 99 points, then scored 99 more points. How many points in all?",
                ),
            ],
        ),
        # A largest number of 99 caps the operands, and the sum too: 60 + 50 is redrawn. A
        # difference is within the first operand already.
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            [Operation.ADD, Operation.SUBTRACT],
            False,
            99,
            999,
            [60, 50, 47, 25, 25, 72],
            [(1, 99), (1, 99), (1, 99), (1, 99), (1, 99), (1, 99)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 25),
                    72,
                    "A basket held 47 cards. Maria added 25 more. "
                    "How many cards are in the basket now?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (72, 25),
                    47,
                    "Maria needs 72 cards in all and has 25 so far. "
                    "How many more cards are needed?",
                ),
            ],
        ),
        # Base-ten blocks: the operands stay within the largest operand, 599, but the sum can go
        # up to the largest number.
        (
            1,
            [Operation.ADD],
            [Operation.ADD],
            False,
            999,
            599,
            [450, 380],
            [(1, 599), (1, 599)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (450, 380),
                    830,
                    "A basket held 450 cards. Maria added 380 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # the operands are drawn up to the smaller of the two limits
        (
            1,
            [Operation.SUBTRACT],
            [Operation.SUBTRACT],
            False,
            99,
            599,
            [25, 72],
            [(1, 99), (1, 99)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (72, 25),
                    47,
                    "Maria needs 72 cards in all and has 25 so far. "
                    "How many more cards are needed?",
                ),
            ],
        ),
        # without distinct answers, 150 - 40 and 55 + 55 can both be 110
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            [Operation.SUBTRACT, Operation.ADD],
            False,
            999,
            999,
            [40, 150, 55, 55],
            [(1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (150, 40),
                    110,
                    "Maria needs 150 cards in all and has 40 so far. "
                    "How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (55, 55),
                    110,
                    "A basket held 55 cards. Maria added 55 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # with them, 55 + 55 is redrawn
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            [Operation.SUBTRACT, Operation.ADD],
            True,
            999,
            999,
            [40, 150, 55, 55, 47, 25],
            [(1, 999), (1, 999), (1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (150, 40),
                    110,
                    "Maria needs 150 cards in all and has 40 so far. "
                    "How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 25),
                    72,
                    "A basket held 47 cards. Maria added 25 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # multiplication: the groups, then the size of each, with the whole to find
        (
            1,
            [Operation.MULTIPLY],
            [Operation.MULTIPLY],
            False,
            999,
            999,
            [3, 4],
            [GROUPS, GROUP_SIZES],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 4),
                    12,
                    "3 friends each have 4 cards. How many cards do they have together?",
                ),
            ],
        ),
        # division: the same draws share the whole, 12, into 3 groups, with their size to find
        (
            1,
            [Operation.DIVIDE],
            [Operation.DIVIDE],
            False,
            999,
            999,
            [3, 4],
            [GROUPS, GROUP_SIZES],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (12, 3),
                    4,
                    "Maria divides 12 cards into 3 equal piles. How many cards are in each pile?",
                ),
            ],
        ),
        # A second 3 groups of 4 is redrawn. 4 groups of 3 is another story, so it stays, even
        # with the same answer.
        (
            2,
            [Operation.MULTIPLY],
            [Operation.MULTIPLY, Operation.MULTIPLY],
            False,
            999,
            999,
            [3, 4, 3, 4, 4, 3],
            [GROUPS, GROUP_SIZES, GROUPS, GROUP_SIZES, GROUPS, GROUP_SIZES],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 4),
                    12,
                    "3 friends each have 4 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (4, 3),
                    12,
                    "Maria buys 4 packs of cards with 3 in each pack. How many cards in all?",
                ),
            ],
        ),
        # with distinct answers, 12 shared into 3 is redrawn, as 2 groups of 2 is also 4
        (
            2,
            [Operation.MULTIPLY, Operation.DIVIDE],
            [Operation.MULTIPLY, Operation.DIVIDE],
            True,
            999,
            999,
            [2, 2, 3, 4, 3, 5],
            [GROUPS, GROUP_SIZES, GROUPS, GROUP_SIZES, GROUPS, GROUP_SIZES],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (2, 2),
                    4,
                    "2 friends each have 2 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (15, 3),
                    5,
                    "Maria divides 15 cards into 3 equal piles. How many cards are in each pile?",
                ),
            ],
        ),
        # the largest number is for addition and subtraction: 6 groups of 20 goes past 20
        (
            2,
            [Operation.ADD, Operation.MULTIPLY],
            [Operation.ADD, Operation.MULTIPLY],
            False,
            20,
            999,
            [7, 9, 6, 20],
            [(1, 20), (1, 20), GROUPS, GROUP_SIZES],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (7, 9),
                    16,
                    "A basket held 7 cards. Maria added 9 more. "
                    "How many cards are in the basket now?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (6, 20),
                    120,
                    "6 friends each have 20 cards. How many cards do they have together?",
                ),
            ],
        ),
    ],
)
def test_word_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    picks: list[Operation],
    distinct_answers: bool,
    largest_number: int,
    largest_operand: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each problem's numbers are drawn, and redrawn until they meet the limits and repeat no
    problem: an addition's or subtraction's operands, and a multiplication's or division's groups
    and size of each.

    ``picks`` are the operations drawn, and the wording is scripted as in ``test_word_problems``.
    Every scripted draw must be made, within ``bounds``. The problems are free response, with no
    wrong answers.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    choices_returns(monkeypatch, picks)
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    questions = generate_word_problems(
        count,
        operations,
        distinct_answers=distinct_answers,
        largest_number=largest_number,
        largest_operand=largest_operand,
    )

    assert drawn_from == bounds
    assert questions == [Question(data, FreeResponse()) for data in expected]


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "largest_operand"),
    [
        # the most problems allowed, 20
        ([Operation.ADD, Operation.SUBTRACT], 20, 999, 999),
        # the most division allows, with its 19 answers, 2 to 20
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 19, 999, 999),
        # The most a largest number of 15 allows: 14 sums, 2 to 15, and 14 differences, 1 to 14.
        # Every answer is used, so the last problems are found by redrawing.
        ([Operation.ADD, Operation.SUBTRACT], 14, 15, 999),
        # base-ten blocks
        ([Operation.ADD, Operation.SUBTRACT], 20, 999, 599),
    ],
)
def test_random_word_problems_have_distinct_answers(
    operations: list[Operation], count: int, largest_number: int, largest_operand: int
) -> None:
    """A sheet of the most problems the limits allow is produced with no answer repeated."""
    questions = generate_word_problems(
        count,
        operations,
        distinct_answers=True,
        largest_number=largest_number,
        largest_operand=largest_operand,
    )
    assert len({question.data.answer for question in questions}) == count


@pytest.mark.parametrize(
    ("operations", "distinct_answers", "up_to", "largest_number", "largest_operand", "expected"),
    [
        # addition's answers, the sums from 1 + 1 to 999
        ([Operation.ADD], False, 1000, 999, 999, 998),
        ([Operation.ADD], True, 1000, 999, 999, 998),
        # subtraction's, the differences from 1 to 999 - 1
        ([Operation.SUBTRACT], True, 1000, 999, 999, 998),
        # with a largest number of 20
        ([Operation.ADD], True, 100, 20, 999, 19),
        ([Operation.SUBTRACT], True, 100, 20, 999, 19),
        # base-ten blocks: the operands stop at 599, but a sum can still reach 999
        ([Operation.ADD], True, 1000, 999, 599, 998),
        ([Operation.SUBTRACT], True, 1000, 999, 599, 598),
        # the smallest largest number with a sum, 1 + 1, and a difference, 2 - 1
        ([Operation.ADD], True, 100, 2, 999, 1),
        ([Operation.SUBTRACT], True, 100, 2, 999, 1),
        # below that, none
        ([Operation.ADD], True, 100, 1, 999, 0),
        ([Operation.SUBTRACT], True, 100, 1, 999, 0),
        # 5 group counts (2 to 6) times 19 sizes (2 to 20)
        ([Operation.MULTIPLY], False, 100, 999, 999, 95),
        ([Operation.DIVIDE], False, 100, 999, 999, 95),
        # the distinct products of those
        ([Operation.MULTIPLY], True, 100, 999, 999, 59),
        # a division's answer is the size of each group
        ([Operation.DIVIDE], True, 100, 999, 999, 19),
        # multiplication and division ignore the largest number
        ([Operation.DIVIDE], True, 100, 20, 999, 19),
        # the least of the operations'
        ([Operation.ADD, Operation.DIVIDE], True, 100, 999, 999, 19),
        ([Operation.ADD, Operation.DIVIDE], True, 100, 10, 999, 9),
        # capped
        ([Operation.MULTIPLY, Operation.DIVIDE], False, 12, 999, 999, 12),
    ],
)
def test_count_possible_word_problems(
    operations: list[Operation],
    distinct_answers: bool,
    up_to: int,
    largest_number: int,
    largest_operand: int,
    expected: int,
) -> None:
    """
    Any one operation may be drawn for every problem, so the count is the least of theirs.
    Addition and subtraction count their answers, with distinct answers or not.
    """
    possible = count_possible_word_problems(
        operations,
        distinct_answers=distinct_answers,
        up_to=up_to,
        largest_number=largest_number,
        largest_operand=largest_operand,
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "distinct_answers", "count", "largest_number", "message"),
    [
        (
            [Operation.DIVIDE],
            True,
            20,
            999,
            "Cannot make 20 problems with different answers: only 19 possible.",
        ),
        (
            [Operation.ADD, Operation.SUBTRACT],
            True,
            15,
            15,
            "Cannot make 15 problems with different answers: only 14 possible.",
        ),
        (
            [Operation.ADD],
            False,
            1,
            1,
            "Cannot make 1 different problems: only 0 possible.",
        ),
        (
            [Operation.MULTIPLY],
            False,
            96,
            999,
            "Cannot make 96 different problems: only 95 possible.",
        ),
    ],
)
def test_word_problem_sheet_errors(
    operations: list[Operation],
    distinct_answers: bool,
    count: int,
    largest_number: int,
    message: str,
) -> None:
    """
    Requesting more problems than the operations and limits allow raises ``ValueError`` saying
    how many.

    Without that check, generation would loop forever looking for an answer or a problem that
    does not exist.
    """
    with pytest.raises(ValueError) as error:
        generate_word_problems(
            count, operations, distinct_answers=distinct_answers, largest_number=largest_number
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("count", "operations", "largest_number", "largest_groups", "drawn", "bounds", "expected"),
    [
        # The defaults, a largest number of 100 and 12 groups: one of each operation, then the
        # sheet is shuffled. An addition's or subtraction's smaller number is at most 12.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            100,
            12,
            [3, 4, 3, 4, 47, 9, 47, 5],
            [(2, 12), (2, 20), (2, 12), (2, 20), (1, 100), (1, 12), (1, 100), (1, 12)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (12, 3),
                    4,
                    "Maria divides 12 cards into 3 equal piles. How many cards are in each pile?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 4),
                    12,
                    "3 friends each have 4 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria needs 47 cards in all and has 9 so far. How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # the largest number caps a dividend and a product too: 6 groups of 20 and 12 groups of
        # 20 are over 100, so they're redrawn
        (
            2,
            [Operation.MULTIPLY, Operation.DIVIDE],
            100,
            12,
            [6, 20, 4, 5, 12, 20, 6, 7],
            [(2, 12), (2, 20), (2, 12), (2, 20), (2, 12), (2, 20), (2, 12), (2, 20)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (20, 4),
                    5,
                    "Maria divides 20 cards into 4 equal piles. How many cards are in each pile?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (6, 7),
                    42,
                    "6 friends each have 7 cards. How many cards do they have together?",
                ),
            ],
        ),
        # 2 groups of 2 and 2 + 2 draw the same strip, so both are redrawn
        (
            2,
            [Operation.ADD, Operation.MULTIPLY],
            100,
            12,
            [2, 2, 2, 3, 2, 2, 2, 3],
            [(2, 12), (2, 20), (2, 12), (2, 20), (1, 100), (1, 12), (1, 100), (1, 12)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (2, 3),
                    6,
                    "2 friends each have 3 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (2, 3),
                    5,
                    "A basket held 2 cards. Maria added 3 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # A largest number of groups of 5 caps every strip's groups: a division's and a
        # multiplication's, and an addition's or subtraction's smaller number. Every number can
        # still reach 100.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            100,
            5,
            [5, 20, 5, 20, 100, 5, 95, 5],
            [(2, 5), (2, 20), (2, 5), (2, 20), (1, 100), (1, 5), (1, 100), (1, 5)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (100, 5),
                    20,
                    "Maria divides 100 cards into 5 equal piles. How many cards are in each pile?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (5, 20),
                    100,
                    "5 friends each have 20 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (100, 5),
                    95,
                    "Maria needs 100 cards in all and has 5 so far. "
                    "How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (95, 5),
                    100,
                    "A basket held 95 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # 3 problems split between 2 operations: the extra goes to the last, subtraction
        (
            3,
            [Operation.ADD, Operation.SUBTRACT],
            100,
            12,
            [47, 9, 60, 12, 47, 5],
            [(1, 100), (1, 12), (1, 100), (1, 12), (1, 100), (1, 12)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria needs 47 cards in all and has 9 so far. How many more cards are needed?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (60, 12),
                    48,
                    "Maria had 60 points and lost 12 points. How many points does Maria have now?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # a largest number under 12 caps the smaller number first, and 7 + 6 is over 10
        (
            1,
            [Operation.ADD],
            10,
            12,
            [7, 6, 3, 6],
            [(1, 10), (1, 10), (1, 10), (1, 10)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (3, 6),
                    9,
                    "A basket held 3 cards. Maria added 6 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
    ],
)
def test_strip_choice_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    largest_number: int,
    largest_groups: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The operations are split evenly, then the sheet is shuffled. Each problem's numbers are
    drawn, and redrawn until they meet the limits and aren't left out: every number at most the
    largest number, a dividend and a product included, and no strip of more groups than the
    largest number of groups.

    ``sample`` keeps the operations' order, so any extra problems go to the last, and ``shuffle``
    reverses the sheet and each problem's choices. The wording takes the first two names, the last
    object and each operation's templates from the last. Every scripted draw must be made, within
    ``bounds``. Each problem's choices are those of ``strip_choices``, tested in
    ``test_representation``.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    choose_last(monkeypatch)

    questions = generate_strip_choice_problems(
        count, operations, largest_number=largest_number, largest_groups=largest_groups
    )

    assert drawn_from == bounds
    assert questions == [Question(data, strip_choices(data)) for data in expected]


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "largest_groups"),
    [
        # every multiplication within 20 but 2 groups of 2
        ([Operation.MULTIPLY], 26, 20, 12),
        # one of each, with 2 groups of 3 the only multiplication
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 4, 6, 2),
        # the most problems allowed, 20, with the defaults
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 20, 100, 12),
    ],
)
def test_random_strip_choice_sheets_can_always_be_finished(
    operations: list[Operation], count: int, largest_number: int, largest_groups: int
) -> None:
    """A sheet of the most problems the limits allow is produced, with no problem repeated."""
    questions = generate_strip_choice_problems(
        count, operations, largest_number=largest_number, largest_groups=largest_groups
    )
    problems = {(question.data.operation, question.data.operands) for question in questions}
    assert len(problems) == count


@pytest.mark.parametrize(
    ("operations", "up_to", "largest_number", "largest_groups", "expected"),
    [
        # the defaults: the sums from 1 + 1 to 100, and the differences from 1 to 99
        ([Operation.ADD], 1000, 100, 12, 99),
        ([Operation.SUBTRACT], 1000, 100, 12, 99),
        # 2 to 12 groups of 2 to 20 within 100, but 2 groups of 2
        ([Operation.MULTIPLY], 1000, 100, 12, 148),
        # every one of those shared, as 4 shared into 2 draws a strip of its own
        ([Operation.DIVIDE], 1000, 100, 12, 149),
        # 2 groups only: of 3 to 20, or 4 to 40 shared into them
        ([Operation.MULTIPLY], 1000, 100, 2, 18),
        ([Operation.DIVIDE], 1000, 100, 2, 19),
        # the largest number caps the product too
        ([Operation.MULTIPLY], 1000, 20, 12, 26),
        # the sums from 1 + 1 to 10
        ([Operation.ADD], 1000, 10, 12, 9),
        # Split evenly, each operation needs only its share: 2 groups of 3, the only
        # multiplication, is enough for 1 of 2 problems, and 1 of 4.
        ([Operation.ADD, Operation.MULTIPLY], 1000, 6, 2, 2),
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 1000, 6, 2, 4),
        # 2 groups of 2 is the only multiplication within 5 in 2 groups, and it's left out
        ([Operation.ADD, Operation.MULTIPLY], 1000, 5, 2, 0),
        # capped
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            20,
            100,
            12,
            20,
        ),
    ],
)
def test_count_possible_strip_choice_problems(
    operations: list[Operation],
    up_to: int,
    largest_number: int,
    largest_groups: int,
    expected: int,
) -> None:
    """
    Each operation counts as on word problems, except that the largest number caps a product or
    dividend too, and 2 groups of 2 is left out. Split evenly, the count is the least of the
    operations' for each operation.
    """
    possible = count_possible_strip_choice_problems(
        operations, up_to=up_to, largest_number=largest_number, largest_groups=largest_groups
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "largest_groups", "message"),
    [
        # 2 groups of 2 is left out, and no other multiplication is within 5 in 2 groups
        (
            [Operation.ADD, Operation.MULTIPLY],
            1,
            5,
            2,
            "Cannot make 1 different problems: only 0 possible.",
        ),
        (
            [Operation.MULTIPLY],
            27,
            20,
            12,
            "Cannot make 27 different problems: only 26 possible.",
        ),
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            5,
            6,
            2,
            "Cannot make 5 different problems: only 4 possible.",
        ),
    ],
)
def test_strip_choice_sheet_errors(
    operations: list[Operation],
    count: int,
    largest_number: int,
    largest_groups: int,
    message: str,
) -> None:
    """
    Requesting more problems than the operations and limits allow raises ``ValueError`` saying
    how many.
    """
    with pytest.raises(ValueError) as error:
        generate_strip_choice_problems(
            count, operations, largest_number=largest_number, largest_groups=largest_groups
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("count", "operations", "largest_number", "drawn", "bounds", "expected"),
    [
        # The defaults: one of each operation, then the sheet is shuffled. Multiplication and
        # division are 2 to 6 groups of 2 to 20, as on any word problem. Subtraction is worded with
        # its comparison, the last of its templates.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            999,
            [3, 4, 3, 4, 47, 9, 47, 5],
            [(2, 6), (2, 20), (2, 6), (2, 20), (1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (12, 3),
                    4,
                    "Maria divides 12 cards into 3 equal piles. How many cards are in each pile?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 4),
                    12,
                    "3 friends each have 4 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria has 47 cards and Jamal has 9 cards. "
                    "How many more cards does Maria have than Jamal?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # 2 groups of 2 is 4, as 2 + 2 is, and 4 - 2 is 2, as 4 ÷ 2 is, so both are redrawn
        (
            2,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            999,
            [2, 2, 2, 3, 4, 2, 4, 3],
            [(2, 6), (2, 20), (2, 6), (2, 20), (1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (2, 3),
                    6,
                    "2 friends each have 3 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (4, 3),
                    1,
                    "Maria has 4 cards and Jamal has 3 cards. "
                    "How many more cards does Maria have than Jamal?",
                ),
            ],
        ),
        # 4 shared into 2 and 2 + 2 are redrawn too, and so is 4 + 2, though none of its wrong
        # equations is 6. 2 + 4 isn't left out.
        (
            2,
            [Operation.ADD, Operation.DIVIDE],
            999,
            [2, 2, 2, 3, 2, 2, 4, 2, 2, 4],
            [
                (2, 6),
                (2, 20),
                (2, 6),
                (2, 20),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
                (1, 999),
            ],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (6, 2),
                    3,
                    "Maria divides 6 cards into 2 equal piles. How many cards are in each pile?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (2, 4),
                    6,
                    "A basket held 2 cards. Maria added 4 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # the largest number caps an addition, so 7 + 6 is redrawn, but not a product
        (
            2,
            [Operation.ADD, Operation.MULTIPLY],
            10,
            [6, 20, 7, 6, 3, 6],
            [(2, 6), (2, 20), (1, 10), (1, 10), (1, 10), (1, 10)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (6, 20),
                    120,
                    "6 friends each have 20 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (3, 6),
                    9,
                    "A basket held 3 cards. Maria added 6 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # 3 problems split between 2 operations: the extra goes to the last, subtraction, whose
        # second problem takes the next of its comparisons
        (
            3,
            [Operation.ADD, Operation.SUBTRACT],
            999,
            [47, 9, 60, 12, 47, 5],
            [(1, 999), (1, 999), (1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria has 47 cards and Jamal has 9 cards. "
                    "How many more cards does Maria have than Jamal?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (60, 12),
                    48,
                    "A school sold 60 tickets on Friday and 12 tickets on Saturday. "
                    "How many more tickets were sold on Friday than on Saturday?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
    ],
)
def test_equation_choice_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    largest_number: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The operations are split evenly, then the sheet is shuffled. Each problem's numbers are
    drawn, and redrawn until they meet the limits and aren't left out: an addition's or
    subtraction's numbers at most the largest number, and no operands of 2 and 2, or 4 and 2.

    ``sample`` keeps the operations' order, so any extra problems go to the last, and ``shuffle``
    reverses the sheet and each problem's choices. The wording takes the first two names, the last
    object and each operation's templates from the last, comparisons included. Every scripted draw
    must be made, within ``bounds``. Each problem's choices are those of ``equation_choices``,
    tested in ``test_representation``.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    choose_last(monkeypatch)

    questions = generate_equation_choice_problems(count, operations, largest_number=largest_number)

    assert drawn_from == bounds
    assert questions == [Question(data, equation_choices(data)) for data in expected]


@pytest.mark.parametrize(
    ("operations", "count", "largest_number"),
    [
        # every multiplication but 2 groups of 2 and 4 groups of 2
        ([Operation.MULTIPLY], 93, 999),
        # every division but 4 shared into 2
        ([Operation.DIVIDE], 94, 999),
        # the sums 2 to 4, with 2 + 2 left out
        ([Operation.ADD], 3, 4),
        # the most problems allowed, 20, with the defaults
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 20, 999),
    ],
)
def test_random_equation_choice_sheets_can_always_be_finished(
    operations: list[Operation], count: int, largest_number: int
) -> None:
    """A sheet of the most problems the limits allow is produced, with no problem repeated."""
    questions = generate_equation_choice_problems(count, operations, largest_number=largest_number)
    problems = {(question.data.operation, question.data.operands) for question in questions}
    assert len(problems) == count


@pytest.mark.parametrize(
    ("operations", "up_to", "largest_number", "expected"),
    [
        # the defaults: the sums from 1 + 1 to 999, and the differences from 1 to 998
        ([Operation.ADD], 1000, 999, 998),
        ([Operation.SUBTRACT], 1000, 999, 998),
        # 2 to 6 groups of 2 to 20, but 2 groups of 2 and 4 groups of 2
        ([Operation.MULTIPLY], 1000, 999, 93),
        # every one of those shared, but 4 shared into 2
        ([Operation.DIVIDE], 1000, 999, 94),
        # the largest number doesn't cap a product
        ([Operation.MULTIPLY], 1000, 10, 93),
        # the sums from 1 + 1 to 10
        ([Operation.ADD], 1000, 10, 9),
        # Split evenly, each operation needs only its share: addition's 2 sums within 3 are
        # enough for 2 of 4 problems.
        ([Operation.ADD, Operation.MULTIPLY], 1000, 3, 4),
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 1000, 999, 372),
        # capped
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 20, 999, 20),
    ],
)
def test_count_possible_equation_choice_problems(
    operations: list[Operation], up_to: int, largest_number: int, expected: int
) -> None:
    """
    Each operation counts as on word problems, except that 2 groups of 2, 4 groups of 2 and 4
    shared into 2 are left out. Split evenly, the count is the least of the operations' for each
    operation.
    """
    possible = count_possible_equation_choice_problems(
        operations, up_to=up_to, largest_number=largest_number
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "message"),
    [
        (
            [Operation.MULTIPLY],
            94,
            999,
            "Cannot make 94 different problems: only 93 possible.",
        ),
        (
            [Operation.ADD],
            10,
            10,
            "Cannot make 10 different problems: only 9 possible.",
        ),
        # split evenly: addition's 2 sums within 3 aren't enough for 3 of 6 problems
        (
            [Operation.ADD, Operation.MULTIPLY],
            6,
            3,
            "Cannot make 6 different problems: only 4 possible.",
        ),
    ],
)
def test_equation_choice_sheet_errors(
    operations: list[Operation], count: int, largest_number: int, message: str
) -> None:
    """
    Requesting more problems than the operations and limits allow raises ``ValueError`` saying
    how many.
    """
    with pytest.raises(ValueError) as error:
        generate_equation_choice_problems(count, operations, largest_number=largest_number)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("count", "operations", "largest_number", "drawn", "bounds", "expected"),
    [
        # The defaults: one of each, then the sheet is shuffled. The addition, drawn 5 and 47,
        # puts its larger number first. Subtraction is worded with its comparison.
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            999,
            [9, 47, 5, 47],
            [(1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria has 47 cards and Jamal has 9 cards. "
                    "How many more cards does Maria have than Jamal?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # an addition's numbers differ, so 30 + 30 is redrawn
        (
            1,
            [Operation.ADD],
            999,
            [30, 30, 47, 5],
            [(1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # the largest number caps the sum, so 50 + 60, put in order as 60 + 50, is redrawn
        (
            1,
            [Operation.ADD],
            100,
            [50, 60, 47, 5],
            [(1, 100), (1, 100), (1, 100), (1, 100)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
        # 3 problems split between 2 operations: the extra goes to the last, subtraction, whose
        # second problem takes the next of its comparisons
        (
            3,
            [Operation.ADD, Operation.SUBTRACT],
            999,
            [47, 9, 60, 12, 5, 47],
            [(1, 999), (1, 999), (1, 999), (1, 999), (1, 999), (1, 999)],
            [
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (47, 9),
                    38,
                    "Maria has 47 cards and Jamal has 9 cards. "
                    "How many more cards does Maria have than Jamal?",
                ),
                BasicOperationQuestionData(
                    Operation.SUBTRACT,
                    (60, 12),
                    48,
                    "A school sold 60 tickets on Friday and 12 tickets on Saturday. "
                    "How many more tickets were sold on Friday than on Saturday?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (47, 5),
                    52,
                    "A basket held 47 cards. Maria added 5 more. "
                    "How many cards are in the basket now?",
                ),
            ],
        ),
    ],
)
def test_number_line_choice_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    largest_number: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The operations are split evenly, then the sheet is shuffled. Each problem's numbers are
    drawn, and redrawn until they meet the limits: every number at most the largest number, and an
    addition's numbers different, with the larger first.

    ``sample`` keeps the operations' order, so any extra problems go to the last, and ``shuffle``
    reverses the sheet and each problem's choices. The wording takes the first two names, the last
    object and each operation's templates from the last, comparisons included, and each wrong
    landing tries below the answer first. Every scripted draw must be made, within ``bounds``.
    Each problem's choices are those of ``number_line_choices``, tested in
    ``test_representation``.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    choose_last(monkeypatch)

    questions = generate_number_line_choice_problems(
        count, operations, largest_number=largest_number
    )

    assert drawn_from == bounds
    assert questions == [Question(data, number_line_choices(data)) for data in expected]


@pytest.mark.parametrize(
    ("operations", "count", "largest_number"),
    [
        # 2 + 1 and 3 + 1, the only additions within 4 with different numbers
        ([Operation.ADD], 2, 4),
        # the differences 1 to 3
        ([Operation.SUBTRACT], 3, 4),
        # one of each, at the smallest largest number with an addition
        ([Operation.ADD, Operation.SUBTRACT], 2, 3),
        # the most problems allowed, 20, with the defaults
        ([Operation.ADD, Operation.SUBTRACT], 20, 999),
    ],
)
def test_random_number_line_choice_sheets_can_always_be_finished(
    operations: list[Operation], count: int, largest_number: int
) -> None:
    """
    A sheet of the most problems the limits allow is produced, with no problem repeated, and
    every problem has its number lines to choose from.
    """
    questions = generate_number_line_choice_problems(
        count, operations, largest_number=largest_number
    )
    problems = {(question.data.operation, question.data.operands) for question in questions}
    assert len(problems) == count


@pytest.mark.parametrize(
    ("operations", "up_to", "largest_number", "expected"),
    [
        # the sums from 2 + 1 to 999, as 1 + 1 has the same numbers
        ([Operation.ADD], 2000, 999, 997),
        # the differences from 1 to 998, as on any word problem
        ([Operation.SUBTRACT], 2000, 999, 998),
        # only 2 + 1, and below that, none
        ([Operation.ADD], 2000, 3, 1),
        ([Operation.ADD], 2000, 2, 0),
        # Split evenly, each operation needs only its share: addition's 1 sum within 3 is
        # enough for 1 of 2 problems.
        ([Operation.ADD, Operation.SUBTRACT], 2000, 3, 2),
        ([Operation.ADD, Operation.SUBTRACT], 2000, 999, 1994),
        # capped
        ([Operation.ADD, Operation.SUBTRACT], 20, 999, 20),
    ],
)
def test_count_possible_number_line_choice_problems(
    operations: list[Operation], up_to: int, largest_number: int, expected: int
) -> None:
    """
    Subtraction counts as on word problems, and addition counts the sums of two different numbers.
    Split evenly, the count is the least of the operations' for each operation.
    """
    possible = count_possible_number_line_choice_problems(
        operations, up_to=up_to, largest_number=largest_number
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "message"),
    [
        (
            [Operation.ADD],
            2,
            3,
            "Cannot make 2 different problems: only 1 possible.",
        ),
        (
            [Operation.ADD],
            1,
            2,
            "Cannot make 1 different problems: only 0 possible.",
        ),
        # split evenly: addition's 1 sum within 3 isn't enough for 2 of 3 problems
        (
            [Operation.ADD, Operation.SUBTRACT],
            3,
            3,
            "Cannot make 3 different problems: only 2 possible.",
        ),
    ],
)
def test_number_line_choice_sheet_errors(
    operations: list[Operation], count: int, largest_number: int, message: str
) -> None:
    """
    Requesting more problems than the operations and limits allow raises ``ValueError`` saying
    how many.
    """
    with pytest.raises(ValueError) as error:
        generate_number_line_choice_problems(count, operations, largest_number=largest_number)
    assert str(error.value) == message


# the shapes of two-step problem: the steps' operations, and the second step's operand carried
ADD_THEN_ADD = (Operation.ADD, Operation.ADD, Unknown.FIRST)
SUBTRACT_THEN_SUBTRACT = (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST)
SUBTRACT_THEN_DIVIDE = (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST)
MULTIPLY_THEN_ADD = (Operation.MULTIPLY, Operation.ADD, Unknown.FIRST)
MULTIPLY_THEN_SUBTRACT = (Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND)
# and some of the shapes only text only shows; in the _GROUPS ones the first step's answer is
# the number of groups, and otherwise the size of each group
ADD_THEN_MULTIPLY = (Operation.ADD, Operation.MULTIPLY, Unknown.SECOND)
ADD_THEN_MULTIPLY_GROUPS = (Operation.ADD, Operation.MULTIPLY, Unknown.FIRST)
MULTIPLY_THEN_MULTIPLY = (Operation.MULTIPLY, Operation.MULTIPLY, Unknown.SECOND)
MULTIPLY_THEN_MULTIPLY_GROUPS = (Operation.MULTIPLY, Operation.MULTIPLY, Unknown.FIRST)
DIVIDE_THEN_SUBTRACT = (Operation.DIVIDE, Operation.SUBTRACT, Unknown.FIRST)
DIVIDE_THEN_DIVIDE = (Operation.DIVIDE, Operation.DIVIDE, Unknown.FIRST)
CARDS = ("card", "cards")  # the object chosen for a problem's wording


@pytest.mark.parametrize(
    (
        "count",
        "operations",
        "picks",
        "distinct_answers",
        "largest_number",
        "largest_groups",
        "chosen",
        "expected",
    ),
    [
        # what's left of 24 after 6, shared into 3, with the default limits
        (
            1,
            [Operation.SUBTRACT, Operation.DIVIDE],
            [SUBTRACT_THEN_DIVIDE],
            False,
            999,
            6,
            [
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                        BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                    ),
                    Unknown.FIRST,
                    6,
                    "Maria has 24 cards. 6 are in a box, and the rest are in 3 bags with the same "
                    "number in each bag. How many cards are in each bag?",
                ),
            ],
        ),
        # the first step's answer taken from the whole, the second step's first operand
        (
            1,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            [MULTIPLY_THEN_SUBTRACT],
            False,
            999,
            6,
            [
                15,
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                        BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
                    ),
                    Unknown.SECOND,
                    30,
                    "A store had 45 cards. It sold 3 packs with 5 cards in each pack. "
                    "How many cards does the store have left?",
                ),
            ],
        ),
        # adding three numbers
        (
            1,
            [Operation.ADD],
            [ADD_THEN_ADD],
            False,
            999,
            6,
            [
                10,
                BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                    ),
                    Unknown.FIRST,
                    17,
                    "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                    "How many cards are in the jar now?",
                ),
            ],
        ),
        # equal groups, with a part added
        (
            1,
            [Operation.ADD, Operation.MULTIPLY],
            [MULTIPLY_THEN_ADD],
            False,
            999,
            6,
            [
                15,
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                        BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
                    ),
                    Unknown.FIRST,
                    19,
                    "There are 3 boxes with 5 cards in each box. Maria brings 4 more. "
                    "How many cards are there now?",
                ),
            ],
        ),
        # a repeated problem is redrawn, and each problem has its own template
        (
            2,
            [Operation.SUBTRACT],
            [SUBTRACT_THEN_SUBTRACT, SUBTRACT_THEN_SUBTRACT],
            False,
            999,
            6,
            [
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 7), 13),
                CARDS,
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                    ),
                    Unknown.FIRST,
                    12,
                    "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                    "How many cards are left in the box?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 7), 13),
                    ),
                    Unknown.FIRST,
                    13,
                    "Maria had 25 cards. Maria gave 5 to Jamal and then lost 7. "
                    "How many cards does Maria have left?",
                ),
            ],
        ),
        # with distinct answers, a second answer of 17 is redrawn
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            [ADD_THEN_ADD, SUBTRACT_THEN_SUBTRACT],
            True,
            999,
            6,
            [
                10,
                BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 3), 17),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                CARDS,
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                    ),
                    Unknown.FIRST,
                    17,
                    "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                    "How many cards are in the jar now?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                    ),
                    Unknown.FIRST,
                    12,
                    "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                    "How many cards are left in the box?",
                ),
            ],
        ),
        # without, it's kept
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            [ADD_THEN_ADD, SUBTRACT_THEN_SUBTRACT],
            False,
            999,
            6,
            [
                10,
                BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 3), 17),
                CARDS,
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                    ),
                    Unknown.FIRST,
                    17,
                    "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                    "How many cards are in the jar now?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 3), 17),
                    ),
                    Unknown.FIRST,
                    17,
                    "A box held 25 cards. Maria took out 5, and then Jamal took out 3. "
                    "How many cards are left in the box?",
                ),
            ],
        ),
        # with up to 12 groups, 18 can be shared into 9
        (
            1,
            [Operation.SUBTRACT, Operation.DIVIDE],
            [SUBTRACT_THEN_DIVIDE],
            False,
            999,
            12,
            [
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 9), 2),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                        BasicOperationQuestionData(Operation.DIVIDE, (18, 9), 2),
                    ),
                    Unknown.FIRST,
                    2,
                    "Maria has 24 cards. 6 are in a box, and the rest are in 9 bags with the same "
                    "number in each bag. How many cards are in each bag?",
                ),
            ],
        ),
        # dividing twice: the first answer, 30, can go past the largest group size, 20
        (
            1,
            [Operation.DIVIDE],
            [DIVIDE_THEN_DIVIDE],
            False,
            999,
            6,
            [
                30,
                BasicOperationQuestionData(Operation.DIVIDE, (60, 2), 30),
                BasicOperationQuestionData(Operation.DIVIDE, (30, 3), 10),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (60, 2), 30),
                        BasicOperationQuestionData(Operation.DIVIDE, (30, 3), 10),
                    ),
                    Unknown.FIRST,
                    10,
                    "Maria puts 60 cards into 2 equal boxes, then splits each box's cards equally "
                    "into 3 bags. How many cards are in each bag?",
                ),
            ],
        ),
        # the first step's answer is the size of each group, the second step's second operand
        (
            1,
            [Operation.ADD, Operation.MULTIPLY],
            [ADD_THEN_MULTIPLY],
            False,
            999,
            6,
            [
                6,
                BasicOperationQuestionData(Operation.ADD, (2, 4), 6),
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 6), 18),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (2, 4), 6),
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 6), 18),
                    ),
                    Unknown.SECOND,
                    18,
                    "Each of 3 bags has 2 cards from Maria and 4 from Jamal. "
                    "How many cards are in the bags altogether?",
                ),
            ],
        ),
        (
            1,
            [Operation.SUBTRACT, Operation.DIVIDE],
            [DIVIDE_THEN_SUBTRACT],
            False,
            999,
            6,
            [
                6,
                BasicOperationQuestionData(Operation.DIVIDE, (24, 4), 6),
                BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 4), 6),
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                    ),
                    Unknown.FIRST,
                    4,
                    "24 cards are put into 4 equal boxes. Maria takes 2 out of one box. "
                    "How many cards are left in that box?",
                ),
            ],
        ),
    ],
)
def test_two_step_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    picks: list[TwoStepShape],
    distinct_answers: bool,
    largest_number: int,
    largest_groups: int,
    chosen: list[object],
    expected: list[TwoStepQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each problem's shape is drawn, as ``picks``. Then ``chosen`` lists the draws: for each
    problem, the number its first step carries into its second, then each step, redrawn while the
    problem repeats a problem, or with ``distinct_answers`` an answer; then the object for each
    problem's wording.

    Every pick must be among those offered, as listed in
    ``test_two_step_problems_offer_only_steps_that_repeat_no_number``. The wording takes the first
    two names and each shape's templates from the last. The problems are free response, with no
    wrong answers.
    """
    choices_returns(monkeypatch, picks)
    choice_returns(monkeypatch, chosen)
    sample_first(monkeypatch)

    questions = generate_two_step_problems(
        count,
        operations,
        distinct_answers=distinct_answers,
        largest_number=largest_number,
        largest_groups=largest_groups,
    )

    assert questions == [Question(data, FreeResponse()) for data in expected]


@pytest.mark.parametrize(
    ("operations", "picks", "largest_number", "chosen", "offered"),
    [
        # Three numbers that make at most 7: 7 can't be carried, as nothing is left to add, and
        # 4 is 1 + 3 or 3 + 1, but not 2 + 2. After 1 + 3, only 2 can be added, not 1 or 3.
        (
            [Operation.ADD],
            [ADD_THEN_ADD],
            7,
            [
                4,
                BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                BasicOperationQuestionData(Operation.ADD, (4, 2), 6),
                CARDS,
            ],
            [
                [3, 4, 5, 6],
                [
                    BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                    BasicOperationQuestionData(Operation.ADD, (3, 1), 4),
                ],
                [BasicOperationQuestionData(Operation.ADD, (4, 2), 6)],
                OBJECTS,
            ],
        ),
        # Equal groups with a part added, within 10: 4 and 9 can't be carried, as 2 groups of 2
        # and 3 groups of 3 repeat a number. After 2 groups of 3, neither 2 nor 3 can be added.
        (
            [Operation.ADD, Operation.MULTIPLY],
            [MULTIPLY_THEN_ADD],
            10,
            [
                6,
                BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                BasicOperationQuestionData(Operation.ADD, (6, 4), 10),
                CARDS,
            ],
            [
                [6, 8],
                [
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 2), 6),
                ],
                [
                    BasicOperationQuestionData(Operation.ADD, (6, 1), 7),
                    BasicOperationQuestionData(Operation.ADD, (6, 4), 10),
                ],
                OBJECTS,
            ],
        ),
    ],
)
def test_two_step_problems_offer_only_steps_that_repeat_no_number(
    operations: list[Operation],
    picks: list[TwoStepShape],
    largest_number: int,
    chosen: list[object],
    offered: list[object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each draw offers only what can make a problem that repeats none of its given numbers, so no
    problem is drawn again for that. ``offered`` lists what each draw is chosen from: the numbers
    the first step can carry, then the first steps, the second steps, and the objects.
    """
    choices_returns(monkeypatch, picks)
    drawn_from = choice_returns(monkeypatch, chosen)
    sample_first(monkeypatch)

    generate_two_step_problems(1, operations, largest_number=largest_number)

    assert drawn_from == offered


@pytest.mark.parametrize(
    ("operations", "largest_number", "expected"),
    [
        # multiplying twice can't be done within 10, either way, so the other four shapes take
        # turns
        (
            [Operation.ADD, Operation.MULTIPLY],
            10,
            [
                ADD_THEN_ADD,
                ADD_THEN_MULTIPLY,
                ADD_THEN_MULTIPLY_GROUPS,
                MULTIPLY_THEN_ADD,
                ADD_THEN_ADD,
                ADD_THEN_MULTIPLY,
            ],
        ),
        # within 36 it can, both ways, with 6 problems each, so each takes its turn
        (
            [Operation.ADD, Operation.MULTIPLY],
            36,
            [
                ADD_THEN_ADD,
                ADD_THEN_MULTIPLY,
                ADD_THEN_MULTIPLY_GROUPS,
                MULTIPLY_THEN_ADD,
                MULTIPLY_THEN_MULTIPLY,
                MULTIPLY_THEN_MULTIPLY_GROUPS,
            ],
        ),
    ],
)
def test_two_step_problems_draw_only_the_shapes_the_limits_allow(
    operations: list[Operation],
    largest_number: int,
    expected: list[TwoStepShape],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ``choices`` takes the shapes it's offered in turn, in the bank's order, so the problems'
    shapes show which were offered.
    """
    choices_in_turn(monkeypatch)

    questions = generate_two_step_problems(6, operations, largest_number=largest_number)

    assert [question.data.shape for question in questions] == expected


@pytest.mark.parametrize(
    ("operations", "count", "largest_number"),
    [
        # tiles: 12 answers with the defaults
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 12, 999),
        # Sharing what's left: every answer, the sizes 2 to 20. The last are found by redrawing.
        ([Operation.SUBTRACT, Operation.DIVIDE], 19, 999),
        # adding three numbers within 20: every answer, 6 to 20
        ([Operation.ADD], 15, 20),
        # the shapes that only multiply and divide
        ([Operation.MULTIPLY, Operation.DIVIDE], 12, 999),
    ],
)
def test_random_two_step_problems_have_distinct_answers(
    operations: list[Operation], count: int, largest_number: int
) -> None:
    """A sheet of the most problems the limits allow is produced with no answer repeated."""
    questions = generate_two_step_problems(
        count, operations, distinct_answers=True, largest_number=largest_number
    )
    assert len({question.data.answer for question in questions}) == count


@pytest.mark.parametrize(
    (
        "operations",
        "distinct_answers",
        "up_to",
        "largest_number",
        "largest_groups",
        "split_evenly",
        "shapes",
        "expected",
    ),
    [
        # three different numbers that make at most 6: 1, 2 and 3 in any order, with 1 answer
        ([Operation.ADD], False, 1000, 6, 6, False, STRIP_TWO_STEP_SHAPES, 6),
        ([Operation.ADD], True, 1000, 6, 6, False, STRIP_TWO_STEP_SHAPES, 1),
        # 5 is too small for three different numbers
        ([Operation.ADD], False, 1000, 5, 6, False, STRIP_TWO_STEP_SHAPES, 0),
        # two different numbers taken from a whole of at most 6, leaving 1 to 3
        ([Operation.SUBTRACT], False, 1000, 6, 6, False, STRIP_TWO_STEP_SHAPES, 14),
        ([Operation.SUBTRACT], True, 1000, 6, 6, False, STRIP_TWO_STEP_SHAPES, 3),
        # the default largest number: sums from 1 + 2 + 3 to 999, and differences from 1 to
        # 999 - 1 - 2
        ([Operation.ADD], True, 1000, 999, 6, False, STRIP_TWO_STEP_SHAPES, 994),
        ([Operation.SUBTRACT], True, 1000, 999, 6, False, STRIP_TWO_STEP_SHAPES, 996),
        # sharing what's left into 2 groups within 20: 4 to 18 left, each in fewer ways
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            False,
            1000,
            20,
            2,
            False,
            STRIP_TWO_STEP_SHAPES,
            64,
        ),
        # more groups, more ways
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            False,
            1000,
            20,
            6,
            False,
            STRIP_TWO_STEP_SHAPES,
            143,
        ),
        # its answers, the sizes of each group, 2 to 20
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            True,
            1000,
            999,
            6,
            False,
            STRIP_TWO_STEP_SHAPES,
            19,
        ),
        # the least of the shapes'
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            True,
            1000,
            999,
            6,
            False,
            STRIP_TWO_STEP_SHAPES,
            19,
        ),
        # every shape adds or subtracts
        ([Operation.MULTIPLY], False, 1000, 999, 6, False, STRIP_TWO_STEP_SHAPES, 0),
        (
            [Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1000,
            999,
            6,
            False,
            STRIP_TWO_STEP_SHAPES,
            0,
        ),
        # Split evenly, each shape needs only its share: 6 of each of two shapes. With distinct
        # answers, any shape's answer can be any problem's.
        ([Operation.ADD, Operation.SUBTRACT], False, 1000, 6, 6, True, STRIP_TWO_STEP_SHAPES, 12),
        ([Operation.ADD, Operation.SUBTRACT], True, 1000, 6, 6, True, STRIP_TWO_STEP_SHAPES, 1),
        # 2 groups within 12, with a part added: 7 problems, so 7 of each of the five shapes
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1000,
            12,
            2,
            False,
            STRIP_TWO_STEP_SHAPES,
            7,
        ),
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1000,
            12,
            2,
            True,
            STRIP_TWO_STEP_SHAPES,
            35,
        ),
        # capped
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            20,
            999,
            6,
            False,
            STRIP_TWO_STEP_SHAPES,
            20,
        ),
        # Every shape, as text only shows them. Multiplying twice within 24, with up to 3 groups:
        # 2 groups of 4 in 3 groups, and 3 groups of 4 in 2, both 24.
        ([Operation.MULTIPLY], False, 1000, 24, 3, False, None, 2),
        ([Operation.MULTIPLY], True, 1000, 24, 3, False, None, 1),
        ([Operation.MULTIPLY], False, 1000, 23, 3, False, None, 0),
        # Dividing twice within 60, with up to 3 groups: 2 then 3 groups, or 3 then 2, with each
        # answer 2 to 10. The first answer can go past 20, up to 30, or there'd be 14.
        ([Operation.DIVIDE], False, 1000, 60, 3, False, None, 18),
        # multiplication and division alone make problems too
        ([Operation.MULTIPLY, Operation.DIVIDE], False, 20, 999, 6, False, None, 20),
        # Multiplying twice can't be done within 10, either way, so it isn't drawn: the least of
        # adding three numbers (66), the sum as the size of each group (6) or as the number of
        # groups (6), and multiplying then adding (6)
        ([Operation.ADD, Operation.MULTIPLY], False, 1000, 10, 6, False, None, 6),
        # split evenly among those four
        ([Operation.ADD, Operation.MULTIPLY], False, 1000, 10, 6, True, None, 24),
    ],
)
def test_count_possible_two_step_problems(
    operations: list[Operation],
    distinct_answers: bool,
    up_to: int,
    largest_number: int,
    largest_groups: int,
    split_evenly: bool,
    shapes: frozenset[TwoStepShape] | None,
    expected: int,
) -> None:
    """
    Any one shape may be drawn for every problem, so the count is the least of theirs: its
    problems with no number repeated, or with distinct answers its answers. A shape the limits
    allow no problem of isn't drawn, so it doesn't count. The largest number caps every number,
    the first step's answer too. ``shapes`` limits the shapes, as a strip diagram's five do.
    """
    possible = count_possible_two_step_problems(
        operations,
        distinct_answers=distinct_answers,
        up_to=up_to,
        largest_number=largest_number,
        largest_groups=largest_groups,
        split_evenly=split_evenly,
        shapes=shapes,
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "distinct_answers", "count", "largest_number", "shapes", "message"),
    [
        # every shape a strip diagram shows adds or subtracts
        (
            [Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1,
            999,
            STRIP_TWO_STEP_SHAPES,
            "Cannot make 1 different problems: only 0 possible.",
        ),
        (
            [Operation.ADD],
            False,
            7,
            6,
            None,
            "Cannot make 7 different problems: only 6 possible.",
        ),
        (
            [Operation.ADD],
            True,
            2,
            6,
            None,
            "Cannot make 2 problems with different answers: only 1 possible.",
        ),
        # multiplying twice needs at least 2 groups of 3 groups of 4, 24
        (
            [Operation.MULTIPLY],
            False,
            1,
            23,
            None,
            "Cannot make 1 different problems: only 0 possible.",
        ),
    ],
)
def test_two_step_sheet_errors(
    operations: list[Operation],
    distinct_answers: bool,
    count: int,
    largest_number: int,
    shapes: frozenset[TwoStepShape] | None,
    message: str,
) -> None:
    """
    Requesting more problems than the operations and limits allow raises ``ValueError`` saying
    how many.
    """
    with pytest.raises(ValueError) as error:
        generate_two_step_problems(
            count,
            operations,
            distinct_answers=distinct_answers,
            largest_number=largest_number,
            shapes=shapes,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("count", "operations", "largest_number", "largest_groups", "chosen", "expected"),
    [
        # the defaults, a largest number of 100 and 12 groups: one of each shape, then the sheet
        # is shuffled
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            100,
            12,
            [
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                10,
                BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                CARDS,
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                    ),
                    Unknown.FIRST,
                    12,
                    "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                    "How many cards are left in the box?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                    ),
                    Unknown.FIRST,
                    17,
                    "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                    "How many cards are in the jar now?",
                ),
            ],
        ),
        # 3 problems split between 2 shapes: the extra goes to the last, sharing what's left,
        # which can share 18 into 9 with up to 12 groups
        (
            3,
            [Operation.SUBTRACT, Operation.DIVIDE],
            100,
            12,
            [
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 9), 2),
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                CARDS,
                CARDS,
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                        BasicOperationQuestionData(Operation.DIVIDE, (18, 9), 2),
                    ),
                    Unknown.FIRST,
                    2,
                    "Maria has 24 cards. 6 are in a box, and the rest are in 9 bags with the same "
                    "number in each bag. How many cards are in each bag?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                        BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                    ),
                    Unknown.FIRST,
                    6,
                    "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                    "How many cards are in each group?",
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                    ),
                    Unknown.FIRST,
                    12,
                    "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                    "How many cards are left in the box?",
                ),
            ],
        ),
    ],
)
def test_two_step_strip_choice_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    largest_number: int,
    largest_groups: int,
    chosen: list[object],
    expected: list[TwoStepQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The shapes are split evenly, then the sheet is shuffled, and each problem is drawn as in
    ``test_two_step_problems_from_scripted_draws``.

    ``sample`` keeps the shapes' order, so any extra problems go to the last, and ``shuffle``
    reverses the sheet and each problem's choices. Each problem's choices are those of
    ``two_step_strip_choices``, tested in ``test_representation``.
    """
    choice_returns(monkeypatch, chosen)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_two_step_strip_choice_problems(
        count, operations, largest_number=largest_number, largest_groups=largest_groups
    )

    assert questions == [Question(data, two_step_strip_choices(data)) for data in expected]


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "largest_groups"),
    [
        # the most problems allowed, 20, with the defaults
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE], 20, 100, 12),
        # every multiplication with a part added within 12 in 2 groups, 7, and as many sums of
        # three numbers
        ([Operation.ADD, Operation.MULTIPLY], 14, 12, 2),
    ],
)
def test_random_two_step_strip_choice_sheets_can_always_be_finished(
    operations: list[Operation], count: int, largest_number: int, largest_groups: int
) -> None:
    """A sheet of the most problems the limits allow is produced, with no problem repeated."""
    questions = generate_two_step_strip_choice_problems(
        count, operations, largest_number=largest_number, largest_groups=largest_groups
    )
    assert len({question.data.steps for question in questions}) == count
