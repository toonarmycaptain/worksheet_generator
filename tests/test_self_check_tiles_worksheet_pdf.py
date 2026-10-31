"""The self-check tiles worksheet PDF: what it draws for hand-built questions and a chosen slot
order.

Nothing here uses the question generator or the random slot order. What each case draws is kept
as text, decoded from the PDF, in one file with a section per case:
``goldens/self_check_tiles_worksheet_pdf_expecteds.txt``. The text holds the questions, the
answer bank in slot order (with the unused slots shaded), the letters, the answer key, and the
position and corners of every tile drawn for the pattern. A changed title, a moved line or a
wrong tile shows up as a changed line in ``git diff``. To regenerate sections after an intended
change, uncomment the regeneration block in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` picks cases).

The text can't show whether the pattern is right for a real case: that is checked on paper
by filling a case from the answer key, flipping it and comparing it with the picture.
"""

from io import BytesIO

import pytest

from core.arithmetic import ArithmeticQuestionData, Operation
from render.pdf.self_check_tiles_worksheet import render_self_check_tiles_worksheet
from tests.pdf_text import pdf_text
from tests.test_arithmetic_worksheet_pdf import read_sections
from tests.test_imported_snapshots import GOLDENS

# twelve questions with twelve different answers: 7 14 16 12 5 9 0 1 42 25 27 24
TWELVE = [
    ArithmeticQuestionData(Operation.ADD, (3, 4), 7),
    ArithmeticQuestionData(Operation.ADD, (5, 9), 14),
    ArithmeticQuestionData(Operation.ADD, (8, 8), 16),
    ArithmeticQuestionData(Operation.ADD, (2, 10), 12),
    ArithmeticQuestionData(Operation.SUBTRACT, (9, 4), 5),
    ArithmeticQuestionData(Operation.SUBTRACT, (10, 1), 9),
    ArithmeticQuestionData(Operation.SUBTRACT, (8, 8), 0),
    ArithmeticQuestionData(Operation.SUBTRACT, (7, 6), 1),
    ArithmeticQuestionData(Operation.MULTIPLY, (6, 7), 42),
    ArithmeticQuestionData(Operation.MULTIPLY, (5, 5), 25),
    ArithmeticQuestionData(Operation.MULTIPLY, (9, 3), 27),
    ArithmeticQuestionData(Operation.MULTIPLY, (4, 6), 24),
]

# each answer in the slot of its own number
IN_ORDER = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
# four questions: tiles 1 to 4 in F, A, L and G, and the other eight slots blocked out
FOUR = (5, 0, 11, 6)
# the slots of a real case (tile 1 in H, tile 2 in J, tile 3 in K, ...): three clean blocks
REAL_CASE = (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2)

EXPECTED = GOLDENS / "self_check_tiles_worksheet_pdf_expecteds.txt"


def render(
    slot_of: tuple[int, ...], answer_key: bool, title: str = "Arithmetic", label: str = "Sheet A"
) -> bytes:
    out = BytesIO()
    render_self_check_tiles_worksheet(
        TWELVE[: len(slot_of)], slot_of, out, title, label, answer_key
    )
    return out.getvalue()


@pytest.mark.parametrize(
    ("case_name", "slot_of", "answer_key", "title", "label"),
    [
        ("in_order", IN_ORDER, False, "Arithmetic", "Sheet A"),
        ("real_case", REAL_CASE, False, "Arithmetic", "Sheet A"),
        ("real_case_answer_key", REAL_CASE, True, "Arithmetic", "Sheet A"),
        ("in_order_other_title_and_label", IN_ORDER, False, "Number Facts", "Day 2"),
        ("four_questions", FOUR, False, "Arithmetic", "Sheet A"),
        ("four_questions_answer_key", FOUR, True, "Arithmetic", "Sheet A"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str, slot_of: tuple[int, ...], answer_key: bool, title: str, label: str
) -> None:
    """The decoded PDF equals this case's section of
    ``self_check_tiles_worksheet_pdf_expecteds.txt``."""
    actual = pdf_text(render(slot_of, answer_key, title, label))
    sections = read_sections(EXPECTED)

    # To regenerate pdfs, uncomment:
    # EXPECTED.write_text(
    #     "".join(
    #         f"=== {name} ===\n{body}\n\n" for name, body in (
    #                 sections | {case_name: actual}
    #         ).items()
    #     )
    # )

    assert actual == sections.get(case_name)
