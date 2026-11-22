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
    DiscreteDataProblem,
    DisplayChoice,
    DisplayMistake,
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
from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from core.question import MultipleChoice, Question

_MINUS = "\N{MINUS SIGN}"

DISPLAY_NAMES = {
    DataDisplay.TABLE: "frequency table",
    DataDisplay.TALLY_TABLE: "tally table",
    DataDisplay.PICTOGRAPH: "pictograph",
    DataDisplay.BAR_GRAPH: "bar graph",
    DataDisplay.DOT_PLOT: "dot plot",
    DataDisplay.LIST: "list",
    DataDisplay.NUMBER_LINE_DOT_PLOT: "dot plot",
}
FRIENDS_CATEGORY_HEADER = "Name"  # heading a table of friends, whose categories are names
NUMBER_WORDS = {3: "Three", 4: "Four", 5: "Five", 6: "Six"}  # how many friends, in words
BLANK_LINE = "____"  # where a student writes in a sentence to complete
# Sentences that fix an error, for each display: {name} is the category or number in error,
# {count} its right count, and for a pictograph, {symbols} its symbols
_FIXES = {
    DataDisplay.DOT_PLOT: "there should be {count} X's above {name}",
    DataDisplay.NUMBER_LINE_DOT_PLOT: "there should be {count} X's above {name}",
    DataDisplay.BAR_GRAPH: "the bar for {name} should end at {count}",
    DataDisplay.PICTOGRAPH: "the row for {name} should have {symbols} symbols",
    DataDisplay.TALLY_TABLE: "the row for {name} should have {count} tally marks",
}

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


def instruction(problems: Sequence[DiscreteDataProblem]) -> str:
    """
    Return the sheet's instruction for ``problems``: "Read the data. Complete the second graph or
    table, then solve the problems." when every problem completes a display, and likewise for
    choosing one, or for problems alone; otherwise "Read the data, then answer the questions."
    """
    counts = {len(problem.word_problems) for problem in problems}
    solve = "solve the problem" if counts == {1} else "solve the problems"
    tasks = {_task(problem) for problem in problems}
    if tasks == {None}:
        return f"Read the data, then {solve}."
    if len(tasks) > 1 or None in tasks or "" in tasks:
        return "Read the data, then answer the questions."
    (task,) = tasks
    return f"Read the data. {task}, then {solve}." if counts != {0} else f"Read the data. {task}."


def tiles_note(problems: Sequence[DiscreteDataProblem]) -> str | None:
    """
    Return the line under a self-check tiles sheet's instruction saying which parts go on the
    tiles: "Answer part a on the sheet. Parts b and c go on the tiles." when the problems have a
    first part, which then every problem has, or ``None`` when every part goes on a tile.
    """
    if all(problem.summarize is None for problem in problems):
        return None
    if max(len(problem.word_problems) for problem in problems) == 1:
        return "Answer part a on the sheet. Part b goes on the tiles."
    return "Answer part a on the sheet. Parts b and c go on the tiles."


def _task(problem: DiscreteDataProblem) -> str | None:
    """Return what a problem's first part asks of a display to complete or choose, ``None``
    without a first part, or an empty string for any other first part."""
    summarize = problem.summarize
    if summarize is None:
        return None
    if not isinstance(summarize.data, SummarizeDataQuestionData):
        return ""
    if isinstance(summarize.response, MultipleChoice):
        return "Choose the graph or table that shows the same data"
    return "Complete the second graph or table"


def intro(dataset: CategoricalData | NumericalData, given: DataDisplay | None) -> str:
    """
    Return the problem's opening text, which introduces the data set and its ``given`` display,
    or with none, states its counts.
    """
    if isinstance(dataset, NumericalData):
        return dataset.topic.intro.format(person=dataset.person)
    topic = dataset.topic
    names = labels(dataset)
    match topic:
        case SurveyTopic():
            opening = (
                f"{dataset.person} asked some students to name their favorite {topic.favorite}."
            )
            stated = _listed(
                [
                    f"{count} chose {category}"
                    for count, category in zip(dataset.counts, dataset.categories, strict=True)
                ]
            )
            shows = "shows the results"
        case FriendsTopic():
            opening = topic.intro.format(count=NUMBER_WORDS[len(dataset.categories)])
            stated = _listed(
                [
                    f"{name} {topic.verb_past} {count} {topic.unit}"
                    for name, count in zip(names, dataset.counts, strict=True)
                ]
            )
            shows = f"shows how many {topic.unit} each friend {topic.verb_past}"
        case _:
            assert_never(topic)
    if given is None:
        return f"{opening} {stated[0].upper()}{stated[1:]}."
    return f"{opening} The {DISPLAY_NAMES[given]} {shows}."


def choice_stem(data: SummarizeDataQuestionData) -> str:
    """Return the question asking for the display to choose: "Which bar graph shows the same
    data?"."""
    return f"Which {DISPLAY_NAMES[data.target]} shows the same data?"


def summarize_stem(question: Question[SummarizeData, SummarizeResponse]) -> str:
    """
    Return the text of a problem's first question: "Use the frequency table to complete the bar
    graph.", "Which list matches the data in the pictograph?", "A dot plot of the data has one
    mistake. Complete the sentence to fix it.", "Which one does NOT show the data in the
    frequency table?".
    """
    data = question.data
    choose = isinstance(question.response, MultipleChoice)
    match data:
        case SummarizeDataQuestionData():
            return choice_stem(data) if choose else _summarize_stem(data)
        case ReadCountsQuestionData():
            return _read_counts_stem(data, choose)
        case FindErrorQuestionData():
            return _find_error_stem(data, choose)
        case DoesntMatchQuestionData():
            if data.source is None:
                return "Which one does NOT show these data?"
            return f"Which one does NOT show the data in the {DISPLAY_NAMES[data.source]}?"
        case _:
            assert_never(data)


def _read_counts_stem(data: ReadCountsQuestionData, choose: bool) -> str:
    dataset = data.dataset
    given = DISPLAY_NAMES[data.given]
    if isinstance(dataset, NumericalData):
        if choose:
            return f"Which list of numbers does the {given} show?"
        return f"Write the numbers the {given} shows, from least to greatest."
    if choose:
        return f"Which list matches the data in the {given}?"
    topic = dataset.topic
    match topic:
        case SurveyTopic():
            return f"Use the {given} to write how many students chose each {topic.favorite}."
        case FriendsTopic():
            return f"Use the {given} to write how many {topic.unit} each friend {topic.verb_past}."
        case _:
            assert_never(topic)


def _find_error_stem(data: FindErrorQuestionData, choose: bool) -> str:
    wrong = DISPLAY_NAMES[data.wrong]
    if not choose:
        return f"A {wrong} of the data has one mistake. Complete the sentence to fix it."
    if data.other is None:
        return f"A {wrong} of the data has one mistake. Which sentence fixes it?"
    first, second = (DISPLAY_NAMES[display] for display in _in_order(data.wrong, data.other))
    return (
        f"A {first} and a {second} of the data should match, but one has a mistake. Which one "
        "has the mistake, and how should it be fixed?"
    )


def error_displays(data: FindErrorQuestionData) -> tuple[DataDisplay, ...]:
    """Return the displays a question to find an error shows, in the order of ``DataDisplay``,
    so where the wrong one stands says nothing."""
    if data.other is None:
        return (data.wrong,)
    return _in_order(data.wrong, data.other)


def _in_order(*displays: DataDisplay) -> tuple[DataDisplay, ...]:
    order = list(DataDisplay)
    return tuple(sorted(displays, key=order.index))


def error_sentence(data: FindErrorQuestionData) -> str:
    """Return the sentence to complete that fixes the error: "There should be ____ X's above
    ____.", "The bar for ____ should end at ____."."""
    if data.wrong in (DataDisplay.DOT_PLOT, DataDisplay.NUMBER_LINE_DOT_PLOT):
        return f"There should be {BLANK_LINE} X's above {BLANK_LINE}."
    fix = _FIXES[data.wrong].format(name=BLANK_LINE, count=BLANK_LINE, symbols=BLANK_LINE)
    return f"{fix[0].upper()}{fix[1:]}."


def error_fix(data: FindErrorQuestionData, choice: ErrorChoice) -> str:
    """
    Return a statement of an error, as a choice or the answer key gives it: "The row for Sports
    should have 1½ symbols", or naming the display, "Pictograph, because the row for Sports
    should have 1½ symbols".
    """
    dataset = data.dataset
    scale = dataset.scale if isinstance(dataset, CategoricalData) else 1
    fix = _FIXES[choice.display].format(
        name=labels(dataset)[choice.index],
        count=choice.count,
        symbols=_symbols(choice.count, scale),
    )
    if data.other is None:
        return f"{fix[0].upper()}{fix[1:]}"
    return f"{DISPLAY_NAMES[choice.display].capitalize()}, because {fix}"


def _symbols(count: int, scale: int) -> str:
    """Return how many symbols show ``count`` on ``scale``: "3", or with a half, "1½"."""
    whole, half = divmod(2 * count // scale, 2)
    if not half:
        return str(whole)
    return f"{whole}\N{VULGAR FRACTION ONE HALF}" if whole else "\N{VULGAR FRACTION ONE HALF}"


def counts_text(dataset: CategoricalData | NumericalData, counts: Sequence[int]) -> str:
    """
    Return a list of counts as a choice or the answer key gives it: "Apples: 12,  Grapes: 3",
    or for a list of numbers, its numbers from least to greatest: "20, 21, 21, 23".
    """
    names = labels(dataset)
    if isinstance(dataset, NumericalData):
        pairs = zip(names, counts, strict=True)
        return ", ".join(name for name, count in pairs for _ in range(count))
    return ",  ".join(f"{name}: {count}" for name, count in zip(names, counts, strict=True))


def _listed(items: Sequence[str]) -> str:
    """Return ``items`` as a list in a sentence: "a, b, and c"."""
    if len(items) <= 2:
        return " and ".join(items)
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def mistake(
    data: SummarizeDataQuestionData | ReadCountsQuestionData | DoesntMatchQuestionData,
    choice: DisplayChoice | ShownDisplay,
) -> str:
    """
    Return what is wrong with a wrong choice, as the answer key says it: "Soccer and Tennis are
    switched", or on a number line, "2 X's above 21 instead of 3". A choice with two mistakes
    names both: "Soccer and Tennis are switched, and the scale counts by 5, not by 10".
    """
    dataset = data.dataset
    given: DataDisplay | None
    shown: DataDisplay | None
    match data:
        case SummarizeDataQuestionData():
            given, shown, scale = data.given, data.target, _scale(dataset)
        case ReadCountsQuestionData():
            given, shown, scale = data.given, None, _scale(dataset)
        case DoesntMatchQuestionData():
            if not isinstance(choice, ShownDisplay):
                raise ValueError("A display that doesn't match is a ShownDisplay.")
            given, shown, scale = None, choice.display, choice.scale
    made = choice.choice if isinstance(choice, ShownDisplay) else choice
    if not made.mistakes:
        raise ValueError("The correct choice has no mistake.")
    return ", and ".join(
        _mistake_text(dataset, given, shown, scale, each) for each in made.mistakes
    )


def _scale(dataset: CategoricalData | NumericalData) -> int:
    return dataset.scale if isinstance(dataset, CategoricalData) else 1


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


def _mistake_text(
    dataset: CategoricalData | NumericalData,
    given: DataDisplay | None,
    shown: DataDisplay | None,
    scale: int,
    mistake: DisplayMistake,
) -> str:
    """Return one mistake's description, from the data set's labels and counts."""
    names = labels(dataset)
    on_line = isinstance(dataset, NumericalData)
    match mistake:
        case Swap():
            first, second = names[mistake.first], names[mistake.second]
            pair = f"the X's for {first} and {second}" if on_line else f"{first} and {second}"
            return f"{pair} are switched"
        case Off():
            name, count, wrong = names[mistake.index], dataset.counts[mistake.index], mistake.count
            if on_line:
                marks = "1 X" if wrong == 1 else f"{wrong} X's"
                return f"{marks} above {name} instead of {count}"
            return f"{name} shows {wrong} instead of {count}"
        case WrongScale():
            return _scale_mistake(given, shown, scale, mistake.scale)
        case OneEach():
            return "only one X for each number in the list"
        case EveryTick():
            return "one X above every number on the line"
        case RoundDown():
            return _round_down_mistake(given, shown)
        case _:
            assert_never(mistake)


def _scale_mistake(
    given: DataDisplay | None, shown: DataDisplay | None, scale: int, wrong_scale: int
) -> str:
    """Return a wrong scale's mistake: in the display shown if it has a scale, or else in
    reading the given display's."""
    if shown is DataDisplay.PICTOGRAPH:
        return f"the key says each star = {wrong_scale}, not {scale}"
    if shown is DataDisplay.BAR_GRAPH:
        return f"the scale counts by {wrong_scale}, not by {scale}"
    if given is DataDisplay.PICTOGRAPH:
        if wrong_scale == 1:
            return "counts each star as 1"
        return f"uses a key of {wrong_scale}, not {scale}"
    if given is DataDisplay.BAR_GRAPH:
        return f"reads the scale as counting by {wrong_scale}, not by {scale}"
    raise ValueError("Neither display has a scale.")


def _round_down_mistake(given: DataDisplay | None, shown: DataDisplay | None) -> str:
    """Return the mistake of taking counts between steps at the step below: in the display shown
    if it has a scale, or else in reading the given display."""
    if shown is DataDisplay.PICTOGRAPH:
        return "leaves out the half stars"
    if shown is DataDisplay.BAR_GRAPH:
        return "each bar that ends between lines stops at the line below"
    if given is DataDisplay.PICTOGRAPH:
        return "doesn't count the half stars"
    if given is DataDisplay.BAR_GRAPH:
        return "reads each bar that ends between lines at the line below"
    raise ValueError("Neither display has a scale.")


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
        case NumericalProblemType.MORE_THAN:
            more_than = _phrase(topic, f"more than {ticks[0]} {topic.amount_plural}")
            return f"How many {topic.unit} {more_than}?"
        case NumericalProblemType.FEWER_THAN:
            fewer_than = _phrase(topic, f"fewer than {ticks[0]} {topic.amount_plural}")
            return f"How many {topic.unit} {fewer_than}?"
        case NumericalProblemType.MISSING_VALUE:
            if topic.missing_question is None or data.total is None:
                raise ValueError("A missing number needs its topic's question and a total.")
            return topic.missing_question.format(total=data.total)
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
        case NumericalProblemType.MORE_THAN:
            threshold = data.tick_indexes[0]
            return _sum_text([count for count in counts[threshold + 1 :] if count])
        case NumericalProblemType.FEWER_THAN:
            threshold = data.tick_indexes[0]
            return _sum_text([count for count in counts[:threshold] if count])
        case NumericalProblemType.MISSING_VALUE:
            if data.total is None:
                raise ValueError("A missing number needs a total.")
            listed = sum(data.dataset.values)
            return f"{_sum_text(data.dataset.values)},  {_difference_text(data.total, listed)}"
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
