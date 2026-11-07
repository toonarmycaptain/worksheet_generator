"""
Tests for the word-problem bank: every template's slots, and the wording of a sheet's questions.

``random`` is scripted: ``sample_first`` takes the first two names and leaves each operation's
templates in order, so they are used from the last, and ``choose_last`` takes the last object,
cards.
"""

from string import Formatter

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.word_problems import TEMPLATES, word_problem_texts
from tests.helpers import choose_last, sample_first

ADD = BasicOperationQuestionData(Operation.ADD, (47, 25), 72)
SUBTRACT = BasicOperationQuestionData(Operation.SUBTRACT, (72, 25), 47)


@pytest.mark.parametrize(
    ("questions", "expected"),
    [
        (
            [ADD],
            ["A basket held 47 cards. Maria added 25 more. How many cards are in the basket now?"],
        ),
        (
            [SUBTRACT],
            ["Maria needs 72 cards in all and has 25 so far. How many more cards are needed?"],
        ),
        # each operation has its own templates, used up separately
        (
            [ADD, SUBTRACT, ADD],
            [
                "A basket held 47 cards. Maria added 25 more. "
                "How many cards are in the basket now?",
                "Maria needs 72 cards in all and has 25 so far. How many more cards are needed?",
                "Maria scored 47 points, then scored 25 more points. How many points in all?",
            ],
        ),
        # no template repeats until all six are used, then they are drawn again
        (
            [ADD] * 7,
            [
                "A basket held 47 cards. Maria added 25 more. "
                "How many cards are in the basket now?",
                "Maria scored 47 points, then scored 25 more points. How many points in all?",
                "Maria read 47 pages on Monday and 25 pages on Tuesday. How many pages in all?",
                "Maria had 47 cards and found 25 more. How many cards does Maria have now?",
                "There were 47 cards in the bin. Maria put in 25 more. "
                "How many cards are in the bin now?",
                "Maria collected 47 cards. Jamal collected 25 cards. "
                "How many cards did they collect altogether?",
                "A basket held 47 cards. Maria added 25 more. "
                "How many cards are in the basket now?",
            ],
        ),
    ],
)
def test_word_problem_texts(
    questions: list[BasicOperationQuestionData],
    expected: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    assert word_problem_texts(questions) == expected


@pytest.mark.parametrize("operation", list(TEMPLATES))
def test_every_template_shows_both_operands_and_uses_only_the_shared_slots(
    operation: Operation,
) -> None:
    """Each template uses {a} and {b}, and no slot outside {n1} {n2} {obj} {a} {b}."""
    for template in TEMPLATES[operation]:
        slots = {field for _, field, _, _ in Formatter().parse(template) if field}
        assert {"a", "b"} <= slots <= {"n1", "n2", "obj", "a", "b"}, template
