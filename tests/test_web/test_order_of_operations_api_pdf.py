"""
Tests for the order of operations PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, call the
generator with the settings its options describe, and draw the questions the generator returns:
its ``pdf_text`` must equal that of the PDF the renderer makes from them. An invalid request
must return 422 with the Django Ninja validation error and no PDF headers. The renderer itself
is tested in ``test_order_of_operations_worksheet``, and the generator in
``test_core/test_order_of_operations``.

The generator draws many random numbers for each expression, so instead of scripting them, the
endpoint's generator is replaced: it records what it's called with, and returns the case's
questions. ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns
the slots of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.arithmetic_expressions.random_expressions import NumberKind
from core.arithmetic_expressions.representation import parse
from core.order_of_operations.data import (
    GroupSymbols,
    OrderOfOperationsQuestion,
    QuestionType,
    SheetSettings,
    ValueQuestionData,
)
from core.question import FreeResponse, MultipleChoice, Question
from tests.data import REAL_CASE_SLOTS
from tests.helpers import (
    conventional_slot_of_returns,
    pdf_text,
    refused,
    render_order_of_operations,
)

WHOLE, DECIMAL, FRACTION = NumberKind
EVERY_TYPE = list(QuestionType)
VALUE_972 = ValueQuestionData(parse("[45 - (6 + 3)] * 27"), True, 972)
VALUE_144 = ValueQuestionData(parse("3(25 + 19) + 4(3)"), True, 144)


@pytest.mark.parametrize(
    ("url", "returned", "expected_call", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 1 problem: every type, STAAR's levels, every kind of number,
            # brackets, missing signs, 50 and 12
            "/api/worksheets/order_of_operations.pdf?problems=1&sheet=1ab2c3",
            [Question(VALUE_972, FreeResponse())],
            (1, EVERY_TYPE, SheetSettings(), False, False),
            200,
            None,
            {"slot_of": None, "answer_key": False, "title": "Order of Operations"},
            "order_of_operations-sheet-a.pdf",
        ),
        (
            # every option for multiple choice
            "/api/worksheets/order_of_operations.pdf?question_types=value&question_types=find_error"
            "&grouping=none&grouping=two&group_symbols=mixed&implied=false&numbers=decimal"
            "&largest_number=200&largest_multiplier=30&multiple_choice=true&problems=1"
            "&answer_key=true&name_line=true&title=Simplify&label=Week+3&sheet=1ab2c3",
            [Question(VALUE_972, MultipleChoice((1134, 972, 198, 1206), frozenset({1})))],
            (
                1,
                [QuestionType.VALUE, QuestionType.FIND_ERROR],
                SheetSettings(
                    levels=(0, 2),
                    numbers=(DECIMAL,),
                    symbols=GroupSymbols.MIXED,
                    implied=False,
                    largest_number=200,
                    largest_multiplier=30,
                ),
                True,
                False,
            ),
            200,
            None,
            {"slot_of": None, "answer_key": True, "title": "Simplify", "label": "Week 3"},
            "order_of_operations-week-3.pdf",
        ),
        (
            # tiles: the simple pattern's slots
            "/api/worksheets/order_of_operations.pdf?question_types=value&numbers=whole"
            "&numbers=fraction&grouping=one&group_symbols=parentheses&self_check_tiles=true"
            "&problems=2&sheet=1ab2c3",
            [Question(VALUE_972, FreeResponse()), Question(VALUE_144, FreeResponse())],
            (
                2,
                [QuestionType.VALUE],
                SheetSettings(
                    levels=(1,), numbers=(WHOLE, FRACTION), symbols=GroupSymbols.PARENTHESES
                ),
                False,
                True,
            ),
            200,
            None,
            {"slot_of": REAL_CASE_SLOTS[:2], "answer_key": False, "title": "Order of Operations"},
            "order_of_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/order_of_operations.pdf?self_check_tiles=true&multiple_choice=true",
            [],
            None,
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            # a type with no tiles form
            "/api/worksheets/order_of_operations.pdf?self_check_tiles=true&question_types=value"
            "&question_types=parentheses&question_types=find_error",
            [],
            None,
            422,
            refused(
                "question_types: What the parentheses show and Find the error can't be asked "
                "with self-check tiles"
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/order_of_operations.pdf?self_check_tiles=true&question_types=value"
            "&problems=13",
            [],
            None,
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # how many have the value, alone: counts 0 to 4
            "/api/worksheets/order_of_operations.pdf?self_check_tiles=true"
            "&question_types=has_value&problems=6",
            [],
            None,
            422,
            refused(
                "problems: at most 5 without repeated answers for that choice of question "
                "types. Lower problems to 5."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/order_of_operations.pdf?largest_number=9",
            [],
            None,
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "largest_number"],
                        "msg": "Input should be greater than or equal to 10",
                        "ctx": {"ge": 10},
                    }
                ]
            },
            None,
            None,
        ),
    ],
)
def test_order_of_operations_pdf(
    url: str,
    returned: list[OrderOfOperationsQuestion],
    expected_call: tuple[int, list[QuestionType], SheetSettings, bool, bool] | None,
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The endpoint calls the generator with the request's options and returns the PDF of what it
    makes, or refuses invalid options before drawing anything.
    """
    calls: list[tuple[int, list[QuestionType], SheetSettings, bool, bool]] = []

    def generate(
        count: int,
        question_types: list[QuestionType],
        settings: SheetSettings,
        *,
        multiple_choice: bool,
        distinct_answers: bool,
    ) -> list[OrderOfOperationsQuestion]:
        calls.append((count, question_types, settings, multiple_choice, distinct_answers))
        return returned

    monkeypatch.setattr("worksheets.registry.generate_order_of_operations_questions", generate)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if filename else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json is not None:
        assert (response.json(), calls) == (expected_json, [])
    else:
        assert pdf_data is not None
        expected_pdf = render_order_of_operations(
            returned,
            pdf_data["slot_of"],
            pdf_data["answer_key"],
            pdf_data["title"],
            pdf_data.get("label", "Sheet A"),
            name_line="label" in pdf_data,
        )
        assert (pdf_text(response.content), calls) == (pdf_text(expected_pdf), [expected_call])
