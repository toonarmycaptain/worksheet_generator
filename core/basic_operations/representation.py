"""
Wording of basic-operation questions: each operation's symbol and name, the equations, two-step
questions' steps, and the questions as the self-check tiles sheet shows them. Also the
representations drawn with, or chosen for, word problems, with their sheet titles, instructions,
hints and diagram descriptions, the equations a problem's own is chosen from, and the strip
diagrams a problem's own is chosen from, two-step problems' included, with what each problem
shows.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    TwoStepQuestionData,
    TwoStepShape,
    Unknown,
)
from core.placevalue.representation import place_value_terms
from core.question import BLANK, FreeResponse, MultipleChoice, Question, multiple_choice
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


def stem(data: BasicOperationQuestionData | TwoStepQuestionData) -> str:
    """Return the question's text: its word-problem wording, or its equation followed by "= ?"."""
    if data.question_text is not None:
        return data.question_text
    return _equation_stem(data)


def _equation_stem(data: BasicOperationQuestionData | TwoStepQuestionData) -> str:
    """
    Return the question's equation followed by "= ?", as in 47 + 25 = ?, or for two steps, with
    the first in brackets, as in (24 - 6) ÷ 3 = ?.
    """
    if isinstance(data, BasicOperationQuestionData):
        return f"{equation(data)} = ?"
    first, second = data.steps
    bracketed = f"({equation(first)})"
    left, right = second.operands
    operands = (bracketed, right) if data.carried is Unknown.FIRST else (left, bracketed)
    return f"{operands[0]} {SYMBOLS[second.operation]} {operands[1]} = ?"


def solved_equation(data: BasicOperationQuestionData) -> str:
    """Return the question's equation with its answer, as in 47 + 25 = 72."""
    return f"{equation(data)} = {data.answer}"


def solved_steps(data: TwoStepQuestionData) -> str:
    """Return each of the two-step question's steps with its answer: 24 - 6 = 18,  18 ÷ 3 = 6."""
    return ",  ".join(solved_equation(step) for step in data.steps)


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


def two_step_tile_question(data: TwoStepQuestionData) -> TileQuestion:
    """Convert the two-step question to a ``TileQuestion`` for the self-check tiles sheet."""
    return TileQuestion(prompt=stem(data), answer=str(data.answer), solution=solved_steps(data))


class Representation(StrEnum):
    """
    The representation drawn with, or chosen for, each word problem on a sheet. Values are stable
    identifiers for the API and storage.
    """

    STRIP = "strip"  # a part-part-whole strip diagram, or bar model
    NONE = "none"  # text only, with a box to show the work
    NUMBER_LINE = "number_line"  # jumps along an open number line
    BLOCKS = "blocks"  # base-ten blocks
    EQUATION_CHOICE = "equation_choice"  # its equation, chosen from lettered equations


# What each representation is called, in a sheet's title and on the web page
REPRESENTATION_NAMES = {
    Representation.STRIP: "Strip Diagrams",
    Representation.NONE: "Text Only",
    Representation.NUMBER_LINE: "Number Lines",
    Representation.BLOCKS: "Base-Ten Blocks",
    Representation.EQUATION_CHOICE: "Equation multiple choice",
}
WORD_PROBLEMS_NAME = "Word Problems"

# The operations each representation can show. A number line jumps forward or back, and base-ten
# blocks are joined or crossed out, so they show only addition and subtraction.
REPRESENTATION_OPERATIONS = {
    Representation.STRIP: frozenset(Operation),
    Representation.NONE: frozenset(Operation),
    Representation.NUMBER_LINE: frozenset({Operation.ADD, Operation.SUBTRACT}),
    Representation.BLOCKS: frozenset({Operation.ADD, Operation.SUBTRACT}),
    Representation.EQUATION_CHOICE: frozenset(Operation),
}


# The representations that can show a two-step problem: one bar of strip diagram, or text only
TWO_STEP_REPRESENTATIONS = frozenset({Representation.STRIP, Representation.NONE})


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
_TWO_STEP_STRIP_HINTS: dict[TwoStepShape, str] = {
    (Operation.ADD, Operation.ADD, Unknown.FIRST): "All three parts are shown. "
    "Add them to find the whole.",
    (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST): "The whole and two parts are shown. "
    "Subtract both parts to find the missing part.",
    (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST): "Subtract the part that's shown from "
    "the whole, then divide the rest into the equal parts.",
    (Operation.MULTIPLY, Operation.ADD, Unknown.FIRST): "Multiply to find the equal parts "
    "together, then add the other part to find the whole.",
    (Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND): "Multiply to find the equal parts "
    "together, then subtract them from the whole to find the missing part.",
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


@dataclass(frozen=True)
class TwoStepStripDiagram:
    """
    A two-step problem's strip diagram: a bar split into ``parts``, which together make
    ``whole``, drawn in a box over them. Equal parts are the same value repeated.

    The unknown value is ``None``, and shown as "?". 294 - 196 - 49 is ``((196, 49, None), 294)``,
    and 68 - 46 shared into 2 is ``((46, None, None), 68)``. A wrong choice can be impossible:
    ``((294, 49, None), 196)`` has a part larger than the whole.
    """

    parts: tuple[int | None, ...]
    whole: int | None


# A word problem or equation as presented: its strip diagram chosen from lettered strips
type StripChoiceQuestion = Question[
    BasicOperationQuestionData, MultipleChoice[StripDiagram | EqualStripDiagram]
]
# A two-step word problem or equation as presented: its strip diagram chosen from lettered strips
type TwoStepStripChoiceQuestion = Question[TwoStepQuestionData, MultipleChoice[TwoStepStripDiagram]]


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


def two_step_strip(data: TwoStepQuestionData) -> TwoStepStripDiagram:
    """
    Return the strip diagram for a two-step question: one bar, with its parts in the order the
    steps meet them. Raises ``ValueError`` for a shape that one bar can't show.
    """
    strip, _ = _two_step_strips(data)
    return strip


def two_step_strip_choices(data: TwoStepQuestionData) -> MultipleChoice[TwoStepStripDiagram]:
    """
    Return the strip diagrams to choose from for a two-step question: its own, and three wrong
    choices made the way the teacher's examples make them.

    A bar of three parts and a whole (adding three numbers, or taking two from a whole) has each
    of its other values in the whole's place, with the whole first among the parts. A bar with
    equal parts has a different value in the whole's place (the unknown, or else its other part),
    its equal parts forgotten (one instead of several), and one equal part too many. Raises
    ``ValueError`` for a shape that one bar can't show.

    A question that repeats one of its given numbers can have two choices that look the same, so
    a sheet of these choices leaves them out.
    """
    strip, wrong = _two_step_strips(data)
    return multiple_choice((strip,), wrong)


def _two_step_strips(
    data: TwoStepQuestionData,
) -> tuple[TwoStepStripDiagram, tuple[TwoStepStripDiagram, ...]]:
    """
    Return a two-step question's strip diagram and its wrong choices, as
    ``two_step_strip_choices`` describes them.
    """
    first, second = data.steps
    match data.shape:
        case (Operation.ADD, Operation.ADD, Unknown.FIRST):  # a + b + c = ?
            a, b = first.operands
            c = second.operands[1]
            return TwoStepStripDiagram((a, b, c), None), (
                TwoStepStripDiagram((None, b, c), a),
                TwoStepStripDiagram((None, a, c), b),
                TwoStepStripDiagram((None, a, b), c),
            )
        case (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST):  # whole - a - b = ?
            whole, a = first.operands
            b = second.operands[1]
            return TwoStepStripDiagram((a, b, None), whole), (
                TwoStepStripDiagram((whole, a, b), None),
                TwoStepStripDiagram((whole, b, None), a),
                TwoStepStripDiagram((whole, a, None), b),
            )
        case (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST):  # whole - part, shared
            whole, part = first.operands
            groups = second.operands[1]
            return TwoStepStripDiagram((part, *(None,) * groups), whole), (
                TwoStepStripDiagram((whole, part), None),
                TwoStepStripDiagram((part, None), whole),
                TwoStepStripDiagram((part, *(None,) * (groups + 1)), whole),
            )
        case (Operation.MULTIPLY, Operation.ADD, Unknown.FIRST):  # groups of size, + part
            groups, size = first.operands
            part = second.operands[1]
            return TwoStepStripDiagram(((size,) * groups + (part,)), None), (
                TwoStepStripDiagram((None, *(size,) * groups), part),
                TwoStepStripDiagram((size, part), None),
                TwoStepStripDiagram(((size,) * (groups + 1) + (part,)), None),
            )
        case (Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND):  # whole - groups of size
            groups, size = first.operands
            whole = second.operands[0]
            return TwoStepStripDiagram(((size,) * groups + (None,)), whole), (
                TwoStepStripDiagram((whole, *(size,) * groups), None),
                TwoStepStripDiagram((size, None), whole),
                TwoStepStripDiagram(((size,) * (groups + 1) + (None,)), whole),
            )
        case _:
            raise ValueError("One strip diagram shows only some shapes of two-step problem.")


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
    into them, with the numbers ``_groups_and_other`` gives.
    """
    first, second = data.operands
    smaller, larger = sorted(data.operands)
    groups, other = _groups_and_other(data)
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


def _groups_and_other(data: BasicOperationQuestionData) -> tuple[int, int]:
    """
    Return the number of equal groups that multiplying or dividing the question's numbers makes,
    and its other number.

    The number of groups is the question's own for multiplication (its first operand) and
    division (its second), and the smaller number for addition and subtraction. The other number
    is the size of each group when multiplying, and the whole when dividing.
    """
    first, second = data.operands
    match data.operation:
        case Operation.MULTIPLY:
            return first, second
        case Operation.DIVIDE:
            return second, first
        case Operation.ADD | Operation.SUBTRACT:
            smaller, larger = sorted(data.operands)
            return smaller, larger
        case _:
            assert_never(data.operation)


# A word problem as presented: its equation chosen from lettered equations
type EquationChoiceQuestion = Question[BasicOperationQuestionData, MultipleChoice[str]]
# A word problem as presented: answered in writing, with one step or two, or its equation chosen
type WordProblemQuestion = (
    Question[BasicOperationQuestionData, FreeResponse]
    | Question[TwoStepQuestionData, FreeResponse]
    | EquationChoiceQuestion
)


def equation_choices(data: BasicOperationQuestionData) -> MultipleChoice[str]:
    """
    Return the equations to choose from for a word problem: its own, and as the wrong choices the
    equations of the other three operations on its numbers. Each has a ``BLANK`` for what to
    find, as in 47 + 25 = □, and is the equation of the strip ``strip_choices`` gives for its
    operation.

    Operands of 2 and 2 give a wrong equation with the problem's answer (2 + 2 and 2 x 2 are
    both 4), and so does a subtraction or division of 4 by 2 (4 - 2 and 4 ÷ 2 are both 2), so a
    sheet of these choices leaves them out.
    """
    wrong = tuple(
        _operation_equation(operation, data)
        for operation in Operation
        if operation is not data.operation
    )
    return multiple_choice((_operation_equation(data.operation, data),), wrong)


def _operation_equation(operation: Operation, data: BasicOperationQuestionData) -> str:
    """
    Return the equation of ``operation`` on the question's numbers, with a ``BLANK`` for what to
    find, which is the question's own equation when ``operation`` is its operation.

    Adding keeps presentation order, and subtracting takes the smaller number from the larger.
    Multiplying is the number of groups times the other number, and dividing is the other number
    divided by the number of groups, with the numbers ``_groups_and_other`` gives.
    """
    first, second = data.operands
    smaller, larger = sorted(data.operands)
    groups, other = _groups_and_other(data)
    match operation:
        case Operation.ADD:
            numbers = first, second
        case Operation.SUBTRACT:
            numbers = larger, smaller
        case Operation.MULTIPLY:
            numbers = groups, other
        case Operation.DIVIDE:
            numbers = other, groups
        case _:
            assert_never(operation)
    return f"{numbers[0]} {SYMBOLS[operation]} {numbers[1]} = {BLANK}"


STRIP_CHOICE_NAME = (
    "Strip Diagram multiple choice"  # a strip-choice sheet's title unless one is given
)
STRIP_CHOICE_INSTRUCTION = (
    "Choose the strip diagram that matches each problem. The ? shows what to find."
)


class Prompt(StrEnum):
    """What each problem on a sheet shows. Values are stable identifiers for the API and storage."""

    WORD_PROBLEM = "word_problem"  # its wording
    EQUATION = "equation"  # its equation, as in 47 + 25 = ?
    BOTH = "both"  # its wording, then its equation


def prompt_texts(
    data: BasicOperationQuestionData | TwoStepQuestionData, prompt: Prompt
) -> tuple[str, ...]:
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


def instruction(
    representation: Representation, operations: Collection[Operation], work_box: bool
) -> str:
    """
    Return the instruction printed under a word-problem sheet's header, for its representation and
    the operations of its problems. ``work_box`` is for text only: whether each problem has a box
    to show the work in.
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
            if work_box:
                return "Read each problem. Show your work in the box."
            return "Read each problem and solve it."
        case Representation.NUMBER_LINE:
            return (
                "Use the number line. Start at the first number and jump by hundreds, tens, and "
                "ones."
            )
        case Representation.BLOCKS:
            return "Use the base-ten blocks to help you solve each problem."
        case Representation.EQUATION_CHOICE:
            return f"Choose the equation that matches each problem. The {BLANK} shows what to find."
        case _:
            assert_never(representation)


def hint(
    data: BasicOperationQuestionData | TwoStepQuestionData, representation: Representation
) -> str | None:
    """
    Return the hint printed under a word problem, for the representation drawn with it, or None if
    the representation has no hints. Strip diagrams have a hint for each shape of two-step
    problem, and text only, the other representation that shows two steps, has none.
    """
    if isinstance(data, TwoStepQuestionData):
        return _TWO_STEP_STRIP_HINTS[data.shape] if representation is Representation.STRIP else None
    match representation:
        case Representation.STRIP:
            return _STRIP_HINTS[data.operation]
        case Representation.NONE:
            return None
        case Representation.NUMBER_LINE:
            return _NUMBER_LINE_HINTS[data.operation]
        case Representation.BLOCKS:
            return _BLOCKS_HINTS[data.operation].format(b=data.operands[1])
        case Representation.EQUATION_CHOICE:
            return None
        case _:
            assert_never(representation)
