"""Generating random addition, subtraction and multiplication questions."""

import random
from typing import assert_never

from core.arithmetic import ArithmeticQuestionData, Operation
from core.question import Question
from core.wrong_answers import random_wrong_answers


def generate_arithmetic_question(
    operation: Operation,
    *,
    low: int = 0,
    high: int = 10,
    wrong_answer_count: int = 3,
) -> Question:
    """One random question whose operands are whole numbers from ``low`` to ``high``.

    Subtraction always puts the larger operand first, so the answer is never negative.
    The wrong answers are random, from 0 up to the largest answer these operands can give
    (or ``wrong_answer_count`` if that is larger, so there are always enough to pick from).
    """
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
        case Operation.DIVIDE:
            raise NotImplementedError("Division questions are not built yet.")
        case _:
            assert_never(operation)

    data = ArithmeticQuestionData(operation, (first, second), answer)
    wrong_answers = random_wrong_answers(
        answer, count=wrong_answer_count, high=max(largest_answer, wrong_answer_count)
    )
    return Question(data, wrong_answers)


def possible_answers(operation: Operation, *, low: int = 0, high: int = 10) -> set[int]:
    """Every answer a question can have, with operands from ``low`` to ``high``."""
    pairs = [(first, second) for first in range(low, high + 1) for second in range(first, high + 1)]
    match operation:
        case Operation.ADD:
            return {first + second for first, second in pairs}
        case Operation.SUBTRACT:
            return {second - first for first, second in pairs}
        case Operation.MULTIPLY:
            return {first * second for first, second in pairs}
        case Operation.DIVIDE:
            raise NotImplementedError("Division questions are not built yet.")
        case _:
            assert_never(operation)


def generate_arithmetic_questions(
    count: int,
    operation: Operation,
    *,
    low: int = 0,
    high: int = 10,
    wrong_answer_count: int = 3,
    distinct_answers: bool = False,
) -> list[Question]:
    """``count`` questions with no repeats. A flipped pair (3 and 4, 4 and 3) is a repeat.

    With ``distinct_answers`` no two questions have the same answer either, so 3 + 4 rules out
    2 + 5.
    """
    if distinct_answers:
        possible = len(possible_answers(operation, low=low, high=high))
        kind = "questions with different answers"
    else:
        values = high - low + 1
        possible = values * (values + 1) // 2  # pairs of operands, ignoring their order
        kind = "different questions"
    if count > possible:
        raise ValueError(f"Cannot make {count} {kind}: only {possible} possible.")

    questions: list[Question] = []
    seen_pairs: set[tuple[int, ...]] = set()
    seen_answers: set[int] = set()
    while len(questions) < count:
        question = generate_arithmetic_question(
            operation, low=low, high=high, wrong_answer_count=wrong_answer_count
        )
        pair = tuple(sorted(question.data.operands))
        answer = question.data.answer
        if pair in seen_pairs or (distinct_answers and answer in seen_answers):
            continue
        seen_pairs.add(pair)
        seen_answers.add(answer)
        questions.append(question)
    return questions
