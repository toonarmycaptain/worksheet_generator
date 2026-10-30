"""The arithmetic worksheet PDF: what it draws for hand-built questions.

Nothing here uses the question generator. Questions are built by hand, and
``predictable_choices`` makes their option order exact: the options are reversed, so the
correct answer is always last.

What each case draws is kept as text, decoded from the PDF, in one file with a section per
case: ``goldens/arithmetic_worksheet_pdf_expecteds.txt``. The text holds every question's wording,
the answer key's equations and letters, and the page breaks. A changed title or a moved line shows
up as a changed line in ``git diff``. Regenerate sections after an intended change (``-k``
picks cases)::

    REGEN_GOLDENS=1 uv run pytest tests/test_arithmetic_worksheet_pdf.py
"""

import re
from io import BytesIO
from pathlib import Path

import pytest

from core.arithmetic import ArithmeticQuestionData, Operation
from core.question import Question
from render.pdf.arithmetic_worksheet import render_arithmetic_worksheet
from tests.pdf_text import pdf_text
from tests.test_imported_snapshots import GOLDENS

# (question data, its wrong answers)
FOUR_OPERATIONS = [
    (ArithmeticQuestionData(Operation.ADD, (3, 4), 7), (0, 1, 2)),
    (ArithmeticQuestionData(Operation.SUBTRACT, (9, 4), 5), (10,)),
    (ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42), (12, 13)),
    (ArithmeticQuestionData(Operation.DIVIDE, (8, 2), 4), (1, 2, 3)),
]

WORD_PROBLEMS = [
    (
        ArithmeticQuestionData(
            Operation.MULTIPLY,
            (4, 3),
            12,
            "Bob has 4 friends and gives each friend 3 apples. How many apples does Bob give away?",
        ),
        (7, 9, 10),
    ),
    (
        ArithmeticQuestionData(
            Operation.ADD,
            (25, 17),
            42,
            "Maria collected 25 stickers on Monday and 17 more on Tuesday. "
            "How many stickers does she have now?",
        ),
        (32, 52, 41),
    ),
    (
        ArithmeticQuestionData(
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
    (ArithmeticQuestionData(Operation.ADD, (number, number), 2 * number), (100, 101, 102))
    for number in range(1, 10)
]


def build(cases: list[tuple[ArithmeticQuestionData, tuple[int, ...]]]) -> list[Question]:
    return [Question(data, wrong_answers) for data, wrong_answers in cases]


def render(
    questions: list[Question],
    answer_key: bool,
    title: str = "Arithmetic",
    label: str = "Sheet A",
) -> bytes:
    out = BytesIO()
    render_arithmetic_worksheet(questions, out, title, label, answer_key)
    return out.getvalue()


EXPECTED = GOLDENS / "arithmetic_worksheet_pdf_expecteds.txt"
SECTION = re.compile(r"^=== (.+) ===$", re.MULTILINE)


def read_sections(path: Path) -> dict[str, str]:
    """The expected text of each case, by case name. Empty if the file does not exist yet."""
    if not path.exists():
        return {}
    text = path.read_text()
    names = SECTION.findall(text)
    bodies = SECTION.split(text)[2::2]  # split() alternates: before, name, body, name, body...
    return {name: body.strip("\n") for name, body in zip(names, bodies, strict=True)}


@pytest.mark.usefixtures("predictable_choices")
@pytest.mark.parametrize(
    ("case_name", "cases", "answer_key", "title", "label"),
    [
        ("four_operations", FOUR_OPERATIONS, False, "Arithmetic", "Sheet A"),
        ("four_operations_answer_key", FOUR_OPERATIONS, True, "Arithmetic", "Sheet A"),
        ("four_operations_other_title_and_label", FOUR_OPERATIONS, False, "Times Tables", "Day 2"),
        ("word_problems_answer_key", WORD_PROBLEMS, True, "Arithmetic", "Sheet A"),
        ("nine_questions_answer_key", NINE_QUESTIONS, True, "Arithmetic", "Sheet A"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    cases: list[tuple[ArithmeticQuestionData, tuple[int, ...]]],
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """The decoded PDF equals this case's section of ``arithmetic_worksheet_pdf_expecteds.txt``.

    The text holds every drawing command and its position, so one comparison covers the
    questions' wording and equations, the lettered options, the answer key's letters, the page
    breaks, and the title and label. The questions are built by hand and their option order is
    made predictable, so the generator is not involved.
    """
    actual = pdf_text(render(build(cases), answer_key, title, label))
    sections = read_sections(EXPECTED)

    # To regenerate pdfs, uncomment:
    # EXPECTED.write_text(
    #     "".join(
    #         f"=== {name} ===\n{body}\n\n" for name, body in (
    #                 sections | {case_name: actual}
    #         ).items()
    #     )
    # )

    if case_name not in sections:
        pytest.fail(f"no expected text for {case_name}; create it with REGEN_GOLDENS=1")
    assert actual == sections[case_name]
