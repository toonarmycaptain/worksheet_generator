"""
Tests for the graphing linear equations PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the test
case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_line_equations_worksheet``.

The PDF tests replace these functions:

- ``random.choice`` returns the picks listed in the case, as ``test_generator`` in
  ``test_core/test_line_equations`` describes for graphing, and raises ``ValueError`` for a
  pick that is not among its call's items.
- ``random.sample`` returns the rows listed, and raises ``ValueError`` for a sample not drawn
  from its call's population.
- ``random.shuffle`` reverses the list, so the pairs of a given and what is asked are dealt in
  their order, and a multiple-choice question's correct option is last.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from fractions import Fraction
from typing import Any

import pytest
from django.test import Client

from core.line_equations.data import Equation, Grid, Line, LineForm, LineQuestionData, NumberStyle
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
            # the defaults, with 1 problem: the first pair is slope-intercept form to graph;
            # y = 2/3x + 1, not through the origin, on a grid to 12 and half of 12
            "/api/worksheets/graphing_linear_equations.pdf?problems=1&sheet=1ab2c3",
            [FRACTION, False, Fraction(2, 3), Fraction(1)],
            [],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(2, -3, -3),
                            SLOPE_INTERCEPT,
                            GRAPH,
                            grid=Grid(12, 6, 1),
                            key_points=((0, 1), (-3, -1)),
                        ),
                        (),
                    )
                ],
                "answer_key": False,
                "title": "Graphing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "graphing_linear_equations-sheet-a.pdf",
        ),
        (
            # multiple choice: y = 2/3x + 1 among STAAR's wrong graphs, the signs of its slope
            # and y-intercept (the first set of mistakes), on one grid fitted to all four
            "/api/worksheets/graphing_linear_equations.pdf?multiple_choice=true&problems=1"
            "&sheet=1ab2c3",
            [FRACTION, False, Fraction(2, 3), Fraction(1), 0],
            [],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(2, -3, -3),
                            SLOPE_INTERCEPT,
                            GRAPH,
                            grid=Grid(12, 6, 1),
                            chosen=True,
                        ),
                        (
                            Equation(Line(2, 3, 3), GRAPH),
                            Equation(Line(2, -3, 3), GRAPH),
                            Equation(Line(2, 3, -3), GRAPH),
                        ),
                    )
                ],
                "answer_key": False,
                "title": "Graphing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "graphing_linear_equations-sheet-a.pdf",
        ),
        (
            # self-check tiles: the graph to find is in the answer bank, on its own grid
            "/api/worksheets/graphing_linear_equations.pdf?self_check_tiles=true&problems=1"
            "&sheet=1ab2c3",
            [FRACTION, False, Fraction(2, 3), Fraction(1)],
            [],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(2, -3, -3),
                            SLOPE_INTERCEPT,
                            GRAPH,
                            grid=Grid(12, 6, 1),
                            key_points=((0, 1), (-3, -1)),
                            chosen=True,
                        ),
                        (),
                    )
                ],
                "slot_of": REAL_CASE_SLOTS[:1],
                "answer_key": False,
                "title": "Graphing Linear Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "graphing_linear_equations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/graphing_linear_equations.pdf?multiple_choice=true"
            "&self_check_tiles=true",
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            # every option: a table of x + 2y = 6 to complete, in decimals, x left out in the
            # third row
            "/api/worksheets/graphing_linear_equations.pdf?given=standard&asked=table"
            "&number_styles=decimal&largest_coordinate=12&largest_denominator=4"
            "&whole_intercepts=true&problems=1&answer_key=true&name_line=true&title=Practice"
            "&label=Week+3&sheet=1ab2c3",
            [
                *(DECIMAL, False, Fraction(-1, 2), Fraction(3)),
                *(False, 4, False, False),
                *(1, 1, 0, 1),
            ],
            [[-4, 2, 4, 8]],
            200,
            None,
            {
                "cases": [
                    (
                        LineQuestionData(
                            Line(1, 2, 6),
                            STANDARD,
                            TABLE,
                            numbers=DECIMAL,
                            table_xs=(-4, 2, 4, 8),
                            table_blanks=(1, 1, 0, 1),
                        ),
                        (),
                    )
                ],
                "answer_key": True,
                "title": "Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "graphing_linear_equations-week-3.pdf",
        ),
        (
            # x = a isn't a function, so it isn't tabled
            "/api/worksheets/graphing_linear_equations.pdf?given=vertical&asked=table",
            [],
            [],
            422,
            refused(
                "asked: none of these fits the lines given. A table is completed from an "
                "equation or a graph, never from x = a, and a graph isn't graphed again"
            ),
            None,
            None,
        ),
        (
            # x = -4 to 4, but 0, inside a grid to 5: 8 lines
            "/api/worksheets/graphing_linear_equations.pdf?given=vertical&asked=graph"
            "&largest_coordinate=5&problems=9",
            [],
            [],
            422,
            refused(
                "problems: at most 8 without repeats for that choice of lines and numbers. "
                "Lower problems to 8, or raise the largest number in a point to 6."
            ),
            None,
            None,
        ),
        (
            # a table is asked, not given
            "/api/worksheets/graphing_linear_equations.pdf?given=table",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "options", "given", 0],
                        "msg": "Input should be 'slope_intercept', 'standard', 'point_slope', "
                        "'slope_and_intercept', 'intercepts', 'point_and_slope', 'two_points', "
                        "'vertical', 'horizontal' or 'graph'",
                        "ctx": {
                            "expected": "'slope_intercept', 'standard', 'point_slope', "
                            "'slope_and_intercept', 'intercepts', 'point_and_slope', "
                            "'two_points', 'vertical', 'horizontal' or 'graph'"
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_graphing_linear_equations_pdf(
    url: str,
    chosen: list[Any],
    sampled: list[list[int]],
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
        assert pdf_data is not None
        assert pdf_text(response.content) == pdf_text(
            render_line_questions(
                pdf_data["cases"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
                slot_of=pdf_data.get("slot_of"),
            )
        )
