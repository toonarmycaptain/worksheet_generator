"""
Tests for the strip choice worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording, and each
has the strip diagrams of ``strip_choices``, or for two steps ``two_step_strip_choices``.
``reverse_shuffle`` fixes their order by reversing them, so the correct strip is always D.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/strip_choice_worksheet_pdf_expecteds.txt``. The text includes the instruction, every
problem's wording or equation, its lettered strips, the answer key and the page breaks. To
regenerate sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    Unknown,
)
from core.basic_operations.representation import Prompt
from tests.helpers import GOLDENS, pdf_text, read_sections, render_strip_choice, reverse_shuffle

TITLE = "Strip Diagram multiple choice"

# one of each operation, each with a smaller number of at most 12, as on a sheet
FOUR_OPERATIONS = [
    BasicOperationQuestionData(
        Operation.ADD,
        (47, 9),
        56,
        "Maria collected 47 stickers. Jamal collected 9 stickers. "
        "How many stickers did they collect altogether?",
    ),
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (52, 8),
        44,
        "Priya had 52 marbles and used 8. How many marbles are left?",
    ),
    BasicOperationQuestionData(
        Operation.MULTIPLY,
        (3, 4),
        12,
        "There are 3 boxes. Each box holds 4 crayons. How many crayons altogether?",
    ),
    BasicOperationQuestionData(
        Operation.DIVIDE,
        (12, 3),
        4,
        "Leo puts 12 apples into 3 baskets with the same number in each. "
        "How many apples per basket?",
    ),
]

# 100 less 12: its choices have 12 groups of 100, whose number shrinks to fit, and 100 shared
# into 12, which is impossible and drawn anyway. 99 + 1: its parts split at 0.68 and 0.32, and its
# choices have 1 group.
AT_THEIR_LIMITS = [
    BasicOperationQuestionData(
        Operation.SUBTRACT,
        (100, 12),
        88,
        "Maria needs 100 cards in all and has 12 so far. How many more cards are needed?",
    ),
    BasicOperationQuestionData(
        Operation.ADD,
        (99, 1),
        100,
        "There were 99 beads in the bin. Leo put in 1 more. How many beads are in the bin now?",
    ),
]

# one two-step problem of each shape, so five, and the fifth starts a second page
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

# 100 less 4 shared into 12, and 12 groups of 8 with 4 more: their choices of one equal part too
# many have 14 parts, each an equal share of the strip. 1 + 2 + 97: its narrow parts are widened
# to fit their numbers.
TWO_STEPS_AT_THEIR_LIMITS = [
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (100, 4), 96),
            BasicOperationQuestionData(Operation.DIVIDE, (96, 12), 8),
        ),
        Unknown.FIRST,
        8,
        "Maria has 100 beads. 4 are in a box, and the rest are in 12 bags with the same number "
        "in each bag. How many beads are in each bag?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (12, 8), 96),
            BasicOperationQuestionData(Operation.ADD, (96, 4), 100),
        ),
        Unknown.FIRST,
        100,
        "There are 12 boxes with 8 cards in each box. Leo brings 4 more. "
        "How many cards are there now?",
    ),
    TwoStepQuestionData(
        (
            BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
            BasicOperationQuestionData(Operation.ADD, (3, 97), 100),
        ),
        Unknown.FIRST,
        100,
        "A jar held 1 bead. Sam added 2 more, and then Ivy added 97 more. "
        "How many beads are in the jar now?",
    ),
]

EXPECTED = GOLDENS / "strip_choice_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "prompt", "answer_key", "title", "label"),
    [
        # The instruction under the header, then each problem's wording and its strips, two to a
        # row, lettered A to D.
        ("word_problem", FOUR_OPERATIONS, Prompt.WORD_PROBLEM, False, TITLE, "Sheet A"),
        # each problem's equation instead, followed by "= ?"
        ("equation", FOUR_OPERATIONS, Prompt.EQUATION, False, TITLE, "Sheet A"),
        # the wording, then the equation; the key gives each equation, answer and letter
        ("both_answer_key", FOUR_OPERATIONS, Prompt.BOTH, True, TITLE, "Sheet A"),
        ("at_their_limits", AT_THEIR_LIMITS, Prompt.WORD_PROBLEM, False, TITLE, "Sheet A"),
        # the title and label are the ones given
        ("title_and_label", FOUR_OPERATIONS, Prompt.WORD_PROBLEM, True, "Strip Practice", "Week 3"),
        # Two steps: each choice is one bar, with its whole in a box over its parts. The
        # equation has the first step in brackets, and the key has each step and the letter.
        ("two_steps_both_answer_key", TWO_STEPS, Prompt.BOTH, True, TITLE, "Sheet A"),
        ("two_steps_word_problem", TWO_STEPS, Prompt.WORD_PROBLEM, False, TITLE, "Sheet A"),
        (
            "two_steps_at_their_limits",
            TWO_STEPS_AT_THEIR_LIMITS,
            Prompt.WORD_PROBLEM,
            False,
            TITLE,
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BasicOperationQuestionData | TwoStepQuestionData],
    prompt: Prompt,
    answer_key: bool,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of ``strip_choice_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the wording and equations, the strips and their
    letters, the answer key, the page breaks, and the title and label.
    """
    reverse_shuffle(monkeypatch)
    actual = pdf_text(render_strip_choice(questions, prompt, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
