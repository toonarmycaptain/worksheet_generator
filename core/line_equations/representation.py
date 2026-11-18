"""
Writing a line's numbers, points and equations, both inline and as pieces for a PDF to draw, and
what a question about a line asks: a feature of the line, or its equation in a form.

A ``Fraction`` among the pieces is drawn as a stacked fraction, which an inline fraction such as
-3/4x can't show unambiguously; a string is drawn as text. Signs are written outside fractions,
with the minus sign rather than a hyphen, and a coefficient of 1 is left out: y = x - 2, not
y = 1x + -2.
"""

from collections.abc import Iterable
from decimal import Decimal
from fractions import Fraction
from typing import assert_never

from core.line_equations.data import (
    X_AXIS,
    Y_AXIS,
    Equation,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    NumberStyle,
    Relation,
    answer_of,
)

MINUS = "\N{MINUS SIGN}"
UNDEFINED = "undefined"  # a vertical line's slope
_ONE = "\N{SUBSCRIPT ONE}"

SLOPE_AND_INTERCEPTS_NAME = "Slope and Intercepts"
WRITING_LINEAR_EQUATIONS_NAME = "Writing Linear Equations"

# What each choice is called on the web page; a form shows what it looks like
FORM_NAMES = {
    LineForm.SLOPE_INTERCEPT: "Slope-intercept form (y = mx + b)",
    LineForm.STANDARD: "Standard form (Ax + By = C)",
    LineForm.POINT_SLOPE: f"Point-slope form (y {MINUS} y{_ONE} = m(x {MINUS} x{_ONE}))",
    LineForm.POINT_AND_SLOPE: "A point and the slope",
    LineForm.TWO_POINTS: "Two points",
    LineForm.VERTICAL: "Vertical lines (x = a)",
    LineForm.HORIZONTAL: "Horizontal lines (y = b)",
}
FEATURE_NAMES = {
    LineFeature.SLOPE: "Slope",
    LineFeature.RATE_OF_CHANGE: "Rate of change",
    LineFeature.Y_INTERCEPT: "y-intercept",
    LineFeature.X_INTERCEPT: "x-intercept",
    LineFeature.ZERO: "Zero",
    LineFeature.SLOPE_AND_Y_INTERCEPT: "Slope and y-intercept",
}
# What each thing an equation is written from is called on the web page: a form, as above, or a
# relation
EQUATION_GIVEN_NAMES: dict[LineForm | Relation, str] = {
    **{form: FORM_NAMES[form] for form in LineForm if form in FORM_NAMES},
    Relation.PARALLEL: "A point and a parallel line",
    Relation.PERPENDICULAR: "A point and a perpendicular line",
}
NUMBER_STYLE_NAMES = {
    NumberStyle.FRACTION: "Fractions (5/2)",
    NumberStyle.DECIMAL: "Decimals (2.5)",
    NumberStyle.MIXED_NUMBER: "Mixed numbers (2 1/2)",
}

# What each feature is called in a question
_FEATURE_WORDS = {
    LineFeature.SLOPE: "slope",
    LineFeature.RATE_OF_CHANGE: "rate of change",
    LineFeature.Y_INTERCEPT: "y-intercept",
    LineFeature.X_INTERCEPT: "x-intercept",
    LineFeature.ZERO: "zero",
    LineFeature.SLOPE_AND_Y_INTERCEPT: "slope and y-intercept",
}

# What each form is called in a question that asks for an equation in it
_FORM_WORDS = {
    LineForm.SLOPE_INTERCEPT: "slope-intercept form",
    LineForm.STANDARD: "standard form",
    LineForm.POINT_SLOPE: "point-slope form",
}

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
            return _merge((sign, size))
        case NumberStyle.DECIMAL:
            if not terminates(size):
                raise ValueError(f"{value} has no decimal that terminates.")
            return (f"{sign}{Decimal(size.numerator) / Decimal(size.denominator):,}",)
        case NumberStyle.MIXED_NUMBER:
            whole, part = divmod(size, 1)
            return _merge((f"{sign}{whole:,} " if whole else sign, part))
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


def point_pieces(point: tuple[Fraction | int, Fraction | int], style: NumberStyle) -> Pieces:
    """Return ``point`` as an ordered pair, such as (5/2, 0), its numbers written in ``style``."""
    x, y = point
    return _merge(("(", *number_pieces(x, style), ", ", *number_pieces(y, style), ")"))


def equation_pieces(
    line: Line,
    form: LineForm,
    *,
    numbers: NumberStyle = NumberStyle.FRACTION,
    function: str | None = None,
    point: tuple[int, int] | None = None,
    solved_for_y: bool = False,
) -> Pieces:
    """
    Return the equation of ``line`` in ``form``, its numbers written in ``numbers``:

    - slope-intercept: y = -3/4x + 2, or with ``function`` "f", f(x) = -3/4x + 2;
    - standard: 3x + 4y = 8, in whole numbers;
    - point-slope through ``point`` (-4, 5): y - 5 = -3/4(x + 4), or with ``solved_for_y``,
      y = -3/4(x + 4) + 5;
    - vertical: x = -4;
    - horizontal: y = 2.5, or f(x) = 2.5.

    A term whose number is 0 is left out, so a line through the origin is y = 3x, and a point
    on an axis gives y = 2(x - 3) in point-slope form. With a slope of 1, point-slope form has
    no brackets, y - 3 = x - 1, except solved for y: y = (x - 1) + 3.

    Raises ``ValueError`` for a form that isn't an equation (a point and slope, two points), for
    a vertical line in slope-intercept or point-slope form, for point-slope form without
    ``point``, and for a line that isn't vertical or horizontal in that form.
    """
    lhs = f"{function}(x)" if function else "y"
    match form:
        case LineForm.POINT_AND_SLOPE | LineForm.TWO_POINTS:
            raise ValueError(f"A line given by {form} isn't an equation.")
        case LineForm.SLOPE_INTERCEPT:
            slope, intercept = _slope_and_intercept(line, form)
            if slope == 0:
                return _merge((f"{lhs} = ", *number_pieces(intercept, numbers)))
            return _merge(
                (f"{lhs} = ", *_coefficient(slope, numbers), "x", *_added(intercept, numbers))
            )
        case LineForm.STANDARD:
            return _standard(line)
        case LineForm.POINT_SLOPE:
            slope, _ = _slope_and_intercept(line, form)
            if point is None:
                raise ValueError("Point-slope form needs a point.")
            x, y = point
            if solved_for_y:
                inner: Pieces = ("(x", *_added(-x, numbers), ")") if x else ("x",)
                right_side = (*_coefficient(slope, numbers), *inner, *_added(y, numbers))
                return _merge((f"{lhs} = ", *right_side))
            left = (lhs, *_added(-y, numbers))
            if x == 0 or slope == 1:
                right: Pieces = ("x", *_added(-x, numbers))
            else:
                right = ("(x", *_added(-x, numbers), ")")
            return _merge((*left, " = ", *_coefficient(slope, numbers), *right))
        case LineForm.VERTICAL:
            if line.b != 0:
                raise ValueError(f"{line} isn't a vertical line.")
            return _merge(("x = ", *number_pieces(Fraction(line.c, line.a), numbers)))
        case LineForm.HORIZONTAL:
            if line.a != 0:
                raise ValueError(f"{line} isn't a horizontal line.")
            return _merge((f"{lhs} = ", *number_pieces(Fraction(line.c, line.b), numbers)))
        case _:
            assert_never(form)


def instruction(data: LineQuestionData) -> str:
    """
    Return what the question asks, such as "Find the slope of this line:", for its given form
    to follow, as ``given_pieces`` writes it.

    A line is a function when its equation is in function notation or its zero is asked:
    "Find the zero of this function:". Two points and a point and slope name the line by them:
    "Find the y-intercept of the line through these points:". An intercept asked as a point
    adds "as an ordered pair". A question that asks for an equation is worded by
    ``_equation_instruction``.
    """
    if isinstance(data.asked, LineForm):
        return _equation_instruction(data, data.asked)
    function = data.function is not None or data.asked is LineFeature.ZERO
    match data.given:
        case LineForm.TWO_POINTS:
            noun = "linear function" if function else "line"
            subject = f"the {noun} through these points"
        case LineForm.POINT_AND_SLOPE:
            noun = "linear function" if function else "line"
            subject = f"the {noun} with this point and slope"
        case _:
            subject = "this function" if function else "this line"
    shape = " as an ordered pair" if data.as_point else ""
    return f"Find the {_FEATURE_WORDS[data.asked]} of {subject}{shape}:"


def _equation_instruction(data: LineQuestionData, form: LineForm) -> str:
    """
    Return what a question that asks for an equation in ``form`` asks, for its given to follow:
    "Write this equation in standard form:", "Write the equation of the line through these
    points in slope-intercept form:", or with a relation, "Write the equation of the line through
    (-3, -6) that is parallel to this line, in point-slope form:".

    x = a and y = b aren't named, since naming them gives the answer's shape away. Point-slope
    form from two points is written through the first point, so the question says so. A line
    parallel or perpendicular to an axis has its point shown below instead: "Write the equation
    of the line through this point that is parallel to the x-axis:".
    """
    in_form = f" in {_FORM_WORDS[form]}" if form in _FORM_WORDS else ""
    if data.relation is not None:
        # an axis's line is vertical or horizontal, the other lines neither (see the generator)
        relation = "parallel" if data.relation is Relation.PARALLEL else "perpendicular"
        if data.reference in (X_AXIS, Y_AXIS):
            axis = "x-axis" if data.reference == X_AXIS else "y-axis"
            subject = f"the line through this point that is {relation} to the {axis}"
            return f"Write the equation of {subject}:"
        (point,) = data.points
        through = inline(point_pieces(point, data.numbers))
        return (
            f"Write the equation of the line through {through} that is {relation} to this "
            f"line,{in_form}:"
        )
    match data.given:
        case LineForm.TWO_POINTS:
            using = ", using the first point" if form is LineForm.POINT_SLOPE else ""
            return f"Write the equation of the line through these points{in_form}{using}:"
        case LineForm.POINT_AND_SLOPE:
            return f"Write the equation of the line with this point and slope{in_form}:"
        case _:
            return f"Write this equation{in_form}:"


def given_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the line as the question shows it: its equation in the given form, its two points,
    "(-4, 5) and (4, -1)", or its point and slope, "point (-4, 5), slope -3/4", where a vertical
    line's slope is "undefined".

    With a relation, it's the line the answer is parallel or perpendicular to, in the given form,
    or for an axis, the point the answer passes through: "(3, 7)".
    """
    if data.reference is not None:
        if data.reference in (X_AXIS, Y_AXIS):
            (point,) = data.points
            return point_pieces(point, data.numbers)
        return equation_pieces(data.reference, data.given, numbers=data.numbers)
    match data.given:
        case LineForm.TWO_POINTS:
            first, second = data.points
            return _merge(
                (*point_pieces(first, data.numbers), " and ", *point_pieces(second, data.numbers))
            )
        case LineForm.POINT_AND_SLOPE:
            slope = data.answer.slope
            (point,) = data.points
            return _merge(
                (
                    "point ",
                    *point_pieces(point, data.numbers),
                    ", slope ",
                    *((UNDEFINED,) if slope is None else number_pieces(slope, data.numbers)),
                )
            )
        case _:
            return equation_pieces(
                data.answer,
                data.given,
                numbers=data.numbers,
                function=data.function,
                point=data.points[0] if data.points else None,
                solved_for_y=data.solved_for_y,
            )


def answer_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the answer to ``data`` for the answer key, as ``choice_pieces`` writes it, except the
    slope and y-intercept, which are "slope -3/4, y-intercept 3".
    """
    answer = answer_of(data)
    if data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT and isinstance(answer, tuple):
        slope, intercept = answer
        return _merge(
            (
                "slope ",
                *number_pieces(slope, data.numbers),
                ", y-intercept ",
                *number_pieces(intercept, data.numbers),
            )
        )
    return choice_pieces(data, answer)


def choice_pieces(data: LineQuestionData, choice: LineAnswer) -> Pieces:
    """
    Return ``choice``, the answer to ``data`` or a wrong one, as a multiple-choice option shows
    it: a number in the question's style, "undefined" for ``None``, an ordered pair, such as
    (0, 2), an equation, as ``equation_pieces`` writes it, or for the slope and y-intercept, a
    statement: "The slope is -3/4, and the y-intercept is 3."
    """
    if choice is None:
        return (UNDEFINED,)
    if isinstance(choice, Equation):
        return equation_pieces(choice.line, choice.form, numbers=data.numbers, point=choice.point)
    if not isinstance(choice, tuple):
        return number_pieces(choice, data.numbers)
    if data.asked is not LineFeature.SLOPE_AND_Y_INTERCEPT:
        return point_pieces(choice, data.numbers)
    slope, intercept = choice
    return _merge(
        (
            "The slope is ",
            *number_pieces(slope, data.numbers),
            ", and the y-intercept is ",
            *number_pieces(intercept, data.numbers),
            ".",
        )
    )


def tile_answer_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the answer to ``data`` as a self-check tile's box shows it: as ``answer_pieces``
    writes it, except the slope and y-intercept, which are labelled "m = -3/4, b = 3".
    """
    answer = answer_of(data)
    if data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT and isinstance(answer, tuple):
        slope, intercept = answer
        return _merge(
            (
                "m = ",
                *number_pieces(slope, data.numbers),
                ", b = ",
                *number_pieces(intercept, data.numbers),
            )
        )
    return answer_pieces(data)


def _slope_and_intercept(line: Line, form: LineForm) -> tuple[Fraction, Fraction]:
    """Return the slope and y-intercept of ``line``, which can't be vertical in ``form``."""
    if line.slope is None or line.y_intercept is None:
        raise ValueError(f"A vertical line can't be written in {form} form.")
    return line.slope, line.y_intercept


def _coefficient(value: Fraction, numbers: NumberStyle) -> Pieces:
    """Return ``value`` as the coefficient of a variable: none for 1, and only a sign for -1."""
    if abs(value) == 1:
        return (MINUS,) if value < 0 else ()
    return number_pieces(value, numbers)


def _added(value: Fraction | int, numbers: NumberStyle) -> Pieces:
    """Return ``value`` added to a term, such as " + 2" or " - 3/4", or nothing for 0."""
    value = Fraction(value)
    if value == 0:
        return ()
    sign = f" {MINUS} " if value < 0 else " + "
    return (sign, *number_pieces(abs(value), numbers))


def _standard(line: Line) -> Pieces:
    """Return Ax + By = C, leaving out a term whose coefficient is 0."""
    pieces: list[Piece] = []
    for coefficient, variable in ((line.a, "x"), (line.b, "y")):
        if coefficient == 0:
            continue
        if pieces:
            pieces.append(f" {MINUS} " if coefficient < 0 else " + ")
        elif coefficient < 0:
            pieces.append(MINUS)
        size = abs(coefficient)
        pieces.append(variable if size == 1 else f"{size:,}{variable}")
    return _merge((*pieces, " = ", *number_pieces(line.c, NumberStyle.FRACTION)))


def _merge(pieces: Iterable[Piece]) -> Pieces:
    """Join neighbouring strings among ``pieces`` and drop empty ones."""
    merged: list[Piece] = []
    for piece in pieces:
        last = merged[-1] if merged else None
        if isinstance(piece, str) and isinstance(last, str):
            merged[-1] = last + piece
        elif piece != "":
            merged.append(piece)
    return tuple(merged)
