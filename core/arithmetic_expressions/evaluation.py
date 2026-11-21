"""
Working out an arithmetic expression: its value, and its steps one operation at a time in the
order of operations.

The order: inside a group before around it, the innermost group first; then multiplication and
division from left to right, a multiplication written without its sign before a x or ÷ beside it
(60 ÷ 6[10] is 60 ÷ 60); then addition and subtraction from left to right. Groups side by
side, as in (9 - 5) x (3 + 7), can be worked in either order, so each one's next operation is
allowed next. A step works the leftmost allowed operation, or all of them together, as STAAR's
[27 - (1.1 x 3)] x (5 + 1.2) to [27 - 3.3] x 6.2 does.
"""

import operator
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from typing import assert_never

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
    Variable,
)
from core.basic_operations.data import Operation
from core.written_numbers import terminates

# Where a part of an expression is: from the top, 0 for a calculation's left side and 1 for its
# right. The whole expression is at ().
type Path = tuple[int, ...]

_EXACT: dict[Operation, Callable[[Fraction, Fraction], Fraction]] = {
    Operation.ADD: operator.add,
    Operation.SUBTRACT: operator.sub,
    Operation.MULTIPLY: operator.mul,
    Operation.DIVIDE: operator.truediv,
}
_FIRST = (Operation.MULTIPLY, Operation.DIVIDE)  # worked before addition and subtraction


def calculate(operation: Operation, left: NumberValue, right: NumberValue) -> NumberValue:
    """
    Return ``left`` and ``right`` combined by ``operation``, exactly. The result is a ``Fraction``
    if either number is one or its decimal doesn't terminate (10 ÷ 3); otherwise an ``int`` if
    both numbers are ints and it is whole, and a ``Decimal`` if not: 8 x 12.5 is Decimal 100, and
    7 ÷ 2 is Decimal 3.5.

    Raises ``ZeroDivisionError`` for division by 0.
    """
    exact = _EXACT[operation](Fraction(left), Fraction(right))
    if isinstance(left, Fraction) or isinstance(right, Fraction) or not terminates(exact):
        return exact
    if isinstance(left, int) and isinstance(right, int) and exact.denominator == 1:
        return exact.numerator
    return Decimal(exact.numerator) / Decimal(exact.denominator)


def value(expression: Expression, variable_value: NumberValue | None = None) -> NumberValue:
    """
    Return ``expression``'s value, with ``variable_value`` as its variable's, worked out by
    ``calculate``.

    Raises ``ValueError`` for a variable with no value and ``ZeroDivisionError`` for division by 0.
    """
    match expression:
        case Number():
            return expression.value
        case Variable():
            if variable_value is None:
                raise ValueError(f"{expression.name} has no value.")
            return variable_value
        case Calculation():
            return calculate(
                expression.operation,
                value(expression.left, variable_value),
                value(expression.right, variable_value),
            )
        case _:
            assert_never(expression)


def next_operations(expression: Expression) -> tuple[Calculation, ...]:
    """
    Return the operations that may be worked next, in the order written: one for each group
    with no groups inside it, or for the whole expression once it has none. For
    40 ÷ (5 + 3) x 8 + 1 it is 5 + 3; for (9 - 5) x (3 + 7), 9 - 5 and 3 + 7.

    An operation on the variable can't be worked, so it isn't returned, and neither is an
    operation it holds up: 3 x p - 10 has none, and 3 x p + 4 x 5 has 4 x 5.
    """
    return tuple(_calculation_at(expression, path) for path in allowed_paths(expression))


def step(expression: Expression, together: bool = False) -> Expression:
    """
    Return ``expression`` with the first of ``next_operations`` worked out, or all of them when
    ``together``: 28 + 7 x (12 - 4) becomes 28 + 7 x 8. A group that becomes a single number
    loses its symbols, and one that doesn't keeps them.

    Raises ``ValueError`` if no operation can be worked.
    """
    paths = allowed_paths(expression)
    if not paths:
        raise ValueError("No operation in this expression can be worked out.")
    for path in paths if together else paths[:1]:
        expression = worked(expression, path)
    return expression


def steps(expression: Expression, together: bool = False) -> tuple[Expression, ...]:
    """
    Return the expressions after each ``step`` of ``expression``, until a number is left or the
    variable holds up the rest: 28 + 7 x (12 - 4) gives 28 + 7 x 8, 28 + 56, 84.
    """
    result: list[Expression] = []
    while allowed_paths(expression):
        expression = step(expression, together)
        result.append(expression)
    return tuple(result)


def allowed_paths(expression: Expression) -> list[Path]:
    """Return the paths of ``next_operations``, in the order written."""
    allowed: list[Path] = []
    _allow(expression, (), allowed)
    return allowed


def worked(expression: Expression, path: Path) -> Expression:
    """Return ``expression`` with the calculation at ``path``, on two numbers, worked out."""
    calculation = _calculation_at(expression, path)
    if not isinstance(calculation.left, Number) or not isinstance(calculation.right, Number):
        raise ValueError("Only a calculation on two numbers can be worked out.")
    result = calculate(calculation.operation, calculation.left.value, calculation.right.value)
    return replaced(expression, path, Number(result))


def at(expression: Expression, path: Path) -> Expression:
    """Return the part of ``expression`` at ``path``."""
    for side in path:
        if not isinstance(expression, Calculation):
            raise ValueError(f"No part of the expression is at {path}.")
        expression = expression.right if side else expression.left
    return expression


def replaced(expression: Expression, path: Path, new: Expression) -> Expression:
    """Return ``expression`` with ``new`` in place of its part at ``path``."""
    if not path:
        return new
    if not isinstance(expression, Calculation):
        raise ValueError(f"No part of the expression is at {path}.")
    if path[0]:
        return replace(expression, right=replaced(expression.right, path[1:], new))
    return replace(expression, left=replaced(expression.left, path[1:], new))


def scope_parts(expression: Expression, path: Path) -> tuple[list[Path], list[Path]]:
    """
    Return the paths of the calculations in the scope topped at ``path``, the whole expression or
    a group, and of the groups directly inside it, each in the order written. A calculation
    inside one of those groups belongs to that group's scope instead.
    """
    calculations: list[Path] = []
    groups: list[Path] = []

    def visit(part: Expression, part_path: Path, top: bool) -> None:
        if not isinstance(part, Calculation):
            return
        if part.grouping is not Grouping.NONE and not top:
            groups.append(part_path)
            return
        visit(part.left, (*part_path, 0), False)
        calculations.append(part_path)
        visit(part.right, (*part_path, 1), False)

    visit(at(expression, path), path, True)
    return calculations, groups


def _allow(expression: Expression, path: Path, allowed: list[Path]) -> None:
    """
    Add to ``allowed`` the operation allowed next in the scope topped at ``path``: its groups'
    operations while it has groups, else its first multiplication or division on two numbers
    (6[10] in 60 ÷ 6[10], whose ÷ waits for it), else its first addition or subtraction, if that
    is on two numbers.
    """
    calculations, groups = scope_parts(expression, path)
    if groups:
        for group in groups:
            _allow(expression, group, allowed)
        return
    if not calculations:
        return
    multiplying = [
        path for path in calculations if _calculation_at(expression, path).operation in _FIRST
    ]
    for candidate in multiplying or calculations[:1]:
        calculation = _calculation_at(expression, candidate)
        if isinstance(calculation.left, Number) and isinstance(calculation.right, Number):
            allowed.append(candidate)
            return


def _calculation_at(expression: Expression, path: Path) -> Calculation:
    """Return the calculation at ``path`` in ``expression``."""
    part = at(expression, path)
    if not isinstance(part, Calculation):
        raise ValueError(f"No calculation is at {path}.")
    return part
