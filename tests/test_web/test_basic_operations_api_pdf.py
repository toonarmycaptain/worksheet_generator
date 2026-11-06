"""
Tests for the basic operations worksheet endpoint: its options reach the core and the renderer
intact.

The questions are random, so ``test_basic_operations_pdf`` scripts ``random.randint`` (the operands)
and makes ``random.sample`` take the top of the allowed wrong-answer range, which exposes the
operation's and ``max_number``'s limits in the PDF. The PDF must then match what the renderer
draws for the same questions. Disallowed options get Ninja's JSON error. The renderer's output
is tested in ``test_basic_operations_worksheet``.

A request needs a ``sheet`` token to receive the PDF; without one, it is redirected to a URL
with a token, which ``test_sheet_redirect`` tests.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.basic_operations.generator import MAXIMUM_OPERAND
from tests.helpers import (
    pdf_text,
    randint_returns,
    refused,
    render_basic_operations,
    render_missing_numbers,
    reverse_shuffle,
    sample_last,
)


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            "/api/worksheets/basic_operations.pdf?operation=add&problems=2&sheet=1ab2c3",
            [3, 4, 5, 6],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20)),
                    (BasicOperationQuestionData(Operation.ADD, (5, 6), 11), (18, 19, 20)),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=add&problems=2&name_line=true&sheet=1ab2c3",
            [3, 4, 5, 6],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20)),
                    (BasicOperationQuestionData(Operation.ADD, (5, 6), 11), (18, 19, 20)),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "name_line": True,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=subtract&problems=2&answer_key=true"
            "&sheet=1ab2c3",
            [7, 3, 9, 2],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.SUBTRACT, (7, 3), 4), (8, 9, 10)),
                    (BasicOperationQuestionData(Operation.SUBTRACT, (9, 2), 7), (8, 9, 10)),
                ],
                "title": "Subtraction",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": True,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=multiply&problems=2&title=Tables&label=Day+2"
            "&sheet=1ab2c3",
            [6, 7, 2, 8],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42), (98, 99, 100)),
                    (BasicOperationQuestionData(Operation.MULTIPLY, (2, 8), 16), (98, 99, 100)),
                ],
                "title": "Tables",
                "label": "Day 2",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-day-2.pdf",
        ),
        (
            # max_number=5 lowers the top of the wrong answers from 20 to 10
            "/api/worksheets/basic_operations.pdf?problems=1&max_number=5&sheet=1ab2c3",
            [3, 4],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [(BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (8, 9, 10))],
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?problems=1&label=&sheet=1ab2c3",
            [3, 4],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [(BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (18, 19, 20))],
                "title": "Addition",
                "label": "",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations.pdf",
        ),
        (
            # 3 problems is all the different pairs that 0 and 1 make, and the top of the wrong
            # answers is raised to 3, the number of wrong answers
            "/api/worksheets/basic_operations.pdf?problems=3&max_number=1&sheet=1ab2c3",
            [0, 0, 0, 1, 1, 1],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.ADD, (0, 0), 0), (1, 2, 3)),
                    (BasicOperationQuestionData(Operation.ADD, (0, 1), 1), (0, 2, 3)),
                    (BasicOperationQuestionData(Operation.ADD, (1, 1), 2), (0, 1, 3)),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            # not an operation the sheet has
            "/api/worksheets/basic_operations.pdf?operation=power",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "operation"],
                        "msg": "Input should be 'add', 'subtract', 'multiply' or 'divide'",
                        "ctx": {"expected": "'add', 'subtract', 'multiply' or 'divide'"},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?problems=0",
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
            "/api/worksheets/basic_operations.pdf?problems=21",
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
            "/api/worksheets/basic_operations.pdf?title=",
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
            "/api/worksheets/basic_operations.pdf?max_number=0",
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
            f"/api/worksheets/basic_operations.pdf?max_number={MAXIMUM_OPERAND + 1}",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": (f"Input should be less than or equal to {MAXIMUM_OPERAND}"),
                        "ctx": {"le": MAXIMUM_OPERAND},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # no title: the operation's name
            "/api/worksheets/basic_operations.pdf?operation=multiply&problems=1&sheet=1ab2c3",
            [6, 7],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42), (98, 99, 100))
                ],
                "title": "Multiplication",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # 3 numbers make only 6 different pairs, so 7 problems cannot all be different
            "/api/worksheets/basic_operations.pdf?problems=7&max_number=2",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["query", "options"],
                        "msg": (
                            "Value error, problems: at most 6 without repeats for that largest "
                            "number. Lower problems to 6, or raise the largest number to 3."
                        ),
                        "ctx": {
                            "error": (
                                "problems: at most 6 without repeats for that largest number. "
                                "Lower problems to 6, or raise the largest number to 3."
                            )
                        },
                    },
                ],
            },
            None,
            None,
        ),
        (
            # division: a divisor, then a quotient, with the wrong answers up to the largest
            # dividend, 100 by default
            "/api/worksheets/basic_operations.pdf?operation=divide&problems=2&sheet=1ab2c3",
            [4, 7, 3, 5],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.DIVIDE, (28, 4), 7), (98, 99, 100)),
                    (BasicOperationQuestionData(Operation.DIVIDE, (15, 3), 5), (98, 99, 100)),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # largest_dividend=20 lowers the top of the wrong answers to 20
            "/api/worksheets/basic_operations.pdf?operation=divide&problems=1&largest_dividend=20"
            "&largest_divisor=5&sheet=1ab2c3",
            [4, 5],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5), (18, 19, 20)),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # division ignores the largest number
            "/api/worksheets/basic_operations.pdf?operation=divide&problems=1&max_number=5&sheet=1ab2c3",
            [4, 7],
            200,
            None,
            {
                "render": render_basic_operations,
                "cases": [
                    (BasicOperationQuestionData(Operation.DIVIDE, (28, 4), 7), (98, 99, 100)),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=add&missing_number=dividend",
            [],
            422,
            refused("missing_number: only division has a missing dividend or divisor"),
            None,
            None,
        ),
        (
            # dividing by 1, 2 and 3 into dividends up to 3 makes only 8 different questions
            "/api/worksheets/basic_operations.pdf?operation=divide&problems=20&largest_dividend=3"
            "&largest_divisor=3",
            [],
            422,
            refused(
                "problems: at most 8 without repeats for that largest dividend and divisor. "
                "Lower problems to 8, or raise the largest dividend to 10."
            ),
            None,
            None,
        ),
        (
            # dividends and divisors up to 10 make 15 fact families. Raising the largest divisor
            # alone adds none, since no divisor can be larger than the dividend.
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=divisor&problems=20"
            "&largest_dividend=10&largest_divisor=10",
            [],
            422,
            refused(
                "problems: at most 15 without repeats for that largest dividend and divisor. "
                "Lower problems to 15, or raise the largest dividend to 13."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&largest_dividend=0",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "largest_dividend"],
                        "msg": "Input should be greater than or equal to 1",
                        "ctx": {"ge": 1},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=divide"
            f"&largest_divisor={MAXIMUM_OPERAND + 1}",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "largest_divisor"],
                        "msg": (f"Input should be less than or equal to {MAXIMUM_OPERAND}"),
                        "ctx": {"le": MAXIMUM_OPERAND},
                    },
                ],
            },
            None,
            None,
        ),
        # a missing dividend or divisor: equations to fill in, drawn as a divisor then a quotient
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=dividend&problems=2"
            "&sheet=1ab2c3",
            [4, 7, 3, 5],
            200,
            None,
            {
                "render": render_missing_numbers,
                "cases": [
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 3, 5, 15), ()),
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28), ()),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=divisor&problems=2"
            "&answer_key=true&title=Find+the+Divisor&label=Day+2&sheet=1ab2c3",
            [4, 7, 3, 5],
            200,
            None,
            {
                "render": render_missing_numbers,
                "cases": [
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 15, 5, 3), ()),
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4), ()),
                ],
                "title": "Find the Divisor",
                "label": "Day 2",
                "name_line": False,
                "answer_key": True,
            },
            "basic_operations-day-2.pdf",
        ),
        (
            # mixed: the missing divisor is made first, then the sheet is reversed
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=mixed&problems=2"
            "&sheet=1ab2c3",
            [4, 7, 3, 5],
            200,
            None,
            {
                "render": render_missing_numbers,
                "cases": [
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 3, 5, 15), ()),
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4), ()),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # limits above the defaults reach the generator: with the default largest divisor
            # of 10, the divisor 20 could not be drawn
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=dividend&problems=1"
            "&largest_dividend=500&largest_divisor=20&sheet=1ab2c3",
            [20, 25],
            200,
            None,
            {
                "render": render_missing_numbers,
                "cases": [
                    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 20, 25, 500), ()),
                ],
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
    ],
)
def test_basic_operations_pdf(
    url: str,
    drawn: list[int],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A request receives the PDF for its options, or the error identifying the invalid option.

    ``randint`` supplies the operands, or a divisor then a quotient, and rejects any value outside
    the requested range, as the real one never returns one. ``sample`` takes the top of the
    wrong answers, and ``shuffle`` reverses the options, or a missing-number sheet's equations.
    The PDF therefore also reflects the operation's and ``max_number``'s limits, and a URL option
    that is dropped, ignored or misrouted changes the drawn text or fails a draw.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header (24 hours, for the edge cache and
      browsers) and the text that ``pdf_data["render"]`` draws for ``pdf_data``: the questions
      with their wrong answers, the title and label, and whether there is an answer key.

    PDF URLs carry a ``sheet`` token, since without one the endpoint only redirects.
    """
    randint_returns(monkeypatch, drawn)
    sample_last(monkeypatch)
    reverse_shuffle(monkeypatch)

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
            pdf_data["render"](
                cases=pdf_data["cases"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
