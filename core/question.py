"""Question data, and questions as presented with their answer options."""

import random

BLANK = "\N{WHITE SQUARE}"  # in a question's text, where an empty square is drawn to write in


class QuestionData:
    """
    Base class for question data.

    Each question type subclasses it with a frozen dataclass that defines the question and its
    correct answer, which is determined by the question itself. Type-agnostic code, such as
    ``Question``, depends only on the attributes declared here.

    Deliberately not a dataclass: dataclass inheritance would place ``answer`` first in every
    subclass's fields, and so first among its ``__init__`` parameters. A bare annotation
    declares the attribute without creating a field, leaving each subclass to position it.
    """

    answer: int


class Question[Data: QuestionData]:
    """
    A question's data paired with its wrong answers, shuffled together into ``options``.

    Wrong answers are not part of the data because they are a presentation choice: the same
    data can appear with different wrong answers, or with none on a free-response.

    ``options`` is shuffled once, at construction. The correct option's index is not stored;
    use ``options.index(data.answer)``.

    Generic such that ``data``'s type comes from whatever ``QuestionData`` subclass the ``Question``
    is composed with.
    """

    def __init__(self, data: Data, wrong_answers: tuple[int, ...]) -> None:
        self.data = data
        self.wrong_answers = wrong_answers
        options = [data.answer, *wrong_answers]
        random.shuffle(options)
        self.options = tuple(options)
