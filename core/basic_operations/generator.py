"""
Random generation of arithmetic questions, missing-number equations, and word problems with one
step or two.
"""

import random
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from dataclasses import replace
from functools import partial
from itertools import accumulate, islice
from typing import Literal, assert_never

from core.base_ten_blocks import LARGEST_BLOCKS_OPERAND
from core.basic_operations.data import (
    BasicOperationMultipleChoiceQuestion,
    BasicOperationQuestionData,
    MissingNumberFreeResponseQuestion,
    MissingNumberQuestionData,
    Operation,
    TwoStepQuestionData,
    TwoStepShape,
    Unknown,
)
from core.basic_operations.multiplication_models import (
    MultiplicationModelsQuestion,
    multiplication_model_choices,
)
from core.basic_operations.representation import (
    COMPARISON_REPRESENTATIONS,
    REPRESENTATION_OPERATIONS,
    STRIP_TWO_STEP_SHAPES,
    EquationChoiceQuestion,
    NumberLineChoiceQuestion,
    Representation,
    Response,
    StripChoiceQuestion,
    TwoStepEquationChoiceQuestion,
    TwoStepStripChoiceQuestion,
    WordProblemKind,
    WordProblemQuestion,
    equation_choices,
    has_fair_equation_choices,
    number_line_choices,
    stem,
    strip_choices,
    two_step_equation_choices,
    two_step_strip_choices,
)
from core.basic_operations.word_problems import (
    TWO_STEP_TEMPLATES,
    two_step_texts,
    unknown_letter,
    word_problem_texts,
)
from core.question import FreeResponse, Question, multiple_choice
from core.wrong_answers import WRONG_ANSWER_COUNT, random_wrong_answers

DEFAULT_LARGEST_OPERAND = 10  # the default for ``high``, the largest operand or dividend
DEFAULT_LARGEST_DIVIDEND = 100  # a division sheet's default ``high``
DEFAULT_LARGEST_DIVISOR = 10  # a division sheet's default ``largest_divisor``
MAXIMUM_OPERAND = 999  # the most a sheet allows for ``high`` and ``largest_divisor``

# The smallest operand of an addition or subtraction word problem. The bank's templates make
# their words agree with 1: "1 sticker", "There was 1".
SMALLEST_WORD_PROBLEM_NUMBER = 1
# The default and the most for a word problem's largest number
LARGEST_WORD_PROBLEM_NUMBER = 999
# The number of equal groups in a multiplication or division word problem: the smallest, and the
# default for the largest
WORD_PROBLEM_GROUPS = (2, 6)
# The most a sheet allows for its largest number of groups: as many as a word problem's strip
# diagram has room for, with a 3-digit number in each, and with no strip to draw, two digits
WORD_PROBLEM_STRIP_LARGEST_GROUPS = 12
WORD_PROBLEM_LARGEST_GROUPS = 99
# The number in each of those groups: the smallest, and the default for the largest
WORD_PROBLEM_GROUP_SIZES = (2, 20)
LARGEST_GROUP_SIZE = 999  # the most a sheet allows for its largest group size
STRIP_CHOICE_LARGEST_NUMBER = 100  # a strip-choice sheet's default largest number
# The most equal groups on a strip-choice sheet: as many as a choice's strip has room for, with a
# 2-digit number in each
STRIP_CHOICE_LARGEST_GROUPS = 12
# 2 + 2 and 2 groups of 2 draw the same strip, so a strip-choice sheet leaves them out
STRIP_CHOICE_EXCLUDED_OPERANDS = frozenset({(2, 2)})
# A multiplication-models sheet's smallest factor, and its default and most for the largest
# factor. Its largest product is TEKS 3.4(K)'s "within 100" by default, and at most the largest
# factor squared, as no fact has a larger one.
MULTIPLICATION_MODELS_SMALLEST_FACTOR = 2
MULTIPLICATION_MODELS_LARGEST_FACTOR = 12
MULTIPLICATION_MODELS_DEFAULT_LARGEST_PRODUCT = 100
MULTIPLICATION_MODELS_LARGEST_PRODUCT = MULTIPLICATION_MODELS_LARGEST_FACTOR**2
# 2 groups of 2 has one wrong model of each kind, 3 groups of 2, so a multiplication-models sheet
# leaves it out
MULTIPLICATION_MODELS_EXCLUDED_OPERANDS = frozenset({(2, 2)})


def generate_basic_operation_question(
    operation: Operation,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    wrong_answer_count: int = WRONG_ANSWER_COUNT,
) -> BasicOperationMultipleChoiceQuestion:
    """
    Generate a random question with whole-number operands from ``low`` to ``high``.

    Subtraction puts the larger operand first, so the answer is never negative. For division,
    the operands are the dividend, at most ``high``, and the divisor, from ``max(low, 1)`` to
    ``largest_divisor`` (``high`` when ``None``); the quotient is at least ``low``.

    Wrong answers are drawn at random from 0 to the largest answer the operands allow, or to
    ``wrong_answer_count`` if that is larger, so there are always enough to choose from.
    """
    if operation is Operation.DIVIDE:
        divisor, quotient = _division_fact(low, high, largest_divisor, smallest_quotient=low)
        data = BasicOperationQuestionData(operation, (divisor * quotient, divisor), quotient)
        wrong_answers = random_wrong_answers(
            quotient, count=wrong_answer_count, high=max(high, wrong_answer_count)
        )
        return Question(data, multiple_choice((quotient,), wrong_answers))

    first = random.randint(low, high)
    second = random.randint(low, high)
    match operation:
        case Operation.ADD:
            answer = first + second
            largest_answer = 2 * high
        case Operation.SUBTRACT:
            first, second = max(first, second), min(first, second)
            answer = first - second
            largest_answer = high
        case Operation.MULTIPLY:
            answer = first * second
            largest_answer = high * high
        case _:
            assert_never(operation)

    data = BasicOperationQuestionData(operation, (first, second), answer)
    wrong_answers = random_wrong_answers(
        answer, count=wrong_answer_count, high=max(largest_answer, wrong_answer_count)
    )
    return Question(data, multiple_choice((answer,), wrong_answers))


def count_possible_answers(
    operation: Operation, *, low: int = 0, high: int = DEFAULT_LARGEST_OPERAND, up_to: int
) -> int:
    """
    Count the distinct answers available with operands from ``low`` to ``high``.

    The count is capped at ``up_to``; a result of ``up_to`` means at least that many.
    """
    match operation:
        case Operation.ADD:
            return min(2 * (high - low) + 1, up_to)  # every sum from 2 * low to 2 * high
        case Operation.SUBTRACT:
            return min(high - low + 1, up_to)  # every difference from 0 to high - low
        case Operation.MULTIPLY:
            # The distinct products have no closed-form count, so collect them until there are
            # enough. Starting from the largest first operand finds new products fastest, since
            # small operands repeat (0 times anything is 0).
            products: set[int] = set()
            for first in range(high, low - 1, -1):
                for second in range(first, high + 1):
                    products.add(first * second)
                    if len(products) >= up_to:
                        return up_to
            return len(products)
        case Operation.DIVIDE:
            # every quotient from low to the largest dividend over the smallest divisor
            return min(high // max(low, 1) - low + 1, up_to)
        case _:
            assert_never(operation)


def count_possible_questions(
    operation: Operation,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    up_to: int,
) -> int:
    """
    Count the distinct questions available when answers may repeat.

    This is the limit for ``generate_basic_operation_questions`` without ``distinct_answers``.
    For addition, subtraction and multiplication it is the number of unordered operand pairs
    from ``low`` to ``high``, since a reversed pair counts as a repeat. For division it is the
    number of division facts ``generate_basic_operation_question`` can draw, as no two facts
    share their operands in either order. The count is capped at ``up_to``; a result of
    ``up_to`` means at least that many.
    """
    match operation:
        case Operation.ADD | Operation.SUBTRACT | Operation.MULTIPLY:
            values = high - low + 1
            possible = values * (values + 1) // 2
        case Operation.DIVIDE:
            facts = _division_facts(low, high, largest_divisor, smallest_quotient=low)
            possible = len(list(facts))
        case _:
            assert_never(operation)
    return min(possible, up_to)


def count_possible_sheet_questions(
    operations: Sequence[Operation],
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_dividend: int | None = None,
    largest_divisor: int | None = None,
    distinct_answers: bool = False,
    up_to: int,
) -> int:
    """
    Count the questions ``generate_basic_operation_questions`` can produce for ``operations``.

    Without ``distinct_answers``, each question's operation is drawn at random, so any one
    operation may be drawn for every question. The count is therefore the smallest number of
    distinct questions that any one operation allows by itself, as in
    ``count_possible_questions``.

    With ``distinct_answers``, the questions are dealt out evenly among the operations, as in
    ``_shares``, and generated from the operation with the fewest possible answers, as in
    ``count_possible_answers``, to the one with the most. An operation's questions always find
    a free answer if it has at least as many answers as the questions dealt to it and to the
    operations before it, since those questions take at most one fewer. The count is the most
    questions for which that holds for every operation.

    The count is capped at ``up_to``.
    """
    if distinct_answers:
        ranked = _rank_by_answers(
            operations, low=low, high=high, largest_dividend=largest_dividend, up_to=up_to
        )
        possible = 0
        while possible < up_to and _can_deal(possible + 1, ranked):
            possible += 1
        return possible
    return min(
        count_possible_questions(
            operation,
            low=low,
            high=_largest_operand(operation, high, largest_dividend),
            largest_divisor=largest_divisor,
            up_to=up_to,
        )
        for operation in operations
    )


def generate_basic_operation_questions(
    count: int,
    operations: Sequence[Operation],
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_dividend: int | None = None,
    largest_divisor: int | None = None,
    wrong_answer_count: int = WRONG_ANSWER_COUNT,
    distinct_answers: bool = False,
) -> list[BasicOperationMultipleChoiceQuestion]:
    """
    Generate ``count`` questions, each with an operation from ``operations``.

    Each question's operation is drawn at random. No two questions of the same operation have
    the same operand pair, in either order. With ``distinct_answers``, no two questions share an
    answer either, whatever their operations, so 3 + 4 excludes 2 + 5 and 10 - 3. The
    operations are then dealt out as evenly as possible instead of drawn, with any extra
    questions going to the operations with the most possible answers, and the questions are
    returned in random order. Operands are from ``low`` to ``high``, except that a
    division's dividend is at most ``largest_dividend`` (``high`` when ``None``) and its divisor
    at most ``largest_divisor``, as in ``generate_basic_operation_question``.

    Raises ``ValueError`` if the settings allow fewer than ``count`` such questions, as counted
    by ``count_possible_sheet_questions``.
    """
    possible = count_possible_sheet_questions(
        operations,
        low=low,
        high=high,
        largest_dividend=largest_dividend,
        largest_divisor=largest_divisor,
        distinct_answers=distinct_answers,
        up_to=count,
    )
    if count > possible:
        kind = "questions with different answers" if distinct_answers else "different questions"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    if distinct_answers:
        # Generated fewest possible answers first, as count_possible_sheet_questions requires.
        # Shuffling first breaks ties at random, so operations with equal counts share the
        # extra questions.
        ranked = _rank_by_answers(
            random.sample(operations, k=len(operations)),
            low=low,
            high=high,
            largest_dividend=largest_dividend,
            up_to=count,
        )
        shares = _shares(count, len(ranked))
        question_operations = [
            operation
            for (operation, _), share in zip(ranked, shares, strict=True)
            for _ in range(share)
        ]
    else:
        question_operations = random.choices(operations, k=count)

    questions: list[BasicOperationMultipleChoiceQuestion] = []
    seen_pairs: set[tuple[Operation, tuple[int, ...]]] = set()
    seen_answers: set[int] = set()
    for operation in question_operations:
        while True:
            question = generate_basic_operation_question(
                operation,
                low=low,
                high=_largest_operand(operation, high, largest_dividend),
                largest_divisor=largest_divisor,
                wrong_answer_count=wrong_answer_count,
            )
            pair = (operation, tuple(sorted(question.data.operands)))
            answer = question.data.answer
            if pair not in seen_pairs and not (distinct_answers and answer in seen_answers):
                break
        seen_pairs.add(pair)
        seen_answers.add(answer)
        questions.append(question)
    if distinct_answers and len(operations) > 1:
        # Dealt questions are grouped by operation. One operation's are already in random order.
        random.shuffle(questions)
    return questions


def _largest_operand(operation: Operation, high: int, largest_dividend: int | None) -> int:
    """Return ``largest_dividend`` for division, if given, and otherwise ``high``."""
    if operation is Operation.DIVIDE and largest_dividend is not None:
        return largest_dividend
    return high


def _rank_by_answers(
    operations: Sequence[Operation],
    *,
    low: int,
    high: int,
    largest_dividend: int | None,
    up_to: int,
) -> list[tuple[Operation, int]]:
    """
    Pair each operation with its count of possible answers, fewest first.

    The counts are as in ``count_possible_answers``, capped at ``up_to``. The sort is stable,
    so operations with equal counts keep their order.
    """
    counts = [
        (
            operation,
            count_possible_answers(
                operation,
                low=low,
                high=_largest_operand(operation, high, largest_dividend),
                up_to=up_to,
            ),
        )
        for operation in operations
    ]
    return sorted(counts, key=lambda pair: pair[1])


def _shares(count: int, operations: int) -> list[int]:
    """
    Split ``count`` questions among ``operations`` as evenly as possible.

    When ``count`` does not divide evenly, the extra questions go to the last operations: in the
    order of ``_rank_by_answers``, those with the most possible answers.
    """
    share, extra = divmod(count, operations)
    return [share + 1 if index >= operations - extra else share for index in range(operations)]


def _can_deal(count: int, ranked: Sequence[tuple[Operation, int]]) -> bool:
    """
    Return whether ``count`` questions with distinct answers can be dealt to ``ranked``.

    ``ranked`` is as returned by ``_rank_by_answers``. Each operation needs at least as many
    possible answers as the questions dealt to it and to the operations before it.
    """
    shares = _shares(count, len(ranked))
    return all(
        dealt <= answers for dealt, (_, answers) in zip(accumulate(shares), ranked, strict=True)
    )


def generate_missing_number_question(
    operation: Operation,
    unknown: Unknown,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
) -> MissingNumberFreeResponseQuestion:
    """
    Generate an equation with its ``unknown`` operand left blank, to be filled in.

    A fill-in question has no wrong answers. Only division is implemented; other operations
    raise ``NotImplementedError``. The dividend is at most ``high``, the divisor is from
    ``max(low, 1)`` to ``largest_divisor`` (``high`` when ``None``), and the quotient is at
    least ``max(low, 1)``, since 0 ÷ □ = 0 holds for every divisor.
    """
    match operation:
        case Operation.DIVIDE:
            divisor, quotient = _division_fact(
                low, high, largest_divisor, smallest_quotient=max(low, 1)
            )
            dividend = divisor * quotient
            match unknown:
                case Unknown.FIRST:
                    known, answer = divisor, dividend
                case Unknown.SECOND:
                    known, answer = dividend, divisor
                case _:
                    assert_never(unknown)
            data = MissingNumberQuestionData(operation, unknown, known, quotient, answer)
        case Operation.ADD | Operation.SUBTRACT | Operation.MULTIPLY:
            raise NotImplementedError("Missing numbers are built for division only.")
        case _:
            assert_never(operation)
    return Question(data, FreeResponse())


def count_possible_missing_number_questions(
    operation: Operation,
    unknown: Unknown | None,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    distinct_answers: bool = False,
    up_to: int,
) -> int:
    """
    Count the questions ``generate_missing_number_questions`` can produce with these settings.

    Without ``distinct_answers``, this is the number of fact families. With it, it is the number
    of distinct answers: the divisors when the divisor is missing, or the distinct dividends
    when the dividend is. When ``unknown`` is ``None`` (mixed), the missing-divisor questions
    are generated first, and each can exclude two dividends, its answer and its own dividend,
    so it counts twice against the dividends. The count is capped at ``up_to``.
    """
    if operation is not Operation.DIVIDE:
        raise NotImplementedError("Missing numbers are built for division only.")
    facts = list(_division_facts(low, high, largest_divisor, smallest_quotient=max(low, 1)))
    if not distinct_answers:
        families = {(min(divisor, quotient), max(divisor, quotient)) for divisor, quotient in facts}
        return min(len(families), up_to)
    divisors = len({divisor for divisor, _ in facts})
    if unknown is Unknown.SECOND:
        return min(divisors, up_to)
    dividends = len({divisor * quotient for divisor, quotient in facts})
    if unknown is Unknown.FIRST:
        return min(dividends, up_to)
    # mixed: count // 2 missing divisors, each counted against the dividends twice
    count = 0
    while count < up_to:
        missing_divisors = (count + 1) // 2
        if missing_divisors > divisors or count + 1 + missing_divisors > dividends:
            break
        count += 1
    return count


def generate_missing_number_questions(
    count: int,
    operation: Operation,
    unknown: Unknown | None,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    distinct_answers: bool = False,
) -> list[MissingNumberFreeResponseQuestion]:
    """
    Generate ``count`` equations, no two from the same fact family, whichever number is missing.

    28 ÷ 4 = 7 excludes 28 ÷ 7 = 4, so □ ÷ 4 = 7 excludes 28 ÷ □ = 4. When ``unknown`` is
    ``None`` (mixed), half the questions, rounded down, omit the divisor and the rest the
    dividend. With ``distinct_answers``, no two questions share an answer either. The questions
    are returned in random order, with numbers as in ``generate_missing_number_question``.

    Raises ``ValueError`` if the settings allow fewer than ``count`` such questions.
    """
    possible = count_possible_missing_number_questions(
        operation,
        unknown,
        low=low,
        high=high,
        largest_divisor=largest_divisor,
        distinct_answers=distinct_answers,
        up_to=count,
    )
    if count > possible:
        kind = "questions with different answers" if distinct_answers else "different questions"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    if unknown is None:
        # missing divisors first, matching count_possible_missing_number_questions
        unknowns = [Unknown.SECOND] * (count // 2) + [Unknown.FIRST] * (count - count // 2)
    else:
        unknowns = [unknown] * count
    questions: list[MissingNumberFreeResponseQuestion] = []
    if distinct_answers:
        # Drawing missing divisors with distinct answers one at a time can deadlock, so they are
        # generated together first; see _distinct_missing_divisors.
        questions += _distinct_missing_divisors(
            unknowns.count(Unknown.SECOND), low, high, largest_divisor
        )
    families = {_fact_family(question.data) for question in questions}
    answers = {question.data.answer for question in questions}
    while len(questions) < count:
        question = generate_missing_number_question(
            operation, unknowns[len(questions)], low=low, high=high, largest_divisor=largest_divisor
        )
        family = _fact_family(question.data)
        answer = question.data.answer
        if family in families or (distinct_answers and answer in answers):
            continue
        families.add(family)
        answers.add(answer)
        questions.append(question)
    random.shuffle(questions)
    return questions


def count_possible_word_problems(
    operations: Sequence[Operation],
    *,
    distinct_answers: bool = False,
    up_to: int,
    largest_number: int | None = LARGEST_WORD_PROBLEM_NUMBER,
    largest_operand: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_smaller_operand: int | None = None,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    largest_whole: int | None = None,
    excluded_operands: Collection[tuple[int, int]] = (),
    keep: Callable[[BasicOperationQuestionData], bool] | None = None,
    split_evenly: bool = False,
    larger_first: bool = False,
) -> int:
    """
    Count the word problems ``generate_word_problems`` can produce for ``operations``, with its
    limits, ``excluded_operands``, ``keep`` and ``larger_first``.

    As in ``count_possible_sheet_questions``, any one operation may be drawn for every problem, so
    the count is the smallest that any one operation allows by itself: its distinct answers with
    ``distinct_answers``, and otherwise its distinct problems. Addition and subtraction count their
    answers either way, which are fewer than their problems: every sum and every difference from the
    smallest to the largest the limits allow, the largest sum being at most ``largest_number`` only
    if that is given. An excluded pair, or one ``keep`` is false of, is taken to leave its answer to
    another pair, as 2 + 2 leaves 4 to 1 + 3. Multiplication and division leave out the excluded
    pairs and those ``keep`` is false of, and stop counting at ``up_to``.


    With ``split_evenly`` and without ``distinct_answers``, each operation needs only enough for
    its share, at most one more than an even split, so the count is that smallest count for each
    operation. The count is capped at ``up_to``.
    """
    smallest = SMALLEST_WORD_PROBLEM_NUMBER
    largest = _given_limit(largest_number, largest_operand)
    smaller = largest if largest_smaller_operand is None else min(largest_smaller_operand, largest)
    counts = []
    for operation in operations:
        match operation:
            case Operation.ADD:
                if larger_first:  # from smallest + 1 + smallest, with a smaller second number
                    lowest = 2 * smallest + 1
                    highest = largest + min(smaller, largest - 1)
                else:  # from smallest + smallest
                    lowest = 2 * smallest
                    highest = largest + smaller
                if largest_number is not None:
                    highest = min(highest, largest_number)
                counts.append(max(highest - lowest + 1, 0))
            case Operation.SUBTRACT:
                counts.append(max(largest - smallest, 0))  # from 1, with 1 taken away
            case Operation.MULTIPLY | Operation.DIVIDE:
                problems = 0
                answers: set[int] = set()
                for data in _all_equal_groups(
                    operation, largest_groups, largest_size, largest_whole
                ):
                    if data.operands in excluded_operands or (keep is not None and not keep(data)):
                        continue
                    problems += 1
                    answers.add(data.answer)
                    if (len(answers) if distinct_answers else problems) >= up_to:
                        break
                counts.append(len(answers) if distinct_answers else problems)
            case _:
                assert_never(operation)
    possible = min(counts, default=up_to)
    if split_evenly and not distinct_answers:
        possible *= len(operations)
    return min(possible, up_to)


def generate_word_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    distinct_answers: bool = False,
    comparisons: bool = False,
    largest_number: int | None = LARGEST_WORD_PROBLEM_NUMBER,
    largest_operand: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_smaller_operand: int | None = None,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    largest_whole: int | None = None,
    excluded_operands: Collection[tuple[int, int]] = (),
    keep: Callable[[BasicOperationQuestionData], bool] | None = None,
    split_evenly: bool = False,
    larger_first: bool = False,
    taken: Collection[BasicOperationQuestionData] = (),
) -> list[Question[BasicOperationQuestionData, FreeResponse]]:
    """
    Generate ``count`` word problems, each with an operation drawn at random from ``operations``.
    With ``split_evenly``, the operations are dealt out as evenly as possible instead, as in
    ``_shares``, with any extra problems going to operations chosen at random, and the problems
    are shuffled.

    Addition and subtraction draw their operands at random, as in ``_sum_or_difference``: the
    operands are at most ``largest_operand``, the numbers the problem gives, or for a representation
    that can show only so much, such as base-ten blocks, which show at most 599. With
    ``largest_number``, every number in the problem, its answer included, is at most that too;
    without it, a sum is whatever its operands make. With ``largest_smaller_operand``, the smaller
    operand is at most that too. With ``larger_first``, an addition's larger operand comes first,
    and its operands differ, as a subtraction's do. Multiplication and division are equal groups, as
    in ``_equal_groups``, with at most ``largest_groups`` groups of at most ``largest_size`` each
    and, if given, a whole (the product, or the dividend) of at most ``largest_whole``. They ignore
    the other limits. The wording comes from the word-problem bank, with its comparisons too if
    ``comparisons`` is set. The problems are answered in writing, so they have no wrong answers.


    No two problems of the same operation have the same operands, and with ``distinct_answers``
    no two problems share an answer either: a problem that breaks either rule is drawn again.
    Neither does any problem have operands in ``excluded_operands``, for a representation that
    can't tell them apart, or is it one ``keep`` is false of, such as one with no fair equations
    to choose from. Nor does any repeat the operation and operands of a problem in
    ``taken``, those already on the sheet, or with ``distinct_answers`` share its answer: the
    caller checks first that enough are left, as ``generate_mixed_word_problems`` does.

    Raises ``ValueError`` if the operations allow fewer than ``count`` such problems, as counted
    by ``count_possible_word_problems``.
    """
    possible = count_possible_word_problems(
        operations,
        distinct_answers=distinct_answers,
        up_to=count,
        largest_number=largest_number,
        largest_operand=largest_operand,
        largest_smaller_operand=largest_smaller_operand,
        largest_groups=largest_groups,
        largest_size=largest_size,
        largest_whole=largest_whole,
        excluded_operands=excluded_operands,
        keep=keep,
        split_evenly=split_evenly,
        larger_first=larger_first,
    )
    if count > possible:
        kind = "problems with different answers" if distinct_answers else "different problems"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    unworded: list[BasicOperationQuestionData] = []
    seen = {(data.operation, data.operands) for data in taken}
    answers = {data.answer for data in taken}
    for operation in _deal(operations, count, split_evenly):
        match operation:
            case Operation.ADD | Operation.SUBTRACT:
                draw = partial(
                    _sum_or_difference,
                    operation,
                    largest_number,
                    largest_operand,
                    largest_smaller_operand,
                    larger_first,
                )
            case Operation.MULTIPLY | Operation.DIVIDE:
                draw = partial(
                    _equal_groups, operation, largest_groups, largest_size, largest_whole
                )
            case _:
                assert_never(operation)
        data = draw()
        while (
            data.operands in excluded_operands
            or (keep is not None and not keep(data))
            or (operation, data.operands) in seen
            or (distinct_answers and data.answer in answers)
        ):
            data = draw()
        seen.add((operation, data.operands))
        answers.add(data.answer)
        unworded.append(data)
    texts = word_problem_texts(unworded, comparisons=comparisons)
    return [
        Question(replace(data, question_text=text), FreeResponse())
        for data, text in zip(unworded, texts, strict=True)
    ]


def count_possible_strip_choice_problems(
    operations: Sequence[Operation],
    *,
    up_to: int,
    largest_number: int = STRIP_CHOICE_LARGEST_NUMBER,
    largest_groups: int = STRIP_CHOICE_LARGEST_GROUPS,
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> int:
    """
    Count the problems ``generate_strip_choice_problems`` can produce, as
    ``count_possible_word_problems`` counts them.
    """
    return count_possible_word_problems(
        operations,
        up_to=up_to,
        largest_number=largest_number,
        largest_smaller_operand=largest_groups,
        largest_groups=largest_groups,
        largest_size=largest_size,
        largest_whole=largest_number,
        excluded_operands=STRIP_CHOICE_EXCLUDED_OPERANDS,
        split_evenly=True,
    )


def generate_strip_choice_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    largest_number: int = STRIP_CHOICE_LARGEST_NUMBER,
    largest_groups: int = STRIP_CHOICE_LARGEST_GROUPS,
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> list[StripChoiceQuestion]:
    """
    Generate ``count`` word problems as ``generate_word_problems`` does, without comparisons, each
    with its strip diagram to choose from those of ``strip_choices``. The operations are split
    evenly, and ``largest_number`` caps every number, a multiplication's product and a
    division's dividend included.

    No strip has more than ``largest_groups`` equal groups. A multiplication has at most that
    many groups, and a division shares into at most that many, with at most ``largest_size`` in
    each group. An addition's or subtraction's wrong choices multiply and divide by its smaller
    number, so that is at most ``largest_groups`` too. No problem's operands are in
    ``STRIP_CHOICE_EXCLUDED_OPERANDS``.
    """
    problems = generate_word_problems(
        count,
        operations,
        largest_number=largest_number,
        largest_smaller_operand=largest_groups,
        largest_groups=largest_groups,
        largest_size=largest_size,
        largest_whole=largest_number,
        excluded_operands=STRIP_CHOICE_EXCLUDED_OPERANDS,
        split_evenly=True,
    )
    return [Question(problem.data, strip_choices(problem.data)) for problem in problems]


def count_possible_equation_choice_problems(
    operations: Sequence[Operation],
    *,
    up_to: int,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    sheet_operations: Collection[Operation] | None = None,
) -> int:
    """
    Count the problems ``generate_equation_choice_problems`` can produce, as
    ``count_possible_word_problems`` counts them, with ``sheet_operations`` as there.
    """
    return count_possible_word_problems(
        operations,
        up_to=up_to,
        largest_number=None,
        largest_operand=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
        keep=partial(has_fair_equation_choices, operations=sheet_operations or operations),
        split_evenly=True,
    )


def generate_equation_choice_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    sheet_operations: Collection[Operation] | None = None,
    taken: Collection[BasicOperationQuestionData] = (),
) -> list[EquationChoiceQuestion]:
    """
    Generate ``count`` word problems as ``generate_word_problems`` does, comparisons included,
    each with its equation to choose from those of ``equation_choices`` for a sheet of
    ``sheet_operations``, ``operations`` unless given, as when a mixed sheet draws one operation
    at a time. Only problems with a fair set of wrong equations are drawn
    (``has_fair_equation_choices``). The operations are split evenly, and the limits are those of
    any word problem: ``largest_number`` caps the numbers an addition or subtraction gives, not
    its answer, and ``largest_groups`` and ``largest_size`` a multiplication's or division's
    equal groups. No problem repeats one in ``taken``, as in ``generate_word_problems``.
    """
    signs = sheet_operations or operations
    problems = generate_word_problems(
        count,
        operations,
        comparisons=True,
        largest_number=None,
        largest_operand=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
        keep=partial(has_fair_equation_choices, operations=signs),
        split_evenly=True,
        taken=taken,
    )
    return [Question(problem.data, equation_choices(problem.data, signs)) for problem in problems]


def count_possible_number_line_choice_problems(
    operations: Sequence[Operation],
    *,
    up_to: int,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
) -> int:
    """
    Count the problems ``generate_number_line_choice_problems`` can produce, as
    ``count_possible_word_problems`` counts them.
    """
    return count_possible_word_problems(
        operations,
        up_to=up_to,
        largest_number=None,
        largest_operand=largest_number,
        split_evenly=True,
        larger_first=True,
    )


def generate_number_line_choice_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    taken: Collection[BasicOperationQuestionData] = (),
) -> list[NumberLineChoiceQuestion]:
    """
    Generate ``count`` addition and subtraction word problems as ``generate_word_problems`` does,
    comparisons included, each with its number line to choose from those of
    ``number_line_choices``. The operations are split evenly, and ``largest_number`` caps the
    numbers a problem gives, not its answer. An addition's larger number comes first, as
    ``number_line_choices`` needs. No problem repeats one in ``taken``, as in
    ``generate_word_problems``.
    """
    problems = generate_word_problems(
        count,
        operations,
        comparisons=True,
        largest_number=None,
        largest_operand=largest_number,
        split_evenly=True,
        larger_first=True,
        taken=taken,
    )
    return [Question(problem.data, number_line_choices(problem.data)) for problem in problems]


def count_possible_multiplication_model_problems(
    *,
    up_to: int,
    largest_factor: int = MULTIPLICATION_MODELS_LARGEST_FACTOR,
    largest_product: int = MULTIPLICATION_MODELS_DEFAULT_LARGEST_PRODUCT,
) -> int:
    """
    Count the problems ``generate_multiplication_model_problems`` can produce: its facts, each
    counted once with its turn (3 groups of 4 with 4 groups of 3). The count is capped at
    ``up_to``.
    """
    facts = _multiplication_facts(largest_factor, largest_product)
    return min(len({(min(fact), max(fact)) for fact in facts}), up_to)


def generate_multiplication_model_problems(
    count: int,
    *,
    largest_factor: int = MULTIPLICATION_MODELS_LARGEST_FACTOR,
    largest_product: int = MULTIPLICATION_MODELS_DEFAULT_LARGEST_PRODUCT,
) -> list[MultiplicationModelsQuestion]:
    """
    Generate ``count`` multiplication word problems, each with its models to choose from those of
    ``multiplication_model_choices``.

    Each problem is a number of equal groups and the size of each, drawn at random from
    ``_multiplication_facts``. No fact comes twice on a sheet, turned round or not, because 3
    groups of 4 and 4 groups of 3 share their arrays.

    Raises ``ValueError`` if the limits allow fewer than ``count`` such problems, as counted by
    ``count_possible_multiplication_model_problems``.
    """
    possible = count_possible_multiplication_model_problems(
        up_to=count, largest_factor=largest_factor, largest_product=largest_product
    )
    if count > possible:
        raise ValueError(f"Cannot make {count} different problems: only {possible} possible.")

    facts = _multiplication_facts(largest_factor, largest_product)
    unworded = []
    for _ in range(count):
        groups, size = random.choice(facts)
        facts = [fact for fact in facts if fact not in {(groups, size), (size, groups)}]
        unworded.append(_equal_groups_problem(Operation.MULTIPLY, groups, size))
    texts = word_problem_texts(unworded)
    return [
        Question(replace(data, question_text=text), multiplication_model_choices(data))
        for data, text in zip(unworded, texts, strict=True)
    ]


def _multiplication_facts(largest_factor: int, largest_product: int) -> list[tuple[int, int]]:
    """
    Return every number of groups and size of each, both from
    ``MULTIPLICATION_MODELS_SMALLEST_FACTOR`` to ``largest_factor``, with a product of at most
    ``largest_product``, except those in ``MULTIPLICATION_MODELS_EXCLUDED_OPERANDS``.
    """
    factors = range(MULTIPLICATION_MODELS_SMALLEST_FACTOR, largest_factor + 1)
    return [
        (groups, size)
        for groups in factors
        for size in factors
        if groups * size <= largest_product
        and (groups, size) not in MULTIPLICATION_MODELS_EXCLUDED_OPERANDS
    ]


def count_possible_two_step_problems(
    operations: Sequence[Operation],
    *,
    distinct_answers: bool = False,
    up_to: int,
    largest_number: int | None = LARGEST_WORD_PROBLEM_NUMBER,
    largest_given: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    split_evenly: bool = False,
    shapes: Collection[TwoStepShape] | None = None,
    keep: Callable[[TwoStepQuestionData], bool] | None = None,
) -> int:
    """
    Count the two-step word problems ``generate_two_step_problems`` can produce for
    ``operations``, with its limits, ``shapes`` and ``keep``, or return 0 if ``two_step_shapes``
    has none for them.

    As in ``count_possible_word_problems``, any one shape may be drawn for every problem, so the
    count is the smallest that any one shape allows by itself: its distinct answers with
    ``distinct_answers``, and otherwise its distinct problems. A shape the limits allow no problem
    of isn't drawn, so it doesn't count: multiplying twice needs a largest number, if given, of
    at least 24, as in 2 groups of 3 groups of 4. With ``split_evenly`` and without
    ``distinct_answers``, each shape needs only enough for its share, so the count is that
    smallest count for each shape. The count is capped at ``up_to``.
    """
    given = _given_limit(largest_number, largest_given)
    counts = [
        _count_shape_problems(
            shape,
            distinct_answers,
            up_to,
            given,
            largest_number,
            largest_groups,
            largest_size,
            keep,
        )
        for shape in two_step_shapes(operations, shapes)
    ]
    drawn = [count for count in counts if count]
    possible = min(drawn, default=0)
    if split_evenly and not distinct_answers:
        possible *= len(drawn)
    return min(possible, up_to)


def generate_two_step_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    distinct_answers: bool = False,
    largest_number: int | None = LARGEST_WORD_PROBLEM_NUMBER,
    largest_given: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    split_evenly: bool = False,
    shapes: Collection[TwoStepShape] | None = None,
    keep: Callable[[TwoStepQuestionData], bool] | None = None,
    taken: Collection[TwoStepQuestionData] = (),
) -> list[Question[TwoStepQuestionData, FreeResponse]]:
    """
    Generate ``count`` two-step word problems, each of a shape drawn at random from
    ``two_step_shapes(operations, shapes)``, or with ``split_evenly`` dealt out as evenly as
    possible, as in ``generate_word_problems``. ``shapes`` limits them to those a representation
    can show, such as ``STRIP_TWO_STEP_SHAPES``, and ``keep`` to those it's true of, such as
    those with fair equations to choose from. A shape the limits and ``keep`` allow no problem of
    isn't drawn.

    The first step's answer is carried into the second step as one of its operands. The limits
    cap the numbers the problem gives (``TwoStepQuestionData.given_numbers``): an addition's and
    a subtraction's numbers, and a division's whole, are at most ``largest_given``, and
    multiplication and division are equal groups, at most ``largest_groups`` of them, of at most
    ``largest_size`` each, so every division comes out even. Addition and subtraction operands
    start at ``SMALLEST_WORD_PROBLEM_NUMBER``, and a difference is at least 1. The number carried
    isn't given, so as a number of groups or a group size it need only be at least the smallest:
    3 shelves of 4 boxes, with 15 books in each box, makes 12 boxes with a largest number of
    groups of 6. The answer isn't given either, so only a division's, the size of each group, is
    capped, by ``largest_size``. A given number that counts groups, or the size of each group,
    keeps that limit, even in an addition or subtraction, so no story shares among 972 friends
    after 969 go home.

    With ``largest_number``, every number in a problem is at most that, the first step's answer
    and the final answer included, and a problem that takes from equal groups, such as 6 boxes of
    9 with 2 of the boxes given away, starts with at most ``largest_number`` in all. The wording
    comes from the word-problem bank. The problems are answered in writing, so
    they have no wrong answers.

    No problem repeats one of its given numbers: each draw offers only the steps that make such a
    problem. (A strip diagram's choices can't tell two equal numbers apart, and another part the
    size of the equal groups beside them would look like one more group.) No two problems are the
    same, though two may share their steps: (2 x 3) x 6 and 6 x (2 x 3) both work 2 x 3 = 6 then
    6 x 6 = 36, but tell different stories. With ``distinct_answers`` no two problems share an
    answer: a problem that breaks either rule is drawn again. Nor does any repeat a problem in
    ``taken``, those already on the sheet, or with ``distinct_answers`` share its answer: the
    caller checks first that enough are left, as ``generate_mixed_word_problems`` does. A problem
    ``keep`` is false of is rare, so it isn't left out of the draws, which would cost a check of
    every candidate; the draw moves on to the next in a shuffled order instead.

    Raises ``ValueError`` if the operations allow fewer than ``count`` such problems, as counted
    by ``count_possible_two_step_problems``.
    """
    possible = count_possible_two_step_problems(
        operations,
        distinct_answers=distinct_answers,
        up_to=count,
        largest_number=largest_number,
        largest_given=largest_given,
        largest_groups=largest_groups,
        largest_size=largest_size,
        split_evenly=split_evenly,
        shapes=shapes,
        keep=keep,
    )
    if count > possible:
        kind = "problems with different answers" if distinct_answers else "different problems"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    given = _given_limit(largest_number, largest_given)
    limits = (given, largest_number, largest_groups, largest_size)
    carried_numbers = {
        shape: list(_carried_numbers(shape, *limits))
        for shape in two_step_shapes(operations, shapes)
    }
    # a shape the limits and keep allow no problem of isn't drawn
    drawn = [
        shape
        for shape, numbers in carried_numbers.items()
        if numbers and (keep is None or _count_shape_problems(shape, False, 1, *limits, keep))
    ]
    unworded: list[TwoStepQuestionData] = []
    # unworded, as the draws are
    seen = {replace(data, question_text=None) for data in taken}
    answers = {data.answer for data in taken}
    for shape in _deal(drawn, count, split_evenly):
        draw = partial(_two_step_problem, shape, carried_numbers[shape], *limits, keep)
        data = draw()
        while data in seen or (distinct_answers and data.answer in answers):
            data = draw()
        seen.add(data)
        answers.add(data.answer)
        unworded.append(data)
    texts = two_step_texts(unworded)
    return [
        Question(replace(data, question_text=text), FreeResponse())
        for data, text in zip(unworded, texts, strict=True)
    ]


def generate_two_step_strip_choice_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    largest_number: int = STRIP_CHOICE_LARGEST_NUMBER,
    largest_groups: int = STRIP_CHOICE_LARGEST_GROUPS,
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> list[TwoStepStripChoiceQuestion]:
    """
    Generate ``count`` two-step word problems as ``generate_two_step_problems`` does, of the
    shapes one strip can show, split evenly, each with its strip diagram to choose from those of
    ``two_step_strip_choices``.
    """
    problems = generate_two_step_problems(
        count,
        operations,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
        split_evenly=True,
        shapes=STRIP_TWO_STEP_SHAPES,
    )
    return [Question(problem.data, two_step_strip_choices(problem.data)) for problem in problems]


def count_possible_two_step_equation_choice_problems(
    operations: Sequence[Operation],
    *,
    up_to: int,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> int:
    """
    Count the problems ``generate_two_step_equation_choice_problems`` can produce, as
    ``count_possible_two_step_problems`` counts them: every shape, split evenly, and only problems
    with fair equations to choose from.
    """
    return count_possible_two_step_problems(
        operations,
        up_to=up_to,
        largest_number=None,
        largest_given=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
        split_evenly=True,
        keep=partial(has_fair_equation_choices, operations=operations),
    )


def generate_two_step_equation_choice_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
    shapes: Collection[TwoStepShape] | None = None,
    taken: Collection[TwoStepQuestionData] = (),
) -> list[TwoStepEquationChoiceQuestion]:
    """
    Generate ``count`` two-step word problems as ``generate_two_step_problems`` does, of every
    shape, split evenly, each with its equation to choose from those of
    ``two_step_equation_choices``. Only problems with a fair set of wrong equations are drawn
    (``has_fair_equation_choices``). The letter for what to find is the one ``unknown_letter``
    gives for the problem's wording. ``largest_number`` caps the numbers each problem gives, not
    the first step's answer or the final answer. ``shapes`` and ``taken`` are as in
    ``generate_two_step_problems``.

    Raises ``ValueError`` if the operations allow fewer than ``count`` such problems, as counted
    by ``count_possible_two_step_equation_choice_problems``.
    """
    problems = generate_two_step_problems(
        count,
        operations,
        largest_number=None,
        largest_given=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
        split_evenly=True,
        shapes=shapes,
        keep=partial(has_fair_equation_choices, operations=operations),
        taken=taken,
    )
    # every problem is worded, so its stem is its wording
    return [
        Question(
            problem.data,
            two_step_equation_choices(problem.data, unknown_letter(stem(problem.data)), operations),
        )
        for problem in problems
    ]


def count_possible_mixed_word_problems(
    operations: Sequence[Operation],
    kinds: Sequence[WordProblemKind],
    *,
    up_to: int,
    two_steps: bool = False,
    distinct_answers: bool = False,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> int:
    """
    Count the word problems ``generate_mixed_word_problems`` can produce for ``operations`` and
    ``kinds``, with its limits, or return 0 if a ticked operation has no kind to show it.

    As in ``count_possible_word_problems``, any one problem may be drawn as any one kind that can
    show it, so the count is the smallest that any one kind allows by itself for any one operation
    it can show, or with ``two_steps`` any one shape of problem it draws, each counted as on a
    sheet of that kind alone. A kind with no problem to draw, such as a two-step one whose limits
    allow none, isn't drawn, but if every kind answered one way is like that, the count is 0. The
    count is capped at ``up_to``.

    Raises ``ValueError`` with ``distinct_answers`` and a kind answered by multiple choice, whose
    answers are letters.
    """
    _no_choices_with_distinct_answers(kinds, distinct_answers)
    limits = (largest_number, largest_groups, largest_size)
    topics = {kind: _kind_topics(kind, operations, two_steps, *limits) for kind in kinds}
    # a way of answering whose kinds can make no problem leaves its share with none to draw
    for response in {response for _, response in kinds}:
        if not any(topics[kind] for kind in kinds if kind[1] is response):
            return 0
    if not two_steps and not {topic for each in topics.values() for topic in each}.issuperset(
        operations
    ):
        return 0
    counts = [
        _count_kind_problems(kind, topic, operations, up_to, distinct_answers, *limits)
        for kind in kinds
        for topic in topics[kind]
    ]
    return min(min(counts, default=0), up_to)


def generate_mixed_word_problems(
    count: int,
    operations: Sequence[Operation],
    kinds: Sequence[WordProblemKind],
    *,
    two_steps: bool = False,
    distinct_answers: bool = False,
    largest_number: int = LARGEST_WORD_PROBLEM_NUMBER,
    largest_groups: int = WORD_PROBLEM_GROUPS[1],
    largest_size: int = WORD_PROBLEM_GROUP_SIZES[1],
) -> list[tuple[Representation, WordProblemQuestion]]:
    """
    Generate ``count`` word problems of a mix of ``kinds``, as ``word_problem_kinds`` returns
    them, each with the representation it's drawn with, in a shuffled order.

    The ways of answering are dealt out evenly. Each problem's operation, or with ``two_steps``
    its shape, is then drawn as on a sheet of one kind: at random from those that some kind
    answered that way can show, or for multiple choice dealt out evenly. Each problem goes to a
    kind answered that way that can show it, to whichever representation has the fewest problems
    so far, and those that the fewest kinds can show go first. Each kind's problems are made as on
    a sheet of that kind alone, with its own limits within the sheet's: ``largest_number`` caps
    the numbers each problem gives, and base-ten blocks show at most ``LARGEST_BLOCKS_OPERAND``.
    No problem repeats one already made, and with ``distinct_answers`` no two share an answer.

    Raises ``ValueError`` if the kinds allow fewer than ``count`` such problems, as counted by
    ``count_possible_mixed_word_problems``, which also guarantees that every kind has enough left
    after the others.
    """
    limits = (largest_number, largest_groups, largest_size)
    possible = count_possible_mixed_word_problems(
        operations,
        kinds,
        up_to=count,
        two_steps=two_steps,
        distinct_answers=distinct_answers,
        largest_number=largest_number,
        largest_groups=largest_groups,
        largest_size=largest_size,
    )
    if count > possible:
        wanted = "problems with different answers" if distinct_answers else "different problems"
        raise ValueError(f"Cannot make {count} {wanted}: only {possible} possible.")

    topics = {kind: _kind_topics(kind, operations, two_steps, *limits) for kind in kinds}
    responses = [response for response in Response if any(each is response for _, each in kinds)]
    dealt = _deal(responses, count, split_evenly=True)
    problems: list[tuple[Response, Operation | TwoStepShape]] = []
    for response in responses:
        answered = [kind for kind in kinds if kind[1] is response]
        shown = [
            topic
            for topic in _topics(operations, two_steps)
            if any(topic in topics[kind] for kind in answered)
        ]
        multiple_choice = response is Response.MULTIPLE_CHOICE
        problems += [
            (response, topic) for topic in _deal(shown, dealt.count(response), multiple_choice)
        ]

    # each problem's kind, those the fewest kinds can show first
    def candidates(problem: tuple[Response, Operation | TwoStepShape]) -> list[WordProblemKind]:
        response, topic = problem
        return [kind for kind in kinds if kind[1] is response and topic in topics[kind]]

    tallies = dict.fromkeys((representation for representation, _ in kinds), 0)
    groups: dict[tuple[WordProblemKind, Operation | TwoStepShape], int] = {}
    for problem in sorted(problems, key=lambda each: len(candidates(each))):
        able = candidates(problem)
        fewest = min(tallies[representation] for representation, _ in able)
        kind = random.choice([each for each in able if tallies[each[0]] == fewest])
        tallies[kind[0]] += 1
        groups[kind, problem[1]] = groups.get((kind, problem[1]), 0) + 1

    made: list[tuple[WordProblemKind, BasicOperationQuestionData | TwoStepQuestionData]] = []
    for (kind, topic), share in groups.items():
        taken = [data for _, data in made]
        questions = _kind_problems(kind, topic, share, operations, taken, distinct_answers, *limits)
        made += [(kind, question.data) for question in questions]
    random.shuffle(made)
    return _worded_together(made, operations)


def _worded_together(
    made: Sequence[tuple[WordProblemKind, BasicOperationQuestionData | TwoStepQuestionData]],
    operations: Sequence[Operation],
) -> list[tuple[Representation, WordProblemQuestion]]:
    """
    Word a mixed sheet's problems again, all together, so that no story repeats until all of its
    operation's, or two-step shape's, have been used, as on a sheet of one kind (each kind's
    problems were worded apart), and return each with its representation and its response, made
    as its kind makes it. A problem has "how many more than" stories where its representation
    does (``COMPARISON_REPRESENTATIONS``), and two-step equations to choose from have the letter
    the new wording gives.
    """
    one_step = [
        (index, data)
        for index, (_, data) in enumerate(made)
        if isinstance(data, BasicOperationQuestionData)
    ]
    two_step = [
        (index, data)
        for index, (_, data) in enumerate(made)
        if isinstance(data, TwoStepQuestionData)
    ]
    compared = [made[index][0][0] in COMPARISON_REPRESENTATIONS for index, _ in one_step]
    one_step_texts = word_problem_texts([data for _, data in one_step], comparisons=compared)
    texts = dict(zip([index for index, _ in one_step], one_step_texts, strict=True))
    two_step_worded = two_step_texts([data for _, data in two_step])
    texts.update(zip([index for index, _ in two_step], two_step_worded, strict=True))
    worded: list[tuple[Representation, WordProblemQuestion]] = []
    for index, ((representation, response), unworded) in enumerate(made):
        data = replace(unworded, question_text=texts[index])
        choices = response is Response.MULTIPLE_CHOICE
        question: WordProblemQuestion
        if isinstance(data, TwoStepQuestionData) and choices:
            letter = unknown_letter(texts[index])
            question = Question(data, two_step_equation_choices(data, letter, operations))
        elif isinstance(data, TwoStepQuestionData):
            question = Question(data, FreeResponse())
        elif choices and representation is Representation.NUMBER_LINE:
            question = Question(data, number_line_choices(data))
        elif choices:
            question = Question(data, equation_choices(data, operations))
        else:
            question = Question(data, FreeResponse())
        worded.append((representation, question))
    return worded


def _no_choices_with_distinct_answers(
    kinds: Sequence[WordProblemKind], distinct_answers: bool
) -> None:
    """Raise ``ValueError`` with ``distinct_answers`` and a kind answered by multiple choice."""
    if distinct_answers and any(response is Response.MULTIPLE_CHOICE for _, response in kinds):
        raise ValueError("Multiple choice answers are letters, so they can't be distinct answers.")


def _topics(operations: Sequence[Operation], two_steps: bool) -> list[Operation | TwoStepShape]:
    """Return ``operations``, or with ``two_steps`` the shapes of problem in the bank for them."""
    if two_steps:
        return list(two_step_shapes(operations))
    return list(operations)


def _kind_topics(
    kind: WordProblemKind,
    operations: Sequence[Operation],
    two_steps: bool,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
) -> list[Operation | TwoStepShape]:
    """
    Return what a word problem of ``kind`` can be: each of ``operations`` its representation shows,
    or with ``two_steps`` each shape of problem in the bank for them that it shows and that the
    limits allow a problem of, as ``generate_two_step_problems`` draws them.
    """
    representation, response = kind
    if not two_steps:
        return [
            operation
            for operation in operations
            if operation in REPRESENTATION_OPERATIONS[representation]
        ]
    shapes = STRIP_TWO_STEP_SHAPES if representation is Representation.STRIP else None
    keep = _two_step_keep(response, operations)
    return [
        shape
        for shape in two_step_shapes(operations, shapes)
        if _count_shape_problems(
            shape, False, 1, largest_number, None, largest_groups, largest_size, keep
        )
    ]


def _two_step_keep(
    response: Response, operations: Sequence[Operation]
) -> Callable[[TwoStepQuestionData], bool] | None:
    """
    Return which two-step problems a kind answered by ``response`` draws: for multiple choice,
    only those with fair equations to choose from, and otherwise any.
    """
    if response is Response.MULTIPLE_CHOICE:
        return partial(has_fair_equation_choices, operations=operations)
    return None


def _largest_drawn_operand(representation: Representation, largest_number: int) -> int:
    """Return the most an operand drawn with ``representation`` may be: base-ten blocks show 599."""
    if representation is Representation.BLOCKS:
        return min(largest_number, LARGEST_BLOCKS_OPERAND)
    return largest_number


def _count_kind_problems(
    kind: WordProblemKind,
    topic: Operation | TwoStepShape,
    operations: Sequence[Operation],
    up_to: int,
    distinct_answers: bool,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
) -> int:
    """
    Count the problems of ``kind`` and ``topic``, an operation or a two-step shape, as on a sheet
    of that kind alone, as ``generate_mixed_word_problems`` makes them, stopping at ``up_to``.
    """
    representation, response = kind
    if not isinstance(topic, Operation):
        keep = _two_step_keep(response, operations)
        return _count_shape_problems(
            topic, distinct_answers, up_to, largest_number, None, largest_groups, largest_size, keep
        )
    match kind:
        case (Representation.NUMBER_LINE, Response.MULTIPLE_CHOICE):
            return count_possible_number_line_choice_problems(
                [topic], up_to=up_to, largest_number=largest_number
            )
        case (Representation.EQUATION, Response.MULTIPLE_CHOICE):
            return count_possible_equation_choice_problems(
                [topic],
                up_to=up_to,
                largest_number=largest_number,
                largest_groups=largest_groups,
                largest_size=largest_size,
                sheet_operations=operations,
            )
        case _:
            return count_possible_word_problems(
                [topic],
                distinct_answers=distinct_answers,
                up_to=up_to,
                largest_number=None,
                largest_operand=_largest_drawn_operand(representation, largest_number),
                largest_groups=largest_groups,
                largest_size=largest_size,
            )


def _kind_problems(
    kind: WordProblemKind,
    topic: Operation | TwoStepShape,
    count: int,
    operations: Sequence[Operation],
    taken: Sequence[BasicOperationQuestionData | TwoStepQuestionData],
    distinct_answers: bool,
    largest_number: int,
    largest_groups: int,
    largest_size: int,
) -> Sequence[WordProblemQuestion]:
    """
    Generate ``count`` problems of ``kind`` and ``topic``, an operation or a two-step shape, as on
    a sheet of that kind alone, none repeating a problem in ``taken``, or with
    ``distinct_answers`` sharing its answer.
    """
    representation, response = kind
    if not isinstance(topic, Operation):
        taken_two = [data for data in taken if isinstance(data, TwoStepQuestionData)]
        if response is Response.MULTIPLE_CHOICE:
            return generate_two_step_equation_choice_problems(
                count,
                operations,
                largest_number=largest_number,
                largest_groups=largest_groups,
                largest_size=largest_size,
                shapes={topic},
                taken=taken_two,
            )
        return generate_two_step_problems(
            count,
            operations,
            distinct_answers=distinct_answers,
            largest_number=None,
            largest_given=largest_number,
            largest_groups=largest_groups,
            largest_size=largest_size,
            shapes={topic},
            taken=taken_two,
        )
    taken_one = [data for data in taken if isinstance(data, BasicOperationQuestionData)]
    match kind:
        case (Representation.NUMBER_LINE, Response.MULTIPLE_CHOICE):
            return generate_number_line_choice_problems(
                count, [topic], largest_number=largest_number, taken=taken_one
            )
        case (Representation.EQUATION, Response.MULTIPLE_CHOICE):
            return generate_equation_choice_problems(
                count,
                [topic],
                largest_number=largest_number,
                largest_groups=largest_groups,
                largest_size=largest_size,
                sheet_operations=operations,
                taken=taken_one,
            )
        case _:
            return generate_word_problems(
                count,
                [topic],
                distinct_answers=distinct_answers,
                comparisons=representation in COMPARISON_REPRESENTATIONS,
                largest_number=None,
                largest_operand=_largest_drawn_operand(representation, largest_number),
                largest_groups=largest_groups,
                largest_size=largest_size,
                taken=taken_one,
            )


def two_step_shapes(
    operations: Collection[Operation], shapes: Collection[TwoStepShape] | None = None
) -> list[TwoStepShape]:
    """
    Return the shapes of two-step problem with stories in the word-problem bank whose two
    operations are both in ``operations``, and that are among ``shapes`` if given, in the bank's
    order.
    """
    return [
        shape
        for shape in TWO_STEP_TEMPLATES
        if shape[0] in operations and shape[1] in operations and (shapes is None or shape in shapes)
    ]


def _sum_or_difference(
    operation: Literal[Operation.ADD, Operation.SUBTRACT],
    largest_number: int | None,
    largest_operand: int,
    largest_smaller_operand: int | None = None,
    larger_first: bool = False,
) -> BasicOperationQuestionData:
    """
    Draw two operands at random from ``SMALLEST_WORD_PROBLEM_NUMBER`` to ``largest_operand``, and
    to ``largest_number`` too if given, redrawing until they meet the word-problem limits: a sum
    is at most ``largest_number`` if given, and a difference is at least 1, with the larger
    operand first. With ``largest_smaller_operand``, the second operand is drawn no larger than
    that, and then an addition's operands are put in random order. With ``larger_first``, an
    addition's larger operand comes first instead, and its operands differ.

    The caller checks first that the limits allow a problem, as ``count_possible_word_problems``
    does. Then about half of all draws meet them, and even the tightest limits meet one draw in
    five, so the redraws end quickly.
    """
    largest = _given_limit(largest_number, largest_operand)
    smaller = largest if largest_smaller_operand is None else min(largest_smaller_operand, largest)
    while True:
        first = random.randint(SMALLEST_WORD_PROBLEM_NUMBER, largest)
        second = random.randint(SMALLEST_WORD_PROBLEM_NUMBER, smaller)
        match operation:
            case Operation.ADD:
                if larger_first:
                    if first == second:
                        continue
                    first, second = max(first, second), min(first, second)
                elif smaller < largest:
                    first, second = random.sample((first, second), 2)
                if largest_number is None or first + second <= largest_number:
                    return BasicOperationQuestionData(operation, (first, second), first + second)
            case Operation.SUBTRACT:
                first, second = max(first, second), min(first, second)
                if first > second:
                    return BasicOperationQuestionData(operation, (first, second), first - second)
            case _:
                assert_never(operation)


def _equal_groups(
    operation: Literal[Operation.MULTIPLY, Operation.DIVIDE],
    largest_groups: int,
    largest_size: int,
    largest_whole: int | None = None,
) -> BasicOperationQuestionData:
    """
    Draw an equal-groups problem: a number of groups from the smallest of
    ``WORD_PROBLEM_GROUPS`` to ``largest_groups``, each of a size from the smallest of
    ``WORD_PROBLEM_GROUP_SIZES`` to ``largest_size``, as ``_equal_groups_problem`` makes it. With
    ``largest_whole``, groups and size are drawn again until their whole is at most that.

    The caller checks first that a problem is possible, as ``count_possible_word_problems``
    does.
    """
    while True:
        groups = random.randint(WORD_PROBLEM_GROUPS[0], largest_groups)
        size = random.randint(WORD_PROBLEM_GROUP_SIZES[0], largest_size)
        if largest_whole is None or groups * size <= largest_whole:
            return _equal_groups_problem(operation, groups, size)


def _all_equal_groups(
    operation: Literal[Operation.MULTIPLY, Operation.DIVIDE],
    largest_groups: int,
    largest_size: int,
    largest_whole: int | None = None,
) -> Iterator[BasicOperationQuestionData]:
    """Yield every equal-groups problem ``_equal_groups`` can draw, fewest groups first."""
    for groups in _group_counts(largest_groups):
        sizes = (
            largest_size if largest_whole is None else min(largest_size, largest_whole // groups)
        )
        for size in _group_sizes(sizes):
            yield _equal_groups_problem(operation, groups, size)


def _equal_groups_problem(
    operation: Literal[Operation.MULTIPLY, Operation.DIVIDE], groups: int, size: int
) -> BasicOperationQuestionData:
    """
    Return the equal-groups problem of ``groups`` groups, each of ``size``.

    Multiplication's operands are the groups and the size, so 3 groups of 4 is (3, 4), and the
    whole is to find. Division is partitive: its operands are the whole and the groups it is
    shared into, so 12 shared into 3 groups is (12, 3), and the size of each group is to find.
    """
    match operation:
        case Operation.MULTIPLY:
            return BasicOperationQuestionData(operation, (groups, size), groups * size)
        case Operation.DIVIDE:
            return BasicOperationQuestionData(operation, (groups * size, groups), size)
        case _:
            assert_never(operation)


def _deal[Kind](kinds: Sequence[Kind], count: int, split_evenly: bool) -> list[Kind]:
    """
    Return ``count`` kinds of problem, each drawn at random from ``kinds``, or with
    ``split_evenly`` dealt out as evenly as possible, as in ``_shares``, with any extra problems
    going to kinds chosen at random, and shuffled.
    """
    if not split_evenly:
        return random.choices(kinds, k=count)
    # shuffled first, so that the extra problems go to kinds at random
    dealt = random.sample(kinds, k=len(kinds))
    problem_kinds = [
        kind
        for kind, share in zip(dealt, _shares(count, len(dealt)), strict=True)
        for _ in range(share)
    ]
    random.shuffle(problem_kinds)
    return problem_kinds


def _group_counts(largest_groups: int) -> range:
    """Return every number of equal groups, up to ``largest_groups``, in a word problem."""
    return range(WORD_PROBLEM_GROUPS[0], largest_groups + 1)


def _group_sizes(largest_size: int) -> range:
    """Return every size of equal group, up to ``largest_size``, in a word problem."""
    return range(WORD_PROBLEM_GROUP_SIZES[0], largest_size + 1)


def _given_limit(largest_number: int | None, largest_given: int) -> int:
    """
    Return the most any number a word problem gives may be: ``largest_given``, and at most
    ``largest_number`` too if given, which caps every number.
    """
    return largest_given if largest_number is None else min(largest_number, largest_given)


def _distinct_numbers(data: TwoStepQuestionData) -> bool:
    """Return whether no two of the two-step problem's given numbers are the same."""
    return len(set(data.given_numbers)) == len(data.given_numbers)


def _allowed(data: TwoStepQuestionData, largest_number: int | None) -> bool:
    """
    Return whether the two-step problem repeats none of its given numbers and, with
    ``largest_number``, if it takes from equal groups, as in 6 boxes of 9 with 2 of the boxes
    given away, starts with at most ``largest_number`` in all, as the whole of any multiplication
    is. That starting total isn't given, so without ``largest_number`` nothing caps it.
    """
    first, second = data.steps
    if (
        largest_number is not None
        and first.operation is Operation.SUBTRACT
        and second.operation is Operation.MULTIPLY
    ):
        groups, size = second.operands
        other = size if data.carried is Unknown.FIRST else groups
        if first.operands[0] * other > largest_number:
            return False
    return _distinct_numbers(data)


def _count_shape_problems(
    shape: TwoStepShape,
    distinct_answers: bool,
    up_to: int,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
    keep: Callable[[TwoStepQuestionData], bool] | None,
) -> int:
    """
    Count the two-step problems of ``shape`` that ``generate_two_step_problems`` can draw, those
    ``keep`` is true of if given, or with ``distinct_answers`` their distinct answers, stopping at
    ``up_to``. ``largest_given`` caps the numbers each problem gives, already within
    ``largest_number``, as ``_given_limit`` returns it.
    """
    first_operation, second_operation, carried = shape
    largest_first_operand = _largest_first_operand(
        shape, largest_given, largest_groups, largest_size
    )
    problems = 0
    answers: set[int] = set()
    for number in _carried_numbers(
        shape, largest_given, largest_number, largest_groups, largest_size
    ):
        for second in _second_steps(
            second_operation,
            carried,
            number,
            largest_given,
            largest_number,
            largest_groups,
            largest_size,
        ):
            if distinct_answers and second.answer in answers:
                continue
            firsts = _first_steps(
                first_operation,
                number,
                largest_given,
                largest_groups,
                largest_size,
                largest_first_operand,
            )
            joined = (_join_steps(shape, first, second) for first in firsts)
            allowed = (
                data
                for data in joined
                if _allowed(data, largest_number) and (keep is None or keep(data))
            )
            if distinct_answers:
                if next(allowed, None) is not None:
                    answers.add(second.answer)
            else:
                # no further than the cap, which spares checking ``keep`` past it
                problems += sum(1 for _ in islice(allowed, up_to - problems))
            if max(problems, len(answers)) >= up_to:
                return up_to
    return len(answers) if distinct_answers else problems


def _two_step_problem(
    shape: TwoStepShape,
    carried_numbers: Sequence[int],
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
    keep: Callable[[TwoStepQuestionData], bool] | None,
) -> TwoStepQuestionData:
    """
    Draw a two-step problem of ``shape`` that ``_allowed`` allows: the number its first step
    carries into its second, from ``carried_numbers``, then its first step, from those of
    ``_followed_first_steps``, then its second step, from those of ``_following_seconds``.

    A problem that ``keep`` is false of gives way to the first that it's true of in a shuffled
    order of the shape's problems. The caller checks first that there is one, as
    ``generate_two_step_problems`` does with ``_count_shape_problems``.
    """
    limits = (largest_given, largest_number, largest_groups, largest_size)
    number = random.choice(carried_numbers)
    first = random.choice(list(_followed_first_steps(shape, number, *limits)))
    second = random.choice(_following_seconds(shape, first, number, *limits))
    data = _join_steps(shape, first, second)
    if keep is None or keep(data):
        return data
    for candidate in _shuffled_problems(shape, carried_numbers, *limits):
        if keep(candidate):
            return candidate
    raise ValueError(f"No problem of {shape} is kept.")


def _following_seconds(
    shape: TwoStepShape,
    first: BasicOperationQuestionData,
    number: int,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> list[BasicOperationQuestionData]:
    """
    Return the second steps of a ``shape`` problem, carrying ``number``, the answer of ``first``,
    that follow ``first`` in a problem that ``_allowed`` allows.
    """
    _, second_operation, carried = shape
    return [
        second
        for second in _second_steps(
            second_operation,
            carried,
            number,
            largest_given,
            largest_number,
            largest_groups,
            largest_size,
        )
        if _allowed(_join_steps(shape, first, second), largest_number)
    ]


def _shuffled_problems(
    shape: TwoStepShape,
    carried_numbers: Sequence[int],
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> Iterator[TwoStepQuestionData]:
    """
    Yield every ``shape`` problem that ``_allowed`` allows, in a shuffled order: the numbers
    carried from ``carried_numbers`` shuffled, each one's first steps shuffled, and each first
    step's second steps shuffled.
    """
    limits = (largest_given, largest_number, largest_groups, largest_size)
    for number in random.sample(carried_numbers, len(carried_numbers)):
        firsts = list(_followed_first_steps(shape, number, *limits))
        for first in random.sample(firsts, len(firsts)):
            seconds = _following_seconds(shape, first, number, *limits)
            for second in random.sample(seconds, len(seconds)):
                yield _join_steps(shape, first, second)


def _join_steps(
    shape: TwoStepShape, first: BasicOperationQuestionData, second: BasicOperationQuestionData
) -> TwoStepQuestionData:
    """Return the two-step problem of ``shape`` whose steps are ``first`` and ``second``."""
    return TwoStepQuestionData((first, second), shape[2], second.answer)


def _carried_numbers(
    shape: TwoStepShape,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> Iterator[int]:
    """
    Yield, smallest first, every number that the first step of a ``shape`` problem can carry into
    its second step, in a problem that ``_allowed`` allows.
    """
    limits = (largest_given, largest_number, largest_groups, largest_size)
    largest = _largest_carried(shape, *limits)
    numbers: Iterable[int]
    if shape[0] is Operation.MULTIPLY:  # only products, far fewer than the numbers up to the most
        products = {
            groups * size
            for groups in _group_counts(largest_groups)
            for size in _group_sizes(min(largest_size, largest // groups))
        }
        numbers = sorted(products)
    else:
        numbers = range(SMALLEST_WORD_PROBLEM_NUMBER, largest + 1)
    for number in numbers:
        if any(_followed_first_steps(shape, number, *limits)):
            yield number


def _followed_first_steps(
    shape: TwoStepShape,
    number: int,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> Iterator[BasicOperationQuestionData]:
    """
    Yield every first step of a ``shape`` problem whose answer is ``number``, as ``_first_steps``
    does, that some second step of ``_second_steps`` can follow in a problem that ``_allowed``
    allows.
    """
    first_operation, second_operation, carried = shape
    seconds = partial(
        _second_steps,
        second_operation,
        carried,
        number,
        largest_given,
        largest_number,
        largest_groups,
        largest_size,
    )
    if next(seconds(), None) is None:  # no second step, so nothing to follow any first step
        return
    firsts = _first_steps(
        first_operation,
        number,
        largest_given,
        largest_groups,
        largest_size,
        _largest_first_operand(shape, largest_given, largest_groups, largest_size),
    )
    for first in firsts:
        if any(_allowed(_join_steps(shape, first, second), largest_number) for second in seconds()):
            yield first


def _largest_carried(
    shape: TwoStepShape,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> int:
    """
    Return the largest number a ``shape`` problem's first step can carry into its second: the
    most its given numbers can make, and at most ``largest_number`` if given. The number carried
    isn't given, so the limits on given numbers don't cap it: 3 shelves of 4 boxes, with 15 books
    in each box, makes 12 boxes, though the largest number of groups is 6.
    """
    largest_operand = _largest_first_operand(shape, largest_given, largest_groups, largest_size)
    first_operation = shape[0]
    match first_operation:
        case Operation.ADD:
            most = 2 * largest_operand
        case Operation.SUBTRACT:
            most = largest_operand - SMALLEST_WORD_PROBLEM_NUMBER
        case Operation.MULTIPLY:
            most = largest_groups * largest_size
        case Operation.DIVIDE:  # the whole, which is given, shared into the fewest groups
            most = largest_given // WORD_PROBLEM_GROUPS[0]
        case _:
            assert_never(first_operation)
    return most if largest_number is None else min(most, largest_number)


def _largest_first_operand(
    shape: TwoStepShape, largest_given: int, largest_groups: int, largest_size: int
) -> int:
    """
    Return the largest operand a ``shape`` problem's first step may have if it's an addition or
    subtraction: the largest of the numbers it adds, or the number it takes from. Those numbers
    count the same things as its answer, so they keep the limit for those things:
    ``largest_groups`` if the answer is the number of groups, as in 12 friends with 3 of them
    gone home, or 3 bags and 4 more bags with 5 apples in each, ``largest_size`` if it's the size
    of each group, and ``largest_given`` otherwise, but never more than ``largest_given``. The
    answer itself isn't given, so it may pass that limit: 3 bags and 4 more make 7 bags, though
    the largest number of groups is 6.
    """
    _, second_operation, carried = shape
    match second_operation, carried:
        case (Operation.MULTIPLY, Unknown.FIRST) | (Operation.DIVIDE, Unknown.SECOND):
            return min(largest_groups, largest_given)
        case (Operation.MULTIPLY, Unknown.SECOND):
            return min(largest_size, largest_given)
        case _:
            return largest_given


def _first_steps(
    operation: Operation,
    answer: int,
    largest_given: int,
    largest_groups: int,
    largest_size: int,
    largest_operand: int,
) -> Iterator[BasicOperationQuestionData]:
    """
    Yield every first step of a two-step problem whose answer is ``answer``. Its operands are
    numbers the problem gives.

    An addition's operands start at ``SMALLEST_WORD_PROBLEM_NUMBER`` and are at most
    ``largest_operand``, as is the number a subtraction takes from. Multiplication and division
    are equal groups, as ``_equal_groups_problem`` makes them, of up to ``largest_groups``
    groups, with a multiplication's groups of up to ``largest_size`` each, and a division's
    whole at most ``largest_given``. A division's answer, the size of each group, is carried into
    the second step, not given, so no limit but the smallest group size applies to it.
    """
    smallest = SMALLEST_WORD_PROBLEM_NUMBER
    match operation:
        case Operation.ADD:
            lowest = max(smallest, answer - largest_operand)
            for first in range(lowest, min(largest_operand, answer - smallest) + 1):
                yield BasicOperationQuestionData(operation, (first, answer - first), answer)
        case Operation.SUBTRACT:
            for second in range(smallest, largest_operand - answer + 1):
                yield BasicOperationQuestionData(operation, (answer + second, second), answer)
        case Operation.MULTIPLY:  # only as many groups as leave each a size within the limits
            fewest = max(WORD_PROBLEM_GROUPS[0], -(-answer // largest_size))
            most = min(largest_groups, answer // WORD_PROBLEM_GROUP_SIZES[0])
            for groups in range(fewest, most + 1):
                size, remainder = divmod(answer, groups)
                if not remainder:
                    yield _equal_groups_problem(operation, groups, size)
        case Operation.DIVIDE:
            if answer >= WORD_PROBLEM_GROUP_SIZES[0]:
                for groups in _group_counts(min(largest_groups, largest_given // answer)):
                    yield _equal_groups_problem(operation, groups, answer)
        case _:
            assert_never(operation)


def _second_steps(
    operation: Operation,
    carried: Unknown,
    number: int,
    largest_given: int,
    largest_number: int | None,
    largest_groups: int,
    largest_size: int,
) -> Iterator[BasicOperationQuestionData]:
    """
    Yield every second step of a two-step problem whose ``carried`` operand is ``number``.

    The other operand is a number the problem gives, with the limits of ``_first_steps``: an
    addition's or subtraction's at most ``largest_given``, a multiplication's groups or size at
    most ``largest_groups`` or ``largest_size``, and a division's whole at most ``largest_given``
    and its groups at most ``largest_groups``. ``number`` isn't given, so as a number of groups
    or a group size it need only be at least the smallest. The answer is at most
    ``largest_number`` if given, and a division's answer, the size of each group, is at most
    ``largest_size``. A difference is at least 1.
    """
    smallest = SMALLEST_WORD_PROBLEM_NUMBER
    match operation:
        case Operation.ADD:
            most = largest_given if largest_number is None else largest_number - number
            for other in range(smallest, min(largest_given, most) + 1):
                operands = (number, other) if carried is Unknown.FIRST else (other, number)
                yield BasicOperationQuestionData(operation, operands, number + other)
        case Operation.SUBTRACT if carried is Unknown.FIRST:  # taking from the number
            for other in range(smallest, min(number - 1, largest_given) + 1):
                yield BasicOperationQuestionData(operation, (number, other), number - other)
        case Operation.SUBTRACT:  # taking the number away
            for other in range(number + 1, largest_given + 1):
                yield BasicOperationQuestionData(operation, (other, number), other - number)
        case Operation.MULTIPLY if carried is Unknown.FIRST:  # the number of groups
            if number >= WORD_PROBLEM_GROUPS[0]:
                most = largest_size if largest_number is None else largest_number // number
                for size in _group_sizes(min(largest_size, most)):
                    yield _equal_groups_problem(operation, number, size)
        case Operation.MULTIPLY:  # the size of each group
            if number >= WORD_PROBLEM_GROUP_SIZES[0]:
                most = largest_groups if largest_number is None else largest_number // number
                for groups in _group_counts(min(largest_groups, most)):
                    yield _equal_groups_problem(operation, groups, number)
        case Operation.DIVIDE if carried is Unknown.FIRST:  # the whole shared
            # only as many groups as leave each a size within the limits
            fewest = max(WORD_PROBLEM_GROUPS[0], -(-number // largest_size))
            most = min(largest_groups, number // WORD_PROBLEM_GROUP_SIZES[0])
            for groups in range(fewest, most + 1):
                size, remainder = divmod(number, groups)
                if not remainder:
                    yield _equal_groups_problem(operation, groups, size)
        case Operation.DIVIDE:  # the number of groups shared into
            if number >= WORD_PROBLEM_GROUPS[0]:  # the whole, which is given, within its limit
                for size in _group_sizes(min(largest_size, largest_given // number)):
                    yield _equal_groups_problem(operation, number, size)
        case _:
            assert_never(operation)


def _distinct_missing_divisors(
    count: int, low: int, high: int, largest_divisor: int | None
) -> list[MissingNumberFreeResponseQuestion]:
    """
    Generate ``count`` missing-divisor equations with distinct divisors and fact families.

    Drawing them one at a time and rejecting conflicts can deadlock. With dividends up to 10,
    10 ÷ □ = 10 (divisor 1) takes the family {1, 10}, the only family available to divisor 10,
    so no later draw for divisor 10 can succeed. Instead, the divisors are sampled first and
    assigned quotients from the largest divisor down, each choosing at random among the
    quotients whose family is still free. This cannot fail: the family of divisor ``d`` and the
    smallest quotient ``s`` could only have been taken by divisor ``s``, but every divisor
    assigned before ``d`` is larger than ``d``, which is at least ``s``.
    """
    smallest_quotient = max(low, 1)
    divisors = random.sample(_divisors(low, high, largest_divisor, smallest_quotient), count)
    questions: list[MissingNumberFreeResponseQuestion] = []
    families: set[tuple[int, int]] = set()
    for divisor in sorted(divisors, reverse=True):
        candidates = [
            MissingNumberQuestionData(
                Operation.DIVIDE, Unknown.SECOND, divisor * quotient, quotient, divisor
            )
            for quotient in range(smallest_quotient, high // divisor + 1)
        ]
        free = [candidate for candidate in candidates if _fact_family(candidate) not in families]
        data = random.choice(free)
        families.add(_fact_family(data))
        questions.append(Question(data, FreeResponse()))
    return questions


def _divisors(low: int, high: int, largest_divisor: int | None, smallest_quotient: int) -> range:
    """
    Return the divisors that leave room for ``smallest_quotient`` within a dividend of ``high``.

    They run from ``max(low, 1)`` to ``largest_divisor`` (``high`` when ``None``).
    """
    top = high // max(smallest_quotient, 1)
    return range(max(low, 1), min(high if largest_divisor is None else largest_divisor, top) + 1)


def _division_fact(
    low: int, high: int, largest_divisor: int | None, smallest_quotient: int
) -> tuple[int, int]:
    """
    Draw a random (divisor, quotient) pair whose dividend is at most ``high``.

    The divisor is drawn first, uniformly, so every divisor is equally likely however many
    quotients it allows. The quotient is then drawn from ``smallest_quotient`` upward.
    """
    # Possible refinement: every divisor, including 1, is equally likely, so at the default
    # limits about one question in ten divides by 1. Weighting this choice, or starting
    # _divisors at 2, would change that. The counts follow _divisors, except the division case
    # of count_possible_answers, which assumes the smallest divisor is 1 (or low).
    divisors = _divisors(low, high, largest_divisor, smallest_quotient)
    divisor = random.randint(divisors.start, divisors.stop - 1)
    return divisor, random.randint(smallest_quotient, high // divisor)


def _division_facts(
    low: int, high: int, largest_divisor: int | None, smallest_quotient: int
) -> Iterator[tuple[int, int]]:
    """Yield every (divisor, quotient) pair that ``_division_fact`` can draw."""
    for divisor in _divisors(low, high, largest_divisor, smallest_quotient):
        for quotient in range(smallest_quotient, high // divisor + 1):
            yield divisor, quotient


def _fact_family(data: MissingNumberQuestionData) -> tuple[int, int]:
    """Return the divisor and quotient, smaller first: 28 ÷ 4 = 7 and 28 ÷ 7 = 4 share a family."""
    divisor = data.known if data.unknown is Unknown.FIRST else data.answer
    return min(divisor, data.result), max(divisor, data.result)
