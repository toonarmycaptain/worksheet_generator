"""Data for addition, subtraction and multiplication questions."""

from dataclasses import dataclass
from enum import StrEnum


class Operation(StrEnum):
    """The arithmetic operation of a question. Values are stable IDs for JSON and databases."""

    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"


@dataclass(frozen=True)
class ArithmeticQuestionData:
    """One arithmetic question: ``operands`` combined by ``operation`` give ``answer``.

    The answer is stored so sets of questions can be searched and filtered on it
    (e.g. every question in a 3 times table). Operand order is the question's order:
    ``(7, 3)`` for subtraction is 7 minus 3, and for multiplication is 7 groups of 3.

    ``question_text`` is the wording of a word problem. When it is ``None`` the question is
    shown from its operation and operands, so many different texts can share the same data.
    """

    operation: Operation
    operands: tuple[int, int]
    answer: int
    question_text: str | None = None
