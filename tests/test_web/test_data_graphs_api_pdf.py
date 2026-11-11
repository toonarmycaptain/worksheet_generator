"""
Tests for the data and graphs PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the problems listed in the test
case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated problems and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_data_graphs_worksheet``.

The PDF tests use the topics and names in ``tests.data`` in place of the banks, and replace
these functions:

- ``random.randint`` returns the values listed in the test case, and raises ``ValueError`` for a
  value outside the bounds of its call. The first value is the shift from each given display to
  the display to complete, in the order table, pictograph, bar graph, dot plot: 1 completes a
  table as a pictograph, and 3 completes a number list as a number-line dot plot.
- ``random.random`` returns the values listed in the test case.
- ``random.choice`` returns the last item.
- ``random.sample`` returns the first items, in order.
- ``random.shuffle`` reverses the list.
"""

from typing import Any

import pytest
from django.test import Client

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    SummarizeDataQuestionData,
)
from render.pdf.data_displays import NumberListStyle
from tests.data import COINS, FRUIT, NAMES
from tests.helpers import (
    choose_last,
    discrete_data_problem,
    pdf_text,
    randint_returns,
    random_returns,
    render_data_graphs,
    reverse_shuffle,
    sample_first,
)

TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = DataDisplay  # enum order

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
# a table completed in a pictograph, with the last problem types
TABLE_TO_PICTOGRAPH = discrete_data_problem(
    SummarizeDataQuestionData(FRUIT_BY_TWOS, TABLE, PICTOGRAPH, (0, 1), (1, 2)),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3),
    CategoricalDataProblemData(FRUIT_BY_TWOS, CategoricalProblemType.ALL, (), 10),
)
# a list completed in a number-line dot plot: the draw under 0.6 makes the first problem MORE
COINS_LIST = discrete_data_problem(
    SummarizeDataQuestionData(
        COINS_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5, 6), (0, 4, 2, 0, 0, 3, 0)
    ),
    NumericalDataProblemData(COINS_DATA, NumericalProblemType.MORE, (1, 2), 2),
    NumericalDataProblemData(COINS_DATA, NumericalProblemType.PAIR_MORE, (1, 2, 5), 3),
)


@pytest.mark.parametrize(
    ("url", "drawn", "randoms", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # The defaults: 4 problems, one of each display to complete. The first two take
            # the first two scales in the deck, 2 and 5, and the dot plot's has a scale of 2.
            "/api/worksheets/data_graphs.pdf?sheet=1ab2c3",
            [1, 4, 2, 3],
            [0.5],
            200,
            None,
            {
                "problems": [
                    TABLE_TO_PICTOGRAPH,
                    discrete_data_problem(
                        SummarizeDataQuestionData(
                            FRUIT_BY_FIVES, PICTOGRAPH, BAR_GRAPH, (0, 1), (5, 10)
                        ),
                        CategoricalDataProblemData(
                            FRUIT_BY_FIVES, CategoricalProblemType.PAIR_TOTAL, (1, 0), 15
                        ),
                        CategoricalDataProblemData(
                            FRUIT_BY_FIVES, CategoricalProblemType.ALL, (), 50
                        ),
                    ),
                    COINS_LIST,
                    discrete_data_problem(
                        SummarizeDataQuestionData(FRUIT_BY_TWOS, DOT_PLOT, TABLE, (0, 1), (1, 2)),
                        CategoricalDataProblemData(
                            FRUIT_BY_TWOS, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3
                        ),
                        CategoricalDataProblemData(
                            FRUIT_BY_TWOS, CategoricalProblemType.ALL, (), 10
                        ),
                    ),
                ],
                "list_style": NumberListStyle.GRID,
                "answer_key": False,
                "title": "Data and Graphs — Read, Complete, Solve",
                "label": "Sheet A",
                "name_line": False,
            },
            "data_graphs-sheet-a.pdf",
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=1&sheet=1ab2c3",
            [1],
            [],
            200,
            None,
            {
                "problems": [TABLE_TO_PICTOGRAPH],
                "list_style": NumberListStyle.GRID,
                "answer_key": False,
                "title": "Data and Graphs — Read, Complete, Solve",
                "label": "Sheet A",
                "name_line": False,
            },
            "data_graphs-sheet-a.pdf",
        ),
        (
            # every option, with a list to show its commas
            "/api/worksheets/data_graphs.pdf?problems=1&list_style=commas&answer_key=true"
            "&name_line=true&title=Graphs+Practice&label=Week+3&sheet=1ab2c3",
            [3, 4, 2, 3],
            [0.5],
            200,
            None,
            {
                "problems": [COINS_LIST],
                "list_style": NumberListStyle.COMMAS,
                "answer_key": True,
                "title": "Graphs Practice",
                "label": "Week 3",
                "name_line": True,
            },
            "data_graphs-week-3.pdf",
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=9",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be less than or equal to 8",
                        "ctx": {"le": 8},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/data_graphs.pdf?problems=0",
            [],
            [],
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
            # no mix: the renderer has no randomness of its own
            "/api/worksheets/data_graphs.pdf?list_style=mix",
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "literal_error",
                        "loc": ["query", "list_style"],
                        "msg": "Input should be 'grid' or 'commas'",
                        "ctx": {"expected": "'grid' or 'commas'"},
                    },
                ],
            },
            None,
            None,
        ),
    ],
)
def test_data_graphs_pdf(
    url: str,
    drawn: list[int],
    randoms: list[float],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A request receives the PDF for its options, or the error identifying the invalid option.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (COINS,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    choose_last(monkeypatch)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if not expected_json else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render_data_graphs(
                problems=pdf_data["problems"],
                list_style=pdf_data["list_style"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
