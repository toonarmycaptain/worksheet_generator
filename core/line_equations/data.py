"""
Data for questions about a line: the line, the form it's shown in, and what is asked about it,
a feature of the line or its equation in a form.
"""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from math import gcd, lcm
from typing import assert_never

from core.question import FreeResponse, MultipleChoice, Question, QuestionData

# A point with integer coordinates, as (x, y)
type Point = tuple[int, int]


@dataclass(frozen=True)
class Line:
    """
    A line as the integers ``a``, ``b`` and ``c`` of its equation in standard form,
    Ax + By = C, so that one shape holds every line, vertical lines included.

    The coefficients are normalised, so each line has one ``Line``: ``a`` is positive, or ``a`` is
    0 and ``b`` positive, and ``a``, ``b`` and ``c`` have no common factor. This class doesn't
    enforce it; the generator only builds normalised lines.
    """

    a: int
    b: int
    c: int

    @property
    def slope(self) -> Fraction | None:
        """The slope, -A/B, or ``None`` for a vertical line, whose slope is undefined."""
        return None if self.b == 0 else Fraction(-self.a, self.b)

    @property
    def y_intercept(self) -> Fraction | None:
        """Where the line crosses the y-axis, C/B, or ``None`` for a vertical line."""
        return None if self.b == 0 else Fraction(self.c, self.b)

    @property
    def x_intercept(self) -> Fraction | None:
        """Where the line crosses the x-axis, C/A, or ``None`` for a horizontal line."""
        return None if self.a == 0 else Fraction(self.c, self.a)


def line_from(a: Fraction, b: Fraction, c: Fraction) -> Line:
    """
    Return the normalised ``Line`` of ax + by = c: whole numbers with no common factor, the
    first that isn't 0 positive. ``a`` and ``b`` mustn't both be 0.
    """
    scale = lcm(a.denominator, b.denominator, c.denominator)
    whole = [int(value * scale) for value in (a, b, c)]
    divisor = gcd(*whole)
    if whole[0] < 0 or (whole[0] == 0 and whole[1] < 0):
        divisor = -divisor
    return Line(*(value // divisor for value in whole))


X_AXIS = Line(0, 1, 0)  # y = 0
Y_AXIS = Line(1, 0, 0)  # x = 0


class LineForm(StrEnum):
    """
    A way of showing a line: an equation, or the points or point and slope it is found from.
    Values are stable identifiers for the API and storage.
    """

    SLOPE_INTERCEPT = "slope_intercept"  # y = -3/4x + 2, or f(x) = -3/4x + 2
    STANDARD = "standard"  # 3x + 4y = 8
    POINT_SLOPE = "point_slope"  # y - 5 = -3/4(x + 4)
    POINT_AND_SLOPE = "point_and_slope"  # through (-4, 5) with a slope of -3/4
    TWO_POINTS = "two_points"  # through (-4, 5) and (4, -1)
    VERTICAL = "vertical"  # x = -4
    HORIZONTAL = "horizontal"  # y = 2.5


class LineFeature(StrEnum):
    """
    What is asked about a line, worded as STAAR words it: the slope and the rate of change are
    the same number, as are the x-intercept and the zero. Values are stable identifiers for the
    API and storage.
    """

    SLOPE = "slope"
    RATE_OF_CHANGE = "rate_of_change"
    Y_INTERCEPT = "y_intercept"
    X_INTERCEPT = "x_intercept"
    ZERO = "zero"
    SLOPE_AND_Y_INTERCEPT = "slope_and_y_intercept"  # both, as 8.4(C) asks in 9 of 22 items


class Relation(StrEnum):
    """
    How a line asked for runs beside another line it's found from: through a given point,
    parallel or perpendicular to it (TEKS A.2(E), (F) and, for the axes, (G)). Values are stable
    identifiers for the API and storage.
    """

    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"


class NumberStyle(StrEnum):
    """
    How a question writes its numbers that aren't whole. Values are stable identifiers for the
    API and storage.
    """

    FRACTION = "fraction"  # 5/2
    DECIMAL = "decimal"  # 2.5, for a number whose decimal terminates
    MIXED_NUMBER = "mixed_number"  # 2 1/2


# What a line's equation is written from (TEKS 8.5(I), A.2(B), (E), (F) and (G)): an equation in
# another form, a point and the slope, two points, or a parallel or perpendicular line and a
# point; and the forms it's written in. x = a and y = b are written, never given.
EQUATION_GIVENS: tuple[LineForm | Relation, ...] = (
    LineForm.SLOPE_INTERCEPT,
    LineForm.STANDARD,
    LineForm.POINT_SLOPE,
    LineForm.POINT_AND_SLOPE,
    LineForm.TWO_POINTS,
    Relation.PARALLEL,
    Relation.PERPENDICULAR,
)
EQUATION_FORMS = (
    LineForm.SLOPE_INTERCEPT,
    LineForm.STANDARD,
    LineForm.POINT_SLOPE,
    LineForm.VERTICAL,
    LineForm.HORIZONTAL,
)


def feature_value(line: Line, feature: LineFeature) -> Fraction | None:
    """
    Return ``feature`` of ``line``: its slope, which is ``None`` for a vertical line, or an
    intercept, which is ``None`` for a line that doesn't cross that axis.

    Raises ``ValueError`` for the slope and y-intercept, which are two numbers.
    """
    match feature:
        case LineFeature.SLOPE | LineFeature.RATE_OF_CHANGE:
            return line.slope
        case LineFeature.Y_INTERCEPT:
            return line.y_intercept
        case LineFeature.X_INTERCEPT | LineFeature.ZERO:
            return line.x_intercept
        case LineFeature.SLOPE_AND_Y_INTERCEPT:
            raise ValueError("The slope and y-intercept are two numbers.")
        case _:
            assert_never(feature)


@dataclass(frozen=True)
class LineQuestionData(QuestionData[Line]):
    """
    A question about a line, ``answer``, shown in the ``given`` form, that asks for a feature of
    it or its equation in a form, ``asked``.

    The answer is the line itself, as in place value: every form shows the same line, and what
    is asked decides what the student writes. ``points`` holds the points the given form shows:
    one for point-slope form and a point and slope, two for two points, none otherwise.

    With a ``relation``, the question shows ``reference``, a line the answer is parallel or
    perpendicular to, written in the ``given`` form, and ``points`` holds the one point the
    answer passes through. The reference is the x- or y-axis, ``X_AXIS`` or ``Y_AXIS``, when the
    answer is horizontal or vertical. Without a relation, ``reference`` is ``None``.

    ``as_point`` is ``True`` when an intercept is answered as an ordered pair, such as (0, 2),
    rather than a number. ``numbers`` is how the question writes its numbers that aren't whole.
    ``function`` names the function when the equation is written in function notation, such as
    "f" for f(x) = 2x + 1, and is ``None`` for y = 2x + 1. ``solved_for_y`` is ``True`` when a
    given equation in point-slope form is written y = m(x - x₁) + y₁ rather than
    y - y₁ = m(x - x₁).

    The generator only asks for a feature the line has: never a vertical line's y-intercept,
    rate of change or zero, nor a horizontal line's x-intercept or zero. It only asks for an
    equation in a form that can show the line: x = a for a vertical line and y = b for a
    horizontal one, the other forms for a line that is neither.
    """

    answer: Line
    given: LineForm
    asked: LineFeature | LineForm
    points: tuple[Point, ...] = ()
    as_point: bool = False
    numbers: NumberStyle = NumberStyle.FRACTION
    function: str | None = None
    reference: Line | None = None
    relation: Relation | None = None
    solved_for_y: bool = False


@dataclass(frozen=True)
class Equation:
    """
    The equation of ``line`` in ``form``, an answer to a question that asks for one. ``point`` is
    the point point-slope form is written through, and ``None`` in the other forms.
    """

    line: Line
    form: LineForm
    point: Point | None = None


# What a student writes or chooses for a question about a line: a number, ``None`` for an
# undefined slope, two numbers, which are an ordered pair for an intercept asked as a point or
# the slope and y-intercept, or an equation
type LineAnswer = Fraction | tuple[Fraction, Fraction] | Equation | None


def answer_of(data: LineQuestionData) -> LineAnswer:
    """
    Return the answer to ``data`` as the student gives it: the feature's number, the intercept's
    ordered pair, such as (0, 2), the slope and y-intercept, or the line's equation in the form
    asked, which in point-slope form goes through the first point shown.
    """
    if isinstance(data.asked, LineForm):
        point = data.points[0] if data.asked is LineForm.POINT_SLOPE else None
        return Equation(data.answer, data.asked, point)
    return line_answer(data.answer, data.asked, data.as_point)


def line_answer(line: Line, asked: LineFeature, as_point: bool) -> LineAnswer:
    """
    Return the answer to ``asked`` about ``line``, as ``answer_of`` does for a question's data.

    Raises ``ValueError`` if the line hasn't the feature asked as two numbers or a point.
    """
    if asked is LineFeature.SLOPE_AND_Y_INTERCEPT:
        if line.slope is None or line.y_intercept is None:
            raise ValueError("A vertical line has no slope or y-intercept to give.")
        return (line.slope, line.y_intercept)
    value = feature_value(line, asked)
    if not as_point:
        return value
    if value is None:
        raise ValueError(f"{line} has no {asked} to give as a point.")
    return (Fraction(0), value) if asked is LineFeature.Y_INTERCEPT else (value, Fraction(0))


# A question about a line as presented: the student writes the answer, or chooses it from the
# answer and wrong answers
type LineQuestion = Question[LineQuestionData, FreeResponse | MultipleChoice[LineAnswer]]
