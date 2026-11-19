"""Random generation of place-value questions."""

import random
from collections.abc import Sequence

from core.placevalue.data import PlaceValueForm, PlaceValueQuestion, PlaceValueQuestionData
from core.placevalue.representation import LARGEST_NUMBER
from core.question import FreeResponse, Question, multiple_choice
from core.wrong_answers import random_wrong_answers

# The default range of a question's number: four- and five-digit numbers.
DEFAULT_SMALLEST_NUMBER = 1000
DEFAULT_LARGEST_NUMBER = 99_999


def generate_place_value_question(
    given: Sequence[PlaceValueForm],
    asked: Sequence[PlaceValueForm],
    *,
    low: int = DEFAULT_SMALLEST_NUMBER,
    high: int = DEFAULT_LARGEST_NUMBER,
    wrong_answer_count: int = 0,
) -> PlaceValueQuestion:
    """
    Generate a question whose number is drawn at random from ``low`` to ``high``.

    The question shows its number in one of the ``given`` forms and asks for one of the
    ``asked`` forms, never the one it shows. The shown form is chosen first, from the given
    forms that leave a different form to ask for, then the asked form from the others: given
    standard and expanded and asked for expanded, the question is always standard to expanded.

    With a non-zero ``wrong_answer_count``, the question is multiple choice: its wrong answers
    are random numbers from ``low`` to ``high``, formatted in the asked form like the correct
    one.

    Raises ``ValueError`` if ``given`` or ``asked`` is empty, if both hold only the same form,
    or if ``low`` and ``high`` are not an ordered range within 1 to 999,999, the numbers the
    forms can represent.
    """
    _check_forms_and_range(given, asked, low, high)
    return _question(random.randint(low, high), given, asked, low, high, wrong_answer_count)


def generate_place_value_questions(
    count: int,
    given: Sequence[PlaceValueForm],
    asked: Sequence[PlaceValueForm],
    *,
    low: int = DEFAULT_SMALLEST_NUMBER,
    high: int = DEFAULT_LARGEST_NUMBER,
    wrong_answer_count: int = 0,
) -> list[PlaceValueQuestion]:
    """
    Generate ``count`` questions with distinct numbers, each with forms chosen on its own.

    The numbers are sampled from ``low`` to ``high`` without replacement, so none repeats.
    Raises ``ValueError`` as ``generate_place_value_question`` does, or if the range holds fewer
    than ``count`` numbers.
    """
    _check_forms_and_range(given, asked, low, high)
    possible = high - low + 1
    if count > possible:
        raise ValueError(
            f"Cannot make {count} questions with different numbers: only {possible} possible."
        )
    numbers = random.sample(range(low, high + 1), count)
    return [_question(number, given, asked, low, high, wrong_answer_count) for number in numbers]


def _check_forms_and_range(
    given: Sequence[PlaceValueForm], asked: Sequence[PlaceValueForm], low: int, high: int
) -> None:
    if not given or not asked:
        raise ValueError("A question needs a form to show and a form to ask for.")
    if len({*given, *asked}) == 1:
        raise ValueError("A question cannot ask for the form it shows.")
    if not 1 <= low <= high <= LARGEST_NUMBER:
        raise ValueError(
            f"The numbers must be from 1 to {LARGEST_NUMBER:,}, with low no more than high, "
            f"not {low:,} to {high:,}."
        )


def _question(
    number: int,
    given: Sequence[PlaceValueForm],
    asked: Sequence[PlaceValueForm],
    low: int,
    high: int,
    wrong_answer_count: int,
) -> PlaceValueQuestion:
    """Build the question for ``number``, choosing its forms and its wrong answers."""
    given_form = random.choice([form for form in given if any(other != form for other in asked)])
    asked_form = random.choice([form for form in asked if form != given_form])
    data = PlaceValueQuestionData(number, given_form, asked_form)
    wrong_answers = random_wrong_answers(number, count=wrong_answer_count, low=low, high=high)
    if not wrong_answers:
        return Question(data, FreeResponse())
    return Question(data, multiple_choice((number,), wrong_answers))
