"""Random generation of data sets, each with a display to complete and two problems to solve."""

import random
from collections.abc import Iterator, Sequence
from itertools import combinations
from typing import assert_never

from core.basic_operations.word_problems import NAMES
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
from core.discrete_data.topics import (
    CATEGORY_TOPICS,
    NUMBER_LIST_TOPICS,
    FriendsTopic,
    NumberListTopic,
    SurveyTopic,
)
from core.question import FreeResponse, Question

# The displays a categorical data set is shown in. The given and target displays rotate through
# them, so each is a target once in every four problems.
CATEGORICAL_DISPLAYS = (
    DataDisplay.TABLE,
    DataDisplay.PICTOGRAPH,
    DataDisplay.BAR_GRAPH,
    DataDisplay.DOT_PLOT,
)
CATEGORY_COUNT = 4  # the categories in a categorical data set
BLANK_CATEGORIES = 2  # the categories whose counts are left out of the target display
SCALES = (2, 5, 10)  # a pictograph symbol's value and a bar graph's interval
DOT_PLOT_SCALE = 2  # the scale of a data set shown in a dot plot
MOST_DOT_PLOT_XS = 10  # with a dot plot, the counts are 1 to this
MOST_PICTOGRAPH_SYMBOLS = 8  # without one, the counts are at most this many symbols' worth

# The ticks on a number line that is a window of its topic's ticks, fewest and most
LINE_TICKS = (6, 18)
LIST_LENGTH = (12, 26)  # the numbers in a list on such a line, fewest and most
# The numbers in a list of a topic's possible values, such as coins, fewest and most
POSSIBLE_VALUES_LIST_LENGTH = (9, 20)
TALLEST_STACK = (3, 8)  # the Xs on a number line's most frequent number, fewest and most
NEAR_PEAK = 0.6  # the chance that a number in a windowed list is drawn near the list's peak
MORE_CHANCE = 0.6  # the chance that a number list's one-step problem is MORE, if it can be


def generate_discrete_data_problems(count: int) -> list[DiscreteDataProblem]:
    """
    Generate ``count`` problems, each a data set with a display to complete, as in
    ``_display_pairs``, and a one-step and a two-step problem solved from its counts.

    Topics and scales are dealt from shuffled decks, so none repeats on a sheet until all have
    been used. A data set shown in a dot plot has a scale of 2.
    """
    category_topics = _deck(CATEGORY_TOPICS)
    number_list_topics = _deck(NUMBER_LIST_TOPICS)
    scales = _deck(SCALES)
    problems: list[DiscreteDataProblem] = []
    for given, target in _display_pairs(count):
        if given is DataDisplay.LIST:
            numerical = _numerical_data(next(number_list_topics))
            problems.append(
                _problem(
                    numerical,
                    given,
                    target,
                    blanks=tuple(range(len(numerical.ticks))),
                    one_step=_numerical_one_step(numerical),
                    two_step=_numerical_two_step(numerical),
                )
            )
        else:
            scale = DOT_PLOT_SCALE if DataDisplay.DOT_PLOT in (given, target) else next(scales)
            categorical = _categorical_data(next(category_topics), given, target, scale)
            problems.append(
                _problem(
                    categorical,
                    given,
                    target,
                    blanks=tuple(sorted(random.sample(range(CATEGORY_COUNT), BLANK_CATEGORIES))),
                    one_step=_categorical_one_step(categorical),
                    two_step=_categorical_two_step(categorical),
                )
            )
    return problems


def _deck[Item](items: Sequence[Item]) -> Iterator[Item]:
    """Deal ``items`` in a random order, reshuffling them each time they run out."""
    while True:
        yield from random.sample(items, len(items))


def _display_pairs(count: int) -> list[tuple[DataDisplay, DataDisplay]]:
    """
    Return ``count`` (given, target) display pairs, where the target is the display to complete.

    The categorical displays are shuffled, and each one's target is the display a random shift
    along, so each display is a target once in every four problems, and never its own given.
    A dot plot target becomes a number list to complete as a number-line dot plot, so a
    categorical dot plot is only ever given.
    """
    givens = random.sample(CATEGORICAL_DISPLAYS, len(CATEGORICAL_DISPLAYS))
    shift = random.randint(1, len(givens) - 1)
    pairs = []
    for index in range(count):
        position = index % len(givens)
        given, target = givens[position], givens[(position + shift) % len(givens)]
        if target is DataDisplay.DOT_PLOT:
            pairs.append((DataDisplay.LIST, DataDisplay.NUMBER_LINE_DOT_PLOT))
        else:
            pairs.append((given, target))
    return pairs


def _problem(
    dataset: CategoricalData | NumericalData,
    given: DataDisplay,
    target: DataDisplay,
    *,
    blanks: tuple[int, ...],
    one_step: CategoricalDataProblemData | NumericalDataProblemData,
    two_step: CategoricalDataProblemData | NumericalDataProblemData,
) -> DiscreteDataProblem:
    """Make the summarizing question, with ``blanks``' counts as its answer, and pair all three
    questions with free response."""
    summarize = SummarizeDataQuestionData(
        dataset=dataset,
        given=given,
        target=target,
        blanks=blanks,
        answer=tuple(dataset.counts[index] for index in blanks),
    )
    return DiscreteDataProblem(
        summarize=Question(summarize, FreeResponse()),
        one_step=Question(one_step, FreeResponse()),
        two_step=Question(two_step, FreeResponse()),
    )


def _categorical_data(
    topic: SurveyTopic | FriendsTopic, given: DataDisplay, target: DataDisplay, scale: int
) -> CategoricalData:
    """
    Make a data set for ``topic`` whose distinct counts fit both displays.

    With a dot plot, the counts are 1 to 10 Xs. Otherwise they are at most 8 pictograph symbols'
    worth, in steps of half a symbol when ``scale`` is even, or a whole symbol when it is odd.
    A survey's categories are drawn from its topic, and friends are drawn from the word-problem
    bank's names.
    """
    if DataDisplay.DOT_PLOT in (given, target):
        allowed = range(1, MOST_DOT_PLOT_XS + 1)
    else:
        step = scale // 2 if scale % 2 == 0 else scale
        allowed = range(step, MOST_PICTOGRAPH_SYMBOLS * scale + 1, step)
    counts = tuple(random.sample(allowed, CATEGORY_COUNT))
    match topic:
        case SurveyTopic():
            categories = tuple(random.sample(topic.categories, CATEGORY_COUNT))
            person: str | None = random.choice(NAMES)
        case FriendsTopic():
            categories = tuple(random.sample(NAMES, CATEGORY_COUNT))
            person = None
        case _:
            assert_never(topic)
    return CategoricalData(
        topic=topic, categories=categories, counts=counts, scale=scale, person=person
    )


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


def _numerical_data(topic: NumberListTopic) -> NumericalData:
    """
    Make a list of numbers for ``topic``, in a random order.

    With ``possible_values``, such as coins, the list holds each possible value 1 to 8 times, at
    least one of them 3 times or more, and 9 to 20 numbers in all; the number line shows all
    the topic's ticks. Otherwise the number line is a random window of 6 to 18 of the topic's
    ticks, and the counts are drawn by ``_window_counts``.
    """
    if topic.possible_values is None:
        tick_count = random.randint(LINE_TICKS[0], min(LINE_TICKS[1], len(topic.ticks)))
        start = random.randint(0, len(topic.ticks) - tick_count)
        ticks = tuple(topic.ticks[start : start + tick_count])
        counts = _window_counts(tick_count)
    else:
        ticks = tuple(topic.ticks)
        while True:
            value_counts = [random.randint(1, TALLEST_STACK[1]) for _ in topic.possible_values]
            fewest, most = POSSIBLE_VALUES_LIST_LENGTH
            if fewest <= sum(value_counts) <= most and max(value_counts) >= TALLEST_STACK[0]:
                break
        count_of = dict(zip(topic.possible_values, value_counts, strict=True))
        counts = [count_of.get(tick, 0) for tick in ticks]
    values = [tick for tick, count in zip(ticks, counts, strict=True) for _ in range(count)]
    random.shuffle(values)
    return NumericalData(
        topic=topic, values=tuple(values), ticks=ticks, person=random.choice(NAMES)
    )


def _window_counts(tick_count: int) -> list[int]:
    """
    Return the counts for a number line of ``tick_count`` ticks: a hump around a random peak,
    with some spread.

    The list has 12 to 26 numbers, each drawn near the peak 60% of the time and anywhere on the
    line otherwise. The counts are drawn again until the tallest stack is 3 to 8 Xs, the first
    two ticks and the last two each have some data, and few ticks are empty: at most one on a
    line of 7 ticks or fewer, and fewer than half on a longer line.
    """
    fewest_used = tick_count - 1 if tick_count <= 7 else tick_count // 2 + 1
    while True:
        peak = random.uniform(0, tick_count - 1)
        counts = [0] * tick_count
        for _ in range(random.randint(*LIST_LENGTH)):
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


def _numerical_two_step(dataset: NumericalData) -> NumericalDataProblemData:
    """
    Make an AT_LEAST, AT_MOST or PAIR_MORE problem, as in ``_choose_type_first``.

    AT_LEAST and AT_MOST take a number in the list with data on both sides of it. PAIR_MORE
    takes two numbers in the list whose total count is larger than a third's.
    """
    counts = dataset.counts
    used = [index for index, count in enumerate(counts) if count]
    candidates: list[tuple[NumericalProblemType, tuple[int, ...], int]] = []
    for threshold in used[1:-1]:
        candidates.append((NumericalProblemType.AT_LEAST, (threshold,), sum(counts[threshold:])))
        candidates.append(
            (NumericalProblemType.AT_MOST, (threshold,), sum(counts[: threshold + 1]))
        )
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
