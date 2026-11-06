"""
Tests for the basic operations endpoint's self-check tiles option: an answer bank and a pattern.

``test_basic_operations_pdf_for_self_check_tiles`` scripts ``random.randint`` (operands, or a
divisor then a quotient) and makes ``random.shuffle`` reverse its list, so the complex pattern's
slots are in reverse order (question 1's answer in L). ``conventional_slot_of`` is replaced to
return the slots of a real case, so each PDF shows which pattern its slots came from. The PDF must
then match what the self-check tiles renderer draws for the same questions and slots, which is
tested in ``test_self_check_tiles_worksheet``. Disallowed options get Ninja's JSON error. The rest
of the endpoint's behaviour, such as the other limits, is shared with the plain sheet and tested in
``test_basic_operations_api_pdf``; the redirect for a request without a ``sheet`` token is tested in
``test_sheet_redirect``.
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
from core.basic_operations.representation import (
    basic_operation_tile_question,
    missing_number_tile_question,
)
from tests.data import REAL_CASE_SLOTS, REVERSED_SLOTS
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    refused,
    render_tiles,
    reverse_shuffle,
    sample_first,
)


@pytest.mark.parametrize(
    ("url", "drawn", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=12&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (0, 1), 1),
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (2, 2), 4),
                    BasicOperationQuestionData(Operation.ADD, (2, 3), 5),
                    BasicOperationQuestionData(Operation.ADD, (3, 3), 6),
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    BasicOperationQuestionData(Operation.ADD, (4, 4), 8),
                    BasicOperationQuestionData(Operation.ADD, (4, 5), 9),
                    BasicOperationQuestionData(Operation.ADD, (5, 5), 10),
                    BasicOperationQuestionData(Operation.ADD, (5, 6), 11),
                    BasicOperationQuestionData(Operation.ADD, (6, 6), 12),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": REVERSED_SLOTS,
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=12&name_line=true&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (0, 1), 1),
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (2, 2), 4),
                    BasicOperationQuestionData(Operation.ADD, (2, 3), 5),
                    BasicOperationQuestionData(Operation.ADD, (3, 3), 6),
                    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
                    BasicOperationQuestionData(Operation.ADD, (4, 4), 8),
                    BasicOperationQuestionData(Operation.ADD, (4, 5), 9),
                    BasicOperationQuestionData(Operation.ADD, (5, 5), 10),
                    BasicOperationQuestionData(Operation.ADD, (5, 6), 11),
                    BasicOperationQuestionData(Operation.ADD, (6, 6), 12),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": REVERSED_SLOTS,
                "title": "Addition",
                "label": "Sheet A",
                "name_line": True,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # 4 questions use tiles 1 to 4, in the first four of the shuffled slots (L, K, J, I)
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&tile_pattern=complex"
            "&problems=4&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (0, 1), 1),
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (2, 2), 4),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": (11, 10, 9, 8),
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # the larger number goes first, and 0 to 11 are the 12 differences
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=12&operation=subtract"
            "&tile_pattern=complex&max_number=11&answer_key=true&sheet=1ab2c3",
            [0, 0, 1, 0, 0, 2, 3, 0, 0, 4, 5, 0, 0, 6, 7, 0, 0, 8, 9, 0, 0, 10, 11, 0],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.SUBTRACT, (0, 0), 0),
                    BasicOperationQuestionData(Operation.SUBTRACT, (1, 0), 1),
                    BasicOperationQuestionData(Operation.SUBTRACT, (2, 0), 2),
                    BasicOperationQuestionData(Operation.SUBTRACT, (3, 0), 3),
                    BasicOperationQuestionData(Operation.SUBTRACT, (4, 0), 4),
                    BasicOperationQuestionData(Operation.SUBTRACT, (5, 0), 5),
                    BasicOperationQuestionData(Operation.SUBTRACT, (6, 0), 6),
                    BasicOperationQuestionData(Operation.SUBTRACT, (7, 0), 7),
                    BasicOperationQuestionData(Operation.SUBTRACT, (8, 0), 8),
                    BasicOperationQuestionData(Operation.SUBTRACT, (9, 0), 9),
                    BasicOperationQuestionData(Operation.SUBTRACT, (10, 0), 10),
                    BasicOperationQuestionData(Operation.SUBTRACT, (11, 0), 11),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": REVERSED_SLOTS,
                "title": "Subtraction",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": True,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # twelve different products, from 0 to 15
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=12&operation=multiply"
            "&tile_pattern=complex&max_number=5&title=Tables&label=Day+2&sheet=1ab2c3",
            [0, 5, 1, 1, 1, 2, 1, 3, 1, 4, 1, 5, 2, 3, 2, 4, 3, 3, 2, 5, 3, 4, 3, 5],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.MULTIPLY, (0, 5), 0),
                    BasicOperationQuestionData(Operation.MULTIPLY, (1, 1), 1),
                    BasicOperationQuestionData(Operation.MULTIPLY, (1, 2), 2),
                    BasicOperationQuestionData(Operation.MULTIPLY, (1, 3), 3),
                    BasicOperationQuestionData(Operation.MULTIPLY, (1, 4), 4),
                    BasicOperationQuestionData(Operation.MULTIPLY, (1, 5), 5),
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 4), 8),
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 3), 9),
                    BasicOperationQuestionData(Operation.MULTIPLY, (2, 5), 10),
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
                    BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": REVERSED_SLOTS,
                "title": "Tables",
                "label": "Day 2",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-day-2.pdf",
        ),
        # The tile pattern chooses where the slots come from: simple, the default, from
        # conventional_slot_of. The rows above use complex, whose slots come from random_slot_of.
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=4&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (0, 1), 1),
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (2, 2), 4),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": (7, 9, 10, 6),
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&tile_pattern=simple"
            "&problems=4&sheet=1ab2c3",
            [0, 1, 1, 1, 1, 2, 2, 2],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.ADD, (0, 1), 1),
                    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
                    BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                    BasicOperationQuestionData(Operation.ADD, (2, 2), 4),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": (7, 9, 10, 6),
                "title": "Addition",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        # Division: a sheet missing the quotient, the dividend or the divisor. Missing divisors
        # with tiles are generated differently: sample takes the first divisors and choice the
        # largest quotient whose family is free.
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&self_check_tiles=true"
            "&tile_pattern=complex&problems=3&sheet=1ab2c3",
            [4, 7, 3, 5, 2, 6],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(Operation.DIVIDE, (28, 4), 7),
                    BasicOperationQuestionData(Operation.DIVIDE, (15, 3), 5),
                    BasicOperationQuestionData(Operation.DIVIDE, (12, 2), 6),
                ],
                "to_tile": basic_operation_tile_question,
                "slot_of": (11, 10, 9),
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # Every divisor from 1 to 10, which drawing one at a time could deadlock on. From 10
            # down, each divisor takes its largest quotient whose fact family is still free.
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=divisor"
            "&self_check_tiles=true&tile_pattern=complex&problems=10&largest_dividend=10"
            "&largest_divisor=10&sheet=1ab2c3",
            [],
            200,
            None,
            {
                "questions": [
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 5, 5, 1),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 6, 3, 2),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 9, 3, 3),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 8, 2, 4),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 10, 2, 5),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 6, 1, 6),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 7, 1, 7),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 8, 1, 8),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 9, 1, 9),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 10, 1, 10),
                ],
                "to_tile": missing_number_tile_question,
                "slot_of": (11, 10, 9, 8, 7, 6, 5, 4, 3, 2),
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": False,
            },
            "basic_operations-sheet-a.pdf",
        ),
        (
            # mixed: the missing divisor 1 (100 ÷ □ = 100) rules out the answer 1, so □ ÷ 1 = 1
            # is drawn again
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=mixed"
            "&self_check_tiles=true&tile_pattern=complex&problems=2&answer_key=true"
            "&sheet=1ab2c3",
            [1, 1, 4, 7],
            200,
            None,
            {
                "questions": [
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
                    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 100, 100, 1),
                ],
                "to_tile": missing_number_tile_question,
                "slot_of": (11, 10),
                "title": "Division",
                "label": "Sheet A",
                "name_line": False,
                "answer_key": True,
            },
            "basic_operations-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=13",
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        # one more problem than there are different answers: 11 sums from 0 to 5, 11 differences
        # from 0 to 10, and 10 products from 0 to 4
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=12&max_number=5",
            [],
            422,
            refused(
                "problems: at most 11 without repeated answers for that largest number. Lower "
                "problems to 11, or raise the largest number to 6."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=12&operation=subtract"
            "&max_number=10",
            [],
            422,
            refused(
                "problems: at most 11 without repeated answers for that largest number. Lower "
                "problems to 11, or raise the largest number to 11."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?self_check_tiles=true&problems=11&operation=multiply"
            "&max_number=4",
            [],
            422,
            refused(
                "problems: at most 10 without repeated answers for that largest number. Lower "
                "problems to 10, or raise the largest number to 5."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=dividend"
            "&self_check_tiles=true&problems=13",
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        # The default largest divisor, 10, gives 10 different divisors to miss.
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=divisor"
            "&self_check_tiles=true&problems=12",
            [],
            422,
            refused(
                "problems: at most 10 without repeated answers for that largest dividend and "
                "divisor. Lower problems to 10, or raise the largest divisor to 12."
            ),
            None,
            None,
        ),
        # With a largest dividend of 10 as well, raising either limit alone adds no divisor.
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=divisor"
            "&self_check_tiles=true&problems=12&largest_dividend=10&largest_divisor=10",
            [],
            422,
            refused(
                "problems: at most 10 without repeated answers for that largest dividend and "
                "divisor. Lower problems to 10."
            ),
            None,
            None,
        ),
        # the quotients 0 to 10
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&self_check_tiles=true&problems=12"
            "&largest_dividend=10",
            [],
            422,
            refused(
                "problems: at most 11 without repeated answers for that largest dividend and "
                "divisor. Lower problems to 11, or raise the largest dividend to 11."
            ),
            None,
            None,
        ),
        # Mixed: 4 missing divisors can use up 8 of the 10 dividends, too many to leave 4.
        (
            "/api/worksheets/basic_operations.pdf?operation=divide&missing_number=mixed"
            "&self_check_tiles=true&problems=8&largest_dividend=10&largest_divisor=10",
            [],
            422,
            refused(
                "problems: at most 7 without repeated answers for that largest dividend and "
                "divisor. Lower problems to 7, or raise the largest dividend to 12."
            ),
            None,
            None,
        ),
    ],
)
def test_basic_operations_pdf_for_self_check_tiles(
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
    A request receives the tiles PDF for its options, or the error identifying the problem.

    ``randint`` returns the scripted ``drawn`` values, and ``sample`` and ``choice`` take the
    first divisors and the last quotient for missing divisors. ``shuffle`` reverses the
    questions and the complex pattern's slots, and the simple pattern's slots are a real case's.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header (24 hours) and the text the renderer
      draws for ``pdf_data``: the tile questions that ``to_tile`` makes, in the slots
      ``slot_of``, the title and label, and whether there is a Name/Date line and an
      answer key.
    """
    randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    choose_last(monkeypatch)
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
            render_tiles(
                questions=pdf_data["questions"],
                to_tile=pdf_data["to_tile"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
