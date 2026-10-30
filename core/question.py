"""The question that is shown: its data together with the choices to pick from."""

import random

from core.arithmetic import ArithmeticQuestionData


class Question:
    """An arithmetic question with its wrong answers and the shuffled choices.

    ``data`` holds the correct answer and ``wrong_answers`` the others. ``options`` is made
    from the two when the question is created, in a random order. Look up the correct
    choice with ``options.index(data.answer)`` rather than storing it separately.
    """

    def __init__(self, data: ArithmeticQuestionData, wrong_answers: tuple[int, ...]) -> None:
        self.data = data
        self.wrong_answers = wrong_answers
        options = [data.answer, *wrong_answers]
        random.shuffle(options)
        self.options = tuple(options)
