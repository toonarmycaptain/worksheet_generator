"""
Tests for the data and graphs PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, call the
generator with the settings its options describe, and draw the problems the generator returns:
its ``pdf_text`` must equal that of the PDF the renderer makes from them. An invalid request
must return 422 with the Django Ninja validation error and no PDF headers. The renderer itself
is tested in ``test_data_graphs_worksheet``, and the generator in
``test_core/test_discrete_data``.

Each problem asks one of several first parts, each drawing its own random numbers, so instead of
scripting them, the endpoint's generator is replaced: it records what it's called with, and
returns the case's problems. ``random.choice``, which draws each problem's list style for mix,
returns the last item, and ``conventional_slot_of``, which gives the slots of the simple tile
pattern, returns the slots of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DiscreteDataPart,
    DiscreteDataProblem,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    SummarizeDataQuestionData,
)
from core.discrete_data.generator import SHEET_DISPLAYS
from core.question import FreeResponse, Question
from render.pdf.data_displays import NumberListStyle
from tests.data import COINS, FRUIT, REAL_CASE_SLOTS
from tests.helpers import (
    choose_last,
    conventional_slot_of_returns,
    discrete_data_problem,
    pdf_text,
    refused,
    render_data_graphs,
)

TABLE, TALLY_TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = (
    DataDisplay  # enum order
)
GRID, COMMAS = NumberListStyle  # in the enum's order
EVERY_DISPLAY = list(SHEET_DISPLAYS)
EVERY_PART = list(DiscreteDataPart)
TITLE = "Data and Graphs — Read, Complete, Solve"

# The smallest counts for a scale of 2, or a dot plot
FRUIT_BY_TWOS = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(1, 2, 3, 4),
    scale=2,
    person="Eve",
)
# The smallest counts for a scale of 5
FRUIT_BY_FIVES = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(5, 10, 15, 20),
    scale=5,
    person="Eve",
)
# 5 four times, 10 twice and 25 three times, reversed
COINS_DATA = NumericalData(
    topic=COINS,
    values=(25, 25, 25, 10, 10, 5, 5, 5, 5),
    ticks=(0, 5, 10, 15, 20, 25, 30),
    person="Eve",
)
# a table completed in a pictograph: answers 3 and 10
TABLE_TO_PICTOGRAPH = discrete_data_problem(
    SummarizeDataQuestionData(FRUIT_BY_TWOS, TABLE, PICTOGRAPH, (0, 1), (1, 2)),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.ALL, (), 10),
)
# a pictograph completed in a bar graph: answers 15 and 50
PICTOGRAPH_TO_BAR_GRAPH = discrete_data_problem(
    SummarizeDataQuestionData(FRUIT_BY_FIVES, PICTOGRAPH, BAR_GRAPH, (0, 1), (5, 10)),
    CategoricalDataProblemData(FRUIT_BY_FIVES, CategoricalProblemType.PAIR_TOTAL, (1, 0), 15),
    CategoricalDataProblemData(FRUIT_BY_FIVES, CategoricalProblemType.ALL, (), 50),
)
# a list completed in a number-line dot plot
COINS_LIST = discrete_data_problem(
    SummarizeDataQuestionData(
        COINS_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5, 6), (0, 4, 2, 0, 0, 3, 0)
    ),
    NumericalDataProblemData(COINS_DATA, NumericalProblemType.MORE, (1, 2), 2),
    NumericalDataProblemData(COINS_DATA, NumericalProblemType.PAIR_MORE, (1, 2, 5), 3),
)
DOT_PLOT_TO_TABLE = discrete_data_problem(
    SummarizeDataQuestionData(FRUIT_BY_TWOS, DOT_PLOT, TABLE, (0, 1), (1, 2)),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.ALL, (), 10),
)
# a table and its one-step problem only
ONE_STEP_ONLY = DiscreteDataProblem(
    dataset=FRUIT_BY_TWOS,
    given=TABLE,
    summarize=None,
    one_step=Question(
        CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3),
        FreeResponse(),
    ),
    two_step=None,
)


@pytest.mark.parametrize(
    ("url", "returned", "expected_call", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # the defaults: 4 problems, every graph and table, every question, written answers
            "/api/worksheets/data_graphs.pdf?sheet=1ab2c3",
            [TABLE_TO_PICTOGRAPH, PICTOGRAPH_TO_BAR_GRAPH, COINS_LIST, DOT_PLOT_TO_TABLE],
            (4, EVERY_DISPLAY, EVERY_PART, False, False),
            200,
            None,
            {"list_styles": [GRID] * 4, "slot_of": None, "answer_key": False, "title": TITLE},
            "data_graphs-sheet-a.pdf",
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=1&sheet=1ab2c3",
            [TABLE_TO_PICTOGRAPH],
            (1, EVERY_DISPLAY, EVERY_PART, False, False),
            200,
            None,
            {"list_styles": [GRID], "slot_of": None, "answer_key": False, "title": TITLE},
            "data_graphs-sheet-a.pdf",
        ),
        (
            # every header option, with a list to show its commas
            "/api/worksheets/data_graphs.pdf?problems=1&list_style=commas&answer_key=true"
            "&name_line=true&title=Graphs+Practice&label=Week+3&sheet=1ab2c3",
            [COINS_LIST],
            (1, EVERY_DISPLAY, EVERY_PART, False, False),
            200,
            None,
            {
                "list_styles": [COMMAS],
                "slot_of": None,
                "answer_key": True,
                "title": "Graphs Practice",
                "label": "Week 3",
            },
            "data_graphs-week-3.pdf",
        ),
        (
            # the graphs and tables and the questions ticked, in the order sent, and multiple
            # choice
            "/api/worksheets/data_graphs.pdf?problems=1&displays=list&displays=dot_plot"
            "&questions=read_counts&questions=one_step&multiple_choice=true&sheet=1ab2c3",
            [COINS_LIST],
            (
                1,
                [LIST, DOT_PLOT],
                [DiscreteDataPart.READ_COUNTS, DiscreteDataPart.ONE_STEP],
                True,
                False,
            ),
            200,
            None,
            {"list_styles": [GRID], "slot_of": None, "answer_key": False, "title": TITLE},
            "data_graphs-sheet-a.pdf",
        ),
        (
            # mix draws each problem's list style
            "/api/worksheets/data_graphs.pdf?problems=2&list_style=mix&sheet=1ab2c3",
            [COINS_LIST, COINS_LIST],
            (2, EVERY_DISPLAY, EVERY_PART, False, False),
            200,
            None,
            {"list_styles": [COMMAS] * 2, "slot_of": None, "answer_key": False, "title": TITLE},
            "data_graphs-sheet-a.pdf",
        ),
        (
            # Tiles ask for different answers, and each word problem takes one: four tiles for
            # two problems.
            "/api/worksheets/data_graphs.pdf?problems=6&self_check_tiles=true&sheet=1ab2c3",
            [TABLE_TO_PICTOGRAPH, PICTOGRAPH_TO_BAR_GRAPH],
            (6, EVERY_DISPLAY, EVERY_PART, False, True),
            200,
            None,
            {
                "list_styles": [GRID] * 2,
                "slot_of": REAL_CASE_SLOTS[:4],
                "answer_key": False,
                "title": TITLE,
            },
            "data_graphs-sheet-a.pdf",
        ),
        (
            # with one word problem, a sheet of tiles can have 12 problems
            "/api/worksheets/data_graphs.pdf?problems=12&questions=one_step"
            "&self_check_tiles=true&sheet=1ab2c3",
            [ONE_STEP_ONLY],
            (12, EVERY_DISPLAY, [DiscreteDataPart.ONE_STEP], False, True),
            200,
            None,
            {
                "list_styles": [GRID],
                "slot_of": REAL_CASE_SLOTS[:1],
                "answer_key": False,
                "title": TITLE,
            },
            "data_graphs-sheet-a.pdf",
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=21",
            [],
            None,
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be less than or equal to 20",
                        "ctx": {"le": 20},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=0",
            [],
            None,
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be greater than or equal to 1",
                        "ctx": {"ge": 1},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/data_graphs.pdf?list_style=rows",
            [],
            None,
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "list_style"],
                        "msg": "Input should be 'grid', 'commas' or 'mix'",
                        "ctx": {"expected": "'grid', 'commas' or 'mix'"},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # a table alone can make only the word problems
            "/api/worksheets/data_graphs.pdf?displays=table",
            [],
            None,
            422,
            refused(
                "questions: those graphs and tables can't make Show the data another way, Read "
                "the counts, Find the error and Which one doesn't match"
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/data_graphs.pdf?questions=read_counts&self_check_tiles=true",
            [],
            None,
            422,
            refused("self_check_tiles: needs a one-step or two-step word problem"),
            None,
            None,
        ),
        (
            # two word problems each take a tile
            "/api/worksheets/data_graphs.pdf?problems=7&self_check_tiles=true",
            [],
            None,
            422,
            refused(
                "problems: self-check tiles has 12 tiles, one for each word problem, so at most 6"
            ),
            None,
            None,
        ),
        (
            # pictographs that don't all match have few different answers
            "/api/worksheets/data_graphs.pdf?problems=5&displays=pictograph"
            "&questions=doesnt_match&questions=one_step&questions=two_step&self_check_tiles=true",
            [],
            None,
            422,
            refused(
                "problems: at most 4 with a different answer on every tile, as Which one doesn't "
                "match has few different answers with those graphs and tables. Tick more graphs "
                "and tables or questions, or untick it"
            ),
            None,
            None,
        ),
    ],
)
def test_data_graphs_pdf(
    url: str,
    returned: list[DiscreteDataProblem],
    expected_call: tuple[int, list[DataDisplay], list[DiscreteDataPart], bool, bool] | None,
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The endpoint calls the generator with the request's options and returns the PDF of what it
    makes, or refuses invalid options before drawing anything.
    """
    calls: list[tuple[int, list[DataDisplay], list[DiscreteDataPart], bool, bool]] = []

    def generate(
        count: int,
        displays: list[DataDisplay],
        parts: list[DiscreteDataPart],
        *,
        multiple_choice: bool,
        distinct_answers: bool,
    ) -> list[DiscreteDataProblem]:
        calls.append((count, displays, parts, multiple_choice, distinct_answers))
        return returned

    monkeypatch.setattr("worksheets.registry.generate_discrete_data_problems", generate)
    choose_last(monkeypatch)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if filename else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json is not None:
        assert (response.json(), calls) == (expected_json, [])
    else:
        assert pdf_data is not None
        expected_pdf = render_data_graphs(
            returned,
            pdf_data["list_styles"],
            pdf_data["answer_key"],
            pdf_data["title"],
            pdf_data.get("label", "Sheet A"),
            slot_of=pdf_data["slot_of"],
            name_line="label" in pdf_data,
        )
        assert (pdf_text(response.content), calls) == (pdf_text(expected_pdf), [expected_call])
