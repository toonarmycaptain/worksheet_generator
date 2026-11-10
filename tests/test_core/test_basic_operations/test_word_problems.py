"""
Tests for the word-problem bank: every template's slots, and the wording of a sheet's questions,
with one step or two.

``random`` is scripted: ``sample_first`` takes the first two names and leaves each operation's,
or each two-step shape's, templates in order, so they are used from the last, with any
comparisons after them, and ``choose_last`` takes the last object, card or cards.
"""

from collections.abc import Callable
from string import Formatter
from typing import Any

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    Unknown,
)
from core.basic_operations.word_problems import (
    COMPARISON_TEMPLATES,
    TEMPLATES,
    TWO_STEP_TEMPLATES,
    two_step_texts,
    word_problem_texts,
)
from tests.helpers import choose_last, sample_first

ADD = BasicOperationQuestionData(Operation.ADD, (47, 25), 72)
SUBTRACT = BasicOperationQuestionData(Operation.SUBTRACT, (72, 25), 47)
ADD_ONES = BasicOperationQuestionData(Operation.ADD, (1, 1), 2)
SUBTRACT_ONE = BasicOperationQuestionData(Operation.SUBTRACT, (2, 1), 1)

# one two-step problem of each shape: (4 + 6) + 7, (25 - 5) - 8, (24 - 6) ÷ 3, (3 x 5) + 4 and
# 45 - (3 x 5)
ADD_ADD = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
    ),
    Unknown.FIRST,
    17,
)
SUBTRACT_SUBTRACT = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
    ),
    Unknown.FIRST,
    12,
)
SUBTRACT_DIVIDE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
        BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
    ),
    Unknown.FIRST,
    6,
)
MULTIPLY_ADD = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
        BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
    ),
    Unknown.FIRST,
    19,
)
MULTIPLY_SUBTRACT = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
        BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
    ),
    Unknown.SECOND,
    30,
)
# a given number of 1: the first, the second and the last
ADD_ADD_ONE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.ADD, (1, 6), 7),
        BasicOperationQuestionData(Operation.ADD, (7, 4), 11),
    ),
    Unknown.FIRST,
    11,
)
SUBTRACT_DIVIDE_ONE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (19, 1), 18),
        BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
    ),
    Unknown.FIRST,
    6,
)
MULTIPLY_ADD_ONE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
        BasicOperationQuestionData(Operation.ADD, (15, 1), 16),
    ),
    Unknown.FIRST,
    16,
)

ONE_STEP_SLOTS = {"n1", "n2", "obj", "a_obj", "b_obj", "a", "b"}
TWO_STEP_SLOTS = {"n1", "n2", "obj", "a_obj", "b_obj", "c_obj", "a", "b", "c"}


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
        # eight in turn, from the last
        (
            [ADD] * 8,
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
            ],
        ),
        # 1 takes the singular, and the words that agree with it, in every addition story
        (
            [ADD_ONES] * 14,
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
                "A museum had 1 visitor on Saturday and 1 visitor on Sunday. "
                "How many visitors did the museum have in all?",
                "Maria took 1 step before lunch and 1 step after lunch. "
                "How many steps did Maria take in all?",
                "The school play sold 1 ticket on Friday and 1 ticket on Saturday. "
                "How many tickets did the play sell in all?",
                "A farm has 1 cow and 1 horse. How many animals are on the farm?",
                "A parking lot had 1 car. Then 1 more car parked there. "
                "How many cars are in the parking lot now?",
                "A school collected 1 can of food on Monday and 1 can on Tuesday. "
                "How many cans of food did the school collect in all?",
            ],
        ),
        # and in every subtraction story, the comparisons included, while 2 stays plural
        (
            [SUBTRACT_ONE] * 16,
            True,
            [
                "Maria has 2 cards and Jamal has 1 card. "
                "How many more cards does Maria have than Jamal?",
                "A school sold 2 tickets on Friday and 1 ticket on Saturday. "
                "How many more tickets were sold on Friday than on Saturday?",
                "Maria has 2 cards. Jamal has 1 card. "
                "How many fewer cards does Jamal have than Maria?",
                "Maria scored 2 points and Jamal scored 1 point. "
                "How many more points did Maria score than Jamal?",
                "Maria needs 2 cards in all and has 1 so far. How many more cards are needed?",
                "Maria had 2 points and lost 1 point. How many points does Maria have now?",
                "A book has 2 pages. Maria has read 1 page. How many pages are left to read?",
                "Maria had 2 cards and used 1. How many cards are left?",
                "There were 2 cards on the shelf. 1 of them was sold. How many cards are left?",
                "Maria had 2 cards. Maria gave away 1 of them. "
                "How many cards does Maria have left?",
                "Maria had 2 dollars and spent 1 dollar. How many dollars does Maria have left?",
                "A tree had 2 leaves. 1 leaf fell off. How many leaves are still on the tree?",
                "A store had 2 bottles of water and sold 1 of them. "
                "How many bottles of water does the store have left?",
                "Maria had 2 cards and put 1 of them in a box. How many cards are not in the box?",
                "A bus had 2 passengers. At the first stop, 1 passenger got off. "
                "How many passengers are on the bus now?",
                "The theater has 2 seats. 1 of them is filled. How many seats are empty?",
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
    ("questions", "expected"),
    [
        (
            [ADD_ADD],
            [
                "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                "How many cards are in the jar now?"
            ],
        ),
        (
            [SUBTRACT_SUBTRACT],
            [
                "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                "How many cards are left in the box?"
            ],
        ),
        (
            [SUBTRACT_DIVIDE],
            [
                "Maria has 24 cards. 6 are in a box, and the rest are in 3 bags with the same "
                "number in each bag. How many cards are in each bag?"
            ],
        ),
        (
            [MULTIPLY_ADD],
            [
                "There are 3 boxes with 5 cards in each box. Maria brings 4 more. "
                "How many cards are there now?"
            ],
        ),
        # the whole, {c}, comes first in the wording
        (
            [MULTIPLY_SUBTRACT],
            [
                "A store had 45 cards. It sold 3 packs with 5 cards in each pack. "
                "How many cards does the store have left?"
            ],
        ),
        # three in turn, from the last
        (
            [SUBTRACT_DIVIDE] * 3,
            [
                "Maria has 24 cards. 6 are in a box, and the rest are in 3 bags with the same "
                "number in each bag. How many cards are in each bag?",
                "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                "How many cards are in each group?",
                "Maria has 24 cards. Maria gives 6 to Jamal and then shares the rest equally "
                "among 3 friends. How many cards does each friend get?",
            ],
        ),
        # each shape has its own templates, used up separately
        (
            [ADD_ADD, SUBTRACT_SUBTRACT, ADD_ADD],
            [
                "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                "How many cards are in the jar now?",
                "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                "How many cards are left in the box?",
                "Maria had 4 cards. Maria found 6 more on Monday and 7 more on Tuesday. "
                "How many cards does Maria have now?",
            ],
        ),
        # 1 takes the singular, and the words that agree with it, in {a}, {b} and {c}
        (
            [SUBTRACT_DIVIDE_ONE, MULTIPLY_ADD_ONE, MULTIPLY_ADD_ONE, ADD_ADD_ONE],
            [
                "Maria has 19 cards. 1 is in a box, and the rest are in 3 bags with the same "
                "number in each bag. How many cards are in each bag?",
                "There are 3 boxes with 5 cards in each box. Maria brings 1 more. "
                "How many cards are there now?",
                "Maria has 3 bags with 5 cards in each bag, and 1 more card on the table. "
                "How many cards does Maria have in all?",
                "A jar held 1 card. Maria added 6 more, and then Jamal added 4 more. "
                "How many cards are in the jar now?",
            ],
        ),
        # the shapes text only shows, beyond the strip diagram's five
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (12, 5), 17),
                        BasicOperationQuestionData(Operation.SUBTRACT, (17, 8), 9),
                    ),
                    Unknown.FIRST,
                    9,
                ),
            ],
            [
                "There were 12 cards in a box. Maria put in 5 more, and then Jamal took out 8. "
                "How many cards are in the box now?"
            ],
        ),
        # the first step's answer is the size of each of {c} groups
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (2, 4), 6),
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 6), 18),
                    ),
                    Unknown.SECOND,
                    18,
                ),
            ],
            [
                "Each of 3 bags has 2 cards from Maria and 4 from Jamal. "
                "How many cards are in the bags altogether?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (20, 4), 24),
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 3), 8),
                    ),
                    Unknown.FIRST,
                    8,
                ),
            ],
            [
                "Maria collected 20 cards and Jamal collected 4 cards. They put them all into 3 "
                "equal piles. How many cards are in each pile?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (12, 5), 7),
                        BasicOperationQuestionData(Operation.ADD, (7, 8), 15),
                    ),
                    Unknown.FIRST,
                    15,
                ),
            ],
            [
                "There were 12 cards on the shelf. 5 were sold, and then 8 more were put out. "
                "How many cards are on the shelf now?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (9, 4), 5),
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
                    ),
                    Unknown.SECOND,
                    15,
                ),
            ],
            [
                "There are 3 boxes with 9 cards in each box. Maria takes 4 out of every box. "
                "How many cards are left in the boxes?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (2, 4), 8),
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 8), 24),
                    ),
                    Unknown.SECOND,
                    24,
                ),
            ],
            [
                "Maria buys 3 cartons. Each carton has 2 packs with 4 cards in each pack. "
                "How many cards did Maria buy?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (4, 6), 24),
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 3), 8),
                    ),
                    Unknown.FIRST,
                    8,
                ),
            ],
            [
                "There are 4 bags with 6 cards in each bag. The cards are put into 3 equal piles. "
                "How many cards are in each pile?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 4), 6),
                        BasicOperationQuestionData(Operation.ADD, (6, 3), 9),
                    ),
                    Unknown.FIRST,
                    9,
                ),
            ],
            [
                "24 cards are put into 4 equal piles. Maria adds 3 more to one pile. "
                "How many cards are in that pile now?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 4), 6),
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                    ),
                    Unknown.FIRST,
                    4,
                ),
            ],
            [
                "24 cards are put into 4 equal boxes. Maria takes 2 out of one box. "
                "How many cards are left in that box?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4),
                        BasicOperationQuestionData(Operation.MULTIPLY, (5, 4), 20),
                    ),
                    Unknown.SECOND,
                    20,
                ),
            ],
            [
                "12 cards fill 3 boxes, with the same number in each box. "
                "How many cards would fill 5 boxes?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (60, 2), 30),
                        BasicOperationQuestionData(Operation.DIVIDE, (30, 3), 10),
                    ),
                    Unknown.FIRST,
                    10,
                ),
            ],
            [
                "Maria puts 60 cards into 2 equal boxes, then splits each box's cards equally "
                "into 3 bags. How many cards are in each bag?"
            ],
        ),
        # 1 takes the singular in these shapes too
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (1, 5), 6),
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                    ),
                    Unknown.FIRST,
                    4,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (12, 5), 7),
                        BasicOperationQuestionData(Operation.ADD, (7, 1), 8),
                    ),
                    Unknown.FIRST,
                    8,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (20, 1), 21),
                        BasicOperationQuestionData(Operation.DIVIDE, (21, 3), 7),
                    ),
                    Unknown.FIRST,
                    7,
                ),
            ],
            [
                "There was 1 card in a box. Maria put in 5 more, and then Jamal took out 2. "
                "How many cards are in the box now?",
                "There were 12 cards on the shelf. 5 were sold, and then 1 more was put out. "
                "How many cards are on the shelf now?",
                "Maria collected 20 cards and Jamal collected 1 card. They put them all into 3 "
                "equal piles. How many cards are in each pile?",
            ],
        ),
        # the first step's answer is the number of groups
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (2, 3), 5),
                        BasicOperationQuestionData(Operation.MULTIPLY, (5, 4), 20),
                    ),
                    Unknown.FIRST,
                    20,
                ),
            ],
            [
                "A shop put out 2 boxes of cards in the morning and 3 more boxes in the "
                "afternoon. Each box holds 4 cards. How many cards did the shop put out?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (2, 3), 5),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 5), 4),
                    ),
                    Unknown.SECOND,
                    4,
                ),
            ],
            [
                "20 cards are put into 2 red boxes and 3 blue boxes, with the same number in "
                "each box. How many cards are in each box?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                        BasicOperationQuestionData(Operation.MULTIPLY, (4, 5), 20),
                    ),
                    Unknown.FIRST,
                    20,
                ),
            ],
            [
                "Maria filled 6 bags with 5 cards each, then gave away 2 of the bags. "
                "How many cards are in the bags Maria kept?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                    ),
                    Unknown.SECOND,
                    5,
                ),
            ],
            [
                "Maria had 6 boxes and gave away 2 of them. Maria puts 20 cards equally into the "
                "boxes that are left. How many cards are in each box?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                        BasicOperationQuestionData(Operation.MULTIPLY, (6, 4), 24),
                    ),
                    Unknown.FIRST,
                    24,
                ),
            ],
            [
                "Maria stacks 2 rows of boxes with 3 boxes in each row. Each box has 4 cards in "
                "it. How many cards are in the boxes?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
                        BasicOperationQuestionData(Operation.DIVIDE, (24, 6), 4),
                    ),
                    Unknown.SECOND,
                    4,
                ),
            ],
            [
                "Maria has 2 bags with 3 pockets in each bag, and puts 24 cards equally into all "
                "the pockets. How many cards are in each pocket?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (8, 2), 4),
                        BasicOperationQuestionData(Operation.MULTIPLY, (4, 5), 20),
                    ),
                    Unknown.FIRST,
                    20,
                ),
            ],
            [
                "Maria sorts 8 bags equally onto 2 shelves. Each bag has 5 cards in it. "
                "How many cards are on each shelf?"
            ],
        ),
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                    ),
                    Unknown.SECOND,
                    5,
                ),
            ],
            [
                "Maria puts 12 boxes equally onto 3 shelves, and then shares 20 cards equally "
                "among the boxes on one shelf. How many cards are in each of those boxes?"
            ],
        ),
        # 1 takes the singular here too, in each shape's templates from the last
        (
            [
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                        BasicOperationQuestionData(Operation.MULTIPLY, (4, 5), 20),
                    ),
                    Unknown.FIRST,
                    20,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (3, 1), 4),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                    ),
                    Unknown.SECOND,
                    5,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 2), 4),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 4), 5),
                    ),
                    Unknown.SECOND,
                    5,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.SUBTRACT, (6, 1), 5),
                        BasicOperationQuestionData(Operation.DIVIDE, (20, 5), 4),
                    ),
                    Unknown.SECOND,
                    4,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (1, 2), 3),
                        BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
                    ),
                    Unknown.FIRST,
                    12,
                ),
                TwoStepQuestionData(
                    (
                        BasicOperationQuestionData(Operation.ADD, (1, 3), 4),
                        BasicOperationQuestionData(Operation.DIVIDE, (12, 4), 3),
                    ),
                    Unknown.SECOND,
                    3,
                ),
            ],
            [
                "A shop put out 1 box of cards in the morning and 3 more boxes in the afternoon. "
                "Each box holds 5 cards. How many cards did the shop put out?",
                "20 cards are put into 3 red boxes and 1 blue box, with the same number in each "
                "box. How many cards are in each box?",
                "Maria had 6 boxes and gave away 2 of them. Maria puts 20 cards equally into the "
                "boxes that are left. How many cards are in each box?",
                "Maria has 20 cards to share equally among 6 friends, but 1 of them goes home. "
                "How many cards does each friend who stayed get?",
                "Maria has 1 red bag and 2 blue bags, with 4 cards in each bag. "
                "How many cards does Maria have in all?",
                "Maria shares 12 cards equally among 1 boy and 3 girls. "
                "How many cards does each child get?",
            ],
        ),
    ],
)
def test_two_step_texts(
    questions: list[TwoStepQuestionData], expected: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    assert two_step_texts(questions) == expected


@pytest.mark.parametrize(
    ("make", "questions", "expected"),
    [
        (
            word_problem_texts,
            [ADD] * 3,
            ["Second: 47 and 25.", "First: 47 and 25.", "Second: 47 and 25."],
        ),
        (
            two_step_texts,
            [SUBTRACT_DIVIDE] * 3,
            ["Second: 24, 6 and 3.", "First: 24, 6 and 3.", "Second: 24, 6 and 3."],
        ),
    ],
)
def test_no_template_repeats_until_all_are_used(
    make: Callable[[list[Any]], list[str]],
    questions: list[Any],
    expected: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Two stand-in templates, so that a story added to the bank changes nothing here: the second
    is used, then the first, and with both used, the second again.
    """
    monkeypatch.setitem(TEMPLATES, Operation.ADD, ("First: {a} and {b}.", "Second: {a} and {b}."))
    monkeypatch.setitem(
        TWO_STEP_TEMPLATES,
        (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST),
        ("First: {a}, {b} and {c}.", "Second: {a}, {b} and {c}."),
    )
    sample_first(monkeypatch)
    choose_last(monkeypatch)

    assert make(questions) == expected


@pytest.mark.parametrize(
    ("templates", "numbers", "allowed"),
    [
        pytest.param(TEMPLATES[Operation.ADD], {"a", "b"}, ONE_STEP_SLOTS, id="add"),
        pytest.param(TEMPLATES[Operation.SUBTRACT], {"a", "b"}, ONE_STEP_SLOTS, id="subtract"),
        pytest.param(TEMPLATES[Operation.MULTIPLY], {"a", "b"}, ONE_STEP_SLOTS, id="multiply"),
        pytest.param(TEMPLATES[Operation.DIVIDE], {"a", "b"}, ONE_STEP_SLOTS, id="divide"),
        pytest.param(
            COMPARISON_TEMPLATES[Operation.SUBTRACT],
            {"a", "b"},
            ONE_STEP_SLOTS,
            id="subtract comparisons",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.ADD, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then add",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then subtract",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then divide",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.ADD, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then add",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then subtract from",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.SUBTRACT, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then subtract",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.MULTIPLY, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then groups of",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.DIVIDE, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then divide",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.ADD, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then add",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.MULTIPLY, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then groups of",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.MULTIPLY, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then groups of",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.DIVIDE, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then divide",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.ADD, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then add",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.SUBTRACT, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then subtract",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.MULTIPLY, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then groups of",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.DIVIDE, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then divide",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.MULTIPLY, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then that many groups",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.ADD, Operation.DIVIDE, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="add then share into that many",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.MULTIPLY, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then that many groups",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.SUBTRACT, Operation.DIVIDE, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="subtract then share into that many",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.MULTIPLY, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then that many groups",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.MULTIPLY, Operation.DIVIDE, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="multiply then share into that many",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.MULTIPLY, Unknown.FIRST],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then that many groups",
        ),
        pytest.param(
            TWO_STEP_TEMPLATES[Operation.DIVIDE, Operation.DIVIDE, Unknown.SECOND],
            {"a", "b", "c"},
            TWO_STEP_SLOTS,
            id="divide then share into that many",
        ),
    ],
)
def test_every_template_shows_its_numbers_and_uses_only_the_shared_slots(
    templates: tuple[str, ...], numbers: set[str], allowed: set[str]
) -> None:
    """
    Each template uses every one of its numbers' slots, {a} and {b}, and for two steps {c}, and
    no slot outside the shared ones.
    """
    for template in templates:
        slots = {field for _, field, _, _ in Formatter().parse(template) if field}
        assert numbers <= slots <= allowed, template
