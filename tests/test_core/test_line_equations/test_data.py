"""
Tests for a line's slope and intercepts, worked out from its equation in standard form, its
normalised form, and the answer to a question about it.
"""

from fractions import Fraction

import pytest

from core.line_equations.data import (
    Equation,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    Relation,
    Stated,
    Statement,
    answer_of,
    choice_row,
    feature_value,
    line_from,
    stated,
)

SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, X_INTERCEPT, ZERO, SLOPE_AND_Y_INTERCEPT = LineFeature
(
    SLOPE_INTERCEPT,
    STANDARD,
    POINT_SLOPE,
    POINT_AND_SLOPE,
    TWO_POINTS,
    VERTICAL,
    HORIZONTAL,
    TABLE,
    GRAPH,
    SLOPE_AND_INTERCEPT,
    INTERCEPTS,
) = LineForm


@pytest.mark.parametrize(
    ("line", "slope", "y_intercept", "x_intercept"),
    [
        (Line(3, 4, 8), Fraction(-3, 4), Fraction(2), Fraction(8, 3)),
        (Line(2, -1, 3), Fraction(2), Fraction(-3), Fraction(3, 2)),
        (Line(1, 1, -5), Fraction(-1), Fraction(-5), Fraction(-5)),
        (Line(3, -1, 0), Fraction(3), Fraction(0), Fraction(0)),  # through the origin
        # vertical: x = -4 and x = 5/2, whose slope is undefined
        (Line(1, 0, -4), None, None, Fraction(-4)),
        (Line(2, 0, 5), None, None, Fraction(5, 2)),
        # horizontal: y = 5/2, which never crosses the x-axis
        (Line(0, 2, 5), Fraction(0), Fraction(5, 2), None),
    ],
)
def test_slope_and_intercepts(
    line: Line,
    slope: Fraction | None,
    y_intercept: Fraction | None,
    x_intercept: Fraction | None,
) -> None:
    """The slope is -A/B, the y-intercept C/B and the x-intercept C/A."""
    assert (line.slope, line.y_intercept, line.x_intercept) == (slope, y_intercept, x_intercept)


@pytest.mark.parametrize(
    ("line", "feature", "value"),
    [
        (Line(3, 4, 8), SLOPE, Fraction(-3, 4)),
        (Line(3, 4, 8), RATE_OF_CHANGE, Fraction(-3, 4)),
        (Line(3, 4, 8), Y_INTERCEPT, Fraction(2)),
        (Line(3, 4, 8), X_INTERCEPT, Fraction(8, 3)),
        (Line(3, 4, 8), ZERO, Fraction(8, 3)),
        (Line(1, 0, -4), SLOPE, None),
        (Line(1, 0, -4), Y_INTERCEPT, None),
        (Line(0, 2, 5), X_INTERCEPT, None),
    ],
)
def test_feature_value(line: Line, feature: LineFeature, value: Fraction | None) -> None:
    """The rate of change is the slope, and the zero is the x-intercept."""
    assert feature_value(line, feature) == value


@pytest.mark.parametrize(
    ("a", "b", "c", "line"),
    [
        # 3/4x + y = 2, in whole numbers
        (Fraction(3, 4), Fraction(1), Fraction(2), Line(3, 4, 8)),
        # -2x + y = 3, its first number made positive
        (Fraction(-2), Fraction(1), Fraction(3), Line(2, -1, -3)),
        # -2y = 4, with no x term, its y term made positive
        (Fraction(0), Fraction(-2), Fraction(4), Line(0, 1, -2)),
        # 4x + 6y = 8, without the common factor
        (Fraction(4), Fraction(6), Fraction(8), Line(2, 3, 4)),
    ],
)
def test_line_from(a: Fraction, b: Fraction, c: Fraction, line: Line) -> None:
    """Each line has one normalised form: whole numbers, no common factor, the first positive."""
    assert line_from(a, b, c) == line


@pytest.mark.parametrize(
    ("data", "answer"),
    [
        (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE), Fraction(-3, 4)),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True),
            (Fraction(0), Fraction(2)),
        ),
        # an equation: in point-slope form through the first point shown, in any other form
        # through none
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))),
            Equation(Line(3, 4, 8), POINT_SLOPE, (-4, 5)),
        ),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, STANDARD, ((-4, 5), (4, -1))),
            Equation(Line(3, 4, 8), STANDARD),
        ),
        (
            LineQuestionData(Line(1, 0, 3), POINT_AND_SLOPE, VERTICAL, ((3, 7),)),
            Equation(Line(1, 0, 3), VERTICAL),
        ),
        # a statement: the equation with its slope, or how it runs against the x-axis
        (
            LineQuestionData(
                Line(1, 0, 3), TWO_POINTS, VERTICAL, ((3, 7), (3, 1)), statement=Statement.SLOPE
            ),
            Stated(Equation(Line(1, 0, 3), VERTICAL), None),
        ),
        (
            LineQuestionData(
                Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),), statement=Statement.X_AXIS
            ),
            Stated(Equation(Line(0, 1, 7), HORIZONTAL), Relation.PARALLEL),
        ),
        # a graph to choose: the line, as an equation in that form
        (
            LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True),
            Equation(Line(2, -3, -12), GRAPH),
        ),
    ],
)
def test_answer_of(data: LineQuestionData, answer: LineAnswer) -> None:
    """The answer is the feature asked, or the line's equation in the form asked."""
    assert answer_of(data) == answer


@pytest.mark.parametrize(
    ("equation", "statement", "stated_answer"),
    [
        (
            Equation(Line(1, 0, -4), VERTICAL),
            Statement.SLOPE,
            Stated(Equation(Line(1, 0, -4), VERTICAL), None),
        ),
        (
            Equation(Line(0, 1, 3), HORIZONTAL),
            Statement.SLOPE,
            Stated(Equation(Line(0, 1, 3), HORIZONTAL), Fraction(0)),
        ),
        (
            Equation(Line(1, 0, -4), VERTICAL),
            Statement.X_AXIS,
            Stated(Equation(Line(1, 0, -4), VERTICAL), Relation.PERPENDICULAR),
        ),
        (
            Equation(Line(0, 1, 3), HORIZONTAL),
            Statement.X_AXIS,
            Stated(Equation(Line(0, 1, 3), HORIZONTAL), Relation.PARALLEL),
        ),
    ],
)
def test_stated(equation: Equation, statement: Statement, stated_answer: Stated) -> None:
    """A vertical line's slope is undefined, a horizontal one's 0; parallel is horizontal."""
    assert stated(equation, statement) == stated_answer


@pytest.mark.parametrize(
    ("line", "x", "row"),
    [
        # y = 2x - 3
        (Line(2, -1, 3), 4, (Fraction(4), Fraction(5))),
        # 2y = 5: y = 2.5 in every row
        (Line(0, 2, 5), -3, (Fraction(-3), Fraction(5, 2))),
        # x = 2.5: x and y exchanged, so 2.5 in every row of x, the x-value as y
        (Line(2, 0, 5), -3, (Fraction(5, 2), Fraction(-3))),
    ],
)
def test_choice_row(line: Line, x: int, row: tuple[Fraction, Fraction]) -> None:
    """A table's row at x is the point on the line there, or for x = c, (c, x)."""
    assert choice_row(line, x) == row
