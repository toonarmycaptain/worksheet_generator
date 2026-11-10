"""
Question data for the four arithmetic operations, for two-step questions and for missing-number
equations.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.question import FreeResponse, MultipleChoice, Question, QuestionData


class Operation(StrEnum):
    """An arithmetic operation. Values are stable identifiers for the API and storage."""

    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"


@dataclass(frozen=True)
class BasicOperationQuestionData(QuestionData[int]):
    """
    An arithmetic question: ``operation`` applied to ``operands`` gives ``answer``.

    ``answer`` is stored rather than computed so that collections of questions can be searched
    and filtered by it, for example every question in the 3 times table. Operand order is
    presentation order: for subtraction ``(7, 3)`` is 7 - 3, and for multiplication it is 7
    groups of 3.

    ``question_text`` holds a word problem's wording. When it is ``None``, the question is
    rendered from its operation and operands, which lets many wordings share the same data.
    """

    operation: Operation
    operands: tuple[int, int]
    answer: int
    question_text: str | None = None


class Unknown(StrEnum):
    """An equation's missing operand. Values are stable identifiers for the API and storage."""

    FIRST = "first"  # □ ÷ 4 = 7, the dividend
    SECOND = "second"  # 28 ÷ □ = 4, the divisor


# A two-step question's shape: the operations of its two steps, and which of the second step's
# operands is the first step's answer
type TwoStepShape = tuple[Operation, Operation, Unknown]


@dataclass(frozen=True)
class TwoStepQuestionData(QuestionData[int]):
    """
    A two-step arithmetic question: ``steps[0]`` is worked first, and its answer is the operand
    of ``steps[1]`` that ``carried`` identifies. ``answer`` is the answer of ``steps[1]``.

    (24 - 6) ÷ 3 is ``((SUBTRACT, (24, 6), 18), (DIVIDE, (18, 3), 6))`` with ``carried``
    ``FIRST``, and 45 - (3 x 5) is ``((MULTIPLY, (3, 5), 15), (SUBTRACT, (45, 15), 30))`` with
    ``carried`` ``SECOND``. The steps have no ``question_text`` of their own: ``question_text``
    holds the word problem's wording, as on ``BasicOperationQuestionData``.
    """

    steps: tuple[BasicOperationQuestionData, BasicOperationQuestionData]
    carried: Unknown
    answer: int
    question_text: str | None = None

    @property
    def shape(self) -> TwoStepShape:
        """The question's shape: its steps' operations, and its ``carried`` operand."""
        first, second = self.steps
        return first.operation, second.operation, self.carried

    @property
    def given_numbers(self) -> tuple[int, int, int]:
        """
        The numbers the question gives: the first step's operands, then the second step's
        operand that isn't the first step's answer. (24 - 6) ÷ 3 gives ``(24, 6, 3)``.
        """
        first, second = self.steps
        other = second.operands[1] if self.carried is Unknown.FIRST else second.operands[0]
        return *first.operands, other


@dataclass(frozen=True)
class MissingNumberQuestionData(QuestionData[int]):
    """
    An equation with one operand missing: ``unknown`` identifies it and ``answer`` is its value.

    ``known`` is the operand shown, and ``result`` is the right-hand side. □ ÷ 4 = 7 is
    ``(DIVIDE, FIRST, 4, 7, 28)``, and 28 ÷ □ = 4 is ``(DIVIDE, SECOND, 28, 4, 7)``.
    """

    operation: Operation
    unknown: Unknown
    known: int
    result: int
    answer: int


# An arithmetic question as presented: chosen from lettered numbers
type BasicOperationMultipleChoiceQuestion = Question[
    BasicOperationQuestionData, MultipleChoice[int]
]
# A missing-number equation as presented: the number written in its square
type MissingNumberFreeResponseQuestion = Question[MissingNumberQuestionData, FreeResponse]
