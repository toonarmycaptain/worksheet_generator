"""
Tests for writing a line's numbers, points, equations and answers, both inline and as pieces, in
which a ``Fraction`` is drawn stacked.
"""

from dataclasses import replace
from fractions import Fraction

import pytest

from core.line_equations.data import (
    X_AXIS,
    Y_AXIS,
    Equation,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    Relation,
    Stated,
    Statement,
)
from core.line_equations.representation import (
    answer_pieces,
    blank_labels,
    choice_pieces,
    choice_table_cells,
    equation_pieces,
    given_pieces,
    instruction,
    point_pieces,
    table_cells,
    tile_answer_pieces,
)
from core.written_numbers import (
    NumberStyle,
    Pieces,
    inline,
)
from tests.data import MINUS

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
FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle
PARALLEL, PERPENDICULAR = Relation
# through (2, -2), perpendicular to y = 2/5x + 2, as A.2 2018 Q39
PERPENDICULAR_DATA = LineQuestionData(
    Line(5, 2, 6),
    SLOPE_INTERCEPT,
    SLOPE_INTERCEPT,
    ((2, -2),),
    reference=Line(2, -5, -10),
    relation=PERPENDICULAR,
)


@pytest.mark.parametrize(
    ("point", "style", "pieces"),
    [
        ((-4, 5), FRACTION, (f"({MINUS}4, 5)",)),
        ((Fraction(5, 2), 0), FRACTION, ("(", Fraction(5, 2), ", 0)")),
        ((0, Fraction(-3, 4)), DECIMAL, (f"(0, {MINUS}0.75)",)),
    ],
)
def test_point_pieces(
    point: tuple[Fraction | int, Fraction | int], style: NumberStyle, pieces: Pieces
) -> None:
    """A point is an ordered pair."""
    assert point_pieces(point, style) == pieces


@pytest.mark.parametrize(
    ("line", "form", "numbers", "function", "point", "pieces", "text"),
    [
        # slope-intercept
        (
            Line(3, 4, 8),
            SLOPE_INTERCEPT,
            FRACTION,
            None,
            None,
            (f"y = {MINUS}", Fraction(3, 4), "x + 2"),
            f"y = {MINUS}3/4x + 2",
        ),
        (
            Line(3, 4, 8),
            SLOPE_INTERCEPT,
            DECIMAL,
            None,
            None,
            (f"y = {MINUS}0.75x + 2",),
            f"y = {MINUS}0.75x + 2",
        ),
        (
            Line(3, 4, 8),
            SLOPE_INTERCEPT,
            FRACTION,
            "f",
            None,
            (f"f(x) = {MINUS}", Fraction(3, 4), "x + 2"),
            f"f(x) = {MINUS}3/4x + 2",
        ),
        (
            Line(2, -3, 1),
            SLOPE_INTERCEPT,
            FRACTION,
            None,
            None,
            ("y = ", Fraction(2, 3), f"x {MINUS} ", Fraction(1, 3)),
            f"y = 2/3x {MINUS} 1/3",
        ),
        # a slope of 1 or -1 has no number, and an intercept of 0 is left out
        (Line(1, -1, -2), SLOPE_INTERCEPT, FRACTION, None, None, ("y = x + 2",), "y = x + 2"),
        (
            Line(1, 1, 2),
            SLOPE_INTERCEPT,
            FRACTION,
            None,
            None,
            (f"y = {MINUS}x + 2",),
            f"y = {MINUS}x + 2",
        ),
        (Line(3, -1, 0), SLOPE_INTERCEPT, FRACTION, None, None, ("y = 3x",), "y = 3x"),
        # a slope of 0 leaves only the intercept
        (Line(0, 2, 5), SLOPE_INTERCEPT, FRACTION, None, None, ("y = ", Fraction(5, 2)), "y = 5/2"),
        # standard, in whole numbers, a coefficient of 0 left out
        (Line(3, 4, 8), STANDARD, FRACTION, None, None, ("3x + 4y = 8",), "3x + 4y = 8"),
        (
            Line(2, -1, -3),
            STANDARD,
            DECIMAL,
            None,
            None,
            (f"2x {MINUS} y = {MINUS}3",),
            f"2x {MINUS} y = {MINUS}3",
        ),
        (Line(1, 1, 2), STANDARD, FRACTION, None, None, ("x + y = 2",), "x + y = 2"),
        (Line(1, 0, -4), STANDARD, FRACTION, None, None, (f"x = {MINUS}4",), f"x = {MINUS}4"),
        (Line(0, 2, 5), STANDARD, FRACTION, None, None, ("2y = 5",), "2y = 5"),
        # point-slope
        (
            Line(3, 4, 8),
            POINT_SLOPE,
            FRACTION,
            None,
            (-4, 5),
            (f"y {MINUS} 5 = {MINUS}", Fraction(3, 4), "(x + 4)"),
            f"y {MINUS} 5 = {MINUS}3/4(x + 4)",
        ),
        (
            Line(3, 4, 8),
            POINT_SLOPE,
            DECIMAL,
            None,
            (-4, 5),
            (f"y {MINUS} 5 = {MINUS}0.75(x + 4)",),
            f"y {MINUS} 5 = {MINUS}0.75(x + 4)",
        ),
        (
            Line(2, -1, 3),
            POINT_SLOPE,
            FRACTION,
            None,
            (1, -1),
            (f"y + 1 = 2(x {MINUS} 1)",),
            f"y + 1 = 2(x {MINUS} 1)",
        ),
        # a slope of 1 needs no brackets, -1 does
        (
            Line(1, -1, -2),
            POINT_SLOPE,
            FRACTION,
            None,
            (1, 3),
            (f"y {MINUS} 3 = x {MINUS} 1",),
            f"y {MINUS} 3 = x {MINUS} 1",
        ),
        (
            Line(1, 1, 2),
            POINT_SLOPE,
            FRACTION,
            None,
            (1, 1),
            (f"y {MINUS} 1 = {MINUS}(x {MINUS} 1)",),
            f"y {MINUS} 1 = {MINUS}(x {MINUS} 1)",
        ),
        # a point on an axis
        (
            Line(3, -1, -2),
            POINT_SLOPE,
            FRACTION,
            None,
            (0, 2),
            (f"y {MINUS} 2 = 3x",),
            f"y {MINUS} 2 = 3x",
        ),
        (
            Line(2, -1, 6),
            POINT_SLOPE,
            FRACTION,
            None,
            (3, 0),
            (f"y = 2(x {MINUS} 3)",),
            f"y = 2(x {MINUS} 3)",
        ),
        # vertical and horizontal
        (Line(2, 0, 5), VERTICAL, FRACTION, None, None, ("x = ", Fraction(5, 2)), "x = 5/2"),
        (Line(2, 0, 5), VERTICAL, DECIMAL, None, None, ("x = 2.5",), "x = 2.5"),
        (Line(1, 0, -4), VERTICAL, FRACTION, None, None, (f"x = {MINUS}4",), f"x = {MINUS}4"),
        (
            Line(0, 5, -18),
            HORIZONTAL,
            DECIMAL,
            None,
            None,
            (f"y = {MINUS}3.6",),
            f"y = {MINUS}3.6",
        ),
        (
            Line(0, 5, -18),
            HORIZONTAL,
            FRACTION,
            "f",
            None,
            (f"f(x) = {MINUS}", Fraction(18, 5)),
            f"f(x) = {MINUS}18/5",
        ),
    ],
)
def test_equation_pieces(
    line: Line,
    form: LineForm,
    numbers: NumberStyle,
    function: str | None,
    point: tuple[int, int] | None,
    pieces: Pieces,
    text: str,
) -> None:
    """Signs stay outside fractions, and a term whose number is 0 is left out."""
    result = equation_pieces(line, form, numbers=numbers, function=function, point=point)
    assert result == pieces
    assert inline(result) == text


@pytest.mark.parametrize(
    ("line", "numbers", "point", "pieces", "text"),
    [
        (
            Line(3, 4, 8),
            FRACTION,
            (-4, 5),
            (f"y = {MINUS}", Fraction(3, 4), "(x + 4) + 5"),
            f"y = {MINUS}3/4(x + 4) + 5",
        ),
        (
            Line(3, 4, 8),
            DECIMAL,
            (4, -1),
            (f"y = {MINUS}0.75(x {MINUS} 4) {MINUS} 1",),
            f"y = {MINUS}0.75(x {MINUS} 4) {MINUS} 1",
        ),
        # a slope of 1 or -1 keeps its brackets
        (Line(1, -1, -2), FRACTION, (1, 3), (f"y = (x {MINUS} 1) + 3",), f"y = (x {MINUS} 1) + 3"),
        (
            Line(1, 1, 4),
            FRACTION,
            (1, 3),
            (f"y = {MINUS}(x {MINUS} 1) + 3",),
            f"y = {MINUS}(x {MINUS} 1) + 3",
        ),
        # a point on the x-axis: y = m(x - r), as in either style
        (Line(2, -1, 6), FRACTION, (3, 0), (f"y = 2(x {MINUS} 3)",), f"y = 2(x {MINUS} 3)"),
    ],
)
def test_point_slope_solved_for_y(
    line: Line, numbers: NumberStyle, point: tuple[int, int], pieces: Pieces, text: str
) -> None:
    """Point-slope form solved for y is y = m(x - x₁) + y₁, as STAAR gives it in A.3."""
    result = equation_pieces(line, POINT_SLOPE, numbers=numbers, point=point, solved_for_y=True)
    assert result == pieces
    assert inline(result) == text


@pytest.mark.parametrize(
    ("line", "form", "point", "message"),
    [
        (
            Line(3, 4, 8),
            POINT_AND_SLOPE,
            (-4, 5),
            "A line given by point_and_slope isn't an equation.",
        ),
        (Line(3, 4, 8), TWO_POINTS, None, "A line given by two_points isn't an equation."),
        (Line(3, 4, 8), TABLE, None, "A line given by table isn't an equation."),
        (Line(3, 4, 8), GRAPH, None, "A line given by graph isn't an equation."),
        (
            Line(1, 0, -4),
            SLOPE_INTERCEPT,
            None,
            "A vertical line can't be written in slope_intercept form.",
        ),
        (
            Line(1, 0, -4),
            POINT_SLOPE,
            (-4, 1),
            "A vertical line can't be written in point_slope form.",
        ),
        (Line(3, 4, 8), POINT_SLOPE, None, "Point-slope form needs a point."),
        (Line(3, 4, 8), VERTICAL, None, "Line(a=3, b=4, c=8) isn't a vertical line."),
        (Line(3, 4, 8), HORIZONTAL, None, "Line(a=3, b=4, c=8) isn't a horizontal line."),
    ],
)
def test_equation_pieces_errors(
    line: Line, form: LineForm, point: tuple[int, int] | None, message: str
) -> None:
    """Points aren't equations, and a vertical line has no slope or y-intercept to write."""
    with pytest.raises(ValueError) as error:
        equation_pieces(line, form, point=point)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("data", "pieces"),
    [
        (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE), (MINUS, Fraction(3, 4))),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, RATE_OF_CHANGE, numbers=DECIMAL),
            (f"{MINUS}0.75",),
        ),
        (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), ("undefined",)),
        (LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT), ("2",)),
        (LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True), ("(0, 2)",)),
        (LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT), (Fraction(8, 3),)),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT, as_point=True),
            ("(", Fraction(8, 3), ", 0)"),
        ),
        (LineQuestionData(Line(2, -1, 5), STANDARD, ZERO, numbers=DECIMAL), ("2.5",)),
        # an equation in the form asked, in point-slope form through the first point shown
        (
            LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD),
            (f"3x {MINUS} 4y = {MINUS}5",),
        ),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))),
            (f"y {MINUS} 5 = {MINUS}", Fraction(3, 4), "(x + 4)"),
        ),
        (LineQuestionData(Line(1, 0, 3), POINT_AND_SLOPE, VERTICAL, ((3, 7),)), ("x = 3",)),
    ],
)
def test_answer_pieces(data: LineQuestionData, pieces: Pieces) -> None:
    """
    The feature asked, as a number or an ordered pair, or "undefined" for a vertical slope; or the
    equation asked.
    """
    assert answer_pieces(data) == pieces


@pytest.mark.parametrize(
    ("data", "text"),
    [
        (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE), "Find the slope of this line:"),
        (
            LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, RATE_OF_CHANGE, function="f"),
            "Find the rate of change of this function:",
        ),
        # a zero makes the line a function
        (LineQuestionData(Line(3, 4, 8), STANDARD, ZERO), "Find the zero of this function:"),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True),
            "Find the y-intercept of this line as an ordered pair:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, X_INTERCEPT, ((-4, 5), (4, -1))),
            "Find the x-intercept of the line through these points:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, ZERO, ((-4, 5), (4, -1))),
            "Find the zero of the linear function through these points:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, Y_INTERCEPT, ((-4, 5),)),
            "Find the y-intercept of the line with this point and slope:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE_AND_Y_INTERCEPT),
            "Find the slope and y-intercept of this line:",
        ),
        # an equation: the form asked is named, except x = a and y = b
        (
            LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, STANDARD),
            "Write this equation in standard form:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_SLOPE, SLOPE_INTERCEPT, ((-4, 5),)),
            "Write this equation in slope-intercept form:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))),
            "Write the equation of the line through these points in point-slope form, using the "
            "first point:",
        ),
        (
            LineQuestionData(Line(1, 0, 3), TWO_POINTS, VERTICAL, ((3, 7), (3, -2))),
            "Write the equation of the line through these points:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, STANDARD, ((-4, 5),)),
            "Write the equation of the line with this point and slope in standard form:",
        ),
        (
            PERPENDICULAR_DATA,
            f"Write the equation of the line through (2, {MINUS}2) that is perpendicular to this "
            "line, in slope-intercept form:",
        ),
        (
            LineQuestionData(
                Line(0, 1, 7),
                HORIZONTAL,
                HORIZONTAL,
                ((3, 7),),
                reference=X_AXIS,
                relation=PARALLEL,
            ),
            "Write the equation of the line through this point that is parallel to the x-axis:",
        ),
        # a table names the line by its points, a graph is "this line", and point-slope form
        # from either names the point it goes through
        (
            LineQuestionData(Line(1, 2, 6), TABLE, SLOPE, ((2, 2),), table_xs=(-4, 2, 4, 8)),
            "Find the slope of the line through the points in this table:",
        ),
        (
            LineQuestionData(Line(1, 2, 6), TABLE, ZERO, ((2, 2),), table_xs=(-4, 2, 4, 8)),
            "Find the zero of the linear function in this table:",
        ),
        (
            LineQuestionData(Line(1, 2, 6), GRAPH, Y_INTERCEPT, ((2, 2), (-4, 5)), as_point=True),
            "Find the y-intercept of this line as an ordered pair:",
        ),
        (
            LineQuestionData(Line(1, 2, 6), TABLE, POINT_SLOPE, ((4, 1),), table_xs=(-4, 2, 4, 8)),
            "Write the equation of the line through the points in this table in point-slope "
            "form, using the point (4, 1):",
        ),
        (
            LineQuestionData(Line(1, 2, 6), GRAPH, POINT_SLOPE, ((-4, 5), (2, 2))),
            f"Write the equation of this line in point-slope form, using the point ({MINUS}4, 5):",
        ),
        (
            LineQuestionData(Line(1, 0, 3), GRAPH, VERTICAL, ((3, 2), (3, -4))),
            "Write the equation of this line:",
        ),
        # graphing a line from each kind of given, and completing a table
        (LineQuestionData(Line(2, -3, -3), SLOPE_INTERCEPT, GRAPH), "Graph this equation:"),
        (LineQuestionData(Line(1, 0, 3), VERTICAL, GRAPH), "Graph this equation:"),
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, GRAPH, ((-4, 5), (4, -1))),
            "Graph the line through these points:",
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, GRAPH, ((-4, 5),)),
            "Graph the line with this point and slope:",
        ),
        (
            LineQuestionData(Line(2, -3, -3), SLOPE_AND_INTERCEPT, GRAPH),
            "Graph the line with this slope and y-intercept:",
        ),
        (
            LineQuestionData(Line(1, 2, 2), INTERCEPTS, GRAPH),
            "Graph the line with these intercepts:",
        ),
        (
            LineQuestionData(Line(1, 2, 6), STANDARD, TABLE, table_xs=(-4, 2, 4, 8)),
            "Complete the table for this equation:",
        ),
        (
            LineQuestionData(Line(1, 2, 6), GRAPH, TABLE, ((2, 2), (-4, 5)), table_xs=(-4, 4)),
            "Complete the table for this line:",
        ),
        # a graph or table to choose, asked as STAAR asks it
        (
            LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True),
            "Which graph represents the line with this slope and y-intercept?",
        ),
        (
            LineQuestionData(Line(4, 1, -14), POINT_SLOPE, GRAPH, ((-3, -2),), chosen=True),
            "Which graph represents this equation?",
        ),
        (
            LineQuestionData(Line(1, 2, 6), STANDARD, TABLE, table_xs=(-4, 2), chosen=True),
            "Which table represents this equation?",
        ),
        (
            LineQuestionData(Line(1, 2, 6), GRAPH, TABLE, ((2, 2), (-4, 5)), chosen=True),
            "Which table represents this line?",
        ),
        # a statement asked too
        (
            LineQuestionData(
                Line(1, 0, -4), TWO_POINTS, VERTICAL, ((-4, 9), (-4, 5)), statement=Statement.SLOPE
            ),
            "Write the equation of the line through these points, and give its slope:",
        ),
        (
            LineQuestionData(
                Line(1, 0, 9), POINT_AND_SLOPE, VERTICAL, ((9, 10),), statement=Statement.X_AXIS
            ),
            "Write the equation of the line with this point and slope, and say whether it is "
            "parallel or perpendicular to the x-axis:",
        ),
        (
            LineQuestionData(
                Line(1, 0, 5),
                VERTICAL,
                VERTICAL,
                ((5, 4),),
                reference=Y_AXIS,
                relation=PARALLEL,
                statement=Statement.SLOPE,
            ),
            "Write the equation of the line through this point that is parallel to the y-axis, "
            "and give its slope:",
        ),
    ],
)
def test_instruction(data: LineQuestionData, text: str) -> None:
    """What to find comes first, ending with a colon, with the line shown under it."""
    assert instruction(data) == text


@pytest.mark.parametrize(
    ("data", "pieces"),
    [
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, SLOPE, ((-4, 5), (4, -1))),
            (f"({MINUS}4, 5) and (4, {MINUS}1)",),
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, Y_INTERCEPT, ((-4, 5),)),
            (f"point ({MINUS}4, 5), slope {MINUS}", Fraction(3, 4)),
        ),
        (
            LineQuestionData(
                Line(3, 4, 8), POINT_AND_SLOPE, Y_INTERCEPT, ((-4, 5),), numbers=DECIMAL
            ),
            (f"point ({MINUS}4, 5), slope {MINUS}0.75",),
        ),
        # an equation, in its notation and number style, through its point in point-slope form
        (
            LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE, function="g"),
            (f"g(x) = {MINUS}", Fraction(3, 4), "x + 2"),
        ),
        (
            LineQuestionData(Line(3, 4, 8), POINT_SLOPE, SLOPE, ((-4, 5),), numbers=DECIMAL),
            (f"y {MINUS} 5 = {MINUS}0.75(x + 4)",),
        ),
        (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), (f"x = {MINUS}4",)),
        (
            LineQuestionData(
                Line(3, 4, 8), POINT_SLOPE, SLOPE_INTERCEPT, ((-4, 5),), solved_for_y=True
            ),
            (f"y = {MINUS}", Fraction(3, 4), "(x + 4) + 5"),
        ),
        # a vertical line's undefined slope
        (
            LineQuestionData(Line(1, 0, 3), POINT_AND_SLOPE, VERTICAL, ((3, 7),)),
            ("point (3, 7), slope undefined",),
        ),
        # the line the answer is parallel or perpendicular to, in the given form, or for an axis,
        # the point
        (PERPENDICULAR_DATA, ("y = ", Fraction(2, 5), "x + 2")),
        (
            LineQuestionData(
                Line(2, 3, 18),
                STANDARD,
                STANDARD,
                ((3, 4),),
                reference=Line(2, 3, 6),
                relation=PARALLEL,
            ),
            ("2x + 3y = 6",),
        ),
        (
            LineQuestionData(
                Line(0, 1, 7),
                HORIZONTAL,
                HORIZONTAL,
                ((3, 7),),
                reference=X_AXIS,
                relation=PARALLEL,
            ),
            ("(3, 7)",),
        ),
        # the slope and y-intercept, and the intercepts, in the question's number style
        (
            LineQuestionData(Line(2, -3, -3), SLOPE_AND_INTERCEPT, GRAPH),
            ("slope ", Fraction(2, 3), ", y-intercept 1"),
        ),
        (
            LineQuestionData(Line(1, -2, -2), SLOPE_AND_INTERCEPT, GRAPH, numbers=DECIMAL),
            ("slope 0.5, y-intercept 1",),
        ),
        (
            LineQuestionData(Line(2, -1, -5), INTERCEPTS, GRAPH, numbers=DECIMAL),
            (f"x-intercept {MINUS}2.5, y-intercept 5",),
        ),
        (
            LineQuestionData(Line(1, 2, 2), INTERCEPTS, GRAPH),
            ("x-intercept 2, y-intercept 1",),
        ),
        # a table and a graph are drawn, not written
        (LineQuestionData(Line(1, 2, 6), TABLE, SLOPE, ((2, 2),), table_xs=(-4, 2, 4, 8)), ()),
        (LineQuestionData(Line(1, 2, 6), GRAPH, SLOPE, ((2, 2), (-4, 5))), ()),
    ],
)
def test_given_pieces(data: LineQuestionData, pieces: Pieces) -> None:
    """
    Points and a point and slope are listed; a table and a graph are drawn, so have none; any
    other form is the line's equation. With a relation, it's the other line, or the point for an
    axis.
    """
    assert given_pieces(data) == pieces


@pytest.mark.parametrize(
    ("data", "cells"),
    [
        # a half in the question's number style: stacked in a fraction question, a decimal in
        # a decimal one
        (
            LineQuestionData(Line(3, -2, 1), TABLE, SLOPE, ((-3, -5),), table_xs=(-3, -1, 2, 5, 6)),
            (
                ("x", (f"{MINUS}3",), (f"{MINUS}1",), ("2",), ("5",), ("6",)),
                (
                    "y",
                    (f"{MINUS}5",),
                    (f"{MINUS}2",),
                    (Fraction(5, 2),),
                    ("7",),
                    (Fraction(17, 2),),
                ),
            ),
        ),
        (
            LineQuestionData(
                Line(3, -2, 1),
                TABLE,
                SLOPE,
                ((-3, -5),),
                numbers=DECIMAL,
                table_xs=(-3, -1, 2, 5, 6),
                table_across=True,
            ),
            (
                ("x", (f"{MINUS}3",), (f"{MINUS}1",), ("2",), ("5",), ("6",)),
                ("y", (f"{MINUS}5",), (f"{MINUS}2",), ("2.5",), ("7",), ("8.5",)),
            ),
        ),
        # a table to complete leaves out the cells its blanks say
        (
            LineQuestionData(
                Line(1, 2, 6), STANDARD, TABLE, table_xs=(-4, 2, 4, 8), table_blanks=(1, 1, 0, 1)
            ),
            (("x", (f"{MINUS}4",), ("2",), None, ("8",)), ("y", None, None, ("1",), None)),
        ),
    ],
)
def test_table_cells(data: LineQuestionData, cells: tuple[tuple[object, ...], ...]) -> None:
    """
    Each row's x and the line's y there, headed x and y, as pieces in the question's number
    style, with minus signs, and ``None`` in a cell a table to complete leaves out.
    """
    assert table_cells(data) == cells


def test_filled_table_cells() -> None:
    """The answer key fills every cell of a table to complete."""
    data = LineQuestionData(
        Line(1, 2, 6), STANDARD, TABLE, table_xs=(-4, 2, 4, 8), table_blanks=(1, 1, 0, 1)
    )
    assert table_cells(data, filled=True) == (
        ("x", (f"{MINUS}4",), ("2",), ("4",), ("8",)),
        ("y", ("5",), ("2",), ("1",), (f"{MINUS}1",)),
    )


@pytest.mark.parametrize(
    ("data", "choice", "pieces"),
    [
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
            Fraction(-4, 3),
            (MINUS, Fraction(4, 3)),
        ),
        (LineQuestionData(Line(0, 1, 3), HORIZONTAL, SLOPE), None, ("undefined",)),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT, as_point=True),
            (Fraction(0), Fraction(2)),
            ("(0, 2)",),
        ),
        # the slope and y-intercept as STAAR's statements
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
            (Fraction(-3, 4), Fraction(2)),
            (f"The slope is {MINUS}", Fraction(3, 4), ", and the y-intercept is 2."),
        ),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT, numbers=DECIMAL),
            (Fraction(-3, 4), Fraction(5, 2)),
            (f"The slope is {MINUS}0.75, and the y-intercept is 2.5.",),
        ),
        # an equation, in the question's number style, through its own point in point-slope form
        (
            PERPENDICULAR_DATA,
            Equation(Line(5, -2, 14), SLOPE_INTERCEPT),
            ("y = ", Fraction(5, 2), f"x {MINUS} 7"),
        ),
        (
            LineQuestionData(Line(1, -4, -12), TWO_POINTS, SLOPE_INTERCEPT, numbers=DECIMAL),
            Equation(Line(4, -1, -18), SLOPE_INTERCEPT),
            ("y = 4x + 18",),
        ),
        (
            LineQuestionData(Line(8, 9, -78), SLOPE_INTERCEPT, POINT_SLOPE, ((-3, -6),)),
            Equation(Line(8, 9, 78), POINT_SLOPE, (3, 6)),
            (f"y {MINUS} 6 = {MINUS}", Fraction(8, 9), f"(x {MINUS} 3)"),
        ),
        (
            LineQuestionData(Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),)),
            Equation(Line(1, 0, 3), VERTICAL),
            ("x = 3",),
        ),
    ],
)
def test_choice_pieces(data: LineQuestionData, choice: LineAnswer, pieces: Pieces) -> None:
    """A choice is written like an answer; a slope and y-intercept is a statement."""
    assert choice_pieces(data, choice) == pieces


VERTICAL_STATEMENT = LineQuestionData(
    Line(1, 0, -4), TWO_POINTS, VERTICAL, ((-4, 9), (-4, 5)), statement=Statement.SLOPE
)


@pytest.mark.parametrize(
    ("data", "choice", "pieces"),
    [
        (
            VERTICAL_STATEMENT,
            Stated(Equation(Line(1, 0, -4), VERTICAL), None),
            (f"The equation of the line is x = {MINUS}4, and the slope is undefined.",),
        ),
        (
            VERTICAL_STATEMENT,
            Stated(Equation(Line(0, 1, -4), HORIZONTAL), Fraction(0)),
            (f"The equation of the line is y = {MINUS}4, and the slope is 0.",),
        ),
        (
            replace(VERTICAL_STATEMENT, statement=Statement.X_AXIS),
            Stated(Equation(Line(1, 0, -4), VERTICAL), Relation.PERPENDICULAR),
            (
                f"The equation of the line is x = {MINUS}4, and the line is perpendicular to "
                "the x-axis.",
            ),
        ),
    ],
)
def test_statement_choice_pieces(
    data: LineQuestionData, choice: LineAnswer, pieces: Pieces
) -> None:
    """A statement choice is a sentence, as STAAR's A.2(G) options are."""
    assert choice_pieces(data, choice) == pieces


def test_choice_pieces_errors() -> None:
    """A graph or table to choose is drawn, so has no pieces."""
    data = LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True)
    with pytest.raises(ValueError) as error:
        choice_pieces(data, Equation(Line(2, 3, 12), GRAPH))
    assert str(error.value) == "A graph to choose is drawn, not written."


@pytest.mark.parametrize(
    ("line", "cells"),
    [
        # y = 2x - 3
        (
            Line(2, -1, 3),
            (("x", ("0",), ("1",), ("3",)), ("y", (f"{MINUS}3",), (f"{MINUS}1",), ("3",))),
        ),
        # x = 2.5: 2.5 in every row of x, with the x-values as its y-values
        (Line(2, 0, 5), (("x", ("2.5",), ("2.5",), ("2.5",)), ("y", ("0",), ("1",), ("3",)))),
    ],
)
def test_choice_table_cells(line: Line, cells: tuple[tuple[object, ...], ...]) -> None:
    """Every table to choose has the question's x-values, in the question's number style."""
    data = LineQuestionData(
        Line(2, -1, 3), SLOPE_INTERCEPT, TABLE, numbers=DECIMAL, table_xs=(0, 1, 3), chosen=True
    )
    assert choice_table_cells(data, line) == cells


@pytest.mark.parametrize(
    ("data", "labels"),
    [
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
            ("Slope", "y-intercept"),
        ),
        (VERTICAL_STATEMENT, ("Equation", "Slope")),
        (
            replace(VERTICAL_STATEMENT, statement=Statement.X_AXIS),
            ("Equation", "Parallel or perpendicular"),
        ),
        (replace(VERTICAL_STATEMENT, statement=None), None),
    ],
)
def test_blank_labels(data: LineQuestionData, labels: tuple[str, str] | None) -> None:
    """Two answers get two labelled blanks; one answer gets none."""
    assert blank_labels(data) == labels


@pytest.mark.parametrize(
    ("data", "answer", "tile"),
    [
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
            (MINUS, Fraction(3, 4)),
            (MINUS, Fraction(3, 4)),
        ),
        # the slope and y-intercept: listed in the key, labelled on a tile
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
            (f"slope {MINUS}", Fraction(3, 4), ", y-intercept 2"),
            (f"m = {MINUS}", Fraction(3, 4), ", b = 2"),
        ),
        (
            LineQuestionData(Line(0, 5, -18), HORIZONTAL, SLOPE_AND_Y_INTERCEPT, numbers=DECIMAL),
            (f"slope 0, y-intercept {MINUS}3.6",),
            (f"m = 0, b = {MINUS}3.6",),
        ),
        # an equation: the same in the key and on a tile
        (
            LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD),
            (f"3x {MINUS} 4y = {MINUS}5",),
            (f"3x {MINUS} 4y = {MINUS}5",),
        ),
        # a statement: written short in the key and on a tile
        (
            VERTICAL_STATEMENT,
            (f"x = {MINUS}4, slope undefined",),
            (f"x = {MINUS}4, slope undefined",),
        ),
        (
            LineQuestionData(
                Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),), statement=Statement.X_AXIS
            ),
            ("y = 7, parallel to the x-axis",),
            ("y = 7, parallel to the x-axis",),
        ),
    ],
)
def test_answer_and_tile_answer_pieces(
    data: LineQuestionData, answer: Pieces, tile: Pieces
) -> None:
    """The key lists both numbers of a slope and y-intercept, and a tile labels them."""
    assert (answer_pieces(data), tile_answer_pieces(data)) == (answer, tile)
