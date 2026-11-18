"""
Tests for the line worksheet PDFs, slope and intercepts and writing linear equations, rendered
from hand-built questions.

The question generator is not used. Questions are built by hand, and ``reverse_shuffle`` fixes
a multiple-choice question's option order by reversing the options, so the correct answer is
always last.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/line_equations_worksheet_pdf_expecteds.txt``. The text includes every question's
wording, the line in its given form with its stacked fractions, the answer lines, blanks or
choices, the tiles page, the answer key and the page breaks. To regenerate sections after an
intended change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text``
and run it (``-k`` selects cases).
"""

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
    NumberStyle,
    Relation,
)
from tests.helpers import GOLDENS, pdf_text, read_sections, render_line_questions, reverse_shuffle

SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, X_INTERCEPT, ZERO, SLOPE_AND_Y_INTERCEPT = LineFeature
SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, POINT_AND_SLOPE, TWO_POINTS, VERTICAL, HORIZONTAL = LineForm
FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle
PARALLEL, PERPENDICULAR = Relation

# (question data, its wrong answers): none for a written question

# Each form shown once, each asking the slope: 3x + 4y = 8 and others. Eight spill onto a
# second page.
EACH_FORM_SHOWN = [
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE, numbers=DECIMAL, function="f"), ()),
    (LineQuestionData(Line(2, -1, 3), STANDARD, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_SLOPE, Y_INTERCEPT, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, Y_INTERCEPT, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), TWO_POINTS, SLOPE, ((-4, 5), (4, -1))), ()),
    (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), ()),
    (LineQuestionData(Line(0, 5, -18), HORIZONTAL, Y_INTERCEPT, numbers=DECIMAL), ()),
]

# Each question asked once, as a number, a point, "undefined" and both numbers
EACH_QUESTION_ASKED = [
    (LineQuestionData(Line(3, 4, 8), STANDARD, RATE_OF_CHANGE), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT, as_point=True), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, ZERO), ()),
    (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE_AND_Y_INTERCEPT), ()),
]

# Numbers and points in a row, statements one under another
CHOICES = [
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
        (Fraction(-4, 3), Fraction(3, 4), Fraction(4, 3)),
    ),
    (LineQuestionData(Line(0, 1, 3), HORIZONTAL, SLOPE), (None, Fraction(3), Fraction(-3))),
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True),
        ((Fraction(2), Fraction(0)), (Fraction(0), Fraction(8, 3)), (Fraction(8, 3), Fraction(0))),
    ),
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
        (
            (Fraction(-4, 3), Fraction(2)),
            (Fraction(-3, 4), Fraction(8, 3)),
            (Fraction(-4, 3), Fraction(8, 3)),
        ),
    ),
]

# Twelve different answers for the tiles case, among them both numbers labelled on one tile
TWELVE = [
    (LineQuestionData(Line(1, -1, -number), SLOPE_INTERCEPT, Y_INTERCEPT), ())
    for number in range(1, 11)
] + [
    (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE_AND_Y_INTERCEPT), ()),
]
TWELVE_SLOTS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

# Each way an equation is written from, with each form asked; eleven spill onto a third page
EACH_EQUATION_GIVEN = [
    (LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD), ()),
    (LineQuestionData(Line(7, 4, -28), STANDARD, SLOPE_INTERCEPT, numbers=DECIMAL), ()),
    (
        LineQuestionData(
            Line(3, 4, 8), POINT_SLOPE, SLOPE_INTERCEPT, ((-4, 5),), solved_for_y=True
        ),
        (),
    ),
    (LineQuestionData(Line(2, 1, 6), POINT_SLOPE, STANDARD, ((3, 0),)), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, POINT_SLOPE, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))), ()),
    (LineQuestionData(Line(1, 0, 3), TWO_POINTS, VERTICAL, ((3, 7), (3, -2))), ()),
    (LineQuestionData(Line(1, 0, -4), POINT_AND_SLOPE, VERTICAL, ((-4, 2),)), ()),
    (
        LineQuestionData(
            Line(5, 2, 6),
            SLOPE_INTERCEPT,
            SLOPE_INTERCEPT,
            ((2, -2),),
            reference=Line(2, -5, -10),
            relation=PERPENDICULAR,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(2, 3, 18),
            STANDARD,
            STANDARD,
            ((3, 4),),
            reference=Line(2, 3, 6),
            relation=PARALLEL,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(0, 1, 7), VERTICAL, HORIZONTAL, ((3, 7),), reference=Y_AXIS, relation=PERPENDICULAR
        ),
        (),
    ),
]

# Equations to choose from, STAAR's: A.2 2019 Q6 in a row, A.2 2026 Q46 one under another, a
# rewritten equation, and y = 7 against x = 7, y = 3 and x = 3
EQUATION_CHOICES = [
    (
        LineQuestionData(Line(1, -4, -12), TWO_POINTS, SLOPE_INTERCEPT, ((-4, 2), (12, 6))),
        (
            Equation(Line(1, -4, -4), SLOPE_INTERCEPT),
            Equation(Line(4, -1, -3), SLOPE_INTERCEPT),
            Equation(Line(4, -1, -1), SLOPE_INTERCEPT),
        ),
    ),
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
    (
        LineQuestionData(Line(7, 3, -14), SLOPE_INTERCEPT, STANDARD),
        (
            Equation(Line(7, 3, 14), STANDARD),
            Equation(Line(7, -3, 14), STANDARD),
            Equation(Line(7, -3, -14), STANDARD),
        ),
    ),
    (
        LineQuestionData(
            Line(0, 1, 7), HORIZONTAL, HORIZONTAL, ((3, 7),), reference=X_AXIS, relation=PARALLEL
        ),
        (
            Equation(Line(0, 1, 3), HORIZONTAL),
            Equation(Line(1, 0, 7), VERTICAL),
            Equation(Line(1, 0, 3), VERTICAL),
        ),
    ),
]

# Twelve different equations for the tiles case, among them stacked fractions and point-slope
# form
TWELVE_EQUATIONS = [
    (LineQuestionData(Line(1, -1, -number), SLOPE_INTERCEPT, STANDARD), ())
    for number in range(1, 11)
] + [
    (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_INTERCEPT), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, POINT_SLOPE, ((-4, 5),)), ()),
]

EXPECTED = GOLDENS / "line_equations_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "cases", "answer_key", "slot_of", "title", "label"),
    [
        (
            "each_form_shown_answer_key",
            EACH_FORM_SHOWN,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        (
            "each_question_asked_answer_key",
            EACH_QUESTION_ASKED,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        ("choices_answer_key", CHOICES, True, None, "Slope and Intercepts", "Sheet A"),
        ("tiles_answer_key", TWELVE, True, TWELVE_SLOTS, "Slope and Intercepts", "Sheet A"),
        ("other_title_and_label", EACH_QUESTION_ASKED, False, None, "Lines", "Day 2"),
        (
            "each_equation_given_answer_key",
            EACH_EQUATION_GIVEN,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "equation_choices_answer_key",
            EQUATION_CHOICES,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "equation_tiles_answer_key",
            TWELVE_EQUATIONS,
            True,
            TWELVE_SLOTS,
            "Writing Linear Equations",
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    cases: list[tuple[LineQuestionData, tuple[LineAnswer, ...]]],
    answer_key: bool,
    slot_of: tuple[int, ...] | None,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of ``line_equations_worksheet_pdf_expecteds.txt``.

    One comparison covers the wording, the lines with their stacked fractions, the answer lines,
    blanks or lettered choices, the tiles page, the answer key's answers, letters and slots, the
    page breaks, and the title and label.
    """
    reverse_shuffle(monkeypatch)

    actual = pdf_text(render_line_questions(cases, answer_key, title, label, slot_of))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
