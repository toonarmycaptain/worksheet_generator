"""
Data for fractions on a number line questions: naming and marking points, stories of a distance
from a start, dividing a line into equal parts, and comparing two distances on one line.
"""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from core.fraction_models.number_lines import FractionLine, LengthUnit
from core.question import FreeResponse, MultipleChoice, Question, QuestionData
from core.written_numbers import UnreducedFraction

NONE_OF_THESE = "None of these"  # a choice, right when no other choice is
MORE, LESS = "more", "less"  # the answers to "did one go more or less than the other?"
GREATER_THAN, LESS_THAN = ">", "<"


class QuestionType(StrEnum):
    """A kind of fractions on a number line question. Values are stable identifiers for the API
    and storage."""

    NAME = "name"  # what fraction a point shows
    MARK = "mark"  # mark and label a fraction
    DISTANCE = "distance"  # a story of a distance from a start
    DIVIDE = "divide"  # divide a line showing only 0 and 1, then mark a fraction
    COMPARE = "compare"  # two distances on one line: who went farther


class DistanceAsked(StrEnum):
    """What a written distance story asks. Values are stable identifiers for the API and
    storage."""

    MARK = "mark"  # the story gives the distance: mark the point
    HOW_FAR = "how_far"  # the point is marked: how far is it from the start


class Compared(StrEnum):
    """What a story of two distances asks. Values are stable identifiers for the API and
    storage."""

    FARTHER = "farther"  # who went farther
    SHORTER = "shorter"  # who went a shorter distance
    MORE_OR_LESS = "more_or_less"  # did the first go more or less than the second


@dataclass(frozen=True)
class Comparison:
    """A comparison as a choice: ``word``, a name, "more" or "less", then ``left``, ``symbol``
    and ``right``: "Ben, 5/8 > 3/8"."""

    word: str
    left: UnreducedFraction
    symbol: str  # GREATER_THAN or LESS_THAN
    right: UnreducedFraction


@dataclass(frozen=True)
class NamePointQuestionData(QuestionData[UnreducedFraction]):
    """Asks what fraction the point on ``line`` shows: ``answer``, over the line's parts."""

    line: FractionLine
    answer: UnreducedFraction


@dataclass(frozen=True)
class MarkPointQuestionData(QuestionData[FractionLine]):
    """
    Asks to mark and label ``fraction`` on ``line``, which has no points: ``answer`` is the line
    with the point marked. As multiple choice, the choices are points on the line, by how far
    along it each is, which can be between ticks.
    """

    fraction: UnreducedFraction
    line: FractionLine
    answer: FractionLine


@dataclass(frozen=True)
class DistanceQuestionData(QuestionData[UnreducedFraction]):
    """
    A story of ``name`` going ``distance`` ``unit`` from a start, a distance as the story says
    it: ``story`` is the bank's story. With ``asked`` how far, ``line`` shows where they stopped,
    a point lettered with the name's first letter, and the question asks how far that is; asked
    to mark it, the question gives the distance, and ``line`` shows only the start. ``answer`` is
    the point as the line's parts write it: 2/4 for 1/2 mile on a line in fourths.
    """

    story: int  # its position in the bank
    name: str
    unit: LengthUnit
    asked: DistanceAsked
    distance: UnreducedFraction
    line: FractionLine
    answer: UnreducedFraction


@dataclass(frozen=True)
class DivideQuestionData(QuestionData[FractionLine]):
    """
    Asks to divide ``line``, which shows only 0 and 1, into ``fraction``'s denominator of equal
    parts, then mark and label ``fraction``: ``answer`` is the line divided, with the point
    marked.
    """

    fraction: UnreducedFraction
    line: FractionLine
    answer: FractionLine


@dataclass(frozen=True)
class CompareQuestionData(QuestionData[str]):
    """
    A story of ``names`` going ``distances`` ``unit`` from a start, in the same parts: ``story``
    is the bank's story. The question asks to mark both points on ``line``, which shows only the
    start, each lettered with its name's first letter, then asks ``compared``: ``answer`` is a
    name, or "more" or "less".
    """

    story: int  # its position in the bank
    names: tuple[str, str]
    unit: LengthUnit
    distances: tuple[UnreducedFraction, UnreducedFraction]
    compared: Compared
    line: FractionLine
    answer: str


# Each kind of question as presented. A name question's choices are fractions, and may end with
# NONE_OF_THESE; a mark question's are points on its line, by how far along it each is; a
# distance or divide question's are lines; a compare question's are comparisons.
type NamePointQuestion = Question[
    NamePointQuestionData, FreeResponse | MultipleChoice[UnreducedFraction | str]
]
type MarkPointQuestion = Question[
    MarkPointQuestionData, FreeResponse | MultipleChoice[Fraction | str]
]
type DistanceQuestion = Question[DistanceQuestionData, FreeResponse | MultipleChoice[FractionLine]]
type DivideQuestion = Question[DivideQuestionData, FreeResponse | MultipleChoice[FractionLine]]
type CompareQuestion = Question[CompareQuestionData, FreeResponse | MultipleChoice[Comparison]]

type FractionNumberLinesQuestionData = (
    NamePointQuestionData
    | MarkPointQuestionData
    | DistanceQuestionData
    | DivideQuestionData
    | CompareQuestionData
)
# Any question on a fractions on a number line sheet
type FractionNumberLinesQuestion = (
    NamePointQuestion | MarkPointQuestion | DistanceQuestion | DivideQuestion | CompareQuestion
)
