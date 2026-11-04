"""
Tests for the arithmetic worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, and ``reverse_shuffle`` fixes
their option order by reversing the options, so the correct answer is always last.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/basic_operations_worksheet_pdf_expecteds.txt``. The text includes every question's
wording, the answer key's equations and letters, and the page breaks, so a changed title or a
moved line appears as a changed line in ``git diff``. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` selects cases).
"""

from collections.abc import Callable

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.question import QuestionData
from tests.helpers import (
    GOLDENS,
    pdf_text,
    read_sections,
    render_basic_operations,
    render_missing_numbers,
    reverse_shuffle,
)

# (question data, its wrong answers)
FOUR_OPERATIONS = [
    (BasicOperationQuestionData(Operation.ADD, (3, 4), 7), (0, 1, 2)),
    (BasicOperationQuestionData(Operation.SUBTRACT, (9, 4), 5), (10,)),
    (BasicOperationQuestionData(Operation.MULTIPLY, (6, 7), 42), (12, 13)),
    (BasicOperationQuestionData(Operation.DIVIDE, (8, 2), 4), (1, 2, 3)),
]

WORD_PROBLEMS = [
    (
        BasicOperationQuestionData(
            Operation.MULTIPLY,
            (4, 3),
            12,
            "Bob has 4 friends and gives each friend 3 apples. How many apples does Bob give away?",
        ),
        (7, 9, 10),
    ),
    (
        BasicOperationQuestionData(
            Operation.ADD,
            (25, 17),
            42,
            "Maria collected 25 stickers on Monday and 17 more on Tuesday. "
            "How many stickers does she have now?",
        ),
        (32, 52, 41),
    ),
    (
        BasicOperationQuestionData(
            Operation.SUBTRACT,
            (50, 18),
            32,
            "A baker made 50 muffins for the school sale. By lunch time 18 of them had been "
            "sold to students and teachers, and the baker wants to know how many muffins are "
            "left to sell in the afternoon. How many muffins are left?",
        ),
        (68, 42),
    ),
]

NINE_QUESTIONS = [
    (BasicOperationQuestionData(Operation.ADD, (number, number), 2 * number), (100, 101, 102))
    for number in range(1, 10)
]

# Each number missing, with numbers up to 3 digits, the widest a square holds.
MISSING_NUMBERS = [
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28), ()),
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4), ()),
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 9, 111, 999), ()),
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 999, 3, 333), ()),
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 1, 1, 1), ()),
]

# Two columns of 11 rows fill a page, so the 23rd equation starts a second.
TWENTY_THREE_MISSING_NUMBERS = [
    (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, number, 1, number), ())
    for number in range(1, 24)
]


EXPECTED = GOLDENS / "basic_operations_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "render", "cases", "answer_key", "title", "label"),
    [
        (
            "four_operations",
            render_basic_operations,
            FOUR_OPERATIONS,
            False,
            "Arithmetic",
            "Sheet A",
        ),
        (
            "four_operations_answer_key",
            render_basic_operations,
            FOUR_OPERATIONS,
            True,
            "Arithmetic",
            "Sheet A",
        ),
        (
            "four_operations_other_title_and_label",
            render_basic_operations,
            FOUR_OPERATIONS,
            False,
            "Times Tables",
            "Day 2",
        ),
        (
            "word_problems_answer_key",
            render_basic_operations,
            WORD_PROBLEMS,
            True,
            "Arithmetic",
            "Sheet A",
        ),
        (
            "nine_questions_answer_key",
            render_basic_operations,
            NINE_QUESTIONS,
            True,
            "Arithmetic",
            "Sheet A",
        ),
        # The missing-number sheet draws its title and label as the multiple-choice sheet does.
        (
            "missing_numbers",
            render_missing_numbers,
            MISSING_NUMBERS,
            False,
            "Division",
            "Sheet A",
        ),
        (
            "missing_numbers_answer_key",
            render_missing_numbers,
            MISSING_NUMBERS,
            True,
            "Division",
            "Sheet A",
        ),
        (
            "twenty_three_missing_numbers_answer_key",
            render_missing_numbers,
            TWENTY_THREE_MISSING_NUMBERS,
            True,
            "Division",
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    render: Callable[[list[tuple[QuestionData, tuple[int, ...]]], bool, str, str], bytes],
    cases: list[tuple[QuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``basic_operations_worksheet_pdf_expecteds.txt``.

    ``render`` is the multiple-choice or the missing-number worksheet. The text records every
    drawing command and its position, so one comparison covers the questions' wording and
    equations, the lettered options or the square drawn for each missing number, the answer
    key, the page breaks, and the title and label. The questions are built by hand with a
    predictable option order, so the generator is not involved.
    """
    reverse_shuffle(monkeypatch)

    actual = pdf_text(render(cases, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
