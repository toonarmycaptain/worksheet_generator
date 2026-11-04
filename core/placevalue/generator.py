"""Random generation of place-value questions."""

import random

from core.placevalue.data import PlaceValueForm, PlaceValueQuestionData
from core.placevalue.representation import LARGEST_NUMBER
from core.question import Question
from core.wrong_answers import random_wrong_answers

# The default range of a question's number: four- and five-digit numbers.
DEFAULT_SMALLEST_NUMBER = 1000
DEFAULT_LARGEST_NUMBER = 99_999


def generate_place_value_question(
    given: PlaceValueForm | None,
    asked: PlaceValueForm | None,
    *,
    low: int = DEFAULT_SMALLEST_NUMBER,
    high: int = DEFAULT_LARGEST_NUMBER,
    wrong_answer_count: int = 0,
) -> Question[PlaceValueQuestionData]:
    """
    Generate a question whose number is drawn at random from ``low`` to ``high``.

    A form of ``None`` is mixed: it is chosen at random for this question and never equals the
    other form, so a question never asks for the form it shows. When both are ``None``, the
    given form is chosen first.

    With a non-zero ``wrong_answer_count``, the question is multiple choice: its wrong answers
    are random numbers from ``low`` to ``high``, formatted in the asked form like the correct
    one.

    Raises ``ValueError`` if ``given`` equals ``asked``, or if ``low`` and ``high`` are not an
    ordered range within 1 to 999,999, the numbers the forms can represent.
    """
    _check_forms_and_range(given, asked, low, high)
    return _question(random.randint(low, high), given, asked, low, high, wrong_answer_count)


def generate_place_value_questions(
    count: int,
    given: PlaceValueForm | None,
    asked: PlaceValueForm | None,
    *,
    low: int = DEFAULT_SMALLEST_NUMBER,
    high: int = DEFAULT_LARGEST_NUMBER,
    wrong_answer_count: int = 0,
) -> list[Question[PlaceValueQuestionData]]:
    """
    Generate ``count`` questions with distinct numbers, whatever their forms.

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
    given: PlaceValueForm | None, asked: PlaceValueForm | None, low: int, high: int
) -> None:
    if given is not None and given == asked:
        raise ValueError("A question cannot ask for the form it shows.")
    if not 1 <= low <= high <= LARGEST_NUMBER:
        raise ValueError(
            f"The numbers must be from 1 to {LARGEST_NUMBER:,}, with low no more than high, "
            f"not {low:,} to {high:,}."
        )


def _question(
    number: int,
    given: PlaceValueForm | None,
    asked: PlaceValueForm | None,
    low: int,
    high: int,
    wrong_answer_count: int,
) -> Question[PlaceValueQuestionData]:
    """Build the question for ``number``, choosing any mixed forms and its wrong answers."""
    if given is None:
        given = random.choice([form for form in PlaceValueForm if form != asked])
    if asked is None:
        asked = random.choice([form for form in PlaceValueForm if form != given])
    wrong_answers = random_wrong_answers(number, count=wrong_answer_count, low=low, high=high)
    return Question(PlaceValueQuestionData(number, given, asked), wrong_answers)
