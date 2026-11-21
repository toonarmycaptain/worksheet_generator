"""
Tests for writing an arithmetic expression, inline and as pieces, and reading one from text.

Most expressions are STAAR's, from 5.4(B), (E) and (F).
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
    Variable,
)
from core.arithmetic_expressions.representation import (
    expression_pieces,
    expression_text,
    parse,
    value_pieces,
)
from core.basic_operations.data import Operation
from core.written_numbers import Pieces
from tests.data import MINUS, TIMES

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
NONE, PARENTHESES, BRACKETS = Grouping


@pytest.mark.parametrize(
    ("value", "money", "pieces"),
    [
        (1368, False, ("1,368",)),
        (50, True, ("50",)),
        # trailing zeros dropped, or two places in money
        (Decimal("2.70"), False, ("2.7",)),
        (Decimal("100.0"), False, ("100",)),
        (Decimal("2.7"), True, ("2.70",)),
        (Decimal("68"), True, ("68.00",)),
        (Decimal("1411"), True, ("1,411.00",)),
        (Decimal("-3.5"), False, (f"{MINUS}3.5",)),
        # a fraction is a mixed number, or proper
        (Fraction(41, 4), False, ("10 ", Fraction(1, 4))),
        (Fraction(1, 4), False, (Fraction(1, 4),)),
    ],
)
def test_value_pieces(value: NumberValue, money: bool, pieces: Pieces) -> None:
    assert value_pieces(value, money) == pieces


def test_value_pieces_errors() -> None:
    """Money is in whole cents."""
    with pytest.raises(ValueError) as error:
        value_pieces(Decimal("3.625"), money=True)
    assert str(error.value) == "3.625 isn't in whole cents."


@pytest.mark.parametrize(
    ("text", "money"),
    [
        # 5.4(E) and (F), with the wrong options' expressions
        (f"28 + 7 {TIMES} (12 {MINUS} 4)", False),
        (f"35 {TIMES} 12 {MINUS} 4", False),
        (f"28 + 84 {MINUS} 4", False),
        (f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2", False),
        (f"2 {TIMES} [30 {MINUS} 20 ÷ (5 {TIMES} 2)]", False),
        (f"(36 {MINUS} 3) {TIMES} 4", False),
        (f"96 ÷ (12 {MINUS} 8)", False),
        (f"36 + 4(120) {MINUS} 6 ÷ 2", False),
        (f"36 + 4(120 {MINUS} 6) ÷ 2", False),
        (f"[36 + 4(120) {MINUS} 6] ÷ 2", False),
        (f"[36 + 4(120 {MINUS} 6)] ÷ 2", False),
        ("3(25 + 19) + 4(3)", False),
        ("10[3 + (7 + 5) ÷ 3]", False),
        ("2(32 + 18) ÷ 4", False),
        (f"(10 {TIMES} 10) ÷ (2 ÷ 2)", False),
        (f"3 {TIMES} 8 {MINUS} 2 + 7", False),
        (f"3(8) {MINUS} 2(7)", False),
        (f"3 {TIMES} 8 {MINUS} (2 + 7)", False),
        (f"[45 {MINUS} (6 + 3)] {TIMES} 27", False),
        (f"[36 + (3 {TIMES} 2)] ÷ 6", False),
        (f"[27 {MINUS} (1.1 {TIMES} 3)] {TIMES} (5 + 1.2)", False),
        (f"[25.9 {TIMES} 3] {TIMES} 6.2", False),
        (f"[27 {MINUS} 3.3] {TIMES} 6", False),
        (f"[127 {MINUS} 8 {TIMES} (14.6 {MINUS} 2.1)] ÷ 3", False),
        (f"6[2 + (1.7 {TIMES} 2.3)] + 39", False),
        (f"12 + (1.7 {TIMES} 2.3) + 39", False),
        (f"6[2 + 1.7] {TIMES} 41.3", False),
        (f"5.75(6 + 5) + 8.50(2 {TIMES} 4)", True),
        (f"(8 {TIMES} 16.95) {MINUS} 7.50", True),
        (f"[2(3.50 {MINUS} 0.80) + 4.85 + 2.40] {MINUS} 3.00", True),
        (f"[2(7.25) + 2(24)] {MINUS} 10", True),
        (f"4[4.5 {MINUS} 2(1.2)]", False),
        (f"1/4 + (2 {TIMES} 5)", False),
        (f"8 {TIMES} (3.8 + 13.2) {MINUS} 6", False),
        (f"40 ÷ (5 + 3) {TIMES} 8 + 1", False),
        (f"10 ÷ 5 + 4(72 {MINUS} 6)", False),
        (f"3 {TIMES} (8 + 2) ÷ 2", False),
        # 5.4(B)'s expressions, a letter for the unknown
        (f"3(p {MINUS} 10)", False),
        (f"3 {TIMES} p {MINUS} 10", False),
        (f"32 {TIMES} b + 30", False),
        (f"m {MINUS} 55 {MINUS} 31", False),
        (f"(18 {TIMES} 4) {MINUS} z", False),
        (f"(18 + 4) {TIMES} z", False),
        ("1,368 ÷ 18 + 1", False),
        ("6(3) + 21(2) + 16", False),
        (f"45 {MINUS} (5 {TIMES} 3) {MINUS} (3 {TIMES} 2) + 17", False),
        (f"90 {TIMES} 36 ÷ 6", False),
        (f"[625 {MINUS} (7 {TIMES} 55)] ÷ 8", False),
        ("(31 + 41)8", False),
        ("144 ÷ (12 ÷ 4)", False),
        (f"(144 ÷ 4) {TIMES} 12", False),
        ("(562,937 + 607,822 + 492,375) + n", False),
        # a letter beside a number, and a mixed number
        ("3p + 1", False),
        (f"10 1/4 {MINUS} 2", False),
    ],
)
def test_written_as_read(text: str, money: bool) -> None:
    """Each expression is written as it was read: STAAR's symbols, signs left out and numbers."""
    assert expression_text(parse(text), money) == text


@pytest.mark.parametrize(
    ("text", "expression"),
    [
        (
            f"28 + 7 {TIMES} (12 {MINUS} 4)",
            Calculation(
                ADD,
                Number(28),
                Calculation(
                    MULTIPLY,
                    Number(7),
                    Calculation(SUBTRACT, Number(12), Number(4), grouping=PARENTHESES),
                ),
            ),
        ),
        # left to right, and a group around a single number dropped
        (
            "20 - 5 + (3)",
            Calculation(ADD, Calculation(SUBTRACT, Number(20), Number(5)), Number(3)),
        ),
        # signs left out
        ("4(3)", Calculation(MULTIPLY, Number(4), Number(3), implied=True)),
        (
            "(31 + 41)8",
            Calculation(
                MULTIPLY,
                Calculation(ADD, Number(31), Number(41), grouping=PARENTHESES),
                Number(8),
                implied=True,
            ),
        ),
        ("3p", Calculation(MULTIPLY, Number(3), Variable("p"), implied=True)),
        # a multiplication without its sign first, as a fraction bar would group it
        (
            "60 ÷ 6[2 + 8]",
            Calculation(
                DIVIDE,
                Number(60),
                Calculation(
                    MULTIPLY,
                    Number(6),
                    Calculation(ADD, Number(2), Number(8), grouping=BRACKETS),
                    implied=True,
                ),
            ),
        ),
        (
            f"[45 {MINUS} (6 + 3)]",
            Calculation(
                SUBTRACT,
                Number(45),
                Calculation(ADD, Number(6), Number(3), grouping=PARENTHESES),
                grouping=BRACKETS,
            ),
        ),
        # numbers: commas, decimals, fractions and mixed numbers; hyphens and * read as signs
        ("1,368 * 3.50", Calculation(MULTIPLY, Number(1368), Number(Decimal("3.50")))),
        (
            f"1/4 {MINUS} 10 1/4",
            Calculation(SUBTRACT, Number(Fraction(1, 4)), Number(Fraction(41, 4))),
        ),
    ],
)
def test_parse(text: str, expression: Expression) -> None:
    assert parse(text) == expression


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("28 +", "'28 +' ends too soon."),
        ("(3 + 4", "'(' isn't closed by ')' in '(3 + 4'."),
        ("[3 + 4)", "'[' isn't closed by ']' in '[3 + 4)'."),
        ("3 $ 4", "Unexpected '$ 4' in '3 $ 4'."),
        ("3 + 4)", "Unexpected ')' in '3 + 4)'."),
        ("+ 3", "Unexpected '+' in '+ 3'."),
    ],
)
def test_parse_errors(text: str, message: str) -> None:
    with pytest.raises(ValueError) as error:
        parse(text)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("text", "pieces"),
    [
        (f"1/4 + (2 {TIMES} 5)", (Fraction(1, 4), f" + (2 {TIMES} 5)")),
        ("10 1/4 ÷ 4", ("10 ", Fraction(1, 4), " ÷ 4")),
    ],
)
def test_expression_pieces(text: str, pieces: Pieces) -> None:
    """A fraction is a piece of its own, drawn stacked."""
    assert expression_pieces(parse(text)) == pieces


@pytest.mark.parametrize(
    ("text", "brackets", "sign_before_implied", "written"),
    [
        # every group in parentheses
        (
            f"8 + [(9 {MINUS} 5) {TIMES} (3 + 7)] {MINUS} 2",
            False,
            False,
            f"8 + ((9 {MINUS} 5) {TIMES} (3 + 7)) {MINUS} 2",
        ),
        (f"4[4.5 {MINUS} 2(1.2)]", False, False, f"4(4.5 {MINUS} 2(1.2))"),
        (f"[27 {MINUS} 3.3] {TIMES} 6", False, False, f"(27 {MINUS} 3.3) {TIMES} 6"),
        (
            f"((2 + 3) {TIMES} 4) {MINUS} 1",
            False,
            False,
            f"((2 + 3) {TIMES} 4) {MINUS} 1",
        ),
        # x or ÷ just before a multiplication without its sign, as STAAR's 2025 Q12
        ("60 ÷ 6[2 + 8]", True, True, "60 ÷ 6[2 + 8]"),
        (
            f"60 ÷ 6[(1 {TIMES} 2) + (4 {TIMES} 2)]",
            False,
            True,
            f"60 ÷ 6((1 {TIMES} 2) + (4 {TIMES} 2))",
        ),
        (f"2 {TIMES} 3(4 + 1)", True, True, f"2 {TIMES} 3(4 + 1)"),
    ],
)
def test_writer_options(text: str, brackets: bool, sign_before_implied: bool, written: str) -> None:
    assert expression_text(parse(text), False, brackets, sign_before_implied) == written


@pytest.mark.parametrize(
    ("expression", "brackets", "message"),
    [
        # read in another order without a group: 20 - 5 + 3, 2 + 3 x 4 as (2 + 3) x 4
        (
            Calculation(SUBTRACT, Number(20), Calculation(ADD, Number(5), Number(3))),
            True,
            "Without a group, part of this calculation would be read in another order.",
        ),
        (
            Calculation(MULTIPLY, Calculation(ADD, Number(2), Number(3)), Number(4)),
            True,
            "Without a group, part of this calculation would be read in another order.",
        ),
        # x or ÷ just before a multiplication without its sign, unless asked for
        (
            parse("60 ÷ 6[2 + 8]"),
            True,
            "A multiplication or division just before a multiplication without its sign is "
            "written only with sign_before_implied.",
        ),
        (
            parse(f"2 {TIMES} 3(4 + 1)"),
            True,
            "A multiplication or division just before a multiplication without its sign is "
            "written only with sign_before_implied.",
        ),
        # (60 ÷ 6)[2 + 8] needs its parentheses
        (
            Calculation(
                MULTIPLY,
                Calculation(DIVIDE, Number(60), Number(6)),
                Calculation(ADD, Number(2), Number(8), grouping=BRACKETS),
                implied=True,
            ),
            True,
            "A multiplication leaves out its sign only beside a number, variable or group.",
        ),
        (
            Calculation(ADD, Number(2), Number(3), implied=True),
            True,
            "Only a multiplication can leave out its sign.",
        ),
        # STAAR's nesting: ( ) inside [ ], two deep at most
        (
            parse(f"((2 + 3) {TIMES} 4) {MINUS} 1"),
            True,
            "Parentheses go inside brackets, and brackets inside nothing.",
        ),
        (
            parse(f"(4(3) + 1) {TIMES} 2"),
            True,
            "Parentheses go inside brackets, and brackets inside nothing.",
        ),
        (
            parse(f"([2 + 3] {TIMES} 4) {MINUS} 1"),
            True,
            "Parentheses go inside brackets, and brackets inside nothing.",
        ),
        (
            parse(f"[([2 + 3] {TIMES} 4) {MINUS} 1] ÷ 3"),
            False,
            "Groups nest at most two deep.",
        ),
    ],
)
def test_expression_errors(expression: Expression, brackets: bool, message: str) -> None:
    with pytest.raises(ValueError) as error:
        expression_pieces(expression, brackets=brackets)
    assert str(error.value) == message
