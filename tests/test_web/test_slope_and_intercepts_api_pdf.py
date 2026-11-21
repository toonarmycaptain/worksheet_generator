"""
Tests for the slope and intercepts PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the test
case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_line_equations_worksheet``.

The PDF tests replace these functions:

- ``random.choice`` returns the picks listed in the case, as ``test_generator`` in
  ``test_core/test_line_equations`` describes, and raises ``ValueError`` for a pick that is not
  among its call's items.
- ``random.sample`` returns the points listed, and raises ``ValueError`` for a sample not drawn
  from its call's population.
- ``random.shuffle`` reverses the list, so the pairs of a form and a question are dealt in their
  order, and a multiple-choice question's correct option is last.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from fractions import Fraction
from typing import Any

import pytest
from django.test import Client

from core.line_equations.data import (
    Grid,
    Line,
    LineFeature,
    LineForm,
    LineQuestionData,
)
from core.written_numbers import NumberStyle
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


@pytest.mark.parametrize(
    ("url", "chosen", "sampled", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: the first pair is slope-intercept form and the slope;
            # y = 3/4x + 5/4, not in function notation, not through the origin
            "/api/worksheets/slope_and_intercepts.pdf?problems=1&sheet=1ab2c3",
            [FRACTION, False, False, Fraction(3, 4), Fraction(5, 4)],
            [],
            200,
            None,
            {
                "cases": [(LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, SLOPE), ())],
                "slot_of": None,
                "answer_key": False,
                "title": "Slope and Intercepts",
                "label": "Sheet A",
                "name_line": False,
            },
            "slope_and_intercepts-sheet-a.pdf",
        ),
        (
            # every option for free response: two points on y = 1/2x + 3 with a blank grid
            # beside them, to 12 and 2 gridlines past the highest point, 4, the y-intercept as a
            # point, in decimals
            "/api/worksheets/slope_and_intercepts.pdf?given=two_points&blank_grids=true"
            "&asked=y_intercept&intercept_answers=point&number_styles=decimal"
            "&largest_coordinate=12&largest_denominator=4&whole_intercepts=true&problems=1"
            "&answer_key=true&name_line=true&title=Practice&label=Week+3&sheet=1ab2c3",
            [DECIMAL, True, "sloped", False, Fraction(1, 2), Fraction(3), True],
            [[(2, 4), (-4, 1)]],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(1, -2, -6),
                            TWO_POINTS,
                            Y_INTERCEPT,
                            ((2, 4), (-4, 1)),
                            True,
                            DECIMAL,
                            grid=Grid(12, 6, 1),
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
            "slope_and_intercepts-week-3.pdf",
        ),
        (
            # a table of y = -1/2x + 3: its row (2, 2), 4 rows unevenly spaced, down the page
            "/api/worksheets/slope_and_intercepts.pdf?given=table&asked=slope&problems=1"
            "&sheet=1ab2c3",
            [FRACTION, "sloped", False, Fraction(-1, 2), Fraction(3), False, 4, False, False],
            [[(2, 2)], [-4, 4, 8]],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(1, 2, 6), TABLE, SLOPE, ((2, 2),), table_xs=(-4, 2, 4, 8)
                        ),
                        (),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Slope and Intercepts",
                "label": "Sheet A",
                "name_line": False,
            },
            "slope_and_intercepts-sheet-a.pdf",
        ),
        (
            # multiple choice: 3x + 4y = 8's slope, among STAAR's mistakes
            "/api/worksheets/slope_and_intercepts.pdf?given=standard&asked=slope"
            "&multiple_choice=true&problems=1&sheet=1ab2c3",
            [FRACTION, False, Fraction(-3, 4), Fraction(2)],
            [],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
                        (Fraction(-4, 3), Fraction(3, 4), Fraction(4, 3)),
                    )
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Slope and Intercepts",
                "label": "Sheet A",
                "name_line": False,
            },
            "slope_and_intercepts-sheet-a.pdf",
        ),
        (
            # self-check tiles: x = 3, then x = -5 as a point, the one pair dealt twice
            "/api/worksheets/slope_and_intercepts.pdf?given=vertical&asked=x_intercept"
            "&whole_intercepts=true&self_check_tiles=true&problems=2&sheet=1ab2c3",
            [FRACTION, False, Fraction(3), FRACTION, True, Fraction(-5)],
            [],
            200,
            None,
            {
                "cases": [
                    (LineQuestionData(Line(1, 0, 3), VERTICAL, X_INTERCEPT), ()),
                    (LineQuestionData(Line(1, 0, -5), VERTICAL, X_INTERCEPT, (), True), ()),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "title": "Slope and Intercepts",
                "label": "Sheet A",
                "name_line": False,
            },
            "slope_and_intercepts-sheet-a.pdf",
        ),
        (
            "/api/worksheets/slope_and_intercepts.pdf?multiple_choice=true&self_check_tiles=true",
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/slope_and_intercepts.pdf?given=vertical&asked=y_intercept",
            [],
            [],
            422,
            refused(
                "asked: none of these fits the lines given. A vertical line has only a slope and "
                "an x-intercept, a horizontal line has no x-intercept or zero, and a point and "
                "the slope give the slope away"
            ),
            None,
            None,
        ),
        (
            # x = -5 to 5 are the only lines
            "/api/worksheets/slope_and_intercepts.pdf?given=vertical&asked=x_intercept"
            "&whole_intercepts=true&largest_coordinate=5&problems=20",
            [],
            [],
            422,
            refused(
                "problems: at most 11 without repeats for that choice of lines and numbers. "
                "Lower problems to 11, or raise the largest number in a point to 10."
            ),
            None,
            None,
        ),
        (
            # x = -5 to 5 are 2 of the 3 pairs: they last 5 rounds and 1 more, and unticking x = a
            # leaves a point and slope's lines
            "/api/worksheets/slope_and_intercepts.pdf?given=vertical&given=point_and_slope"
            "&asked=slope&asked=x_intercept&whole_intercepts=true&largest_coordinate=5"
            "&largest_denominator=1&problems=20",
            [],
            [],
            422,
            refused(
                "problems: at most 16 without repeats for that choice of lines and numbers. "
                "Lower problems to 16, or untick Vertical lines (x = a), or raise the largest "
                "number in a point to 7."
            ),
            None,
            None,
        ),
        (
            # tiles mixing kinds of answer: 21 y-intercepts from -10 to 10 make 11 questions
            "/api/worksheets/slope_and_intercepts.pdf?given=vertical&given=horizontal"
            "&whole_intercepts=true&largest_coordinate=10&largest_denominator=1"
            "&self_check_tiles=true&problems=12",
            [],
            [],
            422,
            refused(
                "problems: at most 11 without repeated answers for that choice of lines and "
                "numbers. Lower problems to 11, or raise the largest number in a point to 11."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/slope_and_intercepts.pdf?intercept_answers=pair",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "options", "intercept_answers", 0],
                        "msg": "Input should be 'number' or 'point'",
                        "ctx": {"expected": "'number' or 'point'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_slope_and_intercepts_pdf(
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
