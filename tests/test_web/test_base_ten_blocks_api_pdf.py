"""
Tests for the base-ten blocks endpoint: its options reach the core and the renderer intact.

The tests script ``random``: ``randint`` returns the numbers listed, ``sample`` gives any extra
questions to the last types, and ``shuffle`` reverses. ``conventional_slot_of`` gives the slots
of a real case. The PDF must then match what the renderer draws for the same questions.
Disallowed options get Ninja's JSON error. The renderer's output is tested in
``test_base_ten_blocks_worksheet``.
"""

from enum import StrEnum
from typing import Any, get_args

import pytest
from django.test import Client
from worksheets.registry import (
    BlocksQuestionChoice,
    NumberListStyleChoice,
    PromptChoice,
    RegroupingChoice,
)

from core.base_ten_blocks import BlocksQuestionType
from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.regrouping import Regrouping
from core.basic_operations.representation import Prompt
from core.placevalue.data import PlaceValueQuestionData
from render.pdf.data_displays import NumberListStyle
from tests.data import BLOCKS, REAL_CASE_SLOTS, STANDARD
from tests.helpers import (
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    refused,
    render_base_ten_blocks,
    reverse_shuffle,
    sample_last,
)


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults, with 3 problems: one of each type, numbers from 100 up
            "/api/worksheets/base_ten_blocks.pdf?problems=3&sheet=1ab2c3",
            [347, 247, 318, 572, 145],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
                    BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                    PlaceValueQuestionData(347, BLOCKS, STANDARD),
                ],
                "slot_of": None,
                "black_and_white": False,
                "answer_key": False,
                "title": "Base-Ten Blocks",
                "label": "Sheet A",
                "name_line": False,
            },
            "base_ten_blocks-sheet-a.pdf",
        ),
        (
            # every option: 23 + 5 doesn't regroup, so it's redrawn, and an operand is at most
            # 49, leaving room for the other in 50
            "/api/worksheets/base_ten_blocks.pdf?questions=add&min_number=1&max_number=50"
            "&regrouping=always&problems=1&black_and_white=true&answer_key=true&name_line=true"
            "&title=Practice&label=Week+3&sheet=1ab2c3",
            [23, 5, 25, 17],
            200,
            None,
            {
                "questions": [BasicOperationQuestionData(Operation.ADD, (25, 17), 42)],
                "slot_of": None,
                "black_and_white": True,
                "answer_key": True,
                "title": "Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "base_ten_blocks-week-3.pdf",
        ),
        (
            # tiles: no boxes, and the bank and pattern on a page of their own
            "/api/worksheets/base_ten_blocks.pdf?self_check_tiles=true&problems=3&sheet=1ab2c3",
            [347, 247, 318, 572, 145],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
                    BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                    PlaceValueQuestionData(347, BLOCKS, STANDARD),
                ],
                "slot_of": REAL_CASE_SLOTS[:3],
                "black_and_white": False,
                "answer_key": False,
                "title": "Base-Ten Blocks",
                "label": "Sheet A",
                "name_line": False,
            },
            "base_ten_blocks-sheet-a.pdf",
        ),
        (
            # shared evenly, each type needs only its share: 1 + 1 is the only sum up to 2, and
            # is enough for 1 of 2 problems
            "/api/worksheets/base_ten_blocks.pdf?questions=write_number&questions=add"
            "&min_number=1&max_number=2&problems=2&sheet=1ab2c3",
            [2, 1, 1],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    PlaceValueQuestionData(2, BLOCKS, STANDARD),
                ],
                "slot_of": None,
                "black_and_white": False,
                "answer_key": False,
                "title": "Base-Ten Blocks",
                "label": "Sheet A",
                "name_line": False,
            },
            "base_ten_blocks-sheet-a.pdf",
        ),
        (
            "/api/worksheets/base_ten_blocks.pdf?min_number=300&max_number=200",
            [],
            422,
            refused("min_number: must not be more than the largest number"),
            None,
            None,
        ),
        (
            "/api/worksheets/base_ten_blocks.pdf?self_check_tiles=true&problems=13",
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # 200 to 210 has 11 numbers to write
            "/api/worksheets/base_ten_blocks.pdf?questions=write_number&min_number=200"
            "&max_number=210&problems=20",
            [],
            422,
            refused(
                "problems: at most 11 without repeats for that range of numbers. Lower problems "
                "to 11, or raise the largest number to 219."
            ),
            None,
            None,
        ),
        (
            # up to 10, only sums of 10 regroup, and all have the same answer
            "/api/worksheets/base_ten_blocks.pdf?questions=add&min_number=1&max_number=10"
            "&regrouping=always&self_check_tiles=true&problems=2",
            [],
            422,
            refused(
                "problems: at most 1 without repeated answers for that range of numbers and "
                "regrouping. Lower problems to 1, or raise the largest number to 11."
            ),
            None,
            None,
        ),
        (
            # 500 + 500 is past 999, so fewer problems can't help
            "/api/worksheets/base_ten_blocks.pdf?questions=add&min_number=500",
            [],
            422,
            refused(
                "min_number: no add questions fit numbers from 500 to 999. Lower the smallest "
                "number, or untick add."
            ),
            None,
            None,
        ),
        (
            # nothing under 10 carries, and the smallest number can't go lower than 1
            "/api/worksheets/base_ten_blocks.pdf?questions=add&min_number=1&max_number=9"
            "&regrouping=always",
            [],
            422,
            refused(
                "min_number: no add questions that regroup fit numbers from 1 to 9. Raise the "
                "largest number to 10, or change the regrouping, or untick add."
            ),
            None,
            None,
        ),
        (
            # From 150, every sum and difference up to 320 regroups. At 351 there are 6 of each,
            # 3 each for the default 6 problems.
            "/api/worksheets/base_ten_blocks.pdf?questions=add&questions=subtract&min_number=150"
            "&max_number=320&regrouping=never",
            [],
            422,
            refused(
                "min_number: no add or subtract questions without regrouping fit numbers from "
                "150 to 320. Lower the smallest number, or raise the largest number to 351, or "
                "change the regrouping, or untick add and subtract."
            ),
            None,
            None,
        ),
        (
            # blocks are drawn for numbers up to 599
            "/api/worksheets/base_ten_blocks.pdf?min_number=600",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "min_number"],
                        "msg": "Input should be less than or equal to 599",
                        "ctx": {"le": 599},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/base_ten_blocks.pdf?max_number=1000",
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
            "/api/worksheets/base_ten_blocks.pdf?regrouping=sometimes",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "regrouping"],
                        "msg": "Input should be 'never', 'mixed' or 'always'",
                        "ctx": {"expected": "'never', 'mixed' or 'always'"},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/base_ten_blocks.pdf?questions=multiply",
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "questions", 0],
                        "msg": "Input should be 'write_number', 'add' or 'subtract'",
                        "ctx": {"expected": "'write_number', 'add' or 'subtract'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_base_ten_blocks_pdf(
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
    sample_last(monkeypatch)
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
            render_base_ten_blocks(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                black_and_white=pdf_data["black_and_white"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )


@pytest.mark.parametrize(
    ("choice", "enum"),
    [
        (BlocksQuestionChoice, BlocksQuestionType),
        (RegroupingChoice, Regrouping),
        (NumberListStyleChoice, NumberListStyle),
        (PromptChoice, Prompt),
    ],
)
def test_the_choices_are_every_value_in_order(choice: Any, enum: type[StrEnum]) -> None:
    """
    Each choice lists its enum's values in order, which is the order the page shows them in.

    They are written out by hand, so a value added to the enum must be added to them too.
    """
    assert get_args(choice) == tuple(member.value for member in enum)
