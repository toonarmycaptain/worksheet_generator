"""
Tests for the base-ten blocks worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand and have no wrong answers.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/base_ten_blocks_worksheet_pdf_expecteds.txt``. The text includes the key to the
blocks, every question's prompt and blocks, the answer boxes, rules and labels or the answer bank
and pattern, the answer key and the page breaks. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` selects cases).
"""

import pytest

from core.base_ten_blocks import BlocksQuestionData
from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.placevalue.data import PlaceValueQuestionData
from tests.data import BLOCKS, REAL_CASE_SLOTS, STANDARD
from tests.helpers import GOLDENS, pdf_text, read_sections, render_base_ten_blocks

TITLE = "Base-Ten Blocks"

# one of each type
WRITE_ADD_SUBTRACT: list[BlocksQuestionData] = [
    PlaceValueQuestionData(347, BLOCKS, STANDARD),
    BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
    BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
]

# The most blocks a number has, 5 flats in one row, 9 rods and 9 units, and the fewest, 1 unit,
# which is shorter than its answer box, so the two are centred on each other.
AT_THEIR_LIMITS: list[BlocksQuestionData] = [
    PlaceValueQuestionData(599, BLOCKS, STANDARD),
    PlaceValueQuestionData(1, BLOCKS, STANDARD),
    BasicOperationQuestionData(Operation.ADD, (1, 1), 2),
    BasicOperationQuestionData(Operation.SUBTRACT, (599, 1), 598),
]

# Three subtractions of two lines each fill the first page, under the key, so the fourth starts
# a second.
FOUR_SUBTRACTIONS: list[BlocksQuestionData] = [
    BasicOperationQuestionData(Operation.SUBTRACT, (599, 101), 498),
    BasicOperationQuestionData(Operation.SUBTRACT, (588, 102), 486),
    BasicOperationQuestionData(Operation.SUBTRACT, (577, 103), 474),
    BasicOperationQuestionData(Operation.SUBTRACT, (566, 104), 462),
]

EXPECTED = GOLDENS / "base_ten_blocks_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "black_and_white", "answer_key", "title", "label"),
    [
        # The key under the header. A number to write has "=" and a box beside its blocks. A
        # sum has "+" beside its second number, and a difference no sign; each has a rule under
        # its blocks, then "Sum =" or its equation, and a box.
        ("write_add_subtract", WRITE_ADD_SUBTRACT, None, False, False, TITLE, "Sheet A"),
        # the key has each number to write, and each equation and answer
        ("answer_key", WRITE_ADD_SUBTRACT, None, False, True, TITLE, "Sheet A"),
        # grey blocks, in the key too
        ("black_and_white", WRITE_ADD_SUBTRACT, None, True, False, TITLE, "Sheet A"),
        # No boxes, rules or labels, so a difference notes beside its blocks how many to cross
        # out. The bank and pattern are on a page of their own, and the key has letters.
        (
            "self_check_tiles_answer_key",
            WRITE_ADD_SUBTRACT,
            REAL_CASE_SLOTS[:3],
            False,
            True,
            TITLE,
            "Sheet A",
        ),
        ("at_their_limits", AT_THEIR_LIMITS, None, False, False, TITLE, "Sheet A"),
        ("four_subtractions", FOUR_SUBTRACTIONS, None, False, False, TITLE, "Sheet A"),
        # the title and label are the ones given
        ("title_and_label", WRITE_ADD_SUBTRACT, None, False, True, "Blocks Practice", "Week 3"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BlocksQuestionData],
    slot_of: tuple[int, ...] | None,
    black_and_white: bool,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of ``base_ten_blocks_worksheet_pdf_expecteds.txt``.

    One comparison covers the key and its colours, the prompts, the blocks and their signs or
    notes, the answer boxes, rules and labels or the answer bank and pattern, the answer key, the
    page breaks, and the title and label.
    """
    actual = pdf_text(
        render_base_ten_blocks(questions, slot_of, black_and_white, answer_key, title, label)
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
