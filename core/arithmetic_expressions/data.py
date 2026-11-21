"""
An arithmetic expression as a tree: numbers and a variable, combined by the four operations, with
parentheses or brackets around groups.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

from core.basic_operations.data import Operation

# A number's value: an int when whole, a Decimal such as 3.5, or a Fraction such as 1/4
type NumberValue = int | Decimal | Fraction


class Grouping(StrEnum):
    """The symbols written around a group. Values are stable identifiers for the API and storage."""

    NONE = "none"
    PARENTHESES = "parentheses"  # (12 - 4)
    BRACKETS = "brackets"  # [45 - (6 + 3)], around parentheses


# An arithmetic expression: a number, a variable, or a calculation on two expressions
type Expression = Number | Variable | Calculation


@dataclass(frozen=True)
class Number:
    """
    A number: an ``int`` when whole, a ``Decimal`` such as 3.5, or a ``Fraction`` such as 1/4.
    Each type is written its own way: a decimal without trailing zeros, or with two places in
    money, and a fraction as a mixed number.
    """

    value: NumberValue


@dataclass(frozen=True)
class Variable:
    """A letter standing for an unknown number: the p in 3 x p - 10 = 47."""

    name: str


@dataclass(frozen=True)
class Calculation:
    """
    ``operation`` applied to ``left`` and ``right``, in the order they're written: 7 - 3 is
    ``Calculation(SUBTRACT, Number(7), Number(3))``.

    ``grouping`` is the symbols written around it. A group keeps its symbols while its inside is
    worked out, as STAAR's steps do: [27 - (1.1 x 3)] becomes [27 - 3.3], brackets with no
    parentheses left inside them. It loses them once it is a single number.

    ``implied`` writes a multiplication without its sign, beside a group or a variable:
    3(25 + 19), (31 + 41)8, 3p. A number on the right is written in parentheses, as in 4(3),
    unless a group is on its left. It joins its sides as one, so it is worked before a x or ÷
    beside it: 60 ÷ 6[2 + 8] is 60 ÷ (6[2 + 8]).
    """

    operation: Operation
    left: Expression
    right: Expression
    grouping: Grouping = Grouping.NONE
    implied: bool = False
