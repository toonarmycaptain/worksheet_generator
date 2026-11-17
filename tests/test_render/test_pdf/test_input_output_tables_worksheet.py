"""
Tests for the input-output tables worksheet PDFs, rendered from hand-built questions.

The question generator is not used. Questions are built by hand from the contexts in
``tests.data``, and ``reverse_shuffle`` fixes a multiple-choice question's option order by
reversing the options, so the correct option is always last.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/input_output_tables_worksheet_pdf_expecteds.txt``. The text includes every rule,
question and instruction, each table's title, headings and numbers, the empty cells, the
lettered tables and statements, the sentences with their operations, box or lines, the answer
bank and pattern, the answer key and the page breaks. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it
(``-k`` selects cases).
"""

from collections.abc import Sequence
from typing import Any

import pytest

from core.basic_operations.data import Operation
from core.input_output_tables.data import (
    InputOutputQuestionData,
    InputOutputRuleQuestionData,
    InputOutputTableQuestionData,
    RuleForm,
)
from tests.data import READING, REAL_CASE_SLOTS, SALE, SOCKS
from tests.helpers import (
    GOLDENS,
    pdf_text,
    read_sections,
    render_input_output_tables,
    reverse_shuffle,
)

ADD, SUBTRACT, MULTIPLY, DIVIDE = Operation
SENTENCE, PLAIN, EXPLAINED = RuleForm

TIMES_8 = ((4, 32), (7, 56), (9, 72), (10, 80))
SALE_PAIRS = ((12, 18), (19, 25), (27, 33), (33, 39))

# (question data, its wrong options): none for a table to complete

# Two tables in two columns, then one in two rows. The subtraction table leaves out inputs and
# an output; the division table has a name, and its outputs come first in the answer key.
TABLES: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (), (1, 2, 3)), ()),
    (
        InputOutputTableQuestionData(
            SALE, None, SUBTRACT, 6, ((18, 12), (25, 19), (33, 27), (39, 33)), (0, 2), (3,)
        ),
        (),
    ),
    (
        InputOutputTableQuestionData(
            READING, "Ana", DIVIDE, 5, ((10, 2), (15, 3), (25, 5), (30, 6)), (1,), (0, 2)
        ),
        (),
    ),
]

# Five rows of two: the rows take turns at columns and rows, and the fifth starts a second page.
TEN_TABLES: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (
        InputOutputTableQuestionData(
            SOCKS,
            None,
            MULTIPLY,
            number,
            ((1, number), (2, 2 * number), (4, 4 * number)),
            (),
            (1, 2),
        ),
        (),
    )
    for number in range(2, 12)
]

# Tables to choose, in two columns, in two rows, then in two columns again, starting a second
# page: two in the swapped look, then one in the shared-inputs look, all four right in the first
# pair.
TABLE_CHOICES: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (
        InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
        (
            ((32, 4), (56, 7), (72, 9), (80, 10)),
            ((30, 38), (41, 49), (57, 65), (60, 68)),
            ((38, 30), (49, 41), (65, 57), (68, 60)),
        ),
    ),
    (
        InputOutputTableQuestionData(SALE, None, ADD, 6, SALE_PAIRS),
        (
            ((18, 12), (25, 19), (33, 27), (39, 33)),
            ((2, 6), (5, 9), (9, 13), (10, 14)),
            ((6, 2), (9, 5), (13, 9), (14, 10)),
        ),
    ),
    (
        InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8),
        (
            ((4, 32), (7, 49), (9, 63), (10, 70)),
            ((4, 32), (7, 42), (9, 54), (10, 60)),
            ((4, 32), (7, 35), (9, 45), (10, 50)),
        ),
    ),
]

# Sentences to complete: one operation, which the sentence states, with four numbers to circle;
# then, in a table of two rows, two operations and two numbers.
SENTENCES: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (
        InputOutputRuleQuestionData(
            READING, "Ana", ((2, 10), (3, 15), (5, 25), (6, 30)), (MULTIPLY, 5), SENTENCE
        ),
        ((MULTIPLY, 3), (MULTIPLY, 6), (MULTIPLY, 7)),
    ),
    (
        InputOutputRuleQuestionData(
            SALE, None, ((18, 12), (25, 19), (33, 27), (39, 33)), (SUBTRACT, 6), SENTENCE
        ),
        ((ADD, 6), (SUBTRACT, 9), (ADD, 9)),
    ),
]

# Statements to choose: plain, then explained, in a table of two rows.
STATEMENTS: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (
        InputOutputRuleQuestionData(SOCKS, None, TIMES_8, (MULTIPLY, 8), PLAIN),
        ((DIVIDE, 8), (MULTIPLY, 6), (DIVIDE, 6)),
    ),
    (
        InputOutputRuleQuestionData(SALE, None, SALE_PAIRS, (ADD, 6), EXPLAINED),
        ((SUBTRACT, 6), (ADD, 9), (SUBTRACT, 9)),
    ),
]

# One of each type of multiple-choice question on one sheet.
MIXED = [TABLE_CHOICES[0], SENTENCES[1], STATEMENTS[1]]

# One number left out of each, for the self-check tiles case: an output, an input, an output.
TILES: list[tuple[InputOutputQuestionData, tuple[Any, ...]]] = [
    (InputOutputTableQuestionData(SOCKS, None, MULTIPLY, 8, TIMES_8, (), (2,)), ()),
    (
        InputOutputTableQuestionData(
            SALE, None, SUBTRACT, 6, ((18, 12), (25, 19), (33, 27), (39, 33)), (0,), ()
        ),
        (),
    ),
    (
        InputOutputTableQuestionData(
            READING, "Ana", DIVIDE, 5, ((10, 2), (15, 3), (25, 5), (30, 6)), (), (3,)
        ),
        (),
    ),
]


EXPECTED = GOLDENS / "input_output_tables_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "questions", "slot_of", "answer_key", "title", "label"),
    [
        ("tables_to_complete", TABLES, None, False, "Input-Output Tables", "Sheet A"),
        ("tables_to_complete_answer_key", TABLES, None, True, "Input-Output Tables", "Sheet A"),
        ("ten_tables_answer_key", TEN_TABLES, None, True, "Input-Output Tables", "Sheet A"),
        (
            "tables_to_choose_answer_key",
            TABLE_CHOICES,
            None,
            True,
            "Input-Output Tables",
            "Sheet A",
        ),
        ("sentences_answer_key", SENTENCES, None, True, "Input-Output Tables", "Sheet A"),
        ("statements_answer_key", STATEMENTS, None, True, "Input-Output Tables", "Sheet A"),
        ("mixed_choices_answer_key", MIXED, None, True, "Input-Output Tables", "Sheet A"),
        ("tiles_answer_key", TILES, REAL_CASE_SLOTS[:3], True, "Input-Output Tables", "Sheet A"),
        ("other_title_and_label", TABLES, None, False, "Rules and Tables", "Day 2"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    questions: Sequence[tuple[InputOutputQuestionData, tuple[Any, ...]]],
    slot_of: tuple[int, ...] | None,
    answer_key: bool,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of
    ``input_output_tables_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction or each problem's question, the rules, the tables'
    titles, headings, numbers and empty cells, their layout in columns or rows, the lettered
    tables and statements, the sentences, the answer bank and pattern, the answer key, the page
    breaks, and the title and label.
    """
    reverse_shuffle(monkeypatch)

    actual = pdf_text(render_input_output_tables(questions, slot_of, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("questions", "message"),
    [
        (
            # a table to complete after a table to choose
            [TABLE_CHOICES[0], TABLES[0]],
            "Tables to complete can't share a sheet with multiple-choice questions.",
        ),
    ],
)
def test_render_input_output_tables_worksheet_errors(
    questions: Sequence[tuple[InputOutputQuestionData, tuple[Any, ...]]],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reverse_shuffle(monkeypatch)
    with pytest.raises(ValueError) as error:
        render_input_output_tables(questions, None, False, "Input-Output Tables", "Sheet A")
    assert str(error.value) == message
