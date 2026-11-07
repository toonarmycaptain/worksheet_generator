"""
Tests for the word problems worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording, and have no
wrong answers.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/word_problems_worksheet_pdf_expecteds.txt``. The text includes the instruction, the
key to base-ten blocks, every problem's wording and hint, its picture or work box, the answer
lines or the answer bank and pattern, the answer key and the page breaks. To regenerate sections
after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.representation import Picture
from tests.data import REAL_CASE_SLOTS
from tests.helpers import GOLDENS, pdf_text, read_sections, render_word_problems

TITLE = "Word Problems — Strip Diagrams"
TEXT_ONLY_TITLE = "Word Problems"
NUMBER_LINE_TITLE = "Word Problems — Number Lines"
BLOCKS_TITLE = "Word Problems — Base-Ten Blocks"

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

# Number lines of three jumps, two with no tens jump for the 0, and one, so wider steps. The
# subtraction starts at the right and jumps left.
JUMPS = [
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (347, 125),
        222,
        "There were 347 cards on the shelf. 125 of them were sold. How many cards are left?",
    ),
    BasicOperationQuestionData(
        Operation.ADD,
        (35, 804),
        839,
        "Kai had 35 pennies and found 804 more. How many pennies does Kai have now?",
    ),
    BasicOperationQuestionData(
        Operation.ADD,
        (81, 70),
        151,
        "Sofia read 81 pages on Monday and 70 pages on Tuesday. How many pages in all?",
    ),
]

# Base-ten blocks of every kind: a flat, rods, and units in two rows. Addition shows both
# numbers, and subtraction shows the first, with the amount to cross out beside it.
BLOCKS = [
    BasicOperationQuestionData(
        Operation.ADD,
        (147, 25),
        172,
        "Maria collected 147 stickers. Jamal collected 25 stickers. "
        "How many stickers did they collect altogether?",
    ),
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (304, 128),
        176,
        "There were 304 cards on the shelf. 128 of them were sold. How many cards are left?",
    ),
]

# The most blocks a number has, 5 flats in one row, 9 rods and 9 units, and the fewest, 1 unit
BLOCKS_AT_THEIR_LIMITS = [
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (599, 1),
        598,
        "Maria had 599 cards and used 1. How many cards are left?",
    ),
    BasicOperationQuestionData(
        Operation.ADD,
        (1, 1),
        2,
        "Maria had 1 card and found 1 more. How many cards does Maria have now?",
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
    (
        "case_name",
        "questions",
        "picture",
        "hints",
        "black_and_white",
        "slot_of",
        "answer_key",
        "title",
        "label",
    ),
    [
        (
            "add_and_subtract",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            True,
            False,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "add_and_subtract_no_hints_answer_key",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            False,
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
            False,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        ("five_problems", FIVE_PROBLEMS, Picture.STRIP, True, False, None, False, TITLE, "Sheet A"),
        (
            "multiply_and_divide",
            MULTIPLY_AND_DIVIDE,
            Picture.STRIP,
            True,
            False,
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
            False,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        # the key has each operation's equation
        ("all_four_answer_key", ALL_FOUR, Picture.STRIP, True, False, None, True, TITLE, "Sheet A"),
        # no answer lines, and the bank and pattern on a page of their own; the key has letters
        (
            "self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Picture.STRIP,
            True,
            False,
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
            False,
            None,
            False,
            "Story Problems",
            "Day 2",
        ),
        # Text only: a box to show the work in, and no hints even with hints on. The key has
        # each operation's equation.
        (
            "text_only_all_four_answer_key",
            ALL_FOUR,
            Picture.NONE,
            True,
            False,
            None,
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # four boxed problems of two lines each fill the first page, so the fifth starts a second
        (
            "text_only_five_problems",
            FIVE_PROBLEMS,
            Picture.NONE,
            True,
            False,
            None,
            False,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # tiles: the boxes stay, and only the answer lines go
        (
            "text_only_self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Picture.NONE,
            True,
            False,
            REAL_CASE_SLOTS[:2],
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # Number lines: jumps with a box under each landing, the last captioned "answer", so no
        # answer lines. The key has each equation, without the landings.
        (
            "number_line_add_and_subtract",
            ADD_AND_SUBTRACT,
            Picture.NUMBER_LINE,
            True,
            False,
            None,
            False,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        (
            "number_line_jumps_no_hints_answer_key",
            JUMPS,
            Picture.NUMBER_LINE,
            False,
            False,
            None,
            True,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        # four number lines of two lines each fill the first page, so the fifth starts a second
        (
            "number_line_five_problems",
            FIVE_PROBLEMS,
            Picture.NUMBER_LINE,
            True,
            False,
            None,
            False,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        # tiles: the number lines are drawn as they are, followed by the bank and pattern
        (
            "number_line_self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Picture.NUMBER_LINE,
            True,
            False,
            REAL_CASE_SLOTS[:2],
            True,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        # Base-ten blocks: the key under the instruction, "+" beside an addition's second
        # number, and a note beside a subtraction's blocks saying what to cross out
        (
            "blocks_add_and_subtract",
            BLOCKS,
            Picture.BLOCKS,
            True,
            False,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # without the hints, the note goes too
        (
            "blocks_no_hints_answer_key",
            BLOCKS,
            Picture.BLOCKS,
            False,
            False,
            None,
            True,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # grey blocks, in the key too
        (
            "blocks_black_and_white",
            BLOCKS,
            Picture.BLOCKS,
            True,
            True,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        (
            "blocks_at_their_limits",
            BLOCKS_AT_THEIR_LIMITS,
            Picture.BLOCKS,
            True,
            False,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # two additions fill the first page, under the key, and two more each later page
        (
            "blocks_five_problems",
            FIVE_PROBLEMS,
            Picture.BLOCKS,
            True,
            False,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # tiles: no answer lines, then the bank and pattern
        (
            "blocks_self_check_tiles_answer_key",
            BLOCKS,
            Picture.BLOCKS,
            True,
            False,
            REAL_CASE_SLOTS[:2],
            True,
            BLOCKS_TITLE,
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BasicOperationQuestionData],
    picture: Picture,
    hints: bool,
    black_and_white: bool,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of ``word_problems_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the wording, the hints, the strips and their splits
    or equal parts, the number lines and their jumps, the base-ten blocks, their key and colours,
    the answer lines or the answer bank and pattern, the answer key, the page breaks, and the
    title and label.
    """
    actual = pdf_text(
        render_word_problems(
            questions, picture, hints, black_and_white, slot_of, answer_key, title, label
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
