"""
Data for order of operations questions: STAAR's ways of asking about simplifying an expression
(its value, an equivalent step, which expression has a value, the first operation, what the
parentheses indicate, where a worked simplification goes wrong), and forms of some of them whose
answer is a number the question doesn't print, for self-check tiles.
"""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from core.arithmetic_expressions.data import Expression, NumberValue
from core.arithmetic_expressions.evaluation import Path
from core.arithmetic_expressions.random_expressions import NumberKind
from core.basic_operations.data import Operation
from core.question import FreeResponse, MultipleChoice, Question, QuestionData


class QuestionType(StrEnum):
    """
    A kind of question on an order of operations sheet. Each is asked written or as multiple
    choice, and some in a form for self-check tiles. Values are stable identifiers for the API
    and storage.
    """

    VALUE = "value"  # the value of an expression
    NEXT_STEP = "next_step"  # an expression equivalent to it, one or two of them
    HAS_VALUE = "has_value"  # which expression has a value, or does not
    FIRST_OPERATION = "first_operation"  # the operation performed first, and why
    PARENTHESES = "parentheses"  # what the parentheses indicate
    FIND_ERROR = "find_error"  # the step where a worked simplification first goes wrong


# The types a self-check tiles sheet asks, in forms whose answer is a number the question doesn't
# print
TILE_TYPES = (
    QuestionType.VALUE,
    QuestionType.NEXT_STEP,
    QuestionType.HAS_VALUE,
    QuestionType.FIRST_OPERATION,
)


class GroupSymbols(StrEnum):
    """
    How a sheet writes a group with a group inside it. Values are stable identifiers for the API
    and storage.
    """

    BRACKETS = "brackets"  # [(9 - 5) x (3 + 7)], as STAAR writes it
    PARENTHESES = "parentheses"  # ((9 - 5) x (3 + 7))
    MIXED = "mixed"  # each expression one way or the other


@dataclass(frozen=True)
class SheetSettings:
    """
    What a sheet's expressions may be: how deeply their groups nest, ``levels``, each problem's
    drawn from those given; the kinds of number, ``numbers``; how a group with a group inside is
    written, ``symbols``; whether a multiplication may leave out its sign, ``implied``; and the
    largest number written, and the largest multiplier or divisor.
    """

    levels: tuple[int, ...] = (1, 2)
    numbers: tuple[NumberKind, ...] = tuple(NumberKind)
    symbols: GroupSymbols = GroupSymbols.BRACKETS
    implied: bool = True
    largest_number: int = 50
    largest_multiplier: int = 12


@dataclass(frozen=True)
class Pair:
    """
    Two numbers and the operation between them, as written next to each other, such as 72 - 6.
    They needn't be one calculation of the expression: 2 + 4 in 6[(1 x 2) + (4 x 2)] is a pair.
    """

    left: NumberValue
    operation: Operation
    right: NumberValue


@dataclass(frozen=True)
class Improper:
    """A fraction written improper, 11/4, as STAAR writes the wrong answer it comes from."""

    value: Fraction


# A value as an option: written as a value is, or an improper fraction
type ValueOption = NumberValue | Improper


@dataclass(frozen=True)
class ValueQuestionData(QuestionData[NumberValue]):
    """
    Asks for the value of ``expression``: ``answer``. ``brackets`` writes a group with a group
    inside in brackets, else in parentheses.
    """

    expression: Expression
    brackets: bool
    answer: NumberValue


@dataclass(frozen=True)
class NextStepQuestionData(QuestionData[tuple[Expression, ...]]):
    """
    Asks for an expression equivalent to ``expression``, later in its working: ``answer``.

    Without ``shown``, it asks for one: written, the step after it, either of those in
    ``answer`` (one operation worked, or all those that may be worked next together); with
    lettered choices, one of them. With ``shown``, five expressions in order, it asks for the two
    in ``answer``, lines of its working, circled or chosen.
    """

    expression: Expression
    brackets: bool
    answer: tuple[Expression, ...]
    shown: tuple[Expression, ...] = ()


@dataclass(frozen=True)
class StepBlankQuestionData(QuestionData[NumberValue]):
    """
    Shows ``expression`` equal to ``step``, a line of its working, with the number at ``blank``
    in ``step`` left out; the student finds it: ``answer``. For self-check tiles.
    """

    expression: Expression
    brackets: bool
    step: Expression
    blank: Path
    answer: NumberValue


@dataclass(frozen=True)
class HasValueQuestionData(QuestionData[Expression]):
    """
    Asks which of ``expressions``, in order, has a value of ``target``, or with ``has`` off,
    which does not: ``answer``. Each of the others comes to the value its look asks about only
    by a common mistake.
    """

    expressions: tuple[Expression, ...]
    target: NumberValue
    has: bool
    brackets: bool
    answer: Expression


@dataclass(frozen=True)
class ValueCountQuestionData(QuestionData[int]):
    """
    Asks how many of ``expressions`` have a value of ``target``: ``answer``. Each of the others
    comes to it by a common mistake. For self-check tiles.
    """

    expressions: tuple[Expression, ...]
    target: NumberValue
    brackets: bool
    answer: int


class Why(StrEnum):
    """
    A reason given for performing an operation first. Values are stable identifiers for the API
    and storage.
    """

    IN_PARENTHESES = "in_parentheses"  # because the operation in the parentheses...
    IN_BRACKETS = "in_brackets"  # because the operation in the brackets...
    MULTIPLYING_FIRST = "multiplying_first"  # because x and ÷ come before + and -
    LEFT_TO_RIGHT = "left_to_right"  # because it is the first operation reading left to right
    RIGHT_TO_LEFT = "right_to_left"  # because it is the first reading right to left
    BEFORE = "before"  # because one operation should be performed before another


@dataclass(frozen=True)
class FirstChoice:
    """
    An operation said to be performed first, ``pair``, and why. A ``Why.BEFORE`` reason says the
    pair's operation comes before ``over``: "because multiplication should be performed before
    addition".
    """

    pair: Pair
    why: Why
    over: Operation | None = None


@dataclass(frozen=True)
class FirstOperationQuestionData(QuestionData[FirstChoice]):
    """Asks which operation is performed first in ``expression``, and why: ``answer``."""

    expression: Expression
    brackets: bool
    answer: FirstChoice


@dataclass(frozen=True)
class FirstResultQuestionData(QuestionData[NumberValue]):
    """
    Asks what number the operation performed first in ``expression``, ``pair``, gives:
    ``answer``. For self-check tiles.
    """

    expression: Expression
    brackets: bool
    pair: Pair
    answer: NumberValue


@dataclass(frozen=True)
class Then:
    """
    What is done after a first operation: ``operation`` with ``number``, the first result on its
    left with ``result_left``. "multiplying by 4", "subtracting the sum from 72".
    """

    operation: Operation
    number: NumberValue
    result_left: bool


@dataclass(frozen=True)
class Order:
    """A statement that ``first`` is done before ``then``: "Subtract 6 from 72 before ..."."""

    first: Pair
    then: Pair | Then


@dataclass(frozen=True)
class Timing:
    """
    A statement that the parentheses indicate ``pair`` should be solved first, or with ``first``
    off, last.
    """

    pair: Pair
    first: bool


type Statement = Order | Timing


@dataclass(frozen=True)
class ParenthesesQuestionData(QuestionData[Statement]):
    """
    Asks what the parentheses in ``expression``, its only group, indicate: ``answer``. An
    ``Order`` answers "What do these parentheses indicate?", and a ``Timing``, "Which statement
    is true about the parentheses?"; a written question always asks the first.
    """

    expression: Expression
    brackets: bool
    answer: Statement


@dataclass(frozen=True)
class ErrorChoice:
    """
    A step said to hold the error, ``step``, counting from 1, and why: ``pairs`` should have
    been simplified first, or with ``equals``, the one pair comes to ``equals``, which the step
    doesn't show.
    """

    step: int
    pairs: tuple[Pair, ...]
    equals: NumberValue | None = None


@dataclass(frozen=True)
class FindErrorQuestionData(QuestionData[ErrorChoice]):
    """
    Shows ``expression`` simplified in ``steps``, one of them wrong, and asks in which step the
    error first appears, and why: ``answer``. The steps after it are worked correctly from the
    wrong line. ``sign_before_implied`` writes a x or ÷ just before a multiplication without its
    sign, as in 60 ÷ 6[2 + 8], which the answer doesn't depend on.
    """

    expression: Expression
    steps: tuple[Expression, ...]
    brackets: bool
    answer: ErrorChoice
    sign_before_implied: bool = False


# Each kind of question as presented. The tile forms are always written.
type ValueQuestion = Question[ValueQuestionData, FreeResponse | MultipleChoice[ValueOption]]
type NextStepQuestion = Question[NextStepQuestionData, FreeResponse | MultipleChoice[Expression]]
type HasValueQuestion = Question[HasValueQuestionData, FreeResponse | MultipleChoice[Expression]]
type FirstOperationQuestion = Question[
    FirstOperationQuestionData, FreeResponse | MultipleChoice[FirstChoice]
]
type ParenthesesQuestion = Question[
    ParenthesesQuestionData, FreeResponse | MultipleChoice[Statement]
]
type FindErrorQuestion = Question[FindErrorQuestionData, FreeResponse | MultipleChoice[ErrorChoice]]
type StepBlankQuestion = Question[StepBlankQuestionData, FreeResponse]
type ValueCountQuestion = Question[ValueCountQuestionData, FreeResponse]
type FirstResultQuestion = Question[FirstResultQuestionData, FreeResponse]

# Any question on an order of operations sheet
type OrderOfOperationsQuestion = (
    ValueQuestion
    | NextStepQuestion
    | HasValueQuestion
    | FirstOperationQuestion
    | ParenthesesQuestion
    | FindErrorQuestion
    | StepBlankQuestion
    | ValueCountQuestion
    | FirstResultQuestion
)
