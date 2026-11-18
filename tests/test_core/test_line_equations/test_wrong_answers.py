"""
Tests for the wrong answers to questions about a line: STAAR's mistakes first, making a balanced
set of four with the answer, then the next mistake or nearby numbers where one repeats.
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
    NumberStyle,
    Relation,
)
from core.line_equations.wrong_answers import wrong_answers

SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, X_INTERCEPT, ZERO, SLOPE_AND_Y_INTERCEPT = LineFeature
SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, POINT_AND_SLOPE, TWO_POINTS, VERTICAL, HORIZONTAL = LineForm
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
        # as A.2 2017 Q36, y = 7 through (3, 7): the point's other number, x = and y = confused
        (
            LineQuestionData(Line(0, 1, 7), POINT_AND_SLOPE, HORIZONTAL, ((3, 7),)),
            (
                Equation(Line(0, 1, 3), HORIZONTAL),
                Equation(Line(1, 0, 7), VERTICAL),
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
