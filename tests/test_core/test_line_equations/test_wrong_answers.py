"""
Tests for the wrong answers to questions about a line: STAAR's mistakes first, making a balanced
set of four with the answer, then the next mistake or nearby numbers where one repeats.
"""

from collections.abc import Iterator
from dataclasses import replace
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
)
from core.line_equations.wrong_answers import mistake_sets, wrong_answers, wrong_lines
from core.written_numbers import NumberStyle

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


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # 3x + 4y = 8, slope -3/4: the reciprocal, the sign, both
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
            (Fraction(-4, 3), Fraction(3, 4), Fraction(4, 3)),
        ),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, RATE_OF_CHANGE),
            (Fraction(-4, 3), Fraction(3, 4), Fraction(4, 3)),
        ),
        # y = x + 2: a slope of 1 is its own reciprocal, so the intercepts fill in
        (
            LineQuestionData(Line(1, -1, -2), SLOPE_INTERCEPT, SLOPE),
            (Fraction(-1), Fraction(2), Fraction(-2)),
        ),
        # x = -4: undefined, against 0, its number and the opposite
        (
            LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE),
            (Fraction(0), Fraction(-4), Fraction(4)),
        ),
        # y = 3: 0, against undefined, its number and the opposite
        (LineQuestionData(Line(0, 1, 3), HORIZONTAL, SLOPE), (None, Fraction(3), Fraction(-3))),
        # y-intercept 2: the x-intercept, the sign, both
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT),
            (Fraction(8, 3), Fraction(-2), Fraction(-8, 3)),
        ),
        # x-intercept or zero 8/3: the y-intercept, the sign, both
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT),
            (Fraction(2), Fraction(-8, 3), Fraction(-2)),
        ),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, ZERO),
            (Fraction(2), Fraction(-8, 3), Fraction(-2)),
        ),
        # y = 2x through the origin: both intercepts 0, so the slope, then 1
        (
            LineQuestionData(Line(2, -1, 0), SLOPE_INTERCEPT, Y_INTERCEPT),
            (Fraction(2), Fraction(-2), Fraction(1)),
        ),
        # intercepts as points: x and y exchanged, and the other intercept
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True),
            (
                (Fraction(2), Fraction(0)),
                (Fraction(0), Fraction(8, 3)),
                (Fraction(8, 3), Fraction(0)),
            ),
        ),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT, as_point=True),
            (
                (Fraction(0), Fraction(8, 3)),
                (Fraction(0), Fraction(2)),
                (Fraction(2), Fraction(0)),
            ),
        ),
        # y = 2x as a point: nearby points stay on the y-axis, so none is ruled out at sight
        (
            LineQuestionData(Line(2, -1, 0), SLOPE_INTERCEPT, Y_INTERCEPT, as_point=True),
            (
                (Fraction(0), Fraction(1)),
                (Fraction(0), Fraction(-1)),
                (Fraction(0), Fraction(2)),
            ),
        ),
        # slope and y-intercept: the reciprocal slope, the x-intercept, both
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
            (
                (Fraction(-4, 3), Fraction(2)),
                (Fraction(-3, 4), Fraction(8, 3)),
                (Fraction(-4, 3), Fraction(8, 3)),
            ),
        ),
        # decimals pass over 5/3 and -10/3, which don't terminate, so 8/5 comes in
        (
            LineQuestionData(Line(3, -5, -10), SLOPE_INTERCEPT, SLOPE, numbers=DECIMAL),
            (Fraction(-3, 5), Fraction(2), Fraction(8, 5)),
        ),
        # as A.2 2019 Q6, y = 1/4x + 3 through (-4, 2) and (12, 6): the sign slip in
        # b = y₁ - m·x₁, y = 1/4x + 1; the reciprocal with each y-intercept, y = 4x + 3 and
        # y = 4x + 1
        (
            LineQuestionData(Line(1, -4, -12), TWO_POINTS, SLOPE_INTERCEPT, ((-4, 2), (12, 6))),
            (
                Equation(Line(1, -4, -4), SLOPE_INTERCEPT),
                Equation(Line(4, -1, -3), SLOPE_INTERCEPT),
                Equation(Line(4, -1, -1), SLOPE_INTERCEPT),
            ),
        ),
        # as A.2 2018 Q39, y = -5/2x + 3 through (2, -2), perpendicular to y = 2/5x + 2: the
        # sign slip, y = -5/2x - 7; the slope only inverted with each y-intercept, y = 5/2x + 3
        # and y = 5/2x - 7
        (
            LineQuestionData(
                Line(5, 2, 6),
                SLOPE_INTERCEPT,
                SLOPE_INTERCEPT,
                ((2, -2),),
                reference=Line(2, -5, -10),
                relation=PERPENDICULAR,
            ),
            (
                Equation(Line(5, 2, -14), SLOPE_INTERCEPT),
                Equation(Line(5, -2, -6), SLOPE_INTERCEPT),
                Equation(Line(5, -2, 14), SLOPE_INTERCEPT),
            ),
        ),
        # as A.2 2021 Q19, 8x + 3y = 45 through (6, -1), parallel to 8x + 3y = 15: through
        # (-6, 1), 8x + 3y = -45; the perpendicular slope through each point, 3x - 8y = 26 and
        # 3x - 8y = -26, so C's sign doesn't mark the answer out
        (
            LineQuestionData(
                Line(8, 3, 45),
                STANDARD,
                STANDARD,
                ((6, -1),),
                reference=Line(8, 3, 15),
                relation=PARALLEL,
            ),
            (
                Equation(Line(8, 3, -45), STANDARD),
                Equation(Line(3, -8, 26), STANDARD),
                Equation(Line(3, -8, -26), STANDARD),
            ),
        ),
        # y = 3x through (1, 3): (-1, -3) is on the line too, and y + 3 = 3(x + 1) is right, so
        # (3, 1) takes its place
        (
            LineQuestionData(Line(3, -1, 0), POINT_AND_SLOPE, POINT_SLOPE, ((1, 3),)),
            (
                Equation(Line(3, -1, 8), POINT_SLOPE, (3, 1)),
                Equation(Line(1, -3, -8), POINT_SLOPE, (1, 3)),
                Equation(Line(1, -3, 0), POINT_SLOPE, (3, 1)),
            ),
        ),
        # as A.2 2026 Q46, y + 6 = -8/9(x + 3), parallel to y = -8/9x + 4: the point's signs
        # flipped, y - 6 = -8/9(x - 3); the perpendicular slope, y + 6 = 9/8(x + 3); both
        (
            LineQuestionData(
                Line(8, 9, -78),
                SLOPE_INTERCEPT,
                POINT_SLOPE,
                ((-3, -6),),
                reference=Line(8, 9, 36),
                relation=PARALLEL,
            ),
            (
                Equation(Line(8, 9, 78), POINT_SLOPE, (3, 6)),
                Equation(Line(9, -8, 21), POINT_SLOPE, (-3, -6)),
                Equation(Line(9, -8, -21), POINT_SLOPE, (3, 6)),
            ),
        ),
        # point-slope form through the first of two points, (-4, 5), on 3x + 4y = 8: through
        # (4, -5); the reciprocal through (-4, 5); both
        (
            LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))),
            (
                Equation(Line(3, 4, -8), POINT_SLOPE, (4, -5)),
                Equation(Line(4, 3, -1), POINT_SLOPE, (-4, 5)),
                Equation(Line(4, 3, 1), POINT_SLOPE, (4, -5)),
            ),
        ),
        # 3x - y = 0 through (1, 3): C = 0, so each slope takes the y-intercepts 0 and 6, as in
        # slope-intercept form, and C = 0 is in two of the four
        (
            LineQuestionData(Line(3, -1, 0), POINT_AND_SLOPE, STANDARD, ((1, 3),)),
            (
                Equation(Line(3, -1, -6), STANDARD),
                Equation(Line(1, -3, 0), STANDARD),
                Equation(Line(1, -3, -18), STANDARD),
            ),
        ),
        # y = x + 2 through (1, 3): a slope of 1 is its own reciprocal, so the sign comes next
        (
            LineQuestionData(Line(1, -1, -2), POINT_AND_SLOPE, SLOPE_INTERCEPT, ((1, 3),)),
            (
                Equation(Line(1, -1, -4), SLOPE_INTERCEPT),
                Equation(Line(1, 1, 2), SLOPE_INTERCEPT),
                Equation(Line(1, 1, 4), SLOPE_INTERCEPT),
            ),
        ),
        # y = -7/3x - 14/3 in standard form, with no point: the slope's and the intercept's
        # signs, without the reciprocal, whose coefficients would give the answer away
        (
            LineQuestionData(Line(7, 3, -14), SLOPE_INTERCEPT, STANDARD),
            (
                Equation(Line(7, 3, 14), STANDARD),
                Equation(Line(7, -3, 14), STANDARD),
                Equation(Line(7, -3, -14), STANDARD),
            ),
        ),
        # 7x + 4y = -28 in slope-intercept form, in decimals: y = -1.75x + 7, y = 1.75x - 7,
        # y = 1.75x + 7
        (
            LineQuestionData(Line(7, 4, -28), STANDARD, SLOPE_INTERCEPT, numbers=DECIMAL),
            (
                Equation(Line(7, 4, 28), SLOPE_INTERCEPT),
                Equation(Line(7, -4, 28), SLOPE_INTERCEPT),
                Equation(Line(7, -4, -28), SLOPE_INTERCEPT),
            ),
        ),
        # as A.2 2017 Q36, y = 7 through (3, 7): x = and y = confused, the point's other number
        (
            LineQuestionData(Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),)),
            (
                Equation(Line(1, 0, 7), VERTICAL),
                Equation(Line(0, 1, 3), HORIZONTAL),
                Equation(Line(1, 0, 3), VERTICAL),
            ),
        ),
        # x = 3 through (3, 3): the point's numbers are the same, so nearby lines fill in
        (
            LineQuestionData(Line(1, 0, 3), TWO_POINTS, VERTICAL, ((3, 3), (3, -2))),
            (
                Equation(Line(0, 1, 3), HORIZONTAL),
                Equation(Line(1, 0, 4), VERTICAL),
                Equation(Line(1, 0, 2), VERTICAL),
            ),
        ),
    ],
)
def test_wrong_answers(data: LineQuestionData, expected: tuple[LineAnswer, ...]) -> None:
    """Three different wrong answers, none the answer, in the order of the mistakes."""
    assert wrong_answers(data, 3) == expected


# y = 3x + 1 in a table stepping by 2 from x = 1: slope 3, y-intercept 1, first row (1, 4)
EVEN_TABLE = LineQuestionData(Line(3, -1, -1), TABLE, SLOPE, ((1, 4),), table_xs=(1, 3, 5, 7))


@pytest.mark.parametrize(
    ("data", "mistakes", "expected"),
    [
        # the commonest mistakes: the reciprocal, the sign, both
        (EVEN_TABLE, 0, (Fraction(1, 3), Fraction(-3), Fraction(-1, 3))),
        # the change in y per row, 6, as the slope, and the signs (8.5 2024 Q34 C)
        (EVEN_TABLE, 1, (Fraction(-3), Fraction(6), Fraction(-6))),
        # the first row's y, 4, as the y-intercept (8.5 2026 Q4 A)
        (replace(EVEN_TABLE, asked=Y_INTERCEPT), 1, (Fraction(-1), Fraction(4), Fraction(-4))),
        (
            replace(EVEN_TABLE, asked=Y_INTERCEPT, as_point=True),
            1,
            ((Fraction(0), Fraction(-1)), (Fraction(0), Fraction(4)), (Fraction(0), Fraction(-4))),
        ),
        # an equation: each of the slope and the change per row with each of b and y₁ + m·x₁
        (
            replace(EVEN_TABLE, asked=SLOPE_INTERCEPT),
            1,
            (
                Equation(Line(3, -1, -7), SLOPE_INTERCEPT),
                Equation(Line(6, -1, -1), SLOPE_INTERCEPT),
                Equation(Line(6, -1, -7), SLOPE_INTERCEPT),
            ),
        ),
    ],
)
def test_second_set_of_mistakes(
    data: LineQuestionData, mistakes: int, expected: tuple[LineAnswer, ...]
) -> None:
    """A table's second set takes a row's change as the slope, or its first y as b."""
    assert wrong_answers(data, 3, mistakes) == expected


@pytest.mark.parametrize(
    ("data", "sets"),
    [
        (EVEN_TABLE, 2),
        (replace(EVEN_TABLE, asked=SLOPE_INTERCEPT), 2),
        (replace(EVEN_TABLE, asked=Y_INTERCEPT), 2),
        # x unevenly spaced: a row's change isn't one number
        (replace(EVEN_TABLE, table_xs=(1, 2, 5, 7)), 1),
        # the first row at x = 0 shows the y-intercept
        (replace(EVEN_TABLE, asked=Y_INTERCEPT, table_xs=(0, 2, 4)), 1),
        (replace(EVEN_TABLE, asked=X_INTERCEPT), 1),
        # a horizontal line in a table
        (LineQuestionData(Line(0, 1, 3), TABLE, SLOPE, ((1, 3),), table_xs=(1, 3, 5)), 1),
        (LineQuestionData(Line(3, -1, -1), TWO_POINTS, SLOPE, ((1, 4), (3, 10))), 1),
        # graphs and tables to choose: STAAR's own wrong graphs, or the writing sheet's mistakes
        (LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True), 2),
        (LineQuestionData(Line(1, 0, -4), VERTICAL, GRAPH, chosen=True), 1),
        (LineQuestionData(Line(0, 2, 5), HORIZONTAL, TABLE, chosen=True), 1),
    ],
)
def test_mistake_sets(data: LineQuestionData, sets: int) -> None:
    """Two balanced sets where STAAR has two ways to go wrong, one otherwise."""
    assert mistake_sets(data) == sets


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # as A.2 2018 Q32, x = -4 through (-4, 9): each of x = -4 and y = -4, x = and y =
        # confused, with each of undefined and 0
        (
            LineQuestionData(
                Line(1, 0, -4), TWO_POINTS, VERTICAL, ((-4, 9), (-4, 5)), statement=Statement.SLOPE
            ),
            (
                Stated(Equation(Line(1, 0, -4), VERTICAL), Fraction(0)),
                Stated(Equation(Line(0, 1, -4), HORIZONTAL), None),
                Stated(Equation(Line(0, 1, -4), HORIZONTAL), Fraction(0)),
            ),
        ),
        # as A.2 2026 Q14, y = 7 through (3, 7): with parallel and perpendicular to the x-axis
        (
            LineQuestionData(
                Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),), statement=Statement.X_AXIS
            ),
            (
                Stated(Equation(Line(0, 1, 7), HORIZONTAL), PERPENDICULAR),
                Stated(Equation(Line(1, 0, 7), VERTICAL), PARALLEL),
                Stated(Equation(Line(1, 0, 7), VERTICAL), PERPENDICULAR),
            ),
        ),
    ],
)
def test_statement_wrong_answers(data: LineQuestionData, expected: tuple[LineAnswer, ...]) -> None:
    """Each of two equations with each of two slopes or directions, balanced with the answer."""
    assert wrong_answers(data, 3) == expected


def first_wrong_lines(data: LineQuestionData, mistakes: int) -> tuple[Line, ...]:
    """Return the first three lines ``wrong_lines`` yields that differ from the answer's."""
    lines: list[Line] = []
    candidates: Iterator[Line] = wrong_lines(data, mistakes)
    while len(lines) < 3:
        line = next(candidates)
        if line != data.answer and line not in lines:
            lines.append(line)
    return tuple(lines)


@pytest.mark.parametrize(
    ("data", "mistakes", "expected"),
    [
        # as A.3 2021 Q41, crossing at -1 and 5: at 1 and -5, at 5 and -1, at -5 and 1
        (
            LineQuestionData(Line(5, -1, -5), INTERCEPTS, GRAPH, chosen=True),
            0,
            (Line(5, -1, 5), Line(1, -5, 5), Line(1, -5, -5)),
        ),
        # as A.3 2025 Q35, y = 2/3x + 4: slope -2/3 through (0, 4), slopes 2/3 and -2/3 through
        # (4, 0)
        (
            LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True),
            0,
            (Line(2, 3, 12), Line(2, -3, 8), Line(2, 3, 8)),
        ),
        # as A.3 2022 Q32, y = -4(x + 3) - 2: slope 4 through (-3, -2), slopes -4 and 4 through
        # (-3, 2)
        (
            LineQuestionData(Line(4, 1, -14), POINT_SLOPE, GRAPH, ((-3, -2),), chosen=True),
            0,
            (Line(4, -1, -10), Line(4, 1, -10), Line(4, -1, -14)),
        ),
        # as A.3 2019 Q7, 6x - 5y = 15, slope 6/5 and y-intercept -3: the signs of each
        (
            LineQuestionData(Line(6, -5, 15), STANDARD, GRAPH, chosen=True),
            0,
            (Line(6, 5, -15), Line(6, -5, -15), Line(6, 5, 15)),
        ),
        # x = -4: y = -4, x = 4, y = 4
        (
            LineQuestionData(Line(1, 0, -4), VERTICAL, GRAPH, chosen=True),
            0,
            (Line(0, 1, -4), Line(1, 0, 4), Line(0, 1, 4)),
        ),
        # y = 2.5: x = 2.5, y = -2.5, x = -2.5
        (
            LineQuestionData(Line(0, 2, 5), HORIZONTAL, TABLE, chosen=True),
            0,
            (Line(2, 0, 5), Line(0, 2, -5), Line(2, 0, -5)),
        ),
        # the writing sheet's mistakes, y = 2x - 3: slopes 2 and 1/2 with y-intercepts -3 and 3
        (
            LineQuestionData(Line(2, -1, 3), SLOPE_INTERCEPT, TABLE, chosen=True),
            1,
            (Line(2, -1, -3), Line(1, -2, 6), Line(1, -2, -6)),
        ),
    ],
)
def test_wrong_lines(data: LineQuestionData, mistakes: int, expected: tuple[Line, ...]) -> None:
    """STAAR's wrong graphs use the answer's numbers, signs flipped or on the other axis."""
    assert first_wrong_lines(data, mistakes) == expected


@pytest.mark.parametrize(
    ("data", "mistakes", "message"),
    [
        (
            LineQuestionData(Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, chosen=True),
            0,
            "A graph or table to choose takes its wrong lines from wrong_lines.",
        ),
        (
            LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
            1,
            "This question has no set of mistakes numbered 1.",
        ),
    ],
)
def test_wrong_answers_errors(data: LineQuestionData, mistakes: int, message: str) -> None:
    """Graphs and tables are chosen through wrong_lines; a missing set is refused."""
    with pytest.raises(ValueError) as error:
        wrong_answers(data, 3, mistakes)
    assert str(error.value) == message
