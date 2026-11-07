"""
Detection of regrouping (carrying or borrowing) in written addition and subtraction, and the
choice of which questions a sheet keeps by it.
"""

from collections.abc import Iterator
from enum import StrEnum
from itertools import zip_longest
from typing import assert_never

from core.basic_operations.data import Operation


class Regrouping(StrEnum):
    """
    Which addition and subtraction questions a sheet keeps, by whether they regroup. Values are
    stable identifiers for the API and storage.
    """

    NEVER = "never"  # only questions that don't regroup
    MIXED = "mixed"  # every question, whether it regroups or not
    ALWAYS = "always"  # only questions that regroup


# What each choice is called on the web page
REGROUPING_NAMES = {
    Regrouping.NEVER: "Never",
    Regrouping.MIXED: "Mixed",
    Regrouping.ALWAYS: "Always",
}


def fits_regrouping(regrouping: Regrouping, operation: Operation, first: int, second: int) -> bool:
    """
    Return whether a sheet with ``regrouping`` keeps ``first`` plus or minus ``second``, as
    judged by ``needs_regrouping``. Mixed keeps every question without judging it.
    """
    match regrouping:
        case Regrouping.MIXED:
            return True
        case Regrouping.ALWAYS:
            return needs_regrouping(operation, first, second)
        case Regrouping.NEVER:
            return not needs_regrouping(operation, first, second)
        case _:
            assert_never(regrouping)


def needs_regrouping(operation: Operation, first: int, second: int) -> bool:
    """
    Return whether ``first`` plus or minus ``second`` carries or borrows in any column.

    Addition regroups when the two digits in a column sum to 10 or more; subtraction regroups
    when a column's top digit is smaller than the digit below it. Columns are aligned from the
    ones, with the shorter number padded with zeros.

    Each column can be judged on its own digits: the first column to carry or borrow receives
    nothing from the column before it, and a column whose own digits carry or borrow does so
    regardless of what it receives.

    Both numbers must be non-negative integers, and for subtraction ``first`` must be at least
    ``second``. Only addition and subtraction involve regrouping in this sense; multiplication
    and division raise ``ValueError``.
    """
    match operation:
        case Operation.ADD:
            return any(top + bottom >= 10 for top, bottom in _column_pairs(first, second))
        case Operation.SUBTRACT:
            return any(top < bottom for top, bottom in _column_pairs(first, second))
        case Operation.MULTIPLY | Operation.DIVIDE:
            raise ValueError("Only addition and subtraction can need regrouping.")
        case _:
            assert_never(operation)


def _column_pairs(first: int, second: int) -> Iterator[tuple[int, int]]:
    """Return the two numbers' digits paired by column from the ones, padded with zeros."""
    first_digits = [int(digit) for digit in reversed(str(first))]
    second_digits = [int(digit) for digit in reversed(str(second))]
    return zip_longest(first_digits, second_digits, fillvalue=0)
