"""Wrong answers for questions with a whole-number answer."""

import random


def random_wrong_answers(
    correct_answer: int,
    *,
    count: int,
    low: int = 0,
    high: int = 100,
    allow_negatives: bool = False,
) -> tuple[int, ...]:
    """Pick ``count`` different wrong answers at random, never ``correct_answer``.

    ``low`` and ``high`` limit the magnitude of a wrong answer, both inclusive (0 to 100
    by default). With ``allow_negatives`` (off by default) the negative of each magnitude
    is also possible, so a correct answer of 4 can have -4 as a wrong answer.
    """
    # The pool of wrong answers, lowest first: the negatives if allowed (0 has none), then
    # low to high. It is kept as ranges so no number in it is ever made, however wide it is.
    # The correct answer splits whichever range holds it.
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
            f"Cannot pick {count} wrong answers: only {size} possible "
            f"between {low} and {high} (allow_negatives={allow_negatives})."
        )
    # sample picks positions in the pool, drawing again on a repeat
    return tuple(_number_at(pool, position) for position in random.sample(range(size), count))


def _number_at(pool: list[range], position: int) -> int:
    """The number at ``position`` in the pool's ranges laid end to end."""
    for numbers in pool:
        if position < len(numbers):
            return numbers[position]
        position -= len(numbers)
    raise IndexError(position)
