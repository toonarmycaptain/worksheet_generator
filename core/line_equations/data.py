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


def choice_row(line: Line, x: int) -> tuple[Fraction, Fraction]:
    """
    Return the row at ``x`` of a table of ``line`` to choose: (x, y) on the line, or for a
    vertical line x = c, which a wrong table can be, (c, x), with x and y exchanged.
    """
    if line.b == 0:
        return (Fraction(line.c, line.a), Fraction(x))
    return (Fraction(x), Fraction(line.c - line.a * x, line.b))


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
    TABLE = "table"  # x: -4, 1, 3, 8 and y: 5, 1.5, 0, -3.5
    GRAPH = "graph"  # drawn on a coordinate grid through two marked points
    SLOPE_AND_INTERCEPT = "slope_and_intercept"  # slope -2/3, y-intercept 2
    INTERCEPTS = "intercepts"  # x-intercept 3, y-intercept 2


@dataclass(frozen=True)
class Grid:
    """
    A coordinate grid with one square per ``step`` units both ways: x from -``largest_x`` to
    ``largest_x`` and y from -``largest_y`` to ``largest_y``, each a multiple of ``step``.
    """

    largest_x: int
    largest_y: int
    step: int


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


class Statement(StrEnum):
    """
    What a statement answer says about a vertical or horizontal line besides its equation, as
    STAAR's A.2(G) items ask it. Values are stable identifiers for the API and storage.
    """

    SLOPE = "slope"  # The equation of the line is x = -4, and the slope is undefined.
    X_AXIS = "x_axis"  # The equation of the line is y = 3, and the line is parallel to the x-axis.


class NumberStyle(StrEnum):
    """
    How a question writes its numbers that aren't whole. Values are stable identifiers for the
    API and storage.
    """

    FRACTION = "fraction"  # 5/2
    DECIMAL = "decimal"  # 2.5, for a number whose decimal terminates
    MIXED_NUMBER = "mixed_number"  # 2 1/2


# What a line is shown as when a feature of it is asked: every form but the slope and y-intercept
# and the intercepts, which graphing lines alone gives
FEATURE_GIVENS = tuple(
    form for form in LineForm if form not in (LineForm.SLOPE_AND_INTERCEPT, LineForm.INTERCEPTS)
)
# What a line's equation is written from (TEKS 8.5(I), A.2(B), (C), (E), (F) and (G)): an
# equation in another form, a point and the slope, two points, a table, a graph, or a parallel or
# perpendicular line and a point; and the forms it's written in. x = a and y = b are written,
# never given.
EQUATION_GIVENS: tuple[LineForm | Relation, ...] = (
    LineForm.SLOPE_INTERCEPT,
    LineForm.STANDARD,
    LineForm.POINT_SLOPE,
    LineForm.POINT_AND_SLOPE,
    LineForm.TWO_POINTS,
    LineForm.TABLE,
    LineForm.GRAPH,
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
# What a line is graphed from (TEKS 8.5(I), A.3(C), A.2(G)): an equation, a point and slope, two
# points, the slope and y-intercept, or the intercepts; and what a table to complete is made
# from: an equation or a graph. A graph and a table are what is asked.
GRAPHING_GIVENS = (
    LineForm.SLOPE_INTERCEPT,
    LineForm.STANDARD,
    LineForm.POINT_SLOPE,
    LineForm.SLOPE_AND_INTERCEPT,
    LineForm.INTERCEPTS,
    LineForm.POINT_AND_SLOPE,
    LineForm.TWO_POINTS,
    LineForm.VERTICAL,
    LineForm.HORIZONTAL,
    LineForm.GRAPH,
)
GRAPHING_ASKED = (LineForm.GRAPH, LineForm.TABLE)


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
    one for point-slope form and a point and slope, two for two points, the two marked points
    for a graph, and for a table, one of its rows with whole numbers off the axes, which an
    equation in point-slope form is written through; none otherwise.

    A table's rows are at the x-values ``table_xs``, in order, each with the line's y-value
    there. It is set out across the page, x above y, when ``table_across`` is ``True``, and
    down it, x beside y, otherwise. A table to complete leaves out one cell of each row,
    ``table_blanks`` holding each row's column left out: 0 for x, 1 for y. ``grid`` is the
    coordinate grid a graph is drawn on, the blank grid a line is graphed on, or a blank grid
    shown beside two points to work on, and ``None`` otherwise. A graph's marked
    points have their coordinates printed beside them when ``labelled`` is ``True``. A line to
    graph has ``key_points``, the two points its answer key marks.

    With a ``relation``, the question shows ``reference``, a line the answer is parallel or
    perpendicular to, written in the ``given`` form, and ``points`` holds the one point the
    answer passes through. The reference is the x- or y-axis, ``X_AXIS`` or ``Y_AXIS``, when the
    answer is horizontal or vertical. Without a relation, ``reference`` is ``None``.

    A question that asks for a vertical or horizontal line's equation can ask, with a
    ``statement``, for its slope or how it runs against the x-axis too, as a ``Stated`` answer.

    A question that asks to graph a line or complete a table is ``chosen`` when the student
    chooses the graph or table, from lettered choices or a self-check tiles bank, instead of
    drawing or completing it. Then ``grid`` is the window every graph to choose from shares, or
    on a tiles sheet the window of the line's own graph in the bank, and ``table_xs`` the
    x-values of every table to choose from, or of the line's own table in the bank, with no
    ``table_blanks``.

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
    table_xs: tuple[int, ...] = ()
    table_across: bool = False
    table_blanks: tuple[int, ...] = ()
    grid: Grid | None = None
    labelled: bool = False
    key_points: tuple[Point, ...] = ()
    statement: Statement | None = None
    chosen: bool = False


@dataclass(frozen=True)
class Equation:
    """
    The equation of ``line`` in ``form``, an answer to a question that asks for one. ``point`` is
    the point point-slope form is written through, and ``None`` in the other forms.
    """

    line: Line
    form: LineForm
    point: Point | None = None


@dataclass(frozen=True)
class Stated:
    """
    A statement answer about a vertical or horizontal line: ``equation``, and ``about``, its
    slope, 0 or ``None`` for undefined, or how it runs against the x-axis,
    ``Relation.PARALLEL`` or ``Relation.PERPENDICULAR``.
    """

    equation: Equation
    about: Fraction | Relation | None


def stated(equation: Equation, statement: Statement) -> Stated:
    """
    Return what ``equation``'s line, vertical or horizontal, has for ``statement``: its slope,
    0 for a horizontal line and ``None`` (undefined) for a vertical one, or how it runs against
    the x-axis, parallel for a horizontal line and perpendicular for a vertical one.
    """
    horizontal = equation.line.a == 0
    if statement is Statement.SLOPE:
        return Stated(equation, Fraction(0) if horizontal else None)
    return Stated(equation, Relation.PARALLEL if horizontal else Relation.PERPENDICULAR)


# What a student writes or chooses for a question about a line: a number, ``None`` for an
# undefined slope, two numbers, which are an ordered pair for an intercept asked as a point or
# the slope and y-intercept, an equation, which for a graph or table to choose stands for the
# line's graph or table, or a statement about a vertical or horizontal line
type LineAnswer = Fraction | tuple[Fraction, Fraction] | Equation | Stated | None


def answer_of(data: LineQuestionData) -> LineAnswer:
    """
    Return the answer to ``data`` as the student gives it: the feature's number, the intercept's
    ordered pair, such as (0, 2), the slope and y-intercept, the line's equation in the form
    asked, which in point-slope form goes through the first point shown, with its statement if
    the question asks one, or for a graph or table, the line as an equation in that form.
    """
    if isinstance(data.asked, LineForm):
        point = data.points[0] if data.asked is LineForm.POINT_SLOPE else None
        equation = Equation(data.answer, data.asked, point)
        return equation if data.statement is None else stated(equation, data.statement)
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
