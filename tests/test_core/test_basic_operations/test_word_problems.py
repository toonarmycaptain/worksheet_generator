"""
Tests for the word-problem bank: every template's slots, and the wording of a sheet's questions.

``random`` is scripted: ``sample_first`` takes the first two names and leaves each operation's
templates in order, so they are used from the last, with any comparisons after them, and
``choose_last`` takes the last object, card or cards.
"""

from string import Formatter

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.word_problems import (
    COMPARISON_TEMPLATES,
    TEMPLATES,
    word_problem_texts,
)
from tests.helpers import choose_last, sample_first

ADD = BasicOperationQuestionData(Operation.ADD, (47, 25), 72)
SUBTRACT = BasicOperationQuestionData(Operation.SUBTRACT, (72, 25), 47)
ADD_ONES = BasicOperationQuestionData(Operation.ADD, (1, 1), 2)
SUBTRACT_ONE = BasicOperationQuestionData(Operation.SUBTRACT, (2, 1), 1)


@pytest.mark.parametrize(
    ("questions", "comparisons", "expected"),
    [
        (
            [ADD],
            False,
            ["A basket held 47 cards. Maria added 25 more. How many cards are in the basket now?"],
        ),
        (
            [SUBTRACT],
            False,
            ["Maria needs 72 cards in all and has 25 so far. How many more cards are needed?"],
        ),
        # with comparisons, subtraction's comparison joins its templates, and comes last
        (
            [SUBTRACT],
            True,
            [
                "Maria has 72 cards and Jamal has 25 cards. "
                "How many more cards does Maria have than Jamal?"
            ],
        ),
        # addition has no comparisons
        (
            [ADD],
            True,
            ["A basket held 47 cards. Maria added 25 more. How many cards are in the basket now?"],
        ),
        # each operation has its own templates, used up separately
        (
            [ADD, SUBTRACT, ADD],
            False,
            [
                "A basket held 47 cards. Maria added 25 more. "
                "How many cards are in the basket now?",
                "Maria needs 72 cards in all and has 25 so far. How many more cards are needed?",
                "Maria scored 47 points, then scored 25 more points. How many points in all?",
            ],
        ),
        # no template repeats until all eight are used, then they are drawn again
        (
            [ADD] * 9,
            False,
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
                "A farm picked 47 apples and then picked 25 more. "
                "How many apples were picked in all?",
                "The library had 47 books. It received 25 more books. "
                "How many books does the library have now?",
                "A basket held 47 cards. Maria added 25 more. "
                "How many cards are in the basket now?",
            ],
        ),
        # 1 takes the singular, and the words that agree with it, in every addition story
        (
            [ADD_ONES] * 8,
            False,
            [
                "A basket held 1 card. Maria added 1 more. How many cards are in the basket now?",
                "Maria scored 1 point, then scored 1 more point. How many points in all?",
                "Maria read 1 page on Monday and 1 page on Tuesday. How many pages in all?",
                "Maria had 1 card and found 1 more. How many cards does Maria have now?",
                "There was 1 card in the bin. Maria put in 1 more. "
                "How many cards are in the bin now?",
                "Maria collected 1 card. Jamal collected 1 card. "
                "How many cards did they collect altogether?",
                "A farm picked 1 apple and then picked 1 more. How many apples were picked in all?",
                "The library had 1 book. It received 1 more book. "
                "How many books does the library have now?",
            ],
        ),
        # and in every subtraction story, the comparison included, while 2 stays plural
        (
            [SUBTRACT_ONE] * 7,
            True,
            [
                "Maria has 2 cards and Jamal has 1 card. "
                "How many more cards does Maria have than Jamal?",
                "Maria needs 2 cards in all and has 1 so far. How many more cards are needed?",
                "Maria had 2 points and lost 1 point. How many points does Maria have now?",
                "A book has 2 pages. Maria has read 1 page. How many pages are left to read?",
                "Maria had 2 cards and used 1. How many cards are left?",
                "There were 2 cards on the shelf. 1 of them was sold. How many cards are left?",
                "Maria had 2 cards. Maria gave away 1 of them. "
                "How many cards does Maria have left?",
            ],
        ),
    ],
)
def test_word_problem_texts(
    questions: list[BasicOperationQuestionData],
    comparisons: bool,
    expected: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    assert word_problem_texts(questions, comparisons=comparisons) == expected


@pytest.mark.parametrize(
    "templates",
    [
        pytest.param(TEMPLATES[Operation.ADD], id="add"),
        pytest.param(TEMPLATES[Operation.SUBTRACT], id="subtract"),
        pytest.param(TEMPLATES[Operation.MULTIPLY], id="multiply"),
        pytest.param(TEMPLATES[Operation.DIVIDE], id="divide"),
        pytest.param(COMPARISON_TEMPLATES[Operation.SUBTRACT], id="subtract comparisons"),
    ],
)
def test_every_template_shows_both_operands_and_uses_only_the_shared_slots(
    templates: tuple[str, ...],
) -> None:
    """
    Each template uses {a} and {b}, and no slot outside {n1} {n2} {obj} {a_obj} {b_obj} {a} {b}.
    """
    for template in templates:
        slots = {field for _, field, _, _ in Formatter().parse(template) if field}
        assert {"a", "b"} <= slots <= {"n1", "n2", "obj", "a_obj", "b_obj", "a", "b"}, template
