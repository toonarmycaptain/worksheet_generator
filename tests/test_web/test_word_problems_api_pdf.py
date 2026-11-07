"""
Tests for the word problems endpoint: its options reach the core and the renderer intact.

The tests script ``random``. ``choices`` returns the operations listed as picks, ``randint``
the operands listed, and ``shuffle`` reverses, so the sizes come in reverse order and the
complex tile pattern runs from L to A.
The wording takes the first two names, the last object and each operation's last template.
``conventional_slot_of`` gives the slots of a real case. The PDF must then match what the
renderer draws for the same questions. Disallowed options get Ninja's JSON error. The renderer's
output is tested in ``test_word_problems_worksheet``.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.representation import Picture
from tests.data import REAL_CASE_SLOTS
from tests.helpers import (
    choices_returns,
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    refused,
    render_word_problems,
    reverse_shuffle,
    sample_first,
)

# drawn as 40 and 150: 2 and 3 digits, swapped so the larger is first
SUBTRACT = BasicOperationQuestionData(
    Operation.SUBTRACT,
    (150, 40),
    110,
    "Maria needs 150 cards in all and has 40 so far. How many more cards are needed?",
)
ADD = BasicOperationQuestionData(
    Operation.ADD,
    (47, 25),
    72,
    "A basket held 47 cards. Maria added 25 more. How many cards are in the basket now?",
)


@pytest.mark.parametrize(
    ("url", "picks", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 2 problems: subtraction then addition, each with its hint
            "/api/worksheets/word_problems.pdf?problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "hints": True,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # addition only
            "/api/worksheets/word_problems.pdf?operations=add&problems=1&no_hints=true"
            "&answer_key=true&title=Story+Problems&label=Day+2&name_line=true&sheet=1ab2c3",
            [Operation.ADD],
            [47, 25],
            200,
            None,
            {
                "questions": [ADD],
                "hints": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Story Problems",
                "label": "Day 2",
                "name_line": True,
            },
            "word_problems-day-2.pdf",
        ),
        (
            # Tiles, with the simple pattern by default. Their answers must differ, so 55 + 55,
            # also 110, is redrawn.
            "/api/worksheets/word_problems.pdf?self_check_tiles=true&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 55, 55, 47, 25],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "hints": True,
                "slot_of": (7, 9),
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            "/api/worksheets/word_problems.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=2&answer_key=true&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "hints": True,
                "slot_of": (11, 10),
                "answer_key": True,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/word_problems.pdf?self_check_tiles=true&problems=13",
            [],
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?problems=21",
            [],
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
            # multiplication only: 3 groups of 4
            "/api/worksheets/word_problems.pdf?operations=multiply&problems=1&sheet=1ab2c3",
            [Operation.MULTIPLY],
            [3, 4],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (3, 4),
                        12,
                        "3 friends each have 4 cards. How many cards do they have together?",
                    ),
                ],
                "hints": True,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # all four ticked: division, then addition with the one size, 2 and 2 digits
            "/api/worksheets/word_problems.pdf?operations=add&operations=subtract"
            "&operations=multiply&operations=divide&problems=2&answer_key=true&sheet=1ab2c3",
            [Operation.DIVIDE, Operation.ADD],
            [3, 4, 47, 25],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (12, 3),
                        4,
                        "Maria divides 12 cards into 3 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    ADD,
                ],
                "hints": True,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # division with tiles: 3 groups of 4, then 5 groups of 6, with the last two templates
            "/api/worksheets/word_problems.pdf?operations=divide&self_check_tiles=true&problems=2"
            "&sheet=1ab2c3",
            [Operation.DIVIDE, Operation.DIVIDE],
            [3, 4, 5, 6],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (12, 3),
                        4,
                        "Maria divides 12 cards into 3 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (30, 5),
                        6,
                        "30 cards are placed in 5 equal rows. How many cards are in each row?",
                    ),
                ],
                "hints": True,
                "slot_of": (7, 9),
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # only the pictures that can be drawn are accepted
            "/api/worksheets/word_problems.pdf?picture=blocks",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "picture"],
                        "msg": "Input should be 'strip'",
                        "ctx": {"expected": "'strip'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_word_problems_pdf(
    url: str,
    picks: list[Operation],
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

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    choices_returns(monkeypatch, picks)
    randint_returns(monkeypatch, drawn)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    choose_last(monkeypatch)
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
            render_word_problems(
                questions=pdf_data["questions"],
                picture=Picture.STRIP,
                hints=pdf_data["hints"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
