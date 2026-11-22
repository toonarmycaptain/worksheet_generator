"""
Choices for data-set questions: displays and lists of a data set's counts, statements of a
display's error, displays that don't all show the data, and numbers answering its problems.

A question to choose a display or a list has four choices: the right one, each of two mistakes on
its own, and both together. So every count and scale a choice shows is right in exactly two of
the four, and comparing the choices with each other, without reading the data, can't single out
the answer. A statement of an error is chosen the same way, from two displays or two counts, and
two categories.
"""

import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from itertools import combinations

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DisplayChoice,
    DisplayMistake,
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
    SummarizeDataQuestionData,
    Swap,
    WrongScale,
)
from core.question import MultipleChoice, multiple_choice

SCALED_DISPLAYS = (DataDisplay.PICTOGRAPH, DataDisplay.BAR_GRAPH)  # the displays with a scale
# the displays whose marks each stand for 1
UNIT_DISPLAYS = (DataDisplay.DOT_PLOT, DataDisplay.TALLY_TABLE)
WRONG_SCALES = (1, 2, 5, 10)  # a wrong scale is one of these
MOST_XS = 10  # a dot plot's column holds at most this many Xs
MOST_TALLIES = 40  # a tally table's row holds at most this many tally marks
MOST_SYMBOLS = 9  # a pictograph's row holds at most this many symbols
MOST_STEPS = 10  # a bar graph's longest bar reaches at most this many steps of its scale
WRONG_NUMBERS = 3

# The kinds of a question's two mistakes. A pair's mistakes change different counts, or one
# changes them all the same way, so both together show each as it shows alone, and the answer
# key can describe both.
CATEGORICAL_PAIRS: tuple[tuple[type[DisplayMistake], type[DisplayMistake]], ...] = (
    (Swap, Off),
    (Swap, Swap),
    (Off, Off),
    (Swap, WrongScale),
    (Swap, RoundDown),
)
NUMBER_LINE_PAIRS: tuple[tuple[type[DisplayMistake], type[DisplayMistake]], ...] = (
    (Swap, Off),
    (Swap, Swap),
    (Off, Off),
    (OneEach, Off),
    (EveryTick, Off),
)


@dataclass(frozen=True)
class _Setting:
    """
    Where choices are made: ``dataset`` read from the ``given`` display, if any, and the choices
    drawn as ``shown``, or written as lists for ``None``.
    """

    dataset: CategoricalData | NumericalData
    given: DataDisplay | None
    shown: DataDisplay | None


def display_choices(data: SummarizeDataQuestionData) -> MultipleChoice[DisplayChoice]:
    """
    Return four displays to choose from, drawn as the question's target, in a random order: the
    data set's own, one for each of two mistakes, and one with both (see ``_square``).
    """
    return _square(_Setting(data.dataset, data.given, data.target))


def count_choices(data: ReadCountsQuestionData) -> MultipleChoice[DisplayChoice]:
    """
    Return four lists of counts to choose from, read from the question's given display, in a
    random order: the right one, one for each of two mistakes, and one with both (see
    ``_square``).
    """
    return _square(_Setting(data.dataset, data.given, None))


def _square(setting: _Setting) -> MultipleChoice[DisplayChoice]:
    """
    Return the right choice, one for each of two mistakes, and one with both, shuffled.

    The two mistakes' kinds are drawn at random from the pairs that fit the data set, then the
    mistakes, from ``_mistakes``. The four choices must fit how they're shown and look
    different: their counts differ, or in a pictograph or bar graph, which shows its scale, their
    scales do.

    Raises ``ValueError`` if no two mistakes fit, which a generated data set never does: its
    counts can always take a swap and an off count elsewhere, or two off counts.
    """
    candidates = _mistakes(setting)
    numerical = isinstance(setting.dataset, NumericalData)
    kinds = NUMBER_LINE_PAIRS if numerical else CATEGORICAL_PAIRS
    for first_kind, second_kind in random.sample(kinds, len(kinds)):
        pairs = [
            (first, second)
            for first in candidates
            if isinstance(first, first_kind)
            for second in candidates
            if isinstance(second, second_kind) and _apart(first, second, setting.dataset.counts)
        ]
        random.shuffle(pairs)
        for first, second in pairs:
            choices = [
                _choice(setting, mistakes)
                for mistakes in ((), (first,), (second,), (first, second))
            ]
            made = [choice for choice in choices if choice is not None]
            if len(made) == len(choices) and len({_looks(setting, each) for each in made}) == 4:
                correct, *wrong = made
                return multiple_choice((correct,), tuple(wrong))
    raise ValueError("No two mistakes fit the data set.")


def _mistakes(setting: _Setting) -> list[DisplayMistake]:
    """Return every mistake that can be made with the setting's data set."""
    dataset = setting.dataset
    match dataset:
        case CategoricalData():
            return _categorical_mistakes(setting, dataset)
        case NumericalData():
            return _number_line_mistakes(dataset)


def _categorical_mistakes(setting: _Setting, dataset: CategoricalData) -> list[DisplayMistake]:
    """
    Return the mistakes with a categorical data set:
    - two categories' counts switched;
    - one count off by a step of the scale, or half a step when the scale is even (a bar ending
      on a line, a whole symbol for a half), or by 1 or 2 when a dot plot or tally table is
      given or shown, staying above 0 and within what that display holds;
    - a wrong scale, from ``WRONG_SCALES``, when the given or shown display has a scale to
      misread. ``_choice`` keeps only those that leave every count whole;
    - counts between steps of the scale taken as the step below, when the given or shown
      display has a scale and a count between its steps.
    """
    counts, scale = dataset.counts, dataset.scale
    displays = (setting.given, setting.shown)
    has_unit_marks = any(display in UNIT_DISPLAYS for display in displays)
    has_scale = any(display in SCALED_DISPLAYS for display in displays)
    mistakes: list[DisplayMistake] = [
        Swap(first, second) for first, second in combinations(range(len(counts)), 2)
    ]
    smallest_step = scale // 2 if scale % 2 == 0 else scale
    steps = (1, 2) if has_unit_marks else sorted({smallest_step, scale})
    if DataDisplay.DOT_PLOT in displays:
        most = MOST_XS
    elif DataDisplay.TALLY_TABLE in displays:
        most = MOST_TALLIES
    else:
        most = MOST_SYMBOLS * scale
    offs = [
        Off(index, wrong_count)
        for index, count in enumerate(counts)
        for step in steps
        for wrong_count in (count - step, count + step)
        if 0 < wrong_count <= most
    ]
    mistakes += dict.fromkeys(offs)
    if has_scale:
        mistakes += [WrongScale(wrong) for wrong in WRONG_SCALES if wrong != scale]
        if any(count % scale for count in counts):
            mistakes.append(RoundDown())
    return mistakes


def _number_line_mistakes(dataset: NumericalData) -> list[DisplayMistake]:
    """
    Return the mistakes with a list of numbers on a number line, at the numbers the list can hold
    (a topic's possible values, such as coins, or else every tick):
    - two numbers' columns of Xs switched, where their counts differ;
    - one number's count off by 1, from 0 to ``MOST_XS``;
    - one X for each number in the list, if any appears more than once;
    - one X above every number on the line, if any number has none or more than one, and the
      topic has no possible values: on a line of coins' values, a 15-cent coin would give it away.
    """
    counts, ticks = dataset.counts, dataset.ticks
    possible_values = dataset.topic.possible_values or ticks
    possible = [index for index, tick in enumerate(ticks) if tick in possible_values]
    mistakes: list[DisplayMistake] = [
        Swap(first, second)
        for first, second in combinations(possible, 2)
        if counts[first] != counts[second]
    ]
    mistakes += [
        Off(index, wrong_count)
        for index in possible
        for wrong_count in (counts[index] - 1, counts[index] + 1)
        if 0 <= wrong_count <= MOST_XS
    ]
    if max(counts) > 1:
        mistakes.append(OneEach())
    if dataset.topic.possible_values is None and any(count != 1 for count in counts):
        mistakes.append(EveryTick())
    return mistakes


def _apart(first: DisplayMistake, second: DisplayMistake, counts: Sequence[int]) -> bool:
    """Whether two mistakes with ``counts`` change different counts, or one changes them all."""
    return first != second and _indexes(first, counts).isdisjoint(_indexes(second, counts))


def _indexes(mistake: DisplayMistake, counts: Sequence[int]) -> set[int]:
    """
    Return the indexes of ``counts`` a mistake changes on its own: none for one changing every
    count the same way. One X above every number changes the counts other than 1, so the only
    mistake it pairs with is an off count where there's 1 X.
    """
    match mistake:
        case Swap():
            return {mistake.first, mistake.second}
        case Off():
            return {mistake.index}
        case EveryTick():
            return {index for index, count in enumerate(counts) if count != 1}
        case WrongScale() | OneEach() | RoundDown():
            return set()


def _choice(setting: _Setting, mistakes: Sequence[DisplayMistake]) -> DisplayChoice | None:
    """
    Return the choice with ``mistakes`` made, the ones changing single counts first, or ``None``
    if it can't be shown: a wrong scale must leave every count whole, and the counts must fit
    ``_fits``.
    """
    dataset = setting.dataset
    counts = list(dataset.counts)
    scale = dataset.scale if isinstance(dataset, CategoricalData) else 1
    for mistake in sorted(mistakes, key=lambda each: not _indexes(each, dataset.counts)):
        match mistake:
            case Swap():
                counts[mistake.first], counts[mistake.second] = (
                    counts[mistake.second],
                    counts[mistake.first],
                )
            case Off():
                counts[mistake.index] = mistake.count
            case WrongScale():
                if any(count * mistake.scale % scale for count in counts):
                    return None
                counts = [count * mistake.scale // scale for count in counts]
                scale = mistake.scale
            case OneEach():
                counts = [min(count, 1) for count in counts]
            case EveryTick():
                for index in _indexes(mistake, dataset.counts):
                    counts[index] = 1
            case RoundDown():
                counts = [count - count % scale for count in counts]
    if not _fits(setting.dataset, setting.shown, counts, scale):
        return None
    return DisplayChoice(tuple(counts), scale, tuple(mistakes))


def _fits(
    dataset: CategoricalData | NumericalData,
    shown: DataDisplay | None,
    counts: Sequence[int],
    scale: int,
) -> bool:
    """
    Whether ``counts`` on ``scale`` can be shown as ``shown``: a number line's counts are 0 to
    ``MOST_XS``, and a categorical display's are above 0, a dot plot's at most ``MOST_XS``, a
    tally table's at most ``MOST_TALLIES``, a pictograph's at most ``MOST_SYMBOLS`` symbols and a
    bar graph's at most ``MOST_STEPS`` steps.
    """
    if isinstance(dataset, NumericalData):
        return all(0 <= count <= MOST_XS for count in counts)
    most = (
        {
            DataDisplay.DOT_PLOT: MOST_XS,
            DataDisplay.TALLY_TABLE: MOST_TALLIES,
            DataDisplay.PICTOGRAPH: MOST_SYMBOLS * scale,
            DataDisplay.BAR_GRAPH: MOST_STEPS * scale,
        }.get(shown)
        if shown
        else None
    )
    return all(count > 0 and (most is None or count <= most) for count in counts)


def _looks(setting: _Setting, choice: DisplayChoice) -> tuple[object, ...]:
    """Return what a choice looks like: its counts, and its scale if its display shows one."""
    return choice.counts, choice.scale if setting.shown in SCALED_DISPLAYS else None


def wrong_display(
    dataset: CategoricalData, display: DataDisplay, scale: int
) -> DisplayChoice | None:
    """
    Return ``display`` of ``dataset`` on ``scale`` with one mistake, drawn at random from those
    that fit it and change what it shows, its kind first so that none crowds out the others, or
    ``None`` if none does.
    """
    setting = _Setting(replace(dataset, scale=scale), None, display)
    right = _looks(setting, DisplayChoice(dataset.counts, scale, ()))
    choices = [_choice(setting, (mistake,)) for mistake in _mistakes(setting)]
    made = [choice for choice in choices if choice is not None and _looks(setting, choice) != right]
    if not made:
        return None
    kind = random.choice(list(dict.fromkeys(type(choice.mistakes[0]) for choice in made)))
    return random.choice([choice for choice in made if isinstance(choice.mistakes[0], kind)])


def doesnt_match_choices(
    displays: Sequence[ShownDisplay], wrong: int
) -> MultipleChoice[ShownDisplay]:
    """Return ``displays`` to choose from, shuffled, with the one at ``wrong`` the answer."""
    rest = tuple(each for index, each in enumerate(displays) if index != wrong)
    return multiple_choice((displays[wrong],), rest)


def error_choices(data: FindErrorQuestionData) -> MultipleChoice[ErrorChoice]:
    """
    Return four statements of the error to choose from, shuffled. The right one names the wrong
    display, the category or number in error, and its right count.

    With a second display, the statements name either display and either the category in error
    or another, so each display and each category is named twice. Without one, they name either
    category, each with a count it doesn't show: its right count or another. A statement's
    count never matches what its display shows there, so none can be ruled out by the display
    alone.
    """
    dataset = data.dataset
    counts = dataset.counts
    other_index = random.choice(
        [index for index in range(len(counts)) if index != data.index and _readable(data, index)]
    )
    step = _error_step(dataset)
    if data.other is not None:
        statements = [
            ErrorChoice(display, index, _stated_count(data, display, index, step))
            for display in (data.wrong, data.other)
            for index in (data.index, other_index)
        ]
    else:
        statements = [
            ErrorChoice(data.wrong, data.index, data.answer),
            ErrorChoice(data.wrong, data.index, _away(data.answer, data.shown, step)),
            ErrorChoice(data.wrong, other_index, _away(counts[other_index], None, step)),
            ErrorChoice(data.wrong, other_index, _away(counts[other_index], None, -step)),
        ]
    correct, *wrong = statements
    return multiple_choice((correct,), tuple(wrong))


def _readable(data: FindErrorQuestionData, index: int) -> bool:
    """
    Whether the count at ``index`` can carry a stated count a step away from it either way:
    above 0 in a categorical display, and 0 or more on a number line. So a number with no Xs
    isn't named, where both ways would give 1, nor a value the topic can't hold, such as a
    15-cent coin.
    """
    count, step = data.dataset.counts[index], _error_step(data.dataset)
    if isinstance(data.dataset, NumericalData):
        return count >= step
    return count > step


def _error_step(dataset: CategoricalData | NumericalData) -> int:
    """Return how far a wrong count in an error is from the right one: half the scale, or 1."""
    if isinstance(dataset, NumericalData):
        return 1
    return dataset.scale // 2 if dataset.scale % 2 == 0 else dataset.scale


def _stated_count(data: FindErrorQuestionData, display: DataDisplay, index: int, step: int) -> int:
    """
    Return the count a statement gives for ``display`` at ``index``: the right count where the
    display is wrong, so the right statement's, or else a count a step from what it shows.
    """
    shown = data.shown if display is data.wrong and index == data.index else None
    if shown is not None:
        return data.answer
    return _away(data.dataset.counts[index], None, step if random.random() < 0.5 else -step)


def _away(count: int, avoid: int | None, step: int) -> int:
    """Return a count a step from ``count``, the other way if that's ``avoid`` or below 0."""
    for candidate in (count + step, count - step, count + 2 * step):
        if candidate >= 0 and candidate != avoid and candidate != count:
            return candidate
    return count + 3 * abs(step)


def number_choices(
    data: CategoricalDataProblemData | NumericalDataProblemData,
) -> MultipleChoice[int]:
    """
    Return the problem's answer and three wrong numbers, shuffled. The wrong numbers come from
    ``_number_mistakes``, padded with numbers near the answer when they run short.

    The answer's place among the four by size is drawn at random first, from the places it can
    have, so it's as likely to be the smallest or largest as in the middle; only an answer under
    3 has too few numbers, from 0, below it. A draw where the answer is the only choice that's
    the sum or difference of two others is drawn again, a few times at most, as that would point
    it out.
    """
    answer = data.answer
    mistakes = list(dict.fromkeys(_number_mistakes(data)))
    candidates = [number for number in mistakes if number >= 0 and number != answer]
    below = [number for number in candidates if number < answer]
    above = [number for number in candidates if number > answer]
    near = _near(answer, set(candidates))
    lowest_place = min(WRONG_NUMBERS, len(below) + sum(number < answer for number in near))
    for _ in range(8):
        place = random.randint(0, lowest_place)
        lower = random.sample(below, min(place, len(below)))
        lower += [number for number in near if number < answer and number not in lower][
            : place - len(lower)
        ]
        higher = random.sample(above, min(WRONG_NUMBERS - len(lower), len(above)))
        higher += [number for number in near if number > answer and number not in higher][
            : WRONG_NUMBERS - len(lower) - len(higher)
        ]
        wrong = (*lower, *higher)
        if not _points_out(answer, wrong):
            break
    return multiple_choice((answer,), wrong)


def _near(answer: int, taken: set[int]) -> list[int]:
    """Return numbers near the answer, nearest first, and not below 0, nor ``taken``."""
    numbers = []
    for distance in range(1, 4 * WRONG_NUMBERS):
        numbers += [
            number
            for number in (answer - distance, answer + distance)
            if number >= 0 and number not in taken
        ]
    return numbers


def _points_out(answer: int, wrong: Sequence[int]) -> bool:
    """Whether the answer is the only choice that's the sum or difference of two others."""
    choices = (answer, *wrong)

    def related(index: int) -> bool:
        others = [number for position, number in enumerate(choices) if position != index]
        return any(
            choices[index] in (first + second, abs(first - second))
            for first, second in combinations(others, 2)
        )

    return related(0) and not any(related(index) for index in range(1, len(choices)))


def _number_mistakes(data: CategoricalDataProblemData | NumericalDataProblemData) -> list[int]:
    """
    Return the numbers a problem's mistakes give: adding instead of subtracting or the other way,
    one category or number only, stopping after the first step, leaving one out, a count between
    steps of the scale read a step off, the boundary of "or more" or "fewer than" counted or
    left out, or the other side of it, and for a missing number, the listed numbers' total.
    """
    match data:
        case CategoricalDataProblemData():
            return list(_categorical_number_mistakes(data))
        case NumericalDataProblemData():
            return list(_numerical_number_mistakes(data))


def _categorical_number_mistakes(data: CategoricalDataProblemData) -> Iterator[int]:
    counts = data.dataset.counts
    named = [counts[index] for index in data.categories]
    total = sum(counts)
    scale = data.dataset.scale
    step = scale // 2 if scale % 2 == 0 else scale
    answer = data.answer
    match data.problem_type:
        case CategoricalProblemType.MORE | CategoricalProblemType.FEWER:
            first, second = named
            yield from (first + second, first, second, answer + step, answer - step)
        case CategoricalProblemType.PAIR_TOTAL:
            first, second = named
            yield from (first - second, first, second, answer + step, answer - step)
        case CategoricalProblemType.PAIR_MORE:
            first, second, third = named
            yield from (first + second, first - third, second - third, first + second + third)
        case CategoricalProblemType.MORE_THAN_PAIR:
            first, second, third = named
            yield from (first - second, first - third, second + third, first + second + third)
        case CategoricalProblemType.ALL_BUT:
            yield from (total, named[0], answer + step, answer - step)
        case CategoricalProblemType.ALL:
            yield from (total - count for count in counts)
            yield from (total + step, total - step, max(counts))


def _numerical_number_mistakes(data: NumericalDataProblemData) -> Iterator[int]:
    counts = data.dataset.counts
    named = [counts[index] for index in data.tick_indexes]
    answer = data.answer
    match data.problem_type:
        case NumericalProblemType.MORE:
            first, second = named
            yield from (first + second, first, second, answer + 1, answer - 1)
        case NumericalProblemType.PAIR_TOTAL:
            first, second = named
            yield from (abs(first - second), first, second, answer + 1, answer - 1)
        case NumericalProblemType.PAIR_MORE:
            first, second, third = named
            yield from (first + second, first - third, second - third, first + second + third)
        case (
            NumericalProblemType.AT_LEAST
            | NumericalProblemType.AT_MOST
            | NumericalProblemType.MORE_THAN
            | NumericalProblemType.FEWER_THAN
        ):
            threshold = data.tick_indexes[0]
            below, at, above = (
                sum(counts[:threshold]),
                counts[threshold],
                sum(counts[threshold + 1 :]),
            )
            # the boundary counted or left out, the other side, and the count at the boundary
            yield from {
                NumericalProblemType.AT_LEAST: (above, below, below + at, at),
                NumericalProblemType.AT_MOST: (below, above, above + at, at),
                NumericalProblemType.MORE_THAN: (above + at, below, below + at, at),
                NumericalProblemType.FEWER_THAN: (below + at, above, above + at, at),
            }[data.problem_type]
        case NumericalProblemType.MISSING_VALUE:
            listed = sum(data.dataset.values)
            step = data.dataset.ticks[1] - data.dataset.ticks[0]
            yield from (listed, answer + step, answer - step, answer + 2 * step)
