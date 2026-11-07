"""
Base-ten blocks, and sheets of questions shown with them: writing the number the blocks show, and
adding and subtracting with them, mixed on one sheet.

Writing the number is a place-value question whose number is given as blocks. Adding and
subtracting are basic-operation questions drawn as blocks: both numbers, to combine, for a sum,
and the first number, to cross out from, for a difference.
"""

import random
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import islice
from typing import Literal, assert_never

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.regrouping import Regrouping, fits_regrouping
from core.basic_operations.representation import OPERATION_NAMES, equation
from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.placevalue.representation import format_number
from core.question import Question
from core.self_check_tiles import TileQuestion

LARGEST_BLOCKS_NUMBER = 999  # base-ten blocks go up to the hundreds' flats
# The largest number drawn as blocks: an operand of a word problem or sheet question, or a number
# to write. A number has at most 5 flats, so they fit in one row.
LARGEST_BLOCKS_OPERAND = 599
# Every number on the legacy sheet, answers included, was at least 100, so each had a flat.
DEFAULT_SMALLEST_BLOCKS_NUMBER = 100

# What each base-ten block is called, keyed by its value, largest first, as a sheet's key names
# them
BLOCK_NAMES = {100: "flat", 10: "rod", 1: "unit"}


@dataclass(frozen=True)
class BaseTenBlocks:
    """A number shown as base-ten blocks: ``hundreds`` flats, ``tens`` rods and ``ones`` units."""

    hundreds: int
    tens: int
    ones: int


def base_ten_blocks(number: int) -> BaseTenBlocks:
    """
    Return the fewest base-ten blocks that show ``number``: one block for each unit of each
    digit, so 347 is 3 flats, 4 rods and 7 units.

    Raises ``ValueError`` for a number below 0 or above ``LARGEST_BLOCKS_NUMBER``.
    """
    if not 0 <= number <= LARGEST_BLOCKS_NUMBER:
        raise ValueError(
            f"Base-ten blocks show numbers from 0 to {LARGEST_BLOCKS_NUMBER}, not {number}."
        )
    hundreds, rest = divmod(number, 100)
    tens, ones = divmod(rest, 10)
    return BaseTenBlocks(hundreds, tens, ones)


@dataclass(frozen=True)
class BlocksDiagram:
    """
    Base-ten blocks for a word problem: ``numbers`` drawn as blocks, one under another, and the
    amount to cross out of the last of them, or None if none is crossed out.

    47 + 25 is ``((BaseTenBlocks(0, 4, 7), BaseTenBlocks(0, 2, 5)), None)``, and 72 - 25 is
    ``((BaseTenBlocks(0, 7, 2),), 25)``.
    """

    numbers: tuple[BaseTenBlocks, ...]
    cross_out: int | None


def blocks_diagram(data: BasicOperationQuestionData) -> BlocksDiagram:
    """
    Return the base-ten blocks for a question.

    Addition shows both operands, to combine. Subtraction shows its first operand, with its
    second as the amount to cross out. Base-ten blocks show only addition and subtraction, so any
    other operation raises ``ValueError``.
    """
    first, second = data.operands
    match data.operation:
        case Operation.ADD:
            return BlocksDiagram((base_ten_blocks(first), base_ten_blocks(second)), None)
        case Operation.SUBTRACT:
            return BlocksDiagram((base_ten_blocks(first),), second)
        case Operation.MULTIPLY | Operation.DIVIDE:
            name = OPERATION_NAMES[data.operation].lower()
            raise ValueError(f"Base-ten blocks show only addition and subtraction, not {name}.")
        case _:
            assert_never(data.operation)


type BlocksQuestionData = PlaceValueQuestionData | BasicOperationQuestionData


class BlocksQuestionType(StrEnum):
    """
    A type of question on a base-ten blocks sheet. Values are stable identifiers for the API and
    storage.
    """

    WRITE_NUMBER = "write_number"  # write the number the blocks show
    ADD = "add"  # combine two numbers' blocks
    SUBTRACT = "subtract"  # cross out blocks from a number


# What each type is called on the web page
BLOCKS_QUESTION_NAMES = {
    BlocksQuestionType.WRITE_NUMBER: "Write the number",
    BlocksQuestionType.ADD: "Add",
    BlocksQuestionType.SUBTRACT: "Subtract",
}

_OPERATIONS: dict[BlocksQuestionType, Literal[Operation.ADD, Operation.SUBTRACT]] = {
    BlocksQuestionType.ADD: Operation.ADD,
    BlocksQuestionType.SUBTRACT: Operation.SUBTRACT,
}


def blocks_prompt(data: BlocksQuestionData) -> str:
    """Return what the question asks the student to do, in the legacy sheet's wording."""
    match data:
        case PlaceValueQuestionData():
            return "Write the number shown by the blocks."
        case BasicOperationQuestionData(operation=Operation.ADD):
            return "Combine the blocks. Regroup if you can, then write the sum."
        case BasicOperationQuestionData(operation=Operation.SUBTRACT):
            return (
                "Cross out blocks to subtract. Break a hundred or ten if needed; write the "
                "difference."
            )
        case _:
            raise ValueError("Base-ten blocks show only addition and subtraction.")


def blocks_question_diagram(data: BlocksQuestionData) -> BlocksDiagram:
    """
    Return the blocks drawn for the question: the number to write, or as in ``blocks_diagram``,
    both numbers of a sum, or the first number of a difference with the second to cross out.
    """
    match data:
        case PlaceValueQuestionData():
            return BlocksDiagram((base_ten_blocks(data.answer),), None)
        case BasicOperationQuestionData():
            return blocks_diagram(data)
        case _:
            assert_never(data)


def blocks_answer_label(data: BlocksQuestionData) -> str:
    """
    Return the text before the box the answer is written in: "=" after the blocks of a number
    to write, "Sum =" for a sum, and the equation for a difference, "572 - 145 =", which says
    how many blocks to cross out.
    """
    match data:
        case PlaceValueQuestionData():
            return "="
        case BasicOperationQuestionData(operation=Operation.ADD):
            return "Sum ="
        case BasicOperationQuestionData():
            return f"{equation(data)} ="
        case _:
            assert_never(data)


def blocks_solution(data: BlocksQuestionData) -> str:
    """Return the question's line in the answer key: the number, or the equation and answer."""
    match data:
        case PlaceValueQuestionData():
            return format_number(data.answer, PlaceValueForm.STANDARD)
        case BasicOperationQuestionData():
            return f"{equation(data)} = {data.answer}"
        case _:
            assert_never(data)


def blocks_tile_question(data: BlocksQuestionData) -> TileQuestion:
    """Convert the question to a ``TileQuestion`` for the self-check tiles case."""
    return TileQuestion(
        prompt=blocks_prompt(data), answer=str(data.answer), solution=blocks_solution(data)
    )


def count_possible_blocks_questions(
    types: Sequence[BlocksQuestionType],
    *,
    smallest: int = DEFAULT_SMALLEST_BLOCKS_NUMBER,
    largest: int = LARGEST_BLOCKS_NUMBER,
    regrouping: Regrouping = Regrouping.MIXED,
    distinct_answers: bool = False,
    up_to: int,
) -> int:
    """
    Count the questions ``generate_blocks_questions`` can produce for ``types``, with its limits,
    up to ``up_to``.

    The questions are shared evenly among the types, and when they don't divide evenly, any type
    may be given an extra one, so each type needs enough distinct questions for the larger share.

    With ``distinct_answers``, a type also needs answers that the types made before it haven't
    taken. The types are made from the one with the fewest distinct answers to the one with the
    most, and each needs at least as many as the questions dealt to it and to the types before
    it, counting the extra questions as dealt to the first types, where they need the most. That
    is enough, though not always necessary: types whose answers don't overlap could share more.
    """
    if not types:
        return 0
    available = sorted(
        _available(question_type, smallest, largest, regrouping, distinct_answers, up_to)
        for question_type in types
    )
    possible = 0
    while possible < up_to and _can_share(possible + 1, available, distinct_answers):
        possible += 1
    return possible


def generate_blocks_questions(
    count: int,
    types: Sequence[BlocksQuestionType],
    *,
    smallest: int = DEFAULT_SMALLEST_BLOCKS_NUMBER,
    largest: int = LARGEST_BLOCKS_NUMBER,
    regrouping: Regrouping = Regrouping.MIXED,
    distinct_answers: bool = False,
) -> list[Question[BlocksQuestionData]]:
    """
    Generate ``count`` questions shown with base-ten blocks, shared as evenly as possible among
    ``types`` and then shuffled. When ``count`` doesn't divide evenly, the extra questions go to
    types chosen at random. With ``distinct_answers``, the types are made from the one with the
    fewest distinct answers to the one with the most, as counted by
    ``count_possible_blocks_questions``.

    Every number in a question, its answer included, is from ``smallest`` to ``largest``, and
    every number drawn as blocks is also at most ``LARGEST_BLOCKS_OPERAND``, so that its flats
    fit in one row. Additions and subtractions also fit ``regrouping``. The questions are
    answered in writing, so they have no wrong answers.

    No question repeats, and with ``distinct_answers`` no two questions share an answer either:
    a question that breaks either rule is drawn again.

    Raises ``ValueError`` if ``types`` is empty, or if the limits allow fewer than ``count`` such
    questions, as counted by ``count_possible_blocks_questions``.
    """
    if not types:
        raise ValueError("A sheet needs at least one type of question.")
    possible = count_possible_blocks_questions(
        types,
        smallest=smallest,
        largest=largest,
        regrouping=regrouping,
        distinct_answers=distinct_answers,
        up_to=count,
    )
    if count > possible:
        kind = "questions with different answers" if distinct_answers else "different questions"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    order = list(types)
    if distinct_answers:
        # fewest answers first, so each type finds answers the earlier ones left, as counted
        order.sort(key=lambda kind: _available(kind, smallest, largest, regrouping, True, count))
    share, extra = divmod(count, len(order))
    given_extra = random.sample(range(len(order)), extra)
    seen: set[BlocksQuestionData] = set()
    answers: set[int] = set()
    questions: list[Question[BlocksQuestionData]] = []
    for index, question_type in enumerate(order):
        for _ in range(share + 1 if index in given_extra else share):
            data = _draw(question_type, smallest, largest, regrouping)
            while data in seen or (distinct_answers and data.answer in answers):
                data = _draw(question_type, smallest, largest, regrouping)
            seen.add(data)
            answers.add(data.answer)
            questions.append(Question(data, ()))
    random.shuffle(questions)
    return questions


def _largest_shown(largest: int) -> int:
    """Return the largest number drawn as blocks, an operand or a number to write."""
    return min(largest, LARGEST_BLOCKS_OPERAND)


def _available(
    question_type: BlocksQuestionType,
    smallest: int,
    largest: int,
    regrouping: Regrouping,
    distinct_answers: bool,
    up_to: int,
) -> int:
    """
    Count a type's distinct questions within the limits, or with ``distinct_answers`` their
    distinct answers, stopping at ``up_to``.
    """
    match question_type:
        case BlocksQuestionType.WRITE_NUMBER:
            # each number is its own answer
            return min(max(_largest_shown(largest) - smallest + 1, 0), up_to)
        case BlocksQuestionType.ADD | BlocksQuestionType.SUBTRACT:
            operation = _OPERATIONS[question_type]
            questions = _every_question(operation, smallest, largest, regrouping)
            return _count(questions, up_to, distinct_answers)
        case _:
            assert_never(question_type)


def _can_share(count: int, available: Sequence[int], distinct_answers: bool) -> bool:
    """
    Return whether ``count`` questions can be shared among types with ``available`` questions,
    or answers, each, smallest first, as ``count_possible_blocks_questions`` describes.
    """
    share, extra = divmod(count, len(available))
    if not distinct_answers:
        return available[0] >= share + (1 if extra else 0)
    return all(
        found >= rank * share + min(rank, extra) for rank, found in enumerate(available, start=1)
    )


def _count(questions: Iterator[BasicOperationQuestionData], up_to: int, answers: bool) -> int:
    """Count ``questions``, or with ``answers`` their distinct answers, stopping at ``up_to``."""
    if not answers:
        return sum(1 for _ in islice(questions, up_to))
    found: set[int] = set()
    for data in questions:
        found.add(data.answer)
        if len(found) >= up_to:
            break
    return len(found)


def _every_question(
    operation: Literal[Operation.ADD, Operation.SUBTRACT],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
) -> Iterator[BasicOperationQuestionData]:
    """
    Yield every addition or subtraction within the limits of ``generate_blocks_questions``, by
    first operand and then second, smallest first.

    Successive questions share their first operand, so their answers differ, and a count of
    distinct answers stops early.
    """
    top = _largest_shown(largest)
    for first in range(smallest, top + 1):
        match operation:
            case Operation.ADD:
                seconds = range(smallest, min(top, largest - first) + 1)
            case Operation.SUBTRACT:
                seconds = range(smallest, first - smallest + 1)  # the difference is >= smallest
            case _:
                assert_never(operation)
        for second in seconds:
            if fits_regrouping(regrouping, operation, first, second):
                yield _question_data(operation, first, second)


def _draw(
    question_type: BlocksQuestionType, smallest: int, largest: int, regrouping: Regrouping
) -> BlocksQuestionData:
    """Draw a question of ``question_type`` at random, within the limits."""
    match question_type:
        case BlocksQuestionType.WRITE_NUMBER:
            number = random.randint(smallest, _largest_shown(largest))
            return PlaceValueQuestionData(number, PlaceValueForm.BLOCKS, PlaceValueForm.STANDARD)
        case BlocksQuestionType.ADD | BlocksQuestionType.SUBTRACT:
            return _draw_operation(_OPERATIONS[question_type], smallest, largest, regrouping)
        case _:
            assert_never(question_type)


def _draw_operation(
    operation: Literal[Operation.ADD, Operation.SUBTRACT],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
) -> BasicOperationQuestionData:
    """
    Draw an addition or subtraction at random within the limits, and fitting ``regrouping``.

    Each operand is drawn from the range the limits leave it, and the pair is redrawn until the
    sum is at most ``largest``, or the difference at least ``smallest``. About half of all pairs
    meet that, and regrouping keeps a share of those. The caller checks first that a question
    exists, as ``count_possible_blocks_questions`` does.
    """
    top = _largest_shown(largest)
    while True:
        match operation:
            case Operation.ADD:
                # the other operand is at least smallest, and the sum at most largest
                high = min(top, largest - smallest)
                first, second = random.randint(smallest, high), random.randint(smallest, high)
                fits = first + second <= largest
            case Operation.SUBTRACT:
                # the second operand and the difference are each at least smallest
                first = random.randint(2 * smallest, top)
                second = random.randint(smallest, top - smallest)
                fits = first - second >= smallest
            case _:
                assert_never(operation)
        if fits and fits_regrouping(regrouping, operation, first, second):
            return _question_data(operation, first, second)


def _question_data(
    operation: Literal[Operation.ADD, Operation.SUBTRACT], first: int, second: int
) -> BasicOperationQuestionData:
    answer = first + second if operation is Operation.ADD else first - second
    return BasicOperationQuestionData(operation, (first, second), answer)
