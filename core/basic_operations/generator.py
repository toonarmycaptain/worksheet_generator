"""Random generation of arithmetic questions, missing-number equations and word problems."""

import random
from collections.abc import Iterator, Sequence
from dataclasses import replace
from functools import partial
from itertools import accumulate
from typing import Literal, assert_never

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.basic_operations.word_problems import word_problem_texts
from core.question import Question
from core.wrong_answers import WRONG_ANSWER_COUNT, random_wrong_answers

DEFAULT_LARGEST_OPERAND = 10  # the default for ``high``, the largest operand or dividend
DEFAULT_LARGEST_DIVIDEND = 100  # a division sheet's default ``high``
DEFAULT_LARGEST_DIVISOR = 10  # a division sheet's default ``largest_divisor``
MAXIMUM_OPERAND = 999  # the most a sheet allows for ``high`` and ``largest_divisor``

# The operand sizes of a sheet's word problems, in digits (first, second), used in turn
WORD_PROBLEM_DIGITS = ((2, 2), (2, 3), (3, 2), (3, 3))
# Number of digits -> the smallest and largest operand of that size in a word problem
WORD_PROBLEM_RANGES = {2: (11, 99), 3: (100, 999)}
LARGEST_WORD_PROBLEM_SUM = 999
SMALLEST_WORD_PROBLEM_DIFFERENCE = 10
# The number of equal groups in a multiplication or division word problem, smallest and largest;
# six is as many as a strip diagram has room for
WORD_PROBLEM_GROUPS = (2, 6)
WORD_PROBLEM_GROUP_SIZES = (2, 20)  # the number in each of those groups, smallest and largest


def generate_basic_operation_question(
    operation: Operation,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    wrong_answer_count: int = WRONG_ANSWER_COUNT,
) -> Question[BasicOperationQuestionData]:
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
        return Question(data, wrong_answers)

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
    return Question(data, wrong_answers)


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
) -> list[Question[BasicOperationQuestionData]]:
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

    questions: list[Question[BasicOperationQuestionData]] = []
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

    The shares are in the order of ``_rank_by_answers``: when ``count`` does not divide evenly,
    the extra questions go to the last operations, those with the most possible answers.
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
) -> Question[MissingNumberQuestionData]:
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
    return Question(data, ())


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
) -> list[Question[MissingNumberQuestionData]]:
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
    questions: list[Question[MissingNumberQuestionData]] = []
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
    operations: Sequence[Operation], *, distinct_answers: bool = False, up_to: int
) -> int:
    """
    Count the word problems ``generate_word_problems`` can produce for ``operations``.

    As in ``count_possible_sheet_questions``, any one operation may be drawn for every problem,
    so the count is the smallest that any one operation allows by itself: its distinct answers
    with ``distinct_answers``, and otherwise its distinct problems. For addition and subtraction
    this is the fewest answers at any operand size, the 79 differences of two 2-digit operands,
    from 10 to 88. The count is capped at ``up_to``.
    """
    groups = range(WORD_PROBLEM_GROUPS[0], WORD_PROBLEM_GROUPS[1] + 1)
    sizes = range(WORD_PROBLEM_GROUP_SIZES[0], WORD_PROBLEM_GROUP_SIZES[1] + 1)
    counts = [up_to]
    for operation in operations:
        match operation:
            case Operation.ADD | Operation.SUBTRACT:
                smallest, largest = WORD_PROBLEM_RANGES[2]
                counts.append(largest - smallest - SMALLEST_WORD_PROBLEM_DIFFERENCE + 1)
            case Operation.MULTIPLY if distinct_answers:
                counts.append(len({number * size for number in groups for size in sizes}))
            case Operation.DIVIDE if distinct_answers:
                counts.append(len(sizes))  # the answer is the size of each group
            case Operation.MULTIPLY | Operation.DIVIDE:
                counts.append(len(groups) * len(sizes))
            case _:
                assert_never(operation)
    return min(counts)


def generate_word_problems(
    count: int,
    operations: Sequence[Operation],
    *,
    distinct_answers: bool = False,
    comparisons: bool = False,
) -> list[Question[BasicOperationQuestionData]]:
    """
    Generate ``count`` word problems, each with an operation drawn at random from ``operations``.

    Addition and subtraction take the operand sizes in ``WORD_PROBLEM_DIGITS`` in turn, in random
    order: 2-digit operands are 11 to 99 and 3-digit operands 100 to 999. A sum is at most 999,
    and a difference at least 10, with the larger operand first. Multiplication and division are
    equal groups, as in ``_equal_groups``. The wording comes from the word-problem bank, with its
    comparisons too if ``comparisons`` is set. The problems are answered in writing, so they have
    no wrong answers.

    No two problems of the same operation have the same operands, and with ``distinct_answers``
    no two problems share an answer either: a problem that breaks either rule is drawn again.

    Raises ``ValueError`` if the operations allow fewer than ``count`` such problems, as counted
    by ``count_possible_word_problems``.
    """
    possible = count_possible_word_problems(
        operations, distinct_answers=distinct_answers, up_to=count
    )
    if count > possible:
        kind = "problems with different answers" if distinct_answers else "different problems"
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    chosen = random.choices(operations, k=count)
    sums_and_differences = sum(
        operation in (Operation.ADD, Operation.SUBTRACT) for operation in chosen
    )
    digits = [
        WORD_PROBLEM_DIGITS[index % len(WORD_PROBLEM_DIGITS)]
        for index in range(sums_and_differences)
    ]
    random.shuffle(digits)
    next_digits = iter(digits)
    unworded: list[BasicOperationQuestionData] = []
    seen: set[tuple[Operation, tuple[int, int]]] = set()
    answers: set[int] = set()
    for operation in chosen:
        match operation:
            case Operation.ADD | Operation.SUBTRACT:
                draw = partial(_sum_or_difference, operation, next(next_digits))
            case Operation.MULTIPLY | Operation.DIVIDE:
                draw = partial(_equal_groups, operation)
            case _:
                assert_never(operation)
        data = draw()
        while (operation, data.operands) in seen or (distinct_answers and data.answer in answers):
            data = draw()
        seen.add((operation, data.operands))
        answers.add(data.answer)
        unworded.append(data)
    texts = word_problem_texts(unworded, comparisons=comparisons)
    return [
        Question(replace(data, question_text=text), ())
        for data, text in zip(unworded, texts, strict=True)
    ]


def _sum_or_difference(
    operation: Literal[Operation.ADD, Operation.SUBTRACT], digits: tuple[int, int]
) -> BasicOperationQuestionData:
    """
    Draw operands with ``digits`` digits, redrawing until they meet the word-problem limits.

    At least 39% of draws meet them (the hardest case is two 3-digit operands with a sum of at
    most 999), so the chance of needing more than 30 draws is below one in a million.
    """
    first_digits, second_digits = digits
    while True:
        first = random.randint(*WORD_PROBLEM_RANGES[first_digits])
        second = random.randint(*WORD_PROBLEM_RANGES[second_digits])
        match operation:
            case Operation.ADD:
                if first + second <= LARGEST_WORD_PROBLEM_SUM:
                    return BasicOperationQuestionData(operation, (first, second), first + second)
            case Operation.SUBTRACT:
                first, second = max(first, second), min(first, second)
                if first - second >= SMALLEST_WORD_PROBLEM_DIFFERENCE:
                    return BasicOperationQuestionData(operation, (first, second), first - second)
            case _:
                assert_never(operation)


def _equal_groups(
    operation: Literal[Operation.MULTIPLY, Operation.DIVIDE],
) -> BasicOperationQuestionData:
    """
    Draw an equal-groups problem: a number of groups from ``WORD_PROBLEM_GROUPS``, each of a
    size from ``WORD_PROBLEM_GROUP_SIZES``.

    Multiplication's operands are the groups and the size, so 3 groups of 4 is (3, 4), and the
    whole is to find. Division is partitive: its operands are the whole and the groups it is
    shared into, so 12 shared into 3 groups is (12, 3), and the size of each group is to find.
    """
    groups = random.randint(*WORD_PROBLEM_GROUPS)
    size = random.randint(*WORD_PROBLEM_GROUP_SIZES)
    match operation:
        case Operation.MULTIPLY:
            return BasicOperationQuestionData(operation, (groups, size), groups * size)
        case Operation.DIVIDE:
            return BasicOperationQuestionData(operation, (groups * size, groups), size)
        case _:
            assert_never(operation)


def _distinct_missing_divisors(
    count: int, low: int, high: int, largest_divisor: int | None
) -> list[Question[MissingNumberQuestionData]]:
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
    questions: list[Question[MissingNumberQuestionData]] = []
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
        questions.append(Question(data, ()))
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
