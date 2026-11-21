"""
Tests for what an order of operations question shows: its question, the lines under it, its
options' wording, the answer key's entry and the tile answer. Most questions are STAAR's.
"""

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
    Pair,
    ParenthesesQuestionData,
    StepBlankQuestionData,
    Then,
    Timing,
    ValueCountQuestionData,
    ValueQuestionData,
    Why,
)
from core.order_of_operations.representation import (
    Option,
    OrderOfOperationsQuestionData,
    circled,
    option_pieces,
    question,
    shown_lines,
    solution,
    tile_answer,
)
from core.question import BLANK
from core.written_numbers import inline
from tests.data import MINUS, TIMES

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
SHOWN_28 = tuple(
    parse(text) for text in ("35 * 8", "28 + 7 * 8", "35 * 12 - 4", "28 + 56", "28 + 84 - 4")
)
STAAR_24 = tuple(
    parse(text) for text in ("(36 - 3) * 4", "2 * (8 + 4)", "96 ÷ (12 - 8)", "(40 + 8) ÷ 2")
)
STAAR_24_TEXT = [
    f"(36 {MINUS} 3) {TIMES} 4",
    f"2 {TIMES} (8 + 4)",
    f"96 ÷ (12 {MINUS} 8)",
    "(40 + 8) ÷ 2",
]
STAAR_24_VALUES = "; ".join(
    f"{text} = {each}" for text, each in zip(STAAR_24_TEXT, (132, 24, 24, 24), strict=True)
)
ERROR_STEPS = (parse("60 ÷ 6[2 + 8]"), parse("60 ÷ 12 + 8"), parse("5 + 8"), Number(13))

VALUE = ValueQuestionData(parse("[45 - (6 + 3)] * 27"), True, 972)
NEXT_STEP = NextStepQuestionData(parse("28 + 7 * (12 - 4)"), True, (parse("28 + 7 * 8"),))
TWO_STEPS = NextStepQuestionData(
    parse("28 + 7 * (12 - 4)"), True, (parse("28 + 7 * 8"), parse("28 + 56")), SHOWN_28
)
STEP_BLANK = StepBlankQuestionData(parse("28 + 7 * (12 - 4)"), True, parse("28 + 56"), (1,), 56)
DOES_NOT = HasValueQuestionData(STAAR_24, 24, False, True, STAAR_24[0])
VALUE_COUNT = ValueCountQuestionData(STAAR_24, 24, True, 3)
FIRST = FirstOperationQuestionData(
    parse("40 ÷ (5 + 3) * 8 + 1"), True, FirstChoice(Pair(5, ADD, 3), Why.IN_PARENTHESES)
)
FIRST_RESULT = FirstResultQuestionData(parse("10 ÷ 5 + 4(72 - 6)"), True, Pair(72, SUBTRACT, 6), 66)
INDICATE = ParenthesesQuestionData(
    parse("10 ÷ 5 + 4(72 - 6)"), True, Order(Pair(72, SUBTRACT, 6), Then(MULTIPLY, 4, False))
)
STATEMENT = ParenthesesQuestionData(parse("3 * (8 + 2) ÷ 2"), True, Timing(Pair(8, ADD, 2), True))
FIND_ERROR = FindErrorQuestionData(
    parse("60 ÷ 6[(1 * 2) + (4 * 2)]"),
    ERROR_STEPS,
    True,
    ErrorChoice(2, (Pair(2, ADD, 8),)),
    sign_before_implied=True,
)


@pytest.mark.parametrize(
    ("data", "expected_written", "expected_choices"),
    [
        (VALUE, "What is the value of this expression?", "What is the value of this expression?"),
        (
            NEXT_STEP,
            "Write the expression after the next step.",
            "Which expression is equivalent to the expression shown?",
        ),
        (
            TWO_STEPS,
            "Circle the two expressions that are equivalent to the expression shown.",
            "Which expressions are equivalent to the expression shown? Select TWO correct answers.",
        ),
        (STEP_BLANK, "What number goes in the box?", "What number goes in the box?"),
        (
            DOES_NOT,
            "Circle the expression that does NOT have a value of 24.",
            "Which expression does NOT have a value of 24?",
        ),
        (
            HasValueQuestionData(STAAR_24, Fraction(41, 4), True, True, STAAR_24[1]),
            "Circle the expression that has a value of 10 1/4.",
            "Which expression has a value of 10 1/4?",
        ),
        (
            VALUE_COUNT,
            "How many of these expressions have a value of 24?",
            "How many of these expressions have a value of 24?",
        ),
        (
            FIRST,
            "Which operation should be performed first when simplifying this expression? "
            "Explain why.",
            "Which operation should be performed first when simplifying this expression?",
        ),
        (
            FIRST_RESULT,
            "What number does the first operation give?",
            "What number does the first operation give?",
        ),
        (
            INDICATE,
            "What do the parentheses tell you to do in this expression?",
            "What do these parentheses indicate in the expression?",
        ),
        (
            STATEMENT,
            "What do the parentheses tell you to do in this expression?",
            "Which statement is true about the parentheses in this expression?",
        ),
        (
            FIND_ERROR,
            "An expression is incorrectly simplified as shown. In which step does the error "
            "first appear? Explain the error.",
            "An expression is incorrectly simplified as shown. In which step does the error "
            "first appear?",
        ),
    ],
)
def test_question(
    data: OrderOfOperationsQuestionData, expected_written: str, expected_choices: str
) -> None:
    """The question, as STAAR words it where it asks it, written and with lettered choices."""
    assert (question(data, choices=False), question(data, choices=True)) == (
        expected_written,
        expected_choices,
    )


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (VALUE, [f"[45 {MINUS} (6 + 3)] {TIMES} 27"]),
        # a group with a group inside, all in parentheses
        (
            ValueQuestionData(parse("[45 - (6 + 3)] * 27"), False, 972),
            [f"(45 {MINUS} (6 + 3)) {TIMES} 27"],
        ),
        (STEP_BLANK, [f"28 + 7 {TIMES} (12 {MINUS} 4) = 28 + {BLANK}"]),
        (
            FIND_ERROR,
            [
                f"Given: 60 ÷ 6[(1 {TIMES} 2) + (4 {TIMES} 2)]",
                "Step 1: 60 ÷ 6[2 + 8]",
                "Step 2: 60 ÷ 12 + 8",
                "Step 3: 5 + 8",
                "Step 4: 13",
            ],
        ),
        # the expressions to choose from aren't shown above them
        (DOES_NOT, []),
    ],
)
def test_shown_lines(data: OrderOfOperationsQuestionData, expected: list[str]) -> None:
    """The lines drawn under the question, written inline."""
    assert [inline(line) for line in shown_lines(data)] == expected


@pytest.mark.parametrize(
    ("data", "choices", "expected"),
    [
        # five to circle two of, when written; lettered, they're the options
        (
            TWO_STEPS,
            False,
            [
                f"35 {TIMES} 8",
                f"28 + 7 {TIMES} 8",
                f"35 {TIMES} 12 {MINUS} 4",
                "28 + 56",
                f"28 + 84 {MINUS} 4",
            ],
        ),
        (TWO_STEPS, True, []),
        (
            DOES_NOT,
            False,
            STAAR_24_TEXT,
        ),
        # four to count, always
        (
            VALUE_COUNT,
            False,
            STAAR_24_TEXT,
        ),
        (VALUE, False, []),
    ],
)
def test_circled(data: OrderOfOperationsQuestionData, choices: bool, expected: list[str]) -> None:
    """The expressions drawn without letters, to circle or count."""
    assert [inline(each) for each in circled(data, choices)] == expected


@pytest.mark.parametrize(
    ("data", "option", "expected"),
    [
        (VALUE, 1134, "1,134"),
        (VALUE, Decimal("8.4"), "8.4"),
        (VALUE, Fraction(41, 4), "10 1/4"),
        # the whole number added to the numerator, written improper, as STAAR writes it
        (VALUE, Improper(Fraction(11, 4)), "11/4"),
        (NEXT_STEP, parse("28 + 84 - 4"), f"28 + 84 {MINUS} 4"),
        # STAAR 2022 Q35's four choices
        (
            FIRST,
            FirstChoice(Pair(5, ADD, 3), Why.IN_PARENTHESES),
            "5 + 3, because the operation in the parentheses should be performed first",
        ),
        (
            FIRST,
            FirstChoice(Pair(40, DIVIDE, 5), Why.LEFT_TO_RIGHT),
            "40 ÷ 5, because it is the first operation when reading left to right",
        ),
        (
            FIRST,
            FirstChoice(Pair(3, MULTIPLY, 8), Why.BEFORE, ADD),
            f"3 {TIMES} 8, because multiplication should be performed before addition",
        ),
        (
            FIRST,
            FirstChoice(Pair(8, ADD, 1), Why.RIGHT_TO_LEFT),
            "8 + 1, because it is the first operation when reading right to left",
        ),
        (
            FIRST,
            FirstChoice(Pair(3, MULTIPLY, 4), Why.MULTIPLYING_FIRST),
            f"3 {TIMES} 4, because multiplication and division should be performed before "
            "addition and subtraction",
        ),
        (
            FIRST,
            FirstChoice(Pair(6, SUBTRACT, 3), Why.IN_BRACKETS),
            f"6 {MINUS} 3, because the operation in the brackets should be performed first",
        ),
        # STAAR 2019 Q8's four choices, "together" left out of the last
        (
            INDICATE,
            Order(Pair(72, SUBTRACT, 6), Then(MULTIPLY, 4, False)),
            "Subtract 6 from 72 before multiplying by 4",
        ),
        (
            INDICATE,
            Order(Pair(10, DIVIDE, 5), Then(ADD, 4, True)),
            "Divide 10 by 5 before adding 4",
        ),
        (
            INDICATE,
            Order(Pair(4, MULTIPLY, 72), Then(SUBTRACT, 6, True)),
            "Multiply 4 by 72 before subtracting 6",
        ),
        (
            INDICATE,
            Order(Pair(5, ADD, 4), Pair(72, SUBTRACT, 6)),
            "Add 5 and 4 before subtracting 6 from 72",
        ),
        # the first result on the right of a subtraction or division
        (
            INDICATE,
            Order(Pair(8, ADD, 2), Then(SUBTRACT, 72, False)),
            "Add 8 and 2 before subtracting the sum from 72",
        ),
        (
            INDICATE,
            Order(Pair(5, ADD, 3), Then(DIVIDE, 40, False)),
            "Add 5 and 3 before dividing 40 by the sum",
        ),
        (
            INDICATE,
            Order(Pair(8, ADD, 2), Then(DIVIDE, 2, True)),
            "Add 8 and 2 before dividing by 2",
        ),
        (
            STATEMENT,
            Timing(Pair(8, ADD, 2), True),
            "The parentheses indicate that 8 + 2 should be solved first.",
        ),
        (
            STATEMENT,
            Timing(Pair(2, DIVIDE, 2), False),
            "The parentheses indicate that 2 ÷ 2 should be solved last.",
        ),
        (
            FIND_ERROR,
            ErrorChoice(2, (Pair(2, ADD, 8),)),
            "Step 2, because 2 + 8 should be simplified first",
        ),
        (
            FIND_ERROR,
            ErrorChoice(1, (Pair(9, SUBTRACT, 5), Pair(3, ADD, 7))),
            f"Step 1, because 9 {MINUS} 5 and 3 + 7 should be simplified first",
        ),
        (
            FIND_ERROR,
            ErrorChoice(3, (Pair(5, ADD, Decimal("1.2")),), Decimal("6.2")),
            "Step 3, because 5 + 1.2 = 6.2",
        ),
    ],
)
def test_option(data: OrderOfOperationsQuestionData, option: Option, expected: str) -> None:
    """A lettered choice as written."""
    assert inline(option_pieces(data, option)) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            VALUE,
            f"972: [45 {MINUS} (6 + 3)] {TIMES} 27 = [45 {MINUS} 9] {TIMES} 27 = 36 {TIMES} 27 "
            "= 972",
        ),
        (
            NextStepQuestionData(
                parse("[27 - (1.1 * 3)] * (5 + 1.2)"),
                True,
                (parse("[27 - 3.3] * (5 + 1.2)"), parse("[27 - 3.3] * 6.2")),
            ),
            f"[27 {MINUS} 3.3] {TIMES} (5 + 1.2), or [27 {MINUS} 3.3] {TIMES} 6.2",
        ),
        (TWO_STEPS, f"28 + 7 {TIMES} 8 and 28 + 56"),
        (STEP_BLANK, f"56: 28 + 7 {TIMES} (12 {MINUS} 4) = 28 + 56"),
        (
            DOES_NOT,
            f"(36 {MINUS} 3) {TIMES} 4. {STAAR_24_VALUES}",
        ),
        (
            VALUE_COUNT,
            f"3: {STAAR_24_VALUES}",
        ),
        (FIRST, "5 + 3, because the operation in the parentheses should be performed first"),
        (FIRST_RESULT, f"66: 72 {MINUS} 6 = 66"),
        (INDICATE, "Subtract 6 from 72 before multiplying by 4"),
        (STATEMENT, "The parentheses indicate that 8 + 2 should be solved first."),
        # the right step after the line before the error, written as the question writes it
        (
            FIND_ERROR,
            "Step 2, because 2 + 8 should be simplified first. Step 2 should be 60 ÷ 6(10).",
        ),
        # an error in the last step: the value
        (
            FindErrorQuestionData(
                parse("(5 + 8) * 2 + 1"),
                (parse("13 * 2 + 1"), Number(16)),
                True,
                ErrorChoice(2, (Pair(13, MULTIPLY, 2),)),
            ),
            f"Step 2, because 13 {TIMES} 2 should be simplified first. Step 2 should be 27.",
        ),
    ],
)
def test_solution(data: OrderOfOperationsQuestionData, expected: str) -> None:
    """The answer key's entry: the answer, with the working that shows it where it helps."""
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (VALUE, "972"),
        (ValueQuestionData(parse("1/4 + (2 * 5)"), True, Fraction(41, 4)), "10 1/4"),
        (STEP_BLANK, "56"),
        (VALUE_COUNT, "3"),
        (ValueCountQuestionData(STAAR_24, 25, True, 0), "0"),
        (FIRST_RESULT, "66"),
    ],
)
def test_tile_answer(data: OrderOfOperationsQuestionData, expected: str) -> None:
    """The answer as the self-check tiles bank shows it."""
    assert tile_answer(data) == expected


def test_a_question_without_a_tiles_form_has_no_tile_answer() -> None:
    """Only a tiles form's answer goes in the bank."""
    with pytest.raises(ValueError, match=r"Only a tiles form's answer is in the bank\."):
        tile_answer(FIRST)
