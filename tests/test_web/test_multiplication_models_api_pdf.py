"""
Tests for the multiplication models PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_multiplication_models_worksheet``.

The PDF tests replace these functions:

- ``random.choice`` returns the last item. Each problem is therefore the last fact left within
  the limits, ordered by number of groups and then group size, so the facts drawn show the
  limits, and its wording uses the last object. Of its models, the repeated addition is the
  type left out, each wrong model is the last of its type, and each array that may lie either
  way is turned round.
- ``random.sample`` returns the first items, in order. The wording therefore uses the first two
  names and the multiplication templates from last to first, and the other two wrong models are
  an array and a number line.
- ``random.shuffle`` reverses the list, so the three correct models of each problem come last.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.multiplication_models import Array, EqualJumpLine, RepeatedAddition
from core.basic_operations.representation import EqualStripDiagram
from core.question import MultipleChoice, Question
from tests.helpers import (
    choose_last,
    pdf_text,
    refused,
    render_multiplication_models,
    reverse_shuffle,
    sample_first,
)


@pytest.mark.parametrize(
    ("url", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults: 4 problems, the last facts with factors up to 12 within 100, and the
            # number lines' jumps numbered
            "/api/worksheets/multiplication_models.pdf?sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (12, 8),
                            96,
                            "12 friends each have 8 cards. How many cards do they have together?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(8, 8),
                                Array(12, 12),
                                RepeatedAddition((12, 8)),
                                EqualStripDiagram(12, 8, None),
                                EqualJumpLine(12, 8),
                                Array(8, 12),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (12, 7),
                            84,
                            "Maria buys 12 packs of cards with 7 in each pack. "
                            "How many cards in all?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(7, 7),
                                Array(12, 12),
                                RepeatedAddition((12, 7)),
                                EqualStripDiagram(12, 7, None),
                                EqualJumpLine(12, 7),
                                Array(7, 12),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (12, 6),
                            72,
                            "Each basket has 6 cards. How many cards are in 12 baskets?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(6, 6),
                                Array(12, 12),
                                RepeatedAddition((12, 6)),
                                EqualStripDiagram(12, 6, None),
                                EqualJumpLine(12, 6),
                                Array(6, 12),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (12, 5),
                            60,
                            "Maria plants 12 rows with 5 flowers in each row. "
                            "How many flowers did Maria plant?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(5, 5),
                                Array(12, 12),
                                RepeatedAddition((12, 5)),
                                EqualStripDiagram(12, 5, None),
                                EqualJumpLine(12, 5),
                                Array(5, 12),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                ],
                "jump_labels": True,
                "answer_key": False,
                "title": "Multiplication Models multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "multiplication_models-sheet-a.pdf",
        ),
        (
            # Every option: the last facts with factors up to 4 within 12. 4 groups of 4 is over
            # 12, and 3 groups of 4 never comes, as 4 groups of 3 came first.
            "/api/worksheets/multiplication_models.pdf?max_factor=4&max_product=12&problems=3"
            "&no_jump_labels=true&answer_key=true&name_line=true&title=Models+Practice"
            "&label=Week+3&sheet=1ab2c3",
            200,
            None,
            {
                "questions": [
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (4, 3),
                            12,
                            "4 friends each have 3 cards. How many cards do they have together?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(3, 3),
                                Array(2, 4),
                                RepeatedAddition((4, 3)),
                                EqualStripDiagram(4, 3, None),
                                EqualJumpLine(4, 3),
                                Array(3, 4),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (4, 2),
                            8,
                            "Maria buys 4 packs of cards with 2 in each pack. "
                            "How many cards in all?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(2, 2),
                                Array(4, 4),
                                RepeatedAddition((4, 2)),
                                EqualStripDiagram(4, 2, None),
                                EqualJumpLine(4, 2),
                                Array(2, 4),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                    Question(
                        BasicOperationQuestionData(
                            Operation.MULTIPLY,
                            (3, 3),
                            9,
                            "Each basket has 3 cards. How many cards are in 3 baskets?",
                        ),
                        MultipleChoice(
                            (
                                EqualJumpLine(2, 3),
                                Array(3, 2),
                                RepeatedAddition((3, 3)),
                                EqualStripDiagram(3, 3, None),
                                EqualJumpLine(3, 3),
                                Array(3, 3),
                            ),
                            frozenset({3, 4, 5}),
                        ),
                    ),
                ],
                "jump_labels": False,
                "answer_key": True,
                "title": "Models Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "multiplication_models-week-3.pdf",
        ),
        (
            # 2 x 3, 2 x 4, 3 x 3 and 3 x 4: either limit can be raised
            "/api/worksheets/multiplication_models.pdf?max_factor=4&max_product=12&problems=5",
            422,
            refused(
                "problems: at most 4 without repeats for that largest factor and largest "
                "product. Lower problems to 4, or raise the largest factor to 5, or raise the "
                "largest product to 16."
            ),
            None,
            None,
        ),
        (
            # the factor can be raised to its most: only 2 x 12 is within 24 and not within 11
            "/api/worksheets/multiplication_models.pdf?max_factor=11&max_product=24&problems=19",
            422,
            refused(
                "problems: at most 18 without repeats for that largest factor and largest "
                "product. Lower problems to 18, or raise the largest factor to 12, or raise the "
                "largest product to 25."
            ),
            None,
            None,
        ),
        (
            # the product is at its most, so only the factor can be raised
            "/api/worksheets/multiplication_models.pdf?max_factor=3&problems=5",
            422,
            refused(
                "problems: at most 2 without repeats for that largest factor and largest "
                "product. Lower problems to 2, or raise the largest factor to 4."
            ),
            None,
            None,
        ),
        (
            # the factor is at its most, so only the product can be raised
            "/api/worksheets/multiplication_models.pdf?max_product=6&problems=3",
            422,
            refused(
                "problems: at most 1 without repeats for that largest factor and largest "
                "product. Lower problems to 1, or raise the largest product to 9."
            ),
            None,
            None,
        ),
        (
            # only 2 x 3: raising either limit alone allows 2 at most
            "/api/worksheets/multiplication_models.pdf?max_factor=3&max_product=6&problems=3",
            422,
            refused(
                "problems: at most 1 without repeats for that largest factor and largest "
                "product. Lower problems to 1."
            ),
            None,
            None,
        ),
        (
            # so there's always a fact other than 2 x 2
            "/api/worksheets/multiplication_models.pdf?max_factor=2",
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_factor"],
                        "msg": "Input should be greater than or equal to 3",
                        "ctx": {"ge": 3},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/multiplication_models.pdf?max_factor=13",
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_factor"],
                        "msg": "Input should be less than or equal to 12",
                        "ctx": {"le": 12},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/multiplication_models.pdf?max_product=5",
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_product"],
                        "msg": "Input should be greater than or equal to 6",
                        "ctx": {"ge": 6},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # within 12 x 12
            "/api/worksheets/multiplication_models.pdf?max_product=145",
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_product"],
                        "msg": "Input should be less than or equal to 144",
                        "ctx": {"le": 144},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_multiplication_models_pdf(
    url: str,
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
    choose_last(monkeypatch)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

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
            render_multiplication_models(
                questions=pdf_data["questions"],
                jump_labels=pdf_data["jump_labels"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
