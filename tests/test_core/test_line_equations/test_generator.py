"""
Tests for the line question generator: questions about a line's features, then questions that
ask for its equation.

The first test of each scripts ``random``, so each case lists the questions that must be
produced:

- ``random.shuffle`` reverses the list, so the pairs of a form and a feature are dealt in their
  order: each form given with each feature asked, in turn.
- ``random.choice`` returns the picks listed in the case, in order. For each question: its number
  style; for an intercept, whether it's asked as a point; for Algebra I slope-intercept form,
  whether it's in function notation, then its name; for two points in Algebra I, which way the
  line runs; for a sloped line, whether it passes through the origin; then the slope and
  y-intercept, or a vertical or horizontal line's number. A pick that is not among its call's
  items raises ``ValueError``.
- ``random.sample`` returns the points shown, as listed.

For equations, ``random.choice`` returns, for each question: its number style; for point-slope
form given, whether it's solved for y; for a sloped line, whether it passes through the origin,
then, when it shows one point and doesn't, whether that point is on the x-axis; then the slope
and y-intercept, or a vertical or horizontal line's number; then, for a sloped line with a
relation, the y-intercept of the line it's parallel or perpendicular to, and that line's form.

The second test of each runs the generator for real and checks every question against the rules
it promises.
"""

from fractions import Fraction
from math import gcd

import pytest

from core.line_equations.data import (
    EQUATION_FORMS,
    EQUATION_GIVENS,
    X_AXIS,
    Y_AXIS,
    Equation,
    Line,
    LineFeature,
    LineForm,
    LineQuestion,
    LineQuestionData,
    NumberStyle,
    Relation,
    answer_of,
    feature_value,
)
from core.line_equations.generator import (
    can_write,
    count_possible_equations,
    count_possible_lines,
    generate_equation_questions,
    generate_line_questions,
)
from core.line_equations.representation import terminates
from core.question import FreeResponse, MultipleChoice
from tests.helpers import choice_returns, reverse_shuffle, sample_returns

SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, X_INTERCEPT, ZERO, SLOPE_AND_Y_INTERCEPT = LineFeature
SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, POINT_AND_SLOPE, TWO_POINTS, VERTICAL, HORIZONTAL = LineForm
FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle
PARALLEL, PERPENDICULAR = Relation


@pytest.mark.parametrize(
    (
        "givens",
        "features",
        "whole_intercepts",
        "number_styles",
        "chosen",
        "sampled",
        "expected",
    ),
    [
        (
            # y = 3/4x + 5/4, not in function notation
            [SLOPE_INTERCEPT],
            [SLOPE],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, False, False, Fraction(3, 4), Fraction(5, 4)],
            [],
            [LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, SLOPE)],
        ),
        (
            # two points on y = 3x, a line through the origin
            [TWO_POINTS],
            [SLOPE],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, "sloped", True, Fraction(3), Fraction(0)],
            [[(1, 3), (-2, -6)]],
            [LineQuestionData(Line(3, -1, 0), TWO_POINTS, SLOPE, ((1, 3), (-2, -6)))],
        ),
        (
            # f(x) = -1/2x + 3, its intercepts whole without a choice, its y-intercept a point
            [SLOPE_INTERCEPT],
            [Y_INTERCEPT],
            True,
            [DECIMAL],
            [DECIMAL, True, True, "f", False, Fraction(-1, 2), Fraction(3)],
            [],
            [LineQuestionData(Line(1, 2, 6), SLOPE_INTERCEPT, Y_INTERCEPT, (), True, DECIMAL, "f")],
        ),
        (
            # x = 5/2, then x = -4: the pairs are dealt in order
            [VERTICAL],
            [X_INTERCEPT, SLOPE],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, False, Fraction(5, 2), FRACTION, Fraction(-4)],
            [],
            [
                LineQuestionData(Line(2, 0, 5), VERTICAL, X_INTERCEPT),
                LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE),
            ],
        ),
        (
            # two points on x = 3, which x = a among the forms allows
            [TWO_POINTS, VERTICAL],
            [SLOPE],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, "vertical", Fraction(3)],
            [[(3, 7), (3, -2)]],
            [LineQuestionData(Line(1, 0, 3), TWO_POINTS, SLOPE, ((3, 7), (3, -2)))],
        ),
        (
            # two points on y = 3/4x + 5/4
            [TWO_POINTS],
            [Y_INTERCEPT],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, False, "sloped", False, Fraction(3, 4), Fraction(5, 4)],
            [[(1, 2), (-3, -1)]],
            [LineQuestionData(Line(3, -4, -5), TWO_POINTS, Y_INTERCEPT, ((1, 2), (-3, -1)))],
        ),
        (
            # a point on y = -2x + 6
            [POINT_SLOPE],
            [ZERO],
            False,
            [FRACTION, DECIMAL],
            [FRACTION, False, Fraction(-2), Fraction(6)],
            [[(5, -4)]],
            [LineQuestionData(Line(2, 1, 6), POINT_SLOPE, ZERO, ((5, -4),))],
        ),
        (
            # y = -3.6
            [HORIZONTAL],
            [RATE_OF_CHANGE],
            False,
            [FRACTION, DECIMAL],
            [DECIMAL, Fraction(-18, 5)],
            [],
            [LineQuestionData(Line(0, 5, -18), HORIZONTAL, RATE_OF_CHANGE, (), False, DECIMAL)],
        ),
        (
            # a point and slope never ask the slope, so the one pair is dealt twice: points on
            # y = 1/3x - 2/3, then y = 1/2x - 2
            [POINT_AND_SLOPE],
            [SLOPE, X_INTERCEPT],
            False,
            [FRACTION, DECIMAL],
            [
                *(FRACTION, True, False, Fraction(1, 3), Fraction(-2, 3)),
                *(DECIMAL, False, False, Fraction(1, 2), Fraction(-2)),
            ],
            [[(-4, -2)], [(8, 2)]],
            [
                LineQuestionData(Line(1, -3, 2), POINT_AND_SLOPE, X_INTERCEPT, ((-4, -2),), True),
                LineQuestionData(
                    Line(1, -2, 4), POINT_AND_SLOPE, X_INTERCEPT, ((8, 2),), False, DECIMAL
                ),
            ],
        ),
    ],
)
def test_questions(
    monkeypatch: pytest.MonkeyPatch,
    givens: list[LineForm],
    features: list[LineFeature],
    whole_intercepts: bool,
    number_styles: list[NumberStyle],
    chosen: list[object],
    sampled: list[list[tuple[int, int]]],
    expected: list[LineQuestionData],
) -> None:
    """Each question is built from its picks: the line, then the points it shows."""
    reverse_shuffle(monkeypatch)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    questions = generate_line_questions(
        len(expected),
        givens,
        features,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
    )
    assert [question.data for question in questions] == expected


# The points each form shows
POINTS_SHOWN = {POINT_SLOPE: 1, POINT_AND_SLOPE: 1, TWO_POINTS: 2}


def broken_rules(
    question: LineQuestion,
    givens: list[LineForm],
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    wrong_answer_count: int,
) -> list[str]:
    """Return the rules ``generate_line_questions`` promises that ``question`` breaks."""
    data, response = question.data, question.response
    choices = response.options if isinstance(response, MultipleChoice) else ()
    choice_numbers = [
        value
        for choice in choices
        if choice is not None
        for value in (choice if isinstance(choice, tuple) else (choice,))
    ]
    line = data.answer
    a, b, c = line.a, line.b, line.c
    intercepts = [value for value in (line.y_intercept, line.x_intercept) if value is not None]
    numbers = intercepts if line.slope is None else [line.slope, *intercepts]
    form_fits = {VERTICAL: b == 0, HORIZONTAL: a == 0, TWO_POINTS: True}
    rules = {
        "not normalised": not (a > 0 or (a == 0 and b > 0)) or gcd(a, b, c) != 1,
        "a point off the line": any(a * x + b * y != c for x, y in data.points),
        "a point outside the coordinates or on an axis": any(
            not 0 < abs(value) <= largest_coordinate for point in data.points for value in point
        ),
        "too many or too few points": len(data.points) != POINTS_SHOWN.get(data.given, 0),
        "an intercept outside the coordinates": any(
            abs(value) > largest_coordinate for value in intercepts
        ),
        "a denominator too large": any(
            value.denominator > largest_denominator for value in numbers
        ),
        "a slope's numerator too large": (
            line.slope is not None and abs(line.slope.numerator) > largest_coordinate
        ),
        "an intercept not whole": (
            whole_intercepts and any(value.denominator != 1 for value in intercepts)
        ),
        "a decimal that doesn't terminate": (
            data.numbers is DECIMAL and not all(terminates(value) for value in numbers)
        ),
        "a form that can't show the line": not form_fits.get(data.given, a != 0 and b != 0),
        "a vertical line without x = a, or a horizontal one without y = b, among the forms": (
            (b == 0 and VERTICAL not in givens) or (a == 0 and HORIZONTAL not in givens)
        ),
        "a feature the line hasn't": (
            line.slope is None
            if data.asked is SLOPE_AND_Y_INTERCEPT
            else feature_value(line, data.asked) is None and data.asked is not SLOPE
        ),
        "a vertical line's zero": b == 0 and data.asked is ZERO,
        "the slope given and asked": (
            data.given is POINT_AND_SLOPE
            and data.asked in (SLOPE, RATE_OF_CHANGE, SLOPE_AND_Y_INTERCEPT)
        ),
        "a point for a feature that isn't an intercept": (
            data.as_point and data.asked not in (X_INTERCEPT, Y_INTERCEPT)
        ),
        "function notation outside slope-intercept form": (
            data.function is not None and data.given is not SLOPE_INTERCEPT
        ),
        "free response with wrong answers asked for, or choices without": (
            isinstance(response, FreeResponse) == bool(wrong_answer_count)
        ),
        "choices that aren't the answer and different wrong ones": bool(choices)
        and (
            len(choices) != wrong_answer_count + 1
            or len(set(choices)) != len(choices)
            or [choices[index] for index in response.correct_indexes] != [answer_of(data)]
        ),
        "a choice whose decimal doesn't terminate": (
            data.numbers is DECIMAL and not all(terminates(value) for value in choice_numbers)
        ),
    }
    return [rule for rule, broken in rules.items() if broken]


# Every form but x = a and y = b
SLOPED_FORMS = [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, POINT_AND_SLOPE, TWO_POINTS]


@pytest.mark.parametrize(
    (
        "givens",
        "features",
        "largest_coordinate",
        "largest_denominator",
        "whole_intercepts",
        "number_styles",
        "wrong_answer_count",
        "distinct_answers",
        "count",
    ),
    [
        (
            [SLOPE_INTERCEPT, TWO_POINTS],
            [SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, SLOPE_AND_Y_INTERCEPT],
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            False,
            20,
        ),
        (
            list(LineForm),
            list(LineFeature),
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            False,
            20,
        ),
        (
            list(LineForm),
            list(LineFeature),
            10,
            5,
            True,
            [FRACTION, DECIMAL],
            0,
            False,
            20,
        ),
        (list(LineForm), list(LineFeature), 10, 5, False, [DECIMAL], 0, False, 20),
        (list(LineForm), list(LineFeature), 10, 5, False, [FRACTION], 0, False, 20),
        (
            list(LineForm),
            list(LineFeature),
            4,
            2,
            False,
            [FRACTION, DECIMAL],
            0,
            False,
            12,
        ),
        (
            list(LineForm),
            list(LineFeature),
            25,
            13,
            False,
            [FRACTION, DECIMAL],
            0,
            False,
            20,
        ),
        # many vertical and horizontal lines, two points among them
        (
            [TWO_POINTS, VERTICAL, HORIZONTAL],
            [SLOPE],
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            False,
            20,
        ),
        # two points without x = a or y = b: no vertical or horizontal line
        ([TWO_POINTS], [SLOPE], 10, 5, False, [FRACTION, DECIMAL], 0, False, 20),
        ([TWO_POINTS, HORIZONTAL], [SLOPE], 10, 5, False, [FRACTION, DECIMAL], 0, False, 20),
        # multiple choice
        (
            [SLOPE_INTERCEPT, TWO_POINTS],
            [SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, SLOPE_AND_Y_INTERCEPT],
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            3,
            False,
            20,
        ),
        (
            list(LineForm),
            list(LineFeature),
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            3,
            False,
            20,
        ),
        (list(LineForm), list(LineFeature), 10, 5, False, [DECIMAL], 3, False, 20),
        (list(LineForm), list(LineFeature), 10, 1, True, [FRACTION], 3, False, 20),
        # self-check tiles: 12 different answers
        (
            SLOPED_FORMS,
            list(LineFeature),
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            True,
            12,
        ),
        (list(LineForm), list(LineFeature), 10, 5, False, [DECIMAL], 0, True, 12),
        # one kind of answer: every x-intercept from -10 to 10 can be a question
        ([VERTICAL], [X_INTERCEPT], 10, 1, True, [FRACTION], 0, True, 12),
        # mixed kinds: 25 y-intercepts make 13 questions
        (
            [VERTICAL, HORIZONTAL],
            list(LineFeature),
            12,
            1,
            True,
            [FRACTION],
            0,
            True,
            12,
        ),
    ],
)
def test_questions_meet_the_rules(
    givens: list[LineForm],
    features: list[LineFeature],
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: list[NumberStyle],
    wrong_answer_count: int,
    distinct_answers: bool,
    count: int,
) -> None:
    """Every question keeps the generator's promises, no line repeats, nor with tiles an answer."""
    questions = generate_line_questions(
        count,
        givens,
        features,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        wrong_answer_count=wrong_answer_count,
        distinct_answers=distinct_answers,
    )
    broken = [
        (question.data, rule)
        for question in questions
        for rule in broken_rules(
            question,
            givens,
            largest_coordinate,
            largest_denominator,
            whole_intercepts,
            wrong_answer_count,
        )
    ]
    answers = {answer_of(question.data) for question in questions}
    assert broken == []
    assert (
        len({question.data.answer for question in questions}),
        len(answers) if distinct_answers else count,
    ) == (count, count)


@pytest.mark.parametrize(
    (
        "givens",
        "features",
        "largest_coordinate",
        "largest_denominator",
        "number_styles",
        "as_point_choices",
        "count",
        "message",
    ),
    [
        (
            [],
            [SLOPE],
            10,
            5,
            [FRACTION],
            [False, True],
            1,
            "At least one form to show is needed.",
        ),
        (
            [SLOPE_INTERCEPT],
            [],
            10,
            5,
            [FRACTION],
            [False, True],
            1,
            "At least one feature to ask is needed.",
        ),
        (
            [STANDARD],
            [SLOPE],
            0,
            5,
            [FRACTION],
            [False, True],
            1,
            "The largest coordinate must be at least 1, not 0.",
        ),
        (
            [STANDARD],
            [SLOPE],
            10,
            0,
            [FRACTION],
            [False, True],
            1,
            "The largest denominator must be at least 1, not 0.",
        ),
        (
            [STANDARD],
            [SLOPE],
            10,
            5,
            [],
            [False, True],
            1,
            "At least one number style is needed.",
        ),
        (
            [STANDARD],
            [SLOPE],
            10,
            5,
            [FRACTION, MIXED_NUMBER],
            [False, True],
            1,
            "Lines are written with fractions or decimals, not mixed numbers.",
        ),
        (
            [VERTICAL],
            [Y_INTERCEPT],
            10,
            5,
            [FRACTION],
            [False, True],
            1,
            "None of the forms given can show a line with the features asked.",
        ),
        (
            [POINT_AND_SLOPE],
            [SLOPE, RATE_OF_CHANGE],
            10,
            5,
            [FRACTION],
            [False, True],
            1,
            "None of the forms given can show a line with the features asked.",
        ),
        (
            # x = -2, -1, 0, 1 and 2 are the only lines
            [VERTICAL],
            [X_INTERCEPT],
            2,
            1,
            [FRACTION],
            [False, True],
            6,
            "Cannot make 6 questions with different lines: only 5 possible.",
        ),
        (
            [STANDARD],
            [Y_INTERCEPT],
            10,
            5,
            [FRACTION],
            [],
            1,
            "Intercepts need asking as numbers, points or both.",
        ),
    ],
)
def test_generate_line_questions_errors(
    givens: list[LineForm],
    features: list[LineFeature],
    largest_coordinate: int,
    largest_denominator: int,
    number_styles: list[NumberStyle],
    as_point_choices: list[bool],
    count: int,
    message: str,
) -> None:
    """Options that can't make a sheet are refused."""
    with pytest.raises(ValueError) as error:
        generate_line_questions(
            count,
            givens,
            features,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            number_styles=number_styles,
            as_point_choices=as_point_choices,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    (
        "givens",
        "features",
        "largest_coordinate",
        "largest_denominator",
        "whole_intercepts",
        "number_styles",
        "distinct_answers",
        "limit",
        "expected",
    ),
    [
        # x = -2 to 2
        ([VERTICAL], [X_INTERCEPT], 2, 1, False, [FRACTION], False, 20, 5),
        # and halves: -3/2, -1/2, 1/2 and 3/2
        ([VERTICAL], [X_INTERCEPT], 2, 2, False, [FRACTION], False, 20, 9),
        ([VERTICAL], [X_INTERCEPT], 2, 2, True, [FRACTION], False, 20, 5),
        # thirds don't terminate, so decimals alone leave out -5/3 to 5/3
        ([VERTICAL], [X_INTERCEPT], 2, 3, False, [DECIMAL], False, 20, 9),
        ([VERTICAL], [X_INTERCEPT], 2, 3, False, [FRACTION, DECIMAL], False, 20, 17),
        # y = -5 to 5
        ([HORIZONTAL], [Y_INTERCEPT], 5, 1, False, [FRACTION], False, 20, 11),
        # two points within 1 of 0 and off the axes: y = x and y = -x
        ([TWO_POINTS], [SLOPE], 1, 1, False, [FRACTION], False, 20, 2),
        # counting stops at the limit
        ([SLOPE_INTERCEPT], [SLOPE], 10, 5, False, [FRACTION], False, 20, 20),
        # x = -2 to 2 last 5 rounds of the deck's 2 pairs
        ([SLOPE_INTERCEPT, VERTICAL], [SLOPE], 2, 1, False, [FRACTION], False, 20, 10),
        # two pairs share x = -2 to 2: 2 rounds of 4 pairs, and 1 more, as x = a may come first
        ([SLOPE_INTERCEPT, VERTICAL], [SLOPE, X_INTERCEPT], 2, 1, False, [FRACTION], False, 20, 9),
        # a form that can't be asked isn't dealt, so it doesn't count
        ([SLOPE_INTERCEPT, VERTICAL], [Y_INTERCEPT], 10, 5, False, [FRACTION], False, 20, 20),
        # tiles: different answers. x = a has one slope, "undefined"
        ([VERTICAL], [SLOPE], 10, 1, True, [FRACTION], True, 12, 1),
        # one kind of answer: every x-intercept from -10 to 10, counting stops at 12
        ([VERTICAL], [X_INTERCEPT], 10, 1, True, [FRACTION], True, 12, 12),
        ([VERTICAL], [X_INTERCEPT], 5, 1, True, [FRACTION], True, 12, 11),
        # two kinds: an earlier question can rule out two answers, so 21 make 11
        ([VERTICAL], [SLOPE, X_INTERCEPT], 10, 1, True, [FRACTION], True, 12, 11),
        ([VERTICAL, HORIZONTAL], list(LineFeature), 10, 1, True, [FRACTION], True, 12, 11),
    ],
)
def test_count_possible_lines(
    givens: list[LineForm],
    features: list[LineFeature],
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: list[NumberStyle],
    distinct_answers: bool,
    limit: int,
    expected: int,
) -> None:
    """
    The count is as many questions as the deck deals while every group of pairs has a line
    meeting every question's rules for each time it's dealt, or with different answers, the pair
    with the most answers, halved when the kinds of answer differ.
    """
    count = count_possible_lines(
        givens,
        features,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        distinct_answers=distinct_answers,
        limit=limit,
    )
    assert count == expected


@pytest.mark.parametrize(
    ("givens", "forms", "chosen", "sampled", "expected"),
    [
        (
            # y = 3/4x + 5/4, written in standard form
            [SLOPE_INTERCEPT],
            [STANDARD],
            [FRACTION, False, Fraction(3, 4), Fraction(5, 4)],
            [],
            [LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD)],
        ),
        (
            # two points on y = 3x, a line through the origin
            [TWO_POINTS],
            [SLOPE_INTERCEPT],
            [FRACTION, True, Fraction(3), Fraction(0)],
            [[(1, 3), (-2, -6)]],
            [LineQuestionData(Line(3, -1, 0), TWO_POINTS, SLOPE_INTERCEPT, ((1, 3), (-2, -6)))],
        ),
        (
            # y = -2(x - 5) - 4, point-slope form solved for y, in decimals
            [POINT_SLOPE],
            [SLOPE_INTERCEPT],
            [DECIMAL, True, False, False, Fraction(-2), Fraction(6)],
            [[(5, -4)]],
            [
                LineQuestionData(
                    Line(2, 1, 6),
                    POINT_SLOPE,
                    SLOPE_INTERCEPT,
                    ((5, -4),),
                    numbers=DECIMAL,
                    solved_for_y=True,
                )
            ],
        ),
        (
            # the point is where y = -2x + 6 crosses the x-axis, which gives y = -2(x - 3)
            [POINT_AND_SLOPE],
            [POINT_SLOPE],
            [FRACTION, False, True, Fraction(-2), Fraction(6)],
            [[(3, 0)]],
            [LineQuestionData(Line(2, 1, 6), POINT_AND_SLOPE, POINT_SLOPE, ((3, 0),))],
        ),
        (
            # two points on y = 7
            [TWO_POINTS],
            [HORIZONTAL],
            [FRACTION, Fraction(7)],
            [[(-2, 7), (5, 7)]],
            [LineQuestionData(Line(0, 1, 7), TWO_POINTS, HORIZONTAL, ((-2, 7), (5, 7)))],
        ),
        (
            # as A.2 2018 Q39: through (2, -2), perpendicular to y = 2/5x + 2
            [PERPENDICULAR],
            [SLOPE_INTERCEPT],
            [FRACTION, False, False, Fraction(-5, 2), Fraction(3), Fraction(2), SLOPE_INTERCEPT],
            [[(2, -2)]],
            [
                LineQuestionData(
                    Line(5, 2, 6),
                    SLOPE_INTERCEPT,
                    SLOPE_INTERCEPT,
                    ((2, -2),),
                    reference=Line(2, -5, -10),
                    relation=PERPENDICULAR,
                )
            ],
        ),
        (
            # through (3, 4), parallel to 2x + 3y = 6, then x = -4 through (-4, 2), parallel to
            # the y-axis: the pairs are dealt in order
            [PARALLEL],
            [STANDARD, VERTICAL],
            [
                *(FRACTION, False, False, Fraction(-2, 3), Fraction(6)),
                *(Fraction(2), STANDARD),
                *(FRACTION, Fraction(-4)),
            ],
            [[(3, 4)], [(-4, 2)]],
            [
                LineQuestionData(
                    Line(2, 3, 18),
                    STANDARD,
                    STANDARD,
                    ((3, 4),),
                    reference=Line(2, 3, 6),
                    relation=PARALLEL,
                ),
                LineQuestionData(
                    Line(1, 0, -4),
                    VERTICAL,
                    VERTICAL,
                    ((-4, 2),),
                    reference=Y_AXIS,
                    relation=PARALLEL,
                ),
            ],
        ),
        (
            # y = 7 through (3, 7), perpendicular to the y-axis
            [PERPENDICULAR],
            [HORIZONTAL],
            [FRACTION, Fraction(7)],
            [[(3, 7)]],
            [
                LineQuestionData(
                    Line(0, 1, 7),
                    VERTICAL,
                    HORIZONTAL,
                    ((3, 7),),
                    reference=Y_AXIS,
                    relation=PERPENDICULAR,
                )
            ],
        ),
    ],
)
def test_equation_questions(
    monkeypatch: pytest.MonkeyPatch,
    givens: list[LineForm | Relation],
    forms: list[LineForm],
    chosen: list[object],
    sampled: list[list[tuple[int, int]]],
    expected: list[LineQuestionData],
) -> None:
    """
    Each question is built from its picks: the line, the points it shows, then the line it's
    parallel or perpendicular to.
    """
    reverse_shuffle(monkeypatch)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    questions = generate_equation_questions(len(expected), givens, forms, largest_coordinate=20)
    assert [question.data for question in questions] == expected


def broken_equation_rules(
    question: LineQuestion,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    wrong_answer_count: int,
) -> list[str]:
    """Return the rules ``generate_equation_questions`` promises that ``question`` breaks."""
    data, response = question.data, question.response
    choices = response.options if isinstance(response, MultipleChoice) else ()
    line, reference, relation = data.answer, data.reference, data.relation
    given = relation or data.given
    shown = [line] if reference is None else [line, reference]
    sloped = [each for each in shown if each.a != 0 and each.b != 0]
    a, b, c = line.a, line.b, line.c
    slant = {VERTICAL: b == 0, HORIZONTAL: a == 0}
    axis = None
    if reference in (X_AXIS, Y_AXIS):
        axis = X_AXIS if (relation is PARALLEL) == (a == 0) else Y_AXIS

    def numbers(each: Line) -> list[Fraction]:
        intercepts = [value for value in (each.y_intercept, each.x_intercept) if value is not None]
        return intercepts if each.slope is None else [each.slope, *intercepts]

    def shows(choice: object) -> list[Fraction]:
        assert isinstance(choice, Equation)
        choice_line = choice.line
        values = {
            SLOPE_INTERCEPT: (choice_line.slope, choice_line.y_intercept),
            POINT_SLOPE: (choice_line.slope,),
            VERTICAL: (choice_line.x_intercept,),
            HORIZONTAL: (choice_line.y_intercept,),
        }.get(choice.form, ())
        return [value for value in values if value is not None]

    rules = {
        "not normalised": not (a > 0 or (a == 0 and b > 0)) or gcd(a, b, c) != 1,
        "a point off the line": any(a * x + b * y != c for x, y in data.points),
        "a point outside the coordinates, or on an axis but the x-axis point": any(
            abs(value) > largest_coordinate for point in data.points for value in point
        )
        or any(x == 0 for x, _ in data.points)
        or any(y == 0 and (len(data.points) != 1 or not sloped) for _, y in data.points),
        "too many or too few points": len(data.points)
        != (1 if relation else POINTS_SHOWN.get(data.given, 0)),
        "an intercept outside the coordinates": any(
            abs(value) > largest_coordinate for each in sloped for value in numbers(each)[1:]
        ),
        "a denominator too large": any(
            value.denominator > largest_denominator for each in shown for value in numbers(each)
        ),
        "a slope's numerator too large": any(
            abs(each.slope.numerator) > largest_coordinate
            for each in sloped
            if each.slope is not None
        ),
        "an intercept not whole": whole_intercepts
        and any(value.denominator != 1 for each in sloped for value in numbers(each)[1:]),
        "a decimal that doesn't terminate": data.numbers is DECIMAL
        and not all(terminates(value) for each in shown for value in numbers(each)),
        "a given or form the sheet doesn't use, or that can't be asked": given
        not in EQUATION_GIVENS
        or data.asked not in EQUATION_FORMS
        or not isinstance(data.asked, LineForm)
        or not can_write(given, data.asked),
        "a line that doesn't run as the form asked says": not slant.get(
            data.asked, a != 0 and b != 0
        ),
        "a relation without its line, or a line without a relation": (relation is None)
        != (reference is None),
        "a line not parallel or perpendicular as the relation says": reference is not None
        and (
            reference != axis
            if axis is not None
            else line.slope is None
            or reference.slope is None
            or (relation is PARALLEL and (reference.slope != line.slope or reference == line))
            or (relation is PERPENDICULAR and reference.slope * line.slope != -1)
        ),
        "a reference line in a form it isn't written in": reference is not None
        and data.given
        not in (
            {X_AXIS: (HORIZONTAL,), Y_AXIS: (VERTICAL,)}.get(reference, (SLOPE_INTERCEPT, STANDARD))
        ),
        "solved for y without point-slope form given": data.solved_for_y
        and data.given is not POINT_SLOPE,
        "function notation, or an answer as a point": data.function is not None or data.as_point,
        "free response with wrong answers asked for, or choices without": (
            isinstance(response, FreeResponse) == bool(wrong_answer_count)
        ),
        "choices that aren't the answer and different wrong ones": bool(choices)
        and (
            len(choices) != wrong_answer_count + 1
            or len(set(choices)) != len(choices)
            or [choices[index] for index in response.correct_indexes] != [answer_of(data)]
        ),
        "a wrong choice that is an equation of the answer's line": any(
            isinstance(choice, Equation) and choice.line == line
            for index, choice in enumerate(choices)
            if index not in response.correct_indexes
        ),
        "a choice not in the form asked, or x = a or y = b for either, or whose decimal doesn't "
        "terminate": any(
            not isinstance(choice, Equation)
            or choice.form not in LEVEL_FORMS.get(data.asked, (data.asked,))
            or (data.numbers is DECIMAL and not all(terminates(value) for value in shows(choice)))
            for choice in choices
        ),
    }
    return [rule for rule, broken in rules.items() if broken]


# The forms the choices for x = a or y = b are in: STAAR's commonest mistake confuses them
LEVEL_FORMS = {VERTICAL: (VERTICAL, HORIZONTAL), HORIZONTAL: (VERTICAL, HORIZONTAL)}
# Every form but x = a and y = b
SLOPED_EQUATION_FORMS = [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE]


@pytest.mark.parametrize(
    (
        "givens",
        "forms",
        "largest_coordinate",
        "largest_denominator",
        "whole_intercepts",
        "number_styles",
        "wrong_answer_count",
        "count",
    ),
    [
        ([TWO_POINTS], [SLOPE_INTERCEPT], 10, 5, False, [FRACTION, DECIMAL], 0, 20),
        (
            list(EQUATION_GIVENS),
            SLOPED_EQUATION_FORMS,
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            5,
            True,
            [FRACTION, DECIMAL],
            0,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            5,
            False,
            [DECIMAL],
            0,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            5,
            2,
            False,
            [FRACTION, DECIMAL],
            0,
            10,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            25,
            13,
            False,
            [FRACTION, DECIMAL],
            0,
            20,
        ),
        # many lines parallel or perpendicular to another, and many x-axis points
        (
            [PARALLEL, PERPENDICULAR],
            SLOPED_EQUATION_FORMS,
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            0,
            20,
        ),
        # multiple choice
        ([TWO_POINTS], [SLOPE_INTERCEPT], 10, 5, False, [FRACTION, DECIMAL], 3, 20),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            5,
            False,
            [FRACTION, DECIMAL],
            3,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            5,
            False,
            [DECIMAL],
            3,
            20,
        ),
        (
            list(EQUATION_GIVENS),
            list(EQUATION_FORMS),
            10,
            1,
            True,
            [FRACTION],
            3,
            20,
        ),
    ],
)
def test_equation_questions_meet_the_rules(
    givens: list[LineForm | Relation],
    forms: list[LineForm],
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: list[NumberStyle],
    wrong_answer_count: int,
    count: int,
) -> None:
    """Every question keeps the generator's promises, and no line repeats."""
    questions = generate_equation_questions(
        count,
        givens,
        forms,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        wrong_answer_count=wrong_answer_count,
    )
    broken = [
        (question.data, rule)
        for question in questions
        for rule in broken_equation_rules(
            question,
            largest_coordinate,
            largest_denominator,
            whole_intercepts,
            wrong_answer_count,
        )
    ]
    assert broken == []
    assert len({question.data.answer for question in questions}) == count


@pytest.mark.parametrize(
    (
        "givens",
        "forms",
        "largest_coordinate",
        "largest_denominator",
        "number_styles",
        "count",
        "message",
    ),
    [
        ([], [SLOPE_INTERCEPT], 10, 5, [FRACTION], 1, "At least one given is needed."),
        ([TWO_POINTS], [], 10, 5, [FRACTION], 1, "At least one form to write is needed."),
        (
            [VERTICAL],
            [SLOPE_INTERCEPT],
            10,
            5,
            [FRACTION],
            1,
            "A line's equation isn't written from vertical.",
        ),
        (
            [TWO_POINTS],
            [TWO_POINTS],
            10,
            5,
            [FRACTION],
            1,
            "Equations aren't written in two_points form.",
        ),
        (
            [STANDARD],
            [SLOPE_INTERCEPT],
            0,
            5,
            [FRACTION],
            1,
            "The largest coordinate must be at least 1, not 0.",
        ),
        (
            [STANDARD],
            [SLOPE_INTERCEPT],
            10,
            0,
            [FRACTION],
            1,
            "The largest denominator must be at least 1, not 0.",
        ),
        (
            [STANDARD],
            [SLOPE_INTERCEPT],
            10,
            5,
            [],
            1,
            "At least one number style is needed.",
        ),
        (
            [STANDARD],
            [SLOPE_INTERCEPT],
            10,
            5,
            [MIXED_NUMBER],
            1,
            "Lines are written with fractions or decimals, not mixed numbers.",
        ),
        (
            [SLOPE_INTERCEPT, STANDARD],
            [POINT_SLOPE, VERTICAL, HORIZONTAL],
            10,
            5,
            [FRACTION],
            1,
            "None of the givens can be written in the forms asked.",
        ),
        (
            # x = -2, -1, 1 and 2 through a point off the axes are the only lines
            [POINT_AND_SLOPE],
            [VERTICAL],
            2,
            1,
            [FRACTION],
            5,
            "Cannot make 5 questions with different lines: only 4 possible.",
        ),
    ],
)
def test_generate_equation_questions_errors(
    givens: list[LineForm | Relation],
    forms: list[LineForm],
    largest_coordinate: int,
    largest_denominator: int,
    number_styles: list[NumberStyle],
    count: int,
    message: str,
) -> None:
    """Options that can't make a sheet are refused."""
    with pytest.raises(ValueError) as error:
        generate_equation_questions(
            count,
            givens,
            forms,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            number_styles=number_styles,
        )
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("given", "forms"),
    [
        (SLOPE_INTERCEPT, [STANDARD]),
        (STANDARD, [SLOPE_INTERCEPT]),
        (POINT_SLOPE, [SLOPE_INTERCEPT, STANDARD]),
        (POINT_AND_SLOPE, [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, VERTICAL, HORIZONTAL]),
        (TWO_POINTS, [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, VERTICAL, HORIZONTAL]),
        (PARALLEL, [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, VERTICAL, HORIZONTAL]),
        (PERPENDICULAR, [SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, VERTICAL, HORIZONTAL]),
        (VERTICAL, [SLOPE_INTERCEPT, STANDARD]),
        (HORIZONTAL, [SLOPE_INTERCEPT, STANDARD]),
    ],
)
def test_can_write(given: LineForm | Relation, forms: list[LineForm]) -> None:
    """
    An equation is never rewritten in its own form, and point-slope form, x = a and y = b need a
    point shown. Two points and a point and slope aren't equations, so they're never asked.
    """
    assert [form for form in LineForm if can_write(given, form)] == forms


@pytest.mark.parametrize(
    (
        "givens",
        "forms",
        "largest_coordinate",
        "largest_denominator",
        "whole_intercepts",
        "number_styles",
        "limit",
        "expected",
    ),
    [
        # x = -2, -1, 1 and 2: a point is shown, so not x = 0
        ([POINT_AND_SLOPE], [VERTICAL], 2, 1, False, [FRACTION], 20, 4),
        # and so whole numbers only, whatever the denominator
        ([POINT_AND_SLOPE], [VERTICAL], 2, 5, False, [FRACTION], 20, 4),
        ([PARALLEL], [VERTICAL], 2, 1, False, [FRACTION], 20, 4),
        # two points within 1 of 0 and off the axes: y = x and y = -x
        ([TWO_POINTS], [SLOPE_INTERCEPT], 1, 1, False, [FRACTION], 20, 2),
        # y = x and y = -x are perpendicular, and each is parallel to the lines 1 above and below
        ([PERPENDICULAR], [SLOPE_INTERCEPT], 1, 1, False, [FRACTION], 20, 2),
        ([PARALLEL], [SLOPE_INTERCEPT], 1, 1, False, [FRACTION], 20, 2),
        # slopes 1 and -1 have 5 lines each through a point off the axes, 2 and -2 have 3 each
        ([POINT_AND_SLOPE], [SLOPE_INTERCEPT], 2, 1, False, [FRACTION], 40, 16),
        # a line perpendicular to a slope of 2 or -2 needs a denominator of 2, so 10 are left
        ([PERPENDICULAR], [SLOPE_INTERCEPT], 2, 1, False, [FRACTION], 40, 10),
        # counting stops at the limit
        ([SLOPE_INTERCEPT], [STANDARD], 10, 5, False, [FRACTION], 20, 20),
        # x = -2, -1, 1 and 2 last 4 rounds of the deck's 2 pairs
        ([TWO_POINTS], [SLOPE_INTERCEPT, VERTICAL], 2, 1, False, [FRACTION], 20, 8),
        # two pairs share x = -2, -1, 1 and 2: 2 rounds of 4 pairs
        (
            [POINT_AND_SLOPE, TWO_POINTS],
            [SLOPE_INTERCEPT, VERTICAL],
            2,
            1,
            False,
            [FRACTION],
            20,
            8,
        ),
        # y = x and y = -x are the only lines of both pairs, so they make 2 questions, not 2 each
        ([TWO_POINTS, PERPENDICULAR], [SLOPE_INTERCEPT], 1, 1, False, [FRACTION], 20, 2),
        # every given and form: 20 questions deal 20 of the 24 pairs once each
        (list(EQUATION_GIVENS), list(EQUATION_FORMS), 2, 1, False, [FRACTION], 20, 20),
        # a pair that can't be asked isn't dealt, so it doesn't count
        ([SLOPE_INTERCEPT, TWO_POINTS], [STANDARD, VERTICAL], 10, 5, False, [FRACTION], 20, 20),
    ],
)
def test_count_possible_equations(
    givens: list[LineForm | Relation],
    forms: list[LineForm],
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: list[NumberStyle],
    limit: int,
    expected: int,
) -> None:
    """
    The count is as many questions as the deck deals while every group of pairs has a line
    meeting every question's rules for each time it's dealt.
    """
    count = count_possible_equations(
        givens,
        forms,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        limit=limit,
    )
    assert count == expected
