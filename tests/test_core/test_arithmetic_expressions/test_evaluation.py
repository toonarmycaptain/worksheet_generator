"""
Tests for working out an arithmetic expression: its value, the operations allowed next, and its
steps one operation at a time. Most expressions and values are STAAR's.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from core.arithmetic_expressions.data import Number, NumberValue
from core.arithmetic_expressions.evaluation import (
    calculate,
    next_operations,
    step,
    steps,
    value,
)
from core.arithmetic_expressions.representation import expression_text, parse
from core.basic_operations.data import Operation
from tests.data import MINUS, TIMES

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation


@pytest.mark.parametrize(
    ("operation", "left", "right", "expected"),
    [
        (ADD, 3, 4, 7),
        (DIVIDE, 1368, 18, 76),
        # a decimal when the quotient of whole numbers isn't whole, a fraction if it doesn't end
        (DIVIDE, 7, 2, Decimal("3.5")),
        (DIVIDE, 10, 3, Fraction(10, 3)),
        # a decimal from a decimal, even when whole
        (MULTIPLY, 8, Decimal("12.5"), Decimal(100)),
        (SUBTRACT, Decimal("3.50"), Decimal("0.80"), Decimal("2.7")),
        # a fraction from a fraction
        (ADD, Fraction(1, 4), 10, Fraction(41, 4)),
        (MULTIPLY, Fraction(1, 4), 4, Fraction(1)),
    ],
)
def test_calculate(
    operation: Operation, left: NumberValue, right: NumberValue, expected: NumberValue
) -> None:
    """Exactly, as an int, Decimal or Fraction."""
    result = calculate(operation, left, right)
    assert (result, type(result)) == (expected, type(expected))


@pytest.mark.parametrize(
    ("text", "variable_value", "expected"),
    [
        # STAAR's answers
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", None, 84),
        (f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2", None, 46),
        (f"2 {TIMES} [30 {MINUS} 20 ÷ (5 {TIMES} 2)]", None, 56),
        (f"(36 {MINUS} 3) {TIMES} 4", None, 132),
        (f"[36 + 4(120 {MINUS} 6)] ÷ 2", None, 246),
        ("3(25 + 19) + 4(3)", None, 144),
        ("10[3 + (7 + 5) ÷ 3]", None, 70),
        ("2(32 + 18) ÷ 4", None, 25),
        (f"3 {TIMES} 8 {MINUS} (2 + 7)", None, 15),
        (f"[45 {MINUS} (6 + 3)] {TIMES} 27", None, 972),
        (f"[36 + (3 {TIMES} 2)] ÷ 6", None, 7),
        (f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)", None, Decimal("146.94")),
        (f"[127 {MINUS} 8 {TIMES} (14.6 {MINUS} 2.1)] ÷ 3", None, 9),
        (f"6[2 + (1.7 {TIMES} 2.3)] + 39", None, Decimal("74.46")),
        (f"5.75(6 + 5) + 8.50(2 {TIMES} 4)", None, Decimal("131.25")),
        (f"(8 {TIMES} 16.95) {MINUS} 7.50", None, Decimal("128.10")),
        (f"[2(3.50 {MINUS} 0.80) + 4.85 + 2.40] {MINUS} 3.00", None, Decimal("9.65")),
        (f"4[4.5 {MINUS} 2(1.2)]", None, Decimal("8.4")),
        (f"1/4 + (2 {TIMES} 5)", None, Fraction(41, 4)),
        (f"8 {TIMES} (3.8 + 13.2) {MINUS} 6", None, 130),
        (f"[2(7.25) + 2(24)] {MINUS} 10", None, Decimal("52.5")),
        (f"40 ÷ (5 + 3) {TIMES} 8 + 1", None, 41),
        ("1,368 ÷ 18 + 1", None, 77),
        ("6(3) + 21(2) + 16", None, 76),
        ("(31 + 41)8", None, 576),
        (f"[625 {MINUS} (7 {TIMES} 55)] ÷ 8", None, 30),
        # a multiplication without its sign first: 60 ÷ 60, and 2 x 15
        (f"60 ÷ 6[(1 {TIMES} 2) + (4 {TIMES} 2)]", None, 1),
        (f"2 {TIMES} 3(4 + 1)", None, 30),
        # a variable's value given: Michela's shirts at $19
        (f"3 {TIMES} p {MINUS} 10", 19, 47),
        (f"3(p {MINUS} 10)", 19, 27),
    ],
)
def test_value(text: str, variable_value: NumberValue | None, expected: NumberValue) -> None:
    assert value(parse(text), variable_value) == expected


def test_value_errors() -> None:
    """A variable needs a value."""
    with pytest.raises(ValueError) as error:
        value(parse(f"3 {TIMES} p {MINUS} 10"))
    assert str(error.value) == "p has no value."


@pytest.mark.parametrize(
    ("text", "operations"),
    [
        # groups first, innermost first, side-by-side groups both allowed
        (f"40 ÷ (5 + 3) {TIMES} 8 + 1", ("(5 + 3)",)),
        (f"3 {TIMES} 4 + (2 + 5)", ("(2 + 5)",)),
        (f"(9 {MINUS} 5) {TIMES} (3 + 7)", (f"(9 {MINUS} 5)", "(3 + 7)")),
        (f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)", (f"(1.1 {TIMES} 3)", "(5 + 1.2)")),
        # then x and ÷ from left to right, then + and - from left to right
        (f"2 + 3 {TIMES} 4", (f"3 {TIMES} 4",)),
        (f"12 ÷ 4 {TIMES} 3", ("12 ÷ 4",)),
        (f"20 {MINUS} 5 + 3", (f"20 {MINUS} 5",)),
        ("10 ÷ 5 + 4(66)", ("10 ÷ 5",)),
        # a multiplication without its sign before the x or ÷ waiting for it
        ("60 ÷ 6(10)", ("6(10)",)),
        (f"2 {TIMES} 3(5)", ("3(5)",)),
        # nothing on the variable, nor held up by it
        (f"3 {TIMES} p {MINUS} 10", ()),
        (f"3 {TIMES} p + 4 {TIMES} 5", (f"4 {TIMES} 5",)),
        ("(31 + 41)p", ("(31 + 41)",)),
        ("17", ()),
    ],
)
def test_next_operations(text: str, operations: tuple[str, ...]) -> None:
    result = tuple(expression_text(operation) for operation in next_operations(parse(text)))
    assert result == operations


@pytest.mark.parametrize(
    ("text", "together", "money", "expected"),
    [
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", False, False, (f"28 + 7 {TIMES} 8", "28 + 56", "84")),
        # brackets kept until a single number is left, and a leftmost group first
        (
            f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2",
            False,
            False,
            (
                f"8 + [4 {TIMES} (3 + 7)] {MINUS} 2",
                f"8 + [4 {TIMES} 10] {MINUS} 2",
                f"8 + 40 {MINUS} 2",
                f"48 {MINUS} 2",
                "46",
            ),
        ),
        # side-by-side groups together, as STAAR's [27 - 3.3] x 6.2
        (
            f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)",
            True,
            False,
            (f"[27 {MINUS} 3.3] {TIMES} 6.2", f"23.7 {TIMES} 6.2", "146.94"),
        ),
        (
            f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)",
            False,
            False,
            (
                f"[27 {MINUS} 3.3] {TIMES} (5 + 1.2)",
                f"23.7 {TIMES} (5 + 1.2)",
                f"23.7 {TIMES} 6.2",
                "146.94",
            ),
        ),
        # a number beside a group keeps its parentheses, 10(7) and 72(8)
        ("10[3 + (7 + 5) ÷ 3]", False, False, ("10[3 + 12 ÷ 3]", "10[3 + 4]", "10(7)", "70")),
        ("(31 + 41)8", False, False, ("72(8)", "576")),
        # STAAR's 2025 Q12, worked: 6[10] before the ÷ waiting for it
        (
            f"60 ÷ 6[(1 {TIMES} 2) + (4 {TIMES} 2)]",
            True,
            False,
            ("60 ÷ 6[2 + 8]", "60 ÷ 6(10)", "60 ÷ 60", "1"),
        ),
        # decimals drop their trailing zeros, or have two places in money
        (
            f"8 {TIMES} (3.8 + 13.2) {MINUS} 6",
            False,
            False,
            (f"8 {TIMES} 17 {MINUS} 6", f"136 {MINUS} 6", "130"),
        ),
        (
            f"5.75(6 + 5) + 8.50(2 {TIMES} 4)",
            True,
            True,
            ("5.75(11) + 8.50(8)", "63.25 + 8.50(8)", "63.25 + 68.00", "131.25"),
        ),
        (f"1/4 + (2 {TIMES} 5)", False, False, ("1/4 + 10", "10 1/4")),
        # the variable holds up the rest
        ("(31 + 41)p", False, False, ("72p",)),
        (f"3 {TIMES} p {MINUS} 10", False, False, ()),
    ],
)
def test_steps(text: str, together: bool, money: bool, expected: tuple[str, ...]) -> None:
    working = steps(parse(text), together)
    result = tuple(expression_text(state, money, sign_before_implied=True) for state in working)
    assert result == expected


def test_step_errors() -> None:
    """A step needs an operation to work."""
    with pytest.raises(ValueError) as error:
        step(Number(17))
    assert str(error.value) == "No operation in this expression can be worked out."
