"""
Tests for the strip choice PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_strip_choice_worksheet``.

The PDF tests replace these functions:

- ``random.randint`` returns the numbers listed in the test case, and raises ``ValueError`` for
  a number outside the bounds of its call.
- ``random.sample`` returns the first items, in order. The operations or two-step shapes
  therefore keep their order, so any extra problems go to the last of them, and the wording uses
  the first two names and the templates of each operation or shape from last to first.
- ``random.shuffle`` reverses the list: the problems on the sheet, and the choices of each
  problem.
- ``random.choice`` returns the ``chosen`` values listed in the test case, and raises
  ``ValueError`` for a value its call did not offer. They are, for each two-step problem, the
  number its first step carries and then each step, followed by the object of each problem.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    Unknown,
)
from core.basic_operations.representation import Prompt
from tests.helpers import (
    choice_returns,
    pdf_text,
    randint_returns,
    refused,
    render_strip_choice,
    reverse_shuffle,
    sample_first,
)


@pytest.mark.parametrize(
    ("url", "drawn", "chosen", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults: one of each operation, then shuffled, with an addition's or
            # subtraction's smaller number at most 12
            "/api/worksheets/strip_choice.pdf?sheet=1ab2c3",
            [3, 4, 3, 4, 47, 9, 47, 5],
            [("card", "cards"), ("card", "cards"), ("card", "cards"), ("card", "cards")],
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
            [("card", "cards"), ("card", "cards")],
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
            [("card", "cards")],
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
            [("card", "cards")],
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
            [("card", "cards"), ("card", "cards")],
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
            # two steps with the defaults: 4 problems among the 5 shapes, so the first, adding
            # three numbers, has none, and then the sheet is shuffled
            "/api/worksheets/strip_choice.pdf?steps=two&sheet=1ab2c3",
            [],
            [
                15,
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
                15,
                BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                ("card", "cards"),
                ("card", "cards"),
                ("card", "cards"),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                            BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
                        ),
                        Unknown.SECOND,
                        30,
                        "A store had 45 cards. It sold 3 packs with 5 cards in each pack. "
                        "How many cards does the store have left?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                            BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
                        ),
                        Unknown.FIRST,
                        19,
                        "There are 3 boxes with 5 cards in each box. Maria brings 4 more. "
                        "How many cards are there now?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                            BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                        ),
                        Unknown.FIRST,
                        6,
                        "Maria has 24 cards. 6 are in a box, and the rest are in 3 bags with the "
                        "same number in each bag. How many cards are in each bag?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.FIRST,
                        12,
                        "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                        "How many cards are left in the box?",
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
            # two steps with every option: 8 groups of 4 within 40, and two answers of 39, as
            # strip choice sheets have no tiles
            "/api/worksheets/strip_choice.pdf?operations=add&operations=multiply&steps=two"
            "&max_number=40&max_groups=8&prompt=both&problems=2&answer_key=true&name_line=true"
            "&title=Strip+Practice&label=Week+3&sheet=1ab2c3",
            [],
            [
                32,
                BasicOperationQuestionData(Operation.MULTIPLY, (8, 4), 32),
                BasicOperationQuestionData(Operation.ADD, (32, 7), 39),
                30,
                BasicOperationQuestionData(Operation.ADD, (12, 18), 30),
                BasicOperationQuestionData(Operation.ADD, (30, 9), 39),
                ("card", "cards"),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.MULTIPLY, (8, 4), 32),
                            BasicOperationQuestionData(Operation.ADD, (32, 7), 39),
                        ),
                        Unknown.FIRST,
                        39,
                        "There are 8 boxes with 4 cards in each box. Maria brings 7 more. "
                        "How many cards are there now?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.ADD, (12, 18), 30),
                            BasicOperationQuestionData(Operation.ADD, (30, 9), 39),
                        ),
                        Unknown.FIRST,
                        39,
                        "A jar held 12 cards. Maria added 18 more, and then Jamal added 9 more. "
                        "How many cards are in the jar now?",
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
            # every shape of two steps adds or subtracts
            "/api/worksheets/strip_choice.pdf?operations=multiply&operations=divide&steps=two",
            [],
            [],
            422,
            refused("operations: two steps need addition or subtraction"),
            None,
            None,
        ),
        (
            # adding three numbers depends on the largest number only
            "/api/worksheets/strip_choice.pdf?operations=add&steps=two&max_number=6&problems=7",
            [],
            [],
            422,
            refused(
                "problems: at most 6 without repeats for that largest number. Lower problems to "
                "6, or raise the largest number to 7."
            ),
            None,
            None,
        ),
        (
            # 7 multiplications with a part added, within 12 in 2 groups, and as many sums
            "/api/worksheets/strip_choice.pdf?operations=add&operations=multiply&steps=two"
            "&max_number=12&max_groups=2&problems=15",
            [],
            [],
            422,
            refused(
                "problems: at most 14 without repeats for that largest number and largest number "
                "of groups. Lower problems to 14, or raise the largest number to 13, or raise the "
                "largest number of groups to 3."
            ),
            None,
            None,
        ),
        (
            # as many groups as a choice's strip has room for
            "/api/worksheets/strip_choice.pdf?max_groups=13",
            [],
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
    chosen: list[object],
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
    choice_returns(monkeypatch, chosen)

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
