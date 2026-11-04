"""Wrong answers for questions with a whole-number answer."""

import random

WRONG_ANSWER_COUNT = 3  # per multiple-choice question, giving four options


def random_wrong_answers(
    correct_answer: int,
    *,
    count: int,
    low: int = 0,
    high: int = 100,
    allow_negatives: bool = False,
) -> tuple[int, ...]:
    """
    Return ``count`` distinct wrong answers drawn at random, excluding ``correct_answer``.

    ``low`` and ``high`` bound the magnitude of a wrong answer, inclusive (0 to 100 by default).
    With ``allow_negatives`` (off by default), the negative of each magnitude is also eligible,
    so a correct answer of 4 can have -4 as a wrong answer.

    Raises ``ValueError`` if fewer than ``count`` wrong answers are available.
    """
    # The pool of wrong answers, lowest first: the negatives if allowed (0 has none), then
    # low to high. It is held as ranges so that no number is materialized, however wide the
    # pool; the correct answer splits whichever range contains it.
    whole = [range(-high, -max(low, 1) + 1)] if allow_negatives else []
    whole.append(range(low, high + 1))
    pool: list[range] = []
    for numbers in whole:
        if correct_answer in numbers:
            pool += [range(numbers.start, correct_answer), range(correct_answer + 1, numbers.stop)]
        else:
            pool.append(numbers)
    size = sum(len(numbers) for numbers in pool)

    if count > size:
        raise ValueError(
            f"Cannot pick {count} wrong answer{'' if count == 1 else 's'}: only {size} possible "
            f"between {low} and {high} (allow_negatives={allow_negatives})."
        )
    # random.sample draws distinct positions from the range without building it as a list
    return tuple(_number_at(pool, position) for position in random.sample(range(size), count))


def _number_at(pool: list[range], position: int) -> int:
    """Return the number at ``position`` in the pool's ranges, taken end to end."""
    for numbers in pool:
        if position < len(numbers):
            return numbers[position]
        position -= len(numbers)
    raise IndexError(position)
