"""
Tests for the arithmetic, missing-number, word-problem, strip-choice, equation-choice,
number-line-choice and multiplication-model generators, with one step or two.

The ``..._from_scripted_draws`` tests pin the exact output: ``random`` is scripted, so each case
lists the questions that must be produced. The no-repeats tests,
``test_missing_number_sheets_can_always_be_finished``,
``test_random_word_problems_have_distinct_answers``,
``test_random_strip_choice_sheets_can_always_be_finished``,
``test_random_equation_choice_sheets_can_always_be_finished``,
``test_random_number_line_choice_sheets_can_always_be_finished``,
``test_random_multiplication_model_sheets_can_always_be_finished``,
``test_random_two_step_problems_have_distinct_answers``,
``test_random_two_step_strip_choice_sheets_can_always_be_finished``,
``test_random_two_step_equation_choice_sheets_can_always_be_finished`` and the mixed sheets'
tests use real random draws.
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import replace

import pytest

from core.basic_operations import word_problems
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
    count_possible_mixed_word_problems,
    count_possible_multiplication_model_problems,
    count_possible_number_line_choice_problems,
    count_possible_questions,
    count_possible_sheet_questions,
    count_possible_strip_choice_problems,
    count_possible_two_step_equation_choice_problems,
    count_possible_two_step_problems,
    count_possible_word_problems,
    generate_basic_operation_questions,
    generate_equation_choice_problems,
    generate_missing_number_questions,
    generate_mixed_word_problems,
    generate_multiplication_model_problems,
    generate_number_line_choice_problems,
    generate_strip_choice_problems,
    generate_two_step_equation_choice_problems,
    generate_two_step_problems,
    generate_two_step_strip_choice_problems,
    generate_word_problems,
)
from core.basic_operations.multiplication_models import multiplication_model_choices
from core.basic_operations.representation import (
    REPRESENTATION_OPERATIONS,
    STRIP_TWO_STEP_SHAPES,
    Representation,
    Response,
    WordProblemKind,
    equation_choices,
    number_line_choices,
    strip_choices,
    two_step_equation_choices,
    two_step_strip_choices,
)
from core.basic_operations.word_problems import OBJECTS, TEMPLATES
from core.question import FreeResponse, MultipleChoice, Question
from tests.helpers import (
    LAST,
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
        "largest_groups",
        "largest_size",
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
        # the number of groups and the size of each have limits of their own, and the product
        # is whatever they make, past the largest number
        (
            1,
            [Operation.MULTIPLY],
            [Operation.MULTIPLY],
            False,
            999,
            999,
            12,
            999,
            [12, 999],
            [(2, 12), (2, 999)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (12, 999),
                    11_988,
                    "12 friends each have 999 cards. How many cards do they have together?",
                ),
            ],
        ),
        # and so is the total a division shares, written with a comma
        (
            1,
            [Operation.DIVIDE],
            [Operation.DIVIDE],
            False,
            999,
            999,
            12,
            999,
            [12, 987],
            [(2, 12), (2, 999)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (11_844, 12),
                    987,
                    "Maria divides 11,844 cards into 12 equal piles. "
                    "How many cards are in each pile?",
                ),
            ],
        ),
        # Without a largest number the sum isn't capped: numbers up to 10 make 7 + 6 = 13.
        (
            1,
            [Operation.ADD],
            [Operation.ADD],
            False,
            None,
            10,
            6,
            20,
            [7, 6],
            [(1, 10), (1, 10)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (7, 6),
                    13,
                    "A basket held 7 cards. Maria added 6 more. "
                    "How many cards are in the basket now?",
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
    largest_number: int | None,
    largest_operand: int,
    largest_groups: int,
    largest_size: int,
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
        largest_groups=largest_groups,
        largest_size=largest_size,
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
    (
        "operations",
        "distinct_answers",
        "up_to",
        "largest_number",
        "largest_operand",
        "largest_groups",
        "largest_size",
        "expected",
    ),
    [
        # addition's answers, the sums from 1 + 1 to 999
        ([Operation.ADD], False, 1000, 999, 999, 6, 20, 998),
        ([Operation.ADD], True, 1000, 999, 999, 6, 20, 998),
        # subtraction's, the differences from 1 to 999 - 1
        ([Operation.SUBTRACT], True, 1000, 999, 999, 6, 20, 998),
        # with a largest number of 20
        ([Operation.ADD], True, 100, 20, 999, 6, 20, 19),
        ([Operation.SUBTRACT], True, 100, 20, 999, 6, 20, 19),
        # base-ten blocks: the operands stop at 599, but a sum can still reach 999
        ([Operation.ADD], True, 1000, 999, 599, 6, 20, 998),
        ([Operation.SUBTRACT], True, 1000, 999, 599, 6, 20, 598),
        # the smallest largest number with a sum, 1 + 1, and a difference, 2 - 1
        ([Operation.ADD], True, 100, 2, 999, 6, 20, 1),
        ([Operation.SUBTRACT], True, 100, 2, 999, 6, 20, 1),
        # below that, none
        ([Operation.ADD], True, 100, 1, 999, 6, 20, 0),
        ([Operation.SUBTRACT], True, 100, 1, 999, 6, 20, 0),
        # 5 group counts (2 to 6) times 19 sizes (2 to 20)
        ([Operation.MULTIPLY], False, 100, 999, 999, 6, 20, 95),
        ([Operation.DIVIDE], False, 100, 999, 999, 6, 20, 95),
        # the distinct products of those
        ([Operation.MULTIPLY], True, 100, 999, 999, 6, 20, 59),
        # a division's answer is the size of each group
        ([Operation.DIVIDE], True, 100, 999, 999, 6, 20, 19),
        # multiplication and division ignore the largest number
        ([Operation.DIVIDE], True, 100, 20, 999, 6, 20, 19),
        # the least of the operations'
        ([Operation.ADD, Operation.DIVIDE], True, 100, 999, 999, 6, 20, 19),
        ([Operation.ADD, Operation.DIVIDE], True, 100, 10, 999, 6, 20, 9),
        # capped
        ([Operation.MULTIPLY, Operation.DIVIDE], False, 12, 999, 999, 6, 20, 12),
        # 2 to 10 groups of 2 to 10: 9 group counts times 9 sizes
        ([Operation.MULTIPLY], False, 100, 999, 999, 10, 10, 81),
        # a division's answers, the sizes 2 to 10, so 12 different answers need sizes up to 13
        ([Operation.DIVIDE], True, 100, 999, 999, 10, 10, 9),
        ([Operation.DIVIDE], True, 100, 999, 999, 10, 13, 12),
        # the products of 2 groups of 2 to 13: 4, 6 and on to 26
        ([Operation.MULTIPLY], True, 100, 999, 999, 2, 13, 12),
        # the fewest, 2 groups of 2
        ([Operation.MULTIPLY], False, 100, 999, 999, 2, 2, 1),
        ([Operation.DIVIDE], False, 100, 999, 999, 2, 2, 1),
        # the most, 99 groups of up to 999, capped too
        ([Operation.MULTIPLY], False, 20, 999, 999, 99, 999, 20),
        ([Operation.DIVIDE], True, 20, 999, 999, 99, 999, 20),
        # without a largest number, operands up to 10 make the sums 2 to 20
        ([Operation.ADD], False, 1000, None, 10, 6, 20, 19),
    ],
)
def test_count_possible_word_problems(
    operations: list[Operation],
    distinct_answers: bool,
    up_to: int,
    largest_number: int | None,
    largest_operand: int,
    largest_groups: int,
    largest_size: int,
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
        largest_groups=largest_groups,
        largest_size=largest_size,
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("distinct_answers", "taken", "expected"),
    [
        # 3 + 4 is already on the sheet, so it's drawn again
        (
            False,
            [BasicOperationQuestionData(Operation.ADD, (3, 4), 7, "On the sheet already.")],
            BasicOperationQuestionData(
                Operation.ADD,
                (5, 6),
                11,
                "A basket held 5 cards. Maria added 6 more. How many cards are in the basket now?",
            ),
        ),
        # with distinct answers, 3 + 4 is drawn again for its answer, as 5 + 2 makes 7 too
        (
            True,
            [BasicOperationQuestionData(Operation.ADD, (5, 2), 7, "On the sheet already.")],
            BasicOperationQuestionData(
                Operation.ADD,
                (5, 6),
                11,
                "A basket held 5 cards. Maria added 6 more. How many cards are in the basket now?",
            ),
        ),
    ],
)
def test_word_problems_repeat_no_problem_taken(
    distinct_answers: bool,
    taken: list[BasicOperationQuestionData],
    expected: BasicOperationQuestionData,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    No problem repeats the operation and operands of one in ``taken``, those already on the
    sheet, or with distinct answers its answer: such a draw, 3 + 4, is drawn again, as 5 + 6.
    Every scripted draw must be made.
    """
    drawn_from = randint_returns(monkeypatch, [3, 4, 5, 6])
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    questions = generate_word_problems(
        1,
        [Operation.ADD],
        distinct_answers=distinct_answers,
        largest_number=None,
        largest_operand=10,
        taken=taken,
    )

    assert drawn_from == [(1, 10)] * 4
    assert questions == [Question(expected, FreeResponse())]


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
    (
        "count",
        "operations",
        "largest_number",
        "largest_groups",
        "largest_size",
        "drawn",
        "bounds",
        "expected",
    ),
    [
        # The defaults, a largest number of 100 and 12 groups: one of each operation, then the
        # sheet is shuffled. An addition's or subtraction's smaller number is at most 12.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            100,
            12,
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
        # the largest group size caps a multiplication's groups: 12 groups of at most 3
        (
            1,
            [Operation.MULTIPLY],
            100,
            12,
            3,
            [12, 3],
            [(2, 12), (2, 3)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (12, 3),
                    36,
                    "12 friends each have 3 cards. How many cards do they have together?",
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
    largest_size: int,
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
        count,
        operations,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
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
    ("operations", "up_to", "largest_number", "largest_groups", "largest_size", "expected"),
    [
        # the defaults: the sums from 1 + 1 to 100, and the differences from 1 to 99
        ([Operation.ADD], 1000, 100, 12, 20, 99),
        ([Operation.SUBTRACT], 1000, 100, 12, 20, 99),
        # 2 to 12 groups of 2 to 20 within 100, but 2 groups of 2
        ([Operation.MULTIPLY], 1000, 100, 12, 20, 148),
        # every one of those shared, as 4 shared into 2 draws a strip of its own
        ([Operation.DIVIDE], 1000, 100, 12, 20, 149),
        # 2 groups only: of 3 to 20, or 4 to 40 shared into them
        ([Operation.MULTIPLY], 1000, 100, 2, 20, 18),
        ([Operation.DIVIDE], 1000, 100, 2, 20, 19),
        # the largest number caps the product too
        ([Operation.MULTIPLY], 1000, 20, 12, 20, 26),
        # the sums from 1 + 1 to 10
        ([Operation.ADD], 1000, 10, 12, 20, 9),
        # Split evenly, each operation needs only its share: 2 groups of 3, the only
        # multiplication, is enough for 1 of 2 problems, and 1 of 4.
        ([Operation.ADD, Operation.MULTIPLY], 1000, 6, 2, 20, 2),
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            1000,
            6,
            2,
            20,
            4,
        ),
        # 2 groups of 2 is the only multiplication within 5 in 2 groups, and it's left out
        ([Operation.ADD, Operation.MULTIPLY], 1000, 5, 2, 20, 0),
        # capped
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            20,
            100,
            12,
            20,
            20,
        ),
        # 2 to 12 groups of 2 or 3, but 2 groups of 2
        ([Operation.MULTIPLY], 1000, 100, 12, 3, 21),
        # every one of those shared
        ([Operation.DIVIDE], 1000, 100, 12, 3, 22),
        # the largest number still caps the product: 2 groups of 3 to 50
        ([Operation.MULTIPLY], 1000, 100, 2, 999, 48),
    ],
)
def test_count_possible_strip_choice_problems(
    operations: list[Operation],
    up_to: int,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
    expected: int,
) -> None:
    """
    Each operation counts as on word problems, except that the largest number caps a product or
    dividend too, and 2 groups of 2 is left out. Split evenly, the count is the least of the
    operations' for each operation.
    """
    possible = count_possible_strip_choice_problems(
        operations,
        up_to=up_to,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
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
    (
        "count",
        "operations",
        "largest_number",
        "largest_groups",
        "largest_size",
        "drawn",
        "bounds",
        "expected",
    ),
    [
        # The defaults: one of each operation, then the sheet is shuffled. Multiplication and
        # division are 2 to 6 groups of 2 to 20, as on any word problem. Subtraction is worded with
        # its comparison, the last of its templates.
        (
            4,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            999,
            6,
            20,
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
            6,
            20,
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
            6,
            20,
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
        # the largest number caps an addition's numbers, not its sum, so 7 + 6 = 13 stands
        # within 10, and it doesn't cap a product
        (
            2,
            [Operation.ADD, Operation.MULTIPLY],
            10,
            6,
            20,
            [6, 20, 7, 6],
            [(2, 6), (2, 20), (1, 10), (1, 10)],
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (6, 20),
                    120,
                    "6 friends each have 20 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.ADD,
                    (7, 6),
                    13,
                    "A basket held 7 cards. Maria added 6 more. "
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
            6,
            20,
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
        # Equations draw no strip, so up to 99 groups: 32 groups of 28 shared, whose total the
        # largest number doesn't cap
        (
            1,
            [Operation.DIVIDE],
            100,
            32,
            28,
            [32, 28],
            [(2, 32), (2, 28)],
            [
                BasicOperationQuestionData(
                    Operation.DIVIDE,
                    (896, 32),
                    28,
                    "Maria divides 896 cards into 32 equal piles. How many cards are in each pile?",
                ),
            ],
        ),
    ],
)
def test_equation_choice_problems_from_scripted_draws(
    count: int,
    operations: list[Operation],
    largest_number: int,
    largest_groups: int,
    largest_size: int,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The operations are split evenly, then the sheet is shuffled. Each problem's numbers are
    drawn, and redrawn until they meet the limits and aren't left out: an addition's or
    subtraction's numbers at most the largest number, its answer not capped, and no operands of
    2 and 2, or 4 and 2.

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

    questions = generate_equation_choice_problems(
        count,
        operations,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
    )

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
    ("operations", "up_to", "largest_number", "largest_groups", "largest_size", "expected"),
    [
        # the defaults: the sums from 1 + 1 to 999 + 999, and the differences from 1 to 998
        ([Operation.ADD], 2000, 999, 6, 20, 1997),
        ([Operation.SUBTRACT], 1000, 999, 6, 20, 998),
        # 2 to 6 groups of 2 to 20, but 2 groups of 2 and 4 groups of 2
        ([Operation.MULTIPLY], 1000, 999, 6, 20, 93),
        # every one of those shared, but 4 shared into 2
        ([Operation.DIVIDE], 1000, 999, 6, 20, 94),
        # the largest number doesn't cap a product
        ([Operation.MULTIPLY], 1000, 10, 6, 20, 93),
        # the sums from 1 + 1 to 10 + 10
        ([Operation.ADD], 1000, 10, 6, 20, 19),
        # Split evenly, each operation needs only its share: addition's 5 sums of numbers up to
        # 3 are enough for 5 of 10 problems.
        ([Operation.ADD, Operation.MULTIPLY], 1000, 3, 6, 20, 10),
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            1000,
            999,
            6,
            20,
            372,
        ),
        # capped
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            20,
            999,
            6,
            20,
            20,
        ),
        # 2 to 32 groups of 2 to 28, but 2 groups of 2 and 4 groups of 2
        ([Operation.MULTIPLY], 1000, 999, 32, 28, 835),
        # 2 groups of 3 only, as 2 groups of 2 is left out; and 6 shared into 2, as 4 is
        ([Operation.MULTIPLY], 1000, 999, 2, 3, 1),
        ([Operation.DIVIDE], 1000, 999, 2, 3, 1),
    ],
)
def test_count_possible_equation_choice_problems(
    operations: list[Operation],
    up_to: int,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
    expected: int,
) -> None:
    """
    Each operation counts as on word problems, except that 2 groups of 2, 4 groups of 2 and 4
    shared into 2 are left out. Split evenly, the count is the least of the operations' for each
    operation.
    """
    possible = count_possible_equation_choice_problems(
        operations,
        up_to=up_to,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
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
            20,
            10,
            "Cannot make 20 different problems: only 19 possible.",
        ),
        # split evenly: addition's 5 sums of numbers up to 3 aren't enough for 6 of 11 problems
        (
            [Operation.ADD, Operation.MULTIPLY],
            11,
            3,
            "Cannot make 11 different problems: only 10 possible.",
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
        # the largest number caps an addition's numbers, not its sum, so 50 and 60, put in order
        # as 60 + 50, make 110 within 100
        (
            1,
            [Operation.ADD],
            100,
            [50, 60],
            [(1, 100), (1, 100)],
            [
                BasicOperationQuestionData(
                    Operation.ADD,
                    (60, 50),
                    110,
                    "A basket held 60 cards. Maria added 50 more. "
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
    drawn, and redrawn until they meet the limits: the numbers given at most the largest number,
    and an addition's numbers different, with the larger first.

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
        # the sums from 2 + 1 to 999 + 998, as 1 + 1 and 999 + 999 have the same numbers
        ([Operation.ADD], 2000, 999, 1995),
        # the differences from 1 to 998, as on any word problem
        ([Operation.SUBTRACT], 2000, 999, 998),
        # 2 + 1, 3 + 1 and 3 + 2; only 2 + 1; and below that, none
        ([Operation.ADD], 2000, 3, 3),
        ([Operation.ADD], 2000, 2, 1),
        ([Operation.ADD], 2000, 1, 0),
        # Split evenly, each operation needs only its share: subtraction's 2 differences within 3
        # are enough for 2 of 4 problems.
        ([Operation.ADD, Operation.SUBTRACT], 2000, 3, 4),
        ([Operation.ADD, Operation.SUBTRACT], 2000, 999, 1996),
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
            4,
            3,
            "Cannot make 4 different problems: only 3 possible.",
        ),
        (
            [Operation.ADD],
            1,
            1,
            "Cannot make 1 different problems: only 0 possible.",
        ),
        # split evenly: subtraction's 2 differences within 3 aren't enough for 3 of 5 problems
        (
            [Operation.ADD, Operation.SUBTRACT],
            5,
            3,
            "Cannot make 5 different problems: only 4 possible.",
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


@pytest.mark.parametrize(
    ("count", "largest_factor", "largest_product", "expected"),
    [
        # the defaults: 12 groups of 8, the last fact within 100, then 12 groups of 7
        (
            2,
            12,
            100,
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (12, 8),
                    96,
                    "12 friends each have 8 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (12, 7),
                    84,
                    "Maria buys 12 packs of cards with 7 in each pack. How many cards in all?",
                ),
            ],
        ),
        # Every fact with factors up to 4 within 12. No fact comes after its turn, so 3 groups of
        # 4 never comes, nor 2 groups of 4, nor 2 groups of 3. 4 groups of 4 is over 12, and 2
        # groups of 2 is left out.
        (
            4,
            4,
            12,
            [
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (4, 3),
                    12,
                    "4 friends each have 3 cards. How many cards do they have together?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (4, 2),
                    8,
                    "Maria buys 4 packs of cards with 2 in each pack. How many cards in all?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 3),
                    9,
                    "Each basket has 3 cards. How many cards are in 3 baskets?",
                ),
                BasicOperationQuestionData(
                    Operation.MULTIPLY,
                    (3, 2),
                    6,
                    "Maria plants 3 rows with 2 flowers in each row. How many flowers did Maria "
                    "plant?",
                ),
            ],
        ),
    ],
)
def test_multiplication_model_problems_from_scripted_draws(
    count: int,
    largest_factor: int,
    largest_product: int,
    expected: list[BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each problem is a fact drawn from those within the limits, with no fact or its turn drawn
    twice, and 2 groups of 2 left out.

    ``choice`` takes the last of the facts left, ordered by groups and then size, and the last
    object. The wording takes the first two names and the multiplication templates from the
    last. Each problem's choices are those of ``multiplication_model_choices``, with ``choice``
    taking the last, ``sample`` the first and ``shuffle`` reversing, tested in
    ``test_multiplication_models``.
    """
    choose_last(monkeypatch)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_multiplication_model_problems(
        count, largest_factor=largest_factor, largest_product=largest_product
    )

    assert questions == [Question(data, multiplication_model_choices(data)) for data in expected]


@pytest.mark.parametrize(
    ("count", "largest_factor", "largest_product"),
    [
        # 2 x 3, 2 x 4, 3 x 3 and 3 x 4, every fact with factors up to 4 within 12
        (4, 4, 12),
        # only 2 x 3
        (1, 3, 6),
        # the most problems allowed, 20, with the defaults
        (20, 12, 100),
    ],
)
def test_random_multiplication_model_sheets_can_always_be_finished(
    count: int, largest_factor: int, largest_product: int
) -> None:
    """
    A sheet of the most problems the limits allow is produced, with no fact repeated, turned
    round or not.
    """
    questions = generate_multiplication_model_problems(
        count, largest_factor=largest_factor, largest_product=largest_product
    )
    facts = {tuple(sorted(question.data.operands)) for question in questions}
    assert len(facts) == count


@pytest.mark.parametrize(
    ("up_to", "largest_factor", "largest_product", "expected"),
    [
        # the 59 facts with factors 2 to 12 within 100, 3 x 4 and 4 x 3 counted once, and 2 x 2
        # left out
        (100, 12, 100, 59),
        # within 20: 2 x 3 to 2 x 10, 3 x 3 to 3 x 6, 4 x 4 and 4 x 5
        (100, 12, 20, 14),
        # 2 x 3, 2 x 4, 3 x 3 and 3 x 4
        (100, 4, 12, 4),
        # only 2 x 3
        (100, 3, 6, 1),
        # only 2 x 2, which is left out
        (100, 2, 100, 0),
        # capped
        (20, 12, 100, 20),
    ],
)
def test_count_possible_multiplication_model_problems(
    up_to: int, largest_factor: int, largest_product: int, expected: int
) -> None:
    """Each fact within the limits counts once with its turn, and 2 x 2 is left out."""
    possible = count_possible_multiplication_model_problems(
        up_to=up_to, largest_factor=largest_factor, largest_product=largest_product
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("count", "largest_factor", "largest_product", "message"),
    [
        (5, 4, 12, "Cannot make 5 different problems: only 4 possible."),
        (1, 2, 100, "Cannot make 1 different problems: only 0 possible."),
    ],
)
def test_multiplication_model_sheet_errors(
    count: int, largest_factor: int, largest_product: int, message: str
) -> None:
    """Requesting more problems than the limits allow raises ``ValueError`` saying how many."""
    with pytest.raises(ValueError) as error:
        generate_multiplication_model_problems(
            count, largest_factor=largest_factor, largest_product=largest_product
        )
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
SUBTRACT_THEN_MULTIPLY = (Operation.SUBTRACT, Operation.MULTIPLY, Unknown.SECOND)
SUBTRACT_THEN_MULTIPLY_GROUPS = (Operation.SUBTRACT, Operation.MULTIPLY, Unknown.FIRST)
SUBTRACT_THEN_DIVIDE_GROUPS = (Operation.SUBTRACT, Operation.DIVIDE, Unknown.SECOND)
# and some of the shapes added last, where the first step's answer is added to the second step's
# other number, as in c + (a + b)
ADD_THEN_ADDED_TO = (Operation.ADD, Operation.ADD, Unknown.SECOND)
MULTIPLY_THEN_ADDED_TO = (Operation.MULTIPLY, Operation.ADD, Unknown.SECOND)
CARDS = ("card", "cards")  # the object chosen for a problem's wording


@pytest.mark.parametrize(
    (
        "count",
        "operations",
        "picks",
        "distinct_answers",
        "largest_number",
        "largest_groups",
        "largest_size",
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
            20,
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
        # Without a largest number, only the numbers given keep the limits: 3 rows of 4 boxes
        # make 12 boxes, though the largest number of groups is 6.
        (
            1,
            [Operation.MULTIPLY],
            [MULTIPLY_THEN_MULTIPLY_GROUPS],
            False,
            None,
            6,
            20,
            [
                12,
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
                BasicOperationQuestionData(Operation.MULTIPLY, (12, 15), 180),
                CARDS,
            ],
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
                        BasicOperationQuestionData(Operation.MULTIPLY, (12, 15), 180),
                    ),
                    Unknown.FIRST,
                    180,
                    "Maria stacks 3 rows of boxes with 4 boxes in each row. Each box has 15 cards "
                    "in it. How many cards are in the boxes?",
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
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
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
        largest_size=largest_size,
    )

    assert questions == [Question(data, FreeResponse()) for data in expected]


@pytest.mark.parametrize(
    (
        "operations",
        "picks",
        "largest_number",
        "largest_groups",
        "largest_size",
        "chosen",
        "offered",
    ),
    [
        # Three numbers that make at most 7: 7 can't be carried, as nothing is left to add, and
        # 4 is 1 + 3 or 3 + 1, but not 2 + 2. After 1 + 3, only 2 can be added, not 1 or 3.
        (
            [Operation.ADD],
            [ADD_THEN_ADD],
            7,
            6,
            20,
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
            6,
            20,
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
        # Dividing twice within 60, in 2 or 3 groups of at most 5. The first answer can still go
        # past 5, but not to 14, which needs groups of 7. After 30 shared into 2, 15 can only be
        # shared into 3, and 45 shared into 3 isn't offered, as then the 3 would repeat.
        (
            [Operation.DIVIDE],
            [DIVIDE_THEN_DIVIDE],
            60,
            3,
            5,
            [
                15,
                BasicOperationQuestionData(Operation.DIVIDE, (30, 2), 15),
                BasicOperationQuestionData(Operation.DIVIDE, (15, 3), 5),
                CARDS,
            ],
            [
                [4, 6, 8, 9, 10, 12, 15],
                [BasicOperationQuestionData(Operation.DIVIDE, (30, 2), 15)],
                [BasicOperationQuestionData(Operation.DIVIDE, (15, 3), 5)],
                OBJECTS,
            ],
        ),
        # Sharing among what's left of up to 4 friends: the friends are groups, so there are at
        # most 4 to start with, not 20. 4 can't be carried, as 5 - 1 needs 5 friends. After
        # 4 - 2, 4 can't be shared, as the 4 would repeat.
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            [SUBTRACT_THEN_DIVIDE_GROUPS],
            20,
            4,
            4,
            [
                2,
                BasicOperationQuestionData(Operation.SUBTRACT, (4, 2), 2),
                BasicOperationQuestionData(Operation.DIVIDE, (8, 2), 4),
                CARDS,
            ],
            [
                [2, 3],
                [
                    BasicOperationQuestionData(Operation.SUBTRACT, (3, 1), 2),
                    BasicOperationQuestionData(Operation.SUBTRACT, (4, 2), 2),
                ],
                [
                    BasicOperationQuestionData(Operation.DIVIDE, (6, 2), 3),
                    BasicOperationQuestionData(Operation.DIVIDE, (8, 2), 4),
                ],
                OBJECTS,
            ],
        ),
        # Boxes, up to 4, with some given away: no more than 4 to start with, and those boxes
        # hold at most 12 in all, so 3 boxes, 1 given away, hold 2 or 4 each, not 5 or 6.
        (
            [Operation.SUBTRACT, Operation.MULTIPLY],
            [SUBTRACT_THEN_MULTIPLY_GROUPS],
            12,
            4,
            6,
            [
                2,
                BasicOperationQuestionData(Operation.SUBTRACT, (3, 1), 2),
                BasicOperationQuestionData(Operation.MULTIPLY, (2, 4), 8),
                CARDS,
            ],
            [
                [2, 3],
                [
                    BasicOperationQuestionData(Operation.SUBTRACT, (3, 1), 2),
                    BasicOperationQuestionData(Operation.SUBTRACT, (4, 2), 2),
                ],
                [
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 2), 4),
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 4), 8),
                ],
                OBJECTS,
            ],
        ),
        # Bags of up to 4 with some taken out of each: no bag starts with more than 4, so only 2
        # and 3 can be left in each, and 3 is only 4 - 1.
        (
            [Operation.SUBTRACT, Operation.MULTIPLY],
            [SUBTRACT_THEN_MULTIPLY],
            20,
            3,
            4,
            [
                3,
                BasicOperationQuestionData(Operation.SUBTRACT, (4, 1), 3),
                BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                CARDS,
            ],
            [
                [2, 3],
                [BasicOperationQuestionData(Operation.SUBTRACT, (4, 1), 3)],
                [
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 3), 9),
                ],
                OBJECTS,
            ],
        ),
        # Without a largest number, an added number that counts groups keeps the groups limit, but
        # their sum, carried, needn't: within 3 groups of up to 3, 1 + 3 or 3 + 1 boxes of 2 make
        # 4 boxes. 2 + 3 or 3 + 2 boxes of 2 or 3 would repeat a number, as would 2 + 2.
        (
            [Operation.ADD, Operation.MULTIPLY],
            [ADD_THEN_MULTIPLY_GROUPS],
            None,
            3,
            3,
            [
                4,
                BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                BasicOperationQuestionData(Operation.MULTIPLY, (4, 2), 8),
                CARDS,
            ],
            [
                [3, 4],
                [
                    BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                    BasicOperationQuestionData(Operation.ADD, (3, 1), 4),
                ],
                [BasicOperationQuestionData(Operation.MULTIPLY, (4, 2), 8)],
                OBJECTS,
            ],
        ),
    ],
)
def test_two_step_problems_offer_only_steps_that_repeat_no_number(
    operations: list[Operation],
    picks: list[TwoStepShape],
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
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

    generate_two_step_problems(
        1,
        operations,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
    )

    assert drawn_from == offered


@pytest.mark.parametrize(
    ("operations", "largest_number", "expected"),
    [
        # multiplying twice can't be done within 10, either way, so the other six shapes take
        # turns, the two added last after the first four
        (
            [Operation.ADD, Operation.MULTIPLY],
            10,
            [
                ADD_THEN_ADD,
                ADD_THEN_MULTIPLY,
                ADD_THEN_MULTIPLY_GROUPS,
                MULTIPLY_THEN_ADD,
                ADD_THEN_ADDED_TO,
                MULTIPLY_THEN_ADDED_TO,
            ],
        ),
        # within 36 it can, both ways, with 6 problems each, so it takes its turns ahead of the
        # two shapes added last
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
        "largest_size",
        "split_evenly",
        "shapes",
        "expected",
    ),
    [
        # three different numbers that make at most 6: 1, 2 and 3 in any order, with 1 answer
        ([Operation.ADD], False, 1000, 6, 6, 20, False, STRIP_TWO_STEP_SHAPES, 6),
        ([Operation.ADD], True, 1000, 6, 6, 20, False, STRIP_TWO_STEP_SHAPES, 1),
        # 5 is too small for three different numbers
        ([Operation.ADD], False, 1000, 5, 6, 20, False, STRIP_TWO_STEP_SHAPES, 0),
        # two different numbers taken from a whole of at most 6, leaving 1 to 3
        ([Operation.SUBTRACT], False, 1000, 6, 6, 20, False, STRIP_TWO_STEP_SHAPES, 14),
        ([Operation.SUBTRACT], True, 1000, 6, 6, 20, False, STRIP_TWO_STEP_SHAPES, 3),
        # the default largest number: sums from 1 + 2 + 3 to 999, and differences from 1 to
        # 999 - 1 - 2
        ([Operation.ADD], True, 1000, 999, 6, 20, False, STRIP_TWO_STEP_SHAPES, 994),
        ([Operation.SUBTRACT], True, 1000, 999, 6, 20, False, STRIP_TWO_STEP_SHAPES, 996),
        # sharing what's left into 2 groups within 20: 4 to 18 left, each in fewer ways
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            False,
            1000,
            20,
            2,
            20,
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
            20,
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
            20,
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
            20,
            False,
            STRIP_TWO_STEP_SHAPES,
            19,
        ),
        # every shape adds or subtracts
        ([Operation.MULTIPLY], False, 1000, 999, 6, 20, False, STRIP_TWO_STEP_SHAPES, 0),
        (
            [Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1000,
            999,
            6,
            20,
            False,
            STRIP_TWO_STEP_SHAPES,
            0,
        ),
        # Split evenly, each shape needs only its share: 6 of each of two shapes. With distinct
        # answers, any shape's answer can be any problem's.
        (
            [Operation.ADD, Operation.SUBTRACT],
            False,
            1000,
            6,
            6,
            20,
            True,
            STRIP_TWO_STEP_SHAPES,
            12,
        ),
        ([Operation.ADD, Operation.SUBTRACT], True, 1000, 6, 6, 20, True, STRIP_TWO_STEP_SHAPES, 1),
        # 2 groups within 12, with a part added: 7 problems, so 7 of each of the five shapes
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            1000,
            12,
            2,
            20,
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
            20,
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
            20,
            False,
            STRIP_TWO_STEP_SHAPES,
            20,
        ),
        # Every shape, as text only shows them. Multiplying twice within 24, with up to 3 groups:
        # 2 groups of 4 in 3 groups, and 3 groups of 4 in 2, both 24.
        ([Operation.MULTIPLY], False, 1000, 24, 3, 20, False, None, 2),
        ([Operation.MULTIPLY], True, 1000, 24, 3, 20, False, None, 1),
        ([Operation.MULTIPLY], False, 1000, 23, 3, 20, False, None, 0),
        # Dividing twice within 60, with up to 3 groups: 2 then 3 groups, or 3 then 2, with each
        # answer 2 to 10. The first answer can go past 20, up to 30, or there'd be 14.
        ([Operation.DIVIDE], False, 1000, 60, 3, 20, False, None, 18),
        # multiplication and division alone make problems too
        ([Operation.MULTIPLY, Operation.DIVIDE], False, 20, 999, 6, 20, False, None, 20),
        # Multiplying twice can't be done within 10, either way, so it isn't drawn: the least of
        # adding three numbers (66 each way), the sum as the size of each group (6) or as the
        # number of groups (6), and multiplying then adding (6 each way)
        ([Operation.ADD, Operation.MULTIPLY], False, 1000, 10, 6, 20, False, None, 6),
        # split evenly among those six
        ([Operation.ADD, Operation.MULTIPLY], False, 1000, 10, 6, 20, True, None, 36),
        # As above, with each answer at most 5: 4 in each order. The first answer can still go
        # past 5, up to 15, or there'd be only 1, 12 shared into 3, then into 2.
        ([Operation.DIVIDE], False, 1000, 60, 3, 5, False, None, 8),
        # Without a largest number, only the numbers given keep the limits: c x (a x b), with c
        # and a 2 and 3 in either order and b from 4 to 20, has the fewest, 34, though 3 x 20
        # makes 60 in each group. (a x b) x c, with a 2 or 3, has 612.
        ([Operation.MULTIPLY], False, 1000, None, 3, 20, False, None, 34),
    ],
)
def test_count_possible_two_step_problems(
    operations: list[Operation],
    distinct_answers: bool,
    up_to: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
    split_evenly: bool,
    shapes: frozenset[TwoStepShape] | None,
    expected: int,
) -> None:
    """
    Any one shape may be drawn for every problem, so the count is the least of theirs: its
    problems with no number repeated, or with distinct answers its answers. A shape the limits
    allow no problem of isn't drawn, so it doesn't count. The largest number caps every number,
    the first step's answer too; without it, the limits cap only the numbers given. ``shapes``
    limits the shapes, as a strip diagram's five do.
    """
    possible = count_possible_two_step_problems(
        operations,
        distinct_answers=distinct_answers,
        up_to=up_to,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
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
    (
        "count",
        "operations",
        "largest_number",
        "largest_groups",
        "largest_size",
        "chosen",
        "expected",
    ),
    [
        # the defaults, a largest number of 100 and 12 groups: one of each shape, then the sheet
        # is shuffled
        (
            2,
            [Operation.ADD, Operation.SUBTRACT],
            100,
            12,
            20,
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
            20,
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
    largest_size: int,
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
        count,
        operations,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
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


@pytest.mark.parametrize(
    ("keep", "expected"),
    [
        # Within 6 the numbers are 1, 2 and 3. Every draw takes the last offered: a sum of 5,
        # its last first step that some number can follow, 3 + 2, and then 1.
        (
            None,
            (
                BasicOperationQuestionData(Operation.ADD, (3, 2), 5),
                BasicOperationQuestionData(Operation.ADD, (5, 1), 6),
            ),
        ),
        # A problem ``keep`` is false of gives way to the first it's true of, with the shuffled
        # order unshuffled: the smallest sum, 3, its first step 1 + 2, then 3.
        (
            lambda data: data.steps[0].operands != (3, 2),
            (
                BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                BasicOperationQuestionData(Operation.ADD, (3, 3), 6),
            ),
        ),
        # A shape it's false of for every problem isn't drawn, so the turn passes to the next:
        # 1 + (3 + 2)
        (
            lambda data: data.shape != ADD_THEN_ADD,
            (
                BasicOperationQuestionData(Operation.ADD, (3, 2), 5),
                BasicOperationQuestionData(Operation.ADD, (1, 5), 6),
            ),
        ),
    ],
)
def test_two_step_problems_keep(
    keep: Callable[[TwoStepQuestionData], bool] | None,
    expected: tuple[BasicOperationQuestionData, BasicOperationQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ``keep`` leaves problems out, such as those without fair equations to choose from: a draw it
    is false of moves on through a shuffled order of the shape's problems, which ``sample``
    leaves in order. ``choices`` takes the shapes in turn, adding three numbers first.
    """
    choices_in_turn(monkeypatch)
    choose_last(monkeypatch)
    sample_first(monkeypatch)

    questions = generate_two_step_problems(1, [Operation.ADD], largest_number=6, keep=keep)

    assert [question.data.steps for question in questions] == [expected]


@pytest.mark.parametrize(
    ("distinct_answers", "taken", "expected"),
    [
        # (1 + 2) + 3 is already on the sheet, worded, so it's drawn again
        (
            False,
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                        BasicOperationQuestionData(Operation.ADD, (3, 3), 6),
                    ),
                    Unknown.FIRST,
                    6,
                    "On the sheet already.",
                )
            ],
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                    BasicOperationQuestionData(Operation.ADD, (4, 2), 6),
                ),
                Unknown.FIRST,
                6,
                "A jar held 1 card. Maria added 3 more, and then Jamal added 2 more. "
                "How many cards are in the jar now?",
            ),
        ),
        # with distinct answers, (1 + 2) + 3 is drawn again for its answer, as (2 + 3) + 1 makes
        # 6 too
        (
            True,
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (2, 3), 5),
                        BasicOperationQuestionData(Operation.ADD, (5, 1), 6),
                    ),
                    Unknown.FIRST,
                    6,
                    "On the sheet already.",
                )
            ],
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                ),
                Unknown.FIRST,
                7,
                "A jar held 1 card. Maria added 2 more, and then Jamal added 4 more. "
                "How many cards are in the jar now?",
            ),
        ),
    ],
)
def test_two_step_problems_repeat_no_problem_taken(
    distinct_answers: bool,
    taken: list[TwoStepQuestionData],
    expected: TwoStepQuestionData,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    No problem repeats one in ``taken``, those already on the sheet, whatever its wording, or
    with distinct answers its answer: such a draw, (1 + 2) + 3, is drawn again. ``chosen`` lists
    both draws, then the object.
    """
    choices_returns(monkeypatch, [ADD_THEN_ADD])
    redrawn = expected.steps
    choice_returns(
        monkeypatch,
        [
            3,
            BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
            BasicOperationQuestionData(Operation.ADD, (3, 3), 6),
            redrawn[0].answer,
            redrawn[0],
            redrawn[1],
            CARDS,
        ],
    )
    sample_first(monkeypatch)

    questions = generate_two_step_problems(
        1,
        [Operation.ADD],
        distinct_answers=distinct_answers,
        largest_number=None,
        largest_given=6,
        taken=taken,
    )

    assert questions == [Question(expected, FreeResponse())]


@pytest.mark.parametrize(
    ("operations", "up_to", "largest_number", "largest_groups", "largest_size", "expected"),
    [
        # with the defaults, capped
        ([Operation.ADD, Operation.SUBTRACT], 20, 999, 6, 20, 20),
        # one operation, with its own mistakes
        ([Operation.SUBTRACT], 20, 999, 6, 20, 20),
        # Multiplication alone, with the signs changed to + if no number can be reversed. Only
        # the numbers given keep the limits, so the first product may pass them. c x (a x b) has
        # the fewest: c and a from 2 to 6 groups and b from 2 to 20, all different, 340, of which
        # 334 have fair equations. Split evenly, 668.
        ([Operation.MULTIPLY], 999, 999, 6, 20, 668),
        # Within 6 the only (a - b) ÷ c, (5 - 1) ÷ 2, has none: (5 - 1) - 2 is 2 too, and moving
        # the brackets gives 1 ÷ 2, ruled out at a glance. So that shape isn't drawn, and of the
        # six left, c ÷ (a ÷ b) has the fewest, 1: 6 ÷ (4 ÷ 2), since in 4 ÷ (6 ÷ 3) 4 ÷ 2 and
        # 4 - 2 are both 2. Split evenly, 6.
        ([Operation.SUBTRACT, Operation.DIVIDE], 99, 6, 6, 20, 6),
        # Within 3 every addition adds 1, 2 and 3 in some order, and multiplying them gives the
        # same answer, 6, so none has fair equations; with at most 2 groups of 2, every
        # multiplication repeats a number.
        ([Operation.ADD, Operation.MULTIPLY], 99, 3, 2, 2, 0),
    ],
)
def test_count_possible_two_step_equation_choice_problems(
    operations: list[Operation],
    up_to: int,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
    expected: int,
) -> None:
    """
    As ``count_possible_two_step_problems`` counts with every shape split evenly, of only the
    problems with fair equations to choose from.
    """
    possible = count_possible_two_step_equation_choice_problems(
        operations,
        up_to=up_to,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "chosen", "expected"),
    [
        # Two problems split among the eight shapes of - and ÷: with ``sample`` keeping their
        # order, the last two, shuffled.
        (
            [Operation.SUBTRACT, Operation.DIVIDE],
            [
                5,
                BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                BasicOperationQuestionData(Operation.SUBTRACT, (30, 5), 25),
                8,
                BasicOperationQuestionData(Operation.SUBTRACT, (9, 1), 8),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                CARDS,
                CARDS,
                LAST,
                LAST,
                LAST,
                LAST,
            ],
            [
                (
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                            BasicOperationQuestionData(Operation.SUBTRACT, (30, 5), 25),
                        ),
                        Unknown.SECOND,
                        25,
                        "A store had 30 cards. A school ordered 20 cards in 4 equal boxes, and "
                        "the store sent the first box. How many cards does the store have left?",
                    ),
                    "c",
                ),
                (
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (9, 1), 8),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.SECOND,
                        12,
                        "A class wants to collect 20 cards. They collected 9, but 1 was lost. "
                        "How many more cards do they need?",
                    ),
                    "c",
                ),
            ],
        ),
    ],
)
def test_two_step_equation_choice_problems_from_scripted_draws(
    operations: list[Operation],
    chosen: list[object],
    expected: list[tuple[TwoStepQuestionData, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The shapes are split evenly, as on Strip Diagram multiple choice, and each problem is drawn
    and worded as in ``test_two_step_problems_from_scripted_draws``. Each problem's choices are
    those of ``two_step_equation_choices`` with the ticked operations and its wording's letter,
    tested in ``test_representation``; ``choice`` takes the last pair of mistakes and set.
    """
    choice_returns(monkeypatch, chosen)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_two_step_equation_choice_problems(len(expected), operations)

    choose_last(monkeypatch)
    assert questions == [
        Question(data, two_step_equation_choices(data, letter, operations))
        for data, letter in expected
    ]


@pytest.mark.parametrize(
    "operations",
    [
        [Operation.ADD, Operation.SUBTRACT],
        [Operation.SUBTRACT, Operation.DIVIDE],
        [Operation.MULTIPLY, Operation.DIVIDE],
        [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
        [Operation.ADD],
        [Operation.SUBTRACT],
        [Operation.MULTIPLY],
        [Operation.DIVIDE],
    ],
)
def test_random_two_step_equation_choice_sheets_can_always_be_finished(
    operations: list[Operation],
) -> None:
    """
    A sheet of 30 problems is produced with no problem repeated, each with four different
    equations to choose from.
    """
    questions = generate_two_step_equation_choice_problems(30, operations)
    assert len({replace(question.data, question_text=None) for question in questions}) == 30
    assert {len(set(question.response.options)) for question in questions} == {4}


@pytest.mark.parametrize(
    ("operations", "count", "largest_number", "largest_groups", "largest_size", "message"),
    [
        # as counted above
        (
            [Operation.MULTIPLY],
            669,
            999,
            6,
            20,
            "Cannot make 669 different problems: only 668 possible.",
        ),
        (
            [Operation.ADD, Operation.MULTIPLY],
            2,
            3,
            2,
            2,
            "Cannot make 2 different problems: only 0 possible.",
        ),
    ],
)
def test_two_step_equation_choice_sheet_errors(
    operations: list[Operation],
    count: int,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_two_step_equation_choice_problems(
            count,
            operations,
            largest_number=largest_number,
            largest_groups=largest_groups,
            largest_size=largest_size,
        )
    assert str(error.value) == message


FIVE_WRITTEN: list[WordProblemKind] = [
    (representation, Response.FREE_RESPONSE) for representation in Representation
]
ALL_SEVEN: list[WordProblemKind] = [
    *FIVE_WRITTEN,
    (Representation.NUMBER_LINE, Response.MULTIPLE_CHOICE),
    (Representation.EQUATION, Response.MULTIPLE_CHOICE),
]
TWO_STEP_KINDS: list[WordProblemKind] = [
    (Representation.STRIP, Response.FREE_RESPONSE),
    (Representation.NONE, Response.FREE_RESPONSE),
    (Representation.EQUATION, Response.FREE_RESPONSE),
    (Representation.EQUATION, Response.MULTIPLE_CHOICE),
]


@pytest.mark.parametrize(
    (
        "operations",
        "kinds",
        "two_steps",
        "distinct_answers",
        "largest_number",
        "up_to",
        "expected",
    ),
    [
        # Blocks show numbers up to 599, so their sums run from 2 to 1,198: 1,197, fewer than a
        # strip's 1,997.
        (
            [Operation.ADD],
            [
                (Representation.BLOCKS, Response.FREE_RESPONSE),
                (Representation.STRIP, Response.FREE_RESPONSE),
            ],
            False,
            False,
            999,
            2000,
            1197,
        ),
        # Number lines show only the addition, which the strip shows too, and the strip's
        # multiplication has the fewest: 2 to 6 groups of 2 to 20, 95.
        (
            [Operation.ADD, Operation.MULTIPLY],
            [
                (Representation.NUMBER_LINE, Response.FREE_RESPONSE),
                (Representation.STRIP, Response.FREE_RESPONSE),
            ],
            False,
            False,
            999,
            2000,
            95,
        ),
        # no kind shows multiplication
        (
            [Operation.MULTIPLY],
            [
                (Representation.NUMBER_LINE, Response.FREE_RESPONSE),
                (Representation.BLOCKS, Response.FREE_RESPONSE),
            ],
            False,
            False,
            999,
            2000,
            0,
        ),
        # with distinct answers, the sums 2 to 20 of numbers up to 10, blocks' and text's alike
        (
            [Operation.ADD],
            [
                (Representation.NONE, Response.FREE_RESPONSE),
                (Representation.BLOCKS, Response.FREE_RESPONSE),
            ],
            False,
            True,
            10,
            2000,
            19,
        ),
        # Within 3 no two-step addition has fair equations to choose from, as every one adds 1, 2
        # and 3, so the half answered by choosing has none, though the written half has some.
        (
            [Operation.ADD],
            [
                (Representation.EQUATION, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
            ],
            True,
            False,
            3,
            999,
            0,
        ),
        # Multiplication alone: c x (a x b) has the fewest, 340 written, and of those 334 with
        # fair equations to choose from.
        (
            [Operation.MULTIPLY],
            [
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
                (Representation.NONE, Response.FREE_RESPONSE),
            ],
            True,
            False,
            999,
            999,
            334,
        ),
    ],
)
def test_count_possible_mixed_word_problems(
    operations: list[Operation],
    kinds: list[WordProblemKind],
    two_steps: bool,
    distinct_answers: bool,
    largest_number: int,
    up_to: int,
    expected: int,
) -> None:
    """
    Any one problem may be drawn as any kind that can show it, so the count is the least that
    any kind allows for any operation it shows, or with two steps any shape it draws, each as on
    a sheet of that kind alone, with up to 6 groups of up to 20. A way of answering that no kind
    can make a problem of allows none.
    """
    possible = count_possible_mixed_word_problems(
        operations,
        kinds,
        up_to=up_to,
        two_steps=two_steps,
        distinct_answers=distinct_answers,
        largest_number=largest_number,
    )
    assert possible == expected


@pytest.mark.parametrize(
    ("operations", "kinds", "count", "expected"),
    [
        # every representation shows addition, so each has 2 of 10
        (
            [Operation.ADD],
            FIVE_WRITTEN,
            10,
            {(representation, Response.FREE_RESPONSE): 2 for representation in Representation},
        ),
        # only the strip shows multiplication
        (
            [Operation.MULTIPLY],
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                (Representation.NUMBER_LINE, Response.FREE_RESPONSE),
                (Representation.BLOCKS, Response.FREE_RESPONSE),
            ],
            4,
            {(Representation.STRIP, Response.FREE_RESPONSE): 4},
        ),
        # Half are chosen, all equations, the only kind chosen; the written half goes to the
        # strip, which has fewer.
        (
            [Operation.ADD],
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
            ],
            4,
            {
                (Representation.STRIP, Response.FREE_RESPONSE): 2,
                (Representation.EQUATION, Response.MULTIPLE_CHOICE): 2,
            },
        ),
    ],
)
def test_mixed_word_problems_spread_evenly(
    operations: list[Operation],
    kinds: list[WordProblemKind],
    count: int,
    expected: dict[WordProblemKind, int],
) -> None:
    """
    The ways of answering are dealt out evenly, then each problem goes to a kind answered that way
    that can show it, to whichever representation has the fewest so far, those the fewest kinds
    can show first. These cases come out the same whatever is drawn.
    """
    sheet = generate_mixed_word_problems(count, operations, kinds)

    made = Counter(
        (
            representation,
            Response.MULTIPLE_CHOICE
            if isinstance(question.response, MultipleChoice)
            else Response.FREE_RESPONSE,
        )
        for representation, question in sheet
    )
    assert made == expected


@pytest.mark.parametrize(
    ("operations", "kinds", "two_steps", "count"),
    [
        # the most problems allowed, 20
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            FIVE_WRITTEN,
            False,
            20,
        ),
        ([Operation.ADD, Operation.SUBTRACT], ALL_SEVEN, False, 20),
        (
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            TWO_STEP_KINDS,
            True,
            20,
        ),
        ([Operation.MULTIPLY], TWO_STEP_KINDS, True, 20),
    ],
)
def test_random_mixed_word_problem_sheets_can_always_be_finished(
    operations: list[Operation], kinds: list[WordProblemKind], two_steps: bool, count: int
) -> None:
    """
    A sheet is produced with no problem repeated, across the kinds too, and each problem drawn
    with a representation that can show its operations.
    """
    sheet = generate_mixed_word_problems(count, operations, kinds, two_steps=two_steps)

    assert len({replace(question.data, question_text=None) for _, question in sheet}) == count
    assert all(
        {step.operation for step in _steps(question.data)}
        <= REPRESENTATION_OPERATIONS[representation]
        for representation, question in sheet
    )


@pytest.mark.parametrize(
    ("operations", "kinds", "two_steps", "count", "largest_number"),
    [
        # every answer, the sums 2 to 13 of numbers up to 7, as tiles need
        ([Operation.ADD], FIVE_WRITTEN, False, 12, 7),
        ([Operation.MULTIPLY, Operation.DIVIDE], TWO_STEP_KINDS[:3], True, 12, 999),
    ],
)
def test_random_mixed_word_problems_have_distinct_answers(
    operations: list[Operation],
    kinds: list[WordProblemKind],
    two_steps: bool,
    count: int,
    largest_number: int,
) -> None:
    """With distinct answers, no two problems on a mixed sheet share an answer."""
    sheet = generate_mixed_word_problems(
        count,
        operations,
        kinds,
        two_steps=two_steps,
        distinct_answers=True,
        largest_number=largest_number,
    )
    assert len({question.data.answer for _, question in sheet}) == count


def test_mixed_word_problems_use_every_story_before_repeating_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A mixed sheet is worded in one pass, as a sheet of one kind is, so 14 additions, one for each
    addition story in the bank, use each story once, however they're split among the
    representations. Each kind's problems are worded first too, so the sheet's stories are the
    last 14.
    """
    used: list[str] = []
    fill = word_problems._fill
    monkeypatch.setattr(
        word_problems,
        "_fill",
        lambda template, numbers: used.append(template) or fill(template, numbers),
    )

    generate_mixed_word_problems(len(TEMPLATES[Operation.ADD]), [Operation.ADD], FIVE_WRITTEN)

    assert sorted(used[-len(TEMPLATES[Operation.ADD]) :]) == sorted(TEMPLATES[Operation.ADD])


@pytest.mark.parametrize(
    ("operations", "kinds", "distinct_answers", "count", "largest_number", "message"),
    [
        # the sums 2 to 6 of numbers up to 3
        (
            [Operation.ADD],
            [(Representation.NONE, Response.FREE_RESPONSE)],
            False,
            6,
            3,
            "Cannot make 6 different problems: only 5 possible.",
        ),
        (
            [Operation.ADD],
            [
                (Representation.NONE, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
            ],
            True,
            4,
            999,
            "Multiple choice answers are letters, so they can't be distinct answers.",
        ),
    ],
)
def test_mixed_word_problem_sheet_errors(
    operations: list[Operation],
    kinds: list[WordProblemKind],
    distinct_answers: bool,
    count: int,
    largest_number: int,
    message: str,
) -> None:
    """
    Requesting more problems than the kinds allow, or distinct answers from choices, raises
    ``ValueError``.
    """
    with pytest.raises(ValueError) as error:
        generate_mixed_word_problems(
            count,
            operations,
            kinds,
            distinct_answers=distinct_answers,
            largest_number=largest_number,
        )
    assert str(error.value) == message


def _steps(
    data: BasicOperationQuestionData | TwoStepQuestionData,
) -> tuple[BasicOperationQuestionData, ...]:
    """Return the problem's steps: its two for a two-step problem, or else the problem itself."""
    return data.steps if isinstance(data, TwoStepQuestionData) else (data,)
