"""
Tests for regrouping: a carry in addition or a borrow in subtraction, in any column, and which
questions a sheet keeps by it.
"""

import pytest

from core.basic_operations.data import Operation
from core.basic_operations.regrouping import Regrouping, fits_regrouping, needs_regrouping


@pytest.mark.parametrize(
    ("operation", "first", "second", "expected"),
    [
        # addition: some column adds to 10 or more
        (Operation.ADD, 3, 4, False),
        (Operation.ADD, 4, 5, False),  # 9 is the most a column can hold
        (Operation.ADD, 5, 5, True),
        (Operation.ADD, 9, 1, True),
        (Operation.ADD, 0, 0, False),
        (Operation.ADD, 99, 0, False),
        (Operation.ADD, 18, 1, False),
        (Operation.ADD, 45, 32, False),
        (Operation.ADD, 45, 37, True),  # the ones carry
        (Operation.ADD, 52, 71, True),  # only the tens carry
        (Operation.ADD, 90, 10, True),  # tens 9 + 1, ones 0 + 0
        (Operation.ADD, 345, 278, True),
        (Operation.ADD, 404, 303, False),
        (Operation.ADD, 500, 500, True),  # only the hundreds carry, into the thousands
        # numbers of different lengths: the shorter one has zeros in the columns it lacks
        (Operation.ADD, 5, 123, False),
        (Operation.ADD, 95, 123, True),  # the tens 9 + 2
        # larger numbers
        (Operation.ADD, 12345, 54321, False),  # every column adds to 6
        (Operation.ADD, 35043, 21589, True),
        # subtraction: some column's top digit is smaller than the one under it
        (Operation.SUBTRACT, 7, 3, False),
        (Operation.SUBTRACT, 5, 5, False),
        (Operation.SUBTRACT, 9, 0, False),
        (Operation.SUBTRACT, 10, 1, True),  # 0 - 1 in the ones borrows
        (Operation.SUBTRACT, 52, 31, False),
        (Operation.SUBTRACT, 52, 38, True),  # the ones borrow
        (Operation.SUBTRACT, 60, 20, False),
        (Operation.SUBTRACT, 60, 25, True),
        (Operation.SUBTRACT, 450, 160, True),  # only the tens borrow
        (Operation.SUBTRACT, 452, 130, False),
        (Operation.SUBTRACT, 372, 150, False),
        (Operation.SUBTRACT, 340, 125, True),
        (Operation.SUBTRACT, 305, 198, True),
        (Operation.SUBTRACT, 500, 499, True),
        # only the hundreds borrow, from the thousands
        (Operation.SUBTRACT, 1500, 800, True),
        (Operation.SUBTRACT, 100, 0, False),
        (Operation.SUBTRACT, 1000, 1, True),
        (Operation.SUBTRACT, 1234, 1234, False),
        # larger numbers
        (Operation.SUBTRACT, 98765, 12345, False),  # every column's top digit is the larger
        (Operation.SUBTRACT, 54321, 12345, True),
        (Operation.SUBTRACT, 35043, 21589, True),
    ],
)
def test_regrouping_is_a_carry_or_a_borrow_in_any_column(
    operation: Operation, first: int, second: int, expected: bool
) -> None:
    """
    Addition regroups when a column sums to 10 or more; subtraction when a top digit is smaller.

    The rows include near misses (a column of 9, equal digits), a single regrouping column in
    the ones, tens or hundreds, and numbers of different lengths.
    """
    assert needs_regrouping(operation, first, second) == expected


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (Operation.MULTIPLY, "Only addition and subtraction can need regrouping."),
        (Operation.DIVIDE, "Only addition and subtraction can need regrouping."),
    ],
)
def test_regrouping_errors(operation: Operation, message: str) -> None:
    """Multiplication and division raise ``ValueError`` rather than returning False."""
    with pytest.raises(ValueError) as error:
        needs_regrouping(operation, 6, 7)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("regrouping", "operation", "first", "second", "expected"),
    [
        # mixed keeps everything, whether it regroups or not, without judging it
        (Regrouping.MIXED, Operation.ADD, 45, 37, True),
        (Regrouping.MIXED, Operation.ADD, 45, 32, True),
        (Regrouping.MIXED, Operation.SUBTRACT, 52, 38, True),
        (Regrouping.MIXED, Operation.SUBTRACT, 52, 31, True),
        (Regrouping.MIXED, Operation.MULTIPLY, 6, 7, True),
        # always keeps only what regroups
        (Regrouping.ALWAYS, Operation.ADD, 45, 37, True),
        (Regrouping.ALWAYS, Operation.ADD, 45, 32, False),
        (Regrouping.ALWAYS, Operation.SUBTRACT, 52, 38, True),
        (Regrouping.ALWAYS, Operation.SUBTRACT, 52, 31, False),
        # never keeps only what doesn't
        (Regrouping.NEVER, Operation.ADD, 45, 37, False),
        (Regrouping.NEVER, Operation.ADD, 45, 32, True),
        (Regrouping.NEVER, Operation.SUBTRACT, 52, 38, False),
        (Regrouping.NEVER, Operation.SUBTRACT, 52, 31, True),
    ],
)
def test_fits_regrouping(
    regrouping: Regrouping, operation: Operation, first: int, second: int, expected: bool
) -> None:
    """A sheet keeps what regroups, what doesn't, or everything, as ``regrouping`` says."""
    assert fits_regrouping(regrouping, operation, first, second) == expected


@pytest.mark.parametrize(
    ("regrouping", "operation", "message"),
    [
        (
            Regrouping.ALWAYS,
            Operation.MULTIPLY,
            "Only addition and subtraction can need regrouping.",
        ),
        (Regrouping.NEVER, Operation.DIVIDE, "Only addition and subtraction can need regrouping."),
    ],
)
def test_fits_regrouping_errors(regrouping: Regrouping, operation: Operation, message: str) -> None:
    """Always and never judge the question, so multiplication and division raise ``ValueError``."""
    with pytest.raises(ValueError) as error:
        fits_regrouping(regrouping, operation, 6, 7)
    assert str(error.value) == message
