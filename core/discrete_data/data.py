"""
Question data for data sets: completing or choosing another display of a data set, reading its
counts, finding an error in a display of it, choosing the display that doesn't show it, and
problems solved from its counts.
"""

from dataclasses import dataclass, replace
from enum import StrEnum

from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from core.question import FreeResponse, MultipleChoice, Question, QuestionData


class DataDisplay(StrEnum):
    """A way of showing a data set. Values are stable identifiers for the API and storage."""

    TABLE = "table"  # a frequency table: each category beside its count
    TALLY_TABLE = "tally_table"  # each category beside tally marks, in groups of five
    PICTOGRAPH = "pictograph"  # a row of symbols per category, each worth the data set's scale
    BAR_GRAPH = "bar_graph"  # a bar per category, on an axis with scaled intervals
    DOT_PLOT = "dot_plot"  # a column of Xs per category, each worth 1
    LIST = "list"  # a numerical data set's numbers, in order
    NUMBER_LINE_DOT_PLOT = "number_line_dot_plot"  # an X above a number line for each number


@dataclass(frozen=True)
class CategoricalData:
    """
    A data set of categories and their counts: ``counts[i]`` is the count of ``categories[i]``.

    For a ``SurveyTopic``, the categories are the choices, such as "apples", and ``person`` is
    the name of the person who asked. For a ``FriendsTopic``, the categories are the friends'
    names, and ``person`` is ``None``.

    ``scale`` is the value of one pictograph symbol and the interval between a bar graph's grid
    lines. ``horizontal_bars`` is whether a bar graph of it has its bars across, from an axis on
    the left, rather than up.
    """

    topic: SurveyTopic | FriendsTopic
    categories: tuple[str, ...]
    counts: tuple[int, ...]
    scale: int
    person: str | None
    horizontal_bars: bool = False


@dataclass(frozen=True)
class NumericalData:
    """
    A data set of numbers, one per data point, such as the number of students in each class.

    ``values`` holds the numbers in the order they are listed. ``ticks`` holds the numbers on the
    number line they are plotted on, which can include numbers absent from ``values``.
    ``person`` is the name in the topic's introduction.
    """

    topic: NumberListTopic
    values: tuple[int, ...]
    ticks: tuple[int, ...]
    person: str

    @property
    def counts(self) -> tuple[int, ...]:
        """How often each tick occurs in ``values``: ``counts[i]`` is the count of ``ticks[i]``."""
        return tuple(self.values.count(tick) for tick in self.ticks)


@dataclass(frozen=True)
class SummarizeDataQuestionData(QuestionData[tuple[int, ...]]):
    """
    Summarize ``dataset``: complete the ``target`` display using the ``given`` display, or choose
    it.

    ``blanks`` holds the indexes, in ascending order, of the categories or ticks whose counts are
    left out of the target, and ``answer`` holds those counts in the same order. From a list,
    every tick is blank, so the student plots the whole data set. A display to choose has every
    count blank, as its choices show them all.
    """

    dataset: CategoricalData | NumericalData
    given: DataDisplay
    target: DataDisplay
    blanks: tuple[int, ...]
    answer: tuple[int, ...]


class CategoricalProblemType(StrEnum):
    """
    A problem solved from a categorical data set's counts, where A, B and C are the problem's
    categories, in order. Values are stable identifiers for the API and storage.
    """

    # one-step
    MORE = "more"  # how many more A than B: A - B
    FEWER = "fewer"  # how many fewer B than A: A - B
    PAIR_TOTAL = "pair_total"  # how many A or B, or A and B in all: A + B
    # two-step
    PAIR_MORE = "pair_more"  # how many more A and B together than C: A + B - C
    MORE_THAN_PAIR = "more_than_pair"  # how many more A than B and C together: A - (B + C)
    ALL_BUT = "all_but"  # how many not A: the total - A
    ALL = "all"  # how many in all: the total


@dataclass(frozen=True)
class CategoricalDataProblemData(QuestionData[int]):
    """
    A ``problem_type`` problem solved from ``dataset``'s counts.

    ``categories`` holds the indexes of the problem's categories, A, B and C in
    ``CategoricalProblemType``, in that order. It holds one index for ``ALL_BUT`` and none for
    ``ALL``.
    """

    dataset: CategoricalData
    problem_type: CategoricalProblemType
    categories: tuple[int, ...]
    answer: int


class NumericalProblemType(StrEnum):
    """
    A problem solved from a numerical data set's counts, where A, B and C are the problem's ticks,
    in order, and a tick's count is how many numbers in the list equal it. Values are stable
    identifiers for the API and storage.
    """

    # one-step
    MORE = "more"  # how many more have A than have B: A - B
    PAIR_TOTAL = "pair_total"  # how many have A or B: A + B
    # two-step
    PAIR_MORE = "pair_more"  # how many more have A or B than have C: A + B - C
    AT_LEAST = "at_least"  # how many have A or more: the counts from A up
    AT_MOST = "at_most"  # how many have A or fewer: the counts up to A
    MORE_THAN = "more_than"  # how many have more than A: the counts above A
    FEWER_THAN = "fewer_than"  # how many have fewer than A: the counts below A
    # the number missing from the list, from the total of all its numbers: the total less the
    # sum of the numbers listed
    MISSING_VALUE = "missing_value"


@dataclass(frozen=True)
class NumericalDataProblemData(QuestionData[int]):
    """
    A ``problem_type`` problem solved from ``dataset``'s counts.

    ``tick_indexes`` holds the indexes into ``dataset.ticks`` of the problem's ticks, A, B and C
    in ``NumericalProblemType``, in that order. It holds one index for ``AT_LEAST``,
    ``AT_MOST``, ``MORE_THAN`` and ``FEWER_THAN``, and none for ``MISSING_VALUE``, whose
    ``total`` is the sum of the listed numbers and the missing one, its answer.
    """

    dataset: NumericalData
    problem_type: NumericalProblemType
    tick_indexes: tuple[int, ...]
    answer: int
    total: int | None = None


@dataclass(frozen=True)
class ReadCountsQuestionData(QuestionData[tuple[int, ...]]):
    """
    Read ``dataset``'s counts from its ``given`` display: a categorical data set's counts, in the
    order of its categories, or a numerical data set's numbers, from least to greatest, from a
    number-line dot plot.
    """

    dataset: CategoricalData | NumericalData
    given: DataDisplay
    answer: tuple[int, ...]


@dataclass(frozen=True)
class FindErrorQuestionData(QuestionData[int]):
    """
    Find the error in the ``wrong`` display of ``dataset``: it shows the count at ``index`` as
    ``shown`` instead of ``answer``.

    ``source`` gives the right data: a table, or a list for a numerical data set, or ``None``
    when the problem's introduction states the counts. ``other`` is a second display of the data,
    without the error, to choose between, or ``None``.
    """

    dataset: CategoricalData | NumericalData
    source: DataDisplay | None
    wrong: DataDisplay
    other: DataDisplay | None
    index: int
    shown: int
    answer: int


@dataclass(frozen=True)
class ErrorChoice:
    """
    A statement of a display's error, to choose: "``display``, because ``index``'s count should
    be ``count``".
    """

    display: DataDisplay
    index: int
    count: int


@dataclass(frozen=True)
class Swap:
    """A mistake: two categories' or numbers' counts switched, at indexes ``first`` and
    ``second``."""

    first: int
    second: int


@dataclass(frozen=True)
class Off:
    """A mistake: the count at ``index`` shown as ``count``."""

    index: int
    count: int


@dataclass(frozen=True)
class WrongScale:
    """
    A mistake: the counts on ``scale`` instead of the data set's. A pictograph or bar graph shows
    the right picture with the wrong key or axis; a table or dot plot shows the counts the given
    pictograph or bar graph would have on ``scale``.
    """

    scale: int


@dataclass(frozen=True)
class OneEach:
    """A mistake: one X for each number in a list, however often it appears."""


@dataclass(frozen=True)
class EveryTick:
    """
    A mistake: one X above every number on the number line, whether it's in the list or not, as
    when a list of every number on the line is taken for the data.
    """


@dataclass(frozen=True)
class RoundDown:
    """
    A mistake: each count between two steps of the scale taken as the step below, as when a bar
    ending between grid lines is read at the line below, or a half symbol isn't counted.
    """


# A wrong display choice's mistake. Counts are in the order of the data set's categories or
# ticks.
type DisplayMistake = Swap | Off | WrongScale | OneEach | EveryTick | RoundDown


@dataclass(frozen=True)
class DisplayChoice:
    """
    A display to choose: its question's target display drawn with ``counts``, in the order of the
    data set's categories or ticks, and ``scale``, which only a pictograph or bar graph shows.

    ``mistakes`` are what make a wrong choice wrong, and the correct choice has none. A numerical
    data set's scale is 1.
    """

    counts: tuple[int, ...]
    scale: int
    mistakes: tuple[DisplayMistake, ...]


def chosen_data(
    dataset: CategoricalData | NumericalData, choice: DisplayChoice
) -> CategoricalData | NumericalData:
    """Return ``dataset`` as ``choice`` shows it: with the choice's counts, and scale if any."""
    match dataset:
        case CategoricalData():
            return replace(dataset, counts=choice.counts, scale=choice.scale)
        case NumericalData():
            pairs = zip(dataset.ticks, choice.counts, strict=True)
            return replace(
                dataset, values=tuple(tick for tick, count in pairs for _ in range(count))
            )


@dataclass(frozen=True)
class ShownDisplay:
    """A display of a data set, drawn as ``choice`` gives it: one of the displays to choose from
    that don't all show the data."""

    display: DataDisplay
    scale: int  # the display's right scale, which a wrong scale's choice doesn't show
    choice: DisplayChoice


@dataclass(frozen=True)
class DoesntMatchQuestionData(QuestionData[ShownDisplay]):
    """
    Choose the display that doesn't show ``dataset``, whose right data ``source`` gives: a table,
    or ``None`` when the problem's introduction states the counts. ``answer`` is that display,
    whose choice has a mistake.
    """

    dataset: CategoricalData
    source: DataDisplay | None
    answer: ShownDisplay


class DiscreteDataPart(StrEnum):
    """A question asked about a data set. Values are stable identifiers for the API and storage."""

    ANOTHER_DISPLAY = "another_display"  # complete another display of the data set, or choose it
    READ_COUNTS = "read_counts"  # write its counts, or choose the list of them
    FIND_ERROR = "find_error"  # find the error in a display of it
    DOESNT_MATCH = "doesnt_match"  # choose the display that doesn't show it
    ONE_STEP = "one_step"  # a one-step problem solved from the counts
    TWO_STEP = "two_step"  # a two-step problem solved from the counts


type SummarizeData = (
    SummarizeDataQuestionData
    | ReadCountsQuestionData
    | FindErrorQuestionData
    | DoesntMatchQuestionData
)
type SummarizeResponse = (
    FreeResponse
    | MultipleChoice[DisplayChoice]
    | MultipleChoice[ErrorChoice]
    | MultipleChoice[ShownDisplay]
)
type DataProblemQuestion = Question[
    CategoricalDataProblemData | NumericalDataProblemData, FreeResponse | MultipleChoice[int]
]


@dataclass(frozen=True)
class DiscreteDataProblem:
    """
    One data set and the questions asked about it: first one summarizing it (completing or
    choosing another display, reading its counts, finding an error, or choosing the display that
    doesn't show it), then a one-step and a two-step problem solved from the counts. Any of the
    three can be left out.

    ``given`` is the display the problems are read from, which is shown regardless, or ``None``
    when the introduction states the counts. Each question holds the data set, so its wording
    needs nothing else.
    """

    dataset: CategoricalData | NumericalData
    given: DataDisplay | None
    summarize: Question[SummarizeData, SummarizeResponse] | None
    one_step: DataProblemQuestion | None
    two_step: DataProblemQuestion | None

    @property
    def word_problems(self) -> tuple[DataProblemQuestion, ...]:
        """The one-step and two-step problems asked, in that order."""
        return tuple(question for question in (self.one_step, self.two_step) if question)
