"""
Tests for the word problems worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording, and have no
wrong answers, except on equation multiple choice sheets, whose choices are those of
``equation_choices``. ``reverse_shuffle`` fixes their order by reversing them.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/word_problems_worksheet_pdf_expecteds.txt``. The text includes the instruction, the
key to base-ten blocks, every problem's wording and hint, its representation or work box, its
lettered equations, the answer lines or the answer bank and pattern, the answer key and the page
breaks. To regenerate sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    Unknown,
)
from core.basic_operations.representation import Representation
from tests.data import REAL_CASE_SLOTS
from tests.helpers import GOLDENS, pdf_text, read_sections, render_word_problems, reverse_shuffle

TITLE = "Word Problems — Strip Diagrams"
TEXT_ONLY_TITLE = "Word Problems"
NUMBER_LINE_TITLE = "Word Problems — Number Lines"
BLOCKS_TITLE = "Word Problems — Base-Ten Blocks"
EQUATION_CHOICE_TITLE = "Word Problems — Equation multiple choice"

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

# Six problems of two lines each, with their equations, fill the first page, so the seventh starts
# a second.
SEVEN_PROBLEMS = [
    BasicOperationQuestionData(
        Operation.ADD,
        (first, 25),
        first + 25,
        f"Maria collected {first} stickers. Jamal collected 25 stickers. "
        "How many stickers did they collect altogether?",
    )
    for first in (11, 22, 33, 44, 55, 66, 77)
]

# one two-step problem of each shape
TWO_STEPS = [
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.ADD, (14, 26), 40),
            BasicOperationQuestionData(Operation.ADD, (40, 9), 49),
        ),
        Unknown.FIRST,
        49,
        "A jar held 14 marbles. Maria added 26 more, and then Jamal added 9 more. "
        "How many marbles are in the jar now?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (64, 15), 49),
            BasicOperationQuestionData(Operation.SUBTRACT, (49, 23), 26),
        ),
        Unknown.FIRST,
        26,
        "A box held 64 crayons. Priya took out 15, and then Leo took out 23. "
        "How many crayons are left in the box?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (38, 8), 30),
            BasicOperationQuestionData(Operation.DIVIDE, (30, 5), 6),
        ),
        Unknown.FIRST,
        6,
        "Sofia has 38 stickers. 8 are in a box, and the rest are in 5 bags with the same number "
        "in each bag. How many stickers are in each bag?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (4, 6), 24),
            BasicOperationQuestionData(Operation.ADD, (24, 7), 31),
        ),
        Unknown.FIRST,
        31,
        "There are 4 boxes with 6 apples in each box. Kai brings 7 more. "
        "How many apples are there now?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (6, 12), 72),
            BasicOperationQuestionData(Operation.SUBTRACT, (90, 72), 18),
        ),
        Unknown.SECOND,
        18,
        "A store had 90 pencils. It sold 6 packs with 12 pencils in each pack. "
        "How many pencils does the store have left?",
    ),
]

# The largest number, 999, less 879 shared into the most groups, 6: each unknown part is 20, so
# narrow, and widened to the least width. 1 + 2 + 996: its narrow parts are widened too.
TWO_STEPS_AT_THEIR_LIMITS = [
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (999, 879), 120),
            BasicOperationQuestionData(Operation.DIVIDE, (120, 6), 20),
        ),
        Unknown.FIRST,
        20,
        "Maria has 999 beads. 879 are in a box, and the rest are in 6 bags with the same number "
        "in each bag. How many beads are in each bag?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
            BasicOperationQuestionData(Operation.ADD, (3, 996), 999),
        ),
        Unknown.FIRST,
        999,
        "A jar held 1 bead. Sam added 2 more, and then Ivy added 996 more. "
        "How many beads are in the jar now?",
    ),
]


EXPECTED = GOLDENS / "word_problems_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    (
        "case_name",
        "questions",
        "representation",
        "hints",
        "black_and_white",
        "work_box",
        "slot_of",
        "answer_key",
        "title",
        "label",
    ),
    [
        (
            "add_and_subtract",
            ADD_AND_SUBTRACT,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "add_and_subtract_no_hints_answer_key",
            ADD_AND_SUBTRACT,
            Representation.STRIP,
            False,
            False,
            True,
            None,
            True,
            TITLE,
            "Sheet A",
        ),
        (
            "splits_at_their_limits",
            SPLITS_AT_THEIR_LIMITS,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "five_problems",
            FIVE_PROBLEMS,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "multiply_and_divide",
            MULTIPLY_AND_DIVIDE,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        (
            "groups_at_their_limits",
            GROUPS_AT_THEIR_LIMITS,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        # the key has each operation's equation
        (
            "all_four_answer_key",
            ALL_FOUR,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            True,
            TITLE,
            "Sheet A",
        ),
        # no answer lines, and the bank and pattern on a page of their own; the key has letters
        (
            "self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Representation.STRIP,
            True,
            False,
            True,
            REAL_CASE_SLOTS[:2],
            True,
            TITLE,
            "Sheet A",
        ),
        (
            "other_title_and_label",
            ADD_AND_SUBTRACT,
            Representation.STRIP,
            True,
            False,
            True,
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
            Representation.NONE,
            True,
            False,
            True,
            None,
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # four boxed problems of two lines each fill the first page, so the fifth starts a second
        (
            "text_only_five_problems",
            FIVE_PROBLEMS,
            Representation.NONE,
            True,
            False,
            True,
            None,
            False,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # tiles: the boxes stay, and only the answer lines go
        (
            "text_only_self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Representation.NONE,
            True,
            False,
            True,
            REAL_CASE_SLOTS[:2],
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # Without the work boxes, each answer line follows its problem's wording, and the
        # instruction doesn't mention a box.
        (
            "text_only_no_work_boxes_answer_key",
            ALL_FOUR,
            Representation.NONE,
            True,
            False,
            False,
            None,
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # without the boxes, all five problems fit on the first page
        (
            "text_only_no_work_boxes_five_problems",
            FIVE_PROBLEMS,
            Representation.NONE,
            True,
            False,
            False,
            None,
            False,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # tiles without the boxes: only the wording, then the bank and pattern
        (
            "text_only_no_work_boxes_self_check_tiles",
            ADD_AND_SUBTRACT,
            Representation.NONE,
            True,
            False,
            False,
            REAL_CASE_SLOTS[:2],
            False,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
        # Number lines: jumps with a box under each landing, the last captioned "answer", so no
        # answer lines. The key has each equation, without the landings.
        (
            "number_line_add_and_subtract",
            ADD_AND_SUBTRACT,
            Representation.NUMBER_LINE,
            True,
            False,
            True,
            None,
            False,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        (
            "number_line_jumps_no_hints_answer_key",
            JUMPS,
            Representation.NUMBER_LINE,
            False,
            False,
            True,
            None,
            True,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        # four number lines of two lines each fill the first page, so the fifth starts a second
        (
            "number_line_five_problems",
            FIVE_PROBLEMS,
            Representation.NUMBER_LINE,
            True,
            False,
            True,
            None,
            False,
            NUMBER_LINE_TITLE,
            "Sheet A",
        ),
        # tiles: the number lines are drawn as they are, followed by the bank and pattern
        (
            "number_line_self_check_tiles_answer_key",
            ADD_AND_SUBTRACT,
            Representation.NUMBER_LINE,
            True,
            False,
            True,
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
            Representation.BLOCKS,
            True,
            False,
            True,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # without the hints, the note goes too
        (
            "blocks_no_hints_answer_key",
            BLOCKS,
            Representation.BLOCKS,
            False,
            False,
            True,
            None,
            True,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # grey blocks, in the key too
        (
            "blocks_black_and_white",
            BLOCKS,
            Representation.BLOCKS,
            True,
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
            Representation.BLOCKS,
            True,
            False,
            True,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # two additions fill the first page, under the key, and two more each later page
        (
            "blocks_five_problems",
            FIVE_PROBLEMS,
            Representation.BLOCKS,
            True,
            False,
            True,
            None,
            False,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # tiles: no answer lines, then the bank and pattern
        (
            "blocks_self_check_tiles_answer_key",
            BLOCKS,
            Representation.BLOCKS,
            True,
            False,
            True,
            REAL_CASE_SLOTS[:2],
            True,
            BLOCKS_TITLE,
            "Sheet A",
        ),
        # Equation multiple choice: each problem's four equations in rows of two, with no hint
        # even with hints on, and no box or answer line even with boxes on. The instruction's □
        # is a square. The key has each equation and its letter.
        (
            "equation_choice_all_four_answer_key",
            ALL_FOUR,
            Representation.EQUATION_CHOICE,
            True,
            False,
            True,
            None,
            True,
            EQUATION_CHOICE_TITLE,
            "Sheet A",
        ),
        (
            "equation_choice_seven_problems",
            SEVEN_PROBLEMS,
            Representation.EQUATION_CHOICE,
            True,
            False,
            True,
            None,
            False,
            EQUATION_CHOICE_TITLE,
            "Sheet A",
        ),
        # Two steps with strip diagrams: one bar each, with its whole in a box over its parts,
        # and each shape's hint. The key has each step.
        (
            "two_steps_strip_answer_key",
            TWO_STEPS,
            Representation.STRIP,
            True,
            False,
            True,
            None,
            True,
            TITLE,
            "Sheet A",
        ),
        (
            "two_steps_strip_at_their_limits",
            TWO_STEPS_AT_THEIR_LIMITS,
            Representation.STRIP,
            False,
            False,
            True,
            None,
            False,
            TITLE,
            "Sheet A",
        ),
        # text only: a box to show the work in, and the bank and pattern; the key has each step
        # and its letter
        (
            "two_steps_text_only_self_check_tiles_answer_key",
            TWO_STEPS,
            Representation.NONE,
            True,
            False,
            True,
            REAL_CASE_SLOTS[:5],
            True,
            TEXT_ONLY_TITLE,
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BasicOperationQuestionData | TwoStepQuestionData],
    representation: Representation,
    hints: bool,
    black_and_white: bool,
    work_box: bool,
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of ``word_problems_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the wording, the hints, the strips and their splits
    or equal parts, the number lines and their jumps, the base-ten blocks, their key and colours,
    the lettered equations, the answer lines or the answer bank and pattern, the answer key, the
    page breaks, and the title and label.
    """
    reverse_shuffle(monkeypatch)
    actual = pdf_text(
        render_word_problems(
            questions,
            representation,
            hints,
            black_and_white,
            work_box,
            slot_of,
            answer_key,
            title,
            label,
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("representation", "message"),
    [
        (
            Representation.NUMBER_LINE,
            "Only strip diagrams and text only show two-step problems.",
        ),
        (Representation.BLOCKS, "Only strip diagrams and text only show two-step problems."),
        (
            Representation.EQUATION_CHOICE,
            "Only strip diagrams and text only show two-step problems.",
        ),
    ],
)
def test_word_problems_worksheet_errors(representation: Representation, message: str) -> None:
    """A two-step problem with a representation that shows only one step raises ``ValueError``."""
    with pytest.raises(ValueError) as error:
        render_word_problems(
            TWO_STEPS[:1], representation, True, False, True, None, False, TITLE, "Sheet A"
        )
    assert str(error.value) == message
