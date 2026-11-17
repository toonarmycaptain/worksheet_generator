"""
Tests for the input-output tables PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_input_output_tables_worksheet``.

The PDF tests use the contexts and names in ``tests.data``, standing in for the banks, and
replace these functions:

- ``random.choice`` returns the picks listed in the case, as ``test_generator`` in
  ``test_core/test_input_output_tables`` describes, and raises ``ValueError`` for a pick that is
  not among its call's items.
- ``random.sample`` returns the samples listed, and raises ``ValueError`` for a sample not drawn
  from its call's population.
- ``random.randrange`` returns the pair left whole, and ``random.randint`` how many inputs are
  left out.
- ``random.shuffle`` reverses the list, so contexts are dealt from the start of their tuple, the
  question types in reverse, and a multiple-choice question's correct option is last.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import Operation
from core.input_output_tables.data import (
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    RuleForm,
)
from tests.data import NAMES, ORANGES, REAL_CASE_SLOTS, SALE, SOCKS, TABLE_CONTEXTS
from tests.helpers import (
    choice_returns,
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    randrange_returns,
    refused,
    render_input_output_tables,
    reverse_shuffle,
    sample_returns,
)

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
SENTENCE, PLAIN, EXPLAINED = RuleForm

TIMES_8 = ((4, 32), (7, 56), (9, 72), (10, 80))
TIMES_8_SWAPPED = ((32, 4), (56, 7), (72, 9), (80, 10))
SALE_PAIRS = ((12, 18), (19, 25), (27, 33), (33, 39))


@pytest.mark.parametrize(
    (
        "url",
        "chosen",
        "sampled",
        "ranged",
        "drawn",
        "status",
        "expected_json",
        "pdf_data",
        "filename",
    ),
    [
        (
            # the defaults, with 2 problems: each operation drawn from all four, and inputs and
            # outputs left out
            "/api/worksheets/input_output_tables.pdf?problems=2&sheet=1ab2c3",
            [MULTIPLY, 8, ADD, 6],
            [[4, 7, 9, 10], [3], [12, 19, 27, 33], [1]],
            [0, 3],
            [1, 1],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputTableQuestionData(
                            SOCKS, None, MULTIPLY, 8, TIMES_8, (3,), (1, 2)
                        ),
                        (),
                    ),
                    (
                        InputOutputTableQuestionData(SALE, None, ADD, 6, SALE_PAIRS, (1,), (0, 2)),
                        (),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # every option for tables to complete: inputs only
            "/api/worksheets/input_output_tables.pdf?operations=divide&blanks=inputs&problems=1"
            "&answer_key=true&name_line=true&title=Practice&label=Week+3&sheet=1ab2c3",
            [DIVIDE, 8],
            [[4, 7, 9, 10]],
            [2],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputTableQuestionData(
                            SOCKS, None, DIVIDE, 8, TIMES_8_SWAPPED, (0, 1, 3), ()
                        ),
                        (),
                    ),
                ],
                "slot_of": None,
                "answer_key": True,
                "title": "Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "input_output_tables-week-3.pdf",
        ),
        (
            # outputs only
            "/api/worksheets/input_output_tables.pdf?operations=add&blanks=outputs&problems=1"
            "&sheet=1ab2c3",
            [ADD, 6],
            [[12, 19, 27, 33]],
            [1],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputTableQuestionData(SALE, None, ADD, 6, SALE_PAIRS, (), (0, 2, 3)),
                        (),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # multiple choice, every question type by default: one problem, so a table to choose,
            # in the swapped look
            "/api/worksheets/input_output_tables.pdf?operations=multiply&multiple_choice=true"
            "&problems=1&sheet=1ab2c3",
            [False, True, MULTIPLY, 8, [(ADD, 8), (SUBTRACT, 8), (DIVIDE, 8)], (ADD, 8)],
            [[4, 7, 9, 10], [30, 41, 57, 60]],
            [],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
                        (
                            TIMES_8_SWAPPED,
                            ((30, 38), (41, 49), (57, 65), (60, 68)),
                            ((38, 30), (49, 41), (65, 57), (68, 60)),
                        ),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # a sentence to complete, reversed: dividing or multiplying by 8 or 10
            "/api/worksheets/input_output_tables.pdf?operations=divide&multiple_choice=true"
            "&question_types=sentence&problems=1&sheet=1ab2c3",
            ["reverse", DIVIDE, 8],
            [[4, 7, 9, 10], [10]],
            [0],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputRuleQuestionData(
                            SOCKS, None, TIMES_8_SWAPPED, (DIVIDE, 8), SENTENCE
                        ),
                        ((MULTIPLY, 8), (DIVIDE, 10), (MULTIPLY, 10)),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # a statement to choose, explained, reversed
            "/api/worksheets/input_output_tables.pdf?operations=add&multiple_choice=true"
            "&question_types=statement&problems=1&sheet=1ab2c3",
            [EXPLAINED, "reverse", ADD, 6],
            [[12, 19, 27, 33], [9]],
            [0],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputRuleQuestionData(SALE, None, SALE_PAIRS, (ADD, 6), EXPLAINED),
                        ((SUBTRACT, 6), (ADD, 9), (SUBTRACT, 9)),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # two question types ticked: one problem each, shuffled
            "/api/worksheets/input_output_tables.pdf?operations=multiply&multiple_choice=true"
            "&question_types=sentence&question_types=statement&problems=2&sheet=1ab2c3",
            [PLAIN, "reverse", MULTIPLY, 8, "numbers", MULTIPLY, 4],
            [[4, 7, 9, 10], [9], [2, 3, 5, 6], [2, 3], [7]],
            [0, 2],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
                        ((DIVIDE, 8), (MULTIPLY, 9), (DIVIDE, 9)),
                    ),
                    (
                        InputOutputRuleQuestionData(
                            ORANGES,
                            None,
                            ((2, 8), (3, 12), (5, 20), (6, 24)),
                            (MULTIPLY, 4),
                            SENTENCE,
                        ),
                        ((MULTIPLY, 2), (MULTIPLY, 3), (MULTIPLY, 7)),
                    ),
                ],
                "slot_of": None,
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            # tiles: one number left out of each, and the second table's 2 is used already
            "/api/worksheets/input_output_tables.pdf?operations=divide&blanks=outputs"
            "&self_check_tiles=true&problems=2&sheet=1ab2c3",
            [DIVIDE, 2, (1, 1), DIVIDE, 3, (2, 1)],
            [[1, 2, 4, 7], [1, 2, 4, 7]],
            [],
            [],
            200,
            None,
            {
                "questions": [
                    (
                        InputOutputTableQuestionData(
                            SOCKS, None, DIVIDE, 2, ((2, 1), (4, 2), (8, 4), (14, 7)), (), (1,)
                        ),
                        (),
                    ),
                    (
                        InputOutputTableQuestionData(
                            ORANGES, None, DIVIDE, 3, ((3, 1), (6, 2), (12, 4), (21, 7)), (), (2,)
                        ),
                        (),
                    ),
                ],
                "slot_of": REAL_CASE_SLOTS[:2],
                "answer_key": False,
                "title": "Input-Output Tables",
                "label": "Sheet A",
                "name_line": False,
            },
            "input_output_tables-sheet-a.pdf",
        ),
        (
            "/api/worksheets/input_output_tables.pdf?self_check_tiles=true&multiple_choice=true",
            [],
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            "/api/worksheets/input_output_tables.pdf?self_check_tiles=true&problems=13",
            [],
            [],
            [],
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            # division's outputs are 1 to 10
            "/api/worksheets/input_output_tables.pdf?operations=divide&blanks=outputs"
            "&self_check_tiles=true&problems=11",
            [],
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 10 without repeated answers for that choice of operations and "
                "missing table values. Lower problems to 10."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/input_output_tables.pdf?blanks=all",
            [],
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "blanks"],
                        "msg": "Input should be 'inputs', 'outputs' or 'inputs_and_outputs'",
                        "ctx": {"expected": "'inputs', 'outputs' or 'inputs_and_outputs'"},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/input_output_tables.pdf?question_types=all",
            [],
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        # the list's first entry
                        "loc": ["query", "options", "question_types", 0],
                        "msg": "Input should be 'table', 'sentence' or 'statement'",
                        "ctx": {"expected": "'table', 'sentence' or 'statement'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_input_output_tables_pdf(
    url: str,
    chosen: list[Any],
    sampled: list[list[int]],
    ranged: list[int],
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
    monkeypatch.setattr("core.input_output_tables.generator.CONTEXTS", TABLE_CONTEXTS)
    monkeypatch.setattr("core.input_output_tables.generator.NAMES", NAMES)
    choice_returns(monkeypatch, chosen)
    sample_returns(monkeypatch, sampled)
    randrange_returns(monkeypatch, ranged)
    randint_returns(monkeypatch, drawn)
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
            render_input_output_tables(
                questions=pdf_data["questions"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
