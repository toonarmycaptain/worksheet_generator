"""
Tests for data sets: a number list's counts, the wording of each question and display, and
generating a sheet.

The generator tests use the test topics and names in ``tests.data`` in place of the banks', and
script ``random``: ``randint``, ``random`` and ``randrange`` return the values listed, each within
its draw's bounds, ``choice`` returns the picks listed, which must be among its items, ``sample``
takes the first items in order, and ``shuffle`` reverses.
"""

from collections.abc import Callable

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
from core.discrete_data.generator import generate_discrete_data_problems
from core.discrete_data.representation import (
    axis_title,
    blank_counts,
    category_header,
    count_header,
    display_title,
    dot_plot_key,
    intro,
    labels,
    pictograph_key,
    stem,
    work,
)
from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from tests.data import CANS, CLASSES, COINS, FRUIT, MINUS, NAMES
from tests.helpers import (
    choice_returns,
    choose_last,
    discrete_data_problem,
    randint_returns,
    random_returns,
    randrange_returns,
    reverse_shuffle,
    sample_first,
    sample_last,
)

TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = DataDisplay  # enum order

# A survey with a scale of 2, so its odd counts are half stars in a pictograph
FRUIT_DATA = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(12, 5, 9, 4),
    scale=2,
    person="Ana",
)
# Friends, with a scale of 5
CANS_DATA = CategoricalData(
    topic=CANS,
    categories=("Ben", "Cy", "Dot", "Eve"),
    counts=(30, 15, 25, 10),
    scale=5,
    person=None,
)
# A number list whose line has two numbers that aren't in the list, 19 and 22
CLASSES_DATA = NumericalData(
    topic=CLASSES,
    values=(18, 20, 18, 21, 20, 18, 23),
    ticks=(18, 19, 20, 21, 22, 23),
    person="Eve",
)
# A number list of coins: three possible values on a line from 0 to 30
COINS_DATA = NumericalData(
    topic=COINS,
    values=(25, 5, 10, 5),
    ticks=(0, 5, 10, 15, 20, 25, 30),
    person="Ana",
)


@pytest.mark.parametrize(
    ("dataset", "counts"),
    [
        (CLASSES_DATA, (3, 0, 2, 1, 0, 1)),
        (COINS_DATA, (0, 2, 1, 0, 0, 1, 0)),
        # an empty list has no Xs
        (NumericalData(topic=CLASSES, values=(), ticks=(15, 16), person="Eve"), (0, 0)),
    ],
)
def test_numerical_data_counts(dataset: NumericalData, counts: tuple[int, ...]) -> None:
    """A tick's count is how many numbers in the list equal it, 0 for a number not in it."""
    assert dataset.counts == counts


@pytest.mark.parametrize(
    ("data", "intro_text", "task", "blanks_text"),
    [
        (
            SummarizeDataQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, (1, 2), (5, 9)),
            "Ana asked some students to name their favorite fruit. The frequency table shows the "
            "results.",
            "Use the frequency table to complete the pictograph.",
            "Bananas: 5,  Grapes: 9",
        ),
        (
            SummarizeDataQuestionData(FRUIT_DATA, BAR_GRAPH, TABLE, (0, 3), (12, 4)),
            "Ana asked some students to name their favorite fruit. The bar graph shows the "
            "results.",
            "Use the bar graph to complete the frequency table.",
            "Apples: 12,  Pears: 4",
        ),
        (
            SummarizeDataQuestionData(CANS_DATA, DOT_PLOT, BAR_GRAPH, (0, 3), (30, 10)),
            "Four friends collected cans for a food drive. The dot plot shows how many cans each "
            "friend collected.",
            "Use the dot plot to complete the bar graph.",
            "Ben: 30,  Eve: 10",
        ),
        (
            SummarizeDataQuestionData(CANS_DATA, PICTOGRAPH, TABLE, (1, 2), (15, 25)),
            "Four friends collected cans for a food drive. The pictograph shows how many cans "
            "each friend collected.",
            "Use the pictograph to complete the frequency table.",
            "Cy: 15,  Dot: 25",
        ),
        # From a list, the student draws every X. The key leaves out the numbers with none.
        (
            SummarizeDataQuestionData(
                CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5), (3, 0, 2, 1, 0, 1)
            ),
            "The list shows how many students are in each class at Eve's school.",
            "Use the list to complete the dot plot. Draw one X for each number in the list.",
            "3 at 18,  2 at 20,  1 at 21,  1 at 23",
        ),
        (
            SummarizeDataQuestionData(
                COINS_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5, 6), (0, 2, 1, 0, 0, 1, 0)
            ),
            "Ana emptied a piggy bank. The list shows the value of each coin in cents.",
            "Use the list to complete the dot plot. Draw one X for each number in the list.",
            "2 at 5,  1 at 10,  1 at 25",
        ),
    ],
)
def test_summarize_wording(
    data: SummarizeDataQuestionData, intro_text: str, task: str, blanks_text: str
) -> None:
    """
    A problem's introduction names its given display, part a's task names both displays, and
    the answer key lists the blank counts.
    """
    assert (intro(data), stem(data), blank_counts(data)) == (intro_text, task, blanks_text)


@pytest.mark.parametrize(
    ("data", "text", "work_text"),
    [
        # a survey: apples 12, bananas 5, grapes 9, pears 4
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 1), 7),
            "How many more students chose apples than chose bananas?",
            f"12 {MINUS} 5 = 7",
        ),
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.FEWER, (2, 3), 5),
            "How many fewer students chose pears than chose grapes?",
            f"9 {MINUS} 4 = 5",
        ),
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.PAIR_TOTAL, (1, 3), 9),
            "How many students chose bananas or pears?",
            "5 + 4 = 9",
        ),
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.PAIR_MORE, (1, 2, 0), 2),
            "How many more students chose bananas or grapes than chose apples?",
            f"5 + 9 = 14,  14 {MINUS} 12 = 2",
        ),
        (
            CategoricalDataProblemData(
                FRUIT_DATA, CategoricalProblemType.MORE_THAN_PAIR, (0, 1, 3), 3
            ),
            "How many more students chose apples than chose bananas or pears?",
            f"5 + 4 = 9,  12 {MINUS} 9 = 3",
        ),
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.ALL_BUT, (2,), 21),
            "How many students did NOT choose grapes?",
            "12 + 5 + 4 = 21",
        ),
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.ALL, (), 30),
            "How many students answered the question in all?",
            "12 + 5 + 9 + 4 = 30",
        ),
        # friends: Ben 30, Cy 15, Dot 25, Eve 10
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.MORE, (0, 2), 5),
            "How many more cans did Ben collect than Dot?",
            f"30 {MINUS} 25 = 5",
        ),
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.FEWER, (1, 3), 5),
            "How many fewer cans did Eve collect than Cy?",
            f"15 {MINUS} 10 = 5",
        ),
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.PAIR_TOTAL, (1, 3), 25),
            "How many cans did Cy and Eve collect in all?",
            "15 + 10 = 25",
        ),
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.PAIR_MORE, (1, 2, 0), 10),
            "How many more cans did Cy and Dot collect together than Ben?",
            f"15 + 25 = 40,  40 {MINUS} 30 = 10",
        ),
        (
            CategoricalDataProblemData(
                CANS_DATA, CategoricalProblemType.MORE_THAN_PAIR, (0, 1, 3), 5
            ),
            "How many more cans did Ben collect than Cy and Eve together?",
            f"15 + 10 = 25,  30 {MINUS} 25 = 5",
        ),
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.ALL_BUT, (0,), 50),
            "How many cans did everyone except Ben collect in all?",
            "15 + 25 + 10 = 50",
        ),
        (
            CategoricalDataProblemData(CANS_DATA, CategoricalProblemType.ALL, (), 80),
            "How many cans were collected in all?",
            "30 + 15 + 25 + 10 = 80",
        ),
        # a number list: 18 three times, 20 twice, 21 and 23 once, and 19 and 22 not at all
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.MORE, (0, 2), 1),
            "How many more classes have 18 students than have 20 students?",
            f"3 {MINUS} 2 = 1",
        ),
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.PAIR_TOTAL, (2, 3), 3),
            "How many classes have 20 or 21 students?",
            "2 + 1 = 3",
        ),
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.PAIR_MORE, (0, 3, 2), 2),
            "How many more classes have 18 or 21 students than have 20 students?",
            f"3 + 1 = 4,  4 {MINUS} 2 = 2",
        ),
        # the work leaves out the numbers with no Xs
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.AT_LEAST, (2,), 4),
            "How many classes have 20 or more students?",
            "2 + 1 + 1 = 4",
        ),
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.AT_MOST, (2,), 5),
            "How many classes have 20 or fewer students?",
            "3 + 2 = 5",
        ),
        # an amount of 1 is singular
        (
            NumericalDataProblemData(
                NumericalData(topic=CLASSES, values=(1, 2, 2), ticks=(1, 2, 3), person="Eve"),
                NumericalProblemType.MORE,
                (1, 0),
                1,
            ),
            "How many more classes have 2 students than have 1 student?",
            f"2 {MINUS} 1 = 1",
        ),
        (
            NumericalDataProblemData(COINS_DATA, NumericalProblemType.MORE, (1, 2), 1),
            "How many more coins are worth 5 cents than are worth 10 cents?",
            f"2 {MINUS} 1 = 1",
        ),
    ],
)
def test_problem_wording(
    data: CategoricalDataProblemData | NumericalDataProblemData, text: str, work_text: str
) -> None:
    """Each type of problem's question, and the work the answer key shows for it."""
    assert (stem(data), work(data)) == (text, work_text)


@pytest.mark.parametrize(
    ("dataset", "title", "names", "category_heading", "count_heading", "key", "x_key"),
    [
        # a survey's categories are capitalized, and its counts are students
        (
            FRUIT_DATA,
            "Favorite Fruit",
            ("Apples", "Bananas", "Grapes", "Pears"),
            "Fruit",
            "Number of Students",
            "= 2 students",
            "Each X = 1 student",
        ),
        # friends are names, and their counts are the topic's unit
        (
            CANS_DATA,
            "Cans Collected",
            ("Ben", "Cy", "Dot", "Eve"),
            "Name",
            "Number of Cans",
            "= 5 cans",
            "Each X = 1 can",
        ),
    ],
)
def test_categorical_display_words(
    dataset: CategoricalData,
    title: str,
    names: tuple[str, ...],
    category_heading: str,
    count_heading: str,
    key: str,
    x_key: str,
) -> None:
    """The title, labels, table headings and keys that a categorical data set's displays draw."""
    assert (
        display_title(dataset),
        labels(dataset),
        category_header(dataset),
        count_header(dataset),
        pictograph_key(dataset),
        dot_plot_key(dataset),
    ) == (title, names, category_heading, count_heading, key, x_key)


@pytest.mark.parametrize(
    ("dataset", "title", "names", "x_key", "axis"),
    [
        (
            CLASSES_DATA,
            "Students in Each Class",
            ("18", "19", "20", "21", "22", "23"),
            "Each X = 1 class",
            "Number of Students",
        ),
        (
            COINS_DATA,
            "Coins in a Piggy Bank",
            ("0", "5", "10", "15", "20", "25", "30"),
            "Each X = 1 coin",
            "Value of Coin (cents)",
        ),
    ],
)
def test_numerical_display_words(
    dataset: NumericalData, title: str, names: tuple[str, ...], x_key: str, axis: str
) -> None:
    """The title, labels, key and axis title that a number list's displays draw."""
    assert (
        display_title(dataset),
        labels(dataset),
        dot_plot_key(dataset),
        axis_title(dataset),
    ) == (
        title,
        names,
        x_key,
        axis,
    )


# The data sets generated in test_generate_discrete_data_problems. A categorical data set's
# counts are the smallest allowed, and its categories the first.
GENERATED_FRUIT = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(1, 2, 3, 4),
    scale=2,
    person="Eve",
)
GENERATED_CANS = CategoricalData(
    topic=CANS,
    categories=("Ana", "Ben", "Cy", "Dot"),
    counts=(1, 2, 3, 4),
    scale=2,
    person=None,
)
# 5 four times, 10 twice and 25 three times, reversed
GENERATED_COINS = NumericalData(
    topic=COINS,
    values=(25, 25, 25, 10, 10, 5, 5, 5, 5),
    ticks=(0, 5, 10, 15, 20, 25, 30),
    person="Eve",
)
# the first 6 of the topic's ticks, 15 to 20, with 3, 2, 2, 2, 1 and 2 Xs, reversed
GENERATED_CLASSES = NumericalData(
    topic=CLASSES,
    values=(20, 20, 19, 18, 18, 17, 17, 16, 16, 15, 15, 15),
    ticks=(15, 16, 17, 18, 19, 20),
    person="Eve",
)
GENERATED_COINS_PROBLEM = discrete_data_problem(
    SummarizeDataQuestionData(
        GENERATED_COINS, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5, 6), (0, 4, 2, 0, 0, 3, 0)
    ),
    NumericalDataProblemData(GENERATED_COINS, NumericalProblemType.MORE, (1, 2), 2),
    NumericalDataProblemData(GENERATED_COINS, NumericalProblemType.PAIR_MORE, (1, 2, 5), 3),
)
GENERATED_CLASSES_PROBLEM = discrete_data_problem(
    SummarizeDataQuestionData(
        GENERATED_CLASSES, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5), (3, 2, 2, 2, 1, 2)
    ),
    NumericalDataProblemData(GENERATED_CLASSES, NumericalProblemType.PAIR_TOTAL, (0, 1), 5),
    NumericalDataProblemData(GENERATED_CLASSES, NumericalProblemType.AT_LEAST, (3,), 5),
)


@pytest.mark.parametrize(
    ("category_topics", "number_list_topics", "drawn", "randoms", "ranges", "picks", "expected"),
    [
        # The first draw shifts the displays one along: a table, completed in a pictograph. The
        # scale is the first in its deck. The question picks follow the person who asked.
        (
            (FRUIT,),
            (COINS,),
            [1],
            [],
            [],
            [
                "Eve",
                CategoricalProblemType.PAIR_TOTAL,
                CategoricalProblemType.MORE_THAN_PAIR,
                (CategoricalProblemType.MORE_THAN_PAIR, (3, 0, 1), 1),
            ],
            discrete_data_problem(
                SummarizeDataQuestionData(GENERATED_FRUIT, TABLE, PICTOGRAPH, (0, 1), (1, 2)),
                # the larger count first
                CategoricalDataProblemData(
                    GENERATED_FRUIT, CategoricalProblemType.PAIR_TOTAL, (1, 0), 3
                ),
                CategoricalDataProblemData(
                    GENERATED_FRUIT, CategoricalProblemType.MORE_THAN_PAIR, (3, 0, 1), 1
                ),
            ),
        ),
        # Two along, a bar graph. Friends are names, with no person who asked.
        (
            (CANS,),
            (COINS,),
            [2],
            [],
            [],
            [
                CategoricalProblemType.MORE,
                CategoricalProblemType.PAIR_MORE,
                (CategoricalProblemType.PAIR_MORE, (2, 3, 1), 5),
            ],
            discrete_data_problem(
                SummarizeDataQuestionData(GENERATED_CANS, TABLE, BAR_GRAPH, (0, 1), (1, 2)),
                CategoricalDataProblemData(GENERATED_CANS, CategoricalProblemType.MORE, (1, 0), 1),
                CategoricalDataProblemData(
                    GENERATED_CANS, CategoricalProblemType.PAIR_MORE, (2, 3, 1), 5
                ),
            ),
        ),
        # Three along, a dot plot, which becomes a number list. Each coin value is drawn 4, 2
        # and 3 times. The first two numbers' counts differ, and the draw under 0.6 makes it
        # MORE.
        (
            (FRUIT,),
            (COINS,),
            [3, 4, 2, 3],
            [0.5],
            [],
            ["Eve", NumericalProblemType.PAIR_MORE, (NumericalProblemType.PAIR_MORE, (1, 2, 5), 3)],
            GENERATED_COINS_PROBLEM,
        ),
        # 24 coins are too many, and are drawn again
        (
            (FRUIT,),
            (COINS,),
            [3, 8, 8, 8, 4, 2, 3],
            [0.5],
            [],
            ["Eve", NumericalProblemType.PAIR_MORE, (NumericalProblemType.PAIR_MORE, (1, 2, 5), 3)],
            GENERATED_COINS_PROBLEM,
        ),
        # 3 coins are too few, and are drawn again
        (
            (FRUIT,),
            (COINS,),
            [3, 1, 1, 1, 4, 2, 3],
            [0.5],
            [],
            ["Eve", NumericalProblemType.PAIR_MORE, (NumericalProblemType.PAIR_MORE, (1, 2, 5), 3)],
            GENERATED_COINS_PROBLEM,
        ),
        # A window of 6 ticks from the topic's start, and 12 numbers, each drawn anywhere on it
        # (a draw over 0.6), and the draw over 0.6 making the one-step problem PAIR_TOTAL
        (
            (FRUIT,),
            (CLASSES,),
            [3, 6, 0, 12],
            [0.9] * 13,
            [0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5],
            ["Eve", NumericalProblemType.AT_LEAST, (NumericalProblemType.AT_LEAST, (3,), 5)],
            GENERATED_CLASSES_PROBLEM,
        ),
        # 2 Xs on every tick is too short a stack, so the 12 numbers are drawn again
        (
            (FRUIT,),
            (CLASSES,),
            [3, 6, 0, 12, 12],
            [0.9] * 25,
            # the first attempt, then the second
            [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5],
            ["Eve", NumericalProblemType.AT_LEAST, (NumericalProblemType.AT_LEAST, (3,), 5)],
            GENERATED_CLASSES_PROBLEM,
        ),
    ],
)
def test_generate_discrete_data_problems(
    category_topics: tuple[SurveyTopic | FriendsTopic, ...],
    number_list_topics: tuple[NumberListTopic, ...],
    drawn: list[int],
    randoms: list[float],
    ranges: list[int],
    picks: list[object],
    expected: DiscreteDataProblem,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A one-problem sheet: its displays, data set, blanks and two problems."""
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", category_topics)
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", number_list_topics)
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    randrange_returns(monkeypatch, ranges)
    choice_returns(monkeypatch, picks)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    assert generate_discrete_data_problems(1) == [expected]


@pytest.mark.parametrize(
    ("count", "drawn", "randoms", "pairs"),
    [
        # Each display is completed once in four problems, and never from itself. The pair that
        # would complete a dot plot completes a number line from a list instead.
        (
            4,
            [1, 4, 2, 3],
            [0.5],
            [
                (TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
            ],
        ),
        (
            4,
            [2, 4, 2, 3],
            [0.5],
            [
                (TABLE, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (BAR_GRAPH, TABLE),
                (DOT_PLOT, PICTOGRAPH),
            ],
        ),
        (
            4,
            [3, 4, 2, 3],
            [0.5],
            [
                (LIST, NUMBER_LINE_DOT_PLOT),
                (PICTOGRAPH, TABLE),
                (BAR_GRAPH, PICTOGRAPH),
                (DOT_PLOT, BAR_GRAPH),
            ],
        ),
        # a fifth problem starts the rotation again
        (
            5,
            [1, 4, 2, 3],
            [0.5],
            [
                (TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
                (TABLE, PICTOGRAPH),
            ],
        ),
        (
            8,
            [1, 4, 2, 3, 4, 2, 3],
            [0.5, 0.5],
            [
                (TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
                (TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
            ],
        ),
    ],
)
def test_generate_discrete_data_problems_rotates_the_displays(
    count: int,
    drawn: list[int],
    randoms: list[float],
    pairs: list[tuple[DataDisplay, DataDisplay]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The displays are shuffled (here, kept in order: table, pictograph, bar graph, dot plot), and
    the first draw is how far along each one's display to complete is.
    """
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (COINS,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    choose_last(monkeypatch)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    problems = generate_discrete_data_problems(count)

    assert [
        (problem.summarize.data.given, problem.summarize.data.target) for problem in problems
    ] == pairs


@pytest.mark.parametrize(
    ("scales", "sample", "scales_and_counts"),
    [
        # The scales are dealt from a deck, so they differ until each has been used. A data set
        # in a dot plot has a scale of 2 and counts of 1 to 10, wherever it is in the deck.
        (
            (2, 5, 10),
            sample_first,
            [(2, (1, 2, 3, 4)), (5, (5, 10, 15, 20)), (2, (1, 2, 3, 4))],
        ),
        # An even scale allows half a symbol, an odd one a whole symbol, up to 8 symbols' worth.
        (
            (2,),
            sample_first,
            [(2, (1, 2, 3, 4)), (2, (1, 2, 3, 4)), (2, (1, 2, 3, 4))],
        ),
        (
            (2,),
            sample_last,
            [(2, (13, 14, 15, 16)), (2, (13, 14, 15, 16)), (2, (7, 8, 9, 10))],
        ),
        (
            (5,),
            sample_first,
            [(5, (5, 10, 15, 20)), (5, (5, 10, 15, 20)), (2, (1, 2, 3, 4))],
        ),
        (
            (5,),
            sample_last,
            [(5, (25, 30, 35, 40)), (5, (25, 30, 35, 40)), (2, (7, 8, 9, 10))],
        ),
        (
            (10,),
            sample_first,
            [(10, (5, 10, 15, 20)), (10, (5, 10, 15, 20)), (2, (1, 2, 3, 4))],
        ),
        (
            (10,),
            sample_last,
            [(10, (65, 70, 75, 80)), (10, (65, 70, 75, 80)), (2, (7, 8, 9, 10))],
        ),
    ],
)
def test_generate_discrete_data_problems_fits_counts_to_the_scale(
    scales: tuple[int, ...],
    sample: Callable[[pytest.MonkeyPatch], None],
    scales_and_counts: list[tuple[int, tuple[int, ...]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The scale and counts of the three categorical data sets on a sheet of four: a table
    completed in a pictograph, a pictograph completed in a bar graph, and a dot plot completed
    in a table. ``sample`` takes the smallest counts allowed, or the largest.
    """
    monkeypatch.setattr("core.discrete_data.generator.SCALES", scales)
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (COINS,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, [1, 4, 2, 3])
    random_returns(monkeypatch, [0.5])
    choose_last(monkeypatch)
    sample(monkeypatch)
    reverse_shuffle(monkeypatch)

    problems = generate_discrete_data_problems(4)

    datasets = [problem.summarize.data.dataset for problem in problems]
    assert [
        (dataset.scale, dataset.counts)
        for dataset in datasets
        if isinstance(dataset, CategoricalData)
    ] == scales_and_counts
