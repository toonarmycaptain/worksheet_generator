"""
Tests for working out an arithmetic expression with a common mistake: the values each mistake
comes to and the next steps it writes. The expressions are STAAR's; the comments give the share of
students choosing a wrong answer the mistake reproduces.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from core.arithmetic_expressions.data import NumberValue
from core.arithmetic_expressions.mistakes import Mistake, mistaken_steps, mistaken_values
from core.arithmetic_expressions.representation import expression_text, parse
from tests.data import MINUS, TIMES

(
    GROUPS_IGNORED_LEFT_TO_RIGHT,
    GROUPS_IGNORED,
    LEFT_TO_RIGHT,
    FIRST_NUMBER_MULTIPLIED,
    LAST_OPERATION_LEFT_OUT,
    FACTOR_LEFT_OUT,
    DECIMAL_PARTS_LEFT_OUT,
    WHOLE_NUMBER_IN_NUMERATOR,
) = Mistake
KASSIDY = f"5.75(6 + 5) + 8.50(2 {TIMES} 4)"
NAKITA = f"[2(3.50 {MINUS} 0.80) + 4.85 + 2.40] {MINUS} 3.00"


@pytest.mark.parametrize(
    ("text", "mistake", "values"),
    [
        # the whole expression, then each group with groups inside, from left to right
        ("3(25 + 19) + 4(3)", GROUPS_IGNORED_LEFT_TO_RIGHT, (294,)),  # 8%
        (
            f"2 {TIMES} [30 {MINUS} 20 ÷ (5 {TIMES} 2)]",
            GROUPS_IGNORED_LEFT_TO_RIGHT,
            (16, 8),
        ),  # both chosen most
        (
            f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2",
            GROUPS_IGNORED_LEFT_TO_RIGHT,
            (41, 25),
        ),  # 25 chosen most
        (f"[45 {MINUS} (6 + 3)] {TIMES} 27", GROUPS_IGNORED_LEFT_TO_RIGHT, (1134,)),  # 4%
        ("1,368 ÷ 18 + 1", GROUPS_IGNORED_LEFT_TO_RIGHT, ()),
        # every group, then each one, ignored
        (f"8 {TIMES} (3.8 + 13.2) {MINUS} 6", GROUPS_IGNORED, (Decimal("37.6"),)),  # 14%
        (
            f"2 {TIMES} [30 {MINUS} 20 ÷ (5 {TIMES} 2)]",
            GROUPS_IGNORED,
            (52, 58, 44),
        ),  # 44 chosen most
        (f"[36 + (3 {TIMES} 2)] ÷ 6", GROUPS_IGNORED, (37,)),
        (f"3 {TIMES} 8 {MINUS} (2 + 7)", GROUPS_IGNORED, (29,)),  # 30%
        # groups kept, left to right otherwise
        ("3(25 + 19) + 4(3)", LEFT_TO_RIGHT, (408,)),  # 15%
        ("10[3 + (7 + 5) ÷ 3]", LEFT_TO_RIGHT, (50,)),  # 29%
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", LEFT_TO_RIGHT, (280,)),
        (f"4[4.5 {MINUS} 2(1.2)]", LEFT_TO_RIGHT, (12,)),  # 15%
        # the misreading of a multiplication without its sign
        ("60 ÷ 6[2 + 8]", LEFT_TO_RIGHT, (100,)),
        # at any step of the working
        (f"4[4.5 {MINUS} 2(1.2)]", FIRST_NUMBER_MULTIPLIED, (Decimal("15.6"),)),  # 16%
        ("10[3 + (7 + 5) ÷ 3]", FIRST_NUMBER_MULTIPLIED, (34,)),  # 13%
        (f"[45 {MINUS} (6 + 3)] {TIMES} 27", FIRST_NUMBER_MULTIPLIED, (1206,)),  # 3%
        (f"6[2 + (1.7 {TIMES} 2.3)] + 39", FIRST_NUMBER_MULTIPLIED, (Decimal("54.91"),)),
        # each side of the last operation that is worked out
        (f"[36 + (3 {TIMES} 2)] ÷ 6", LAST_OPERATION_LEFT_OUT, (42,)),
        (NAKITA, LAST_OPERATION_LEFT_OUT, (Decimal("12.65"),)),  # 11%
        ("1,368 ÷ 18 + 1", LAST_OPERATION_LEFT_OUT, (76,)),  # 19%
        ("3(25 + 19) + 4(3)", LAST_OPERATION_LEFT_OUT, (132, 12)),
        # each number that multiplies
        (
            KASSIDY,
            FACTOR_LEFT_OUT,
            (79, Decimal("71.25"), Decimal("97.25"), Decimal("80.25")),  # 97.25 17%
        ),
        (NAKITA, FACTOR_LEFT_OUT, (Decimal("6.95"),)),  # 12%
        # slips at any step of the working
        (
            f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)",
            DECIMAL_PARTS_LEFT_OUT,
            (Decimal("142.2"), Decimal("148.8")),
        ),
        (f"8 {TIMES} (3.8 + 13.2) {MINUS} 6", DECIMAL_PARTS_LEFT_OUT, (122,)),
        ("12 ÷ (0.5 + 0.5)", DECIMAL_PARTS_LEFT_OUT, ()),  # 12 ÷ 0
        (f"1/4 + (2 {TIMES} 5)", WHOLE_NUMBER_IN_NUMERATOR, (Fraction(11, 4),)),  # 12%
    ],
)
def test_mistaken_values(text: str, mistake: Mistake, values: tuple[NumberValue, ...]) -> None:
    assert mistaken_values(parse(text), mistake) == values


@pytest.mark.parametrize(
    ("text", "mistake", "money", "expected"),
    [
        # STAAR's wrong options: 35 x 12 - 4, 6[3.7 x 2.3] + 39 and [25.9 x 3] x 6.2's step
        (
            f"28 + 7 {TIMES} (12 {MINUS} 4)",
            GROUPS_IGNORED_LEFT_TO_RIGHT,
            False,
            (f"35 {TIMES} 12 {MINUS} 4",),
        ),
        (
            f"6[2 + (1.7 {TIMES} 2.3)] + 39",
            GROUPS_IGNORED_LEFT_TO_RIGHT,
            False,
            (f"12 + 1.7 {TIMES} 2.3 + 39", f"6[3.7 {TIMES} 2.3] + 39"),
        ),
        (
            f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)",
            GROUPS_IGNORED_LEFT_TO_RIGHT,
            False,
            (f"25.9 {TIMES} 3 {TIMES} 5 + 1.2", f"[25.9 {TIMES} 3] {TIMES} (5 + 1.2)"),
        ),
        # a group's symbols dropped, then the next operation
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", GROUPS_IGNORED, False, (f"28 + 84 {MINUS} 4",)),
        (
            f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2",
            GROUPS_IGNORED,
            False,
            (f"8 + [9 {MINUS} 5 {TIMES} 10] {MINUS} 2", f"8 + [4 {TIMES} 3 + 7] {MINUS} 2"),
        ),
        # STAAR's 35 x 8, a step before
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", LEFT_TO_RIGHT, False, (f"35 {TIMES} (12 {MINUS} 4)",)),
        (f"4[4.5 {MINUS} 2(1.2)]", LEFT_TO_RIGHT, False, ("4[2.5(1.2)]",)),
        # STAAR's 28 + 84 - 4 and 12 + (1.7 x 2.3) + 39
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", FIRST_NUMBER_MULTIPLIED, False, (f"28 + 84 {MINUS} 4",)),
        (
            f"6[2 + (1.7 {TIMES} 2.3)] + 39",
            FIRST_NUMBER_MULTIPLIED,
            False,
            (f"12 + (1.7 {TIMES} 2.3) + 39",),
        ),
        (
            f"[45 {MINUS} (6 + 3)] {TIMES} 27",
            FIRST_NUMBER_MULTIPLIED,
            False,
            (f"1,215 {MINUS} (6 + 3)",),
        ),
        # STAAR's 2025 Q12 step 2, where the error first appears
        ("60 ÷ 6[2 + 8]", FIRST_NUMBER_MULTIPLIED, False, ("60 ÷ 12 + 8",)),
        (f"[36 + (3 {TIMES} 2)] ÷ 6", LAST_OPERATION_LEFT_OUT, False, ()),
        (
            KASSIDY,
            FACTOR_LEFT_OUT,
            True,
            (
                f"(6 + 5) + 8.50(2 {TIMES} 4)",
                f"5.75(6 + 5) + (2 {TIMES} 4)",
                "5.75(6 + 5) + 8.50(4)",
                "5.75(6 + 5) + 8.50(2)",
            ),
        ),
        (NAKITA, FACTOR_LEFT_OUT, True, (f"[(3.50 {MINUS} 0.80) + 4.85 + 2.40] {MINUS} 3.00",)),
        # STAAR's [27 - 3.3] x 6, a step before; only operations allowed next slip
        (
            f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)",
            DECIMAL_PARTS_LEFT_OUT,
            False,
            (f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} 6",),
        ),
        ("12 ÷ (0.5 + 0.5)", DECIMAL_PARTS_LEFT_OUT, False, ()),  # 12 ÷ 0
        (f"1/4 + (2 {TIMES} 5)", WHOLE_NUMBER_IN_NUMERATOR, False, ()),
        ("1/4 + 10", WHOLE_NUMBER_IN_NUMERATOR, False, ("2 3/4",)),
    ],
)
def test_mistaken_steps(
    text: str, mistake: Mistake, money: bool, expected: tuple[str, ...]
) -> None:
    result = mistaken_steps(parse(text), mistake)
    written = tuple(expression_text(wrong, money) for wrong in result)
    assert written == expected
