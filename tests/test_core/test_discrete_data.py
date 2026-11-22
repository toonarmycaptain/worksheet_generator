"""
Tests for data sets: a number list's counts, the wording of each question and display, and
generating a sheet.

The generator tests use the test topics and names in ``tests.data`` in place of the banks', and
script ``random``: ``randint``, ``random`` and ``randrange`` return the values listed, each within
its draw's bounds, ``choice`` returns the picks listed, which must be among its items, ``sample``
takes the first items in order, and ``shuffle`` reverses.
"""

from collections.abc import Callable
from dataclasses import replace

import pytest

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DiscreteDataPart,
    DiscreteDataProblem,
    DisplayChoice,
    DoesntMatchQuestionData,
    ErrorChoice,
    EveryTick,
    FindErrorQuestionData,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    Off,
    OneEach,
    ReadCountsQuestionData,
    RoundDown,
    ShownDisplay,
    SummarizeData,
    SummarizeDataQuestionData,
    SummarizeResponse,
    Swap,
    WrongScale,
)
from core.discrete_data.generator import (
    SHEET_DISPLAYS,
    available_parts,
    generate_discrete_data_problems,
    most_tile_problems,
)
from core.discrete_data.representation import (
    axis_title,
    blank_counts,
    category_header,
    count_header,
    counts_text,
    display_title,
    dot_plot_key,
    error_displays,
    error_fix,
    error_sentence,
    instruction,
    intro,
    labels,
    mistake,
    pictograph_key,
    stem,
    summarize_stem,
    tiles_note,
    work,
)
from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from core.question import FreeResponse, MultipleChoice, Question
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

TABLE, TALLY_TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = (
    DataDisplay  # enum order
)
ANOTHER_DISPLAY, READ_COUNTS, FIND_ERROR, DOESNT_MATCH, ONE_STEP, TWO_STEP = DiscreteDataPart

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
# The same list, for a topic that asks for a missing number from the total
MISSING_CLASSES_DATA = replace(
    CLASSES_DATA,
    topic=replace(
        CLASSES,
        missing_question="One class is missing from the list. All the classes together have "
        "{total} students. How many students are in the missing class?",
    ),
)
# A number list of coins: three possible values on a line from 0 to 30
COINS_DATA = NumericalData(
    topic=COINS,
    values=(25, 5, 10, 5),
    ticks=(0, 5, 10, 15, 20, 25, 30),
    person="Ana",
)
ALL_FRUIT = (12, 5, 9, 4)  # FRUIT_DATA's counts, as a choice or answer
# a marker for multiple choice, in wording that only asks whether a question has choices
CHOOSE_ONE = MultipleChoice((0,), frozenset({0}))
# a bar graph of FRUIT_DATA on a scale of 5 that reads its scale as 10, to choose among displays
SHOWN_BAR_GRAPH = ShownDisplay(BAR_GRAPH, 5, DisplayChoice(ALL_FRUIT, 10, (WrongScale(10),)))


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
    actual = (intro(data.dataset, data.given), stem(data), blank_counts(data))
    assert actual == (intro_text, task, blanks_text)


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
        # strictly more or fewer leaves out the number itself
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.MORE_THAN, (2,), 2),
            "How many classes have more than 20 students?",
            "1 + 1 = 2",
        ),
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.FEWER_THAN, (3,), 5),
            "How many classes have fewer than 21 students?",
            "3 + 2 = 5",
        ),
        (
            NumericalDataProblemData(COINS_DATA, NumericalProblemType.MORE_THAN, (2,), 1),
            "How many coins are worth more than 10 cents?",
            "1 = 1",
        ),
        # a missing number: the listed numbers' total, taken from the total given
        (
            NumericalDataProblemData(
                MISSING_CLASSES_DATA, NumericalProblemType.MISSING_VALUE, (), 19, 157
            ),
            "One class is missing from the list. All the classes together have 157 students. How "
            "many students are in the missing class?",
            f"18 + 20 + 18 + 21 + 20 + 18 + 23 = 138,  157 {MINUS} 138 = 19",
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


@pytest.mark.parametrize(
    ("data", "function", "message"),
    [
        # the topic has no missing-number question
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.MISSING_VALUE, (), 19, 157),
            stem,
            "A missing number needs its topic's question and a total.",
        ),
        (
            NumericalDataProblemData(
                MISSING_CLASSES_DATA, NumericalProblemType.MISSING_VALUE, (), 19
            ),
            stem,
            "A missing number needs its topic's question and a total.",
        ),
        (
            NumericalDataProblemData(
                MISSING_CLASSES_DATA, NumericalProblemType.MISSING_VALUE, (), 19
            ),
            work,
            "A missing number needs a total.",
        ),
    ],
)
def test_missing_value_errors(
    data: NumericalDataProblemData,
    function: Callable[[NumericalDataProblemData], str],
    message: str,
) -> None:
    """A missing number's question needs its topic's question and the total."""
    with pytest.raises(ValueError) as error:
        function(data)
    assert str(error.value) == message


# A problem completing a display with both word problems, and the same problem's other forms
FRUIT_SUMMARIZE = SummarizeDataQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, (1, 2), (5, 9))
COMPLETE = discrete_data_problem(
    FRUIT_SUMMARIZE,
    CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 1), 7),
    CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.ALL, (), 30),
)
CHOOSE = replace(
    COMPLETE,
    summarize=Question(
        FRUIT_SUMMARIZE, MultipleChoice((DisplayChoice((12, 5, 9, 4), 2, ()),), frozenset({0}))
    ),
)
READ = replace(
    COMPLETE,
    given=PICTOGRAPH,
    summarize=Question(
        ReadCountsQuestionData(FRUIT_DATA, PICTOGRAPH, (12, 5, 9, 4)), FreeResponse()
    ),
)
COMPLETE_ONE_STEP = replace(COMPLETE, two_step=None)
COMPLETE_ONLY = replace(COMPLETE, one_step=None, two_step=None)
WORDS_ONLY = replace(COMPLETE, summarize=None)
ONE_STEP_ONLY = replace(WORDS_ONLY, two_step=None)


@pytest.mark.parametrize(
    ("problems", "text"),
    [
        # the same task for every problem is named, then the problems
        (
            [COMPLETE, COMPLETE],
            "Read the data. Complete the second graph or table, then solve the problems.",
        ),
        (
            [CHOOSE],
            "Read the data. Choose the graph or table that shows the same data, then solve the "
            "problems.",
        ),
        (
            [COMPLETE_ONE_STEP],
            "Read the data. Complete the second graph or table, then solve the problem.",
        ),
        ([COMPLETE_ONLY], "Read the data. Complete the second graph or table."),
        # problems alone
        ([WORDS_ONLY], "Read the data, then solve the problems."),
        ([ONE_STEP_ONLY], "Read the data, then solve the problem."),
        # any other first part, or a mix, is a question
        ([READ], "Read the data, then answer the questions."),
        ([COMPLETE, CHOOSE], "Read the data, then answer the questions."),
        ([COMPLETE, WORDS_ONLY], "Read the data, then answer the questions."),
    ],
)
def test_instruction(problems: list[DiscreteDataProblem], text: str) -> None:
    """The sheet's instruction names the task every problem shares, or asks for answers."""
    assert instruction(problems) == text


@pytest.mark.parametrize(
    ("problems", "note"),
    [
        ([COMPLETE, READ], "Answer part a on the sheet. Parts b and c go on the tiles."),
        ([COMPLETE_ONE_STEP], "Answer part a on the sheet. Part b goes on the tiles."),
        # every part goes on a tile
        ([WORDS_ONLY], None),
        ([ONE_STEP_ONLY], None),
    ],
)
def test_tiles_note(problems: list[DiscreteDataProblem], note: str | None) -> None:
    """A tiles sheet whose problems have a first part says which parts go on the tiles."""
    assert tiles_note(problems) == note


@pytest.mark.parametrize(
    ("dataset", "given", "text"),
    [
        (
            FRUIT_DATA,
            TALLY_TABLE,
            "Ana asked some students to name their favorite fruit. The tally table shows the "
            "results.",
        ),
        (
            replace(CANS_DATA, categories=("Ben", "Cy", "Dot"), counts=(30, 15, 25)),
            BAR_GRAPH,
            "Three friends collected cans for a food drive. The bar graph shows how many cans "
            "each friend collected.",
        ),
        # with no display given, the introduction states the counts
        (
            FRUIT_DATA,
            None,
            "Ana asked some students to name their favorite fruit. 12 chose apples, 5 chose "
            "bananas, 9 chose grapes, and 4 chose pears.",
        ),
        (
            CANS_DATA,
            None,
            "Four friends collected cans for a food drive. Ben collected 30 cans, Cy collected 15 "
            "cans, Dot collected 25 cans, and Eve collected 10 cans.",
        ),
    ],
)
def test_intro(
    dataset: CategoricalData | NumericalData, given: DataDisplay | None, text: str
) -> None:
    """A problem's introduction names its given display, or states the counts."""
    assert intro(dataset, given) == text


@pytest.mark.parametrize(
    ("question", "text"),
    [
        (CHOOSE.summarize, "Which pictograph shows the same data?"),
        (
            Question(ReadCountsQuestionData(FRUIT_DATA, PICTOGRAPH, (12, 5, 9, 4)), FreeResponse()),
            "Use the pictograph to write how many students chose each fruit.",
        ),
        (
            Question(
                ReadCountsQuestionData(CANS_DATA, BAR_GRAPH, (30, 15, 25, 10)), FreeResponse()
            ),
            "Use the bar graph to write how many cans each friend collected.",
        ),
        (
            Question(ReadCountsQuestionData(FRUIT_DATA, PICTOGRAPH, (12, 5, 9, 4)), CHOOSE_ONE),
            "Which list matches the data in the pictograph?",
        ),
        # a list of numbers is read from its number line
        (
            Question(
                ReadCountsQuestionData(
                    CLASSES_DATA, NUMBER_LINE_DOT_PLOT, (18, 18, 18, 20, 20, 21, 23)
                ),
                FreeResponse(),
            ),
            "Write the numbers the dot plot shows, from least to greatest.",
        ),
        (
            Question(
                ReadCountsQuestionData(
                    CLASSES_DATA, NUMBER_LINE_DOT_PLOT, (18, 18, 18, 20, 20, 21, 23)
                ),
                CHOOSE_ONE,
            ),
            "Which list of numbers does the dot plot show?",
        ),
        (
            Question(
                FindErrorQuestionData(CANS_DATA, TABLE, BAR_GRAPH, None, 0, 25, 30), FreeResponse()
            ),
            "A bar graph of the data has one mistake. Complete the sentence to fix it.",
        ),
        (
            Question(
                FindErrorQuestionData(CANS_DATA, TABLE, BAR_GRAPH, None, 0, 25, 30), CHOOSE_ONE
            ),
            "A bar graph of the data has one mistake. Which sentence fixes it?",
        ),
        # two displays are named in the order of the displays, whichever has the error
        (
            Question(
                FindErrorQuestionData(CANS_DATA, TABLE, BAR_GRAPH, PICTOGRAPH, 0, 25, 30),
                CHOOSE_ONE,
            ),
            "A pictograph and a bar graph of the data should match, but one has a mistake. Which "
            "one has the mistake, and how should it be fixed?",
        ),
        (
            Question(DoesntMatchQuestionData(FRUIT_DATA, TABLE, SHOWN_BAR_GRAPH), CHOOSE_ONE),
            "Which one does NOT show the data in the frequency table?",
        ),
        (
            Question(DoesntMatchQuestionData(FRUIT_DATA, None, SHOWN_BAR_GRAPH), CHOOSE_ONE),
            "Which one does NOT show these data?",
        ),
    ],
)
def test_summarize_stem(question: Question[SummarizeData, SummarizeResponse], text: str) -> None:
    """Each first part's question, written or chosen."""
    assert summarize_stem(question) == text


@pytest.mark.parametrize(
    ("data", "choice", "displays", "sentence", "fix"),
    [
        # a pictograph's fix counts its symbols, with a half
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, None, 1, 7, 5),
            ErrorChoice(PICTOGRAPH, 1, 5),
            (PICTOGRAPH,),
            "The row for ____ should have ____ symbols.",
            "The row for Bananas should have 2\N{VULGAR FRACTION ONE HALF} symbols",
        ),
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, None, 1, 7, 5),
            ErrorChoice(PICTOGRAPH, 3, 4),
            (PICTOGRAPH,),
            "The row for ____ should have ____ symbols.",
            "The row for Pears should have 2 symbols",
        ),
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, None, 1, 7, 5),
            ErrorChoice(PICTOGRAPH, 3, 1),
            (PICTOGRAPH,),
            "The row for ____ should have ____ symbols.",
            "The row for Pears should have \N{VULGAR FRACTION ONE HALF} symbols",
        ),
        (
            FindErrorQuestionData(CANS_DATA, None, BAR_GRAPH, None, 0, 25, 30),
            ErrorChoice(BAR_GRAPH, 0, 30),
            (BAR_GRAPH,),
            "The bar for ____ should end at ____.",
            "The bar for Ben should end at 30",
        ),
        (
            FindErrorQuestionData(CANS_DATA, TABLE, TALLY_TABLE, None, 1, 16, 15),
            ErrorChoice(TALLY_TABLE, 1, 15),
            (TALLY_TABLE,),
            "The row for ____ should have ____ tally marks.",
            "The row for Cy should have 15 tally marks",
        ),
        (
            FindErrorQuestionData(CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, None, 0, 2, 3),
            ErrorChoice(NUMBER_LINE_DOT_PLOT, 0, 3),
            (NUMBER_LINE_DOT_PLOT,),
            "There should be ____ X's above ____.",
            "There should be 3 X's above 18",
        ),
        # With a second display, a statement names its display. The displays are in their
        # order, whichever has the error.
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, BAR_GRAPH, 1, 7, 5),
            ErrorChoice(BAR_GRAPH, 2, 9),
            (PICTOGRAPH, BAR_GRAPH),
            "The row for ____ should have ____ symbols.",
            "Bar graph, because the bar for Grapes should end at 9",
        ),
        (
            FindErrorQuestionData(FRUIT_DATA, None, DOT_PLOT, PICTOGRAPH, 3, 5, 4),
            ErrorChoice(DOT_PLOT, 3, 4),
            (PICTOGRAPH, DOT_PLOT),
            "There should be ____ X's above ____.",
            "Dot plot, because there should be 4 X's above Pears",
        ),
    ],
)
def test_error_wording(
    data: FindErrorQuestionData,
    choice: ErrorChoice,
    displays: tuple[DataDisplay, ...],
    sentence: str,
    fix: str,
) -> None:
    """A display with an error: the displays shown, the sentence to complete, and a statement."""
    actual = (error_displays(data), error_sentence(data), error_fix(data, choice))
    assert actual == (displays, sentence, fix)


@pytest.mark.parametrize(
    ("dataset", "counts", "text"),
    [
        (FRUIT_DATA, (12, 5, 9, 4), "Apples: 12,  Bananas: 5,  Grapes: 9,  Pears: 4"),
        # a list's numbers, from least to greatest
        (CLASSES_DATA, (3, 0, 2, 1, 0, 1), "18, 18, 18, 20, 20, 21, 23"),
        (CLASSES_DATA, (1, 1, 1, 1, 1, 1), "18, 19, 20, 21, 22, 23"),
    ],
)
def test_counts_text(
    dataset: CategoricalData | NumericalData, counts: tuple[int, ...], text: str
) -> None:
    """A list of counts as a choice or the answer key writes it."""
    assert counts_text(dataset, counts) == text


TABLE_TO_BAR_GRAPH = SummarizeDataQuestionData(
    FRUIT_DATA, TABLE, BAR_GRAPH, (0, 1, 2, 3), ALL_FRUIT
)
TABLE_TO_PICTOGRAPH = SummarizeDataQuestionData(
    FRUIT_DATA, TABLE, PICTOGRAPH, (0, 1, 2, 3), ALL_FRUIT
)
PICTOGRAPH_TO_TABLE = SummarizeDataQuestionData(
    FRUIT_DATA, PICTOGRAPH, TABLE, (0, 1, 2, 3), ALL_FRUIT
)
BAR_GRAPH_TO_TABLE = SummarizeDataQuestionData(
    FRUIT_DATA, BAR_GRAPH, TABLE, (0, 1, 2, 3), ALL_FRUIT
)
LIST_TO_LINE = SummarizeDataQuestionData(
    CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5), (3, 0, 2, 1, 0, 1)
)


@pytest.mark.parametrize(
    ("data", "choice", "text"),
    [
        (
            TABLE_TO_BAR_GRAPH,
            DisplayChoice((5, 12, 9, 4), 2, (Swap(0, 1),)),
            "Apples and Bananas are switched",
        ),
        (
            TABLE_TO_BAR_GRAPH,
            DisplayChoice((12, 7, 9, 4), 2, (Off(1, 7),)),
            "Bananas shows 7 instead of 5",
        ),
        # two mistakes are both named
        (
            TABLE_TO_BAR_GRAPH,
            DisplayChoice((5, 12, 9, 4), 5, (Swap(0, 1), WrongScale(5))),
            "Apples and Bananas are switched, and the scale counts by 5, not by 2",
        ),
        # a wrong scale in the display shown, or in reading the given display
        (
            TABLE_TO_PICTOGRAPH,
            DisplayChoice((12, 5, 9, 4), 5, (WrongScale(5),)),
            "the key says each star = 5, not 2",
        ),
        (
            PICTOGRAPH_TO_TABLE,
            DisplayChoice((6, 3, 5, 2), 1, (WrongScale(1),)),
            "counts each star as 1",
        ),
        (
            PICTOGRAPH_TO_TABLE,
            DisplayChoice((30, 15, 25, 10), 5, (WrongScale(5),)),
            "uses a key of 5, not 2",
        ),
        (
            BAR_GRAPH_TO_TABLE,
            DisplayChoice((30, 15, 25, 10), 5, (WrongScale(5),)),
            "reads the scale as counting by 5, not by 2",
        ),
        (
            Question(ReadCountsQuestionData(FRUIT_DATA, PICTOGRAPH, ALL_FRUIT), CHOOSE_ONE).data,
            DisplayChoice((6, 3, 5, 2), 1, (WrongScale(1),)),
            "counts each star as 1",
        ),
        # counts between steps taken at the step below, likewise
        (
            TABLE_TO_PICTOGRAPH,
            DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
            "leaves out the half stars",
        ),
        (
            TABLE_TO_BAR_GRAPH,
            DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
            "each bar that ends between lines stops at the line below",
        ),
        (
            PICTOGRAPH_TO_TABLE,
            DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
            "doesn't count the half stars",
        ),
        (
            BAR_GRAPH_TO_TABLE,
            DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
            "reads each bar that ends between lines at the line below",
        ),
        # on a number line
        (
            LIST_TO_LINE,
            DisplayChoice((2, 0, 3, 1, 0, 1), 1, (Swap(0, 2),)),
            "the X's for 18 and 20 are switched",
        ),
        (
            LIST_TO_LINE,
            DisplayChoice((3, 1, 2, 1, 0, 1), 1, (Off(1, 1),)),
            "1 X above 19 instead of 0",
        ),
        (
            LIST_TO_LINE,
            DisplayChoice((2, 0, 2, 1, 0, 1), 1, (Off(0, 2),)),
            "2 X's above 18 instead of 3",
        ),
        (
            LIST_TO_LINE,
            DisplayChoice((1, 0, 1, 1, 0, 1), 1, (OneEach(),)),
            "only one X for each number in the list",
        ),
        (
            LIST_TO_LINE,
            DisplayChoice((1, 1, 1, 2, 1, 1), 1, (EveryTick(), Off(3, 2))),
            "one X above every number on the line, and 2 X's above 21 instead of 1",
        ),
        # a display that doesn't match has its own scale
        (
            DoesntMatchQuestionData(FRUIT_DATA, TABLE, SHOWN_BAR_GRAPH),
            SHOWN_BAR_GRAPH,
            "the scale counts by 10, not by 5",
        ),
    ],
)
def test_mistake(
    data: SummarizeDataQuestionData | ReadCountsQuestionData | DoesntMatchQuestionData,
    choice: DisplayChoice | ShownDisplay,
    text: str,
) -> None:
    """What the answer key says is wrong with a wrong choice."""
    assert mistake(data, choice) == text


@pytest.mark.parametrize(
    ("data", "choice", "message"),
    [
        (
            TABLE_TO_BAR_GRAPH,
            DisplayChoice(ALL_FRUIT, 2, ()),
            "The correct choice has no mistake.",
        ),
        (
            DoesntMatchQuestionData(FRUIT_DATA, TABLE, SHOWN_BAR_GRAPH),
            SHOWN_BAR_GRAPH.choice,
            "A display that doesn't match is a ShownDisplay.",
        ),
        # a frequency table and a dot plot have no scale
        (
            SummarizeDataQuestionData(FRUIT_DATA, TABLE, DOT_PLOT, (0, 1, 2, 3), ALL_FRUIT),
            DisplayChoice((30, 15, 25, 10), 5, (WrongScale(5),)),
            "Neither display has a scale.",
        ),
        (
            SummarizeDataQuestionData(FRUIT_DATA, TABLE, DOT_PLOT, (0, 1, 2, 3), ALL_FRUIT),
            DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
            "Neither display has a scale.",
        ),
    ],
)
def test_mistake_errors(
    data: SummarizeDataQuestionData | ReadCountsQuestionData | DoesntMatchQuestionData,
    choice: DisplayChoice | ShownDisplay,
    message: str,
) -> None:
    """A right choice has no mistake to describe, and a scale's mistake needs a scale."""
    with pytest.raises(ValueError) as error:
        mistake(data, choice)
    assert str(error.value) == message


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
GENERATED_ACROSS = replace(GENERATED_CANS, horizontal_bars=True)
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
        # The first draw shifts each display along, of table, tally table, pictograph, bar graph
        # and dot plot: 2 completes the table as a pictograph. The scale is the first in the
        # pictograph scales' deck, and the second draw takes 4 categories. The question picks
        # follow the person who asked.
        (
            (FRUIT,),
            (COINS,),
            [2, 4],
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
        # Three along, a bar graph, with the first of the other scales. Friends are names, with
        # no person who asked. The draw of 0.5 keeps the bars upright.
        (
            (CANS,),
            (COINS,),
            [3, 4],
            [0.5],
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
        # a draw under 0.5 turns the bars across
        (
            (CANS,),
            (COINS,),
            [3, 4],
            [0.4],
            [],
            [
                CategoricalProblemType.MORE,
                CategoricalProblemType.PAIR_MORE,
                (CategoricalProblemType.PAIR_MORE, (2, 3, 1), 5),
            ],
            discrete_data_problem(
                SummarizeDataQuestionData(GENERATED_ACROSS, TABLE, BAR_GRAPH, (0, 1), (1, 2)),
                CategoricalDataProblemData(
                    GENERATED_ACROSS, CategoricalProblemType.MORE, (1, 0), 1
                ),
                CategoricalDataProblemData(
                    GENERATED_ACROSS, CategoricalProblemType.PAIR_MORE, (2, 3, 1), 5
                ),
            ),
        ),
        # Four along, a dot plot, which becomes a number list. Each coin value is drawn 4, 2
        # and 3 times. The first two numbers' counts differ, and the draw under 0.6 makes it
        # MORE.
        (
            (FRUIT,),
            (COINS,),
            [4, 4, 2, 3],
            [0.5],
            [],
            ["Eve", NumericalProblemType.PAIR_MORE, (NumericalProblemType.PAIR_MORE, (1, 2, 5), 3)],
            GENERATED_COINS_PROBLEM,
        ),
        # 24 coins are too many, and are drawn again
        (
            (FRUIT,),
            (COINS,),
            [4, 8, 8, 8, 4, 2, 3],
            [0.5],
            [],
            ["Eve", NumericalProblemType.PAIR_MORE, (NumericalProblemType.PAIR_MORE, (1, 2, 5), 3)],
            GENERATED_COINS_PROBLEM,
        ),
        # 3 coins are too few, and are drawn again
        (
            (FRUIT,),
            (COINS,),
            [4, 1, 1, 1, 4, 2, 3],
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
            [4, 6, 0, 12],
            [0.9] * 13,
            [0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5],
            ["Eve", NumericalProblemType.AT_LEAST, (NumericalProblemType.AT_LEAST, (3,), 5)],
            GENERATED_CLASSES_PROBLEM,
        ),
        # 2 Xs on every tick is too short a stack, so the 12 numbers are drawn again
        (
            (FRUIT,),
            (CLASSES,),
            [4, 6, 0, 12, 12],
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
    """
    A one-problem sheet with every display and question: its first part, dealt first, is
    another display, then its displays, data set, blanks and two problems.
    """
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
    ("displays", "count", "drawn", "pairs"),
    [
        # Each categorical display is completed once in five problems, and never from itself.
        # The pair that would complete a dot plot completes a number line from a list instead.
        # Each categorical data set takes 3 categories, and the coins 4, 2 and 3 of each value.
        (
            SHEET_DISPLAYS,
            5,
            [1, 3, 3, 3, 4, 2, 3, 3],
            [
                (TABLE, TALLY_TABLE),
                (TALLY_TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
            ],
        ),
        (
            SHEET_DISPLAYS,
            5,
            [2, 3, 3, 4, 2, 3, 3, 3],
            [
                (TABLE, PICTOGRAPH),
                (TALLY_TABLE, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (BAR_GRAPH, TABLE),
                (DOT_PLOT, TALLY_TABLE),
            ],
        ),
        (
            SHEET_DISPLAYS,
            5,
            [3, 3, 4, 2, 3, 3, 3, 3],
            [
                (TABLE, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (PICTOGRAPH, TABLE),
                (BAR_GRAPH, TALLY_TABLE),
                (DOT_PLOT, PICTOGRAPH),
            ],
        ),
        (
            SHEET_DISPLAYS,
            5,
            [4, 4, 2, 3, 3, 3, 3, 3],
            [
                (LIST, NUMBER_LINE_DOT_PLOT),
                (TALLY_TABLE, TABLE),
                (PICTOGRAPH, TALLY_TABLE),
                (BAR_GRAPH, PICTOGRAPH),
                (DOT_PLOT, BAR_GRAPH),
            ],
        ),
        # a sixth problem starts a new round, with its own shift
        (
            SHEET_DISPLAYS,
            6,
            [1, 3, 3, 3, 4, 2, 3, 3, 2, 3],
            [
                (TABLE, TALLY_TABLE),
                (TALLY_TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
                (TABLE, PICTOGRAPH),
            ],
        ),
        (
            SHEET_DISPLAYS,
            10,
            [1, 3, 3, 3, 4, 2, 3, 3, 3, 3, 4, 2, 3, 3, 3, 3],
            [
                (TABLE, TALLY_TABLE),
                (TALLY_TABLE, PICTOGRAPH),
                (PICTOGRAPH, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (DOT_PLOT, TABLE),
                (TABLE, BAR_GRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (PICTOGRAPH, TABLE),
                (BAR_GRAPH, TALLY_TABLE),
                (DOT_PLOT, PICTOGRAPH),
            ],
        ),
        # Without a dot plot, a list joins each round at the place of the second draw, here 1.
        (
            (TABLE, PICTOGRAPH, BAR_GRAPH, LIST),
            4,
            [1, 1, 3, 4, 2, 3, 3, 3],
            [
                (TABLE, PICTOGRAPH),
                (LIST, NUMBER_LINE_DOT_PLOT),
                (PICTOGRAPH, BAR_GRAPH),
                (BAR_GRAPH, TABLE),
            ],
        ),
        # with one categorical display, every pair is a list's
        (
            (PICTOGRAPH, LIST),
            2,
            [4, 2, 3, 4, 2, 3],
            [(LIST, NUMBER_LINE_DOT_PLOT), (LIST, NUMBER_LINE_DOT_PLOT)],
        ),
    ],
)
def test_generate_discrete_data_problems_rotates_the_displays(
    displays: tuple[DataDisplay, ...],
    count: int,
    drawn: list[int],
    pairs: list[tuple[DataDisplay, DataDisplay]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each round, the categorical displays are shuffled (here, kept in their order: table, tally
    table, pictograph, bar graph, dot plot), and the round's first draw is how far along each
    one's display to complete is. The sheet asks only for another display.
    """
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (COINS,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, [0.5] * count)
    choose_last(monkeypatch)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    problems = generate_discrete_data_problems(count, displays, [ANOTHER_DISPLAY])

    assert [(problem.given, problem.summarize.data.target) for problem in problems] == pairs


@pytest.mark.parametrize(
    ("displays", "scales", "pictograph_scales", "sample", "scales_and_counts"),
    [
        # A pictograph's scales are dealt from their own deck, so they differ until each has
        # been used.
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (2, 5),
            sample_first,
            [(2, (1, 2, 3, 4)), (5, (5, 10, 15, 20)), (2, (1, 2, 3, 4))],
        ),
        # An even scale allows half a symbol, an odd one a whole symbol, up to 8 symbols' worth.
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (2,),
            sample_first,
            [(2, (1, 2, 3, 4)), (2, (1, 2, 3, 4)), (2, (1, 2, 3, 4))],
        ),
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (2,),
            sample_last,
            [(2, (13, 14, 15, 16)), (2, (13, 14, 15, 16)), (2, (13, 14, 15, 16))],
        ),
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (5,),
            sample_first,
            [(5, (5, 10, 15, 20)), (5, (5, 10, 15, 20)), (5, (5, 10, 15, 20))],
        ),
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (5,),
            sample_last,
            [(5, (25, 30, 35, 40)), (5, (25, 30, 35, 40)), (5, (25, 30, 35, 40))],
        ),
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (10,),
            sample_first,
            [(10, (5, 10, 15, 20)), (10, (5, 10, 15, 20)), (10, (5, 10, 15, 20))],
        ),
        (
            (TABLE, PICTOGRAPH),
            (20,),
            (10,),
            sample_last,
            [(10, (65, 70, 75, 80)), (10, (65, 70, 75, 80)), (10, (65, 70, 75, 80))],
        ),
        # A bar graph without a pictograph takes the other scales, by the same rule.
        (
            (TABLE, BAR_GRAPH),
            (20,),
            (2,),
            sample_first,
            [(20, (10, 20, 30, 40)), (20, (10, 20, 30, 40)), (20, (10, 20, 30, 40))],
        ),
        (
            (TABLE, BAR_GRAPH),
            (3,),
            (2,),
            sample_last,
            [(3, (15, 18, 21, 24)), (3, (15, 18, 21, 24)), (3, (15, 18, 21, 24))],
        ),
        # A data set in a dot plot has a scale of 2 and counts of 1 to 10, whatever the decks.
        (
            (TABLE, DOT_PLOT),
            (5,),
            (5,),
            sample_first,
            [(2, (1, 2, 3, 4)), (2, (1, 2, 3, 4)), (2, (1, 2, 3, 4))],
        ),
        (
            (TABLE, DOT_PLOT),
            (5,),
            (5,),
            sample_last,
            [(2, (7, 8, 9, 10)), (2, (7, 8, 9, 10)), (2, (7, 8, 9, 10))],
        ),
        # Tally marks with neither a pictograph nor a bar graph: a scale of 1, counts of 1 to 20.
        (
            (TABLE, TALLY_TABLE),
            (5,),
            (5,),
            sample_last,
            [(1, (17, 18, 19, 20)), (1, (17, 18, 19, 20)), (1, (17, 18, 19, 20))],
        ),
        # With a pictograph or bar graph, tally marks keep the counts to 40.
        (
            (TALLY_TABLE, PICTOGRAPH),
            (20,),
            (10,),
            sample_last,
            [(10, (25, 30, 35, 40)), (10, (25, 30, 35, 40)), (10, (25, 30, 35, 40))],
        ),
        (
            (TALLY_TABLE, BAR_GRAPH),
            (10,),
            (2,),
            sample_last,
            [(10, (25, 30, 35, 40)), (10, (25, 30, 35, 40)), (10, (25, 30, 35, 40))],
        ),
    ],
)
def test_generate_discrete_data_problems_fits_counts_to_the_scale(
    displays: tuple[DataDisplay, DataDisplay],
    scales: tuple[int, ...],
    pictograph_scales: tuple[int, ...],
    sample: Callable[[pytest.MonkeyPatch], None],
    scales_and_counts: list[tuple[int, tuple[int, ...]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The scale and counts of the data sets on a sheet of three problems from two displays, each
    completing one in the other in turn, with 4 categories. ``sample`` takes the smallest counts
    allowed, or the largest.
    """
    monkeypatch.setattr("core.discrete_data.generator.SCALES", scales)
    monkeypatch.setattr("core.discrete_data.generator.PICTOGRAPH_SCALES", pictograph_scales)
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    # each round's shift, of 1, and each data set's 4 categories
    randint_returns(monkeypatch, [1, 4, 4, 1, 4])
    random_returns(monkeypatch, [0.5] * 3)
    choose_last(monkeypatch)
    sample(monkeypatch)
    reverse_shuffle(monkeypatch)

    problems = generate_discrete_data_problems(3, displays, [ANOTHER_DISPLAY])

    datasets = [problem.dataset for problem in problems]
    assert [
        (dataset.scale, dataset.counts)
        for dataset in datasets
        if isinstance(dataset, CategoricalData)
    ] == scales_and_counts


@pytest.mark.parametrize(
    ("displays", "parts"),
    [
        # a table shows its counts as numbers, so it can only give the data for problems
        ((TABLE,), (ONE_STEP, TWO_STEP)),
        # one kind of display: nothing to complete, but its counts to read, and pictographs of
        # several scales that don't all match
        ((PICTOGRAPH,), (READ_COUNTS, FIND_ERROR, DOESNT_MATCH, ONE_STEP, TWO_STEP)),
        # two kinds, but tally marks alone don't make four different displays
        ((TABLE, TALLY_TABLE), (ANOTHER_DISPLAY, READ_COUNTS, FIND_ERROR, ONE_STEP, TWO_STEP)),
        ((DOT_PLOT, TALLY_TABLE), (ANOTHER_DISPLAY, READ_COUNTS, FIND_ERROR, ONE_STEP, TWO_STEP)),
        # a list is completed, read and checked as a number-line dot plot
        ((LIST,), (ANOTHER_DISPLAY, READ_COUNTS, FIND_ERROR, ONE_STEP, TWO_STEP)),
        (SHEET_DISPLAYS, tuple(DiscreteDataPart)),
    ],
)
def test_available_parts(
    displays: tuple[DataDisplay, ...], parts: tuple[DiscreteDataPart, ...]
) -> None:
    """The questions a set of displays can make, in the order of ``DiscreteDataPart``."""
    assert available_parts(displays) == parts


@pytest.mark.parametrize(
    ("displays", "parts", "distinct_answers", "message"),
    [
        (SHEET_DISPLAYS, (), False, "Ask at least one part."),
        (
            (),
            (ONE_STEP,),
            False,
            "Displays must be from table, tally_table, pictograph, bar_graph, dot_plot, list.",
        ),
        # a number-line dot plot is how a list is completed, not a display to tick
        (
            (NUMBER_LINE_DOT_PLOT,),
            (ONE_STEP,),
            False,
            "Displays must be from table, tally_table, pictograph, bar_graph, dot_plot, list.",
        ),
        ((TABLE,), (READ_COUNTS,), False, "The displays can't make read_counts."),
        (
            (TABLE,),
            (ANOTHER_DISPLAY, READ_COUNTS, ONE_STEP),
            False,
            "The displays can't make another_display, read_counts.",
        ),
        (
            SHEET_DISPLAYS,
            (READ_COUNTS, FIND_ERROR),
            True,
            "Distinct answers need a one-step or two-step problem.",
        ),
    ],
)
def test_generate_discrete_data_problems_errors(
    displays: tuple[DataDisplay, ...],
    parts: tuple[DiscreteDataPart, ...],
    distinct_answers: bool,
    message: str,
) -> None:
    """Options that can't make a sheet are refused before anything is drawn."""
    with pytest.raises(ValueError) as error:
        generate_discrete_data_problems(1, displays, parts, distinct_answers=distinct_answers)
    assert str(error.value) == message


def test_generate_discrete_data_problems_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    A sheet of different answers that can't be found is refused after ``SHEET_ATTEMPTS`` starts,
    each problem drawn at most ``PROBLEM_ATTEMPTS`` times: pictographs that don't all match have
    10 two-step answers, too few for 12 problems.
    """
    monkeypatch.setattr("core.discrete_data.generator.PROBLEM_ATTEMPTS", 5)
    with pytest.raises(ValueError) as error:
        generate_discrete_data_problems(
            12, (PICTOGRAPH,), (DOESNT_MATCH, TWO_STEP), distinct_answers=True
        )
    assert str(error.value) == (
        "No sheet has a different answer for every problem with those displays."
    )


@pytest.mark.parametrize(
    ("displays", "parts", "most"),
    [
        # Pictographs that don't all match: their counts are multiples of 6, and the one-step
        # answers 6 to 42, 7 of them.
        ((PICTOGRAPH,), (DOESNT_MATCH, ONE_STEP), 7),
        # the two-step answers 6 to 60
        ((PICTOGRAPH,), (DOESNT_MATCH, TWO_STEP), 10),
        # Both from one data set: at most half the 10 answers between them, and one fewer, so a
        # sheet is found every time.
        ((PICTOGRAPH,), (DOESNT_MATCH, ONE_STEP, TWO_STEP), 4),
        # with another first part dealt in turn, half the problems are another kind
        ((PICTOGRAPH,), (READ_COUNTS, DOESNT_MATCH, ONE_STEP, TWO_STEP), 8),
        # only displays that don't all match limit the answers
        ((PICTOGRAPH,), (READ_COUNTS, ONE_STEP, TWO_STEP), None),
        ((PICTOGRAPH,), (DOESNT_MATCH,), None),
    ],
)
def test_most_tile_problems(
    displays: tuple[DataDisplay, ...], parts: tuple[DiscreteDataPart, ...], most: int | None
) -> None:
    """The most problems a tiles sheet can have, each answer different, or ``None`` for any."""
    assert most_tile_problems(displays, parts) == most


@pytest.mark.parametrize(
    ("displays", "part", "multiple_choice", "drawn", "randoms", "picks", "given", "data"),
    [
        # the counts read from a display that takes reading
        (
            (PICTOGRAPH,),
            READ_COUNTS,
            False,
            [4],
            [],
            ["Eve"],
            PICTOGRAPH,
            ReadCountsQuestionData(GENERATED_FRUIT, PICTOGRAPH, (1, 2, 3, 4)),
        ),
        # a list's numbers read from its number line, from least to greatest
        (
            (LIST,),
            READ_COUNTS,
            False,
            [4, 2, 3],
            [],
            ["Eve"],
            NUMBER_LINE_DOT_PLOT,
            ReadCountsQuestionData(
                GENERATED_COINS, NUMBER_LINE_DOT_PLOT, (5, 5, 5, 5, 10, 10, 25, 25, 25)
            ),
        ),
        # An error in a bar graph, its data in a table: bananas' 2 shown a scale's step too high.
        # The draw of 0.5 keeps the bars upright.
        (
            (TABLE, BAR_GRAPH),
            FIND_ERROR,
            False,
            [4],
            [0.5],
            ["Eve", (1, 4)],
            TABLE,
            FindErrorQuestionData(GENERATED_FRUIT, TABLE, BAR_GRAPH, None, 1, 4, 2),
        ),
        # without a table, the introduction states the data
        (
            (BAR_GRAPH,),
            FIND_ERROR,
            False,
            [4],
            [0.5],
            ["Eve", (1, 4)],
            None,
            FindErrorQuestionData(GENERATED_FRUIT, None, BAR_GRAPH, None, 1, 4, 2),
        ),
        # a list's error is in its number line: 25's 3 Xs shown as 4
        (
            (LIST,),
            FIND_ERROR,
            False,
            [4, 2, 3],
            [],
            ["Eve", (5, 4)],
            LIST,
            FindErrorQuestionData(GENERATED_COINS, LIST, NUMBER_LINE_DOT_PLOT, None, 5, 4, 3),
        ),
        # With multiple choice, a second display of another kind beside it: the pictograph is
        # first in the deck, and the bar graph is picked. Its choices take the last pick, a
        # second category, and the draws of 0.5.
        (
            (TABLE, PICTOGRAPH, BAR_GRAPH),
            FIND_ERROR,
            True,
            [4],
            [0.5] * 4,
            [BAR_GRAPH, "Eve", (1, 4), 2],
            TABLE,
            FindErrorQuestionData(GENERATED_FRUIT, TABLE, PICTOGRAPH, BAR_GRAPH, 1, 4, 2),
        ),
    ],
)
def test_generate_discrete_data_problems_asks_the_first_part(
    displays: tuple[DataDisplay, ...],
    part: DiscreteDataPart,
    multiple_choice: bool,
    drawn: list[int],
    randoms: list[float],
    picks: list[object],
    given: DataDisplay | None,
    data: SummarizeData,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A one-problem sheet asking one first part: its given display and the question's data."""
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (COINS,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    choice_returns(monkeypatch, picks)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    (problem,) = generate_discrete_data_problems(
        1, displays, [part], multiple_choice=multiple_choice
    )

    assert (problem.given, problem.summarize.data) == (given, data)


# A topic whose numbers add up, asking for a missing one
ADDING_CLASSES = MISSING_CLASSES_DATA.topic
# 15 once, 16 three times, 18 and 19 once, reversed
SHORT_DATA = NumericalData(
    topic=ADDING_CLASSES, values=(19, 18, 16, 16, 16, 15), ticks=(15, 16, 17, 18, 19), person="Eve"
)
# GENERATED_CLASSES's numbers, for the adding topic
LONG_DATA = replace(GENERATED_CLASSES, topic=ADDING_CLASSES)


@pytest.mark.parametrize(
    ("parts", "drawn", "randoms", "ranges", "picks", "expected"),
    [
        # A draw of 0 of 6 two-step kinds asks for a missing number, from a short list: 5 ticks
        # and 6 numbers. The missing number is any the line could hold, here 17.
        (
            (ONE_STEP, TWO_STEP),
            [5, 0, 6],
            [0.9] * 7,
            [0, 0, 1, 1, 1, 3, 4],
            ["Eve", 17],
            DiscreteDataProblem(
                dataset=SHORT_DATA,
                given=LIST,
                summarize=None,
                one_step=Question(
                    NumericalDataProblemData(
                        SHORT_DATA, NumericalProblemType.PAIR_TOTAL, (0, 1), 4
                    ),
                    FreeResponse(),
                ),
                two_step=Question(
                    NumericalDataProblemData(
                        SHORT_DATA, NumericalProblemType.MISSING_VALUE, (), 17, 117
                    ),
                    FreeResponse(),
                ),
            ),
        ),
        # any other draw asks another kind, from a list of the usual length
        (
            (ONE_STEP, TWO_STEP),
            [6, 0, 12],
            [0.9] * 13,
            [1, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5],
            ["Eve", NumericalProblemType.AT_LEAST, (NumericalProblemType.AT_LEAST, (3,), 5)],
            DiscreteDataProblem(
                dataset=LONG_DATA,
                given=LIST,
                summarize=None,
                one_step=Question(
                    NumericalDataProblemData(LONG_DATA, NumericalProblemType.PAIR_TOTAL, (0, 1), 5),
                    FreeResponse(),
                ),
                two_step=Question(
                    NumericalDataProblemData(LONG_DATA, NumericalProblemType.AT_LEAST, (3,), 5),
                    FreeResponse(),
                ),
            ),
        ),
        # without a two-step problem, nothing is drawn for it
        (
            (ONE_STEP,),
            [6, 0, 12],
            [0.9] * 13,
            [0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5],
            ["Eve"],
            DiscreteDataProblem(
                dataset=LONG_DATA,
                given=LIST,
                summarize=None,
                one_step=Question(
                    NumericalDataProblemData(LONG_DATA, NumericalProblemType.PAIR_TOTAL, (0, 1), 5),
                    FreeResponse(),
                ),
                two_step=None,
            ),
        ),
    ],
)
def test_generate_discrete_data_problems_draws_a_missing_number(
    parts: tuple[DiscreteDataPart, ...],
    drawn: list[int],
    randoms: list[float],
    ranges: list[int],
    picks: list[object],
    expected: DiscreteDataProblem,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A list for a topic whose numbers add up asks for a missing number as often as each other
    two-step kind, drawn before the list. A one-problem sheet of a list and its problems.
    """
    monkeypatch.setattr("core.discrete_data.generator.NUMBER_LIST_TOPICS", (ADDING_CLASSES,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, drawn)
    random_returns(monkeypatch, randoms)
    randrange_returns(monkeypatch, ranges)
    choice_returns(monkeypatch, picks)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    assert generate_discrete_data_problems(1, (LIST,), parts) == [expected]


def test_generate_discrete_data_problems_draws_new_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    With distinct answers, a problem whose answer is already on the sheet is drawn again: the
    second problem's first draw, MORE, repeats the first's answer of 1, and its second,
    PAIR_TOTAL, gives 3. Each data set has 3 categories, the smallest counts.
    """
    monkeypatch.setattr("core.discrete_data.generator.CATEGORY_TOPICS", (FRUIT,))
    monkeypatch.setattr("core.discrete_data.generator.NAMES", NAMES)
    randint_returns(monkeypatch, [3, 3, 3])
    choice_returns(
        monkeypatch,
        [
            "Eve",
            CategoricalProblemType.MORE,
            "Eve",
            CategoricalProblemType.MORE,
            "Eve",
            CategoricalProblemType.PAIR_TOTAL,
        ],
    )
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    problems = generate_discrete_data_problems(
        2, (TABLE, PICTOGRAPH), (ONE_STEP,), distinct_answers=True
    )

    assert [
        [question.data.answer for question in problem.word_problems] for problem in problems
    ] == [
        [1],
        [3],
    ]
