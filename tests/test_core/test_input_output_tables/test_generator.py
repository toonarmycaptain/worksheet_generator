"""
Tests for the input-output table generator.

``random`` is scripted, so each case lists the questions that must be produced. The tests use
the contexts and names in ``tests.data``, standing in for the banks, and replace these
functions:

- ``random.choice`` returns the picks listed in the case, in order. For each question: on a
  multiple-choice sheet, first what is chosen once for it (for a table to choose, whether its
  tables share their inputs, then the size of its wrong tables; for a question asking for the
  rule, how it's answered); then its operation, its name if its context has one, and its rule's
  number; then with distinct answers, the cell left out, for a swapped table to choose, each
  try's kind of wrong rule and rule, and for a statement, the nearby number's rule. A pick that
  is not among its call's items raises ``ValueError``.
- ``random.sample`` returns the samples listed: each table's smaller quantities, then any wrong
  table's, and the pairs whose inputs are left out. A sample that is not drawn from its call's
  population raises ``ValueError``.
- ``random.randrange`` returns the pair left whole, or how many shared-inputs wrong tables are
  smaller than the correct one, and ``random.randint`` how many inputs are left out.
- ``random.shuffle`` reverses the list, so contexts are dealt from the start of their tuple, a
  multiple-choice question's correct option is last, and so on, as each test says.
"""

from typing import Any

import pytest

from core.basic_operations.data import Operation
from core.input_output_tables.data import (
    Blanks,
    ChoiceType,
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    RuleForm,
)
from core.input_output_tables.generator import (
    count_possible_answers,
    generate_input_output_table_questions,
)
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import NAMES, ORANGES, READING, SALE, SOCKS, TABLE_CONTEXTS
from tests.helpers import (
    choice_returns,
    randint_returns,
    randrange_returns,
    reverse_shuffle,
    sample_returns,
)

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
INPUTS, OUTPUTS, INPUTS_AND_OUTPUTS = Blanks
TABLE, SENTENCE, STATEMENT = ChoiceType
SENTENCE_FORM, PLAIN, EXPLAINED = RuleForm

# The kinds of wrong rule for multiplying by 8: another operation, then a number up to 3 away
WRONG_OPERATIONS_BY_8 = [(ADD, 8), (SUBTRACT, 8), (DIVIDE, 8)]
WRONG_NUMBERS_FOR_8 = [(MULTIPLY, 5), (MULTIPLY, 6), (MULTIPLY, 7), (MULTIPLY, 9), (MULTIPLY, 10)]
# The table times 8, and swapped
TIMES_8 = ((4, 32), (7, 56), (9, 72), (10, 80))
TIMES_8_SWAPPED = ((32, 4), (56, 7), (72, 9), (80, 10))


def use_test_banks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the context and name banks with the stand-ins in ``tests.data``."""
    monkeypatch.setattr("core.input_output_tables.generator.CONTEXTS", TABLE_CONTEXTS)
    monkeypatch.setattr("core.input_output_tables.generator.NAMES", NAMES)


@pytest.mark.parametrize(
    ("operations", "blanks", "count", "chosen", "sampled", "ranged", "drawn", "expected"),
    [
        (
            # the first pair whole, the other outputs left out
            [MULTIPLY],
            OUTPUTS,
            1,
            [MULTIPLY, 8],
            [[4, 7, 9, 10]],
            [0],
            [],
            [InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (), (1, 2, 3))],
        ),
        (
            # division takes the larger quantity first
            [DIVIDE],
            OUTPUTS,
            1,
            [DIVIDE, 8],
            [[4, 7, 9, 10]],
            [3],
            [],
            [InputOutputTableQuestionData(SOCKS, None, DIVIDE, 8, TIMES_8_SWAPPED, (), (0, 1, 2))],
        ),
        (
            # addition's smaller quantities leave room for 6 more: from 1 to 94
            [ADD],
            OUTPUTS,
            1,
            [ADD, 6],
            [[12, 19, 27, 33]],
            [1],
            [],
            [
                InputOutputTableQuestionData(
                    SALE, None, ADD, 6, ((12, 18), (19, 25), (27, 33), (33, 39)), (), (0, 2, 3)
                )
            ],
        ),
        (
            # subtraction takes the larger quantity first
            [SUBTRACT],
            OUTPUTS,
            1,
            [SUBTRACT, 6],
            [[12, 19, 27, 33]],
            [2],
            [],
            [
                InputOutputTableQuestionData(
                    SALE, None, SUBTRACT, 6, ((18, 12), (25, 19), (33, 27), (39, 33)), (), (0, 1, 3)
                )
            ],
        ),
        (
            # 1, 3, 5 has two equal gaps in a row, so it's drawn again
            [MULTIPLY],
            OUTPUTS,
            1,
            [MULTIPLY, 3],
            [[1, 3, 5, 9], [1, 3, 4, 9]],
            [0],
            [],
            [
                InputOutputTableQuestionData(
                    SOCKS, None, MULTIPLY, 3, ((1, 3), (3, 9), (4, 12), (9, 27)), (), (1, 2, 3)
                )
            ],
        ),
        (
            # inputs only
            [DIVIDE],
            INPUTS,
            1,
            [DIVIDE, 8],
            [[4, 7, 9, 10]],
            [1],
            [],
            [InputOutputTableQuestionData(SOCKS, None, DIVIDE, 8, TIMES_8_SWAPPED, (0, 2, 3), ())],
        ),
        (
            # inputs and outputs: one of the three pairs left out loses its input
            [DIVIDE],
            INPUTS_AND_OUTPUTS,
            1,
            [DIVIDE, 8],
            [[4, 7, 9, 10], [3]],
            [2],
            [1],
            [InputOutputTableQuestionData(SOCKS, None, DIVIDE, 8, TIMES_8_SWAPPED, (3,), (0, 1))],
        ),
        (
            # inputs and outputs: two lose their inputs, in order whatever order they're drawn in
            [ADD],
            INPUTS_AND_OUTPUTS,
            1,
            [ADD, 6],
            [[12, 19, 27, 33], [3, 1]],
            [0],
            [2],
            [
                InputOutputTableQuestionData(
                    SALE, None, ADD, 6, ((12, 18), (19, 25), (27, 33), (33, 39)), (1, 3), (2,)
                )
            ],
        ),
        (
            # contexts are dealt in turn, a name drawn for the one with a name, and dealt again
            # once all are used
            [MULTIPLY],
            OUTPUTS,
            4,
            [MULTIPLY, 8, MULTIPLY, 4, MULTIPLY, "Ana", 5, MULTIPLY, 2],
            [[4, 7, 9, 10], [1, 2, 4, 7], [2, 3, 5, 6], [1, 2, 4, 7]],
            [0, 0, 0, 0],
            [],
            [
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (), (1, 2, 3)),
                InputOutputTableQuestionData(
                    ORANGES, None, MULTIPLY, 4, ((1, 4), (2, 8), (4, 16), (7, 28)), (), (1, 2, 3)
                ),
                InputOutputTableQuestionData(
                    READING, "Ana", MULTIPLY, 5, ((2, 10), (3, 15), (5, 25), (6, 30)), (), (1, 2, 3)
                ),
                InputOutputTableQuestionData(
                    SOCKS, None, MULTIPLY, 2, ((1, 2), (2, 4), (4, 8), (7, 14)), (), (1, 2, 3)
                ),
            ],
        ),
        (
            # each question's operation is drawn from those given, its context from its own deck
            [ADD, DIVIDE],
            OUTPUTS,
            2,
            [DIVIDE, 2, ADD, 1],
            [[1, 2, 4, 7], [10, 11, 13, 16]],
            [0, 0],
            [],
            [
                InputOutputTableQuestionData(
                    SOCKS, None, DIVIDE, 2, ((2, 1), (4, 2), (8, 4), (14, 7)), (), (1, 2, 3)
                ),
                InputOutputTableQuestionData(
                    SALE, None, ADD, 1, ((10, 11), (11, 12), (13, 14), (16, 17)), (), (1, 2, 3)
                ),
            ],
        ),
    ],
)
def test_tables_to_complete(
    operations: list[Operation],
    blanks: Blanks,
    count: int,
    chosen: list[Any],
    sampled: list[list[int]],
    ranged: list[int],
    drawn: list[int],
    expected: list[InputOutputTableQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each table follows its drawn operation and number, leaving out the cells drawn."""
    use_test_banks(monkeypatch)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    randrange_returns(monkeypatch, ranged)
    randint_returns(monkeypatch, drawn)
    reverse_shuffle(monkeypatch)

    questions = generate_input_output_table_questions(count, operations, blanks=blanks)

    assert questions == [Question(data, FreeResponse()) for data in expected]


@pytest.mark.parametrize(
    ("operations", "blanks", "count", "chosen", "sampled", "expected", "last_offered"),
    [
        (
            # the second table's 2 is used, so its cell isn't offered
            [DIVIDE],
            OUTPUTS,
            2,
            [DIVIDE, 2, (1, 1), DIVIDE, 3, (2, 1)],
            [[1, 2, 4, 7], [1, 2, 4, 7]],
            [
                InputOutputTableQuestionData(
                    SOCKS, None, DIVIDE, 2, ((2, 1), (4, 2), (8, 4), (14, 7)), (), (1,)
                ),
                InputOutputTableQuestionData(
                    ORANGES, None, DIVIDE, 3, ((3, 1), (6, 2), (12, 4), (21, 7)), (), (2,)
                ),
            ],
            [(0, 1), (2, 1), (3, 1)],
        ),
        (
            # inputs only: only inputs are offered
            [MULTIPLY],
            INPUTS,
            1,
            [MULTIPLY, 8, (1, 0)],
            [[4, 7, 9, 10]],
            [InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (1,), ())],
            [(0, 0), (1, 0), (2, 0), (3, 0)],
        ),
        (
            # inputs and outputs: every cell is offered
            [MULTIPLY],
            INPUTS_AND_OUTPUTS,
            1,
            [MULTIPLY, 8, (3, 0)],
            [[4, 7, 9, 10]],
            [InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (3,), ())],
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)],
        ),
        (
            # the fifth table's outputs, 1, 2, 4 and 7, are all used, so it's drawn again
            [DIVIDE],
            OUTPUTS,
            5,
            [
                *(DIVIDE, 2, (0, 1)),
                *(DIVIDE, 3, (1, 1)),
                *(DIVIDE, "Ana", 4, (2, 1)),
                *(DIVIDE, 5, (3, 1)),
                *(DIVIDE, 6),
                *(DIVIDE, "Ana", 7, (1, 1)),
            ],
            [[1, 2, 4, 7], [1, 2, 4, 7], [1, 2, 4, 7], [1, 2, 4, 7], [1, 2, 4, 7], [1, 3, 4, 9]],
            [
                InputOutputTableQuestionData(
                    SOCKS, None, DIVIDE, 2, ((2, 1), (4, 2), (8, 4), (14, 7)), (), (0,)
                ),
                InputOutputTableQuestionData(
                    ORANGES, None, DIVIDE, 3, ((3, 1), (6, 2), (12, 4), (21, 7)), (), (1,)
                ),
                InputOutputTableQuestionData(
                    READING, "Ana", DIVIDE, 4, ((4, 1), (8, 2), (16, 4), (28, 7)), (), (2,)
                ),
                InputOutputTableQuestionData(
                    SOCKS, None, DIVIDE, 5, ((5, 1), (10, 2), (20, 4), (35, 7)), (), (3,)
                ),
                InputOutputTableQuestionData(
                    READING, "Ana", DIVIDE, 7, ((7, 1), (21, 3), (28, 4), (63, 9)), (), (1,)
                ),
            ],
            [(1, 1), (3, 1)],
        ),
    ],
)
def test_distinct_answers_leave_out_one_unused_number(
    operations: list[Operation],
    blanks: Blanks,
    count: int,
    chosen: list[Any],
    sampled: list[list[int]],
    expected: list[InputOutputTableQuestionData],
    last_offered: list[tuple[int, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each table leaves out one number, chosen from the cells ``blanks`` allows whose numbers no
    earlier table left out; a table whose numbers are all used is drawn again.
    """
    use_test_banks(monkeypatch)
    offered = choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)

    questions = generate_input_output_table_questions(
        count, operations, blanks=blanks, distinct_answers=True
    )

    assert questions == [Question(data, FreeResponse()) for data in expected]
    assert offered[-1] == last_offered


@pytest.mark.parametrize(
    ("operations", "chosen", "ranged", "sampled", "expected"),
    [
        (
            # swapped look: adding 8, its numbers adding up to more
            [MULTIPLY],
            [False, True, MULTIPLY, 8, WRONG_OPERATIONS_BY_8, (ADD, 8)],
            [],
            [[4, 7, 9, 10], [30, 41, 57, 60]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((38, 30), (49, 41), (65, 57), (68, 60)),
                        ((30, 38), (41, 49), (57, 65), (60, 68)),
                        TIMES_8_SWAPPED,
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # swapped look, a wrong number adding up to less: times 5 puts a 4 in the first pair,
            # as the correct table has, so times 6 is tried
            [MULTIPLY],
            [
                *(False, False, MULTIPLY, 8),
                *(WRONG_NUMBERS_FOR_8, (MULTIPLY, 5), WRONG_NUMBERS_FOR_8, (MULTIPLY, 6)),
            ],
            [],
            [[4, 7, 9, 10], [4, 5, 7, 10], [1, 3, 4, 6]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((6, 1), (18, 3), (24, 4), (36, 6)),
                        ((1, 6), (3, 18), (4, 24), (6, 36)),
                        TIMES_8_SWAPPED,
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # swapped look: subtracting 6 adds up to more than the correct table, not less, so
            # adding 4 is tried
            [ADD],
            [
                *(False, False, ADD, 6),
                *([(SUBTRACT, 6), (MULTIPLY, 6), (DIVIDE, 6)], (SUBTRACT, 6)),
                *([(ADD, 3), (ADD, 4), (ADD, 5), (ADD, 7), (ADD, 8), (ADD, 9)], (ADD, 4)),
            ],
            [],
            [[12, 19, 27, 33], [50, 61, 63, 80], [2, 5, 9, 10]],
            Question(
                InputOutputTableQuestionData(
                    SALE, None, ADD, 6, ((12, 18), (19, 25), (27, 33), (33, 39))
                ),
                MultipleChoice(
                    (
                        ((6, 2), (9, 5), (13, 9), (14, 10)),
                        ((2, 6), (5, 9), (9, 13), (10, 14)),
                        ((18, 12), (25, 19), (33, 27), (39, 33)),
                        ((12, 18), (19, 25), (27, 33), (33, 39)),
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # division alone has no shared-inputs look, so none is drawn: only the size
            [DIVIDE],
            [True, DIVIDE, 8, [(ADD, 8), (SUBTRACT, 8), (MULTIPLY, 8)], (ADD, 8)],
            [],
            [[4, 7, 9, 10], [30, 41, 57, 60]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, DIVIDE, 8, TIMES_8_SWAPPED),
                MultipleChoice(
                    (
                        ((38, 30), (49, 41), (65, 57), (68, 60)),
                        ((30, 38), (41, 49), (57, 65), (60, 68)),
                        TIMES_8,
                        TIMES_8_SWAPPED,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # shared inputs, all four right in the second pair, 7 and 56, and one smaller than
            # the correct table: plus 8 and times 5 and 6 would put 56 above the next output, out
            # of order, so the wrong rules left are times 7, 9 and 10, shuffled in reverse
            [MULTIPLY],
            [True, MULTIPLY, 8, 1],
            [1],
            [[4, 7, 9, 10], [1]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((4, 36), (7, 56), (9, 81), (10, 90)),
                        ((4, 40), (7, 56), (9, 90), (10, 100)),
                        ((4, 28), (7, 56), (9, 63), (10, 70)),
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # shared inputs, all four right in the first pair, as STAAR's socks tables are, and
            # all three wrong tables smaller than the correct one
            [MULTIPLY],
            [True, MULTIPLY, 8, 1],
            [3],
            [[4, 7, 9, 10], [0]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((4, 32), (7, 35), (9, 45), (10, 50)),
                        ((4, 32), (7, 42), (9, 54), (10, 60)),
                        ((4, 32), (7, 49), (9, 63), (10, 70)),
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # shared inputs, all four right in two pairs, the first and last: only times 5, 6
            # and 7 keep their outputs in order between 32 and 80, all smaller
            [MULTIPLY],
            [True, MULTIPLY, 8, 2],
            [3],
            [[4, 7, 9, 10], [3, 0]],
            Question(
                InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((4, 32), (7, 35), (9, 45), (10, 80)),
                        ((4, 32), (7, 42), (9, 54), (10, 80)),
                        ((4, 32), (7, 49), (9, 63), (10, 80)),
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
    ],
)
def test_tables_to_choose(
    operations: list[Operation],
    chosen: list[Any],
    ranged: list[int],
    sampled: list[list[int]],
    expected: Question[Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A table to choose comes with three wrong tables. In the swapped look, they are the table
    swapped, a wrong rule's table and that one swapped; a wrong table of the wrong size, or with
    a number in the same pair as the correct table, is tried again. In the shared-inputs look,
    all four are right in the pair drawn and have the same inputs, and the wrong tables follow
    wrong rules in the other pairs, the number asked for smaller than the correct table.
    """
    use_test_banks(monkeypatch)
    choice_returns(monkeypatch, chosen)
    randrange_returns(monkeypatch, ranged)
    sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)

    questions = generate_input_output_table_questions(1, operations, choice_types=[TABLE])

    assert questions == [expected]


@pytest.mark.parametrize(
    ("chosen", "ranged", "sampled", "expected"),
    [
        (
            # swapped look, one try allowed: times 5 adds up to less than the correct table, not
            # more
            [
                *(False, True, MULTIPLY, 8, WRONG_NUMBERS_FOR_8, (MULTIPLY, 5)),
                *(MULTIPLY, 8, WRONG_OPERATIONS_BY_8, (ADD, 8)),
            ],
            [],
            [[4, 7, 9, 10], [1, 2, 4, 7], [4, 7, 9, 10], [30, 41, 57, 60]],
            Question(
                InputOutputTableQuestionData(ORANGES, None, MULTIPLY, 8, TIMES_8),
                MultipleChoice(
                    (
                        ((38, 30), (49, 41), (65, 57), (68, 60)),
                        ((30, 38), (41, 49), (57, 65), (60, 68)),
                        TIMES_8_SWAPPED,
                        TIMES_8,
                    ),
                    frozenset({3}),
                ),
            ),
        ),
        (
            # shared inputs, all three larger: right in the second pair, times 8 has only times 9
            # and 10 above it, so new numbers are drawn, times 3 right in the first pair, whose
            # times 4, 5 and 6 are larger
            [True, MULTIPLY, 8, 1, MULTIPLY, 3, 1],
            [0],
            [[4, 7, 9, 10], [1], [1, 2, 4, 7], [0]],
            Question(
                InputOutputTableQuestionData(
                    ORANGES, None, MULTIPLY, 3, ((1, 3), (2, 6), (4, 12), (7, 21))
                ),
                MultipleChoice(
                    (
                        ((1, 3), (2, 8), (4, 16), (7, 28)),
                        ((1, 3), (2, 10), (4, 20), (7, 35)),
                        ((1, 3), (2, 12), (4, 24), (7, 42)),
                        ((1, 3), (2, 6), (4, 12), (7, 21)),
                    ),
                    frozenset({3}),
                ),
            ),
        ),
    ],
)
def test_new_numbers_for_a_table_to_choose_keep_its_look_and_size(
    chosen: list[Any],
    ranged: list[int],
    sampled: list[list[int]],
    expected: Question[Any, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    When a question's numbers leave no room for wrong tables of the size chosen, new numbers are
    drawn, with the next context, and its look and size are kept: the picks have none for the
    second try, so drawing them again would fail.
    """
    use_test_banks(monkeypatch)
    monkeypatch.setattr("core.input_output_tables.generator.WRONG_TABLE_TRIES", 1)
    choice_returns(monkeypatch, chosen)
    randrange_returns(monkeypatch, ranged)
    sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)

    questions = generate_input_output_table_questions(1, [MULTIPLY], choice_types=[TABLE])

    assert questions == [expected]


@pytest.mark.parametrize(
    ("operations", "choice_types", "count", "chosen", "ranged", "sampled", "expected"),
    [
        (
            # a sentence, one operation with four numbers: one wrong number below 8, two above
            [MULTIPLY],
            [SENTENCE],
            1,
            ["numbers", MULTIPLY, 8],
            [1],
            [[4, 7, 9, 10], [6], [9, 10]],
            [
                Question(
                    InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), SENTENCE_FORM),
                    MultipleChoice(
                        ((MULTIPLY, 10), (MULTIPLY, 9), (MULTIPLY, 6), (MULTIPLY, 8)),
                        frozenset({3}),
                    ),
                )
            ],
        ),
        (
            # a sentence about division, reversed: its wrong number above 8
            [DIVIDE],
            [SENTENCE],
            1,
            ["reverse", DIVIDE, 8],
            [0],
            [[4, 7, 9, 10], [10]],
            [
                Question(
                    InputOutputRuleQuestionData(
                        SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), SENTENCE_FORM
                    ),
                    MultipleChoice(
                        ((MULTIPLY, 10), (DIVIDE, 10), (MULTIPLY, 8), (DIVIDE, 8)), frozenset({3})
                    ),
                )
            ],
        ),
        (
            # a plain statement, with an operation of the other kind, its wrong number below
            [MULTIPLY],
            [STATEMENT],
            1,
            [PLAIN, "other operation", MULTIPLY, 8, ADD],
            [1],
            [[4, 7, 9, 10], [6]],
            [
                Question(
                    InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
                    MultipleChoice(
                        ((ADD, 6), (MULTIPLY, 6), (ADD, 8), (MULTIPLY, 8)), frozenset({3})
                    ),
                )
            ],
        ),
        (
            # an explained statement about addition, reversed
            [ADD],
            [STATEMENT],
            1,
            [EXPLAINED, "reverse", ADD, 6],
            [0],
            [[12, 19, 27, 33], [9]],
            [
                Question(
                    InputOutputRuleQuestionData(
                        SALE, None, ((12, 18), (19, 25), (27, 33), (33, 39)), (ADD, 6), EXPLAINED
                    ),
                    MultipleChoice(
                        ((SUBTRACT, 9), (ADD, 9), (SUBTRACT, 6), (ADD, 6)), frozenset({3})
                    ),
                )
            ],
        ),
        (
            # three wrong numbers below 2 aren't there, so new numbers are drawn, times 8, with
            # the same pattern and place, and the next context
            [MULTIPLY],
            [SENTENCE],
            1,
            ["numbers", MULTIPLY, 2, MULTIPLY, 8],
            [3],
            [[4, 7, 9, 10], [4, 7, 9, 10], [5, 6, 7]],
            [
                Question(
                    InputOutputRuleQuestionData(
                        ORANGES, None, TIMES_8, (MULTIPLY, 8), SENTENCE_FORM
                    ),
                    MultipleChoice(
                        ((MULTIPLY, 7), (MULTIPLY, 6), (MULTIPLY, 5), (MULTIPLY, 8)),
                        frozenset({3}),
                    ),
                )
            ],
        ),
        (
            # the questions are shared evenly among the types, then shuffled: here reversed
            [MULTIPLY],
            [SENTENCE, STATEMENT],
            2,
            [PLAIN, "reverse", MULTIPLY, 8, "numbers", MULTIPLY, 4],
            [0, 2],
            [[4, 7, 9, 10], [9], [2, 3, 5, 6], [2, 3], [7]],
            [
                Question(
                    InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
                    MultipleChoice(
                        ((DIVIDE, 9), (MULTIPLY, 9), (DIVIDE, 8), (MULTIPLY, 8)), frozenset({3})
                    ),
                ),
                Question(
                    InputOutputRuleQuestionData(
                        ORANGES,
                        None,
                        ((2, 8), (3, 12), (5, 20), (6, 24)),
                        (MULTIPLY, 4),
                        SENTENCE_FORM,
                    ),
                    MultipleChoice(
                        ((MULTIPLY, 7), (MULTIPLY, 3), (MULTIPLY, 2), (MULTIPLY, 4)),
                        frozenset({3}),
                    ),
                ),
            ],
        ),
    ],
)
def test_questions_asking_for_the_rule(
    operations: list[Operation],
    choice_types: list[ChoiceType],
    count: int,
    chosen: list[Any],
    ranged: list[int],
    sampled: list[list[int]],
    expected: list[Question[Any, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The rule is chosen from four, its own and three wrong rules' in the pattern drawn, with the
    rule's number at the place drawn among the numbers, shown as a sentence to circle or as
    statements, plain or explained.
    """
    use_test_banks(monkeypatch)
    choice_returns(monkeypatch, chosen)
    randrange_returns(monkeypatch, ranged)
    sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)

    questions = generate_input_output_table_questions(count, operations, choice_types=choice_types)

    assert questions == expected


@pytest.mark.parametrize(
    ("operations", "choice_types", "chosen", "sampled", "population"),
    [
        # a table about multiplication whose rule is chosen leaves out 1, whose pair would show
        # the rule's number
        (
            [MULTIPLY],
            [STATEMENT],
            [PLAIN, "reverse", MULTIPLY, 8],
            [[4, 7, 9, 10], [9]],
            range(2, 11),
        ),
        ([DIVIDE], [STATEMENT], [PLAIN, "reverse", DIVIDE, 8], [[4, 7, 9, 10], [9]], range(2, 11)),
        ([MULTIPLY], [SENTENCE], ["reverse", MULTIPLY, 8], [[4, 7, 9, 10], [9]], range(2, 11)),
        # a statement about addition keeps 1
        ([ADD], [STATEMENT], [PLAIN, "reverse", ADD, 6], [[12, 19, 27, 33], [9]], range(1, 95)),
    ],
)
def test_the_smaller_quantities_a_question_asking_for_the_rule_draws_from(
    operations: list[Operation],
    choice_types: list[ChoiceType],
    chosen: list[Any],
    sampled: list[list[int]],
    population: range,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The table's smaller quantities are drawn from ``population``; its wrong number above."""
    use_test_banks(monkeypatch)
    choice_returns(monkeypatch, chosen)
    randrange_returns(monkeypatch, [0])
    populations = sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)

    generate_input_output_table_questions(1, operations, choice_types=choice_types)

    assert populations[0] == population


@pytest.mark.parametrize(
    ("count", "operations", "blanks", "choice_types", "distinct_answers", "message"),
    [
        (1, [], OUTPUTS, [], False, "At least one operation is needed."),
        (
            1,
            [MULTIPLY],
            OUTPUTS,
            [TABLE],
            True,
            "Multiple-choice questions leave out no numbers to keep distinct.",
        ),
        (
            # division's outputs are 1 to 10
            11,
            [DIVIDE],
            OUTPUTS,
            [],
            True,
            "Cannot make 11 tables with different missing numbers: only 10 possible.",
        ),
    ],
)
def test_generate_input_output_table_questions_errors(
    count: int,
    operations: list[Operation],
    blanks: Blanks,
    choice_types: list[ChoiceType],
    distinct_answers: bool,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        generate_input_output_table_questions(
            count,
            operations,
            blanks=blanks,
            choice_types=choice_types,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("operations", "blanks", "possible"),
    [
        # division's outputs: the smaller quantities, 1 to 10
        ([DIVIDE], OUTPUTS, 10),
        # its inputs: the 41 products of 1 to 10 and 2 to 10
        ([DIVIDE], INPUTS, 41),
        # both: the products, and 1
        ([DIVIDE], INPUTS_AND_OUTPUTS, 42),
        ([MULTIPLY], OUTPUTS, 41),
        ([MULTIPLY], INPUTS, 10),
        ([MULTIPLY], INPUTS_AND_OUTPUTS, 42),
        # addition's outputs: 1 + 1 up to 100
        ([ADD], OUTPUTS, 99),
        # subtraction's outputs: 1 up to 100 - 1
        ([SUBTRACT], OUTPUTS, 99),
        ([ADD, SUBTRACT], OUTPUTS, 100),
        ([ADD, SUBTRACT, MULTIPLY, DIVIDE], INPUTS_AND_OUTPUTS, 100),
    ],
)
def test_count_possible_answers(operations: list[Operation], blanks: Blanks, possible: int) -> None:
    """The count is the number of different numbers a table's one blank can hold."""
    assert count_possible_answers(operations, blanks) == possible
