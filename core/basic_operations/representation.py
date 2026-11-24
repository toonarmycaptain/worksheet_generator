"""
Wording of basic-operation questions: each operation's symbol and name, the equations, two-step
questions' steps, and the questions as the self-check tiles sheet shows them. Also the
representations drawn with, or chosen for, word problems, with their sheet titles, instructions,
hints and diagram descriptions, the equations and number lines a problem's own is chosen from,
the numbers its answer is chosen from, and the strip diagrams a problem's own is chosen from,
two-step problems' equations and strip diagrams included, with what each problem shows.
"""

import random
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass, replace
from enum import Enum, StrEnum
from fractions import Fraction
from functools import partial
from itertools import combinations, combinations_with_replacement, product
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
    return f"{_term_text(_two_step_side(data), BLANK)} = ?"


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
    NUMBER_CHOICE = (
        "number_choice"  # its answer chosen from lettered numbers, under its representation
    )


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
    each way it can be. Only a representation in ``CHOICE_NAMES`` is chosen, any can have its
    answer chosen from numbers, and with ``two_steps`` only one in ``TWO_STEP_REPRESENTATIONS``
    is drawn, and only equations are chosen.
    """
    return [
        (representation, response)
        for representation in Representation
        if representation in representations
        and (not two_steps or representation in TWO_STEP_REPRESENTATIONS)
        for response in Response
        if response in responses
        and (
            response is not Response.MULTIPLE_CHOICE
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
# A word problem as presented, with one step or two: its answer chosen from lettered numbers
type NumberChoiceQuestion = Question[
    BasicOperationQuestionData | TwoStepQuestionData, MultipleChoice[int]
]
# A word problem as presented: answered in writing, with one step or two, or its equation, with
# one step or two, or number line chosen, or its answer chosen from numbers
type WordProblemQuestion = (
    Question[BasicOperationQuestionData, FreeResponse]
    | Question[TwoStepQuestionData, FreeResponse]
    | EquationChoiceQuestion
    | TwoStepEquationChoiceQuestion
    | NumberLineChoiceQuestion
    | NumberChoiceQuestion
)


def number_choices(
    data: BasicOperationQuestionData | TwoStepQuestionData, operations: Collection[Operation]
) -> MultipleChoice[int]:
    """
    Return the numbers to choose a word problem's answer from, on a sheet of ``operations``: its
    answer and three wrong numbers, each what a mistake in working it out comes to, as
    ``_mistaken_answers`` gives them, shuffled together. The three are drawn at random among the
    sets from the most kinds of mistake, three where they can be. Only when the mistakes come to
    fewer than three numbers does the answer slipped in its last step (``_answer_slips``) join
    the numbers a little off. The wrong numbers are whole, from 0 up, and none is the answer or
    another's.
    """
    kinds = _mistaken_answers(data, operations)
    if len(set().union(*kinds.values())) < 3:
        kinds = {**kinds, "number": kinds.get("number", set()) | _answer_slips(data.answer)}
    sets = _wrong_number_sets(kinds)
    most = max(kinds_used for kinds_used, _ in sets)
    candidates = random.choice([lists for kinds_used, lists in sets if kinds_used == most])
    wrong = _distinct_pick([random.sample(each, len(each)) for each in candidates])
    assert wrong is not None  # each of ``sets`` has a pick
    return multiple_choice((data.answer,), wrong)


def _wrong_number_sets(kinds: dict[str, set[int]]) -> list[tuple[int, list[list[int]]]]:
    """
    Return the ways of choosing three wrong numbers from the numbers of ``kinds``, a kind used
    once or more, each as how many kinds it uses and the numbers each of the three can be. Only
    ways that give three different numbers.
    """
    names = sorted(kinds)
    ways = []
    for chosen in combinations_with_replacement(names, 3):
        lists = [sorted(kinds[name]) for name in chosen]
        if _distinct_pick(lists) is not None:
            ways.append((len(set(chosen)), lists))
    return ways


def _distinct_pick(lists: Sequence[Sequence[int]]) -> tuple[int, ...] | None:
    """
    Return the first numbers, one from each of ``lists`` in turn, that are all different, or
    ``None`` if there are none.
    """
    return next((each for each in product(*lists) if len(set(each)) == len(each)), None)


def _mistaken_answers(
    data: BasicOperationQuestionData | TwoStepQuestionData, operations: Collection[Operation]
) -> dict[str, set[int]]:
    """
    Return what mistakes in working out the word problem come to, by kind, on a sheet of
    ``operations``, leaving out the answer and any that aren't whole or are below 0. The kinds:

    - "sign": a sign changed to another that ``_mistaken_signs`` gives: 52 - 38 → 90;
    - "number": a number a little off, as ``_answer_slips_of`` gives it: 3 x 19 x 16 → 855;
    - "regrouping": a column slip in adding or subtracting, as ``_step_slips`` gives it:
      345 + 278 → 513, 52 - 38 → 26 or 24;
    - "quotient": a division one or two off: 42 ÷ 7 → 5 or 7, 4 or 8;

    and with two steps, where a slip in the first step is carried into the second:

    - "brackets": the steps worked in the wrong order: (24 - 6) ÷ 3 → 24 - (6 ÷ 3) = 22;
    - "step": a step left out: 18 or 2;
    - "every sign": every sign + or x, where it's one of those ``_mistaken_signs`` gives:
      (31 + 41) x 8 → 80.

    A kind with nothing to give is left out.
    """
    right = _right_equation(data)
    signs = _mistaken_signs(operations)
    worked: dict[str, list[Fraction | None]] = {
        "sign": [
            _solved(edit(right))
            for place in range(len(_signs_of(right)))
            for edit in _signs_changed(right, place, signs)
        ],
        "number": [
            _solved(_with_number(right, place, slip))
            for place, number in enumerate(_numbers_of(right))
            for slip in _answer_slips_of(number)
            if slip not in _numbers_of(right)
        ],
    }
    for kind, values in _working_slips(data).items():
        worked[kind] = list(values)
    if isinstance(data, TwoStepQuestionData):
        numbers: list[_Term] = [*_numbers_of(right)]
        worked["brackets"] = [_solved(_regrouped(right))]
        worked["step"] = [_solved(_step_kept(right, first)) for first in (True, False)]
        worked["every sign"] = [
            _solved(_rebuilt_equation(right, numbers, [sign, sign]))
            for sign in (Operation.ADD, Operation.MULTIPLY)
            if sign in signs and _signs_of(right) != [sign, sign]
        ]
    answers = {
        kind: {
            int(value)
            for value in values
            if value is not None and value.denominator == 1 and 0 <= value != data.answer
        }
        for kind, values in worked.items()
    }
    return {kind: values for kind, values in answers.items() if values}


def _answer_slips_of(number: int) -> list[int]:
    """
    Return what ``number`` might be written as by mistake in working out an answer: what
    ``_slips`` gives, and two less or more, so a wrong answer near the right one isn't always
    odd where it's even: 52 - 38 = 14 gives 13 and 15 one off, but 12 and 16 two off.
    """
    slips = _slips(number)
    return [*slips, *(slip for slip in (number - 2, number + 2) if slip > 1 and slip not in slips)]


def _working_slips(
    data: BasicOperationQuestionData | TwoStepQuestionData,
) -> dict[str, list[Fraction | None]]:
    """
    Return what slips in working out the problem's steps come to, by kind, as ``_step_slips``
    gives them: with two steps, a slip in the first is carried into the second, whose own slips
    follow. ``None`` where carrying a slip divides by 0.
    """
    if isinstance(data, BasicOperationQuestionData):
        return {
            kind: [Fraction(each) for each in slips] for kind, slips in _step_slips(data).items()
        }
    first, second = data.steps
    worked: dict[str, list[Fraction | None]] = {}
    for kind, slips in _step_slips(first).items():
        for slip in slips:
            left, right = second.operands
            if data.carried is Unknown.FIRST:
                left = slip
            else:
                right = slip
            divides_by_0 = second.operation is Operation.DIVIDE and right == 0
            value = (
                None if divides_by_0 else _worked(second.operation, Fraction(left), Fraction(right))
            )
            worked.setdefault(kind, []).append(value)
    for kind, slips in _step_slips(second).items():
        worked.setdefault(kind, []).extend(Fraction(each) for each in slips)
    return worked


def _step_slips(step: BasicOperationQuestionData) -> dict[str, list[int]]:
    """
    Return what slips in working out the step come to, by kind: in adding, the carrying
    forgotten (``_carries_dropped``); in subtracting a smaller number, the smaller digit taken
    from the larger in each column (``_smaller_digits_taken``) or the ten borrowed but not taken
    from the next column (``_borrows_kept``), both "regrouping"; in dividing, one or two less or
    more ("quotient"). A slip may come to the step's own answer, where there's nothing to regroup.
    """
    first, second = step.operands
    match step.operation:
        case Operation.ADD:
            return {"regrouping": [_carries_dropped(first, second)]}
        case Operation.SUBTRACT:
            if first < second:
                return {}
            return {
                "regrouping": [_smaller_digits_taken(first, second), _borrows_kept(first, second)]
            }
        case Operation.MULTIPLY:
            return {}
        case Operation.DIVIDE:
            return {"quotient": [step.answer + off for off in (-2, -1, 1, 2)]}
        case _:
            assert_never(step.operation)


def _carries_dropped(first: int, second: int) -> int:
    """
    Return ``first`` + ``second`` added column by column with nothing carried, the last column
    written whole: 345 + 278 → 513, and 852 + 461 → 1,213.
    """
    total, place = 0, 1
    while first >= 10 or second >= 10:
        total += (first % 10 + second % 10) % 10 * place
        first, second, place = first // 10, second // 10, place * 10
    return total + (first + second) * place


def _smaller_digits_taken(first: int, second: int) -> int:
    """
    Return ``first`` - ``second`` taken column by column, the smaller digit from the larger in
    each: 52 - 38 → 26, and 400 - 123 → 323.
    """
    total, place = 0, 1
    while first or second:
        total += abs(first % 10 - second % 10) * place
        first, second, place = first // 10, second // 10, place * 10
    return total


def _borrows_kept(first: int, second: int) -> int:
    """
    Return ``first`` - ``second`` taken column by column, a column with too small a digit given
    ten from the next, which isn't made one less: 52 - 38 → 24, and 400 - 123 → 387.
    """
    total, place = 0, 1
    while first or second:
        top, bottom = first % 10, second % 10
        total += (top + 10 - bottom if top < bottom else top - bottom) * place
        first, second, place = first // 10, second // 10, place * 10
    return total


def _answer_slips(answer: int) -> set[int]:
    """
    Return ``answer`` slipped in its last step: 1 or 2 less or more, 10 less or more, or its
    digits the other way round, as ``_reversed_digits`` gives them, from 0 up and other than the
    answer.
    """
    slips = {answer - 2, answer - 1, answer + 1, answer + 2, answer - 10, answer + 10}
    slips.add(_reversed_digits(answer))
    return {slip for slip in slips if 0 <= slip != answer}


def equation_choices(
    data: BasicOperationQuestionData, operations: Collection[Operation]
) -> MultipleChoice[str]:
    """
    Return the equations to choose from for a word problem on a sheet of ``operations``: its own,
    with a ``BLANK`` for what to find, as in 47 + 25 = □, and three wrong ones that cross two
    kinds of mistake, as ``two_step_equation_choices`` describes for two steps. A one-step
    equation's mistakes are its sign changed (47 - 25 = □), a number a little off
    (47 + 26 = □), and what to find swapped with a number (□ + 25 = 47). With all four
    operations, the other three on its numbers (47 - 25, 47 x 25 and 47 ÷ 25, each = □) are one
    more set to draw from.

    Raises ``ValueError`` if no set is fair.
    """
    right, wrong = _chosen_set(data, operations)
    return multiple_choice(
        (_equation_text(right, BLANK),),
        tuple(_equation_text(equation, BLANK) for equation in wrong),
    )


# A written equation's term: a number, the letter for what to find, or two terms joined by a sign
type _Term = int | _Letter | _Joined


class _Letter(Enum):
    """What to find in a written equation, written as a problem's letter or as a ``BLANK``."""

    LETTER = "letter"


_LETTER = _Letter.LETTER


@dataclass(frozen=True)
class _Joined:
    """
    Two terms of a written equation joined by a sign, left to right: 24 - 6 is
    ``_Joined(SUBTRACT, 24, 6)``. Joined terms inside another are written in brackets.
    """

    sign: Operation
    left: _Term
    right: _Term


@dataclass(frozen=True)
class _Equation:
    """
    A written equation's two sides: (24 - 6) ÷ 3 = s is
    ``_Equation(_Joined(DIVIDE, _Joined(SUBTRACT, 24, 6), 3), _LETTER)``, and 3 x 19 = 16 x e
    is ``_Equation(_Joined(MULTIPLY, 3, 19), _Joined(MULTIPLY, 16, _LETTER))``.
    """

    left: _Term
    right: _Term


def _two_step_side(data: TwoStepQuestionData) -> _Joined:
    """
    Return the two-step question's equation as written, without what it equals: its first step
    in brackets, as in (24 - 6) ÷ 3 or 45 - (5 x 3).
    """
    first, second = data.steps
    first_step = _Joined(first.operation, *first.operands)
    if data.carried is Unknown.FIRST:  # (a ○ b) ● c
        return _Joined(second.operation, first_step, second.operands[1])
    return _Joined(second.operation, second.operands[0], first_step)  # c ● (a ○ b)


def _term_text(term: _Term, letter: str, *, inner: bool = False) -> str:
    """
    Return the term as written, with ``letter`` for what to find and a comma in 1,000 and up. A
    joined term is in brackets if it's ``inner``, inside another.
    """
    match term:
        case _Letter.LETTER:
            return letter
        case _Joined(sign, left, right):
            left_text = _term_text(left, letter, inner=True)
            text = f"{left_text} {SYMBOLS[sign]} {_term_text(right, letter, inner=True)}"
            return f"({text})" if inner else text
        case int():
            return f"{term:,}"
        case _:
            assert_never(term)


def _equation_text(equation: _Equation, letter: str) -> str:
    """Return the written equation, as in (24 - 6) ÷ 3 = s, with ``letter`` for what to find."""
    return f"{_term_text(equation.left, letter)} = {_term_text(equation.right, letter)}"


def two_step_equation_choices(
    data: TwoStepQuestionData, unknown: str, operations: Collection[Operation]
) -> MultipleChoice[str]:
    """
    Return the equations to choose from for a two-step word problem on a sheet of
    ``operations``: its own, with its first step in brackets and ``unknown`` for what to find, as
    in (24 - 6) ÷ 3 = s, and three wrong ones.

    The wrong equations cross two kinds of mistake: one wrong equation has one, one the other,
    and one both, so each change is in exactly two of the four choices, and no choice is the one
    most like the others. The kinds, as ``_mistake_pairs`` pairs them:

    - the first sign written changed, or the second, each its own kind, to another of the signs
      ``_mistaken_signs`` gives: (24 + 6) ÷ 3 = s;
    - a number a little off, as ``_slips`` gives it: (24 - 7) ÷ 3 = s;
    - the brackets moved to the other pair of numbers: 24 - (6 ÷ 3) = s;

    and, made last because they change the equation's shape:

    - the step outside the brackets written the other way round: 3 ÷ (24 - 6) = s;
    - what to find swapped with a number, which stands alone on the other side:
      (24 - s) ÷ 3 = 6;
    - the equals sign moved between the second number and the third: 24 - 6 = 3 ÷ s;
    - a step left out: 24 - 6 = s, or 6 ÷ 3 = s.

    Which two kinds, and which ways of making them, are drawn at random among those that make a
    fair set. The right equation has the problem's numbers in the story's order.

    A set is fair, as ``_is_fair`` checks, when what to find in each wrong equation works out
    differently from the answer and from the others', and none can be ruled out without working
    it out. Working out to an uneven number or one below zero is allowed, as in (25 + 5) ÷ 4.

    Raises ``ValueError`` if no set is fair.
    """
    right, wrong = _chosen_set(data, operations)
    return multiple_choice(
        (_equation_text(right, unknown),),
        tuple(_equation_text(equation, unknown) for equation in wrong),
    )


def has_fair_equation_choices(
    data: BasicOperationQuestionData | TwoStepQuestionData, operations: Collection[Operation]
) -> bool:
    """
    Return whether ``equation_choices``, or ``two_step_equation_choices`` for a two-step word
    problem, can give the problem a fair set of wrong equations on a sheet of ``operations``.
    """
    return next(_fair_sets(data, operations), None) is not None


def _chosen_set(
    data: BasicOperationQuestionData | TwoStepQuestionData, operations: Collection[Operation]
) -> tuple[_Equation, tuple[_Equation, ...]]:
    """
    Return the question's right equation and a fair set of wrong ones, drawn at random: first a
    pair of kinds of mistake among those of the earliest tier with a fair set, a kind made at
    different places counting as one, then one of its sets.

    Raises ``ValueError`` if no set is fair.
    """
    right = _right_equation(data)
    chosen: int | None = None
    sets: dict[tuple[str, ...], list[tuple[_Equation, ...]]] = {}
    for tier, mistakes, wrong in _fair_sets(data, operations):
        if chosen is not None and tier != chosen:
            break
        chosen = tier
        sets.setdefault(mistakes, []).append(wrong)
    if chosen is None:
        raise ValueError(f"No fair wrong equations for {_term_text(right.left, '?')}.")
    return right, random.choice(random.choice(list(sets.values())))


def _right_equation(data: BasicOperationQuestionData | TwoStepQuestionData) -> _Equation:
    """
    Return the question's own equation as written, with what to find alone on its right: one
    step in the story's order, or two with the first in brackets.
    """
    if isinstance(data, BasicOperationQuestionData):
        return _Equation(_Joined(data.operation, *data.operands), _LETTER)
    return _Equation(_two_step_side(data), _LETTER)


# A change to a written equation, one way of making a mistake. It makes the same change in any
# equation of the shape it was made for, so two kinds of mistake can be made together.
type _Edit = Callable[[_Equation], _Equation]
# A kind of mistake: it returns the ways of making it in an equation
type _Mistake = Callable[[_Equation], list[_Edit]]
# A kind of mistake, named, as the same name for the kind made at each place, with its ways
type _Kind = tuple[str, _Mistake]
# two kinds of mistake for wrong choices to cross, the second made last
type _MistakePair = tuple[_Kind, _Kind]


def _fair_sets(
    data: BasicOperationQuestionData | TwoStepQuestionData, operations: Collection[Operation]
) -> Iterator[tuple[int, tuple[str, ...], tuple[_Equation, ...]]]:
    """
    Yield every fair set of three wrong equations for the question on a sheet of
    ``operations``, each with the tier of its pair of kinds of mistake, as ``_mistake_pairs``
    gives them, and the names of the kinds, in order of tier. With one step and all four
    operations, the other three operations on its numbers are one more set, in the first tier.
    """
    right = _right_equation(data)
    answer = _solved(right)
    for tier, pairs in enumerate(_mistake_pairs(right, operations)):
        for (one_name, one), (other_name, other) in pairs:
            for wrong in _crossed_mistakes(right, one, other):
                if _is_fair(answer, wrong):
                    yield tier, (one_name, other_name), wrong
        if tier == 0 and len(_numbers_of(right)) == 2 and set(operations) >= set(Operation):
            others = _other_operations(right)
            if _is_fair(answer, others):
                yield tier, ("other operations",), others


def _crossed_mistakes(
    right: _Equation, one: _Mistake, other: _Mistake
) -> Iterator[tuple[_Equation, _Equation, _Equation]]:
    """
    Yield every set of three wrong equations that crosses the mistakes ``one`` and ``other`` in
    ``right``: a way of making the first, a way of making the second, and both at once.
    """
    seconds = other(right)
    for first in one(right):
        once = first(right)
        for second in seconds:
            yield once, second(right), second(once)


def _mistake_pairs(right: _Equation, operations: Collection[Operation]) -> list[list[_MistakePair]]:
    """
    Return the pairs of kinds of mistake a right equation's wrong choices can cross, on a sheet
    of ``operations``: any two that keep its shape (the sign changed and a number a little off,
    each place its own kind, and with two steps the brackets moved), or one of those and one
    made last that changes the shape (what to find swapped with a number, and with two steps the
    step outside the brackets the other way round, the equals moved and a step left out).

    They come in two tiers, the second used only when no pair of the first gives a fair set. The
    second holds two places of one kind, whose wrong choices one check rules out: a number that
    isn't the story's, or a sign that no problem on the sheet has. Signs on a sheet of two or
    more operations stay in the first, as any of them can be right.
    """
    signs = _mistaken_signs(operations)
    keep_shape: list[_Kind] = [
        *(
            ("sign", partial(_signs_changed, place=place, signs=signs))
            for place in range(len(_signs_of(right)))
        ),
        *(
            ("number", partial(_numbers_off, place=place))
            for place in range(len(_numbers_of(right)))
        ),
    ]
    change_shape: list[_Kind] = [("letter", _letters_swapped)]
    if len(_numbers_of(right)) == 3:
        keep_shape.append(("brackets", _brackets_moved))
        change_shape = [
            ("order", _order_swapped),
            ("letter", _letters_swapped),
            ("equals", _equals_moved),
            ("step", _steps_left_out),
        ]
    pairs = [*combinations(keep_shape, 2), *product(keep_shape, change_shape)]
    several = len(set(operations)) > 1
    one_check = [
        (one, other)
        for one, other in pairs
        if one[0] == other[0] and not (several and one[0] == "sign")
    ]
    return [[pair for pair in pairs if pair not in one_check], one_check]


# The sign written by mistake for each operation, on a sheet of that operation alone
_MISTAKEN_SIGNS = {
    Operation.ADD: Operation.SUBTRACT,
    Operation.SUBTRACT: Operation.ADD,
    Operation.MULTIPLY: Operation.ADD,
    Operation.DIVIDE: Operation.MULTIPLY,
}


def _mistaken_signs(operations: Collection[Operation]) -> frozenset[Operation]:
    """
    Return the signs a wrong equation can have on a sheet of ``operations``: the sheet's own, as
    a sign that no problem on the sheet has in its own equation would rule a choice out, or with
    one operation alone, it and the sign ``_MISTAKEN_SIGNS`` gives for it.
    """
    signs = frozenset(operations)
    if len(signs) == 1:
        (sign,) = signs
        return signs | {_MISTAKEN_SIGNS[sign]}
    return signs


def _signs_changed(right: _Equation, place: int, signs: Collection[Operation]) -> list[_Edit]:
    """
    Return the ways of changing the sign at ``place``, counting from 0 left to right, to another
    of ``signs``, in ``Operation``'s order.
    """
    current = _signs_of(right)[place]
    return [
        partial(_with_sign, place=place, sign=sign)
        for sign in Operation
        if sign in signs and sign is not current
    ]


def _numbers_off(right: _Equation, place: int) -> list[_Edit]:
    """
    Return the ways of writing the equation's number at ``place``, counting from 0 left to
    right, a little off, as ``_slips`` gives them. A slip that's another of its numbers is left
    out.
    """
    numbers = _numbers_of(right)
    return [
        partial(_with_number, place=place, number=slip)
        for slip in _slips(numbers[place])
        if slip not in numbers
    ]


def _slips(number: int) -> list[int]:
    """
    Return what ``number`` might be written as by mistake, a little off: one less, one more, its
    digits the other way round (21 for 12, as ``_reversed_digits`` gives it), and for a number of
    two digits or more, ten less and ten more. Only numbers from 2 up, as 1 x (3 x 8) reads as no
    mistake anyone makes, and other than ``number``.
    """
    slips = [number - 1, number + 1, _reversed_digits(number)]
    if number >= 10:
        slips += [number - 10, number + 10]
    return [slip for slip in dict.fromkeys(slips) if 1 < slip != number]


def _reversed_digits(number: int) -> int:
    """
    Return ``number`` with its digits the other way round, as 21 for 12, or ``number`` itself if
    the copy would start with 0, as 30's would.
    """
    return number if number % 10 == 0 else int(str(number)[::-1])


def _brackets_moved(right: _Equation) -> list[_Edit]:
    """Return the way of moving a two-step equation's brackets to the other pair of numbers."""
    return [_regrouped]


def _regrouped(equation: _Equation) -> _Equation:
    """Return the two-step equation with its brackets around the other pair of numbers."""
    match equation.left:
        case _Joined(outer, _Joined(inner, first, second), int() as third):
            return replace(equation, left=_Joined(inner, first, _Joined(outer, second, third)))
        case _Joined(outer, int() as first, _Joined(inner, second, third)):
            return replace(equation, left=_Joined(inner, _Joined(outer, first, second), third))
        case _:
            raise ValueError(f"Not a two-step equation: {_equation_text(equation, '?')}.")


def _order_swapped(right: _Equation) -> list[_Edit]:
    """
    Return the way of writing the step outside a two-step equation's brackets the other way
    round: the brackets and the number outside them swap places, so (45 - 12) - 8 is
    8 - (45 - 12).
    """
    return [_outer_swapped]


def _outer_swapped(equation: _Equation) -> _Equation:
    """Return the equation with the two terms of its left side's outer step swapped."""
    side = equation.left
    if not isinstance(side, _Joined):
        raise ValueError(f"Not a two-step equation: {_equation_text(equation, '?')}.")
    return replace(equation, left=_Joined(side.sign, side.right, side.left))


def _letters_swapped(right: _Equation) -> list[_Edit]:
    """
    Return the ways of swapping what to find with one of the equation's numbers, left to right:
    the letter takes the number's place, and the number stands alone on the other side, so
    47 + 25 = □ gives □ + 25 = 47 and 47 + □ = 25.
    """
    return [partial(_letter_swapped, place=place) for place in range(len(_numbers_of(right)))]


def _letter_swapped(equation: _Equation, place: int) -> _Equation:
    """
    Return the equation, which has what to find alone on its right, with the letter in place of
    the number at ``place`` and that number on the right.
    """
    numbers: list[_Term] = [*_numbers_of(equation)]
    number = numbers[place]
    numbers[place] = _LETTER
    return _Equation(_rebuilt(equation.left, iter(numbers), iter(_signs_of(equation))), number)


def _equals_moved(right: _Equation) -> list[_Edit]:
    """
    Return the way of moving a two-step equation's equals sign between its second number and its
    third, so (3 x 19) x 16 = e is 3 x 19 = 16 x e.
    """
    return [_split]


def _split(equation: _Equation) -> _Equation:
    """Return the two-step equation split after its second number, as ``_equals_moved`` says."""
    first, second, third = _numbers_of(equation)
    first_sign, second_sign = _signs_of(equation)
    return _Equation(_Joined(first_sign, first, second), _Joined(second_sign, third, _LETTER))


def _steps_left_out(right: _Equation) -> list[_Edit]:
    """
    Return the ways of stopping a two-step equation after one step: its first two numbers with
    its first sign, then its last two with its second, as either step can come first in adding
    or multiplying three numbers. (12 + 8) + 5 gives 12 + 8 and 8 + 5.
    """
    return [partial(_step_kept, first=True), partial(_step_kept, first=False)]


def _step_kept(equation: _Equation, first: bool) -> _Equation:
    """Return the two-step equation stopped after one step, as ``_steps_left_out`` says."""
    numbers = _numbers_of(equation)
    first_sign, second_sign = _signs_of(equation)
    if first:
        return _Equation(_Joined(first_sign, numbers[0], numbers[1]), _LETTER)
    return _Equation(_Joined(second_sign, numbers[1], numbers[2]), _LETTER)


_ORDERED = frozenset({Operation.SUBTRACT, Operation.DIVIDE})  # the larger number written first


def _other_operations(right: _Equation) -> tuple[_Equation, _Equation, _Equation]:
    """
    Return the other three operations on a one-step equation's numbers, each with what to find
    alone on its right: in the story's order to add or multiply, and the larger number first to
    subtract or divide.
    """
    first, second = _numbers_of(right)
    (own,) = _signs_of(right)
    larger, smaller = max(first, second), min(first, second)
    first_other, second_other, third_other = (
        _Equation(
            _Joined(sign, *((larger, smaller) if sign in _ORDERED else (first, second))), _LETTER
        )
        for sign in Operation
        if sign is not own
    )
    return first_other, second_other, third_other


def _numbers_of(equation: _Equation) -> list[int]:
    """Return the equation's numbers, left to right."""
    return [*_term_numbers(equation.left), *_term_numbers(equation.right)]


def _term_numbers(term: _Term) -> Iterator[int]:
    """Yield the term's numbers, left to right."""
    match term:
        case _Joined(_, left, right):
            yield from _term_numbers(left)
            yield from _term_numbers(right)
        case int():
            yield term


def _signs_of(equation: _Equation) -> list[Operation]:
    """Return the equation's signs, left to right, without its equals sign."""
    return [*_term_signs(equation.left), *_term_signs(equation.right)]


def _term_signs(term: _Term) -> Iterator[Operation]:
    """Yield the term's signs, left to right."""
    if isinstance(term, _Joined):
        yield from _term_signs(term.left)
        yield term.sign
        yield from _term_signs(term.right)


def _with_number(equation: _Equation, place: int, number: int) -> _Equation:
    """Return the equation with ``number`` in place of its number at ``place``, from 0."""
    numbers: list[_Term] = [*_numbers_of(equation)]
    numbers[place] = number
    return _rebuilt_equation(equation, numbers, _signs_of(equation))


def _with_sign(equation: _Equation, place: int, sign: Operation) -> _Equation:
    """Return the equation with ``sign`` in place of its sign at ``place``, from 0."""
    signs = _signs_of(equation)
    signs[place] = sign
    return _rebuilt_equation(equation, [*_numbers_of(equation)], signs)


def _rebuilt_equation(
    equation: _Equation, numbers: Sequence[_Term], signs: Sequence[Operation]
) -> _Equation:
    """Return the equation with its numbers and signs, left to right, replaced in turn."""
    number_terms, sign_terms = iter(numbers), iter(signs)
    left = _rebuilt(equation.left, number_terms, sign_terms)
    return _Equation(left, _rebuilt(equation.right, number_terms, sign_terms))


def _rebuilt(term: _Term, numbers: Iterator[_Term], signs: Iterator[Operation]) -> _Term:
    """
    Return the term with its numbers and signs, left to right, taken in turn from ``numbers`` and
    ``signs``. The letter for what to find stays.
    """
    match term:
        case _Joined(_, left, right):
            new_left = _rebuilt(left, numbers, signs)
            sign = next(signs)
            return _Joined(sign, new_left, _rebuilt(right, numbers, signs))
        case int():
            return next(numbers)
        case _:
            return term


def _is_fair(answer: Fraction | None, wrong: Sequence[_Equation]) -> bool:
    """
    Return whether every equation of ``wrong`` needs working out to rule out, and what to find in
    each works out differently from ``answer`` and from the others: a wrong equation with the
    answer would be a second right one, and two with the same value, as (5 + 3) + 2 and
    5 + (3 + 2), would rule each other out. An equation that can't be worked out, dividing by 0,
    isn't fair.
    """
    values: list[Fraction] = []
    for equation in wrong:
        value = _solved(equation)
        if value is None or _ruled_out_at_a_glance(equation, value):
            return False
        values.append(value)
    return len({answer, *values}) == len(wrong) + 1


def _ruled_out_at_a_glance(equation: _Equation, value: Fraction) -> bool:
    """
    Return whether the wrong equation, in which what to find works out to ``value``, can be ruled
    out without working it out: two numbers side by side in it take a number from one no larger
    or divide a number by a larger one, as 3 - 5 and 3 ÷ 5 do, or what to find shares its side
    with a number and works out below 1, as in (3 x 19) x e = 16.
    """
    if _LETTER not in (equation.left, equation.right) and value < 1:
        return True
    return any(
        _pair_ruled_out(joined)
        for side in (equation.left, equation.right)
        for joined in _joined_terms(side)
    )


def _pair_ruled_out(joined: _Joined) -> bool:
    """
    Return whether the joined term is two numbers that take a number from one no larger, or
    divide a number by a larger one, as 3 - 5 and 3 ÷ 5 do.
    """
    if not (isinstance(joined.left, int) and isinstance(joined.right, int)):
        return False
    match joined.sign:
        case Operation.SUBTRACT:
            return joined.left <= joined.right
        case Operation.DIVIDE:
            return joined.left < joined.right
        case Operation.ADD | Operation.MULTIPLY:
            return False
        case _:
            assert_never(joined.sign)


def _joined_terms(term: _Term) -> Iterator[_Joined]:
    """Yield the joined terms in ``term``, itself included, outer ones first."""
    if isinstance(term, _Joined):
        yield term
        yield from _joined_terms(term.left)
        yield from _joined_terms(term.right)


def _solved(equation: _Equation) -> Fraction | None:
    """
    Return what the letter stands for in the written equation, worked out exactly, or ``None``
    if working it out divides by 0.
    """
    if _holds_letter(equation.left):
        return _solved_for(equation.left, _evaluated(equation.right))
    return _solved_for(equation.right, _evaluated(equation.left))


def _solved_for(term: _Term, value: Fraction | None) -> Fraction | None:
    """
    Return what the letter stands for when ``term``, which holds it, works out to ``value``, or
    ``None`` if either can't be worked out.
    """
    if value is None or not isinstance(term, _Joined):
        return value
    if _holds_letter(term.left):
        known = _evaluated(term.right)
        return _solved_for(term.left, _undone(term.sign, value, known, letter_first=True))
    known = _evaluated(term.left)
    return _solved_for(term.right, _undone(term.sign, value, known, letter_first=False))


def _undone(
    sign: Operation, value: Fraction, known: Fraction | None, *, letter_first: bool
) -> Fraction | None:
    """
    Return what the term holding the letter must work out to, joined by ``sign`` with ``known``,
    after it if ``letter_first`` and before it otherwise, to give ``value``. ``None`` if
    ``known`` can't be worked out or the answer divides by 0.
    """
    if known is None:
        return None
    match sign:
        case Operation.ADD:
            return value - known
        case Operation.SUBTRACT:
            return value + known if letter_first else known - value
        case Operation.MULTIPLY:
            return None if known == 0 else value / known
        case Operation.DIVIDE:
            if letter_first:
                return value * known
            return None if value == 0 else known / value
        case _:
            assert_never(sign)


def _holds_letter(term: _Term) -> bool:
    """Return whether the term holds the letter for what to find."""
    match term:
        case _Joined(_, left, right):
            return _holds_letter(left) or _holds_letter(right)
        case int():
            return False
        case _:
            return True


def _evaluated(term: _Term) -> Fraction | None:
    """
    Return the term, which doesn't hold the letter, worked out exactly, or ``None`` if working
    it out divides by 0.
    """
    match term:
        case _Joined(sign, left, right):
            left_value, right_value = _evaluated(left), _evaluated(right)
            if left_value is None or right_value is None:
                return None
            if sign is Operation.DIVIDE and right_value == 0:
                return None
            return _worked(sign, left_value, right_value)
        case int():
            return Fraction(term)
        case _:
            raise ValueError("A term holding the letter can't be worked out on its own.")


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


# How to answer a problem whose answer is chosen from numbers, after the representation's
# instruction; and on a representation's problems answered both in writing and that way
CHOOSE_NUMBER = "Circle the correct answer."
CHOOSE_NUMBER_WHERE_GIVEN = "Where there are choices, circle the correct answer."


def instruction(
    representation: Representation,
    operations: Collection[Operation],
    work_box: bool,
    choices: bool = False,
    two_steps: bool = False,
    number_choices: bool = False,
) -> str:
    """
    Return the instruction printed under a word-problem sheet's header, for its representation and
    the operations of its problems. ``work_box`` is for text only: whether each problem has a box
    to show the work in. ``choices`` is for number lines and equations: whether each problem's is
    chosen from lettered ones. ``two_steps`` is for equations to choose from: whether the problems
    have two steps, whose equations have a letter for what to find. With ``number_choices``, each
    problem's answer is chosen from lettered numbers: the instruction for writing it, followed by
    ``CHOOSE_NUMBER``, and for equations, which have no line to write one on then, text only's
    without a box.
    """
    if number_choices:
        if representation is Representation.EQUATION:
            return f"{instruction(Representation.NONE, operations, False)} {CHOOSE_NUMBER}"
        return f"{instruction(representation, operations, work_box)} {CHOOSE_NUMBER}"
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
