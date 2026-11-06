"""
Tests for the self-check tiles worksheet PDF, rendered from hand-built questions and slots.

Neither the question generator nor the random slot order is used. Each case's output is stored
as text decoded from the PDF, in one file with a section per case:
``goldens/self_check_tiles_worksheet_pdf_expecteds.txt``. The text includes the questions, the
answer bank in slot order (with unused slots shaded), the letters, the answer key, and the
position and corners of every tile in the pattern, so a changed title, a moved line or a wrong
tile appears as a changed line in ``git diff``. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` selects cases).

The text cannot show whether the pattern is correct for a physical case. That is verified on
paper, by filling a case from the answer key, flipping it and comparing it with the picture.
"""

from collections.abc import Callable

import pytest

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
from core.placevalue.data import PlaceValueQuestionData
from core.placevalue.representation import place_value_tile_question
from core.question import QuestionData
from core.self_check_tiles import TileQuestion
from tests.data import EXPANDED, EXPANDED_NOTATION, REAL_CASE_SLOTS, STANDARD, UNIT, WORD
from tests.helpers import GOLDENS, pdf_text, read_sections, render_tiles

# twelve questions with twelve different answers: 7 14 16 12 5 9 0 1 42 25 27 24
TWELVE = [
    BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
    BasicOperationQuestionData(Operation.ADD, (5, 9), 14),
    BasicOperationQuestionData(Operation.ADD, (8, 8), 16),
    BasicOperationQuestionData(Operation.ADD, (2, 10), 12),
    BasicOperationQuestionData(Operation.SUBTRACT, (9, 4), 5),
    BasicOperationQuestionData(Operation.SUBTRACT, (10, 1), 9),
    BasicOperationQuestionData(Operation.SUBTRACT, (8, 8), 0),
    BasicOperationQuestionData(Operation.SUBTRACT, (7, 6), 1),
    BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42),
    BasicOperationQuestionData(Operation.MULTIPLY, (5, 5), 25),
    BasicOperationQuestionData(Operation.MULTIPLY, (9, 3), 27),
    BasicOperationQuestionData(Operation.MULTIPLY, (4, 6), 24),
]

# twelve numbers to write in standard form, from every other form. Some don't fit one line of
# their column at full size: word form, unit form and expanded notation, up to the longest
# number the forms write.
PLACE_VALUE_TWELVE = [
    PlaceValueQuestionData(35043, EXPANDED, STANDARD),
    PlaceValueQuestionData(54321, WORD, STANDARD),
    PlaceValueQuestionData(50421, UNIT, STANDARD),
    PlaceValueQuestionData(99999, EXPANDED_NOTATION, STANDARD),
    PlaceValueQuestionData(40014, WORD, STANDARD),
    PlaceValueQuestionData(12000, EXPANDED, STANDARD),
    PlaceValueQuestionData(1005, UNIT, STANDARD),
    PlaceValueQuestionData(70707, EXPANDED_NOTATION, STANDARD),
    PlaceValueQuestionData(23456, WORD, STANDARD),
    PlaceValueQuestionData(999_999, EXPANDED_NOTATION, STANDARD),
    PlaceValueQuestionData(8008, WORD, STANDARD),
    PlaceValueQuestionData(60000, UNIT, STANDARD),
]


# twelve numbers to write in every form, so the bank shows answers that need more than one
# line, some of them more lines than fit unless the boxes grow taller.
PLACE_VALUE_EVERY_ANSWER_FORM = [
    PlaceValueQuestionData(35043, STANDARD, EXPANDED),
    PlaceValueQuestionData(54321, STANDARD, WORD),
    PlaceValueQuestionData(50421, STANDARD, UNIT),
    PlaceValueQuestionData(99999, STANDARD, EXPANDED_NOTATION),
    PlaceValueQuestionData(40014, EXPANDED, WORD),
    PlaceValueQuestionData(12000, WORD, EXPANDED),
    PlaceValueQuestionData(1005, WORD, UNIT),
    PlaceValueQuestionData(70707, UNIT, EXPANDED_NOTATION),
    PlaceValueQuestionData(23456, EXPANDED_NOTATION, WORD),
    PlaceValueQuestionData(8008, EXPANDED, STANDARD),
    PlaceValueQuestionData(60000, UNIT, EXPANDED),
    PlaceValueQuestionData(11111, STANDARD, UNIT),
]

# four equations, each number missing twice, with numbers up to 3 digits
MISSING_NUMBERS = [
    MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4),
    MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 9, 111, 999),
    MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 999, 3, 333),
]

# each answer in the slot of its own number
IN_ORDER = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
# four questions: tiles 1 to 4 in F, A, L and G, and the other eight slots blocked out
FOUR = (5, 0, 11, 6)

EXPECTED = GOLDENS / "self_check_tiles_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "to_tile", "slot_of", "answer_key", "title", "label"),
    [
        (
            "in_order",
            TWELVE,
            basic_operation_tile_question,
            IN_ORDER,
            False,
            "Basic Operations",
            "Sheet A",
        ),
        (
            "real_case",
            TWELVE,
            basic_operation_tile_question,
            REAL_CASE_SLOTS,
            False,
            "Basic Operations",
            "Sheet A",
        ),
        (
            "real_case_answer_key",
            TWELVE,
            basic_operation_tile_question,
            REAL_CASE_SLOTS,
            True,
            "Basic Operations",
            "Sheet A",
        ),
        (
            "in_order_other_title_and_label",
            TWELVE,
            basic_operation_tile_question,
            IN_ORDER,
            False,
            "Number Facts",
            "Day 2",
        ),
        (
            "four_questions",
            TWELVE,
            basic_operation_tile_question,
            FOUR,
            False,
            "Basic Operations",
            "Sheet A",
        ),
        (
            "four_questions_answer_key",
            TWELVE,
            basic_operation_tile_question,
            FOUR,
            True,
            "Basic Operations",
            "Sheet A",
        ),
        # Place-value questions are drawn in their given form, with answers in their asked form.
        # A question too long for its column is drawn smaller on two lines. Every bank answer is
        # drawn at the largest size at which all of them fit, and when even the smallest size is
        # not enough, the boxes grow taller and the pattern moves down.
        (
            "place_value_real_case_answer_key",
            PLACE_VALUE_TWELVE,
            place_value_tile_question,
            REAL_CASE_SLOTS,
            True,
            "Place Value",
            "Sheet A",
        ),
        (
            "place_value_four_questions",
            PLACE_VALUE_TWELVE,
            place_value_tile_question,
            FOUR,
            False,
            "Place Value",
            "Sheet A",
        ),
        (
            "place_value_every_answer_form_answer_key",
            PLACE_VALUE_EVERY_ANSWER_FORM,
            place_value_tile_question,
            REAL_CASE_SLOTS,
            True,
            "Place Value",
            "Sheet A",
        ),
        # Missing-number questions show an empty square for the missing number. The bank shows
        # the missing numbers, and the key shows each completed equation.
        (
            "missing_numbers_four_questions_answer_key",
            MISSING_NUMBERS,
            missing_number_tile_question,
            FOUR,
            True,
            "Division",
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[QuestionData],
    to_tile: Callable[[QuestionData], TileQuestion],
    slot_of: tuple[int, ...],
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``self_check_tiles_worksheet_pdf_expecteds.txt``.

    ``to_tile`` makes each question's tile question: basic operations, place value or missing
    number. The sheet uses as many of the questions as there are slots in ``slot_of``.
    """
    actual = pdf_text(
        render_tiles(questions[: len(slot_of)], to_tile, slot_of, answer_key, title, label)
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
