"""
Tests for the word problems worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording, and have no
wrong answers.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/word_problems_worksheet_pdf_expecteds.txt``. The text includes the instruction, every
problem's wording and hint, its picture, the answer lines or the answer bank and pattern, the
answer key and the page breaks. To regenerate sections after an intended change, uncomment the
``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.representation import Picture
from tests.data import REAL_CASE_SLOTS
from tests.helpers import GOLDENS, pdf_text, read_sections, render_word_problems

TITLE = "Word Problems — Strip Diagrams"

ADD_AND_SUBTRACT = [
    BasicOperationQuestionData(
        Operation.ADD,
        (47, 25),
        72,
        "Maria collected 47 stickers. Jamal collected 25 stickers. "
        "How many stickers did they collect altogether?",
    ),
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (72, 25),
        47,
        "Priya had 72 marbles and used 25. How many marbles are left?",
    ),
]

# A part's share of the strip is kept from 0.32 to 0.68: 12 of 912 is drawn at 0.32, and 74 of
# 89 at 0.68.
SPLITS_AT_THEIR_LIMITS = [
    BasicOperationQuestionData(
        Operation.ADD,
        (12, 900),
        912,
        "There were 12 books in the bin. Leo put in 900 more. How many books are in the bin now?",
    ),
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (89, 74),
        15,
        "Sam had 89 apples and used 74. How many apples are left?",
    ),
]

# Equal-groups strips: 3 parts of 4 with the whole to find, and 12 in 3 parts of unknown size
MULTIPLY_AND_DIVIDE = [
    BasicOperationQuestionData(
        Operation.MULTIPLY,
        (3, 4),
        12,
        "Maria has 3 bags with 4 stickers in each bag. How many stickers are there in all?",
    ),
    BasicOperationQuestionData(
        Operation.DIVIDE,
        (12, 3),
        4,
        "Jamal shares 12 marbles equally among 3 friends. How many marbles does each friend get?",
    ),
]

# The most and fewest parts of an equal-groups strip: 6 groups of the largest size, 20, and 2
# groups of the smallest, 2.
GROUPS_AT_THEIR_LIMITS = [
    BasicOperationQuestionData(
        Operation.MULTIPLY,
        (6, 20),
        120,
        "There are 6 boxes. Each box holds 20 crayons. How many crayons altogether?",
    ),
    BasicOperationQuestionData(
        Operation.DIVIDE,
        (4, 2),
        2,
        "4 beads are put into 2 equal groups. How many beads are in each group?",
    ),
]

# Both kinds of strip on one sheet, with the instruction for both
ALL_FOUR = ADD_AND_SUBTRACT + MULTIPLY_AND_DIVIDE

# Four problems of two lines each fill the first page, so the fifth starts a second.
FIVE_PROBLEMS = [
    BasicOperationQuestionData(
        Operation.ADD,
        (first, 25),
        first + 25,
        f"Maria collected {first} stickers. Jamal collected 25 stickers. "
        "How many stickers did they collect altogether?",
    )
    for first in (11, 22, 33, 44, 55)
]


EXPECTED = GOLDENS / "word_problems_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "picture", "hints", "slot_of", "answer_key", "title", "label"),
    [
        ("add_and_subtract", ADD_AND_SUBTRACT, Picture.STRIP, True, None, False, TITLE, "Sheet A"),
        (
            "add_and_subtract_no_hints_answer_key",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            False,
            None,
            True,
            TITLE,
            "Sheet A",
        ),
        (
            "splits_at_their_limits",
            SPLITS_AT_THEIR_LIMITS,
            Picture.STRIP,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        ("five_problems", FIVE_PROBLEMS, Picture.STRIP, True, None, False, TITLE, "Sheet A"),
        (
            "multiply_and_divide",
            MULTIPLY_AND_DIVIDE,
            Picture.STRIP,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "groups_at_their_limits",
            GROUPS_AT_THEIR_LIMITS,
            Picture.STRIP,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        # the key has each operation's equation
        ("all_four_answer_key", ALL_FOUR, Picture.STRIP, True, None, True, TITLE, "Sheet A"),
        # no answer lines, and the bank and pattern on a page of their own; the key has letters
        (
            "self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            True,
            REAL_CASE_SLOTS[:2],
            True,
            TITLE,
            "Sheet A",
        ),
        (
            "other_title_and_label",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            True,
            None,
            False,
            "Story Problems",
            "Day 2",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BasicOperationQuestionData],
    picture: Picture,
    hints: bool,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of ``word_problems_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the wording, the hints, the strips and their splits
    or equal parts, the answer lines or the answer bank and pattern, the answer key, the page
    breaks, and the title and label.
    """
    actual = pdf_text(
        render_word_problems(questions, picture, hints, slot_of, answer_key, title, label)
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
