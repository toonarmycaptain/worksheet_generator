"""
Tests for the writing linear equations PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the test
case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_line_equations_worksheet``.

The PDF tests replace these functions:

- ``random.choice`` returns the picks listed in the case, as ``test_generator`` in
  ``test_core/test_line_equations`` describes for equations, and raises ``ValueError`` for a
  pick that is not among its call's items.
- ``random.sample`` returns the points listed, and raises ``ValueError`` for a sample not drawn
  from its call's population.
- ``random.shuffle`` reverses the list, so the pairs of a given and a form are dealt in their
  order, and a multiple-choice question's correct option is last.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from fractions import Fraction
from typing import Any

import pytest
from django.test import Client

from core.line_equations.data import (
    Equation,
    Line,
    LineForm,
    LineQuestionData,
    NumberStyle,
    Relation,
)
from tests.data import REAL_CASE_SLOTS
from tests.helpers import (
    choice_returns,
    conventional_slot_of_returns,
    pdf_text,
    refused,
    render_line_questions,
    reverse_shuffle,
    sample_returns,
)

SLOPE_INTERCEPT, STANDARD, POINT_SLOPE, POINT_AND_SLOPE, TWO_POINTS, VERTICAL, HORIZONTAL = LineForm
PARALLEL, PERPENDICULAR = Relation
FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle


@pytest.mark.parametrize(
    ("url", "chosen", "sampled", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: the first pair is slope-intercept form written in
            # standard form; y = 3/4x + 5/4, not through the origin
            "/api/worksheets/writing_linear_equations.pdf?problems=1&sheet=1ab2c3",
            [FRACTION, False, Fraction(3, 4), Fraction(5, 4)],
            [],
            200,
            None,
            {
                "cases": [(LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD), ())],
                "slot_of": None,
                "answer_key": False,
                "title": "Writing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "writing_linear_equations-sheet-a.pdf",
        ),
        (
            # every option for free response: two points on y = 1/2x + 3, in decimals
            "/api/worksheets/writing_linear_equations.pdf?given=two_points"
            "&asked=slope_intercept&number_styles=decimal&largest_coordinate=12"
            "&largest_denominator=4&whole_intercepts=true&problems=1&answer_key=true"
            "&name_line=true&title=Practice&label=Week+3&sheet=1ab2c3",
            [DECIMAL, False, Fraction(1, 2), Fraction(3)],
            [[(2, 4), (-4, 1)]],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(1, -2, -6),
                            TWO_POINTS,
                            SLOPE_INTERCEPT,
                            ((2, 4), (-4, 1)),
                            numbers=DECIMAL,
                        ),
                        (),
                    )
                ],
                "slot_of": None,
                "answer_key": True,
                "title": "Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "writing_linear_equations-week-3.pdf",
        ),
        (
            # multiple choice, as A.2 2026 Q46: through (-3, -6), parallel to y = -8/9x + 4, in
            # point-slope form; the wrong ones flip the point's signs and use the perpendicular
            # slope
            "/api/worksheets/writing_linear_equations.pdf?given=parallel&asked=point_slope"
            "&largest_denominator=9&multiple_choice=true&problems=1&sheet=1ab2c3",
            [
                FRACTION,
                False,
                False,
                Fraction(-8, 9),
                Fraction(-26, 3),
                Fraction(4),
                SLOPE_INTERCEPT,
            ],
            [[(-3, -6)]],
            200,
            None,
            {
                "cases": [
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
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Writing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "writing_linear_equations-sheet-a.pdf",
        ),
        (
            # self-check tiles: x = 3, then x = -5, each through a point with an undefined slope
            "/api/worksheets/writing_linear_equations.pdf?given=point_and_slope&asked=vertical"
            "&self_check_tiles=true&problems=2&sheet=1ab2c3",
            [FRACTION, Fraction(3), FRACTION, Fraction(-5)],
            [[(3, 7)], [(-5, 2)]],
            200,
            None,
            {
                "cases": [
                    (LineQuestionData(Line(1, 0, 3), POINT_AND_SLOPE, VERTICAL, ((3, 7),)), ()),
                    (LineQuestionData(Line(1, 0, -5), POINT_AND_SLOPE, VERTICAL, ((-5, 2),)), ()),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "title": "Writing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "writing_linear_equations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/writing_linear_equations.pdf?multiple_choice=true"
            "&self_check_tiles=true",
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/writing_linear_equations.pdf?given=slope_intercept"
            "&asked=slope_intercept&asked=point_slope",
            [],
            [],
            422,
            refused(
                "asked: none of these can be written from the lines given. An equation isn't "
                "rewritten in its own form, and point-slope form, x = a and y = b need a point "
                "given"
            ),
            None,
            None,
        ),
        (
            # x = -5 to 5 through a point off the axes are the only lines
            "/api/worksheets/writing_linear_equations.pdf?given=point_and_slope&asked=vertical"
            "&largest_coordinate=5&problems=20",
            [],
            [],
            422,
            refused(
                "problems: at most 10 without repeats for that choice of lines and numbers. "
                "Lower problems to 10, or raise the largest number in a point to 10."
            ),
            None,
            None,
        ),
        (
            # x = -5 to 5 through a point off the axes are 4 of the 8 pairs: they last 2 rounds and
            # 2 more, and slope-intercept form has lines enough
            "/api/worksheets/writing_linear_equations.pdf?given=point_and_slope&given=two_points"
            "&given=parallel&given=perpendicular&asked=slope_intercept&asked=vertical"
            "&largest_coordinate=5&problems=20",
            [],
            [],
            422,
            refused(
                "problems: at most 18 without repeats for that choice of lines and numbers. "
                "Lower problems to 18, or untick Vertical lines (x = a), or raise the largest "
                "number in a point to 6."
            ),
            None,
            None,
        ),
        (
            # unticking x = a and y = b would leave nothing to write, so it isn't suggested
            "/api/worksheets/writing_linear_equations.pdf?given=point_and_slope&given=two_points"
            "&given=parallel&given=perpendicular&asked=vertical&asked=horizontal"
            "&largest_coordinate=5&problems=20",
            [],
            [],
            422,
            refused(
                "problems: at most 18 without repeats for that choice of lines and numbers. "
                "Lower problems to 18, or raise the largest number in a point to 6."
            ),
            None,
            None,
        ),
        (
            # x = a and y = b are written, not given
            "/api/worksheets/writing_linear_equations.pdf?given=vertical",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "options", "given", 0],
                        "msg": "Input should be 'slope_intercept', 'standard', 'point_slope', "
                        "'point_and_slope', 'two_points', 'parallel' or 'perpendicular'",
                        "ctx": {
                            "expected": "'slope_intercept', 'standard', 'point_slope', "
                            "'point_and_slope', 'two_points', 'parallel' or 'perpendicular'"
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_writing_linear_equations_pdf(
    url: str,
    chosen: list[Any],
    sampled: list[list[tuple[int, int]]],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A request receives the PDF for its options, or the error identifying the invalid option.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    reverse_shuffle(monkeypatch)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if not expected_json else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render_line_questions(
                pdf_data["cases"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                slot_of=pdf_data["slot_of"],
                name_line=pdf_data["name_line"],
            )
        )
