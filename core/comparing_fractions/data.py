"""
Data for comparing fractions questions: comparing two fractions with a symbol, with or without a
reason, word problems, ways of shading a fraction less or greater than a model's, drawing two
fractions to compare, and finding the greatest or least of three or four.

Every comparison is of fractions that share a numerator or a denominator.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.fraction_models import answers
from core.fraction_models.area_models import AreaModel, FractionWall
from core.fraction_models.number_lines import FractionLine, LengthUnit
from core.fraction_models.object_groups import ObjectGroup
from core.question import FreeResponse, MultipleChoice, Question, QuestionData
from core.written_numbers import UnreducedFraction

GREATER_THAN, LESS_THAN, EQUAL_TO = ">", "<", "="
MORE, LESS = (
    answers.MORE,
    answers.LESS,
)  # the answers to "did one have more or less than the other?"
SAME = "the same"  # a word problem's answer when both have the same amount
CANT_TELL = "can't tell"  # a word problem's answer when the wholes are different sizes
ALL_OF_THESE = "All of these"  # a choice, right when every other choice is
ALL_OF_THEM, NONE_OF_THEM = "all of them", "none of them"  # the answers to "which of these are"

# A picture of one fraction: a whole cut into parts, a group of objects, or a number line
type Picture = AreaModel | ObjectGroup | FractionLine


class QuestionType(StrEnum):
    """A kind of comparing fractions question. Values are stable identifiers for the API and
    storage."""

    COMPARE = "compare"  # write >, < or =
    EXPLAIN = "explain"  # write the symbol and a reason
    WORD = "word"  # a story of two people's fractions
    LESS_GREATER = "less_greater"  # ways of showing a fraction less or greater than a model's
    DRAW = "draw"  # divide and shade two wholes, then compare
    GREATEST = "greatest"  # the greatest or least of three or four fractions


class Representation(StrEnum):
    """The pictures a question's fractions are shown with. Values are stable identifiers for the
    API and storage."""

    STRIP = "strip"
    GRID = "grid"  # a rectangle cut into rows and columns
    CIRCLE = "circle"  # cut from its centre
    OTHER_SHAPE = "other_shape"  # a regular polygon or a concave octagon cut from its centre
    GROUP = "group"  # of objects
    LINE = "line"  # a number line for each fraction, one above another
    WALL = "wall"  # a fraction wall (fraction strip chart), unlabelled, with the fractions printed
    NONE = "none"  # the fractions alone


class Shared(StrEnum):
    """What two compared fractions have the same. Values are stable identifiers for the API and
    storage."""

    NUMERATOR = "numerator"  # 2/3 and 2/8, and unit fractions such as 1/3 and 1/4
    DENOMINATOR = "denominator"  # 3/8 and 5/8


class StoryKind(StrEnum):
    """What a word problem's two fractions are of. Values are stable identifiers for the API and
    storage."""

    WHOLE = "whole"  # a whole each, the same size: 1/3 of a pie and 1/4 of a pie
    LENGTH = "length"  # a length with a unit: a worm 1/2 foot long and one 2/2 foot long
    GROUP = "group"  # a group of objects each: 3 of 6 blocks painted and 3 of 8


class WordAsked(StrEnum):
    """What a written word problem asks. Values are stable identifiers for the API and
    storage."""

    WHO = "who"  # who has more, then the fractions with >, < or =
    SENTENCE = "sentence"  # a sentence with words to circle


class StoryForm(StrEnum):
    """How a multiple-choice word problem's choices are written. Values are stable identifiers
    for the API and storage."""

    REASONS = "reasons"  # statements with reasons: "Alexis reads more because 1/3 is more than 1/4"
    WHO_SYMBOL = "who_symbol"  # who, by which comparison: "Kayla, because 3/6 > 3/8"
    PLAIN = "plain"  # statements alone: "Worm T is longer."


class ExplainForm(StrEnum):
    """How a compare and explain question is asked. Values are stable identifiers for the API and
    storage."""

    CIRCLE = "circle"  # written: circle the symbol and the reason's words
    WRITE = "write"  # written: write the symbol, then explain on lines
    PAIR = "pair"  # multiple choice: comparisons, each with an explanation
    WHY = "why"  # multiple choice: the true comparison given, reasons to choose from


class LessGreaterForm(StrEnum):
    """How a less or greater than a model question is asked. Values are stable identifiers for
    the API and storage."""

    DIVIDE = "divide"  # written: divide and shade blank wholes
    CIRCLE = "circle"  # written: circle every model, of four, that is less (or greater)
    WRITE = "write"  # written: write a fraction less (or greater)
    NOT_A_WAY = "not_a_way"  # multiple choice: which is NOT a way
    SHOWS = "shows"  # multiple choice: which model shows a fraction less (or greater)


class DrawAsked(StrEnum):
    """What a draw and compare question asks after the drawing. Values are stable identifiers
    for the API and storage."""

    SYMBOL = "symbol"  # >, < or =
    GREATER = "greater"  # which fraction is greater
    LESS = "less"  # which fraction is less


@dataclass(frozen=True)
class Comparison:
    """``left`` compared with ``right`` by ``symbol``, >, < or =, true or not: "2/4 > 2/6"."""

    left: UnreducedFraction
    symbol: str
    right: UnreducedFraction


# --- reasons


@dataclass(frozen=True)
class PartSize:
    """A reason about part sizes: "sixths are larger than eighths", parts of ``first`` and of
    ``second`` equal parts, larger or not. Read from numerators, it's a mistake: "6/8 < 8/8,
    because sixths are smaller than eighths"."""

    first: int
    second: int
    larger: bool


@dataclass(frozen=True)
class PartsOf:
    """A reason counting parts: "6 out of 8 parts is less than 8 out of 8 parts", ``first``
    compared with ``second``, greater or not."""

    first: UnreducedFraction
    second: UnreducedFraction
    greater: bool


@dataclass(frozen=True)
class BiggerNumber:
    """A mistaken reason comparing denominators as numbers: "3 is less than 4", ``first``
    compared with ``second``, greater or not."""

    first: int
    second: int
    greater: bool


@dataclass(frozen=True)
class SameCount:
    """A mistaken reason for "=": each model has ``count`` parts shaded, or with ``total``, has
    ``count`` equal parts in all."""

    count: int
    total: bool
    pictured: bool  # "each model has", or "both have"


type Reason = PartSize | PartsOf | BiggerNumber | SameCount


@dataclass(frozen=True)
class Explanation:
    """A comparison with a reason, true or not: "5/6 > 5/8, because sixths are larger than
    eighths"."""

    comparison: Comparison
    reason: Reason


# --- word problem choices


class Verdict(StrEnum):
    """What a word problem's statement says. Values are stable identifiers for the API and
    storage."""

    AHEAD = "ahead"  # one person has more, or a longer length
    SAME = "same"  # both have the same
    CANT_TELL = "cant_tell"  # there's not enough information


class StoryReason(StrEnum):
    """The reason a word problem's statement gives. Values are stable identifiers for the API and
    storage."""

    NONE = "none"  # a plain statement
    FRACTION = "fraction"  # "because 1/3 of the book is more than 1/4"
    PART_SIZE = "part_size"  # "because thirds are larger than fourths"
    DENOMINATOR = "denominator"  # "because a denominator of 4 is larger than a denominator of 3"
    SAME_WHOLE = "same_whole"  # "because they are reading the same book"
    SAME_NUMERATOR = "same_numerator"  # "because both fractions have a numerator of 1"
    EQUAL = "equal"  # "because 1/4 is equal to 1/3"


@dataclass(frozen=True)
class Pick:
    """A choice naming one of two fractions with the comparison that picks it: "2/3, because
    2/3 > 2/4", true or not."""

    fraction: UnreducedFraction
    claim: Comparison


@dataclass(frozen=True)
class StoryChoice:
    """
    A word problem's statement: ``who`` comes out ahead, with ``verdict`` AHEAD, else ``None``,
    and ``reason`` why; a FRACTION reason claims ``who``'s fraction is the greater, as the
    statement's ``claim`` compares them. A ``brief`` statement, the who-and-symbol form, is the
    name and ``claim`` alone, the answer to the question it follows: "Kayla, because 3/6 > 3/8".
    """

    verdict: Verdict
    who: str | None
    reason: StoryReason
    claim: Comparison | None = None
    brief: bool = False


# --- questions


@dataclass(frozen=True)
class CompareQuestionData(QuestionData[str]):
    """
    Asks to compare ``fractions`` with >, < or =: ``answer``. ``pictures`` show them, one each,
    the same shape and size, for the student to read and write; or a ``wall`` is shown with them
    printed; or neither. As multiple choice, the choices are comparisons, written in words with
    ``in_words``: "2/3 is greater than 2/8".
    """

    fractions: tuple[UnreducedFraction, UnreducedFraction]
    pictures: tuple[Picture, ...]
    wall: FractionWall | None
    in_words: bool
    answer: str


@dataclass(frozen=True)
class EveryQuestionData(QuestionData[tuple[UnreducedFraction, ...]]):
    """
    Asks which of ``fractions`` are greater than ``target``, or less with ``greater`` false:
    ``answer``, those that are, in order. Each shares a numerator or a denominator with
    ``target``. Written, the student circles them; as multiple choice, the choices are the
    fractions and "All of these"; on a tiles sheet, the answer is "all of them" or "none of
    them".
    """

    target: UnreducedFraction
    greater: bool
    fractions: tuple[UnreducedFraction, ...]
    answer: tuple[UnreducedFraction, ...]


@dataclass(frozen=True)
class ExplainQuestionData(QuestionData[Explanation]):
    """
    Asks to compare ``fractions`` and say why: ``answer``, the true comparison with its reason.
    ``pictures`` or a ``wall`` show them, as for a compare question, or neither. It's asked in
    ``form``: written, the student circles the symbol and the reason's words, or writes the
    symbol and explains; as multiple choice, the choices are explanations, their comparisons
    written in words with ``in_words``, or the comparison is given and the choices are reasons.
    """

    fractions: tuple[UnreducedFraction, UnreducedFraction]
    pictures: tuple[Picture, ...]
    wall: FractionWall | None
    in_words: bool
    form: ExplainForm
    answer: Explanation


@dataclass(frozen=True)
class WordQuestionData(QuestionData[str]):
    """
    A story of ``names`` having ``fractions``, in order, of the bank's story ``story`` of
    ``kind``: wholes the same size, unless they have ``sizes``, "small" and "large" in the names'
    order, lengths in ``unit``, or groups of as many objects as each fraction's parts. The
    question asks who has the greater share, or the smaller with
    ``greater`` false, or with ``more_or_less``, whether the first has more or less than the
    second. ``answer`` is a name, "the same", "can't tell", or "more" or "less". ``pictures``,
    if any, draw the two wholes, lengths or groups. A written problem asks ``asked``; a
    multiple-choice one has its statements in ``form``, else ``None``.
    """

    kind: StoryKind
    story: int  # its position in its kind's bank
    names: tuple[str, str]
    fractions: tuple[UnreducedFraction, UnreducedFraction]
    unit: LengthUnit | None
    sizes: tuple[str, str] | None
    greater: bool
    more_or_less: bool
    asked: WordAsked
    form: StoryForm | None
    pictures: tuple[Picture, ...]
    answer: str


@dataclass(frozen=True)
class LessGreaterQuestionData(QuestionData[tuple[UnreducedFraction, ...]]):
    """
    Shows ``model``, a whole with ``fraction`` shaded, and asks about ways of dividing and
    shading a whole to show a fraction less than ``fraction``, or greater with ``greater``, each
    a fraction (shaded parts, parts) sharing its numerator or denominator, as ``form`` asks:

    - divide and shade wholes like ``blank``, uncut: ``answer`` gives three ways;
    - circle every one of ``pictures``, four wholes cut and shaded as ``model`` is, that's a
      way: ``answer`` is the ways among them, in order;
    - write a way: ``answer`` is every way; those over ``fraction``'s denominator are asked for
      with the same denominator, the rest with the same numerator;
    - as multiple choice, which is NOT a way, or which shows one: the choices are wholes cut and
      shaded as ``model`` is, and ``answer`` is the fraction the right one shows.
    """

    fraction: UnreducedFraction
    greater: bool
    form: LessGreaterForm
    model: AreaModel
    blank: Picture
    pictures: tuple[AreaModel, ...]
    answer: tuple[UnreducedFraction, ...]


@dataclass(frozen=True)
class DrawQuestionData(QuestionData[str]):
    """
    Asks to divide and shade ``blanks``, two wholes the same size, uncut, or mark two number
    lines, to show ``fractions``, then compare them: with ``asked`` SYMBOL, with >, < or =, the
    symbol ``answer``; else which fraction is greater, or less, as ``answer`` compares them. As
    multiple choice, the choices are comparisons, or each fraction picked with the comparison
    true or flipped: "2/3, because 2/3 > 2/4".
    """

    fractions: tuple[UnreducedFraction, UnreducedFraction]
    blanks: tuple[Picture, Picture]
    asked: DrawAsked
    answer: str


@dataclass(frozen=True)
class GreatestQuestionData(QuestionData[UnreducedFraction]):
    """
    Asks which of ``fractions``, two to four sharing a numerator or a denominator, is the
    greatest, or the least with ``greatest`` false: ``answer``. Two are asked as "Which is
    greater?". ``pictures`` or a ``wall`` show them, or neither.
    """

    fractions: tuple[UnreducedFraction, ...]
    greatest: bool
    pictures: tuple[Picture, ...]
    wall: FractionWall | None
    answer: UnreducedFraction


# Each kind of question as presented. A compare question's choices are comparisons; a draw
# question's comparisons, or fractions picked with comparisons; an every question's fractions
# and "All of these"; an explain question's explanations, or reasons; a word problem's
# statements; a less or greater question's ways, as pictures; a greatest question's fractions,
# or with pictures, the pictures.
type CompareQuestion = Question[CompareQuestionData, FreeResponse | MultipleChoice[Comparison]]
type EveryQuestion = Question[
    EveryQuestionData, FreeResponse | MultipleChoice[UnreducedFraction | str]
]
type ExplainQuestion = Question[
    ExplainQuestionData, FreeResponse | MultipleChoice[Explanation] | MultipleChoice[Reason]
]
type WordQuestion = Question[WordQuestionData, FreeResponse | MultipleChoice[StoryChoice]]
type LessGreaterQuestion = Question[
    LessGreaterQuestionData, FreeResponse | MultipleChoice[AreaModel]
]
type DrawQuestion = Question[
    DrawQuestionData, FreeResponse | MultipleChoice[Comparison] | MultipleChoice[Pick]
]
type GreatestQuestion = Question[
    GreatestQuestionData, FreeResponse | MultipleChoice[UnreducedFraction | Picture]
]

type ComparingFractionsQuestionData = (
    CompareQuestionData
    | EveryQuestionData
    | ExplainQuestionData
    | WordQuestionData
    | LessGreaterQuestionData
    | DrawQuestionData
    | GreatestQuestionData
)
# Any question on a comparing fractions sheet
type ComparingFractionsQuestion = (
    CompareQuestion
    | EveryQuestion
    | ExplainQuestion
    | WordQuestion
    | LessGreaterQuestion
    | DrawQuestion
    | GreatestQuestion
)
