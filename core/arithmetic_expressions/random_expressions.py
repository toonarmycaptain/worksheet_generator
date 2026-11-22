"""
Random arithmetic expressions within limits: how many operations, how deeply groups nest as
written, what kind of numbers, how large, and whether a multiplication may leave out its sign.

An expression is drawn in two parts. Its shape comes first: numbers joined by signs, some of them
in groups, with groups inside groups as deep as asked. Then its numbers, from the top down. A
part whose value is fixed by what is around it, such as a divisor and the number it divides, or
a number to subtract from, is given that value; the rest are drawn at random. So every division
comes out as the kind of number asked for, and no value in the working is 0 or below.

The limits are parameters, with no grade's rules built in, so later sheets can widen them. Every
value staying above 0 is the one fixed rule: allowing negatives would also need
``expression_pieces`` to write a negative number in parentheses, as in 5 x (-3).
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from functools import lru_cache
from itertools import pairwise
from math import ceil, floor, isqrt

from core.arithmetic_expressions.data import (
    Calculation,
    Expression,
    Grouping,
    Number,
    NumberValue,
    Variable,
)
from core.arithmetic_expressions.evaluation import Path, calculate
from core.arithmetic_expressions.representation import expression_text, is_grouped
from core.basic_operations.data import Operation

DECIMAL_SHARE = 1 / 3  # the chance each number in a decimal expression isn't whole
HUNDREDTHS_SHARE = 1 / 4  # the chance a number that isn't whole has hundredths, not tenths
DENOMINATORS = (2, 3, 4, 5, 6, 8, 10, 12)  # a fraction's, as grade 5 uses them
PROPER_SHARE = 3 / 4  # the chance a fraction is less than 1, 1/4, rather than mixed, 2 1/4
LARGEST_MIXED_WHOLE = 9  # the largest whole part of a random mixed number
SECOND_GROUP_SHARE = 1 / 2  # the chance of a second group side by side, as in (9 - 5) x (3 + 7)
IMPLIED_BESIDE_GROUP = 1 / 2  # the chance a x beside a group is left out: 3(25 + 19)
IMPLIED_BESIDE_NUMBER = 1 / 5  # the chance a x between two numbers is left out: 4(3)
SHAPE_TRIES = 400  # shapes drawn for an expression before giving up
FILL_TRIES = 6  # ways tried to fill each part with numbers before giving up on it
# parts tried for one shape before giving up on it, so another is drawn: a part that can't be
# filled is tried again at each level above it, so without a limit the tries multiply with depth
FILL_BUDGET = 150
LARGEST_VALUE = 9_999  # no value in the working is larger, by default
_PLACEHOLDER = Number(0)  # a number in a shape, before the numbers are drawn

# A sign between two terms, and whether it's left out, as in 3(25 + 19)
type Sign = tuple[Operation, bool]


class NumberKind(StrEnum):
    """
    The kind of numbers an expression is made of. Values are stable identifiers for the API and
    storage.
    """

    WHOLE = "whole"  # 28 + 7 x (12 - 4)
    DECIMAL = "decimal"  # [27 - (1.1 x 3)] x (5 + 1.2): tenths and hundredths, and whole numbers
    FRACTION = "fraction"  # 1/4 + (2 x 5): one fraction, the other numbers whole


@dataclass(frozen=True)
class ExpressionLimits:
    """
    What a random expression may be.

    ``levels`` is how deeply its groups nest as written, exactly: 0 for 20 - 3 x 4 + 6, 1 for
    28 + 7 x (12 - 4), 2 for [45 - (6 + 3)] x 27. A multiplication written without its sign
    with a number on the right counts, as its number is in parentheses: 4[4.5 - 2(1.2)] is 2.
    ``operations`` is how many operations it may have. No number written in it is larger than
    ``largest_number``, and no value in its working is larger than ``largest_value``. The
    smaller side of each multiplication, and every divisor, is at most ``largest_multiplier``;
    a divisor is always whole, and nothing is multiplied or divided by 1.

    With ``implied``, a multiplication may leave out its sign beside a group or between two
    numbers: 3(25 + 19), 4(3). With ``sign_before_implied`` as well, a x or ÷ may come just
    before one, as in 60 ÷ 6[2 + 8], which is written only for questions whose answers don't
    depend on how it's read (see ``expression_pieces``).
    """

    levels: int
    operations: range
    numbers: NumberKind = NumberKind.WHOLE
    largest_number: int = 50
    largest_multiplier: int = 12
    implied: bool = True
    sign_before_implied: bool = False
    largest_value: int = LARGEST_VALUE


def random_expression(
    limits: ExpressionLimits, target: NumberValue | None = None, tries: int = SHAPE_TRIES
) -> Expression:
    """
    Return an expression drawn within ``limits``, as the module describes, whose value is
    ``target`` if given, from at most ``tries`` shapes.

    Raises ``ValueError`` if no expression within ``limits`` is found, as when ``operations``
    is too few for ``levels`` or ``target`` can't be reached.
    """
    for _ in range(tries):
        filled = fill(random_shape(limits), limits, target)
        if filled is not None and written_levels(filled, limits) == limits.levels:
            return filled
    raise ValueError("No expression fits these limits.")


def random_shape(limits: ExpressionLimits) -> Expression:
    """
    Return the shape of an expression within ``limits``: its groups and signs, its numbers all
    0 until ``fill`` draws them. A group with a group inside it has brackets, as STAAR writes
    them, and the others parentheses.

    Raises ``ValueError`` if ``limits.operations`` is too few for ``limits.levels``: each level
    takes an operation inside a group, and the whole expression one outside.
    """
    least = limits.levels + 1
    counts = [count for count in limits.operations if count >= max(least, 1)]
    if not counts:
        raise ValueError(f"{limits.levels} levels of grouping need {least} operations.")
    terms, signs = _sequence(random.choice(counts), limits.levels, limits.implied)
    return _with_symbols(combine(terms, signs))


def fill(
    shape: Expression, limits: ExpressionLimits, target: NumberValue | None = None
) -> Expression | None:
    """
    Return ``shape`` with numbers drawn within ``limits``, as the module describes, so that its
    value is ``target`` if given; ``None`` if the numbers drawn didn't fit, or none were found
    in ``FILL_BUDGET`` tries at its parts. In a fraction expression, the fraction is a number
    with no division above it, so it's only added to, subtracted from or multiplied by.
    """
    fraction_at = None
    if limits.numbers is NumberKind.FRACTION:
        open_numbers = [path for path, _ in _numbers(shape) if not _divided(shape, path)]
        if not open_numbers:
            return None
        fraction_at = random.choice(open_numbers)
    filled = _Filling(limits, fraction_at).part(shape, (), target)
    if filled is None:
        return None
    expression = filled[0]
    if limits.numbers is NumberKind.DECIMAL and all(
        isinstance(number.value, int) for _, number in _numbers(expression)
    ):
        return None
    return expression


def combine(terms: Sequence[Expression], signs: Sequence[Sign]) -> Expression:
    """
    Return ``terms`` joined by ``signs`` as one expression, in the order of operations: first
    each multiplication whose sign is left out, then x and ÷ from left to right, then + and -.
    """
    joined = [terms[0]]
    rest: list[Operation] = []
    for (operation, implied), term in zip(signs, terms[1:], strict=True):
        if implied:
            joined[-1] = Calculation(Operation.MULTIPLY, joined[-1], term, implied=True)
        else:
            rest.append(operation)
            joined.append(term)
    products = [joined[0]]
    adding: list[Operation] = []
    for operation, term in zip(rest, joined[1:], strict=True):
        if operation in (Operation.MULTIPLY, Operation.DIVIDE):
            products[-1] = Calculation(operation, products[-1], term)
        else:
            adding.append(operation)
            products.append(term)
    expression = products[0]
    for operation, term in zip(adding, products[1:], strict=True):
        expression = Calculation(operation, expression, term)
    return expression


def written_levels(expression: Expression, limits: ExpressionLimits) -> int | None:
    """
    Return how deeply ``expression``'s groups nest as written, or ``None`` if it can't be
    written within ``limits``, as with a x before a multiplication without its sign when
    ``limits.sign_before_implied`` is off.
    """
    try:
        text = expression_text(expression, sign_before_implied=limits.sign_before_implied)
    except ValueError:
        return None
    deepest = depth = 0
    for character in text:
        if character in "([":
            depth += 1
            deepest = max(deepest, depth)
        elif character in ")]":
            depth -= 1
    return deepest


def within(expression: Expression, limits: ExpressionLimits) -> bool:
    """
    Return whether every value in ``expression``'s working fits ``limits``: above 0, at most
    ``largest_value``, of its kind of number (whole, with at most two decimal places, or a
    fraction), each multiplication's smaller side at most ``largest_multiplier`` and neither 1,
    and each divisor whole, from 2 to ``largest_multiplier``. Its numbers may be larger than
    ``largest_number``, as later steps' are.
    """
    match expression:
        case Number():
            return _fits_kind(expression.value, limits) and expression.value > 0
        case Variable():
            return False
        case Calculation():
            if not (within(expression.left, limits) and within(expression.right, limits)):
                return False
            left, right = _value(expression.left), _value(expression.right)
            if not _operands_fit(expression.operation, left, right, limits):
                return False
            result = calculate(expression.operation, left, right)
            return 0 < result <= limits.largest_value and _fits_kind(result, limits)


def numbers_in(expression: Expression) -> list[tuple[Path, Number]]:
    """Return ``expression``'s numbers, each with its path, in the order written."""
    return _numbers(expression)


def with_numbers(shape: Expression, numbers: Sequence[NumberValue]) -> Expression:
    """Return ``shape`` with ``numbers`` in place of its numbers, in the order written."""
    values = iter(numbers)

    def placed(part: Expression) -> Expression:
        if isinstance(part, Number):
            return Number(next(values))
        if isinstance(part, Calculation):
            return replace(part, left=placed(part.left), right=placed(part.right))
        return part

    return placed(shape)


@dataclass
class _Filling:
    """
    Drawing an expression's numbers within ``limits``, any fraction at ``fraction_at``, with
    ``left`` more tries at its parts. Once they're spent, every part fails at once, so each
    retry above it ends without going deeper.
    """

    limits: ExpressionLimits
    fraction_at: Path | None
    left: int = FILL_BUDGET

    def part(
        self, shape: Expression, path: Path, target: NumberValue | None
    ) -> tuple[Expression, NumberValue] | None:
        """
        Return the part of the expression at ``path``, ``shape`` with numbers drawn, and its
        value, ``target`` if given; ``None`` if no numbers that fit were found, or no tries are
        left.
        """
        if self.left == 0:
            return None
        self.left -= 1
        if isinstance(shape, Number):
            number = target if target is not None else self.draw(path, 1, self.most(path))
            if number is None or not self.number_fits(_tidy(number), path):
                return None
            return Number(_tidy(number)), _tidy(number)
        if not isinstance(shape, Calculation):
            return None
        for _ in range(FILL_TRIES):
            sides = self.sides(shape, path, target)
            if sides is None:
                continue
            (left, left_value), (right, right_value) = sides
            if not _operands_fit(shape.operation, left_value, right_value, self.limits):
                continue
            # (31 + 41)8 reads well; [17.12 x 6.25]0.7 doesn't
            if shape.implied and is_grouped(left) and not isinstance(right_value, int):
                continue
            result = calculate(shape.operation, left_value, right_value)
            if (target is None or result == target) and self.value_fits(result, path):
                return replace(shape, left=left, right=right), result
        return None

    def sides(
        self, shape: Calculation, path: Path, target: NumberValue | None
    ) -> tuple[tuple[Expression, NumberValue], tuple[Expression, NumberValue]] | None:
        """
        Return both sides of the calculation ``shape`` at ``path`` filled, so its value is
        ``target`` if given, or ``None`` if a side couldn't be. A side that its operation
        constrains is drawn after the other, from what that other came to.
        """
        left_path, right_path = (*path, 0), (*path, 1)
        left, right = shape.left, shape.right
        match shape.operation:
            case Operation.ADD if target is None:
                return self.both(left, left_path, None, right, right_path, None)
            case Operation.ADD:
                assert target is not None
                fraction_left = self.on_fraction_path(left_path)
                whole_path = right_path if fraction_left else left_path
                part = self.draw(whole_path, 1, min(_below(target), self.most(whole_path)))
                if part is None:
                    return None
                rest = calculate(Operation.SUBTRACT, target, part)
                if fraction_left:
                    return self.both(left, left_path, rest, right, right_path, part)
                return self.both(left, left_path, part, right, right_path, rest)
            case Operation.SUBTRACT if target is None:
                if isinstance(right, Number) or not isinstance(left, Number):
                    first = self.part(left, left_path, None)
                    if first is None:
                        return None
                    taken = self.draw(right_path, 1, min(_below(first[1]), self.most(right_path)))
                    if taken is None:
                        return None
                    second = self.part(right, right_path, taken)
                    return None if second is None else (first, second)
                second = self.part(right, right_path, None)
                if second is None:
                    return None
                room = calculate(Operation.SUBTRACT, self.most(left_path), second[1])
                extra = self.draw(left_path, 1, room)
                if extra is None:
                    return None
                first = self.part(left, left_path, calculate(Operation.ADD, second[1], extra))
                return None if first is None else (first, second)
            case Operation.SUBTRACT:
                assert target is not None
                if isinstance(right, Number):
                    taken = self.draw(right_path, 1, self.most(right_path))
                    second = None if taken is None else self.part(right, right_path, taken)
                else:
                    second = self.part(right, right_path, None)
                if second is None:
                    return None
                first = self.part(left, left_path, calculate(Operation.ADD, target, second[1]))
                return None if first is None else (first, second)
            case Operation.MULTIPLY if target is None:
                small_left = random.random() < 1 / 2
                small_path = left_path if small_left else right_path
                small = self.draw(small_path, 1, self.limits.largest_multiplier)
                if small is None:
                    return None
                if small_left:
                    return self.both(left, left_path, small, right, right_path, None)
                return self.both(left, left_path, None, right, right_path, small)
            case Operation.MULTIPLY:
                assert target is not None
                pairs = self.factor_pairs(target, left_path, right_path)
                if not pairs:
                    return None
                first_factor, second_factor = random.choice(pairs)
                return self.both(left, left_path, first_factor, right, right_path, second_factor)
            case Operation.DIVIDE:
                most_divisor = self.limits.largest_multiplier
                if isinstance(left, Number) and target is not None:
                    most_divisor = min(most_divisor, floor(self.limits.largest_number / target))
                if most_divisor < 2:
                    return None
                divisor = random.randint(2, most_divisor)
                second = self.part(right, right_path, divisor)
                if second is None:
                    return None
                quotient = target
                if quotient is None:
                    most = self.most(left_path)
                    high = Fraction(most, divisor) if isinstance(left, Number) else most
                    quotient = self.draw(left_path, 1, high)
                if quotient is None:
                    return None
                first = self.part(left, left_path, calculate(Operation.MULTIPLY, quotient, divisor))
                return None if first is None else (first, second)
        return None

    def both(
        self,
        left: Expression,
        left_path: Path,
        left_target: NumberValue | None,
        right: Expression,
        right_path: Path,
        right_target: NumberValue | None,
    ) -> tuple[tuple[Expression, NumberValue], tuple[Expression, NumberValue]] | None:
        """Return both sides filled, each to its target if given, or ``None`` if one couldn't be."""
        first = self.part(left, left_path, left_target)
        if first is None:
            return None
        second = self.part(right, right_path, right_target)
        return None if second is None else (first, second)

    def factor_pairs(
        self, target: NumberValue, left_path: Path, right_path: Path
    ) -> list[tuple[NumberValue, NumberValue]]:
        """
        Return the pairs of numbers, left side first, that multiply to ``target`` within the
        limits: neither 1, the smaller at most ``largest_multiplier``, each of its side's kind. A
        fraction's side gets the fraction, and the other a whole number.
        """
        limit = self.limits.largest_multiplier
        if isinstance(target, Fraction):
            fraction_left = self.on_fraction_path(left_path)
            pairs: list[tuple[NumberValue, NumberValue]] = []
            for whole in range(2, limit + 1):
                part = target / whole
                pairs.append((part, whole) if fraction_left else (whole, part))
            return pairs
        decimal = self.limits.numbers is NumberKind.DECIMAL
        return list(_factor_pairs(target, limit, decimal))

    def draw(self, path: Path, low: NumberValue, high: NumberValue) -> NumberValue | None:
        """
        Return a random number from ``low`` to ``high`` for the part at ``path``: a fraction that
        isn't whole, from just above 0, if the fraction is in it; in a decimal expression, tenths
        or hundredths, or a whole number; else whole. ``None`` if there is no such number.
        """
        if self.on_fraction_path(path):
            return _random_fraction(high)
        if self.limits.numbers is NumberKind.DECIMAL and random.random() < DECIMAL_SHARE:
            places = 2 if random.random() < HUNDREDTHS_SHARE else 1
            lowest, highest = max(1, ceil(low * 10**places)), floor(high * 10**places)
            if lowest > highest:
                return None
            # a step that's a multiple of 10 would have fewer places; most steps aren't
            for _ in range(FILL_TRIES * 3):
                step = random.randint(lowest, highest)
                if step % 10:
                    return Decimal(step).scaleb(-places)
            return None
        if ceil(low) > floor(high):
            return None
        return random.randint(ceil(low), floor(high))

    def most(self, path: Path) -> int:
        """Return the largest a random part at ``path`` should be: a number's limit."""
        return self.limits.largest_number

    def on_fraction_path(self, path: Path) -> bool:
        """Return whether the part at ``path`` holds the fraction."""
        return self.fraction_at is not None and self.fraction_at[: len(path)] == path

    def number_fits(self, number: NumberValue, path: Path) -> bool:
        """Return whether ``number`` can be written at ``path``: of its kind, above 0, in range."""
        if not 0 < number <= self.limits.largest_number:
            return False
        if path == self.fraction_at:
            return isinstance(number, Fraction) and number.denominator in DENOMINATORS
        return _fits_kind(number, self.limits) and not isinstance(number, Fraction)

    def value_fits(self, result: NumberValue, path: Path) -> bool:
        """Return whether the value ``result`` of the part at ``path`` fits the limits."""
        if not 0 < result <= self.limits.largest_value:
            return False
        if self.on_fraction_path(path):
            return True
        return _fits_kind(result, self.limits) and not isinstance(result, Fraction)


def _sequence(operations: int, levels: int, implied: bool) -> tuple[list[Expression], list[Sign]]:
    """
    Return the terms and signs of an expression with ``operations`` operations whose groups nest
    ``levels`` deep: numbers, and for ``levels`` above 0, one or two groups among them, one
    nesting ``levels`` - 1 deep inside. A group nesting g deep inside takes g + 1 operations.
    """
    if levels == 0:
        terms: list[Expression] = [_PLACEHOLDER] * (operations + 1)
    else:
        outside = random.randint(1, operations - levels)
        inside = operations - outside
        depths = [levels - 1]
        if inside > levels and random.random() < SECOND_GROUP_SHARE:
            depths.append(random.randint(0, min(levels - 1, inside - levels - 1)))
        counts = [depth + 1 for depth in depths]
        for _ in range(inside - sum(counts)):
            counts[random.randrange(len(counts))] += 1
        terms = [_PLACEHOLDER] * (outside + 1)
        for slot, depth, count in zip(
            random.sample(range(outside + 1), len(depths)), depths, counts, strict=True
        ):
            inner = combine(*_sequence(count, depth, implied))
            if isinstance(inner, Calculation):
                terms[slot] = replace(inner, grouping=Grouping.PARENTHESES)
    signs: list[Sign] = []
    for before, after in pairwise(terms):
        operation = random.choice(list(Operation))
        share = IMPLIED_BESIDE_GROUP if is_grouped(before) or is_grouped(after) else 0.0
        if isinstance(before, Number) and isinstance(after, Number):
            share = IMPLIED_BESIDE_NUMBER
        left_out = implied and operation is Operation.MULTIPLY and random.random() < share
        signs.append((operation, left_out))
    return terms, signs


def _with_symbols(expression: Expression) -> Expression:
    """
    Return ``expression`` with brackets around each group that has parentheses written inside
    it, and parentheses around the rest, as STAAR writes them.
    """
    if not isinstance(expression, Calculation):
        return expression
    marked = replace(
        expression, left=_with_symbols(expression.left), right=_with_symbols(expression.right)
    )
    if marked.grouping is Grouping.NONE:
        return marked
    inside = _has_parentheses(marked.left) or _has_parentheses(marked.right)
    if marked.implied and isinstance(marked.right, Number) and not is_grouped(marked.left):
        inside = True
    return replace(marked, grouping=Grouping.BRACKETS if inside else Grouping.PARENTHESES)


def _has_parentheses(expression: Expression) -> bool:
    """Return whether ``expression`` is written with any grouping symbols: a group, or 4(3)."""
    if not isinstance(expression, Calculation):
        return False
    if is_grouped(expression):
        return True
    if (
        expression.implied
        and isinstance(expression.right, Number)
        and not is_grouped(expression.left)
    ):
        return True
    return _has_parentheses(expression.left) or _has_parentheses(expression.right)


def _numbers(expression: Expression, path: Path = ()) -> list[tuple[Path, Number]]:
    """Return ``expression``'s numbers, each with its path, in the order written."""
    if isinstance(expression, Number):
        return [(path, expression)]
    if isinstance(expression, Calculation):
        return _numbers(expression.left, (*path, 0)) + _numbers(expression.right, (*path, 1))
    return []


def _divided(expression: Expression, path: Path) -> bool:
    """Return whether a division is above the part of ``expression`` at ``path``."""
    part = expression
    for side in path:
        if not isinstance(part, Calculation):
            return False
        if part.operation is Operation.DIVIDE:
            return True
        part = part.right if side else part.left
    return False


def _value(expression: Expression) -> NumberValue:
    """Return the value of a part with no variable, worked out by ``calculate``."""
    if isinstance(expression, Number):
        return expression.value
    if isinstance(expression, Calculation):
        return calculate(expression.operation, _value(expression.left), _value(expression.right))
    raise ValueError("A variable has no value.")


def _operands_fit(
    operation: Operation, left: NumberValue, right: NumberValue, limits: ExpressionLimits
) -> bool:
    """
    Return whether ``operation`` may be worked on ``left`` and ``right`` within ``limits``: a
    multiplication's smaller side at most ``largest_multiplier``, neither side 1, and their
    decimal places two at most between them, as a product to hundredths has (1.7 x 2.3, not
    32.36 x 2.5); a divisor whole, from 2 to ``largest_multiplier``, and no fraction divided.
    """
    if operation is Operation.MULTIPLY:
        places = _places(left) + _places(right)
        return (
            left != 1
            and right != 1
            and min(left, right) <= limits.largest_multiplier
            and places <= 2
        )
    if operation is Operation.DIVIDE:
        whole_divided = not isinstance(left, Fraction) or left.denominator == 1
        return whole_divided and right == int(right) and 2 <= right <= limits.largest_multiplier
    return True


def _fits_kind(number: NumberValue, limits: ExpressionLimits) -> bool:
    """
    Return whether ``number`` is of ``limits``' kind of number: whole for whole numbers; at most
    two decimal places for decimals; terminating or a fraction for fractions.
    """
    match limits.numbers:
        case NumberKind.WHOLE:
            return number == int(number)
        case NumberKind.DECIMAL:
            return (Fraction(number) * 100).denominator == 1
        case NumberKind.FRACTION:
            return True


def _random_fraction(high: NumberValue) -> Fraction | None:
    """
    Return a random fraction that isn't whole, above 0 and at most ``high``, with a denominator
    from ``DENOMINATORS``: less than 1 ``PROPER_SHARE`` of the time, else a mixed number whose
    whole part is at most ``LARGEST_MIXED_WHOLE``. ``None`` if there is none.
    """
    denominator = random.choice(DENOMINATORS)
    most = min(high, LARGEST_MIXED_WHOLE + 1)
    steps = [step for step in range(1, floor(most * denominator) + 1) if step % denominator]
    if not steps:
        return None
    proper = [step for step in steps if step < denominator]
    if proper and random.random() < PROPER_SHARE:
        return Fraction(random.choice(proper), denominator)
    return Fraction(random.choice(steps), denominator)


@lru_cache(maxsize=4096)
def _factor_pairs(
    target: NumberValue, limit: int, decimal: bool
) -> tuple[tuple[NumberValue, NumberValue], ...]:
    """
    Return the pairs of numbers, each order, that multiply to ``target``: neither 1, the
    smaller at most ``limit``, and with ``decimal``, at most two decimal places between them,
    as 1.7 x 2.3 = 3.91 has; else whole. A product with p places is target x 10^p as whole
    numbers, so those are factored, each factor up to its square root.
    """
    found: list[tuple[NumberValue, NumberValue]] = []
    for places in range(3 if decimal else 1):
        total = Fraction(target) * 10**places
        if total.denominator != 1:
            continue
        whole = total.numerator
        for small in range(1, isqrt(whole) + 1):
            if whole % small:
                continue
            for small_places in range(places + 1):
                first = _tidy(Decimal(small).scaleb(-small_places))
                second = _tidy(Decimal(whole // small).scaleb(small_places - places))
                found += [(first, second), (second, first)]
    return tuple(
        (first, second)
        for first, second in dict.fromkeys(found)
        if first != 1
        and second != 1
        and min(first, second) <= limit
        and _places(first) + _places(second) <= 2
    )


def _places(number: NumberValue) -> int:
    """Return how many decimal places ``number`` has: 0 for a whole number or a fraction."""
    if not isinstance(number, Decimal):
        return 0
    exponent = number.normalize().as_tuple().exponent
    return max(0, -exponent) if isinstance(exponent, int) else 0


def _tidy(number: NumberValue) -> NumberValue:
    """Return ``number`` as an int when whole, as a ``Number`` holds it."""
    if isinstance(number, (Decimal, Fraction)) and number == int(number):
        return int(number)
    return number


def _below(number: NumberValue) -> int:
    """Return the largest whole number below ``number``, the most a part of it may be."""
    return ceil(number) - 1
