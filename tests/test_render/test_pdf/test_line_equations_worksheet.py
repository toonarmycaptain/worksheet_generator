"""
Tests for the line worksheet PDFs, slope and intercepts, writing linear equations and graphing
linear equations, rendered from hand-built questions.

The question generator is not used. Questions are built by hand, and ``reverse_shuffle`` fixes
a multiple-choice question's option order by reversing the options, so the correct answer is
always last.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/line_equations_worksheet_pdf_expecteds.txt``. The text includes every question's
wording, the line in its given form with its stacked fractions, the answer lines, blanks or
choices, the tiles page, the answer key and the page breaks. To regenerate sections after an
intended change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text``
and run it (``-k`` selects cases).
"""

from fractions import Fraction

import pytest

from core.line_equations.data import (
    X_AXIS,
    Y_AXIS,
    Equation,
    Grid,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    NumberStyle,
    Relation,
    Stated,
    Statement,
)
from tests.helpers import GOLDENS, pdf_text, read_sections, render_line_questions, reverse_shuffle

SLOPE, RATE_OF_CHANGE, Y_INTERCEPT, X_INTERCEPT, ZERO, SLOPE_AND_Y_INTERCEPT = LineFeature
(
    SLOPE_INTERCEPT,
    STANDARD,
    POINT_SLOPE,
    POINT_AND_SLOPE,
    TWO_POINTS,
    VERTICAL,
    HORIZONTAL,
    TABLE,
    GRAPH,
    SLOPE_AND_INTERCEPT,
    INTERCEPTS,
) = LineForm
FRACTION, DECIMAL, MIXED_NUMBER = NumberStyle
PARALLEL, PERPENDICULAR = Relation

# (question data, its wrong answers): none for a written question

# Each form shown once, each asking the slope: 3x + 4y = 8 and others. Eight spill onto a
# second page.
EACH_FORM_SHOWN = [
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE, numbers=DECIMAL, function="f"), ()),
    (LineQuestionData(Line(2, -1, 3), STANDARD, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_SLOPE, Y_INTERCEPT, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, Y_INTERCEPT, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), TWO_POINTS, SLOPE, ((-4, 5), (4, -1))), ()),
    (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), ()),
    (LineQuestionData(Line(0, 5, -18), HORIZONTAL, Y_INTERCEPT, numbers=DECIMAL), ()),
]

# Each question asked once, as a number, a point, "undefined" and both numbers
EACH_QUESTION_ASKED = [
    (LineQuestionData(Line(3, 4, 8), STANDARD, RATE_OF_CHANGE), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, X_INTERCEPT, as_point=True), ()),
    (LineQuestionData(Line(3, 4, 8), STANDARD, ZERO), ()),
    (LineQuestionData(Line(1, 0, -4), VERTICAL, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE_AND_Y_INTERCEPT), ()),
]

# Numbers and points in a row, statements one under another
CHOICES = [
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE),
        (Fraction(-4, 3), Fraction(3, 4), Fraction(4, 3)),
    ),
    (LineQuestionData(Line(0, 1, 3), HORIZONTAL, SLOPE), (None, Fraction(3), Fraction(-3))),
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, Y_INTERCEPT, as_point=True),
        ((Fraction(2), Fraction(0)), (Fraction(0), Fraction(8, 3)), (Fraction(8, 3), Fraction(0))),
    ),
    (
        LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_AND_Y_INTERCEPT),
        (
            (Fraction(-4, 3), Fraction(2)),
            (Fraction(-3, 4), Fraction(8, 3)),
            (Fraction(-4, 3), Fraction(8, 3)),
        ),
    ),
]

# Twelve different answers for the tiles case, among them both numbers labelled on one tile
TWELVE = [
    (LineQuestionData(Line(1, -1, -number), SLOPE_INTERCEPT, Y_INTERCEPT), ())
    for number in range(1, 11)
] + [
    (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE), ()),
    (LineQuestionData(Line(3, 4, 8), SLOPE_INTERCEPT, SLOPE_AND_Y_INTERCEPT), ()),
]
TWELVE_SLOTS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)

# Each way an equation is written from, with each form asked; eleven spill onto a third page
EACH_EQUATION_GIVEN = [
    (LineQuestionData(Line(3, -4, -5), SLOPE_INTERCEPT, STANDARD), ()),
    (LineQuestionData(Line(7, 4, -28), STANDARD, SLOPE_INTERCEPT, numbers=DECIMAL), ()),
    (
        LineQuestionData(
            Line(3, 4, 8), POINT_SLOPE, SLOPE_INTERCEPT, ((-4, 5),), solved_for_y=True
        ),
        (),
    ),
    (LineQuestionData(Line(2, 1, 6), POINT_SLOPE, STANDARD, ((3, 0),)), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, POINT_SLOPE, ((-4, 5),)), ()),
    (LineQuestionData(Line(3, 4, 8), TWO_POINTS, POINT_SLOPE, ((-4, 5), (4, -1))), ()),
    (LineQuestionData(Line(1, 0, 3), TWO_POINTS, VERTICAL, ((3, 7), (3, -2))), ()),
    (LineQuestionData(Line(1, 0, -4), POINT_AND_SLOPE, VERTICAL, ((-4, 2),)), ()),
    (
        LineQuestionData(
            Line(5, 2, 6),
            SLOPE_INTERCEPT,
            SLOPE_INTERCEPT,
            ((2, -2),),
            reference=Line(2, -5, -10),
            relation=PERPENDICULAR,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(2, 3, 18),
            STANDARD,
            STANDARD,
            ((3, 4),),
            reference=Line(2, 3, 6),
            relation=PARALLEL,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(0, 1, 7), VERTICAL, HORIZONTAL, ((3, 7),), reference=Y_AXIS, relation=PERPENDICULAR
        ),
        (),
    ),
]

# Equations to choose from, STAAR's: A.2 2019 Q6 in a row, A.2 2026 Q46 one under another, a
# rewritten equation, and y = 7 against x = 7, y = 3 and x = 3
EQUATION_CHOICES = [
    (
        LineQuestionData(Line(1, -4, -12), TWO_POINTS, SLOPE_INTERCEPT, ((-4, 2), (12, 6))),
        (
            Equation(Line(1, -4, -4), SLOPE_INTERCEPT),
            Equation(Line(4, -1, -3), SLOPE_INTERCEPT),
            Equation(Line(4, -1, -1), SLOPE_INTERCEPT),
        ),
    ),
    (
        LineQuestionData(
            Line(8, 9, -78),
            SLOPE_INTERCEPT,
            POINT_SLOPE,
            ((-3, -6),),
            reference=Line(8, 9, 36),
            relation=PARALLEL,
        ),
        (
            Equation(Line(8, 9, 78), POINT_SLOPE, (3, 6)),
            Equation(Line(9, -8, 21), POINT_SLOPE, (-3, -6)),
            Equation(Line(9, -8, -21), POINT_SLOPE, (3, 6)),
        ),
    ),
    (
        LineQuestionData(Line(7, 3, -14), SLOPE_INTERCEPT, STANDARD),
        (
            Equation(Line(7, 3, 14), STANDARD),
            Equation(Line(7, -3, 14), STANDARD),
            Equation(Line(7, -3, -14), STANDARD),
        ),
    ),
    (
        LineQuestionData(
            Line(0, 1, 7), HORIZONTAL, HORIZONTAL, ((3, 7),), reference=X_AXIS, relation=PARALLEL
        ),
        (
            Equation(Line(0, 1, 3), HORIZONTAL),
            Equation(Line(1, 0, 7), VERTICAL),
            Equation(Line(1, 0, 3), VERTICAL),
        ),
    ),
]

# Twelve different equations for the tiles case, among them stacked fractions and point-slope
# form
TWELVE_EQUATIONS = [
    (LineQuestionData(Line(1, -1, -number), SLOPE_INTERCEPT, STANDARD), ())
    for number in range(1, 11)
] + [
    (LineQuestionData(Line(3, 4, 8), STANDARD, SLOPE_INTERCEPT), ()),
    (LineQuestionData(Line(3, 4, 8), POINT_AND_SLOPE, POINT_SLOPE, ((-4, 5),)), ()),
]

# Tables and grids in the left half with the answer beside them: a table down the page with an
# answer line, one across it with halves and two blanks, graphs labelled and not, a vertical
# line, a grid counting by 5, and two points with a blank grid
TABLES_AND_GRAPHS = [
    (LineQuestionData(Line(1, 2, 6), TABLE, SLOPE, ((2, 2),), table_xs=(-4, 2, 4, 8)), ()),
    (
        LineQuestionData(
            Line(3, -2, 1),
            TABLE,
            SLOPE_AND_Y_INTERCEPT,
            ((-3, -5),),
            table_xs=(-3, -1, 2, 5, 6),
            table_across=True,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(7, 5, 7), GRAPH, ZERO, ((-4, 7), (6, -7)), grid=Grid(10, 9, 1), labelled=True
        ),
        (),
    ),
    (LineQuestionData(Line(1, 0, 3), GRAPH, SLOPE, ((3, 2), (3, -4)), grid=Grid(10, 6, 1)), ()),
    (
        LineQuestionData(
            Line(1, -2, -6), TWO_POINTS, Y_INTERCEPT, ((2, 4), (-4, 1)), grid=Grid(10, 6, 1)
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(2, -1, -5), GRAPH, SLOPE, ((5, 15), (-5, -5)), grid=Grid(25, 25, 5), labelled=True
        ),
        (),
    ),
]

# An equation in point-slope form through a table's named row, and one in standard form from a
# graph
EQUATIONS_FROM_TABLES_AND_GRAPHS = [
    (
        LineQuestionData(Line(1, 2, 6), TABLE, POINT_SLOPE, ((4, 1),), table_xs=(-4, 2, 4, 8)),
        (),
    ),
    (
        LineQuestionData(Line(1, -3, -3), GRAPH, STANDARD, ((3, 2), (-6, -1)), grid=Grid(10, 5, 1)),
        (),
    ),
]

# Numbers chosen beside a graph; statements too wide for the right half, below a table
PICTURE_CHOICES = [
    (
        LineQuestionData(
            Line(1, -2, -6),
            GRAPH,
            Y_INTERCEPT,
            ((2, 4), (-4, 1)),
            grid=Grid(10, 6, 1),
            labelled=True,
        ),
        (Fraction(-6), Fraction(-3), Fraction(6)),
    ),
    (
        LineQuestionData(
            Line(1, 2, 6), TABLE, SLOPE_AND_Y_INTERCEPT, ((2, 2),), table_xs=(-4, 2, 4, 8)
        ),
        (
            (Fraction(-2), Fraction(3)),
            (Fraction(-1, 2), Fraction(-6)),
            (Fraction(-2), Fraction(-6)),
        ),
    ),
]

# Graphing lines: blank grids fitted to each line, from an equation, the intercepts, x = a and
# two points, and tables to complete, from an equation down the page and from a graph across it
GRAPHING = [
    (
        LineQuestionData(
            Line(2, -3, -3),
            SLOPE_INTERCEPT,
            GRAPH,
            grid=Grid(10, 5, 1),
            key_points=((0, 1), (-3, -1)),
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(1, 2, 2), INTERCEPTS, GRAPH, grid=Grid(10, 5, 1), key_points=((0, 1), (2, 0))
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(1, 0, -2), VERTICAL, GRAPH, grid=Grid(10, 5, 1), key_points=((-2, 0), (-2, -1))
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(3, 4, 8),
            TWO_POINTS,
            GRAPH,
            ((-4, 5), (4, -1)),
            grid=Grid(10, 7, 1),
            key_points=((-4, 5), (4, -1)),
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(1, 2, 6), STANDARD, TABLE, table_xs=(-4, 2, 4, 8), table_blanks=(1, 1, 0, 1)
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(1, -2, -6),
            GRAPH,
            TABLE,
            ((2, 4), (-4, 1)),
            grid=Grid(10, 6, 1),
            labelled=True,
            table_xs=(-4, -2, 2, 6),
            table_across=True,
            table_blanks=(1, 0, 1, 1),
        ),
        (),
    ),
]

# Graphs and tables to choose: y = 2/3x + 4 as in A.3 2025 Q35, its wrong graphs the slope's sign
# and the 4 on the other axis, sharing one grid; y = 2x - 3's tables down the page, y = -2x - 3's
# sharing the row (0, -3); tables across the page of a graphed line; y = 2.5's tables, two of
# them vertical lines', x and y exchanged
GRAPH_AND_TABLE_CHOICES = [
    (
        LineQuestionData(
            Line(2, -3, -12), SLOPE_AND_INTERCEPT, GRAPH, grid=Grid(12, 6, 1), chosen=True
        ),
        (
            Equation(Line(2, 3, 12), GRAPH),
            Equation(Line(2, -3, 8), GRAPH),
            Equation(Line(2, 3, 8), GRAPH),
        ),
    ),
    (
        LineQuestionData(
            Line(2, -1, 3), SLOPE_INTERCEPT, TABLE, table_xs=(0, 1, 3, 5), chosen=True
        ),
        (
            Equation(Line(2, 1, -3), TABLE),
            Equation(Line(2, -1, -3), TABLE),
            Equation(Line(2, 1, 3), TABLE),
        ),
    ),
    (
        LineQuestionData(
            Line(1, -2, -6),
            GRAPH,
            TABLE,
            ((2, 4), (-4, 1)),
            grid=Grid(12, 6, 1),
            labelled=True,
            table_xs=(-4, 0, 2, 4),
            table_across=True,
            chosen=True,
        ),
        (
            Equation(Line(1, 2, 6), TABLE),
            Equation(Line(1, -2, 6), TABLE),
            Equation(Line(1, 2, -6), TABLE),
        ),
    ),
    (
        LineQuestionData(
            Line(0, 2, 5),
            HORIZONTAL,
            TABLE,
            numbers=DECIMAL,
            table_xs=(-3, 1, 2, 4),
            chosen=True,
        ),
        (
            Equation(Line(2, 0, 5), TABLE),
            Equation(Line(0, 2, -5), TABLE),
            Equation(Line(2, 0, -5), TABLE),
        ),
    ),
]

# Statements about vertical and horizontal lines (A.2(G)): two labelled blanks, under the line
# or beside a graph, then four statements, each equation with each slope or direction
STATEMENTS = [
    (
        LineQuestionData(
            Line(1, 0, -4), TWO_POINTS, VERTICAL, ((-4, 9), (-4, 5)), statement=Statement.SLOPE
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(0, 1, 7),
            GRAPH,
            HORIZONTAL,
            ((-3, 7), (5, 7)),
            grid=Grid(12, 9, 1),
            labelled=True,
            statement=Statement.X_AXIS,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(0, 1, -7), TWO_POINTS, HORIZONTAL, ((10, -7), (1, -7)), statement=Statement.SLOPE
        ),
        (
            Stated(Equation(Line(0, 1, -7), HORIZONTAL), None),
            Stated(Equation(Line(1, 0, -7), VERTICAL), Fraction(0)),
            Stated(Equation(Line(1, 0, -7), VERTICAL), None),
        ),
    ),
    (
        LineQuestionData(
            Line(1, 0, 9), POINT_AND_SLOPE, VERTICAL, ((9, 10),), statement=Statement.X_AXIS
        ),
        (
            Stated(Equation(Line(1, 0, 9), VERTICAL), PARALLEL),
            Stated(Equation(Line(0, 1, 9), HORIZONTAL), PERPENDICULAR),
            Stated(Equation(Line(0, 1, 9), HORIZONTAL), PARALLEL),
        ),
    ),
]

# A tiles sheet of graphs and tables to find: the bank draws each on its own grid, or filled in
GRAPHING_TILES = [
    (
        LineQuestionData(
            Line(2, -3, -12),
            SLOPE_AND_INTERCEPT,
            GRAPH,
            grid=Grid(12, 6, 1),
            key_points=((0, 4), (-6, 0)),
            chosen=True,
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(2, -1, 3), SLOPE_INTERCEPT, TABLE, table_xs=(0, 1, 3, 5), chosen=True
        ),
        (),
    ),
    (
        LineQuestionData(
            Line(1, 0, -9),
            VERTICAL,
            GRAPH,
            grid=Grid(12, 6, 1),
            key_points=((-9, 0), (-9, 1)),
            chosen=True,
        ),
        (),
    ),
]

EXPECTED = GOLDENS / "line_equations_worksheet_pdf_expecteds.txt"


@pytest.mark.parametrize(
    ("case_name", "cases", "answer_key", "slot_of", "title", "label"),
    [
        (
            "each_form_shown_answer_key",
            EACH_FORM_SHOWN,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        (
            "each_question_asked_answer_key",
            EACH_QUESTION_ASKED,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        ("choices_answer_key", CHOICES, True, None, "Slope and Intercepts", "Sheet A"),
        ("tiles_answer_key", TWELVE, True, TWELVE_SLOTS, "Slope and Intercepts", "Sheet A"),
        ("other_title_and_label", EACH_QUESTION_ASKED, False, None, "Lines", "Day 2"),
        (
            "each_equation_given_answer_key",
            EACH_EQUATION_GIVEN,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "equation_choices_answer_key",
            EQUATION_CHOICES,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "equation_tiles_answer_key",
            TWELVE_EQUATIONS,
            True,
            TWELVE_SLOTS,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "tables_and_graphs_answer_key",
            TABLES_AND_GRAPHS,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        (
            "equations_from_tables_and_graphs_answer_key",
            EQUATIONS_FROM_TABLES_AND_GRAPHS,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "picture_choices_answer_key",
            PICTURE_CHOICES,
            True,
            None,
            "Slope and Intercepts",
            "Sheet A",
        ),
        (
            "graphing_answer_key",
            GRAPHING,
            True,
            None,
            "Graphing Linear Equations",
            "Sheet A",
        ),
        (
            "picture_tiles_answer_key",
            [TABLES_AND_GRAPHS[0], TABLES_AND_GRAPHS[2], TABLES_AND_GRAPHS[4]],
            True,
            (0, 1, 2),
            "Slope and Intercepts",
            "Sheet A",
        ),
        (
            "graph_and_table_choices_answer_key",
            GRAPH_AND_TABLE_CHOICES,
            True,
            None,
            "Graphing Linear Equations",
            "Sheet A",
        ),
        (
            "statements_answer_key",
            STATEMENTS,
            True,
            None,
            "Writing Linear Equations",
            "Sheet A",
        ),
        (
            "graphing_tiles_answer_key",
            GRAPHING_TILES,
            True,
            (0, 1, 2),
            "Graphing Linear Equations",
            "Sheet A",
        ),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    cases: list[tuple[LineQuestionData, tuple[LineAnswer, ...]]],
    answer_key: bool,
    slot_of: tuple[int, ...] | None,
    title: str,
    label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The decoded PDF matches this case's section of ``line_equations_worksheet_pdf_expecteds.txt``.

    One comparison covers the wording, the lines with their stacked fractions, the answer lines,
    blanks or lettered choices, the tiles page, the answer key's answers, letters and slots, the
    page breaks, and the title and label.
    """
    reverse_shuffle(monkeypatch)

    actual = pdf_text(render_line_questions(cases, answer_key, title, label, slot_of))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
