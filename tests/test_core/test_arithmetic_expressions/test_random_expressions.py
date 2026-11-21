"""
Tests for random arithmetic expressions: joining terms in the order of operations, checking an
expression's working against limits, how deeply its groups nest as written, and the rules every
drawn expression keeps, over many real draws.
"""

from decimal import Decimal
from fractions import Fraction

import pytest

from core.arithmetic_expressions.data import Calculation, Expression, Grouping, Number
from core.arithmetic_expressions.evaluation import value
from core.arithmetic_expressions.random_expressions import (
    ExpressionLimits,
    NumberKind,
    combine,
    numbers_in,
    random_expression,
    random_shape,
    with_numbers,
    within,
    written_levels,
)
from core.arithmetic_expressions.representation import parse
from core.basic_operations.data import Operation

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
WHOLE, DECIMAL, FRACTION = NumberKind
DRAWS = 200  # expressions drawn for each case of the rules


def _group(text: str, grouping: Grouping = Grouping.PARENTHESES) -> Calculation:
    """Return the calculation ``text`` writes, with ``grouping`` around it."""
    calculation = parse(text)
    assert isinstance(calculation, Calculation)
    return Calculation(
        calculation.operation, calculation.left, calculation.right, grouping, calculation.implied
    )


@pytest.mark.parametrize(
    ("terms", "signs", "expected"),
    [
        # x before +
        ([Number(3), Number(4), Number(5)], [(ADD, False), (MULTIPLY, False)], "3 + 4 * 5"),
        # left to right among equals
        ([Number(20), Number(5), Number(3)], [(SUBTRACT, False), (ADD, False)], "20 - 5 + 3"),
        # a sign left out beside a group
        ([Number(3), _group("25 + 19")], [(MULTIPLY, True)], "3(25 + 19)"),
        # and before a ÷ beside it, as a fraction bar joins its sides
        (
            [Number(60), Number(6), _group("2 + 8", Grouping.BRACKETS)],
            [(DIVIDE, False), (MULTIPLY, True)],
            "60 ÷ 6[2 + 8]",
        ),
        # between two numbers, the right one in parentheses
        (
            [_group("25 + 19"), Number(4), Number(3)],
            [(ADD, False), (MULTIPLY, True)],
            "(25 + 19) + 4(3)",
        ),
    ],
)
def test_combine_joins_terms_in_the_order_of_operations(
    terms: list[Expression], signs: list[tuple[Operation, bool]], expected: str
) -> None:
    """The terms and signs make the tree that the expression's text reads as."""
    assert combine(terms, signs) == parse(expected)


@pytest.mark.parametrize(
    ("text", "numbers", "largest_multiplier", "expected"),
    [
        ("28 + 7 * (12 - 4)", WHOLE, 12, True),
        # a quotient that isn't whole, among whole numbers; fine with decimals
        ("7 ÷ 2", WHOLE, 12, False),
        ("7 ÷ 2", DECIMAL, 12, True),
        # a product to hundredths, but not past them
        ("1.7 * 2.3", DECIMAL, 12, True),
        ("32.36 * 2.5", DECIMAL, 12, False),
        # a value below 0 in the working
        ("20 - 25 + 10", WHOLE, 12, False),
        # 0 itself
        ("5 - 5 + 3", WHOLE, 12, False),
        # a divisor past the largest multiplier, or a multiplication by 1
        ("60 ÷ 15", WHOLE, 12, False),
        ("60 ÷ 15", WHOLE, 15, True),
        ("5 * 1", WHOLE, 12, False),
        # both sides of a multiplication past the largest multiplier
        ("36 * 27", WHOLE, 12, False),
        ("36 * 27", WHOLE, 27, True),
        # a fraction added; a fraction divided
        ("1/4 + (2 * 5)", FRACTION, 12, True),
        ("(1/4 + 1) ÷ 2", FRACTION, 12, False),
    ],
)
def test_within_checks_every_value_in_the_working(
    text: str, numbers: NumberKind, largest_multiplier: int, expected: bool
) -> None:
    """Every value in the working is above 0, of its kind, and its operations within limits."""
    limits = ExpressionLimits(1, range(1, 6), numbers, largest_multiplier=largest_multiplier)
    assert within(parse(text), limits) is expected


@pytest.mark.parametrize(
    ("text", "sign_before_implied", "expected"),
    [
        ("20 - 3 * 4 + 6", False, 0),
        ("28 + 7 * (12 - 4)", False, 1),
        ("[45 - (6 + 3)] * 27", False, 2),
        # a number in parentheses counts, as written
        ("4[4.5 - 2(1.2)]", False, 2),
        ("3(25 + 19) + 4(3)", False, 1),
        # a x or ÷ just before a multiplication without its sign, written only on request
        ("60 ÷ 6[2 + 8]", False, None),
        ("60 ÷ 6[2 + 8]", True, 1),
    ],
)
def test_written_levels(text: str, sign_before_implied: bool, expected: int | None) -> None:
    """How deeply groups nest as written, or ``None`` if the expression can't be written."""
    limits = ExpressionLimits(1, range(1, 6), sign_before_implied=sign_before_implied)
    assert written_levels(parse(text), limits) == expected


def test_with_numbers_places_numbers_in_the_order_written() -> None:
    """The numbers go in as ``numbers_in`` lists them."""
    shape = parse("[0 - (0 + 0)] * 0")
    filled = with_numbers(shape, [45, 6, 3, 27])
    assert (filled, [number.value for _, number in numbers_in(filled)]) == (
        parse("[45 - (6 + 3)] * 27"),
        [45, 6, 3, 27],
    )


def test_a_shape_needs_an_operation_per_level_and_one_outside() -> None:
    """Two levels of grouping take three operations, so two aren't enough."""
    with pytest.raises(ValueError, match="2 levels of grouping need 3 operations"):
        random_shape(ExpressionLimits(2, range(2, 3)))


@pytest.mark.parametrize(
    "limits",
    [
        ExpressionLimits(0, range(2, 5)),
        ExpressionLimits(1, range(2, 5)),
        ExpressionLimits(2, range(3, 6)),
        ExpressionLimits(1, range(2, 5), DECIMAL),
        ExpressionLimits(2, range(3, 6), DECIMAL),
        ExpressionLimits(1, range(2, 5), FRACTION),
        ExpressionLimits(1, range(2, 5), WHOLE, largest_number=10, largest_multiplier=2),
        ExpressionLimits(2, range(3, 6), DECIMAL, largest_number=1_000, largest_multiplier=99),
        ExpressionLimits(1, range(2, 5), implied=False),
    ],
)
def test_every_drawn_expression_keeps_its_limits(limits: ExpressionLimits) -> None:
    """
    Every expression's working is within its limits, its groups nest as deep as asked, it has
    as many operations as allowed, and no number written in it is larger than the largest.
    """
    for _ in range(DRAWS):
        expression = random_expression(limits)
        numbers = [number.value for _, number in numbers_in(expression)]
        assert (
            within(expression, limits),
            written_levels(expression, limits),
            len(numbers) - 1 in limits.operations,
            max(numbers) <= limits.largest_number,
        ) == (True, limits.levels, True, True), expression


@pytest.mark.parametrize(
    ("numbers", "expected"),
    [
        # whole numbers only
        (WHOLE, (0, 0)),
        # some decimals, every expression at least one
        (DECIMAL, (0, None)),
        # one fraction in each, never divided
        (FRACTION, (1, 0)),
    ],
)
def test_each_kind_of_number(numbers: NumberKind, expected: tuple[int, int | None]) -> None:
    """
    How many fractions, and decimals that aren't whole, each expression has: a whole-number
    expression none, a decimal one at least one decimal and no fraction, a fraction one exactly
    one fraction and no decimal. ``None`` stands for any number above 0.
    """
    limits = ExpressionLimits(1, range(2, 5), numbers)
    for _ in range(DRAWS):
        expression = random_expression(limits)
        values = [number.value for _, number in numbers_in(expression)]
        fractions = sum(isinstance(each, Fraction) for each in values)
        decimals = sum(isinstance(each, Decimal) for each in values)
        assert (fractions, decimals if expected[1] is not None or not decimals else None) == (
            expected
        ), expression


@pytest.mark.parametrize(
    ("limits", "target"),
    [
        (ExpressionLimits(1, range(2, 4)), 24),
        (ExpressionLimits(1, range(2, 4)), 25),
        (ExpressionLimits(2, range(3, 4)), 37),
        (ExpressionLimits(1, range(2, 4), DECIMAL), Decimal("74.9")),
        (ExpressionLimits(1, range(2, 4), FRACTION), Fraction(41, 4)),
    ],
)
def test_an_expression_drawn_to_a_value_has_it(
    limits: ExpressionLimits, target: Decimal | Fraction | int
) -> None:
    """An expression drawn to a value has that value, within its limits."""
    for _ in range(DRAWS // 10):
        expression = random_expression(limits, target)
        assert (value(expression), within(expression, limits)) == (target, True), expression
