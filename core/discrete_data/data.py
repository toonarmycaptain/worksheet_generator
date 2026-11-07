"""
Question data for data sets: completing one display of a data set from another, and problems
solved from its counts.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from core.question import FreeResponse, Question, QuestionData


class DataDisplay(StrEnum):
    """A way of showing a data set. Values are stable identifiers for the API and storage."""

    TABLE = "table"  # a frequency table: each category beside its count
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
    lines.
    """

    topic: SurveyTopic | FriendsTopic
    categories: tuple[str, ...]
    counts: tuple[int, ...]
    scale: int
    person: str | None


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
    Complete the ``target`` display of ``dataset`` using the ``given`` display, which TEKS 3.8(A)
    calls summarizing a data set.

    ``blanks`` holds the indexes, in ascending order, of the categories or ticks whose counts are
    left out of the target, and ``answer`` holds those counts in the same order. From a list,
    every tick is blank, so the student plots the whole data set.
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


@dataclass(frozen=True)
class NumericalDataProblemData(QuestionData[int]):
    """
    A ``problem_type`` problem solved from ``dataset``'s counts.

    ``tick_indexes`` holds the indexes into ``dataset.ticks`` of the problem's ticks, A, B and C
    in ``NumericalProblemType``, in that order. It holds one index for ``AT_LEAST`` and
    ``AT_MOST``.
    """

    dataset: NumericalData
    problem_type: NumericalProblemType
    tick_indexes: tuple[int, ...]
    answer: int


@dataclass(frozen=True)
class DiscreteDataProblem:
    """
    One data set's three questions: completing a display, then a one-step and a two-step problem
    solved from the counts. Each question holds the data set, so its wording needs nothing else.
    """

    summarize: Question[SummarizeDataQuestionData, FreeResponse]
    one_step: Question[CategoricalDataProblemData | NumericalDataProblemData, FreeResponse]
    two_step: Question[CategoricalDataProblemData | NumericalDataProblemData, FreeResponse]
