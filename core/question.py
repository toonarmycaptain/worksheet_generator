"""Question data, the ways a student responds, and questions pairing the two."""

import random
from dataclasses import dataclass
from typing import Any

BLANK = "\N{WHITE SQUARE}"  # in a question's text, where an empty square is drawn to write in


class QuestionData[Answer]:
    """
    Base class for question data.

    Each question type subclasses it with a frozen dataclass that defines the question and its
    correct answer, which is determined by the question itself. ``Answer`` is the answer's type:
    ``int`` for an arithmetic question, or a tuple of counts for a question with several blanks.
    Type-agnostic code, such as ``Question``, depends only on the attributes declared here.

    Deliberately not a dataclass: dataclass inheritance would place ``answer`` first in every
    subclass's fields, and so first among its ``__init__`` parameters. A bare annotation
    declares the attribute without creating a field, leaving each subclass to position it.
    """

    answer: Answer


@dataclass(frozen=True)
class FreeResponse:
    """The student writes the answer, which is the question data's ``answer``."""


@dataclass(frozen=True)
class MultipleChoice[Option]:
    """
    The student chooses from ``options``. ``correct_indexes`` holds the positions of the correct
    options, so a question can have several.

    An option's type is independent of the answer's. It is a number for an arithmetic question,
    but it can be a diagram, such as a number line, which is correct without being equal to the
    answer. So the correct options are stored rather than found by comparison with the answer.
    """

    options: tuple[Option, ...]
    correct_indexes: frozenset[int]


def multiple_choice[Option](
    correct_options: tuple[Option, ...], wrong_options: tuple[Option, ...]
) -> MultipleChoice[Option]:
    """Shuffle the correct and wrong options together, recording where the correct ones land."""
    tagged = [(option, True) for option in correct_options]
    tagged += [(option, False) for option in wrong_options]
    random.shuffle(tagged)
    return MultipleChoice(
        options=tuple(option for option, _ in tagged),
        correct_indexes=frozenset(index for index, (_, correct) in enumerate(tagged) if correct),
    )


@dataclass(frozen=True)
class Question[Data: QuestionData[Any], Response]:
    """
    A question's data paired with the way the student responds to it, such as ``FreeResponse``
    or ``MultipleChoice``.

    The response is not part of the data because it is a presentation choice: the same data can
    be multiple choice with different wrong answers, or free response.

    Generic such that ``data``'s type comes from whatever ``QuestionData`` subclass the
    ``Question`` is composed with, and ``response``'s type from the response it is given.
    """

    data: Data
    response: Response
