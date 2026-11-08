"""
Tests for the strip choice endpoint: its options reach the core and the renderer intact.

The tests script ``random``. ``randint`` returns the numbers listed, ``sample`` keeps the
operations' order, so any extra problems go to the last, and ``shuffle`` reverses, both the sheet
and each problem's choices. The wording takes the first two names, the last object and each
operation's last template. The PDF must then match what the renderer draws for the same
questions. Disallowed options get Ninja's JSON error. The renderer's output is tested in
``test_strip_choice_worksheet``.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.representation import Prompt
from tests.helpers import (
    choose_last,
    pdf_text,
    randint_returns,
    refused,
    render_strip_choice,
    reverse_shuffle,
    sample_first,
)


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults: one of each operation, then shuffled, with an addition's or
            # subtraction's smaller number at most 12
            "/api/worksheets/strip_choice.pdf?sheet=1ab2c3",
            [3, 4, 3, 4, 47, 9, 47, 5],
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
                        Operation.MULTIPLY,
                        (3, 4),
                        12,
                        "3 friends each have 4 cards. How many cards do they have together?",
                    ),
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (47, 9),
                        38,
                        "Maria needs 47 cards in all and has 9 so far. "
                        "How many more cards are needed?",
                    ),
                    BasicOperationQuestionData(
                        Operation.ADD,
                        (47, 5),
                        52,
                        "A basket held 47 cards. Maria added 5 more. "
                        "How many cards are in the basket now?",
                    ),
                ],
                "prompt": Prompt.WORD_PROBLEM,
                "answer_key": False,
                "title": "Strip Diagram multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "strip_choice-sheet-a.pdf",
        ),
        (
            # every option: 5 groups of 5 is over 20, and 2 groups of 2 is left out, so both are
            # redrawn
            "/api/worksheets/strip_choice.pdf?operations=multiply&operations=divide&max_number=20"
            "&max_groups=5&prompt=both&problems=2&answer_key=true&name_line=true"
            "&title=Strip+Practice&label=Week+3&sheet=1ab2c3",
            [5, 5, 4, 5, 2, 2, 3, 6],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (20, 4),
                        5,
                        "Maria divides 20 cards into 4 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (3, 6),
                        18,
                        "3 friends each have 6 cards. How many cards do they have together?",
                    ),
                ],
                "prompt": Prompt.BOTH,
                "answer_key": True,
                "title": "Strip Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "strip_choice-week-3.pdf",
        ),
        (
            # addition only, shown as equations
            "/api/worksheets/strip_choice.pdf?operations=add&prompt=equation&problems=1"
            "&sheet=1ab2c3",
            [47, 5],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.ADD,
                        (47, 5),
                        52,
                        "A basket held 47 cards. Maria added 5 more. "
                        "How many cards are in the basket now?",
                    ),
                ],
                "prompt": Prompt.EQUATION,
                "answer_key": False,
                "title": "Strip Diagram multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "strip_choice-sheet-a.pdf",
        ),
        (
            # the largest number of groups caps a subtraction's smaller number, which its wrong
            # choices multiply and divide by
            "/api/worksheets/strip_choice.pdf?operations=subtract&max_groups=3&problems=1"
            "&sheet=1ab2c3",
            [47, 3],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (47, 3),
                        44,
                        "Maria needs 47 cards in all and has 3 so far. "
                        "How many more cards are needed?",
                    ),
                ],
                "prompt": Prompt.WORD_PROBLEM,
                "answer_key": False,
                "title": "Strip Diagram multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "strip_choice-sheet-a.pdf",
        ),
        (
            # Split evenly, each operation needs only its share: 2 groups of 3 is the only
            # multiplication within 6 in 2 groups, and enough for 1 of 2 problems.
            "/api/worksheets/strip_choice.pdf?operations=add&operations=multiply&max_number=6"
            "&max_groups=2&problems=2&sheet=1ab2c3",
            [2, 3, 4, 2],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (2, 3),
                        6,
                        "2 friends each have 3 cards. How many cards do they have together?",
                    ),
                    BasicOperationQuestionData(
                        Operation.ADD,
                        (4, 2),
                        6,
                        "A basket held 4 cards. Maria added 2 more. "
                        "How many cards are in the basket now?",
                    ),
                ],
                "prompt": Prompt.WORD_PROBLEM,
                "answer_key": False,
                "title": "Strip Diagram multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "strip_choice-sheet-a.pdf",
        ),
        (
            # 3 can't be split so: either limit can be raised
            "/api/worksheets/strip_choice.pdf?operations=add&operations=multiply&max_number=6"
            "&max_groups=2&problems=3",
            [],
            422,
            refused(
                "problems: at most 2 without repeats for that largest number and largest number "
                "of groups. Lower problems to 2, or raise the largest number to 8, or raise the "
                "largest number of groups to 3."
            ),
            None,
            None,
        ),
        (
            # subtraction's count depends on the largest number only
            "/api/worksheets/strip_choice.pdf?operations=subtract&max_number=10&max_groups=5"
            "&problems=12",
            [],
            422,
            refused(
                "problems: at most 9 without repeats for that largest number. Lower problems to "
                "9, or raise the largest number to 13."
            ),
            None,
            None,
        ),
        (
            # 2 groups of 20 is the most in 2 groups, so only the groups can be raised
            "/api/worksheets/strip_choice.pdf?operations=multiply&max_groups=2&problems=20",
            [],
            422,
            refused(
                "problems: at most 18 without repeats for that largest number and largest number "
                "of groups. Lower problems to 18, or raise the largest number of groups to 3."
            ),
            None,
            None,
        ),
        (
            # the groups are at their most, so only the largest number can be raised
            "/api/worksheets/strip_choice.pdf?operations=multiply&max_number=10&problems=20",
            [],
            422,
            refused(
                "problems: at most 7 without repeats for that largest number and largest number "
                "of groups. Lower problems to 7, or raise the largest number to 18."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/strip_choice.pdf?operations=multiply&max_number=20&max_groups=2"
            "&problems=12",
            [],
            422,
            refused(
                "problems: at most 8 without repeats for that largest number and largest number "
                "of groups. Lower problems to 8, or raise the largest number to 28, or raise the "
                "largest number of groups to 3."
            ),
            None,
            None,
        ),
        (
            # as many groups as a choice's strip has room for
            "/api/worksheets/strip_choice.pdf?max_groups=13",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_groups"],
                        "msg": "Input should be less than or equal to 12",
                        "ctx": {"le": 12},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/strip_choice.pdf?max_groups=1",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_groups"],
                        "msg": "Input should be greater than or equal to 2",
                        "ctx": {"ge": 2},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/strip_choice.pdf?max_number=1000",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be less than or equal to 999",
                        "ctx": {"le": 999},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # no mixed until the wording axis is settled
            "/api/worksheets/strip_choice.pdf?prompt=mixed",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "prompt"],
                        "msg": "Input should be 'word_problem', 'equation' or 'both'",
                        "ctx": {"expected": "'word_problem', 'equation' or 'both'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_strip_choice_pdf(
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

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    choose_last(monkeypatch)

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
            render_strip_choice(
                questions=pdf_data["questions"],
                prompt=pdf_data["prompt"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
