"""
Tests for the multiplication models worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, with their wording and their
six models, so the choices are fixed and each kind of model appears.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/multiplication_models_worksheet_pdf_expecteds.txt``. The text includes the instruction,
every problem's wording, its lettered models, the answer key and the page breaks. To regenerate
sections after an intended change, uncomment the ``write_section`` lines in
``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.multiplication_models import (
    Array,
    EqualJumpLine,
    MultiplicationModelsQuestion,
    RepeatedAddition,
)
from core.basic_operations.representation import EqualStripDiagram, StripDiagram
from core.question import MultipleChoice, Question
from tests.helpers import GOLDENS, pdf_text, read_sections, render_multiplication_models

TITLE = "Multiplication Models multiple choice"

# Three problems, so the third starts a second page, with every kind of model, wrong ones
# included: two parts as a strip and as an addition, and arrays drawn either way round, or on
# their side when a side is longer than 7
THREE_PROBLEMS: list[MultiplicationModelsQuestion] = [
    Question(
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (4, 11),
            44,
            "There are 4 teams with 11 players on each team. How many players are there in all?",
        ),
        MultipleChoice(
            (
                EqualJumpLine(11, 11),
                RepeatedAddition((4, 11)),
                Array(4, 11),
                RepeatedAddition((11, 11, 11, 11)),
                EqualJumpLine(4, 11),
                EqualStripDiagram(11, 11, None),
            ),
            frozenset({2, 3, 4}),
        ),
    ),
    Question(
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (9, 2),
            18,
            "9 friends each have 2 erasers. How many erasers do they have together?",
        ),
        MultipleChoice(
            (
                Array(2, 9),
                EqualStripDiagram(9, 2, None),
                RepeatedAddition((2, 2, 2, 2, 2, 2, 2, 2, 2)),
                Array(3, 9),
                EqualStripDiagram(2, 2, None),
                EqualJumpLine(2, 2),
            ),
            frozenset({0, 1, 2}),
        ),
    ),
    Question(
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (3, 4),
            12,
            "There are 3 boxes. Each box holds 4 crayons. How many crayons altogether?",
        ),
        MultipleChoice(
            (
                StripDiagram((3, 4), None),
                EqualJumpLine(4, 4),
                Array(4, 2),
                RepeatedAddition((4, 4, 4)),
                EqualStripDiagram(3, 4, None),
                EqualJumpLine(3, 4),
            ),
            frozenset({3, 4, 5}),
        ),
    ),
]

# 12 groups of 8: 13 parts of 8, 13 eights added, which wrap onto a second line, and 12 rows of
# 12. 2 groups of 12: 12 jumps of 12, whose numbers shrink to fit between the ticks, and 2 and 12
# as two parts, split at 0.32.
AT_THEIR_LIMITS: list[MultiplicationModelsQuestion] = [
    Question(
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (12, 8),
            96,
            "There are 12 boxes. Each box holds 8 stamps. How many stamps altogether?",
        ),
        MultipleChoice(
            (
                Array(8, 12),
                EqualJumpLine(12, 8),
                EqualStripDiagram(13, 8, None),
                RepeatedAddition((8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8)),
                RepeatedAddition((8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8)),
                Array(12, 12),
            ),
            frozenset({0, 1, 4}),
        ),
    ),
    Question(
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (2, 12),
            24,
            "A frog hops 12 spaces each time it jumps. It jumps 2 times. "
            "How many spaces does the frog move in all?",
        ),
        MultipleChoice(
            (
                Array(2, 12),
                EqualJumpLine(12, 12),
                StripDiagram((2, 12), None),
                RepeatedAddition((12, 12)),
                EqualJumpLine(2, 12),
                RepeatedAddition((12, 12, 12)),
            ),
            frozenset({0, 3, 4}),
        ),
    ),
]

EXPECTED = GOLDENS / "multiplication_models_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "jump_labels", "answer_key", "title", "label"),
    [
        # The instruction under the header, then each problem's wording and its models, two to a
        # row, lettered A to F, with the number lines' jumps numbered. The key gives each
        # equation, answer and letters, then what each wrong model shows.
        ("answer_key", THREE_PROBLEMS, True, True, TITLE, "Sheet A"),
        # the number lines' jumps left for the student to count
        ("no_jump_labels", THREE_PROBLEMS, False, False, TITLE, "Sheet A"),
        ("at_their_limits", AT_THEIR_LIMITS, True, False, TITLE, "Sheet A"),
        # the title and label are the ones given
        ("title_and_label", THREE_PROBLEMS, True, True, "Models Practice", "Week 3"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: list[MultiplicationModelsQuestion],
    jump_labels: bool,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``multiplication_models_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the wording, the models and their letters, the answer
    key, the page breaks, and the title and label.
    """
    actual = pdf_text(
        render_multiplication_models(questions, jump_labels, answer_key, title, label)
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
