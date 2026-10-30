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
    candidates = set(range(low, high + 1))
    if allow_negatives:
        candidates |= {-magnitude for magnitude in candidates}
    candidates.discard(correct_answer)

    if count > len(candidates):
        raise ValueError(
            f"Cannot pick {count} wrong answers: only {len(candidates)} possible "
            f"between {low} and {high} (allow_negatives={allow_negatives})."
        )
    return tuple(random.sample(sorted(candidates), count))
