"""
Tests for the order of operations worksheet PDFs, rendered from hand-built questions.

The question generator is not used: each question is built by hand with its response, most of
them from STAAR's released items.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/order_of_operations_worksheet_pdf_expecteds.txt``. The text includes every question,
the expressions and steps under it with their stacked fractions and boxes, the lettered choices
in a row or one under another, the expressions to circle, the answer lines, the answer bank and
pattern, the answer key and the page breaks. To regenerate sections after an intended change,
uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it (``-k``
selects cases).
"""

from collections.abc import Sequence
from decimal import Decimal
from fractions import Fraction

import pytest

from core.arithmetic_expressions.data import Number
from core.arithmetic_expressions.representation import parse
from core.basic_operations.data import Operation
from core.order_of_operations.data import (
    ErrorChoice,
    FindErrorQuestionData,
    FirstChoice,
    FirstOperationQuestionData,
    FirstResultQuestionData,
    HasValueQuestionData,
    Improper,
    NextStepQuestionData,
    Order,
    OrderOfOperationsQuestion,
    Pair,
    ParenthesesQuestionData,
    StepBlankQuestionData,
    Then,
    Timing,
    ValueCountQuestionData,
    ValueQuestionData,
    Why,
)
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import REAL_CASE_SLOTS
from tests.helpers import GOLDENS, pdf_text, read_sections, render_order_of_operations

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
STAAR_24 = tuple(
    parse(text) for text in ("(36 - 3) * 4", "2 * (8 + 4)", "96 ÷ (12 - 8)", "(40 + 8) ÷ 2")
)
SHOWN_28 = tuple(
    parse(text) for text in ("35 * 8", "28 + 7 * 8", "35 * 12 - 4", "28 + 56", "28 + 84 - 4")
)
VALUE = ValueQuestionData(parse("[45 - (6 + 3)] * 27"), True, 972)
FRACTION_VALUE = ValueQuestionData(parse("1/4 + (2 * 5)"), True, Fraction(41, 4))
NEXT_STEP = NextStepQuestionData(
    parse("6[2 + (1.7 * 2.3)] + 39"), True, (parse("6[2 + 3.91] + 39"),)
)
TWO_STEPS = NextStepQuestionData(
    parse("28 + 7 * (12 - 4)"), True, (parse("28 + 7 * 8"), parse("28 + 56")), SHOWN_28
)
DOES_NOT = HasValueQuestionData(STAAR_24, 24, False, True, STAAR_24[0])
FIRST = FirstOperationQuestionData(
    parse("40 ÷ (5 + 3) * 8 + 1"), True, FirstChoice(Pair(5, ADD, 3), Why.IN_PARENTHESES)
)
INDICATE = ParenthesesQuestionData(
    parse("10 ÷ 5 + 4(72 - 6)"), True, Order(Pair(72, SUBTRACT, 6), Then(MULTIPLY, 4, False))
)
STATEMENT = ParenthesesQuestionData(parse("3 * (8 + 2) ÷ 2"), True, Timing(Pair(8, ADD, 2), True))
FIND_ERROR = FindErrorQuestionData(
    parse("60 ÷ 6[(1 * 2) + (4 * 2)]"),
    (parse("60 ÷ 6[2 + 8]"), parse("60 ÷ 12 + 8"), parse("5 + 8"), Number(13)),
    True,
    ErrorChoice(2, (Pair(2, ADD, 8),)),
    sign_before_implied=True,
)

# One of each, written: an answer line, two to explain, the expressions to circle, a stacked
# fraction, and a worked simplification's lines. It runs onto a second page.
WRITTEN: list[OrderOfOperationsQuestion] = [
    Question(VALUE, FreeResponse()),
    Question(FRACTION_VALUE, FreeResponse()),
    Question(NEXT_STEP, FreeResponse()),
    Question(TWO_STEPS, FreeResponse()),
    Question(DOES_NOT, FreeResponse()),
    Question(FIRST, FreeResponse()),
    Question(INDICATE, FreeResponse()),
    Question(FIND_ERROR, FreeResponse()),
]

# One of each, as multiple choice: values and expressions in a row, an improper fraction, five
# to select two from, and sentences one under another.
CHOICES: list[OrderOfOperationsQuestion] = [
    Question(VALUE, MultipleChoice((1134, 972, 198, 1206), frozenset({1}))),
    Question(
        FRACTION_VALUE,
        MultipleChoice(
            (Fraction(41, 4), Fraction(45, 4), Improper(Fraction(11, 4)), Fraction(15, 4)),
            frozenset({0}),
        ),
    ),
    Question(
        NEXT_STEP,
        MultipleChoice(
            (
                parse("6[2 + 3.91] + 39"),
                parse("12 + (1.7 * 2.3) + 39"),
                parse("6[2 + 1.7] * 41.3"),
                parse("6[3.7 * 2.3] + 39"),
            ),
            frozenset({0}),
        ),
    ),
    Question(TWO_STEPS, MultipleChoice(SHOWN_28, frozenset({1, 3}))),
    Question(DOES_NOT, MultipleChoice(STAAR_24, frozenset({0}))),
    Question(
        FIRST,
        MultipleChoice(
            (
                FirstChoice(Pair(40, DIVIDE, 5), Why.LEFT_TO_RIGHT),
                FirstChoice(Pair(5, ADD, 3), Why.IN_PARENTHESES),
                FirstChoice(Pair(3, MULTIPLY, 8), Why.BEFORE, ADD),
                FirstChoice(Pair(8, ADD, 1), Why.RIGHT_TO_LEFT),
            ),
            frozenset({1}),
        ),
    ),
    Question(
        INDICATE,
        MultipleChoice(
            (
                Order(Pair(10, DIVIDE, 5), Then(ADD, 4, True)),
                Order(Pair(4, MULTIPLY, 72), Then(SUBTRACT, 6, True)),
                Order(Pair(5, ADD, 4), Pair(72, SUBTRACT, 6)),
                Order(Pair(72, SUBTRACT, 6), Then(MULTIPLY, 4, False)),
            ),
            frozenset({3}),
        ),
    ),
    Question(
        STATEMENT,
        MultipleChoice(
            (
                Timing(Pair(8, ADD, 2), True),
                Timing(Pair(8, ADD, 2), False),
                Timing(Pair(2, DIVIDE, 2), False),
                Timing(Pair(3, MULTIPLY, 8), True),
            ),
            frozenset({0}),
        ),
    ),
    Question(
        FIND_ERROR,
        MultipleChoice(
            (
                ErrorChoice(1, (Pair(2, ADD, 4),)),
                ErrorChoice(2, (Pair(2, ADD, 8),)),
                ErrorChoice(3, (Pair(12, ADD, 8),)),
                ErrorChoice(4, (Pair(5, ADD, 8),), 12),
            ),
            frozenset({1}),
        ),
    ),
]

# Twelve tiles forms with different answers, as a tiles sheet asks them
TILES: list[OrderOfOperationsQuestion] = [
    Question(VALUE, FreeResponse()),
    Question(FRACTION_VALUE, FreeResponse()),
    Question(ValueQuestionData(parse("4[4.5 - 2(1.2)]"), True, Decimal("8.4")), FreeResponse()),
    Question(
        StepBlankQuestionData(parse("28 + 7 * (12 - 4)"), True, parse("28 + 56"), (1,), 56),
        FreeResponse(),
    ),
    Question(
        StepBlankQuestionData(parse("28 + 7 * (12 - 4)"), True, parse("28 + 7 * 8"), (1, 1), 8),
        FreeResponse(),
    ),
    Question(ValueCountQuestionData(STAAR_24, 24, True, 3), FreeResponse()),
    Question(ValueCountQuestionData(STAAR_24, 132, True, 1), FreeResponse()),
    Question(
        FirstResultQuestionData(parse("10 ÷ 5 + 4(72 - 6)"), True, Pair(72, SUBTRACT, 6), 66),
        FreeResponse(),
    ),
    Question(
        FirstResultQuestionData(parse("[36 + (3 * 2)] ÷ 6"), True, Pair(3, MULTIPLY, 2), 6),
        FreeResponse(),
    ),
    Question(ValueQuestionData(parse("3(25 + 19) + 4(3)"), True, 144), FreeResponse()),
    Question(ValueQuestionData(parse("10[3 + (7 + 5) ÷ 3]"), True, 70), FreeResponse()),
    Question(ValueQuestionData(parse("2 * [30 - 20 ÷ (5 * 2)]"), True, 56), FreeResponse()),
]


EXPECTED = GOLDENS / "order_of_operations_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "title", "label"),
    [
        ("written", WRITTEN, None, False, "Order of Operations", "Sheet A"),
        ("written_answer_key", WRITTEN, None, True, "Order of Operations", "Sheet A"),
        ("choices_answer_key", CHOICES, None, True, "Order of Operations", "Sheet A"),
        ("tiles_answer_key", TILES, REAL_CASE_SLOTS, True, "Order of Operations", "Sheet A"),
        ("other_title_and_label", WRITTEN[:2], None, False, "Simplify", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[OrderOfOperationsQuestion],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``order_of_operations_worksheet_pdf_expecteds.txt``.

    One comparison covers each problem's question, the expressions and steps under it, its
    lettered choices and their layout, the expressions to circle, its answer lines, the answer
    bank and pattern, the answer key, the page breaks, and the title and label.
    """
    actual = pdf_text(render_order_of_operations(questions, slot_of, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


def test_a_tiles_sheet_asks_only_tiles_forms() -> None:
    """A tiles sheet refuses a question with no tiles form, or a lettered one."""
    refused = r"A self-check tiles sheet asks only written tiles forms\."
    with pytest.raises(ValueError, match=refused):
        render_order_of_operations(CHOICES[:1], REAL_CASE_SLOTS[:1], False, "Order", "A")
