"""
Tests for the data and graphs worksheet PDFs, rendered from hand-built problems.

The problem generator is not used. Problems are built by hand from the test topics in
``tests.data``.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/data_graphs_worksheet_pdf_expecteds.txt``. The text includes the instruction, every
problem's introduction, task, displays and questions with their answer boxes, the answer key and
the page breaks. To regenerate sections after an intended change, uncomment the ``write_section``
lines in ``test_pdf_draws_the_expected_text`` and run it (``-k`` selects cases).
"""

from io import BytesIO

import pytest

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DiscreteDataProblem,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    SummarizeDataQuestionData,
)
from core.discrete_data.topics import NumberListTopic
from render.pdf.data_displays import NumberListStyle, draw_display
from render.pdf.page import new_pdf
from tests.data import CANS, CLASSES, FRUIT
from tests.helpers import (
    GOLDENS,
    discrete_data_problem,
    pdf_text,
    read_sections,
    render_data_graphs,
)

TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = DataDisplay  # enum order
GRID, COMMAS = NumberListStyle  # in the enum's order
TITLE = "Data and Graphs — Read, Complete, Solve"

# A survey with a scale of 2: bananas and grapes are half stars in a pictograph
FRUIT_DATA = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(12, 5, 9, 4),
    scale=2,
    person="Ana",
)
# Friends with a scale of 5, so a bar graph's axis goes up in fives
CANS_DATA = CategoricalData(
    topic=CANS,
    categories=("Ben", "Cy", "Dot", "Eve"),
    counts=(30, 15, 25, 10),
    scale=5,
    person=None,
)
# Friends in a dot plot, with a scale of 2
DOT_PLOT_DATA = CategoricalData(
    topic=CANS,
    categories=("Ana", "Ben", "Cy", "Dot"),
    counts=(6, 2, 9, 4),
    scale=2,
    person=None,
)
# A number list whose line has two numbers that aren't in the list, 19 and 22
CLASSES_DATA = NumericalData(
    topic=CLASSES,
    values=(18, 20, 18, 21, 20, 18, 23),
    ticks=(18, 19, 20, 21, 22, 23),
    person="Eve",
)
# A topic whose questions take more than a line
MINUTES = NumberListTopic(
    title="Minutes to Get to School",
    axis_title="Number of Minutes",
    ticks=range(5, 61, 5),
    unit="students",
    unit_singular="student",
    phrase="take {amount} to get to school",
    amount_singular="minute",
    amount_plural="minutes",
    intro="{person} asked some students how many minutes it takes them to get to school. The "
    "list shows their answers.",
)
# 18 numbers, three rows of a grid, on a line of 12 ticks
MINUTES_DATA = NumericalData(
    topic=MINUTES,
    values=(10, 15, 10, 20, 25, 10, 15, 60, 20, 10, 15, 30, 35, 40, 45, 50, 55, 5),
    ticks=(5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60),
    person="Cy",
)

# Every display, each given and completed once: a table and a pictograph, a pictograph and a bar
# graph, a list and a number line, and a dot plot and a table. Two to a page.
EVERY_DISPLAY = [
    discrete_data_problem(
        SummarizeDataQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, (1, 2), (5, 9)),
        CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 3), 8),
        CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.ALL_BUT, (3,), 26),
    ),
    discrete_data_problem(
        SummarizeDataQuestionData(CANS_DATA, PICTOGRAPH, BAR_GRAPH, (0, 3), (30, 10)),
        CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.FEWER, (2, 1), 10),
        CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.MORE_THAN_PAIR, (0, 1, 3), 5),
    ),
    discrete_data_problem(
        SummarizeDataQuestionData(
            CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5), (3, 0, 2, 1, 0, 1)
        ),
        NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.PAIR_TOTAL, (2, 3), 3),
        NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.AT_LEAST, (2,), 4),
    ),
    discrete_data_problem(
        SummarizeDataQuestionData(DOT_PLOT_DATA, DOT_PLOT, TABLE, (0, 2), (6, 9)),
        CategoricalDataProblemData(DOT_PLOT_DATA, CategoricalProblemType.PAIR_TOTAL, (2, 0), 15),
        CategoricalDataProblemData(DOT_PLOT_DATA, CategoricalProblemType.PAIR_MORE, (0, 3, 2), 1),
    ),
]
LONG_QUESTIONS = [
    discrete_data_problem(
        SummarizeDataQuestionData(
            MINUTES_DATA,
            LIST,
            NUMBER_LINE_DOT_PLOT,
            (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
            (1, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1),
        ),
        NumericalDataProblemData(MINUTES_DATA, NumericalProblemType.MORE, (1, 2), 1),
        NumericalDataProblemData(MINUTES_DATA, NumericalProblemType.PAIR_MORE, (1, 2, 3), 5),
    ),
]

EXPECTED = GOLDENS / "data_graphs_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "problems", "list_style", "answer_key", "title", "label"),
    [
        # The instruction under the header. Each problem's introduction, task and two displays,
        # the second missing its blank counts, then two questions with answer boxes. A list is
        # a grid of boxes.
        ("every_display", EVERY_DISPLAY, GRID, False, TITLE, "Sheet A"),
        # the list's numbers separated by commas, in a box
        ("commas", EVERY_DISPLAY[2:3], COMMAS, False, TITLE, "Sheet A"),
        # the key has each problem's blank counts, then its answers with their work
        ("answer_key", EVERY_DISPLAY, GRID, True, TITLE, "Sheet A"),
        # Questions of two lines, each answer box beside its first, and the label clear of the
        # text. Three rows in the grid.
        ("long_questions", LONG_QUESTIONS, GRID, False, TITLE, "Sheet A"),
        # the title and label are the ones given
        ("title_and_label", EVERY_DISPLAY[:1], GRID, True, "Graphs Practice", "Week 3"),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    problems: list[DiscreteDataProblem],
    list_style: NumberListStyle,
    answer_key: bool,
    title: str,
    label: str,
) -> None:
    """
    The decoded PDF matches this case's section of ``data_graphs_worksheet_pdf_expecteds.txt``.

    One comparison covers the instruction, the introductions and tasks, the displays and their
    blanks, the questions and answer boxes, the answer key, the page breaks, and the title and
    label.
    """
    actual = pdf_text(render_data_graphs(problems, list_style, answer_key, title, label))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("display", "dataset", "message"),
    [
        (LIST, FRUIT_DATA, "A list display can't show CategoricalData."),
        (TABLE, CLASSES_DATA, "A table display can't show NumericalData."),
        (
            NUMBER_LINE_DOT_PLOT,
            CANS_DATA,
            "A number_line_dot_plot display can't show CategoricalData.",
        ),
        (DOT_PLOT, CLASSES_DATA, "A dot_plot display can't show NumericalData."),
    ],
)
def test_draw_display_errors(
    display: DataDisplay, dataset: CategoricalData | NumericalData, message: str
) -> None:
    """A categorical data set can't be drawn as a list or number line, nor a number list as the
    other displays."""
    pdf = new_pdf(BytesIO(), "Test")
    with pytest.raises(ValueError) as error:
        draw_display(pdf, display, dataset, 0, 0, 200, 150, (), GRID)
    assert str(error.value) == message
