"""
Working out an arithmetic expression with a common mistake, for wrong answers: the values a
mistake comes to, and the next steps it writes. Each mistake is one that STAAR's most chosen wrong
answers show.

A scope is the whole expression or a group: what's worked together once the groups inside it are
done. Its parts are its numbers, variables and groups, in the order written, with the signs
between them.
"""

from collections.abc import Callable, Iterable
from dataclasses import replace
from enum import StrEnum
from fractions import Fraction
from typing import assert_never

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
)
from core.arithmetic_expressions.evaluation import (
    Path,
    allowed_paths,
    at,
    calculate,
    replaced,
    scope_parts,
    step,
    steps,
    value,
)
from core.arithmetic_expressions.representation import expression_pieces, is_grouped
from core.basic_operations.data import Operation

# A scope's parts: its numbers, variables and groups in the order written, each with its path,
# and the signs between them, each with whether it is left out, as in 3(25 + 19)
type _Parts = tuple[list[tuple[Path, Expression]], list[tuple[Operation, bool]]]


class Mistake(StrEnum):
    """
    A mistake in working out an expression, as STAAR's wrong answers show it. Values are stable
    identifiers for the API and storage.
    """

    # Left to right, ignoring the groups in the whole expression or a group:
    # 3(25 + 19) + 4(3) as 3 x 25 + 19 + 4 x 3 from left to right, 294
    GROUPS_IGNORED_LEFT_TO_RIGHT = "groups_ignored_left_to_right"
    # A group ignored, or all of them, x and ÷ still before + and -:
    # 8 x (3.8 + 13.2) - 6 as 8 x 3.8 + 13.2 - 6, 37.6
    GROUPS_IGNORED = "groups_ignored"
    # Groups kept, but left to right otherwise: 28 + 7 x (12 - 4) as 35 x (12 - 4), 280, and
    # 10[3 + (7 + 5) ÷ 3] as 10[15 ÷ 3], 50
    LEFT_TO_RIGHT = "left_to_right"
    # A number beside a group multiplies only the group's first number:
    # 4[4.5 - 2(1.2)] as 18 - 2(1.2), 15.6
    FIRST_NUMBER_MULTIPLIED = "first_number_multiplied"
    # The last operation left out: [36 + (3 x 2)] ÷ 6 as 42
    LAST_OPERATION_LEFT_OUT = "last_operation_left_out"
    # A number multiplying left out: 5.75(6 + 5) + 8.50(2 x 4) as 5.75(6 + 5) + 8.50(4), 97.25
    FACTOR_LEFT_OUT = "factor_left_out"
    # A sum or difference with a decimal worked on whole parts only: 5 + 1.2 as 6
    DECIMAL_PARTS_LEFT_OUT = "decimal_parts_left_out"
    # A whole number added to a fraction's numerator: 1/4 + 10 as 11/4
    WHOLE_NUMBER_IN_NUMERATOR = "whole_number_in_numerator"


def mistaken_values(expression: Expression, mistake: Mistake) -> tuple[NumberValue, ...]:
    """
    Return the values ``expression``, which has no variable, comes to with ``mistake``, apart
    from its value: each once, in a fixed order. A number multiplied by a group's first number, and
    a slip in a decimal or fraction, may be made at any step of the working; the other mistakes
    are made reading the given expression. Working that divides by 0 gives no value.
    """
    candidates: list[NumberValue | None]
    match mistake:
        case Mistake.GROUPS_IGNORED_LEFT_TO_RIGHT:
            candidates = [
                _groups_ignored_left_to_right_value(expression, scope)
                for scope in _scopes(expression)
                if scope_parts(expression, scope)[1]
            ]
        case Mistake.GROUPS_IGNORED:
            everything = _rebuilt(expression, (), _parts(expression, (), lambda _: True))
            candidates = [
                _value_or_none(ignored)
                for ignored in (everything, *_each_group_ignored(expression))
            ]
        case Mistake.LEFT_TO_RIGHT:
            candidates = [_left_to_right_value(expression)]
        case (
            Mistake.FIRST_NUMBER_MULTIPLIED
            | Mistake.DECIMAL_PARTS_LEFT_OUT
            | Mistake.WHOLE_NUMBER_IN_NUMERATOR
        ):
            candidates = _step_mistake_values(expression, mistake)
        case Mistake.LAST_OPERATION_LEFT_OUT:
            candidates = _last_operation_left_out(expression)
        case Mistake.FACTOR_LEFT_OUT:
            candidates = [_value_or_none(left_out) for left_out in _factors_left_out(expression)]
        case _:
            assert_never(mistake)
    return _distinct(candidates, value(expression))


def mistaken_steps(expression: Expression, mistake: Mistake) -> tuple[Expression, ...]:
    """
    Return the next steps ``expression``, which has no variable, could be written with
    ``mistake``: each once, in a fixed order, only those that can be written and whose value
    isn't the expression's. Ignoring a group drops its symbols and works the next operation.
    Leaving out the last operation isn't a step, so it gives none.
    """
    candidates: list[Expression | None]
    match mistake:
        case Mistake.GROUPS_IGNORED_LEFT_TO_RIGHT:
            candidates = [
                _first_two_combined(expression, scope, lambda _: True)
                for scope in _scopes(expression)
                if scope_parts(expression, scope)[1]
            ]
        case Mistake.GROUPS_IGNORED:
            candidates = [
                step(ignored) if allowed_paths(ignored) else ignored
                for ignored in _each_group_ignored(expression)
            ]
        case Mistake.LEFT_TO_RIGHT:
            candidates = [
                _first_two_combined(expression, scope, lambda _: False)
                for scope in _scopes(expression)
            ]
        case Mistake.FIRST_NUMBER_MULTIPLIED:
            candidates = list(_first_numbers_multiplied(expression))
        case Mistake.DECIMAL_PARTS_LEFT_OUT | Mistake.WHOLE_NUMBER_IN_NUMERATOR:
            candidates = list(_slips(expression, mistake))
        case Mistake.LAST_OPERATION_LEFT_OUT:
            candidates = []
        case Mistake.FACTOR_LEFT_OUT:
            candidates = list(_factors_left_out(expression))
        case _:
            assert_never(mistake)
    right = value(expression)
    found: list[Expression] = []
    for candidate in candidates:
        if (
            candidate is not None
            and candidate not in found
            and _value_or_none(candidate) not in (None, right)
            and _writable(candidate)
        ):
            found.append(candidate)
    return tuple(found)


def _groups_ignored_left_to_right_value(expression: Expression, scope: Path) -> NumberValue | None:
    """
    Return the value of ``expression`` with the scope at ``scope`` worked from left to right,
    ignoring the groups inside it, and the rest worked correctly; ``None`` if it divides by 0.
    """
    operands, signs = _parts(expression, scope, lambda _: True)
    try:
        worked = _left_to_right([value(operand) for _, operand in operands], signs)
        return value(replaced(expression, scope, Number(worked)))
    except ZeroDivisionError:
        return None


def _left_to_right_value(expression: Expression) -> NumberValue | None:
    """
    Return the value of ``expression`` with each group worked before what's around it, but every
    scope from left to right; ``None`` if it divides by 0.
    """
    operands, signs = _parts(expression, (), lambda _: False)
    try:
        values: list[NumberValue] = []
        for _, operand in operands:
            group_value = _left_to_right_value(operand) if is_grouped(operand) else value(operand)
            if group_value is None:
                return None
            values.append(group_value)
        return _left_to_right(values, signs)
    except ZeroDivisionError:
        return None


def _left_to_right(values: list[NumberValue], signs: list[tuple[Operation, bool]]) -> NumberValue:
    """Return ``values`` combined by ``signs`` from left to right, whatever the operations."""
    result = values[0]
    for (operation, _), number in zip(signs, values[1:], strict=True):
        result = calculate(operation, result, number)
    return result


def _first_two_combined(
    expression: Expression, scope: Path, through: Callable[[Path], bool]
) -> Expression | None:
    """
    Return ``expression`` with the first two numbers of the scope at ``scope``, seeing through
    the groups ``through`` picks, combined by the sign between them, whatever its operation;
    ``None`` if there aren't two numbers there or it divides by 0.
    """
    operands, signs = _parts(expression, scope, through)
    if not signs:
        return None
    first, second = operands[0][1], operands[1][1]
    if not isinstance(first, Number) or not isinstance(second, Number):
        return None
    try:
        combined = Number(calculate(signs[0][0], first.value, second.value))
    except ZeroDivisionError:
        return None
    return _rebuilt(expression, scope, ([((), combined), *operands[2:]], signs[1:]))


def _each_group_ignored(expression: Expression) -> list[Expression]:
    """Return ``expression`` with each of its groups in turn written without its symbols."""
    ignored: list[Expression] = []
    for group in _scopes(expression)[1:]:
        parent = next(
            group[:end]
            for end in range(len(group) - 1, -1, -1)
            if _is_scope(expression, group[:end])
        )
        ignored.append(_rebuilt(expression, parent, _parts(expression, parent, group.__eq__)))
    return ignored


def _first_numbers_multiplied(expression: Expression) -> Iterable[Expression]:
    """
    Yield ``expression`` with each number beside a group of additions or subtractions multiplied
    by the group's first number only, the group's symbols dropped: 28 + 7 x (12 - 4) as
    28 + 84 - 4, and [45 - (6 + 3)] x 27 as 1,215 - (6 + 3).
    """
    for scope in _scopes(expression):
        operands, signs = _parts(expression, scope, lambda _: False)
        for index, (operation, _) in enumerate(signs):
            (left_path, left), (right_path, right) = operands[index], operands[index + 1]
            # the two sides of one multiplication, not 60 ÷ 6 and a group after it
            if operation is not Operation.MULTIPLY or left_path[:-1] != right_path[:-1]:
                continue
            if isinstance(left, Number) and _is_sum_group(right):
                number, group_path = left, right_path
            elif _is_sum_group(left) and isinstance(right, Number):
                number, group_path = right, left_path
            else:
                continue
            group_operands, group_signs = _parts(expression, group_path, lambda _: False)
            first = group_operands[0][1]
            if not isinstance(first, Number):
                continue
            product = ((), Number(calculate(Operation.MULTIPLY, number.value, first.value)))
            yield _rebuilt(
                expression,
                scope,
                (
                    [*operands[:index], product, *group_operands[1:], *operands[index + 2 :]],
                    [*signs[:index], *group_signs, *signs[index + 1 :]],
                ),
            )


def _slips(expression: Expression, mistake: Mistake) -> Iterable[Expression]:
    """
    Yield ``expression`` with each operation allowed next worked with ``mistake``, a slip in its
    numbers: the decimal parts left out (5 + 1.2 as 6) or the whole number added to the numerator
    (1/4 + 10 as 11/4), where the slip applies.
    """
    for path in allowed_paths(expression):
        calculation = at(expression, path)
        assert isinstance(calculation, Calculation)
        assert isinstance(calculation.left, Number) and isinstance(calculation.right, Number)
        left, right = calculation.left.value, calculation.right.value
        slipped = _slip(calculation.operation, left, right, mistake)
        if slipped is not None:
            yield replaced(expression, path, Number(slipped))


def _slip(
    operation: Operation, left: NumberValue, right: NumberValue, mistake: Mistake
) -> NumberValue | None:
    """Return ``left`` and ``right`` combined by ``operation`` with ``mistake``, or ``None`` if it
    doesn't apply."""
    fractions = [number for number in (left, right) if isinstance(number, Fraction)]
    match mistake:
        case Mistake.DECIMAL_PARTS_LEFT_OUT:
            if operation not in (Operation.ADD, Operation.SUBTRACT) or fractions:
                return None
            if all(number == int(number) for number in (left, right)):
                return None
            return calculate(operation, int(left), int(right))
        case Mistake.WHOLE_NUMBER_IN_NUMERATOR:
            wholes = [number for number in (left, right) if isinstance(number, int)]
            if operation is not Operation.ADD or len(fractions) != 1 or len(wholes) != 1:
                return None
            fraction = fractions[0]
            if fraction.denominator == 1:
                return None
            return Fraction(fraction.numerator + wholes[0], fraction.denominator)
        case _:
            return None


def _step_mistake_values(expression: Expression, mistake: Mistake) -> list[NumberValue | None]:
    """Return the values of ``expression`` with ``mistake`` made at each step of its working, and
    the rest worked correctly."""
    working = steps(expression)
    candidates: list[NumberValue | None] = []
    for state in (expression, *working[:-1]):
        if mistake is Mistake.FIRST_NUMBER_MULTIPLIED:
            mistaken = list(_first_numbers_multiplied(state))
        else:
            mistaken = list(_slips(state, mistake))
        candidates.extend(_value_or_none(wrong) for wrong in mistaken)
    return candidates


def _last_operation_left_out(expression: Expression) -> list[NumberValue | None]:
    """
    Return the values worked out just before the last operation, the top calculation's, as if
    it were left out: each of its sides that is a calculation. [36 + (3 x 2)] ÷ 6 gives 42.
    """
    if not isinstance(expression, Calculation):
        return []
    return [
        _value_or_none(side)
        for side in (expression.left, expression.right)
        if isinstance(side, Calculation)
    ]


def _factors_left_out(expression: Expression) -> Iterable[Expression]:
    """
    Yield ``expression`` with each number that multiplies left out, the other side of its
    multiplication in its place: 8.50(2 x 4) as 8.50(4), and 2(3.50 - 0.80) as (3.50 - 0.80).
    """
    for scope in _scopes(expression):
        for path in scope_parts(expression, scope)[0]:
            calculation = at(expression, path)
            assert isinstance(calculation, Calculation)
            if calculation.operation is not Operation.MULTIPLY:
                continue
            for number, other in (
                (calculation.left, calculation.right),
                (calculation.right, calculation.left),
            ):
                if not isinstance(number, Number):
                    continue
                kept = other
                if isinstance(other, Calculation) and other.grouping is Grouping.NONE:
                    kept = replace(other, grouping=calculation.grouping)
                yield replaced(expression, path, kept)


def _parts(expression: Expression, scope: Path, through: Callable[[Path], bool]) -> _Parts:
    """
    Return the parts of the scope at ``scope``, seeing through the groups ``through`` picks as
    if their symbols weren't there. A left-out sign beside a group seen through is written:
    3(25 + 19) seen through is 3 x 25 + 19.
    """
    operands: list[tuple[Path, Expression]] = []
    signs: list[tuple[Operation, bool]] = []

    def opened(part: Expression, path: Path) -> bool:
        return is_grouped(part) and through(path)

    def visit(part: Expression, path: Path, top: bool) -> None:
        if isinstance(part, Calculation) and (
            top or part.grouping is Grouping.NONE or through(path)
        ):
            left, right = (*path, 0), (*path, 1)
            visit(part.left, left, False)
            implied = part.implied and not (opened(part.left, left) or opened(part.right, right))
            signs.append((part.operation, implied))
            visit(part.right, right, False)
        else:
            operands.append((path, part))

    visit(at(expression, scope), scope, True)
    return operands, signs


def _rebuilt(expression: Expression, scope: Path, parts: _Parts) -> Expression:
    """
    Return ``expression`` with the scope at ``scope`` replaced by ``parts``, read by the order of
    operations; the scope keeps its symbols unless it is now a single number.
    """
    operands = [operand for _, operand in parts[0]]
    signs = parts[1]
    # multiplications without their signs first, then x and ÷, then + and -
    for joins in (
        lambda _, implied: implied,
        lambda operation, _: operation in (Operation.MULTIPLY, Operation.DIVIDE),
        lambda _, __: True,
    ):
        operands, signs = _joined(operands, signs, joins)
    new = operands[0]
    old = at(expression, scope)
    if isinstance(new, Calculation) and isinstance(old, Calculation):
        new = replace(new, grouping=old.grouping)
    return replaced(expression, scope, new)


def _joined(
    operands: list[Expression],
    signs: list[tuple[Operation, bool]],
    joins: Callable[[Operation, bool], bool],
) -> tuple[list[Expression], list[tuple[Operation, bool]]]:
    """Return ``operands`` with each pair whose sign ``joins`` picks made one calculation, from
    left to right, and the signs left between them."""
    joined = [operands[0]]
    left: list[tuple[Operation, bool]] = []
    for (operation, implied), operand in zip(signs, operands[1:], strict=True):
        if joins(operation, implied):
            joined[-1] = Calculation(operation, joined[-1], operand, implied=implied)
        else:
            left.append((operation, implied))
            joined.append(operand)
    return joined, left


def _scopes(expression: Expression) -> list[Path]:
    """Return the paths of the whole expression and its groups, outer groups first, in the order
    written."""
    paths: list[Path] = [()]

    def visit(part: Expression, path: Path) -> None:
        if isinstance(part, Calculation):
            if path and part.grouping is not Grouping.NONE:
                paths.append(path)
            visit(part.left, (*path, 0))
            visit(part.right, (*path, 1))

    visit(expression, ())
    return paths


def _is_scope(expression: Expression, path: Path) -> bool:
    """Return whether ``path`` tops a scope: the whole expression, or a group."""
    return not path or is_grouped(at(expression, path))


def _is_sum_group(expression: Expression) -> bool:
    """Return whether ``expression`` is a group whose last operation is + or -."""
    return is_grouped(expression) and expression.operation in (Operation.ADD, Operation.SUBTRACT)


def _value_or_none(expression: Expression) -> NumberValue | None:
    """Return ``expression``'s value, or ``None`` if working it out divides by 0."""
    try:
        return value(expression)
    except ZeroDivisionError:
        return None


def _writable(expression: Expression) -> bool:
    """Return whether ``expression`` can be written in some way."""
    try:
        expression_pieces(expression, sign_before_implied=True)
    except ValueError:
        return False
    return True


def _distinct(
    candidates: Iterable[NumberValue | None], right: NumberValue
) -> tuple[NumberValue, ...]:
    """Return ``candidates`` other than ``None`` and ``right``, each once, in order."""
    found: list[NumberValue] = []
    for candidate in candidates:
        if candidate is not None and candidate != right and candidate not in found:
            found.append(candidate)
    return tuple(found)
