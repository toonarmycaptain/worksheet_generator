"""
Writing numbers, whole or not, as fractions, decimals or mixed numbers, both inline and as pieces
for a PDF to draw.

A ``Fraction`` among the pieces is drawn as a stacked fraction, which an inline fraction such as
-3/4x can't show unambiguously; a string is drawn as text. Signs are written outside fractions,
with the minus sign rather than a hyphen.
"""

from collections.abc import Iterable
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from typing import assert_never

MINUS = "\N{MINUS SIGN}"


class NumberStyle(StrEnum):
    """
    How a question writes its numbers that aren't whole. Values are stable identifiers for the
    API and storage.
    """

    FRACTION = "fraction"  # 5/2
    DECIMAL = "decimal"  # 2.5, for a number whose decimal terminates
    MIXED_NUMBER = "mixed_number"  # 2 1/2


# A piece of written maths: text, or a positive fraction that isn't whole, drawn stacked
type Piece = str | Fraction
type Pieces = tuple[Piece, ...]


def inline(pieces: Iterable[Piece]) -> str:
    """Return ``pieces`` as one line of text, each fraction written as 3/4."""
    return "".join(
        piece if isinstance(piece, str) else f"{piece.numerator}/{piece.denominator}"
        for piece in pieces
    )


def number_pieces(value: Fraction | int, style: NumberStyle) -> Pieces:
    """
    Return ``value`` written in ``style``, with commas between groups of three digits.

    A whole number is written the same in every style: -12. A number that isn't whole is a
    fraction, proper or improper (-5/2), a decimal (-2.5) or a mixed number (-2 1/2).

    Raises ``ValueError`` for a decimal that doesn't terminate, such as 1/3's.
    """
    value = Fraction(value)
    sign = MINUS if value < 0 else ""
    size = abs(value)
    if size.denominator == 1:
        return (f"{sign}{size.numerator:,}",)
    match style:
        case NumberStyle.FRACTION:
            return merge_pieces((sign, size))
        case NumberStyle.DECIMAL:
            if not terminates(size):
                raise ValueError(f"{value} has no decimal that terminates.")
            return (f"{sign}{Decimal(size.numerator) / Decimal(size.denominator):,}",)
        case NumberStyle.MIXED_NUMBER:
            whole, part = divmod(size, 1)
            return merge_pieces((f"{sign}{whole:,} " if whole else sign, part))
        case _:
            assert_never(style)


def format_number(value: Fraction | int, style: NumberStyle) -> str:
    """Return ``value`` written inline in ``style``, as ``number_pieces`` writes it."""
    return inline(number_pieces(value, style))


def terminates(value: Fraction) -> bool:
    """Return whether ``value``'s decimal terminates: whether its denominator has no factor but
    2 and 5."""
    denominator = value.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    return denominator == 1


def merge_pieces(pieces: Iterable[Piece]) -> Pieces:
    """Join neighbouring strings among ``pieces`` and drop empty ones."""
    merged: list[Piece] = []
    for piece in pieces:
        last = merged[-1] if merged else None
        if isinstance(piece, str) and isinstance(last, str):
            merged[-1] = last + piece
        elif piece != "":
            merged.append(piece)
    return tuple(merged)
