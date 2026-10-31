"""The arithmetic worksheet endpoint passes its options through to the core and the renderer.

The questions are random, so ``test_arithmetic_pdf`` scripts ``random.randint`` (the operands),
and makes ``random.sample`` take the top of the allowed range of wrong answers, which shows the
operation's and ``max_number``'s limits in the PDF. The PDF must then draw what the renderer
makes for those same questions. Options the endpoint does not allow get Ninja's JSON error.
What the renderer draws is tested in ``test_arithmetic_worksheet_pdf``.

A request needs a ``sheet`` token to get the PDF. Without one it is redirected to a URL with a
token (``test_a_request_without_a_sheet_is_redirected``).
"""

import random
import secrets
from typing import Any

import pytest
from django.test import Client

from core.arithmetic import ArithmeticQuestionData, Operation
from tests.pdf_text import pdf_text
from tests.test_arithmetic_worksheet_pdf import build, render


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            "/api/worksheets/arithmetic.pdf?operation=add&problems=2&sheet=1ab2c3",
            [3, 4, 5, 6],
            200,
            None,
            {
                "cases": [
                    (ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20)),
                    (ArithmeticQuestionData(Operation.ADD, (5, 6), 11), (18, 19, 20)),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?operation=subtract&problems=2&answer_key=true"
            "&sheet=1ab2c3",
            [7, 3, 9, 2],
            200,
            None,
            {
                "cases": [
                    (ArithmeticQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10)),
                    (ArithmeticQuestionData(Operation.SUBTRACT, (9, 2), 7), (8, 9, 10)),
                ],
                "title": "Subtraction",
                "label": "Sheet A",
                "answer_key": True,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2&title=Tables&label=Day+2"
            "&sheet=1ab2c3",
            [6, 7, 2, 8],
            200,
            None,
            {
                "cases": [
                    (ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42), (98, 99, 100)),
                    (ArithmeticQuestionData(Operation.MULTIPLY, (2, 8), 16), (98, 99, 100)),
                ],
                "title": "Tables",
                "label": "Day 2",
                "answer_key": False,
            },
            "arithmetic-day-2.pdf",
        ),
        (
            # max_number=5 lowers the top of the wrong answers from 20 to 10
            "/api/worksheets/arithmetic.pdf?problems=1&max_number=5&sheet=1ab2c3",
            [3, 4],
            200,
            None,
            {
                "cases": [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (8, 9, 10))],
                "title": "Addition",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            "/api/worksheets/arithmetic.pdf?problems=1&label=&sheet=1ab2c3",
            [3, 4],
            200,
            None,
            {
                "cases": [(ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20))],
                "title": "Addition",
                "label": "",
                "answer_key": False,
            },
            "arithmetic.pdf",
        ),
        (
            # 3 problems is all the different pairs that 0 and 1 make, and the top of the wrong
            # answers is raised to 3, the number of wrong answers
            "/api/worksheets/arithmetic.pdf?problems=3&max_number=1&sheet=1ab2c3",
            [0, 0, 0, 1, 1, 1],
            200,
            None,
            {
                "cases": [
                    (ArithmeticQuestionData(Operation.ADD, (0, 0), 0), (1, 2, 3)),
                    (ArithmeticQuestionData(Operation.ADD, (0, 1), 1), (0, 2, 3)),
                    (ArithmeticQuestionData(Operation.ADD, (1, 1), 2), (0, 1, 3)),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/arithmetic.pdf?operation=divide",  # not built yet
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "operation"],
                        "msg": "Input should be 'add', 'subtract' or 'multiply'",
                        "ctx": {"expected": "'add', 'subtract' or 'multiply'"},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?problems=0",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be greater than or equal to 1",
                        "ctx": {"ge": 1},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?problems=21",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be less than or equal to 20",
                        "ctx": {"le": 20},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?title=",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["query", "title"],
                        "msg": "String should have at least 1 character",
                        "ctx": {"min_length": 1},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?max_number=0",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be greater than or equal to 1",
                        "ctx": {"ge": 1},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?max_number=25",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be less than or equal to 24",
                        "ctx": {"le": 24},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # no title: the operation's name
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=1&sheet=1ab2c3",
            [6, 7],
            200,
            None,
            {
                "cases": [(ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42), (98, 99, 100))],
                "title": "Multiplication",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            # 3 numbers make only 6 different pairs, so 7 problems cannot all be different
            "/api/worksheets/arithmetic.pdf?problems=7&max_number=2",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["query", "options"],
                        "msg": (
                            "Value error, problems: too many for that largest number, "
                            "which allows no repeats"
                        ),
                        "ctx": {
                            "error": (
                                "problems: too many for that largest number, "
                                "which allows no repeats"
                            )
                        },
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_arithmetic_pdf(
    url: str,
    drawn: list[int],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request gets the PDF for its options, or the error that says which option is wrong.

    ``randint`` gives the operands and ``sample`` takes the top of the wrong answers, so the PDF
    also shows the operation's and ``max_number``'s limits. A URL option that is dropped, ignored
    or sent to the wrong place changes the drawn text.

    - A refused request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header (24 hours, for the edge cache and
      browsers) and the text the renderer draws for ``pdf_data``: the questions with their wrong
      answers, the title and label, and whether there is an answer key.

    PDF URLs carry a ``sheet`` token, since without one the endpoint only redirects.
    """
    values = iter(drawn)
    monkeypatch.setattr(random, "randint", lambda low, high: next(values))
    monkeypatch.setattr(random, "sample", lambda population, k: list(population[-k:]))
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())

    response = client.get(url)

    assert response.status_code == status
    # headers
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if not expected_json else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render(
                questions=build(pdf_data["cases"]),
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
            )
        )


@pytest.mark.parametrize(
    ("url", "location"),
    [
        ("/api/worksheets/arithmetic.pdf", "/api/worksheets/arithmetic.pdf?sheet=1ab2c3"),
        (
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2",
            "/api/worksheets/arithmetic.pdf?operation=multiply&problems=2&sheet=1ab2c3",
        ),
        (
            "/api/worksheets/arithmetic.pdf?title=Times+Tables&label=Day+2",
            "/api/worksheets/arithmetic.pdf?title=Times+Tables&label=Day+2&sheet=1ab2c3",
        ),
        # an empty token counts as none
        (
            "/api/worksheets/arithmetic.pdf?problems=3&sheet=",
            "/api/worksheets/arithmetic.pdf?problems=3&sheet=1ab2c3",
        ),
    ],
)
def test_a_request_without_a_sheet_is_redirected(
    url: str, location: str, client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A request with no ``sheet`` token is sent to the same URL with a random token added.

    ``token_hex`` is fixed so the new URL is known. The options keep their order and an empty
    ``sheet`` is replaced. The redirect is ``no-store``: if it were cached, everyone who asked
    for those options would be sent to the same token, and so to the same sheet.
    """
    monkeypatch.setattr(secrets, "token_hex", lambda nbytes: "1ab2c3")

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == location
    assert response["Cache-Control"] == "no-store"
