"""
Random generation of data sets, each with a question summarizing it, and two problems to solve.
"""

import random
from collections.abc import Collection, Iterator, Sequence
from dataclasses import dataclass
from functools import cache
from itertools import combinations, repeat
from typing import assert_never

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DataProblemQuestion,
    DiscreteDataPart,
    DiscreteDataProblem,
    DisplayChoice,
    DoesntMatchQuestionData,
    FindErrorQuestionData,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    ReadCountsQuestionData,
    ShownDisplay,
    SummarizeData,
    SummarizeDataQuestionData,
    SummarizeResponse,
)
from core.discrete_data.topics import (
    CATEGORY_TOPICS,
    NUMBER_LIST_TOPICS,
    FriendsTopic,
    NumberListTopic,
    SurveyTopic,
)
from core.discrete_data.wrong_answers import (
    MOST_STEPS,
    MOST_SYMBOLS,
    MOST_TALLIES,
    MOST_XS,
    count_choices,
    display_choices,
    doesnt_match_choices,
    error_choices,
    number_choices,
    wrong_display,
)
from core.names import NAMES
from core.question import FreeResponse, Question

# The displays a categorical data set is shown in
CATEGORICAL_DISPLAYS = (
    DataDisplay.TABLE,
    DataDisplay.TALLY_TABLE,
    DataDisplay.PICTOGRAPH,
    DataDisplay.BAR_GRAPH,
    DataDisplay.DOT_PLOT,
)
# The displays a sheet can show its data sets in: the categorical displays, and a list of
# numbers, which is completed as a number-line dot plot
SHEET_DISPLAYS = (*CATEGORICAL_DISPLAYS, DataDisplay.LIST)
# The categorical displays whose counts take reading: a table shows its counts as numbers
READ_DISPLAYS = (
    DataDisplay.TALLY_TABLE,
    DataDisplay.PICTOGRAPH,
    DataDisplay.BAR_GRAPH,
    DataDisplay.DOT_PLOT,
)
# The parts that summarize a data set, of which a problem asks one first
SUMMARIZE_PARTS = (
    DiscreteDataPart.ANOTHER_DISPLAY,
    DiscreteDataPart.READ_COUNTS,
    DiscreteDataPart.FIND_ERROR,
    DiscreteDataPart.DOESNT_MATCH,
)
# The parts whose answers can go on self-check tiles, one tile each
TILE_PARTS = (DiscreteDataPart.ONE_STEP, DiscreteDataPart.TWO_STEP)

type ProblemData = CategoricalDataProblemData | NumericalDataProblemData
CATEGORY_COUNTS = (3, 6)  # the categories in a categorical data set, fewest and most
BLANK_CATEGORIES = 2  # the categories whose counts are left out of a display to complete
# A pictograph symbol's value and a bar graph's interval: a pictograph's, or else one of these
SCALES = (2, 3, 4, 5, 6, 8, 10, 20)
PICTOGRAPH_SCALES = (2, 3, 4, 5, 6, 10)
DOT_PLOT_SCALE = 2  # the scale of a data set shown in a dot plot
MOST_DOT_PLOT_XS = 10  # with a dot plot, the counts are 1 to this
MOST_PICTOGRAPH_SYMBOLS = 8  # otherwise, the counts are at most this many symbols' worth
MOST_TALLY_ONLY = 20  # with tally marks and neither a pictograph nor a bar graph, the most
HORIZONTAL_BARS_CHANCE = 0.5  # the chance that a data set's bar graph has its bars across
# Displays that don't all show the data: the units their counts are multiples of, and the
# scales their pictographs and bar graphs can have
MATCH_UNITS = (1, 2, 3, 4, 5, 6, 10)
MATCH_PICTOGRAPH_SCALES = (2, 3, 4, 5, 6, 10, 12)
MATCH_BAR_SCALES = (2, 3, 4, 5, 6, 8, 10, 20)
MATCH_DISPLAYS = 4
MATCH_MULTIPLES = (3, 6)  # a count is one of these many multiples of the unit, fewest and most

# The ticks on a number line that is a window of its topic's ticks, fewest and most
LINE_TICKS = (6, 18)
LIST_LENGTH = (12, 26)  # the numbers in a list on such a line, fewest and most
# The numbers in a list of a topic's possible values, such as coins, fewest and most
POSSIBLE_VALUES_LIST_LENGTH = (9, 20)
TALLEST_STACK = (3, 8)  # the Xs on a number line's most frequent number, fewest and most
NEAR_PEAK = 0.6  # the chance that a number in a windowed list is drawn near the list's peak
MORE_CHANCE = 0.6  # the chance that a number list's one-step problem is MORE, if it can be
# With distinct answers: a problem's draws before its sheet starts again, its draws before it
# takes a new topic, and the sheet's starts before it's refused
PROBLEM_ATTEMPTS = 100
TOPIC_ATTEMPTS = 20
SHEET_ATTEMPTS = 10
# A list with a missing number is short, so its total is a sum a student can work out: its
# number line's ticks, and its numbers, fewest and most
SHORT_LINE_TICKS = (5, 7)
SHORT_LIST_LENGTH = (6, 10)
# The two-step problems about a list of numbers, of which a topic whose numbers add up asks a
# missing number as often as each other kind
NUMERICAL_TWO_STEP_TYPES = (
    NumericalProblemType.AT_LEAST,
    NumericalProblemType.AT_MOST,
    NumericalProblemType.MORE_THAN,
    NumericalProblemType.FEWER_THAN,
    NumericalProblemType.PAIR_MORE,
    NumericalProblemType.MISSING_VALUE,
)


@dataclass(frozen=True)
class _Plan:
    """
    The displays a problem shows, before its data set is drawn. ``given`` is the display its
    problems are read from, or ``None`` when its introduction states the counts. ``target`` is
    the display to complete or choose, ``wrong`` the display with an error and ``other`` a second
    display beside it, each ``None`` where the problem's first part has none.
    """

    part: DiscreteDataPart | None
    given: DataDisplay | None
    target: DataDisplay | None = None
    wrong: DataDisplay | None = None
    other: DataDisplay | None = None

    @property
    def numerical(self) -> bool:
        """Whether the data set is a list of numbers."""
        numbers = (DataDisplay.LIST, DataDisplay.NUMBER_LINE_DOT_PLOT)
        return any(display in numbers for display in (self.given, self.target, self.wrong))

    @property
    def displays(self) -> set[DataDisplay]:
        """The displays the data set is drawn in."""
        shown = (self.given, self.target, self.wrong, self.other)
        return {display for display in shown if display is not None}


@dataclass(frozen=True)
class _Decks:
    """The decks a sheet deals its topics and scales from, so none repeats until all are used."""

    category_topics: Iterator[SurveyTopic | FriendsTopic]
    number_list_topics: Iterator[NumberListTopic]
    scales: Iterator[int]
    pictograph_scales: Iterator[int]


def available_parts(displays: Collection[DataDisplay]) -> tuple[DiscreteDataPart, ...]:
    """
    Return the parts that can be asked with ``displays``, in the order of ``DiscreteDataPart``:
    - another display, with two categorical displays to pair, or a list;
    - reading the counts and finding an error, with a display whose counts take reading (any but
      a table), or a list, read from its number-line dot plot;
    - which display doesn't match, with four different displays of one data set, as
      ``_match_layouts`` finds them;
    - the problems, with any display.
    """
    categorical = [display for display in CATEGORICAL_DISPLAYS if display in displays]
    available = set()
    if len(categorical) >= 2 or DataDisplay.LIST in displays:
        available.add(DiscreteDataPart.ANOTHER_DISPLAY)
    if _read_displays(displays):
        available |= {DiscreteDataPart.READ_COUNTS, DiscreteDataPart.FIND_ERROR}
    if _match_layouts(displays):
        available.add(DiscreteDataPart.DOESNT_MATCH)
    if displays:
        available |= set(TILE_PARTS)
    return tuple(part for part in DiscreteDataPart if part in available)


def generate_discrete_data_problems(
    count: int,
    displays: Collection[DataDisplay] = SHEET_DISPLAYS,
    parts: Collection[DiscreteDataPart] = tuple(DiscreteDataPart),
    *,
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[DiscreteDataProblem]:
    """
    Generate ``count`` problems from ``displays``, each a data set with the ``parts`` asked
    about it: first one of the summarizing parts, dealt in turn so each comes up equally, then a
    one-step and a two-step problem solved from its counts.

    With ``multiple_choice``, every question that can be chosen is: the display to complete,
    the list of counts, the statement of an error, and the problems' numbers. Choosing the
    display that doesn't match always is. Topics and scales are dealt from shuffled decks, so
    none repeats on a sheet until all have been used.

    With ``distinct_answers``, as the self-check tiles case needs, the problems are written,
    whatever ``multiple_choice`` says, and no two of the sheet's problems' answers are the same:
    a problem's data set is drawn again until its answers differ from each other and from the
    earlier problems', and a sheet that runs short starts again (see ``_sheet``). Ask no more
    than ``most_tile_problems`` allows.

    Raises ``ValueError`` if ``parts`` is empty, if ``displays`` is empty or holds one not in
    ``SHEET_DISPLAYS``, if a part in ``parts`` isn't among ``available_parts(displays)``, if
    ``distinct_answers`` is given without a part from ``TILE_PARTS``, or if no sheet with
    distinct answers is found in ``SHEET_ATTEMPTS`` starts.
    """
    if not parts:
        raise ValueError("Ask at least one part.")
    if not displays or any(display not in SHEET_DISPLAYS for display in displays):
        raise ValueError(f"Displays must be from {', '.join(SHEET_DISPLAYS)}.")
    unavailable = [part for part in parts if part not in available_parts(displays)]
    if unavailable:
        raise ValueError(f"The displays can't make {', '.join(unavailable)}.")
    if distinct_answers and not any(part in parts for part in TILE_PARTS):
        raise ValueError("Distinct answers need a one-step or two-step problem.")

    for _ in range(SHEET_ATTEMPTS):
        problems = _sheet(count, displays, parts, multiple_choice, distinct_answers)
        if problems is not None:
            return problems
    raise ValueError("No sheet has a different answer for every problem with those displays.")


def _sheet(
    count: int,
    displays: Collection[DataDisplay],
    parts: Collection[DiscreteDataPart],
    multiple_choice: bool,
    distinct_answers: bool,
) -> list[DiscreteDataProblem] | None:
    """
    Draw a sheet, as ``generate_discrete_data_problems`` describes, or return ``None`` if, with
    ``distinct_answers``, a problem's answers can't be made new in ``PROBLEM_ATTEMPTS`` draws.
    A problem draws a new topic every ``TOPIC_ATTEMPTS`` draws, as a topic's answers can all be
    used already.
    """
    summarizing = [part for part in SUMMARIZE_PARTS if part in parts]
    first_parts: Iterator[DiscreteDataPart | None] = (
        _deck(summarizing) if summarizing else repeat(None)
    )
    pairs = _display_pairs(displays)
    givens = _deck([display for display in SHEET_DISPLAYS if display in displays])
    readable = _read_displays(displays)
    read_displays = _deck(readable) if readable else iter(())
    wrong_displays = _deck(readable) if readable else iter(())
    decks = _Decks(
        _deck(CATEGORY_TOPICS), _deck(NUMBER_LIST_TOPICS), _deck(SCALES), _deck(PICTOGRAPH_SCALES)
    )
    word_choices = multiple_choice and not distinct_answers
    used: set[int] = set()
    problems: list[DiscreteDataProblem] = []
    for _ in range(count):
        part = next(first_parts)
        plan = _plan(part, displays, pairs, givens, read_displays, wrong_displays, multiple_choice)
        for attempt in range(PROBLEM_ATTEMPTS):
            if attempt % TOPIC_ATTEMPTS == 0:
                if plan.numerical:
                    number_list_topic = next(decks.number_list_topics)
                    # the problem's kind is chosen before its list, short for a missing number
                    missing = (
                        DiscreteDataPart.TWO_STEP in parts
                        and number_list_topic.missing_question is not None
                        and random.randrange(len(NUMERICAL_TWO_STEP_TYPES)) == 0
                    )
                else:
                    missing = False
                    category_topic = next(decks.category_topics)
                    scale = _scale(plan.displays, decks)
            if plan.numerical:
                dataset: CategoricalData | NumericalData = _numerical_data(
                    number_list_topic, short=missing
                )
            elif part is DiscreteDataPart.DOESNT_MATCH:
                dataset, shown = _doesnt_match(category_topic, displays)
            else:
                dataset = _categorical_data(category_topic, plan.displays, scale)
            summarize = None
            if part is DiscreteDataPart.DOESNT_MATCH and isinstance(dataset, CategoricalData):
                summarize = _doesnt_match_question(dataset, plan, shown)
            elif part is not None:
                summarize = _summarize(part, plan, dataset, multiple_choice)
            problem = DiscreteDataProblem(
                dataset=dataset,
                given=plan.given,
                summarize=summarize,
                one_step=_word_problem(
                    dataset, DiscreteDataPart.ONE_STEP, parts, word_choices, missing
                ),
                two_step=_word_problem(
                    dataset, DiscreteDataPart.TWO_STEP, parts, word_choices, missing
                ),
            )
            answers = [question.data.answer for question in problem.word_problems]
            if not distinct_answers or (
                len(set(answers)) == len(answers) and used.isdisjoint(answers)
            ):
                break
        else:
            return None
        used.update(answers)
        problems.append(problem)
    return problems


def most_tile_problems(
    displays: Collection[DataDisplay], parts: Collection[DiscreteDataPart]
) -> int | None:
    """
    Return the most problems a sheet of self-check tiles can have, each answer different, with
    ``parts`` from ``displays``, or ``None`` for no limit but the tiles'.

    Only choosing the display that doesn't match limits it: its counts are a few multiples of a
    unit, so its problems' answers take few values, as ``_match_answers`` finds them. It's one
    of the summarizing parts dealt in turn, so it asks one problem in so many, and the sheet
    can have that many times as many problems as its answers allow.
    """
    words = [part for part in TILE_PARTS if part in parts]
    if DiscreteDataPart.DOESNT_MATCH not in parts or not words:
        return None
    one_step, two_step = _match_answers(frozenset(displays))
    if words == [DiscreteDataPart.ONE_STEP]:
        most = len(one_step)
    elif words == [DiscreteDataPart.TWO_STEP]:
        most = len(two_step)
    else:
        # both from one data set, which not every pair of answers can be: one fewer than they
        # allow, so a sheet is found every time rather than most times
        most = min(len(one_step), len(two_step), len(one_step | two_step) // 2) - 1
    return most * sum(part in parts for part in SUMMARIZE_PARTS)


@cache
def _match_answers(displays: frozenset[DataDisplay]) -> tuple[set[int], set[int]]:
    """
    Return every answer a one-step and a two-step problem can have with the data sets of
    ``_match_layouts``: 3 to 6 of the multiples of a layout's unit, as ``_doesnt_match`` draws
    them.
    """
    one_step: set[int] = set()
    two_step: set[int] = set()
    for unit, multiples, _ in _match_layouts(displays):
        counts = [unit * multiple for multiple in range(1, multiples + 1)]
        for size in range(CATEGORY_COUNTS[0], min(CATEGORY_COUNTS[1], multiples) + 1):
            for chosen in combinations(counts, size):
                total = sum(chosen)
                for first, second in combinations(chosen, 2):
                    one_step |= {abs(first - second), first + second}
                for third in chosen:
                    rest = [count for count in chosen if count != third]
                    two_step.add(total - third)
                    for first, second in combinations(rest, 2):
                        two_step.add(abs(first + second - third))
                two_step.add(total)
    return one_step, two_step - {0}


def _deck[Item](items: Sequence[Item]) -> Iterator[Item]:
    """Deal ``items`` in a random order, reshuffling them each time they run out."""
    while True:
        yield from random.sample(items, len(items))


def _read_displays(displays: Collection[DataDisplay]) -> list[DataDisplay]:
    """Return the displays among ``displays`` to read counts from or find errors in: the
    categorical ones that take reading, and a list's number-line dot plot."""
    readable = [display for display in READ_DISPLAYS if display in displays]
    if DataDisplay.LIST in displays:
        readable.append(DataDisplay.NUMBER_LINE_DOT_PLOT)
    return readable


def _plan(
    part: DiscreteDataPart | None,
    displays: Collection[DataDisplay],
    pairs: Iterator[tuple[DataDisplay, DataDisplay]],
    givens: Iterator[DataDisplay],
    read_displays: Iterator[DataDisplay],
    wrong_displays: Iterator[DataDisplay],
    multiple_choice: bool,
) -> _Plan:
    """
    Plan a problem's displays for its first ``part``, drawing from the sheet's decks:
    - none: a given display, any of ``displays``;
    - another display: a pair from ``_display_pairs``;
    - reading counts: a display that takes reading, or a list's number-line dot plot;
    - finding an error: the wrong display likewise, with the data in a table if ``displays``
      has one, or else stated in the introduction, or for a list, in the list. With
      ``multiple_choice``, a second display of another kind beside it, if there is one;
    - which doesn't match: the data in a table if ``displays`` has one, or else stated.
    """
    table = DataDisplay.TABLE if DataDisplay.TABLE in displays else None
    match part:
        case None:
            return _Plan(part, next(givens))
        case DiscreteDataPart.ANOTHER_DISPLAY:
            given, target = next(pairs)
            return _Plan(part, given, target=target)
        case DiscreteDataPart.READ_COUNTS:
            return _Plan(part, next(read_displays))
        case DiscreteDataPart.FIND_ERROR:
            wrong = next(wrong_displays)
            if wrong is DataDisplay.NUMBER_LINE_DOT_PLOT:
                return _Plan(part, DataDisplay.LIST, wrong=wrong)
            others = [
                display
                for display in _read_displays(displays)
                if display not in (wrong, DataDisplay.NUMBER_LINE_DOT_PLOT)
            ]
            other = random.choice(others) if multiple_choice and others else None
            return _Plan(part, table, wrong=wrong, other=other)
        case DiscreteDataPart.DOESNT_MATCH:
            return _Plan(part, table)
        case DiscreteDataPart.ONE_STEP | DiscreteDataPart.TWO_STEP:
            raise ValueError(f"{part} is not a summarizing part.")
        case _:
            assert_never(part)


def _display_pairs(displays: Collection[DataDisplay]) -> Iterator[tuple[DataDisplay, DataDisplay]]:
    """
    Deal (given, target) display pairs from ``displays``, where the target is the display to
    complete or choose.

    Each round, the categorical displays among ``displays`` are shuffled, and each one's target
    is the display a random shift along, so each is a target once in a round, and never its own
    given. With a list among ``displays``, a dot plot target becomes a list to complete as a
    number-line dot plot, so a categorical dot plot is then only ever given; without a dot plot,
    a list joins each round at a random place. With fewer than two categorical displays, every
    pair is a list's.
    """
    categorical = [display for display in CATEGORICAL_DISPLAYS if display in displays]
    lists = DataDisplay.LIST in displays
    list_pair = (DataDisplay.LIST, DataDisplay.NUMBER_LINE_DOT_PLOT)
    while True:
        if len(categorical) < 2:
            yield list_pair
            continue
        givens = random.sample(categorical, len(categorical))
        shift = random.randint(1, len(givens) - 1)
        round_pairs = []
        for position, given in enumerate(givens):
            target = givens[(position + shift) % len(givens)]
            round_pairs.append(
                list_pair if lists and target is DataDisplay.DOT_PLOT else (given, target)
            )
        if lists and DataDisplay.DOT_PLOT not in categorical:
            round_pairs.insert(random.randint(0, len(round_pairs)), list_pair)
        yield from round_pairs


def _summarize(
    part: DiscreteDataPart,
    plan: _Plan,
    dataset: CategoricalData | NumericalData,
    multiple_choice: bool,
) -> Question[SummarizeData, SummarizeResponse]:
    """Make the problem's first question, for any part but which display doesn't match."""
    response: SummarizeResponse = FreeResponse()
    data: SummarizeData
    match part:
        case DiscreteDataPart.ANOTHER_DISPLAY:
            if plan.given is None or plan.target is None:
                raise ValueError("Another display needs a given display and a target.")
            if multiple_choice:
                blanks = tuple(range(len(dataset.counts)))
            elif isinstance(dataset, NumericalData):
                blanks = tuple(range(len(dataset.ticks)))
            else:
                blanks = tuple(sorted(random.sample(range(len(dataset.counts)), BLANK_CATEGORIES)))
            data = SummarizeDataQuestionData(
                dataset=dataset,
                given=plan.given,
                target=plan.target,
                blanks=blanks,
                answer=tuple(dataset.counts[index] for index in blanks),
            )
            if multiple_choice:
                response = display_choices(data)
        case DiscreteDataPart.READ_COUNTS:
            if plan.given is None:
                raise ValueError("Reading counts needs a given display.")
            answer = (
                tuple(sorted(dataset.values))
                if isinstance(dataset, NumericalData)
                else dataset.counts
            )
            data = ReadCountsQuestionData(dataset=dataset, given=plan.given, answer=answer)
            if multiple_choice:
                response = count_choices(data)
        case DiscreteDataPart.FIND_ERROR:
            if plan.wrong is None:
                raise ValueError("Finding an error needs a wrong display.")
            index, shown = _error(dataset, plan.wrong)
            data = FindErrorQuestionData(
                dataset=dataset,
                source=plan.given,
                wrong=plan.wrong,
                other=plan.other,
                index=index,
                shown=shown,
                answer=dataset.counts[index],
            )
            if multiple_choice:
                response = error_choices(data)
        case DiscreteDataPart.DOESNT_MATCH | DiscreteDataPart.ONE_STEP | DiscreteDataPart.TWO_STEP:
            raise ValueError(f"{part} has no question of this kind.")
        case _:
            assert_never(part)
    return Question(data, response)


def _error(dataset: CategoricalData | NumericalData, wrong: DataDisplay) -> tuple[int, int]:
    """
    Return an error for the ``wrong`` display: the index of a count, and the count it shows
    instead. It's off by 1 or 2 in a display of marks worth 1 each, or else by a step of the
    scale or half a step, and fits the display.
    """
    counts = dataset.counts
    if isinstance(dataset, NumericalData):
        possible_values = dataset.topic.possible_values or dataset.ticks
        indexes = [index for index, tick in enumerate(dataset.ticks) if tick in possible_values]
        errors = [
            (index, count)
            for index in indexes
            for count in (counts[index] - 1, counts[index] + 1)
            if 0 <= count <= MOST_XS
        ]
        return random.choice(errors)
    scale = dataset.scale
    if wrong in (DataDisplay.DOT_PLOT, DataDisplay.TALLY_TABLE):
        steps: Sequence[int] = (1, 2)
        most = MOST_XS if wrong is DataDisplay.DOT_PLOT else MOST_TALLIES
    else:
        steps = sorted({scale // 2 if scale % 2 == 0 else scale, scale})
        most = (MOST_SYMBOLS if wrong is DataDisplay.PICTOGRAPH else MOST_STEPS) * scale
    errors = [
        (index, count + direction * step)
        for index, count in enumerate(counts)
        for step in steps
        for direction in (-1, 1)
        if 0 < count + direction * step <= most
    ]
    return random.choice(errors)


def _word_problem(
    dataset: CategoricalData | NumericalData,
    part: DiscreteDataPart,
    parts: Collection[DiscreteDataPart],
    multiple_choice: bool,
    missing: bool,
) -> DataProblemQuestion | None:
    """
    Make the one-step or two-step problem, if ``parts`` asks it, with choices if asked. A list's
    two-step problem asks for a missing number if ``missing``.
    """
    if part not in parts:
        return None
    data: ProblemData
    match dataset, part:
        case CategoricalData(), DiscreteDataPart.ONE_STEP:
            data = _categorical_one_step(dataset)
        case CategoricalData(), _:
            data = _categorical_two_step(dataset)
        case NumericalData(), DiscreteDataPart.ONE_STEP:
            data = _numerical_one_step(dataset)
        case _:
            data = _numerical_two_step(dataset, missing)
    if multiple_choice:
        return Question(data, number_choices(data))
    return Question(data, FreeResponse())


def _scale(displays: Collection[DataDisplay], decks: _Decks) -> int:
    """
    Return a categorical data set's scale for ``displays``: 2 with a dot plot, a pictograph's
    with a pictograph, 1 with tally marks and neither a pictograph nor a bar graph, or else any.
    """
    if DataDisplay.DOT_PLOT in displays:
        return DOT_PLOT_SCALE
    if DataDisplay.PICTOGRAPH in displays:
        return next(decks.pictograph_scales)
    if DataDisplay.TALLY_TABLE in displays and DataDisplay.BAR_GRAPH not in displays:
        return 1
    return next(decks.scales)


def _categorical_data(
    topic: SurveyTopic | FriendsTopic, displays: Collection[DataDisplay], scale: int
) -> CategoricalData:
    """
    Make a data set for ``topic`` whose distinct counts fit ``displays``, with 3 to 6
    categories, as many as the topic and the counts allow.

    With a dot plot, the counts are 1 to 10 Xs. With tally marks and no pictograph or bar graph,
    they're 1 to 20. Otherwise they are at most 8 pictograph symbols' worth, and 40 with tally
    marks, in steps of half a symbol when ``scale`` is even, or a whole symbol when it is odd.
    A survey's categories are drawn from its topic, and friends are drawn from the word-problem
    bank's names. A bar graph has its bars across half the time.
    """
    if DataDisplay.DOT_PLOT in displays:
        allowed = range(1, MOST_DOT_PLOT_XS + 1)
    elif scale == 1:
        allowed = range(1, MOST_TALLY_ONLY + 1)
    else:
        step = scale // 2 if scale % 2 == 0 else scale
        most = MOST_PICTOGRAPH_SYMBOLS * scale
        if DataDisplay.TALLY_TABLE in displays:
            most = min(most, MOST_TALLIES)
        allowed = range(step, most + 1, step)
    categories, person = _categories(topic, min(CATEGORY_COUNTS[1], len(allowed)))
    counts = tuple(random.sample(allowed, len(categories)))
    horizontal = DataDisplay.BAR_GRAPH in displays and random.random() < HORIZONTAL_BARS_CHANCE
    return CategoricalData(
        topic=topic,
        categories=categories,
        counts=counts,
        scale=scale,
        person=person,
        horizontal_bars=horizontal,
    )


def _categories(topic: SurveyTopic | FriendsTopic, most: int) -> tuple[tuple[str, ...], str | None]:
    """
    Return 3 to ``most`` categories for ``topic``, at most as many as a survey has, and the
    person who asked, if any: a survey's are drawn from its topic, and friends from the
    word-problem bank's names.
    """
    match topic:
        case SurveyTopic():
            count = random.randint(CATEGORY_COUNTS[0], min(most, len(topic.categories)))
            return tuple(random.sample(topic.categories, count)), random.choice(NAMES)
        case FriendsTopic():
            count = random.randint(CATEGORY_COUNTS[0], most)
            return tuple(random.sample(NAMES, count)), None
        case _:
            assert_never(topic)


def _match_layouts(
    displays: Collection[DataDisplay],
) -> tuple[tuple[int, int, tuple[tuple[DataDisplay, int], ...]], ...]:
    """Return ``_layouts`` for ``displays``, which it keeps for the next time."""
    return _layouts(frozenset(displays))


@cache
def _layouts(
    displays: frozenset[DataDisplay],
) -> tuple[tuple[int, int, tuple[tuple[DataDisplay, int], ...]], ...]:
    """
    Return the ways four different displays among ``displays`` can show one data set, as
    (unit, multiples, displays): the counts are multiples of the unit, up to ``multiples`` of
    them, and each display is a kind and a scale. A pictograph or bar graph of a scale needs
    every count a whole number of its steps, half a symbol or interval when the scale is even,
    and at most ``MOST_SYMBOLS`` symbols or ``MOST_STEPS`` intervals; a dot plot needs counts up
    to ``MOST_XS``, and a tally table up to ``MOST_TALLIES``. A table gives the data, so it's
    never one of the four.
    """
    layouts = []
    for unit in MATCH_UNITS:
        for multiples in range(MATCH_MULTIPLES[1], MATCH_MULTIPLES[0] - 1, -1):
            top = unit * multiples
            configs: list[tuple[DataDisplay, int]] = []
            if DataDisplay.PICTOGRAPH in displays:
                configs += [
                    (DataDisplay.PICTOGRAPH, scale)
                    for scale in MATCH_PICTOGRAPH_SCALES
                    if _shows(unit, top, scale, MOST_SYMBOLS)
                ]
            if DataDisplay.BAR_GRAPH in displays:
                configs += [
                    (DataDisplay.BAR_GRAPH, scale)
                    for scale in MATCH_BAR_SCALES
                    if _shows(unit, top, scale, MOST_STEPS)
                ]
            if DataDisplay.DOT_PLOT in displays and top <= MOST_XS:
                configs.append((DataDisplay.DOT_PLOT, unit))
            if DataDisplay.TALLY_TABLE in displays and top <= MOST_TALLIES:
                configs.append((DataDisplay.TALLY_TABLE, unit))
            if len(configs) >= MATCH_DISPLAYS:
                layouts.append((unit, multiples, tuple(configs)))
    return tuple(layouts)


def _shows(unit: int, top: int, scale: int, most: int) -> bool:
    """Whether a display of ``scale`` shows every multiple of ``unit`` up to ``top``."""
    step = scale // 2 if scale % 2 == 0 else scale
    return unit % step == 0 and top <= most * scale


def _doesnt_match(
    topic: SurveyTopic | FriendsTopic, displays: Collection[DataDisplay]
) -> tuple[CategoricalData, list[ShownDisplay]]:
    """
    Make a data set for ``topic`` and four different displays of it, from a layout of
    ``_match_layouts`` drawn at random: one of each kind first, then more scales, and one of the
    four with a mistake from ``wrong_display``, which comes first. Any display can take one: a
    swap changes every display, as the counts differ.
    """
    unit, multiples, configs = random.choice(_match_layouts(displays))
    kinds = list(dict.fromkeys(display for display, _ in configs))
    chosen: list[tuple[DataDisplay, int]] = []
    for kind in random.sample(kinds, len(kinds)):
        if len(chosen) < MATCH_DISPLAYS:
            chosen.append(random.choice([config for config in configs if config[0] is kind]))
    rest = [config for config in configs if config not in chosen]
    chosen += random.sample(rest, MATCH_DISPLAYS - len(chosen))
    categories, person = _categories(topic, min(CATEGORY_COUNTS[1], multiples))
    counts = tuple(
        random.sample([unit * multiple for multiple in range(1, multiples + 1)], len(categories))
    )
    horizontal = any(display is DataDisplay.BAR_GRAPH for display, _ in chosen) and (
        random.random() < HORIZONTAL_BARS_CHANCE
    )
    dataset = CategoricalData(
        topic=topic,
        categories=categories,
        counts=counts,
        scale=unit,
        person=person,
        horizontal_bars=horizontal,
    )
    random.shuffle(chosen)
    shown = [
        ShownDisplay(display, scale, DisplayChoice(counts, scale, ())) for display, scale in chosen
    ]
    for position, (display, scale) in enumerate(chosen):
        mistaken = wrong_display(dataset, display, scale)
        if mistaken is not None:
            shown[position] = ShownDisplay(display, scale, mistaken)
            shown.insert(0, shown.pop(position))
            return dataset, shown
    raise ValueError("None of the displays can take a mistake.")


def _doesnt_match_question(
    dataset: CategoricalData, plan: _Plan, shown: list[ShownDisplay]
) -> Question[SummarizeData, SummarizeResponse]:
    """Ask which of the ``shown`` displays doesn't match: the first, which has a mistake."""
    data = DoesntMatchQuestionData(dataset=dataset, source=plan.given, answer=shown[0])
    return Question(data, doesnt_match_choices(shown, 0))


def _categorical_one_step(dataset: CategoricalData) -> CategoricalDataProblemData:
    """Make a MORE, FEWER or PAIR_TOTAL problem about two random categories, larger count first."""
    counts = dataset.counts
    problem_type = random.choice(
        (
            CategoricalProblemType.MORE,
            CategoricalProblemType.FEWER,
            CategoricalProblemType.PAIR_TOTAL,
        )
    )
    larger, smaller = sorted(
        random.sample(range(len(counts)), 2), key=lambda index: counts[index], reverse=True
    )
    if problem_type is CategoricalProblemType.PAIR_TOTAL:
        answer = counts[larger] + counts[smaller]
    else:
        answer = counts[larger] - counts[smaller]
    return CategoricalDataProblemData(dataset, problem_type, (larger, smaller), answer)


def _categorical_two_step(dataset: CategoricalData) -> CategoricalDataProblemData:
    """
    Make a PAIR_MORE, MORE_THAN_PAIR, ALL_BUT or ALL problem, as in ``_choose_type_first``.

    A pair of categories and a third make PAIR_MORE when the pair's total is larger, and
    MORE_THAN_PAIR when the third is.
    """
    counts = dataset.counts
    total = sum(counts)
    candidates: list[tuple[CategoricalProblemType, tuple[int, ...], int]] = []
    for third in range(len(counts)):
        rest = [index for index in range(len(counts)) if index != third]
        for first, second in combinations(rest, 2):
            pair = counts[first] + counts[second]
            if pair > counts[third]:
                candidates.append(
                    (CategoricalProblemType.PAIR_MORE, (first, second, third), pair - counts[third])
                )
            if counts[third] > pair:
                candidates.append(
                    (
                        CategoricalProblemType.MORE_THAN_PAIR,
                        (third, first, second),
                        counts[third] - pair,
                    )
                )
        candidates.append((CategoricalProblemType.ALL_BUT, (third,), total - counts[third]))
    candidates.append((CategoricalProblemType.ALL, (), total))
    problem_type, categories, answer = _choose_type_first(candidates)
    return CategoricalDataProblemData(dataset, problem_type, categories, answer)


def _numerical_data(topic: NumberListTopic, short: bool = False) -> NumericalData:
    """
    Make a list of numbers for ``topic``, in a random order.

    With ``possible_values``, such as coins, the list holds each possible value 1 to 8 times, at
    least one of them 3 times or more, and 9 to 20 numbers in all; the number line shows all
    the topic's ticks. Otherwise the number line is a random window of 6 to 18 of the topic's
    ticks, and the counts are drawn by ``_window_counts``. A ``short`` list has 6 to 10 numbers,
    and a window of 5 to 7 ticks.
    """
    if topic.possible_values is None:
        fewest_ticks, most_ticks = SHORT_LINE_TICKS if short else LINE_TICKS
        tick_count = random.randint(fewest_ticks, min(most_ticks, len(topic.ticks)))
        start = random.randint(0, len(topic.ticks) - tick_count)
        ticks = tuple(topic.ticks[start : start + tick_count])
        counts = _window_counts(tick_count, SHORT_LIST_LENGTH if short else LIST_LENGTH)
    else:
        ticks = tuple(topic.ticks)
        fewest, most = SHORT_LIST_LENGTH if short else POSSIBLE_VALUES_LIST_LENGTH
        while True:
            value_counts = [random.randint(1, TALLEST_STACK[1]) for _ in topic.possible_values]
            if fewest <= sum(value_counts) <= most and max(value_counts) >= TALLEST_STACK[0]:
                break
        count_of = dict(zip(topic.possible_values, value_counts, strict=True))
        counts = [count_of.get(tick, 0) for tick in ticks]
    values = [tick for tick, count in zip(ticks, counts, strict=True) for _ in range(count)]
    random.shuffle(values)
    return NumericalData(
        topic=topic, values=tuple(values), ticks=ticks, person=random.choice(NAMES)
    )


def _window_counts(tick_count: int, length: tuple[int, int] = LIST_LENGTH) -> list[int]:
    """
    Return the counts for a number line of ``tick_count`` ticks: a hump around a random peak,
    with some spread.

    The list has ``length`` numbers, fewest and most, each drawn near the peak 60% of the time
    and anywhere on the line otherwise. The counts are drawn again until the tallest stack is 3
    to 8 Xs, the first two ticks and the last two each have some data, and few ticks are empty:
    at most one on a line of 7 ticks or fewer, and fewer than half on a longer line.
    """
    fewest_used = tick_count - 1 if tick_count <= 7 else tick_count // 2 + 1
    while True:
        peak = random.uniform(0, tick_count - 1)
        counts = [0] * tick_count
        for _ in range(random.randint(*length)):
            if random.random() < NEAR_PEAK:
                index = round(random.triangular(-0.5, tick_count - 0.5, peak))
            else:
                index = random.randrange(tick_count)
            counts[min(tick_count - 1, max(0, index))] += 1
        if (
            TALLEST_STACK[0] <= max(counts) <= TALLEST_STACK[1]
            and sum(1 for count in counts if count) >= fewest_used
            and (counts[0] or counts[1])
            and (counts[-1] or counts[-2])
        ):
            return counts


def _numerical_one_step(dataset: NumericalData) -> NumericalDataProblemData:
    """
    Make a problem about two numbers in the list: MORE, with the larger count first, 60% of the
    time when their counts differ, and otherwise PAIR_TOTAL, in number-line order.
    """
    counts = dataset.counts
    used = [index for index, count in enumerate(counts) if count]
    larger, smaller = sorted(random.sample(used, 2), key=lambda index: counts[index], reverse=True)
    if counts[larger] != counts[smaller] and random.random() < MORE_CHANCE:
        return NumericalDataProblemData(
            dataset, NumericalProblemType.MORE, (larger, smaller), counts[larger] - counts[smaller]
        )
    first, second = sorted((larger, smaller))
    return NumericalDataProblemData(
        dataset, NumericalProblemType.PAIR_TOTAL, (first, second), counts[first] + counts[second]
    )


def _numerical_two_step(dataset: NumericalData, missing: bool) -> NumericalDataProblemData:
    """
    Make a MISSING_VALUE problem if ``missing``, or else an AT_LEAST, AT_MOST, MORE_THAN,
    FEWER_THAN or PAIR_MORE problem, as in ``_choose_type_first``.

    MISSING_VALUE takes a number the list could hold, and the total of the list with it. AT_LEAST,
    AT_MOST, MORE_THAN and FEWER_THAN take a number in the list with data on both sides of it.
    PAIR_MORE takes two numbers in the list whose total count is larger than a third's.
    """
    if missing:
        answer = random.choice(dataset.topic.possible_values or dataset.ticks)
        total = sum(dataset.values) + answer
        return NumericalDataProblemData(
            dataset, NumericalProblemType.MISSING_VALUE, (), answer, total
        )
    counts = dataset.counts
    used = [index for index, count in enumerate(counts) if count]
    candidates: list[tuple[NumericalProblemType, tuple[int, ...], int]] = []
    for threshold in used[1:-1]:
        below, above = sum(counts[:threshold]), sum(counts[threshold + 1 :])
        candidates += [
            (NumericalProblemType.AT_LEAST, (threshold,), counts[threshold] + above),
            (NumericalProblemType.AT_MOST, (threshold,), below + counts[threshold]),
            (NumericalProblemType.MORE_THAN, (threshold,), above),
            (NumericalProblemType.FEWER_THAN, (threshold,), below),
        ]
    for third in used:
        rest = [index for index in used if index != third]
        for first, second in combinations(rest, 2):
            pair = counts[first] + counts[second]
            if pair > counts[third]:
                candidates.append(
                    (NumericalProblemType.PAIR_MORE, (first, second, third), pair - counts[third])
                )
    problem_type, tick_indexes, answer = _choose_type_first(candidates)
    return NumericalDataProblemData(dataset, problem_type, tick_indexes, answer)


def _choose_type_first[ProblemType](
    candidates: list[tuple[ProblemType, tuple[int, ...], int]],
) -> tuple[ProblemType, tuple[int, ...], int]:
    """
    Choose a problem type at random from the candidates' types, then one of that type's
    candidates, so that a type with many candidates doesn't crowd out the others.
    """
    problem_type = random.choice(list(dict.fromkeys(candidate[0] for candidate in candidates)))
    return random.choice([candidate for candidate in candidates if candidate[0] == problem_type])
