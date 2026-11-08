"""
Tests for the strip choice worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording, and each
has the strip diagrams of ``strip_choices``. ``reverse_shuffle`` fixes their order by reversing
them, so the correct strip is always D.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/strip_choice_worksheet_pdf_expecteds.txt``. The text includes the instruction, every
problem's wording or equation, its lettered strips, the answer key and the page breaks. To
regenerate sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
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
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[BasicOperationQuestionData],
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
