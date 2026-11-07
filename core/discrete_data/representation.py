"""
Wording of data-set questions: the displays' names, each data set's introduction, title and
labels, the questions, and the work the answer key shows.

The renderer gets every word about a data set's topic from here, never from the topic itself, so
that how a data set holds its topic can change without touching the renderer.
"""

from collections.abc import Sequence
from typing import assert_never

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
from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic

_MINUS = "\N{MINUS SIGN}"

DISPLAY_NAMES = {
    DataDisplay.TABLE: "frequency table",
    DataDisplay.PICTOGRAPH: "pictograph",
    DataDisplay.BAR_GRAPH: "bar graph",
    DataDisplay.DOT_PLOT: "dot plot",
    DataDisplay.LIST: "list",
    DataDisplay.NUMBER_LINE_DOT_PLOT: "dot plot",
}
INSTRUCTION = "Read the data. Complete the second graph or table, then solve the problems."
FRIENDS_CATEGORY_HEADER = "Name"  # heading a table of friends, whose categories are names

# The problems about a survey, where {a}, {b} and {c} are the problem's categories
_SURVEY_PROBLEMS = {
    CategoricalProblemType.MORE: "How many more students chose {a} than chose {b}?",
    CategoricalProblemType.FEWER: "How many fewer students chose {b} than chose {a}?",
    CategoricalProblemType.PAIR_TOTAL: "How many students chose {a} or {b}?",
    CategoricalProblemType.PAIR_MORE: "How many more students chose {a} or {b} than chose {c}?",
    CategoricalProblemType.MORE_THAN_PAIR: (
        "How many more students chose {a} than chose {b} or {c}?"
    ),
    CategoricalProblemType.ALL_BUT: "How many students did NOT choose {a}?",
    CategoricalProblemType.ALL: "How many students answered the question in all?",
}
# The problems about friends, where {a}, {b} and {c} are the problem's friends, and {unit},
# {verb} and {verb_past} come from the topic
_FRIENDS_PROBLEMS = {
    CategoricalProblemType.MORE: "How many more {unit} did {a} {verb} than {b}?",
    CategoricalProblemType.FEWER: "How many fewer {unit} did {b} {verb} than {a}?",
    CategoricalProblemType.PAIR_TOTAL: "How many {unit} did {a} and {b} {verb} in all?",
    CategoricalProblemType.PAIR_MORE: (
        "How many more {unit} did {a} and {b} {verb} together than {c}?"
    ),
    CategoricalProblemType.MORE_THAN_PAIR: (
        "How many more {unit} did {a} {verb} than {b} and {c} together?"
    ),
    CategoricalProblemType.ALL_BUT: "How many {unit} did everyone except {a} {verb} in all?",
    CategoricalProblemType.ALL: "How many {unit} were {verb_past} in all?",
}


def intro(data: SummarizeDataQuestionData) -> str:
    """Return the problem's opening text, which introduces the data set and its given display."""
    dataset = data.dataset
    if isinstance(dataset, NumericalData):
        return dataset.topic.intro.format(person=dataset.person)
    given = DISPLAY_NAMES[data.given]
    topic = dataset.topic
    match topic:
        case SurveyTopic():
            return (
                f"{dataset.person} asked some students to name their favorite {topic.favorite}. "
                f"The {given} shows the results."
            )
        case FriendsTopic():
            return (
                f"{topic.intro} The {given} shows how many {topic.unit} each friend "
                f"{topic.verb_past}."
            )
        case _:
            assert_never(topic)


def stem(
    data: SummarizeDataQuestionData | CategoricalDataProblemData | NumericalDataProblemData,
) -> str:
    """
    Return the question's text: for completing a display, "Use the frequency table to complete
    the bar graph.", and for a problem, its question.
    """
    match data:
        case SummarizeDataQuestionData():
            return _summarize_stem(data)
        case CategoricalDataProblemData():
            return _categorical_stem(data)
        case NumericalDataProblemData():
            return _numerical_stem(data)
        case _:
            assert_never(data)


def work(data: CategoricalDataProblemData | NumericalDataProblemData) -> str:
    """
    Return the arithmetic that solves the problem, as the answer key shows it: "12 - 5 = 7", or
    for two steps, "4 + 6 = 10,  10 - 3 = 7".
    """
    match data:
        case CategoricalDataProblemData():
            return _categorical_work(data)
        case NumericalDataProblemData():
            return _numerical_work(data)
        case _:
            assert_never(data)


def blank_counts(data: SummarizeDataQuestionData) -> str:
    """
    Return the counts left blank, as the answer key shows them: "Apples: 12,  Grapes: 3", or on
    a number line, "3 at 20,  1 at 21", leaving out the numbers with no Xs.
    """
    names = labels(data.dataset)
    blanks = zip(data.blanks, data.answer, strict=True)
    if isinstance(data.dataset, NumericalData):
        return ",  ".join(f"{count} at {names[index]}" for index, count in blanks if count)
    return ",  ".join(f"{names[index]}: {count}" for index, count in blanks)


def display_title(dataset: CategoricalData | NumericalData) -> str:
    """Return the title above each display of the data set: "Favorite Fruit"."""
    return dataset.topic.title


def labels(dataset: CategoricalData | NumericalData) -> tuple[str, ...]:
    """
    Return the labels of a display's categories or ticks: a survey's categories capitalized
    ("Apples"), the friends' names, or a number line's numbers.
    """
    if isinstance(dataset, NumericalData):
        return tuple(str(tick) for tick in dataset.ticks)
    if isinstance(dataset.topic, SurveyTopic):
        return tuple(category.capitalize() for category in dataset.categories)
    return dataset.categories


def category_header(dataset: CategoricalData) -> str:
    """Return the heading of a table's categories: the survey's ("Fruit"), or "Name"."""
    topic = dataset.topic
    match topic:
        case SurveyTopic():
            return topic.category_header
        case FriendsTopic():
            return FRIENDS_CATEGORY_HEADER
        case _:
            assert_never(topic)


def count_header(dataset: CategoricalData) -> str:
    """
    Return the heading of a table's counts, which also labels a bar graph's axis: "Number of
    Students".
    """
    return f"Number of {_units(dataset)[1].capitalize()}"


def pictograph_key(dataset: CategoricalData) -> str:
    """Return what one pictograph symbol is worth, written after it in the key: "= 5 students"."""
    return f"= {_count_text(dataset, dataset.scale)}"


def dot_plot_key(dataset: CategoricalData | NumericalData) -> str:
    """Return what one X in a dot plot stands for: "Each X = 1 student"."""
    return f"Each X = {_count_text(dataset, 1)}"


def axis_title(dataset: NumericalData) -> str:
    """Return the title under a number line: "Number of Students"."""
    return dataset.topic.axis_title


def _summarize_stem(data: SummarizeDataQuestionData) -> str:
    text = f"Use the {DISPLAY_NAMES[data.given]} to complete the {DISPLAY_NAMES[data.target]}."
    if data.given is DataDisplay.LIST:
        text += " Draw one X for each number in the list."
    return text


def _categorical_stem(data: CategoricalDataProblemData) -> str:
    dataset = data.dataset
    names = dict(zip("abc", (dataset.categories[index] for index in data.categories), strict=False))
    topic = dataset.topic
    match topic:
        case SurveyTopic():
            return _SURVEY_PROBLEMS[data.problem_type].format(**names)
        case FriendsTopic():
            return _FRIENDS_PROBLEMS[data.problem_type].format(
                **names, unit=topic.unit, verb=topic.verb, verb_past=topic.verb_past
            )
        case _:
            assert_never(topic)


def _numerical_stem(data: NumericalDataProblemData) -> str:
    topic = data.dataset.topic
    ticks = [data.dataset.ticks[index] for index in data.tick_indexes]
    problem_type = data.problem_type
    match problem_type:
        case NumericalProblemType.MORE:
            larger = _phrase(topic, _value_text(topic, ticks[0]))
            smaller = _phrase(topic, _value_text(topic, ticks[1]))
            return f"How many more {topic.unit} {larger} than {smaller}?"
        case NumericalProblemType.PAIR_TOTAL:
            pair = _phrase(topic, f"{ticks[0]} or {ticks[1]} {topic.amount_plural}")
            return f"How many {topic.unit} {pair}?"
        case NumericalProblemType.PAIR_MORE:
            pair = _phrase(topic, f"{ticks[0]} or {ticks[1]} {topic.amount_plural}")
            third = _phrase(topic, _value_text(topic, ticks[2]))
            return f"How many more {topic.unit} {pair} than {third}?"
        case NumericalProblemType.AT_LEAST:
            at_least = _phrase(topic, f"{ticks[0]} or more {topic.amount_plural}")
            return f"How many {topic.unit} {at_least}?"
        case NumericalProblemType.AT_MOST:
            at_most = _phrase(topic, f"{ticks[0]} or fewer {topic.amount_plural}")
            return f"How many {topic.unit} {at_most}?"
        case _:
            assert_never(problem_type)


def _categorical_work(data: CategoricalDataProblemData) -> str:
    counts = data.dataset.counts
    named = [counts[index] for index in data.categories]
    problem_type = data.problem_type
    match problem_type:
        case CategoricalProblemType.MORE | CategoricalProblemType.FEWER:
            return _difference_text(named[0], named[1])
        case CategoricalProblemType.PAIR_TOTAL:
            return _sum_text(named)
        case CategoricalProblemType.PAIR_MORE:
            return _pair_more_text(named)
        case CategoricalProblemType.MORE_THAN_PAIR:
            return f"{_sum_text(named[1:])},  {_difference_text(named[0], named[1] + named[2])}"
        case CategoricalProblemType.ALL_BUT:
            return _sum_text(
                [count for index, count in enumerate(counts) if index not in data.categories]
            )
        case CategoricalProblemType.ALL:
            return _sum_text(counts)
        case _:
            assert_never(problem_type)


def _numerical_work(data: NumericalDataProblemData) -> str:
    counts = data.dataset.counts
    named = [counts[index] for index in data.tick_indexes]
    problem_type = data.problem_type
    match problem_type:
        case NumericalProblemType.MORE:
            return _difference_text(named[0], named[1])
        case NumericalProblemType.PAIR_TOTAL:
            return _sum_text(named)
        case NumericalProblemType.PAIR_MORE:
            return _pair_more_text(named)
        case NumericalProblemType.AT_LEAST:
            threshold = data.tick_indexes[0]
            return _sum_text([count for count in counts[threshold:] if count])
        case NumericalProblemType.AT_MOST:
            threshold = data.tick_indexes[0]
            return _sum_text([count for count in counts[: threshold + 1] if count])
        case _:
            assert_never(problem_type)


def _units(dataset: CategoricalData | NumericalData) -> tuple[str, str]:
    """Return what the data set counts, singular and plural: ("student", "students")."""
    topic = dataset.topic
    if isinstance(topic, SurveyTopic):
        return "student", "students"
    return topic.unit_singular, topic.unit


def _count_text(dataset: CategoricalData | NumericalData, count: int) -> str:
    """Return ``count`` with what the data set counts: "5 students", "1 class"."""
    singular, plural = _units(dataset)
    return f"{count} {singular if count == 1 else plural}"


def _value_text(topic: NumberListTopic, value: int) -> str:
    """Return a number in the list with its amount: "20 students", "1 cent"."""
    return f"{value} {topic.amount_singular if value == 1 else topic.amount_plural}"


def _phrase(topic: NumberListTopic, amount: str) -> str:
    """Return the topic's phrase for ``amount``: "have 20 students"."""
    return topic.phrase.format(amount=amount)


def _sum_text(numbers: Sequence[int]) -> str:
    return f"{' + '.join(map(str, numbers))} = {sum(numbers)}"


def _difference_text(larger: int, smaller: int) -> str:
    return f"{larger} {_MINUS} {smaller} = {larger - smaller}"


def _pair_more_text(named: Sequence[int]) -> str:
    """Return the work for a pair's total less a third: "4 + 6 = 10,  10 - 3 = 7"."""
    return f"{_sum_text(named[:2])},  {_difference_text(named[0] + named[1], named[2])}"
