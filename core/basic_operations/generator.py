"""Random generation of arithmetic questions and missing-number equations."""

import random
from collections.abc import Iterator
from typing import assert_never

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.question import Question
from core.wrong_answers import WRONG_ANSWER_COUNT, random_wrong_answers

DEFAULT_LARGEST_OPERAND = 10  # the default for ``high``, the largest operand or dividend
DEFAULT_LARGEST_DIVIDEND = 100  # a division sheet's default ``high``
DEFAULT_LARGEST_DIVISOR = 10  # a division sheet's default ``largest_divisor``
MAXIMUM_OPERAND = 999  # the most a sheet allows for ``high`` and ``largest_divisor``


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


def generate_basic_operation_questions(
    count: int,
    operation: Operation,
    *,
    low: int = 0,
    high: int = DEFAULT_LARGEST_OPERAND,
    largest_divisor: int | None = None,
    wrong_answer_count: int = WRONG_ANSWER_COUNT,
    distinct_answers: bool = False,
) -> list[Question[BasicOperationQuestionData]]:
    """
    Generate ``count`` questions with no repeated operand pair, in either order.

    With ``distinct_answers``, no two questions share an answer either, so 3 + 4 excludes 2 + 5.
    ``largest_divisor`` applies to division, as in ``generate_basic_operation_question``.

    Raises ``ValueError`` if the settings allow fewer than ``count`` such questions.
    """
    if distinct_answers:
        possible = count_possible_answers(operation, low=low, high=high, up_to=count)
        kind = "questions with different answers"
    else:
        possible = count_possible_questions(
            operation, low=low, high=high, largest_divisor=largest_divisor, up_to=count
        )
        kind = "different questions"
    if count > possible:
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    questions: list[Question[BasicOperationQuestionData]] = []
    seen_pairs: set[tuple[int, ...]] = set()
    seen_answers: set[int] = set()
    while len(questions) < count:
        question = generate_basic_operation_question(
            operation,
            low=low,
            high=high,
            largest_divisor=largest_divisor,
            wrong_answer_count=wrong_answer_count,
        )
        pair = tuple(sorted(question.data.operands))
        answer = question.data.answer
        if pair in seen_pairs or (distinct_answers and answer in seen_answers):
            continue
        seen_pairs.add(pair)
        seen_answers.add(answer)
        questions.append(question)
    return questions


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
