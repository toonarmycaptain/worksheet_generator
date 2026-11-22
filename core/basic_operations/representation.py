"""
Wording of basic-operation questions: each operation's symbol and name, the equations, two-step
questions' steps, and the questions as the self-check tiles sheet shows them. Also the
representations drawn with, or chosen for, word problems, with their sheet titles, instructions,
hints and diagram descriptions, the equations and number lines a problem's own is chosen from,
and the strip diagrams a problem's own is chosen from, two-step problems' equations and strip
diagrams included, with what each problem shows.
"""

import random
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from fractions import Fraction
from functools import partial
from itertools import combinations, product
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
    """Return the question's equation, as in 47 + 25, with a comma in 1,000 and up."""
    first, second = data.operands
    return f"{first:,} {SYMBOLS[data.operation]} {second:,}"


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
    return f"{_written_text(_written_steps(data))} = ?"


def solved_equation(data: BasicOperationQuestionData) -> str:
    """Return the question's equation with its answer, as in 47 + 25 = 72."""
    return f"{equation(data)} = {data.answer:,}"


def solved_steps(data: TwoStepQuestionData) -> str:
    """Return each of the two-step question's steps with its answer: 24 - 6 = 18,  18 ÷ 3 = 6."""
    return ",  ".join(solved_equation(step) for step in data.steps)


def basic_operation_tile_question(data: BasicOperationQuestionData) -> TileQuestion:
    """Convert the question to a ``TileQuestion`` for the self-check tiles sheet."""
    return TileQuestion(
        prompt=stem(data), answer=f"{data.answer:,}", solution=solved_equation(data)
    )


def missing_number_equation(data: MissingNumberQuestionData, missing: int | str = BLANK) -> str:
    """
    Return the equation with ``missing`` in place of its missing operand.

    By default the gap is a ``BLANK`` (□ ÷ 4 = 7); passing the answer gives the completed
    equation (28 ÷ 4 = 7). Numbers of 1,000 and up have a comma.
    """
    shown = f"{missing:,}" if isinstance(missing, int) else missing
    known = f"{data.known:,}"
    operands = (shown, known) if data.unknown is Unknown.FIRST else (known, shown)
    return f"{operands[0]} {SYMBOLS[data.operation]} {operands[1]} = {data.result:,}"


def missing_number_tile_question(data: MissingNumberQuestionData) -> TileQuestion:
    """Convert the equation to a ``TileQuestion``, with a square for the missing number."""
    return TileQuestion(
        prompt=missing_number_equation(data),
        answer=f"{data.answer:,}",
        solution=missing_number_equation(data, data.answer),
    )


def two_step_tile_question(data: TwoStepQuestionData) -> TileQuestion:
    """Convert the two-step question to a ``TileQuestion`` for the self-check tiles sheet."""
    return TileQuestion(prompt=stem(data), answer=f"{data.answer:,}", solution=solved_steps(data))


class Representation(StrEnum):
    """
    The representation drawn with, or chosen for, each word problem on a sheet. Values are stable
    identifiers for the API and storage.
    """

    STRIP = "strip"  # a part-part-whole strip diagram, or bar model
    NONE = "none"  # text only, with a box to show the work
    NUMBER_LINE = "number_line"  # jumps along an open number line
    BLOCKS = "blocks"  # base-ten blocks
    EQUATION = "equation"  # its equation, as in 47 + 25 = □, written on a line or chosen


# What each representation is called, in a sheet's title and on the web page
REPRESENTATION_NAMES = {
    Representation.STRIP: "Strip Diagrams",
    Representation.NONE: "Text Only",
    Representation.NUMBER_LINE: "Number Lines",
    Representation.BLOCKS: "Base-Ten Blocks",
    Representation.EQUATION: "Equations",
}
WORD_PROBLEMS_NAME = "Word Problems"

# What a sheet of word problems is called after its name, when each problem's representation is
# chosen from lettered ones. Only these representations are offered as multiple choice.
CHOICE_NAMES = {
    Representation.NUMBER_LINE: "Number Line multiple choice",
    Representation.EQUATION: "Equation multiple choice",
}

# The operations each representation can show. A number line jumps forward or back, and base-ten
# blocks are joined or crossed out, so they show only addition and subtraction.
REPRESENTATION_OPERATIONS = {
    Representation.STRIP: frozenset(Operation),
    Representation.NONE: frozenset(Operation),
    Representation.NUMBER_LINE: frozenset({Operation.ADD, Operation.SUBTRACT}),
    Representation.BLOCKS: frozenset({Operation.ADD, Operation.SUBTRACT}),
    Representation.EQUATION: frozenset(Operation),
}


# The representations that can show a two-step problem: one bar of strip diagram, text only, or
# its equation, with the first step in brackets
TWO_STEP_REPRESENTATIONS = frozenset(
    {Representation.STRIP, Representation.NONE, Representation.EQUATION}
)


# The representations whose sheets have "how many more than" stories. A strip shows parts making a
# whole, and blocks show the first number with the second crossed out, taken away, so neither
# shows a comparison.
COMPARISON_REPRESENTATIONS = frozenset(
    {Representation.NONE, Representation.NUMBER_LINE, Representation.EQUATION}
)


class Response(StrEnum):
    """
    How each word problem on a sheet is answered. Values are stable identifiers for the API and
    storage.
    """

    FREE_RESPONSE = "free_response"  # written, beside or under its representation
    MULTIPLE_CHOICE = "multiple_choice"  # its representation chosen from lettered ones


# A kind of word problem on a sheet that mixes them: its representation, and how it's answered
type WordProblemKind = tuple[Representation, Response]


def word_problem_kinds(
    representations: Collection[Representation],
    responses: Collection[Response],
    two_steps: bool = False,
) -> list[WordProblemKind]:
    """
    Return the kinds of word problem a sheet mixing ``representations`` and ``responses`` can
    draw, in the order of ``Representation``, then of ``Response``: each representation answered
    each way it can be. Only a representation in ``CHOICE_NAMES`` is chosen, and with
    ``two_steps`` only one in ``TWO_STEP_REPRESENTATIONS`` is drawn, and only equations are
    chosen.
    """
    return [
        (representation, response)
        for representation in Representation
        if representation in representations
        and (not two_steps or representation in TWO_STEP_REPRESENTATIONS)
        for response in Response
        if response in responses
        and (
            response is Response.FREE_RESPONSE
            or (
                representation in CHOICE_NAMES
                and (not two_steps or representation is Representation.EQUATION)
            )
        )
    ]


# The shapes of two-step problem one bar of strip diagram can show: three parts, the whole less a
# part shared into equal parts, or equal parts and one other. Text only shows every shape.
STRIP_TWO_STEP_SHAPES: frozenset[TwoStepShape] = frozenset(
    {
        (Operation.ADD, Operation.ADD, Unknown.FIRST),
        (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST),
        (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST),
        (Operation.MULTIPLY, Operation.ADD, Unknown.FIRST),
        (Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND),
    }
)


def word_problems_title(representation: Representation, choices: bool = False) -> str:
    """
    Return what a sheet of word problems drawn with ``representation`` is called, so its title
    unless one is given: "Word Problems", followed by the representation's name unless the sheet is
    text only. With ``choices``, each problem's representation is chosen from lettered ones, and
    its name in ``CHOICE_NAMES`` follows instead.
    """
    if choices:
        return f"{WORD_PROBLEMS_NAME} — {CHOICE_NAMES[representation]}"
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
    choices.

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
# A two-step word problem as presented: its equation chosen from lettered equations
type TwoStepEquationChoiceQuestion = Question[TwoStepQuestionData, MultipleChoice[str]]
# A word problem as presented: answered in writing, with one step or two, or its equation, with
# one step or two, or number line chosen
type WordProblemQuestion = (
    Question[BasicOperationQuestionData, FreeResponse]
    | Question[TwoStepQuestionData, FreeResponse]
    | EquationChoiceQuestion
    | TwoStepEquationChoiceQuestion
    | NumberLineChoiceQuestion
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
    return f"{numbers[0]:,} {SYMBOLS[operation]} {numbers[1]:,} = {BLANK}"


@dataclass(frozen=True)
class _WrittenSteps:
    """
    A two-step equation's left side as written: ``numbers`` and the two signs between them, left
    to right, with the brackets around the first two numbers if ``brackets_first``, or else the
    last two. (24 - 6) ÷ 3 is ``((24, 6, 3), SUBTRACT, DIVIDE, True)``, and 45 - (5 x 3) is
    ``((45, 5, 3), SUBTRACT, MULTIPLY, False)``.
    """

    numbers: tuple[int, int, int]
    first_sign: Operation
    second_sign: Operation
    brackets_first: bool


@dataclass(frozen=True)
class _WrittenStep:
    """
    A one-step equation's left side as written, as a two-step equation stopped after one step
    gives it: 12 + 8 is ``((12, 8), ADD)``.
    """

    numbers: tuple[int, int]
    sign: Operation


# an equation's left side to choose, the right one or a wrong one
type _Written = _WrittenSteps | _WrittenStep


def _written_steps(data: TwoStepQuestionData) -> _WrittenSteps:
    """Return the two-step question's equation as written, with its first step in brackets."""
    first, second = data.steps
    if data.carried is Unknown.FIRST:  # (a ○ b) ● c
        numbers = (*first.operands, second.operands[1])
        return _WrittenSteps(numbers, first.operation, second.operation, brackets_first=True)
    numbers = (second.operands[0], *first.operands)  # c ● (a ○ b)
    return _WrittenSteps(numbers, second.operation, first.operation, brackets_first=False)


def _written_text(written: _Written) -> str:
    """Return the written equation's left side, as in (24 - 6) ÷ 3, with a comma in 1,000 and up."""
    if isinstance(written, _WrittenStep):
        left, right = written.numbers
        return f"{left:,} {SYMBOLS[written.sign]} {right:,}"
    first, second, third = (f"{number:,}" for number in written.numbers)
    first_sign, second_sign = SYMBOLS[written.first_sign], SYMBOLS[written.second_sign]
    if written.brackets_first:
        return f"({first} {first_sign} {second}) {second_sign} {third}"
    return f"{first} {first_sign} ({second} {second_sign} {third})"


def two_step_equation_choices(
    data: TwoStepQuestionData, unknown: str, operations: Collection[Operation]
) -> MultipleChoice[str]:
    """
    Return the equations to choose from for a two-step word problem: its own, with its first step
    in brackets and ``unknown`` for what to find, as in (24 - 6) ÷ 3 = s, and three wrong ones.

    The wrong equations cross two mistakes: one wrong equation has one mistake, one the other, and
    one both, so each change is in exactly two of the four choices, and no choice is the one most
    like the others. The mistakes depend on ``operations``, the sheet's, as ``_mistake_pairs``
    gives them:

    - With two or more operations, two of three: the first sign written changed, the second sign
      written changed, and the brackets moved to the other pair of numbers. For (24 - 6) ÷ 3 they
      can be (24 + 6) ÷ 3, 24 - (6 ÷ 3) and 24 + (6 ÷ 3). A changed sign is one of
      ``operations``: a sign that no problem on the sheet has in its own equation would rule a
      choice out. The brackets can go on either pair, since for any two operations the
      word-problem bank has stories with each.
    - With subtraction or division alone, the brackets moved, and the step outside them written
      the other way round. For (45 - 12) - 8 they are 45 - (12 - 8), 8 - (45 - 12) and
      (12 - 8) - 45.
    - With addition or multiplication alone, where neither of those changes the value, a number
      copied with its digits the other way round, and the equation stopped after one step. For
      (12 + 8) + 5 they can be (21 + 8) + 5, 12 + 8 and 21 + 8.
    - With multiplication alone, when those give no fair set, as with no number of two digits to
      reverse, the first sign and the second changed to +. For 5 x (3 x 2) they are
      5 + (3 x 2), 5 x (3 + 2) and 5 + (3 + 2). A student who knows the sheet is multiplication
      alone can rule out a + choice, but nothing else changes the value of three numbers
      multiplied, and few problems have a number to reverse.

    Which two mistakes, and which ways of making them, are drawn at random among those that make
    a fair set. Every choice has the problem's numbers in the same order: the story's, unless that
    gives no fair set with those mistakes and the brackets add or multiply, when the two numbers in
    them go the other way round, so 3 and then 5 more, and then 2 more, can be (5 + 3) + 2,
    (5 - 3) + 2, (5 + 3) - 2 and (5 - 3) - 2.

    A set is fair when no wrong equation has the problem's answer, as moving the brackets in
    (5 + 3) + 2 would, and none can be ruled out without working it out: its brackets never take
    a number from one no larger, or divide a number by a larger one, as 3 - 5 or 3 ÷ 5 would. A
    wrong equation that works out uneven or below zero is allowed, as (25 + 5) ÷ 4 is.

    Raises ``ValueError`` if no set is fair.
    """
    for pairs, right in product(_mistake_pairs(operations), _written_orders(data)):
        fair_by_mistakes: dict[int, list[tuple[_Written, _Written, _Written]]] = {}
        for mistakes, wrong in _fair_sets(right, pairs):
            fair_by_mistakes.setdefault(mistakes, []).append(wrong)
        if fair_by_mistakes:
            break
    else:
        raise ValueError(f"No fair wrong equations for {_written_text(_written_steps(data))}.")
    wrong = random.choice(random.choice(list(fair_by_mistakes.values())))
    return multiple_choice(
        (f"{_written_text(right)} = {unknown}",),
        tuple(f"{_written_text(written)} = {unknown}" for written in wrong),
    )


def has_fair_equation_choices(data: TwoStepQuestionData, operations: Collection[Operation]) -> bool:
    """
    Return whether ``two_step_equation_choices`` can give the two-step word problem a fair set of
    wrong equations for a sheet of ``operations``.
    """
    return any(
        next(_fair_sets(right, pairs), None) is not None
        for pairs, right in product(_mistake_pairs(operations), _written_orders(data))
    )


def _written_orders(data: TwoStepQuestionData) -> list[_WrittenSteps]:
    """
    Return the ways to write the two-step question's equation that ``two_step_equation_choices``
    tries, in turn: the story's order, and then, if its brackets add or multiply, the same with
    the two numbers in them the other way round.
    """
    story_order = _written_steps(data)
    if _bracketed(story_order)[0] in (Operation.ADD, Operation.MULTIPLY):
        return [story_order, _swapped(story_order)]
    return [story_order]


# A mistake in a written two-step equation: it returns the equation with each way of making it
type _Mistake = Callable[[_WrittenSteps], list[_WrittenSteps]]
# A mistake that may leave a step out, so its equations take no further mistake: crossed with
# another, it's made second
type _LastMistake = Callable[[_WrittenSteps], Sequence[_Written]]
# two mistakes for wrong choices to cross, the second made last
type _MistakePair = tuple[_Mistake, _LastMistake]


def _fair_sets(
    right: _WrittenSteps, pairs: Sequence[_MistakePair]
) -> Iterator[tuple[int, tuple[_Written, _Written, _Written]]]:
    """
    Yield every fair set of three wrong equations for ``right`` that crosses one of ``pairs`` of
    mistakes, each with the index of its pair.
    """
    answer = _value(right)
    for mistakes, (one, other) in enumerate(pairs):
        for wrong in _crossed_mistakes(right, one, other):
            if _is_fair(answer, wrong):
                yield mistakes, wrong


def _first_signs_changed(
    written: _WrittenSteps, signs: Collection[Operation]
) -> list[_WrittenSteps]:
    """
    Return the written equation with each other first sign of ``signs``, in ``Operation``'s
    order.
    """
    return [
        replace(written, first_sign=sign)
        for sign in Operation
        if sign in signs and sign is not written.first_sign
    ]


def _second_signs_changed(
    written: _WrittenSteps, signs: Collection[Operation]
) -> list[_WrittenSteps]:
    """
    Return the written equation with each other second sign of ``signs``, in ``Operation``'s
    order.
    """
    return [
        replace(written, second_sign=sign)
        for sign in Operation
        if sign in signs and sign is not written.second_sign
    ]


def _brackets_moved(written: _WrittenSteps) -> list[_WrittenSteps]:
    """Return the written equation with its brackets around the other pair of numbers."""
    return [replace(written, brackets_first=not written.brackets_first)]


def _order_swapped(written: _WrittenSteps) -> list[_WrittenSteps]:
    """
    Return the written equation with the step outside its brackets written the other way round:
    the brackets and the number outside them swap places, so (45 - 12) - 8 is 8 - (45 - 12).
    """
    first, second, third = written.numbers
    if written.brackets_first:
        numbers, brackets_first = (third, first, second), False
    else:
        numbers, brackets_first = (second, third, first), True
    return [_WrittenSteps(numbers, written.second_sign, written.first_sign, brackets_first)]


def _digits_reversed(written: _WrittenSteps) -> list[_WrittenSteps]:
    """
    Return the written equation with each of its numbers in turn, left to right, copied with its
    digits the other way round, as 21 for 12. A number has no such copy if it reads the same
    either way, as 44 and 7 do, if the copy would start with 0, as 30's would, or if the copy is
    another of the equation's numbers.
    """
    first, second, third = written.numbers
    copies = (
        (_reversed_digits(first), second, third),
        (first, _reversed_digits(second), third),
        (first, second, _reversed_digits(third)),
    )
    return [
        replace(written, numbers=numbers)
        for numbers in copies
        if numbers != written.numbers and len(set(numbers)) == len(numbers)
    ]


def _reversed_digits(number: int) -> int:
    """
    Return ``number`` with its digits the other way round, as 21 for 12, or ``number`` itself if
    the copy would start with 0, as 30's would.
    """
    return number if number % 10 == 0 else int(str(number)[::-1])


def _step_left_out(written: _WrittenSteps) -> list[_WrittenStep]:
    """
    Return the written equation stopped after one step: its first two numbers with its first
    sign, then its last two with its second, as either step can come first in adding or
    multiplying three numbers. (12 + 8) + 5 gives 12 + 8 and 8 + 5.
    """
    first, second, third = written.numbers
    return [
        _WrittenStep((first, second), written.first_sign),
        _WrittenStep((second, third), written.second_sign),
    ]


def _mistake_pairs(signs: Collection[Operation]) -> Sequence[Sequence[_MistakePair]]:
    """
    Return the pairs of mistakes a two-step equation's wrong choices can cross, on a sheet of the
    operations ``signs``, in tiers: a tier's pairs are used only when no pair of an earlier tier
    gives a fair set. Each mistake changes a part of the equation that the other leaves alone.

    With two or more operations, any two of: the first sign or the second changed to another of
    ``signs``, and the brackets moved. With subtraction or division alone: the brackets moved,
    and the step outside them written the other way round. With addition or multiplication
    alone, where neither of those changes the value: a number with its digits reversed, and a
    step left out; with multiplication alone, failing those, the first sign and the second
    changed to +.
    """
    if len(set(signs)) > 1:
        mistakes: tuple[_Mistake, ...] = (
            partial(_first_signs_changed, signs=signs),
            partial(_second_signs_changed, signs=signs),
            _brackets_moved,
        )
        return [list(combinations(mistakes, 2))]
    if set(signs) <= {Operation.SUBTRACT, Operation.DIVIDE}:
        return [[(_brackets_moved, _order_swapped)]]
    tiers: list[list[_MistakePair]] = [[(_digits_reversed, _step_left_out)]]
    if Operation.MULTIPLY in signs:
        with_add = {Operation.ADD, Operation.MULTIPLY}
        signs_changed = (
            partial(_first_signs_changed, signs=with_add),
            partial(_second_signs_changed, signs=with_add),
        )
        tiers.append([signs_changed])
    return tiers


def _crossed_mistakes(
    right: _WrittenSteps, one: _Mistake, other: _LastMistake
) -> Iterator[tuple[_Written, _Written, _Written]]:
    """
    Yield every set of three wrong equations that crosses the mistakes ``one`` and ``other`` in
    ``right``: a way of making the first, a way of making the second, and both at once.
    """
    for first in one(right):
        # ``other`` changes a part ``one`` leaves alone, so it gives ``first`` its ways of being
        # made in the same order as ``right``'s
        for index, second in enumerate(other(right)):
            yield first, second, other(first)[index]


def _is_fair(answer: Fraction, wrong: Sequence[_Written]) -> bool:
    """
    Return whether every equation of ``wrong`` needs working out to rule out, and no two of them
    or ``answer`` share a value: a wrong equation with the answer's value would be a second right
    one, and two with the same value, as (5 + 3) + 2 and 5 + (3 + 2), would rule each other out.
    """
    # Checked first: a number taken from itself would leave 0 to divide by.
    if any(_ruled_out_at_a_glance(written) for written in wrong):
        return False
    return len({answer, *(_value(written) for written in wrong)}) == len(wrong) + 1


def _bracketed(written: _WrittenSteps) -> tuple[Operation, int, int]:
    """Return the sign in the written equation's brackets and the numbers either side of it."""
    first, second, third = written.numbers
    if written.brackets_first:
        return written.first_sign, first, second
    return written.second_sign, second, third


def _swapped(written: _WrittenSteps) -> _WrittenSteps:
    """Return the written equation with the two numbers in its brackets the other way round."""
    first, second, third = written.numbers
    numbers = (second, first, third) if written.brackets_first else (first, third, second)
    return replace(written, numbers=numbers)


def _ruled_out_at_a_glance(written: _Written) -> bool:
    """
    Return whether the written equation's brackets, or its one step, take a number from one no
    larger, or divide a number by a larger one, as in 3 - 5 or 3 ÷ 5.
    """
    if isinstance(written, _WrittenStep):
        sign, (left, right) = written.sign, written.numbers
    else:
        sign, left, right = _bracketed(written)
    match sign:
        case Operation.SUBTRACT:
            return left <= right
        case Operation.DIVIDE:
            return left < right
        case Operation.ADD | Operation.MULTIPLY:
            return False
        case _:
            assert_never(sign)


def _value(written: _Written) -> Fraction:
    """Return the written equation's value, worked out exactly."""
    if isinstance(written, _WrittenStep):
        left, right = written.numbers
        return _worked(written.sign, Fraction(left), Fraction(right))
    first, second, third = (Fraction(number) for number in written.numbers)
    if written.brackets_first:
        return _worked(written.second_sign, _worked(written.first_sign, first, second), third)
    return _worked(written.first_sign, first, _worked(written.second_sign, second, third))


def _worked(operation: Operation, left: Fraction, right: Fraction) -> Fraction:
    """Return ``operation`` applied to ``left`` and ``right``."""
    match operation:
        case Operation.ADD:
            return left + right
        case Operation.SUBTRACT:
            return left - right
        case Operation.MULTIPLY:
            return left * right
        case Operation.DIVIDE:
            return left / right
        case _:
            assert_never(operation)


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
    direction = _jump_direction(data.operation)
    return tuple(direction * term for term in place_value_terms(data.operands[1]))


def _jump_direction(operation: Operation) -> int:
    """
    Return 1 for addition, which jumps forward on a number line, and -1 for subtraction, which
    jumps back. A number line shows only addition and subtraction, so any other operation raises
    ``ValueError``.
    """
    match operation:
        case Operation.ADD:
            return 1
        case Operation.SUBTRACT:
            return -1
        case Operation.MULTIPLY | Operation.DIVIDE:
            name = OPERATION_NAMES[operation].lower()
            raise ValueError(f"A number line shows only addition and subtraction, not {name}.")
        case _:
            assert_never(operation)


@dataclass(frozen=True)
class TwoJumpLine:
    """
    A number line from 0 with two jumps: ``first`` forward, then ``second``, forward if positive
    and back if negative, landing on ``end``.

    47 + 25 is ``(47, 25, 72)``, and 72 - 25 is ``(72, -25, 47)``. A wrong choice can land where
    its jumps don't: ``(47, 25, 82)``.
    """

    first: int
    second: int
    end: int


# A word problem as presented: its number line chosen from lettered number lines
type NumberLineChoiceQuestion = Question[BasicOperationQuestionData, MultipleChoice[TwoJumpLine]]

# A wrong landing's distance from the answer, a ten miscounted, where the numbers leave room for it
_LANDING_STEP = 10


def number_line_choices(data: BasicOperationQuestionData) -> MultipleChoice[TwoJumpLine]:
    """
    Return the number lines to choose from for an addition or subtraction: its own, which jumps
    its first number and then its second, and three wrong lines, each with one mistake:

    - the second jump going the wrong way, which is the other operation;
    - the right jumps landing on the wrong number, ``_landing_step`` from the answer, on a side
      drawn at random, or else on the other side;
    - one of its numbers misread, as ``_misread_lines`` gives it, landing more than that step from
      the answer if any misreading does, and failing that anywhere new.

    The wrong landing has the same jumps as the problem's own line, so nothing else may tell the
    two apart. Its side is drawn, so the problem's own isn't always the lower or the higher. It
    lands past the first number the way the second jump goes, so its arc points the way its sign
    says. The misread line lands clear of both its possible spots where it can, so where it lands
    doesn't depend on the side drawn. With a second number of 1, or a subtraction's answer of 1,
    only one side is past the first number. With 2 - 1 neither is, so its wrong landing is 10
    above, pointing back. A subtraction whose answer is its second number, such as 50 - 25, has no
    misreading clear of both spots.

    Every line lands on a different number, above 0 and not on the first number. An addition's
    larger number must come first, so that its wrong way stays above 0, or this raises
    ``ValueError``, as it does for any other operation.
    """
    first, second = data.operands
    direction = _jump_direction(data.operation)
    right = TwoJumpLine(first, direction * second, data.answer)
    wrong_way = TwoJumpLine(first, -direction * second, first - direction * second)
    if wrong_way.end <= 0:
        raise ValueError("A number line from 0 needs an addition's larger number first.")
    step = _landing_step(data)
    side = random.choice((1, -1))  # above the answer or below, for the wrong landing to try first
    # Each is past the first number, by the step's choice, or on it or 0, for _first_new to skip.
    landings = [
        TwoJumpLine(first, right.second, data.answer + sign * step) for sign in (side, -side)
    ]
    pointing_back = TwoJumpLine(first, right.second, data.answer + _LANDING_STEP)  # for 2 - 1
    misread = list(_misread_lines(data))
    clear = [line for line in misread if abs(line.end - data.answer) > step]
    lines = [right, wrong_way]
    lines.append(_first_new([*landings, pointing_back], lines))
    lines.append(_first_new(clear + misread, lines))
    return multiple_choice((right,), tuple(lines[1:]))


def _landing_step(data: BasicOperationQuestionData) -> int:
    """
    Return how far a wrong landing is from the answer: ``_LANDING_STEP`` when that leaves it past
    the first number and above 0 on both sides of the answer, which needs a second number over 10
    and, for a subtraction, an answer over 10 too. Otherwise 1, the start counted as a jump.
    """
    second = data.operands[1]
    room = second if data.operation is Operation.ADD else min(second, data.answer)
    return _LANDING_STEP if room > _LANDING_STEP else 1


def _misread_lines(data: BasicOperationQuestionData) -> Iterator[TwoJumpLine]:
    """
    Yield the problem's own line with one of its numbers misread, most likely first: the second
    number, then the first, each as ``_misreadings`` gives it. Some land on or below 0, for the
    caller to skip.
    """
    first, second = data.operands
    direction = _jump_direction(data.operation)
    for number in _misreadings(second):
        yield TwoJumpLine(first, direction * number, first + direction * number)
    for number in _misreadings(first):
        yield TwoJumpLine(number, direction * second, number + direction * second)


def _misreadings(number: int) -> Iterator[int]:
    """
    Yield what ``number`` might be misread as, most likely first: its tens and ones swapped (25 as
    52, 30 as 3), double it, 10 less, and last, miscounted by one, one less and one more. A swap
    that reads the same, such as 33's, and anything 0 or less are skipped.
    """
    hundreds, tens, ones = number // 100, number // 10 % 10, number % 10
    swapped = hundreds * 100 + ones * 10 + tens
    for misread in (swapped, 2 * number, number - 10, number - 1, number + 1):
        if 0 < misread != number:
            yield misread


def _first_new(candidates: Iterable[TwoJumpLine], lines: Sequence[TwoJumpLine]) -> TwoJumpLine:
    """
    Return the first of ``candidates`` that lands above 0, not on the first number, and not where
    any of ``lines`` lands, or raise ``ValueError`` if none does.
    """
    taken = {lines[0].first} | {line.end for line in lines}
    for line in candidates:
        if line.end > 0 and line.end not in taken:
            return line
    raise ValueError("No wrong number line lands somewhere new.")


_BLOCKS_HINTS = {
    Operation.ADD: "Combine the blocks to find the total.",
    Operation.SUBTRACT: "Cross out {b} to subtract.",
}


def instruction(
    representation: Representation,
    operations: Collection[Operation],
    work_box: bool,
    choices: bool = False,
    two_steps: bool = False,
) -> str:
    """
    Return the instruction printed under a word-problem sheet's header, for its representation and
    the operations of its problems. ``work_box`` is for text only: whether each problem has a box
    to show the work in. ``choices`` is for number lines and equations: whether each problem's is
    chosen from lettered ones. ``two_steps`` is for equations to choose from: whether the problems
    have two steps, whose equations have a letter for what to find.
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
            if choices:
                return (
                    "Each number line starts at 0 and shows both numbers as jumps. Circle the "
                    "correct one."
                )
            return (
                "Use the number line. Start at the first number and jump by hundreds, tens, and "
                "ones."
            )
        case Representation.BLOCKS:
            return "Use the base-ten blocks to help you solve each problem."
        case Representation.EQUATION:
            if choices and two_steps:
                return (
                    "Choose the equation that matches each problem. The letter stands for the "
                    "number to find."
                )
            if choices:
                return (
                    f"Choose the equation that matches each problem. The {BLANK} shows what to "
                    "find."
                )
            return f"Write an equation for each problem, with a {BLANK} for what to find. Solve it."
        case _:
            assert_never(representation)


def hint(
    data: BasicOperationQuestionData | TwoStepQuestionData, representation: Representation
) -> str | None:
    """
    Return the hint printed under a word problem, for the representation drawn with it, or None if
    the representation has no hints. Strip diagrams have a hint for each shape of two-step
    problem, and text only and equations, the others that show two steps, have none.
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
        case Representation.EQUATION:
            return None
        case _:
            assert_never(representation)
