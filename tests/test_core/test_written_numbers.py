"""Tests for writing numbers as fractions, decimals or mixed numbers, inline and as pieces."""

from fractions import Fraction

import pytest

from core.written_numbers import NumberStyle, Pieces, format_number, number_pieces, terminates
from tests.data import MINUS

FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle


@pytest.mark.parametrize(
    ("value", "style", "pieces", "text"),
    [
        # a whole number is the same in every style
        (Fraction(-12), FRACTION, (f"{MINUS}12",), f"{MINUS}12"),
        (Fraction(-12), DECIMAL, (f"{MINUS}12",), f"{MINUS}12"),
        (Fraction(-12), MIXED_NUMBER, (f"{MINUS}12",), f"{MINUS}12"),
        (0, FRACTION, ("0",), "0"),
        (3050, FRACTION, ("3,050",), "3,050"),
        # fractions, the sign outside
        (Fraction(5, 2), FRACTION, (Fraction(5, 2),), "5/2"),
        (Fraction(-5, 2), FRACTION, (MINUS, Fraction(5, 2)), f"{MINUS}5/2"),
        # decimals
        (Fraction(-5, 2), DECIMAL, (f"{MINUS}2.5",), f"{MINUS}2.5"),
        (Fraction(1, 8), DECIMAL, ("0.125",), "0.125"),
        (Fraction(12201, 4), DECIMAL, ("3,050.25",), "3,050.25"),
        # mixed numbers; a proper fraction has no whole part
        (Fraction(-5, 2), MIXED_NUMBER, (f"{MINUS}2 ", Fraction(1, 2)), f"{MINUS}2 1/2"),
        (Fraction(6101, 2), MIXED_NUMBER, ("3,050 ", Fraction(1, 2)), "3,050 1/2"),
        (Fraction(-1, 2), MIXED_NUMBER, (MINUS, Fraction(1, 2)), f"{MINUS}1/2"),
    ],
)
def test_number_pieces(
    value: Fraction | int, style: NumberStyle, pieces: Pieces, text: str
) -> None:
    """Commas group the digits, and the minus sign stays outside a stacked fraction."""
    assert number_pieces(value, style) == pieces
    assert format_number(value, style) == text


def test_number_pieces_errors() -> None:
    """A decimal has to terminate."""
    with pytest.raises(ValueError) as error:
        number_pieces(Fraction(1, 3), DECIMAL)
    assert str(error.value) == "1/3 has no decimal that terminates."


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Fraction(5), True),
        (Fraction(1, 2), True),
        (Fraction(3, 40), True),
        (Fraction(1, 3), False),
        (Fraction(7, 6), False),
    ],
)
def test_terminates(value: Fraction, expected: bool) -> None:
    """A decimal terminates when the denominator has no factor but 2 and 5."""
    assert terminates(value) == expected
