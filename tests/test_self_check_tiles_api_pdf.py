"""The arithmetic endpoint with the self-check tiles option: an answer bank, a pattern and no
choices.

``test_arithmetic_pdf_for_self_check_tiles`` scripts ``random.randint`` (the operands) and makes
``random.shuffle`` reverse its list, so the slot order is the reverse of the slots (question 1's
answer in L). Its requests ask for the complex pattern, which is the one that shuffles every slot.
The PDF must then draw what the self-check tiles renderer makes for those same
questions and slots, which is tested in ``test_self_check_tiles_worksheet_pdf``.
``test_the_tile_pattern_chooses_where_the_slots_come_from`` checks that simple, the default, takes
its slots from ``conventional_slot_of`` instead. Options the
endpoint does not allow get Ninja's JSON error. Everything else about the endpoint (the redirect
for a request without a ``sheet`` token, the other limits) is shared with the plain sheet and
tested in ``test_arithmetic_api_pdf``.
"""

import random
from io import BytesIO
from typing import Any

import pytest
from django.test import Client

from core.arithmetic import ArithmeticQuestionData, Operation
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
from tests.pdf_text import pdf_text

REVERSED_SLOTS = (11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)


def render(
    questions: list[ArithmeticQuestionData],
    answer_key: bool,
    title: str,
    label: str,
    all_slots: tuple[int, ...] = REVERSED_SLOTS,
) -> bytes:
    out = BytesIO()
    slot_of = all_slots[: len(questions)]
    render_self_check_tiles_worksheet(questions, slot_of, out, title, label, answer_key)
    return out.getvalue()


def refused(message: str) -> dict[str, Any]:
    """Ninja's JSON error for an after-validator that raised ``ValueError(message)``."""
    return {
        "detail": [
            {
                "type": "value_error",
                "loc": ["query", "options"],
                "msg": f"Value error, {message}",
                "ctx": {"error": message},
            },
        ],
    }


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=12&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6],
            200,
            None,
            {
                "questions": [
                    ArithmeticQuestionData(Operation.ADD, (0, 1), 1),
                    ArithmeticQuestionData(Operation.ADD, (1, 1), 2),
                    ArithmeticQuestionData(Operation.ADD, (1, 2), 3),
                    ArithmeticQuestionData(Operation.ADD, (2, 2), 4),
                    ArithmeticQuestionData(Operation.ADD, (2, 3), 5),
                    ArithmeticQuestionData(Operation.ADD, (3, 3), 6),
                    ArithmeticQuestionData(Operation.ADD, (3, 4), 7),
                    ArithmeticQuestionData(Operation.ADD, (4, 4), 8),
                    ArithmeticQuestionData(Operation.ADD, (4, 5), 9),
                    ArithmeticQuestionData(Operation.ADD, (5, 5), 10),
                    ArithmeticQuestionData(Operation.ADD, (5, 6), 11),
                    ArithmeticQuestionData(Operation.ADD, (6, 6), 12),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            # 4 questions use tiles 1 to 4, in the first four of the shuffled slots (L, K, J, I)
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=4&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2],
            200,
            None,
            {
                "questions": [
                    ArithmeticQuestionData(Operation.ADD, (0, 1), 1),
                    ArithmeticQuestionData(Operation.ADD, (1, 1), 2),
                    ArithmeticQuestionData(Operation.ADD, (1, 2), 3),
                    ArithmeticQuestionData(Operation.ADD, (2, 2), 4),
                ],
                "title": "Addition",
                "label": "Sheet A",
                "answer_key": False,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            # the larger number goes first, and 0 to 11 are the 12 differences
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=12&operation=subtract"
            "&tile_pattern=complex&max_number=11&answer_key=true&sheet=1ab2c3",
            [0, 0, 1, 0, 0, 2, 3, 0, 0, 4, 5, 0, 0, 6, 7, 0, 0, 8, 9, 0, 0, 10, 11, 0],
            200,
            None,
            {
                "questions": [
                    ArithmeticQuestionData(Operation.SUBTRACT, (0, 0), 0),
                    ArithmeticQuestionData(Operation.SUBTRACT, (1, 0), 1),
                    ArithmeticQuestionData(Operation.SUBTRACT, (2, 0), 2),
                    ArithmeticQuestionData(Operation.SUBTRACT, (3, 0), 3),
                    ArithmeticQuestionData(Operation.SUBTRACT, (4, 0), 4),
                    ArithmeticQuestionData(Operation.SUBTRACT, (5, 0), 5),
                    ArithmeticQuestionData(Operation.SUBTRACT, (6, 0), 6),
                    ArithmeticQuestionData(Operation.SUBTRACT, (7, 0), 7),
                    ArithmeticQuestionData(Operation.SUBTRACT, (8, 0), 8),
                    ArithmeticQuestionData(Operation.SUBTRACT, (9, 0), 9),
                    ArithmeticQuestionData(Operation.SUBTRACT, (10, 0), 10),
                    ArithmeticQuestionData(Operation.SUBTRACT, (11, 0), 11),
                ],
                "title": "Subtraction",
                "label": "Sheet A",
                "answer_key": True,
            },
            "arithmetic-sheet-a.pdf",
        ),
        (
            # twelve different products, from 0 to 15
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=12&operation=multiply"
            "&tile_pattern=complex&max_number=5&title=Tables&label=Day+2&sheet=1ab2c3",
            [0, 5, 1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 2, 3, 2, 4, 3, 3, 2, 5, 3, 4, 3, 5],
            200,
            None,
            {
                "questions": [
                    ArithmeticQuestionData(Operation.MULTIPLY, (0, 5), 0),
                    ArithmeticQuestionData(Operation.MULTIPLY, (1, 1), 1),
                    ArithmeticQuestionData(Operation.MULTIPLY, (1, 2), 2),
                    ArithmeticQuestionData(Operation.MULTIPLY, (1, 3), 3),
                    ArithmeticQuestionData(Operation.MULTIPLY, (1, 4), 4),
                    ArithmeticQuestionData(Operation.MULTIPLY, (1, 5), 5),
                    ArithmeticQuestionData(Operation.MULTIPLY, (2, 3), 6),
                    ArithmeticQuestionData(Operation.MULTIPLY, (2, 4), 8),
                    ArithmeticQuestionData(Operation.MULTIPLY, (3, 3), 9),
                    ArithmeticQuestionData(Operation.MULTIPLY, (2, 5), 10),
                    ArithmeticQuestionData(Operation.MULTIPLY, (3, 4), 12),
                    ArithmeticQuestionData(Operation.MULTIPLY, (3, 5), 15),
                ],
                "title": "Tables",
                "label": "Day 2",
                "answer_key": False,
            },
            "arithmetic-day-2.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=13",
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        # one more problem than there are different answers: 11 sums from 0 to 5, 11 differences
        # from 0 to 10, and 10 products from 0 to 4
        (
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=12&max_number=5",
            [],
            422,
            refused("problems: too many for that largest number, which allows no repeated answers"),
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=12&operation=subtract"
            "&max_number=10",
            [],
            422,
            refused("problems: too many for that largest number, which allows no repeated answers"),
            None,
            None,
        ),
        (
            "/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=11&operation=multiply"
            "&max_number=4",
            [],
            422,
            refused("problems: too many for that largest number, which allows no repeated answers"),
            None,
            None,
        ),
    ],
)
def test_arithmetic_pdf_for_self_check_tiles(
    url: str,
    drawn: list[int],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request gets the self-check tiles PDF for its options, or the error that says what is
    wrong.

    - A refused request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header (24 hours) and the text the renderer
      draws for ``pdf_data``: the questions in the reversed slots, the title and label, and
      whether there is an answer key.
    """
    values = iter(drawn)
    monkeypatch.setattr(random, "randint", lambda low, high: next(values))
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())

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
            render(
                pdf_data["questions"], pdf_data["answer_key"], pdf_data["title"], pdf_data["label"]
            )
        )


# three clean blocks, as on a real case
CONVENTIONAL_SLOTS = (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2)


@pytest.mark.parametrize(
    ("query", "slots"),
    [
        ("", CONVENTIONAL_SLOTS),  # simple is the default
        ("&tile_pattern=simple", CONVENTIONAL_SLOTS),
        ("&tile_pattern=complex", REVERSED_SLOTS),
    ],
)
def test_the_tile_pattern_chooses_where_the_slots_come_from(
    query: str, slots: tuple[int, ...], client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simple takes its slots from ``conventional_slot_of`` and complex from ``random_slot_of``.

    ``conventional_slot_of`` is replaced by a function that returns the clean blocks' slots, and
    the shuffle by one that reverses the slots, so the PDF shows which one was used.
    """
    values = iter([0, 1, 1, 1, 1, 2, 2, 2])
    monkeypatch.setattr(random, "randint", lambda low, high: next(values))
    monkeypatch.setattr(random, "shuffle", lambda items: items.reverse())
    monkeypatch.setattr(
        "worksheets.registry.conventional_slot_of", lambda count: CONVENTIONAL_SLOTS[:count]
    )
    questions = [
        ArithmeticQuestionData(Operation.ADD, (0, 1), 1),
        ArithmeticQuestionData(Operation.ADD, (1, 1), 2),
        ArithmeticQuestionData(Operation.ADD, (1, 2), 3),
        ArithmeticQuestionData(Operation.ADD, (2, 2), 4),
    ]

    response = client.get(
        f"/api/worksheets/arithmetic.pdf?self_check_tiles=true&problems=4&sheet=1ab2c3{query}"
    )

    assert response.status_code == 200
    assert pdf_text(response.content) == pdf_text(
        render(questions, False, "Addition", "Sheet A", slots)
    )
