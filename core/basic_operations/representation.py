"""
Wording of basic-operation questions: each operation's symbol and name, the equations, and the
questions as the self-check tiles sheet shows them. Also the representations drawn with word
problems, with their sheet titles, instructions, hints and diagram descriptions, and the strip
diagrams a problem's own is chosen from, with what each problem shows.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.placevalue.representation import place_value_terms
from core.question import BLANK, MultipleChoice, Question, multiple_choice
from core.self_check_tiles import TileQuestion

SYMBOLS = {
    Operation.ADD: "+",
    Operation.SUBTRACT: "\N{MINUS SIGN}",
    Operation.MULTIPLY: "\N{MULTIPLICATION SIGN}",
    Operation.DIVIDE: "\N{DIVISION SIGN}",
}

# What a sheet of each operation is called, so its title unless one is given
OPERATION_NAMES = {
    Operation.ADD: "Addition",
    Operation.SUBTRACT: "Subtraction",
    Operation.MULTIPLY: "Multiplication",
    Operation.DIVIDE: "Division",
}
MIXED_OPERATIONS_NAME = "Mixed Operations"  # a sheet of more than two operations


def operations_name(operations: Sequence[Operation]) -> str:
    """
    Return what a sheet of ``operations`` is called: one operation's name, two joined by "and"
    ("Addition and Subtraction"), or ``MIXED_OPERATIONS_NAME`` for more.
    """
    if len(operations) > 2:
        return MIXED_OPERATIONS_NAME
    return " and ".join(OPERATION_NAMES[operation] for operation in operations)


def equation(data: BasicOperationQuestionData) -> str:
    first, second = data.operands
    return f"{first} {SYMBOLS[data.operation]} {second}"


def stem(data: BasicOperationQuestionData) -> str:
    """Return the question's text: its word-problem wording, or its equation followed by "= ?"."""
    if data.question_text is not None:
        return data.question_text
    return _equation_stem(data)


def _equation_stem(data: BasicOperationQuestionData) -> str:
    """Return the question's equation followed by "= ?", as in 47 + 25 = ?."""
    return f"{equation(data)} = ?"


def solved_equation(data: BasicOperationQuestionData) -> str:
    """Return the question's equation with its answer, as in 47 + 25 = 72."""
    return f"{equation(data)} = {data.answer}"


def basic_operation_tile_question(data: BasicOperationQuestionData) -> TileQuestion:
    """Convert the question to a ``TileQuestion`` for the self-check tiles sheet."""
    return TileQuestion(prompt=stem(data), answer=str(data.answer), solution=solved_equation(data))


def missing_number_equation(data: MissingNumberQuestionData, missing: int | str = BLANK) -> str:
    """
    Return the equation with ``missing`` in place of its missing operand.

    By default the gap is a ``BLANK`` (□ ÷ 4 = 7); passing the answer gives the completed
    equation (28 ÷ 4 = 7).
    """
    operands = (missing, data.known) if data.unknown is Unknown.FIRST else (data.known, missing)
    return f"{operands[0]} {SYMBOLS[data.operation]} {operands[1]} = {data.result}"


def missing_number_tile_question(data: MissingNumberQuestionData) -> TileQuestion:
    """Convert the equation to a ``TileQuestion``, with a square for the missing number."""
    return TileQuestion(
        prompt=missing_number_equation(data),
        answer=str(data.answer),
        solution=missing_number_equation(data, data.answer),
    )


class Representation(StrEnum):
    """
    The representation drawn with each word problem on a sheet. Values are stable identifiers for
    the API and storage.
    """

    STRIP = "strip"  # a part-part-whole strip diagram, or bar model
    NONE = "none"  # text only, with a box to show the work
    NUMBER_LINE = "number_line"  # jumps along an open number line
    BLOCKS = "blocks"  # base-ten blocks


# What each representation is called, in a sheet's title and on the web page
REPRESENTATION_NAMES = {
    Representation.STRIP: "Strip Diagrams",
    Representation.NONE: "Text Only",
    Representation.NUMBER_LINE: "Number Lines",
    Representation.BLOCKS: "Base-Ten Blocks",
}
WORD_PROBLEMS_NAME = "Word Problems"

# The operations each representation can show. A number line jumps forward or back, and base-ten
# blocks are joined or crossed out, so they show only addition and subtraction.
REPRESENTATION_OPERATIONS = {
    Representation.STRIP: frozenset(Operation),
    Representation.NONE: frozenset(Operation),
    Representation.NUMBER_LINE: frozenset({Operation.ADD, Operation.SUBTRACT}),
    Representation.BLOCKS: frozenset({Operation.ADD, Operation.SUBTRACT}),
}


def word_problems_title(representation: Representation) -> str:
    """
    Return what a sheet of word problems drawn with ``representation`` is called, so its title
    unless one is given: "Word Problems", followed by the representation's name unless the sheet is
    text only.
    """
    if representation is Representation.NONE:
        return WORD_PROBLEMS_NAME
    return f"{WORD_PROBLEMS_NAME} — {REPRESENTATION_NAMES[representation]}"


_STRIP_HINTS = {
    Operation.ADD: "Both parts are shown. Add the parts to find the whole.",
    Operation.SUBTRACT: "The whole and one part are shown. Subtract to find the missing part.",
    Operation.MULTIPLY: "Equal groups are shown. Multiply the group size by the number of groups.",
    Operation.DIVIDE: "The whole is split into equal groups. "
    "Divide to find the amount in each group.",
}


@dataclass(frozen=True)
class StripDiagram:
    """
    A part-part-whole strip diagram: a bar split into two ``parts``, which together make
    ``whole``.

    The unknown value is ``None``, and shown as "?". 47 + 25 is ``((47, 25), None)``, and
    72 - 25 is ``((25, None), 72)``. A wrong choice can be impossible: ``((47, None), 25)`` has
    a part larger than the whole.
    """

    parts: tuple[int, int | None]
    whole: int | None


@dataclass(frozen=True)
class EqualStripDiagram:
    """
    An equal-groups strip diagram: a bar split into ``groups`` equal parts, each of ``size``,
    which together make ``whole``.

    The unknown value is ``None``, and shown as "?": an unknown size in every part. 3 groups of 4
    is ``(3, 4, None)``, and 12 shared into 3 groups is ``(3, None, 12)``. A wrong choice can be
    impossible: ``(3, None, 4)`` shares 4 into 3 equal groups.
    """

    groups: int
    size: int | None
    whole: int | None


# A word problem or equation as presented: its strip diagram chosen from lettered strips
type StripChoiceQuestion = Question[
    BasicOperationQuestionData, MultipleChoice[StripDiagram | EqualStripDiagram]
]


def strip_diagram(data: BasicOperationQuestionData) -> StripDiagram | EqualStripDiagram:
    """
    Return the strip diagram for a question.

    Addition shows its operands as the parts and asks for the whole. Subtraction shows its first
    operand as the whole and its second as the left part, and asks for the right part.
    Multiplication shows its first operand's number of equal parts, each of its second operand,
    and asks for the whole. Division shows its first operand as the whole, split into its second
    operand's number of equal parts, and asks for their size.
    """
    return _operation_strip(data.operation, data)


def strip_choices(
    data: BasicOperationQuestionData,
) -> MultipleChoice[StripDiagram | EqualStripDiagram]:
    """
    Return the strip diagrams to choose from for a question: its own, and as the wrong choices
    the strips of the other three operations on its numbers. So an addition's wrong choices
    subtract, multiply and divide its numbers instead.

    Operands of 2 and 2 give two strips that look the same, 2 + 2 and 2 groups of 2, so a sheet
    of these choices leaves them out.
    """
    wrong = tuple(
        _operation_strip(operation, data)
        for operation in Operation
        if operation is not data.operation
    )
    return multiple_choice((strip_diagram(data),), wrong)


def _operation_strip(
    operation: Operation, data: BasicOperationQuestionData
) -> StripDiagram | EqualStripDiagram:
    """
    Return the strip diagram of ``operation`` on the question's numbers, which is the question's
    own strip diagram when ``operation`` is its operation.

    Adding makes the numbers the parts, in presentation order. Subtracting makes the larger
    number the whole and the smaller a part. Multiplying makes equal groups, and dividing shares
    into them. The number of groups is the question's own for multiplication (its first operand)
    and division (its second), and the smaller number for addition and subtraction. The other
    number is the size of each group when multiplying, and the whole when dividing.
    """
    first, second = data.operands
    smaller, larger = sorted(data.operands)
    match data.operation:
        case Operation.MULTIPLY:
            groups, other = first, second
        case Operation.DIVIDE:
            groups, other = second, first
        case Operation.ADD | Operation.SUBTRACT:
            groups, other = smaller, larger
        case _:
            assert_never(data.operation)
    match operation:
        case Operation.ADD:
            return StripDiagram((first, second), None)
        case Operation.SUBTRACT:
            return StripDiagram((smaller, None), larger)
        case Operation.MULTIPLY:
            return EqualStripDiagram(groups, other, None)
        case Operation.DIVIDE:
            return EqualStripDiagram(groups, None, other)
        case _:
            assert_never(operation)


STRIP_CHOICE_NAME = "Pick the Strip Diagram"  # a strip-choice sheet's title unless one is given
STRIP_CHOICE_INSTRUCTION = (
    "Choose the strip diagram that matches each problem. The ? shows what to find."
)


class Prompt(StrEnum):
    """What each problem on a sheet shows. Values are stable identifiers for the API and storage."""

    WORD_PROBLEM = "word_problem"  # its wording
    EQUATION = "equation"  # its equation, as in 47 + 25 = ?
    BOTH = "both"  # its wording, then its equation


def prompt_texts(data: BasicOperationQuestionData, prompt: Prompt) -> tuple[str, ...]:
    """
    Return the paragraphs a problem shows for ``prompt``: its wording, its equation followed by
    "= ?", or both, in that order.
    """
    match prompt:
        case Prompt.WORD_PROBLEM:
            return (stem(data),)
        case Prompt.EQUATION:
            return (_equation_stem(data),)
        case Prompt.BOTH:
            return stem(data), _equation_stem(data)
        case _:
            assert_never(prompt)


_NUMBER_LINE_HINTS = {
    Operation.ADD: "Jump forward to add. Fill in each box; the last box is your answer.",
    Operation.SUBTRACT: "Jump backward to subtract. Fill in each box; the last box is your answer.",
}


def number_line_jumps(data: BasicOperationQuestionData) -> tuple[int, ...]:
    """
    Return the jumps along a question's number line, which starts at its first operand.

    The jumps are the place-value terms of the second operand, largest first: positive for
    addition and negative for subtraction. 347 - 125 jumps ``(-100, -20, -5)``, landing on 247,
    227 and 222. A number line shows only addition and subtraction, so any other operation
    raises ``ValueError``.
    """
    terms = place_value_terms(data.operands[1])
    match data.operation:
        case Operation.ADD:
            return terms
        case Operation.SUBTRACT:
            return tuple(-term for term in terms)
        case Operation.MULTIPLY | Operation.DIVIDE:
            name = OPERATION_NAMES[data.operation].lower()
            raise ValueError(f"A number line shows only addition and subtraction, not {name}.")
        case _:
            assert_never(data.operation)


_BLOCKS_HINTS = {
    Operation.ADD: "Combine the blocks to find the total.",
    Operation.SUBTRACT: "Cross out {b} to subtract.",
}


def instruction(representation: Representation, operations: Collection[Operation]) -> str:
    """
    Return the instruction printed under a word-problem sheet's header, for its representation and
    the operations of its problems.
    """
    match representation:
        case Representation.STRIP:
            parts = not {Operation.ADD, Operation.SUBTRACT}.isdisjoint(operations)
            equal_groups = not {Operation.MULTIPLY, Operation.DIVIDE}.isdisjoint(operations)
            if parts and equal_groups:
                makes = "parts or equal groups make a whole"
            elif equal_groups:
                makes = "equal groups make a whole"
            else:
                makes = "two parts make a whole"
            return f"Use the strip diagram (bar model): {makes}. The ? shows what to find."
        case Representation.NONE:
            return "Read each problem. Show your work in the box."
        case Representation.NUMBER_LINE:
            return (
                "Use the number line. Start at the first number and jump by hundreds, tens, and "
                "ones."
            )
        case Representation.BLOCKS:
            return "Use the base-ten blocks to help you solve each problem."
        case _:
            assert_never(representation)


def hint(data: BasicOperationQuestionData, representation: Representation) -> str | None:
    """
    Return the hint printed under a word problem, for the representation drawn with it, or None if
    the representation has no hints.
    """
    match representation:
        case Representation.STRIP:
            return _STRIP_HINTS[data.operation]
        case Representation.NONE:
            return None
        case Representation.NUMBER_LINE:
            return _NUMBER_LINE_HINTS[data.operation]
        case Representation.BLOCKS:
            return _BLOCKS_HINTS[data.operation].format(b=data.operands[1])
        case _:
            assert_never(representation)
