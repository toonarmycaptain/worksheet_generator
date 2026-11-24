"""
Tests for the word problems PDF endpoint.

A valid request must return a PDF with the expected filename and cache header, and its
``pdf_text`` must equal that of the PDF the renderer makes from the questions listed in the
test case. With ``random`` scripted, an option that the endpoint drops or passes on incorrectly
changes the generated questions and fails that comparison. An invalid request must return 422
with the Django Ninja validation error and no PDF headers. The renderer itself is tested in
``test_word_problems_worksheet``.

The PDF tests replace these functions:

- ``random.choices`` returns the operations or two-step shapes listed in the test case as
  ``picks``, and raises ``ValueError`` for picks that are not ``k`` items of its population.
- ``random.randint`` returns the operands listed in the test case, and raises ``ValueError`` for
  an operand outside the bounds of its call.
- ``random.shuffle`` reverses the list. The complex tile pattern therefore runs from L to A, and
  a multiple choice sheet, whose operations are split evenly rather than picked, lists them in
  the reverse of the ticked order.
- ``random.sample`` returns the first items, in order, so the wording uses the first two names
  and the templates of each operation or shape from last to first.
- ``random.choice`` returns the ``chosen`` values listed in the test case, and raises
  ``ValueError`` for a value its call did not offer. They are, for each two-step problem, the
  number its first step carries and then each step, followed by the object of each problem, and,
  for number lines to choose from, the side of the answer that each wrong landing tries first,
  or for two-step equations to choose from, ``LAST`` for each problem's pair of mistakes and its
  set of wrong equations; both for the request and again for the expected PDF.
- ``conventional_slot_of``, which gives the slots of the simple tile pattern, returns the slots
  of a real case.
"""

from typing import Any

import pytest
from django.test import Client

from core.basic_operations.data import (
    BasicOperationQuestionData,
    Operation,
    TwoStepQuestionData,
    TwoStepShape,
    Unknown,
)
from core.basic_operations.representation import Representation, Response
from tests.data import REAL_CASE_SLOTS
from tests.helpers import (
    LAST,
    choice_returns,
    choices_returns,
    conventional_slot_of_returns,
    pdf_text,
    randint_returns,
    refused,
    render_word_problems,
    reverse_shuffle,
    sample_first,
)

# drawn as 40 and 150, swapped so the larger is first
SUBTRACT = BasicOperationQuestionData(
    Operation.SUBTRACT,
    (150, 40),
    110,
    "Maria needs 150 cards in all and has 40 so far. How many more cards are needed?",
)
ADD = BasicOperationQuestionData(
    Operation.ADD,
    (47, 25),
    72,
    "A basket held 47 cards. Maria added 25 more. How many cards are in the basket now?",
)


@pytest.mark.parametrize(
    ("url", "picks", "drawn", "chosen", "status", "expected_json", "pdf_data", "filename"),
    [
        (
            # strip diagrams, with 2 problems: subtraction then addition, each with its hint
            "/api/worksheets/word_problems.pdf?representation=strip&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # addition only
            "/api/worksheets/word_problems.pdf?representation=strip&operations=add&problems=1"
            "&no_hints=true&answer_key=true&title=Story+Problems&label=Day+2&name_line=true"
            "&sheet=1ab2c3",
            [Operation.ADD],
            [47, 25],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [ADD],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": False,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Story Problems",
                "label": "Day 2",
                "name_line": True,
            },
            "word_problems-day-2.pdf",
        ),
        (
            # Tiles, with the simple pattern by default. Their answers must differ, so 55 + 55,
            # also 110, is redrawn.
            "/api/worksheets/word_problems.pdf?representation=strip&self_check_tiles=true"
            "&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 55, 55, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (7, 9),
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=strip&self_check_tiles=true"
            "&tile_pattern=complex&problems=2&answer_key=true&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (11, 10),
                "answer_key": True,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # Options that are not allowed are refused before anything is drawn, and before the
        # redirect, so these URLs have no token.
        (
            "/api/worksheets/word_problems.pdf?self_check_tiles=true&problems=13",
            [],
            [],
            [],
            422,
            refused("problems: self-check tiles has 12 tiles, so at most 12"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?problems=21",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "problems"],
                        "msg": "Input should be less than or equal to 20",
                        "ctx": {"le": 20},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # multiplication only: 3 groups of 4
            "/api/worksheets/word_problems.pdf?representation=strip&operations=multiply&problems=1"
            "&sheet=1ab2c3",
            [Operation.MULTIPLY],
            [3, 4],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (3, 4),
                        12,
                        "3 friends each have 4 cards. How many cards do they have together?",
                    ),
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # all four ticked: division, then addition with the one size, 2 and 2 digits
            "/api/worksheets/word_problems.pdf?representation=strip&operations=add"
            "&operations=subtract&operations=multiply&operations=divide&problems=2"
            "&answer_key=true&sheet=1ab2c3",
            [Operation.DIVIDE, Operation.ADD],
            [3, 4, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (12, 3),
                        4,
                        "Maria divides 12 cards into 3 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    ADD,
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # division with tiles: 3 groups of 4, then 5 groups of 6, with the last two templates
            "/api/worksheets/word_problems.pdf?representation=strip&operations=divide"
            "&self_check_tiles=true&problems=2&sheet=1ab2c3",
            [Operation.DIVIDE, Operation.DIVIDE],
            [3, 4, 5, 6],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (12, 3),
                        4,
                        "Maria divides 12 cards into 3 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (30, 5),
                        6,
                        "30 cards are placed in 5 equal rows. How many cards are in each row?",
                    ),
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (7, 9),
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # The defaults, with 2 problems: text only, with no working out space, and the title
            # "Word Problems", since none is given. The hints are on, but text only has none.
            # Subtraction is worded with its comparison, the last of its templates on a text-only
            # sheet.
            "/api/worksheets/word_problems.pdf?problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # text only with multiplication, and a title given, which is kept
            "/api/worksheets/word_problems.pdf?representation=none&operations=multiply&problems=1"
            "&title=Story+Problems&sheet=1ab2c3",
            [Operation.MULTIPLY],
            [3, 4],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (3, 4),
                        12,
                        "3 friends each have 4 cards. How many cards do they have together?",
                    ),
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Story Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # text only with working out space
            "/api/worksheets/word_problems.pdf?work_box=true&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": True,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # two steps with strip diagrams: the shapes listed as picks
            "/api/worksheets/word_problems.pdf?representation=strip&steps=two&operations=add"
            "&operations=subtract&problems=2&sheet=1ab2c3",
            [
                (Operation.ADD, Operation.ADD, Unknown.FIRST),
                (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST),
            ],
            [],
            [
                10,
                BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                ("card", "cards"),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                            BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
                        ),
                        Unknown.FIRST,
                        17,
                        "A jar held 4 cards. Maria added 6 more, and then Jamal added 7 more. "
                        "How many cards are in the jar now?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.FIRST,
                        12,
                        "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                        "How many cards are left in the box?",
                    ),
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # two steps, text only, with tiles and the answer key: a second answer of 6 is redrawn
            "/api/worksheets/word_problems.pdf?representation=none&steps=two&operations=subtract"
            "&operations=divide&self_check_tiles=true&problems=2&answer_key=true&sheet=1ab2c3",
            [
                (Operation.SUBTRACT, Operation.DIVIDE, Unknown.FIRST),
                (Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST),
            ],
            [],
            [
                18,
                BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 14), 6),
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                ("card", "cards"),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                            BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                        ),
                        Unknown.FIRST,
                        6,
                        "Maria has 24 cards. 6 are in a box, and the rest are in 3 bags with the "
                        "same number in each bag. How many cards are in each bag?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.FIRST,
                        12,
                        "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                        "How many cards are left in the box?",
                    ),
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (7, 9),
                "answer_key": True,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # two steps, text only, with working out space, and a largest number given
            "/api/worksheets/word_problems.pdf?representation=none&steps=two&operations=subtract"
            "&operations=multiply&max_number=50&work_box=true&problems=1&sheet=1ab2c3",
            [(Operation.MULTIPLY, Operation.SUBTRACT, Unknown.SECOND)],
            [],
            [
                48,
                BasicOperationQuestionData(Operation.MULTIPLY, (6, 8), 48),
                BasicOperationQuestionData(Operation.SUBTRACT, (50, 48), 2),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.MULTIPLY, (6, 8), 48),
                            BasicOperationQuestionData(Operation.SUBTRACT, (50, 48), 2),
                        ),
                        Unknown.SECOND,
                        2,
                        "A store had 50 cards. It sold 6 packs with 8 cards in each pack. "
                        "How many cards does the store have left?",
                    ),
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": True,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # two steps only with strip diagrams, text only or equations, and every strip shape adds
        # or subtracts
        (
            "/api/worksheets/word_problems.pdf?representation=number_line&steps=two",
            [],
            [],
            [],
            422,
            refused("steps: two steps not available with Number Lines"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=blocks&steps=two",
            [],
            [],
            [],
            422,
            refused("steps: two steps not available with Base-Ten Blocks"),
            None,
            None,
        ),
        (
            # equations show two steps: written, with an equation line under the problem
            "/api/worksheets/word_problems.pdf?representation=equation&steps=two&problems=1"
            "&sheet=1ab2c3",
            [(Operation.SUBTRACT, Operation.SUBTRACT, Unknown.FIRST)],
            [],
            [
                20,
                BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.FIRST,
                        12,
                        "A box held 25 cards. Maria took out 5, and then Jamal took out 8. "
                        "How many cards are left in the box?",
                    ),
                ],
                "representation": Representation.EQUATION,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # and to choose from, with the key: two problems split among the eight shapes of + and
            # -, so the last two, as ``sample`` keeps their order, then shuffled. Each has its
            # letter, c for cards, and its wrong equations use + and - only.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&steps=two&problems=2&answer_key=true&sheet=1ab2c3",
            [],
            [],
            [
                8,
                BasicOperationQuestionData(Operation.SUBTRACT, (9, 1), 8),
                BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                7,
                BasicOperationQuestionData(Operation.SUBTRACT, (9, 2), 7),
                BasicOperationQuestionData(Operation.ADD, (1, 7), 8),
                ("card", "cards"),
                ("card", "cards"),
                LAST,
                LAST,
                LAST,
                LAST,
                LAST,
                LAST,
                LAST,
                LAST,
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (9, 1), 8),
                            BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
                        ),
                        Unknown.SECOND,
                        12,
                        "A class wants to collect 20 cards. They collected 9, but 1 was lost. "
                        "How many more cards do they need?",
                    ),
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.SUBTRACT, (9, 2), 7),
                            BasicOperationQuestionData(Operation.ADD, (1, 7), 8),
                        ),
                        Unknown.SECOND,
                        8,
                        "There is 1 card in the red box. The blue box had 9 cards, and 2 were "
                        "taken out. How many cards are in the two boxes now?",
                    ),
                ],
                "representation": Representation.EQUATION,
                "choices": True,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Equation multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # Multiplication alone with 2 groups of up to 5: c x (a x b) needs two numbers of
            # groups, both 2, so only (2 x b) x c, with b and c two different numbers from 3 to 5,
            # 6. The largest number caps none of these numbers, so it isn't named.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&steps=two&operations=multiply&max_groups=2&max_group_size=5&problems=20",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 6 without repeats for that largest number of groups and largest "
                "group size. Lower problems to 6, or raise the largest number of groups to 4, or "
                "raise the largest group size to 7."
            ),
            None,
            None,
        ),
        (
            # Within 3 every addition adds 1, 2 and 3 in some order, 6 to a shape, each with fair
            # equations to choose from, and with 2 groups of 2 every multiplication repeats a
            # number, so only the two shapes of addition are drawn: 12, split evenly.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&steps=two&operations=add&operations=multiply&max_number=3&max_groups=2"
            "&max_group_size=2&problems=13",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 12 without repeats for that largest number, largest number of "
                "groups and largest group size. Lower problems to 12, or raise the largest number "
                "to 4, or raise the largest number of groups to 4, or raise the largest group size "
                "to 4."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=strip&steps=two&operations=multiply"
            "&operations=divide",
            [],
            [],
            [],
            422,
            refused("operations: two steps need addition or subtraction"),
            None,
            None,
        ),
        (
            # Text only shows every shape, so multiplication and division alone make two steps.
            # Dividing twice, its first answer, 30, goes past the largest group size, 20.
            "/api/worksheets/word_problems.pdf?representation=none&steps=two&operations=multiply"
            "&operations=divide&problems=1&answer_key=true&sheet=1ab2c3",
            [(Operation.DIVIDE, Operation.DIVIDE, Unknown.FIRST)],
            [],
            [
                30,
                BasicOperationQuestionData(Operation.DIVIDE, (60, 2), 30),
                BasicOperationQuestionData(Operation.DIVIDE, (30, 3), 10),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.DIVIDE, (60, 2), 30),
                            BasicOperationQuestionData(Operation.DIVIDE, (30, 3), 10),
                        ),
                        Unknown.FIRST,
                        10,
                        "Maria puts 60 cards into 2 equal boxes, then splits each box's cards "
                        "equally into 3 bags. How many cards are in each bag?",
                    ),
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # with tiles, three different numbers up to 6, the answer no longer capped, make only
            # the answers 6 to 15
            "/api/worksheets/word_problems.pdf?representation=none&steps=two&operations=add"
            "&max_number=6&self_check_tiles=true&problems=12",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 10 without repeated answers for that largest number. Lower "
                "problems to 10, or raise the largest number to 7."
            ),
            None,
            None,
        ),
        (
            # Number lines, with their title, since none is given. Subtraction is worded with its
            # comparison, the last of its templates on a number-line sheet.
            "/api/worksheets/word_problems.pdf?representation=number_line&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.NUMBER_LINE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Number Lines",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # number lines with tiles and the answer key
            "/api/worksheets/word_problems.pdf?representation=number_line&self_check_tiles=true"
            "&problems=2&answer_key=true&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.NUMBER_LINE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (7, 9),
                "answer_key": True,
                "title": "Word Problems — Number Lines",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # a number line shows only addition and subtraction
        (
            "/api/worksheets/word_problems.pdf?representation=number_line&operations=add"
            "&operations=multiply",
            [],
            [],
            [],
            422,
            refused("operations: Number Lines show only addition and subtraction"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=number_line&operations=divide",
            [],
            [],
            [],
            422,
            refused("operations: Number Lines show only addition and subtraction"),
            None,
            None,
        ),
        (
            # Base-ten blocks, with their title, since none is given. Subtraction has no
            # comparison on a blocks sheet, so it is worded with the last of its other templates.
            "/api/worksheets/word_problems.pdf?representation=blocks&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [SUBTRACT, ADD],
                "representation": Representation.BLOCKS,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Base-Ten Blocks",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # black and white blocks, without the hints or the note saying what to cross out
            "/api/worksheets/word_problems.pdf?representation=blocks&operations=subtract&problems=1"
            "&black_and_white=true&no_hints=true&sheet=1ab2c3",
            [Operation.SUBTRACT],
            [40, 150],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [SUBTRACT],
                "representation": Representation.BLOCKS,
                "choices": False,
                "hints": False,
                "black_and_white": True,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Base-Ten Blocks",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # base-ten blocks show only addition and subtraction
            "/api/worksheets/word_problems.pdf?representation=blocks&operations=multiply",
            [],
            [],
            [],
            422,
            refused("operations: Base-Ten Blocks show only addition and subtraction"),
            None,
            None,
        ),
        (
            # Equation multiple choice, with its title, since none is given. Addition and
            # subtraction are split evenly, one each, then the sheet is shuffled, and subtraction
            # is worded with its comparison. The hints are on, but it has none. Each problem's
            # wrong equations take the last pair of mistakes and its last set, for the request and
            # again for the expected PDF.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&problems=2&answer_key=true&sheet=1ab2c3",
            [],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards"), *[LAST] * 8],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.EQUATION,
                "choices": True,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Equation multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # All four ticked, one of each: 1 + 1 is redrawn, as it has no fair set of wrong
            # equations, and the largest number caps the subtraction and addition, but not 6
            # groups of 20.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&operations=add&operations=subtract&operations=multiply&operations=divide&problems=4"
            "&max_number=100&sheet=1ab2c3",
            [],
            [3, 4, 6, 20, 40, 90, 1, 1, 47, 25],
            [
                ("card", "cards"),
                ("card", "cards"),
                ("card", "cards"),
                ("card", "cards"),
                *[LAST] * 16,
            ],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (12, 3),
                        4,
                        "Maria divides 12 cards into 3 equal piles. "
                        "How many cards are in each pile?",
                    ),
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (6, 20),
                        120,
                        "6 friends each have 20 cards. How many cards do they have together?",
                    ),
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (90, 40),
                        50,
                        "Maria has 90 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.EQUATION,
                "choices": True,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Equation multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # multiple choice has no tiles
        (
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&self_check_tiles=true",
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            # Split evenly, addition needs 6 of 11 problems, and numbers up to 3 make 5 sums, 2 to
            # 6. Text only would allow 5 problems in all.
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&operations=add&operations=multiply&problems=11&max_number=3",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 10 without repeats for that largest number, largest number of "
                "groups and largest group size. Lower problems to 10, or raise the largest number "
                "to 4."
            ),
            None,
            None,
        ),
        (
            # Number line multiple choice, with its title, since none is given. Split evenly and
            # shuffled, as equation multiple choice is. The addition, drawn 25 and 47, puts its
            # larger number first. Subtraction is worded with its comparison. Its wrong landing
            # tries below the answer first, and the addition's above, for the request and again
            # for the expected PDF.
            "/api/worksheets/word_problems.pdf?representation=number_line"
            "&response=multiple_choice&problems=2&answer_key=true&sheet=1ab2c3",
            [],
            [40, 150, 25, 47],
            [("card", "cards"), ("card", "cards"), -1, 1, -1, 1],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.NUMBER_LINE,
                "choices": True,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Number Line multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=number_line"
            "&response=multiple_choice&self_check_tiles=true",
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        (
            # an addition's numbers differ, so a largest number of 3 allows only 2 + 1, 3 + 1 and
            # 3 + 2
            "/api/worksheets/word_problems.pdf?representation=number_line"
            "&response=multiple_choice&operations=add&problems=4&max_number=3",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 3 without repeats for that largest number. Lower problems to 3, "
                "or raise the largest number to 4."
            ),
            None,
            None,
        ),
        (
            # and 2 allows only 2 + 1
            "/api/worksheets/word_problems.pdf?representation=number_line"
            "&response=multiple_choice&operations=add&problems=2&max_number=2",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 1 without repeats for that largest number. Lower problems to 1, "
                "or raise the largest number to 3."
            ),
            None,
            None,
        ),
        # only number lines and equations are multiple choice
        (
            "/api/worksheets/word_problems.pdf?representation=strip&response=multiple_choice",
            [],
            [],
            [],
            422,
            refused("response: multiple choice not available with Strip Diagrams"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=none&response=multiple_choice",
            [],
            [],
            [],
            422,
            refused("response: multiple choice not available with Text Only"),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=blocks&response=multiple_choice",
            [],
            [],
            [],
            422,
            refused("response: multiple choice not available with Base-Ten Blocks"),
            None,
            None,
        ),
        (
            # Equations, written, by default: an operation drawn for each problem, as on text only,
            # and subtraction worded with its comparison. The hints are on, but it has none.
            "/api/worksheets/word_problems.pdf?representation=equation&problems=2&answer_key=true"
            "&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.EQUATION,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": True,
                "title": "Word Problems — Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # written equations work with tiles, whose answers must differ, so 55 + 55, also 110,
            # is redrawn
            "/api/worksheets/word_problems.pdf?representation=equation&self_check_tiles=true"
            "&problems=2&sheet=1ab2c3",
            [Operation.SUBTRACT, Operation.ADD],
            [40, 150, 55, 55, 47, 25],
            [("card", "cards"), ("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.SUBTRACT,
                        (150, 40),
                        110,
                        "Maria has 150 cards and Jamal has 40 cards. "
                        "How many more cards does Maria have than Jamal?",
                    ),
                    ADD,
                ],
                "representation": Representation.EQUATION,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": (7, 9),
                "answer_key": False,
                "title": "Word Problems — Equations",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # a largest number of 99 caps the numbers given, not the sum, so 60 + 50 = 110 stands
            "/api/worksheets/word_problems.pdf?representation=strip&operations=add&problems=1"
            "&max_number=99&sheet=1ab2c3",
            [Operation.ADD],
            [60, 50],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.ADD,
                        (60, 50),
                        110,
                        "A basket held 60 cards. Maria added 50 more. "
                        "How many cards are in the basket now?",
                    )
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # 12 tiles need 12 answers, and a largest number of 10 allows 9: 2 to 10 for
            # addition, and 1 to 9 for subtraction
            "/api/worksheets/word_problems.pdf?self_check_tiles=true&problems=12&max_number=10",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 9 without repeated answers for that largest number. "
                "Lower problems to 9, or raise the largest number to 13."
            ),
            None,
            None,
        ),
        (
            # with multiplication too, raising the largest number helps only the addition, whose
            # numbers up to 3 make 5 sums, 2 to 6
            "/api/worksheets/word_problems.pdf?operations=add&operations=multiply&problems=6"
            "&max_number=3",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 5 without repeats for that largest number, largest number of "
                "groups and largest group size. Lower problems to 5, or raise the largest number "
                "to 4."
            ),
            None,
            None,
        ),
        (
            # the largest number is for addition and subtraction: 120 shared into 6 goes past 2
            "/api/worksheets/word_problems.pdf?representation=strip&operations=divide&problems=1"
            "&max_number=2&sheet=1ab2c3",
            [Operation.DIVIDE],
            [6, 20],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (120, 6),
                        20,
                        "Maria divides 120 cards into 6 equal piles. "
                        "How many cards are in each pile?",
                    ),
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # the largest number is at least 1 + 1
            "/api/worksheets/word_problems.pdf?max_number=1",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be greater than or equal to 2",
                        "ctx": {"ge": 2},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?max_number=1000",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_number"],
                        "msg": "Input should be less than or equal to 999",
                        "ctx": {"le": 999},
                    },
                ],
            },
            None,
            None,
        ),
        (
            # Strip diagrams have room for 12 groups. The size of each has a field of its own, and
            # the total shared is whatever they make, past the largest number.
            "/api/worksheets/word_problems.pdf?representation=strip&operations=divide"
            "&max_groups=12&max_group_size=999&problems=1&sheet=1ab2c3",
            [Operation.DIVIDE],
            [12, 987],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.DIVIDE,
                        (11_844, 12),
                        987,
                        "Maria divides 11,844 cards into 12 equal piles. "
                        "How many cards are in each pile?",
                    ),
                ],
                "representation": Representation.STRIP,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Strip Diagrams",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # equations draw no strip, so they can have more groups
            "/api/worksheets/word_problems.pdf?representation=equation&response=multiple_choice"
            "&operations=multiply&max_groups=32&max_group_size=28&problems=1&sheet=1ab2c3",
            [],
            [32, 28],
            [("card", "cards"), *[LAST] * 4],
            200,
            None,
            {
                "questions": [
                    BasicOperationQuestionData(
                        Operation.MULTIPLY,
                        (32, 28),
                        896,
                        "32 friends each have 28 cards. How many cards do they have together?",
                    ),
                ],
                "representation": Representation.EQUATION,
                "choices": True,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems — Equation multiple choice",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            # two steps, text only: 12 groups of 25 needs both limits raised
            "/api/worksheets/word_problems.pdf?steps=two&operations=add&operations=multiply"
            "&max_groups=12&max_group_size=25&problems=1&sheet=1ab2c3",
            [(Operation.MULTIPLY, Operation.ADD, Unknown.FIRST)],
            [],
            [
                300,
                BasicOperationQuestionData(Operation.MULTIPLY, (12, 25), 300),
                BasicOperationQuestionData(Operation.ADD, (300, 5), 305),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [
                    TwoStepQuestionData(
                        (
                            BasicOperationQuestionData(Operation.MULTIPLY, (12, 25), 300),
                            BasicOperationQuestionData(Operation.ADD, (300, 5), 305),
                        ),
                        Unknown.FIRST,
                        305,
                        "There are 12 boxes with 25 cards in each box. Maria brings 5 more. "
                        "How many cards are there now?",
                    ),
                ],
                "representation": Representation.NONE,
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        (
            "/api/worksheets/word_problems.pdf?representation=strip&operations=multiply"
            "&max_groups=13",
            [],
            [],
            [],
            422,
            refused("max_groups: at most 12 with Strip Diagrams"),
            None,
            None,
        ),
        (
            # a division's answers are the sizes of each group, 2 to 10, so the size can be raised
            "/api/worksheets/word_problems.pdf?operations=divide&max_group_size=10"
            "&self_check_tiles=true&problems=12",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 9 without repeated answers for that largest number of groups "
                "and largest group size. Lower problems to 9, or raise the largest group size to "
                "13."
            ),
            None,
            None,
        ),
        (
            # 2 groups of 2 to 5: either limit can be raised
            "/api/worksheets/word_problems.pdf?operations=multiply&max_groups=2&max_group_size=5"
            "&problems=20",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 4 without repeats for that largest number of groups and "
                "largest group size. Lower problems to 4, or raise the largest number of groups "
                "to 6, or raise the largest group size to 21."
            ),
            None,
            None,
        ),
        (
            # With two steps the largest number caps a division's whole. Multiplying twice, which
            # within 3 groups of 4 needs 2 x 3 x 4 in some order, always makes 24, so with tiles
            # the sheet allows 1.
            "/api/worksheets/word_problems.pdf?operations=multiply&operations=divide&steps=two"
            "&max_groups=3&max_group_size=4&self_check_tiles=true&problems=12",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 1 without repeated answers for that largest number, largest "
                "number of groups and largest group size. Lower problems to 1, or raise the "
                "largest group size to 24."
            ),
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?max_groups=1",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_groups"],
                        "msg": "Input should be greater than or equal to 2",
                        "ctx": {"ge": 2},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?max_groups=100",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_groups"],
                        "msg": "Input should be less than or equal to 99",
                        "ctx": {"le": 99},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?max_group_size=1",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "greater_than_equal",
                        "loc": ["query", "max_group_size"],
                        "msg": "Input should be greater than or equal to 2",
                        "ctx": {"ge": 2},
                    },
                ],
            },
            None,
            None,
        ),
        (
            "/api/worksheets/word_problems.pdf?max_group_size=1000",
            [],
            [],
            [],
            422,
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["query", "max_group_size"],
                        "msg": "Input should be less than or equal to 999",
                        "ctx": {"le": 999},
                    },
                ],
            },
            None,
            None,
        ),
        # Mixed: one strip addition, as the only representation ticked shows it, worded once more
        # with the sheet, and titled "Word Problems". Each draw of the object is scripted.
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&representation_mix=strip"
            "&operations=add&problems=1&sheet=1ab2c3",
            [Operation.ADD],
            [47, 25],
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                ("card", "cards"),
                ("card", "cards"),
            ],
            200,
            None,
            {
                "questions": [ADD],
                "representation": [Representation.STRIP],
                "choices": False,
                "hints": True,
                "black_and_white": False,
                "work_box": False,
                "slot_of": None,
                "answer_key": False,
                "title": "Word Problems",
                "label": "Sheet A",
                "name_line": False,
            },
            "word_problems-sheet-a.pdf",
        ),
        # mixed refuses a representation that shows none of the operations, as the page greys
        # it out
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&representation_mix=blocks"
            "&representation_mix=strip&operations=multiply",
            [],
            [],
            [],
            422,
            refused("representation_mix: Base-Ten Blocks show only addition and subtraction"),
            None,
            None,
        ),
        # and an operation no representation ticked shows
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&representation_mix=number_line"
            "&representation_mix=blocks&operations=add&operations=multiply",
            [],
            [],
            [],
            422,
            refused("operations: no representation ticked shows multiplication"),
            None,
            None,
        ),
        # multiple choice alone needs every representation ticked to have choices
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&response=multiple_choice"
            "&representation_mix=strip&representation_mix=equation",
            [],
            [],
            [],
            422,
            refused("representation_mix: multiple choice not available with Strip Diagrams"),
            None,
            None,
        ),
        # mixed answering needs one of them to
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&response=mixed"
            "&representation_mix=strip&representation_mix=none",
            [],
            [],
            [],
            422,
            refused("response: multiple choice not available with Strip Diagrams and Text Only"),
            None,
            None,
        ),
        # two steps need every representation ticked to show them
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&steps=two"
            "&representation_mix=strip&representation_mix=number_line",
            [],
            [],
            [],
            422,
            refused("representation_mix: two steps not available with Number Lines"),
            None,
            None,
        ),
        # Mixed answering, two steps of addition alone: within 3 every problem adds 1, 2 and 3 in
        # some order, 6 to a shape, each with fair equations to choose from, so the half
        # answered by choosing allows as many as the written half.
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&response=mixed&steps=two"
            "&representation_mix=strip&representation_mix=none&representation_mix=equation"
            "&operations=add&max_number=3&problems=7",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 6 without repeats for that largest number. Lower problems to 6, "
                "or raise the largest number to 4."
            ),
            None,
            None,
        ),
        # no tiles with mixed answering, as with multiple choice
        (
            "/api/worksheets/word_problems.pdf?representation=equation&response=mixed"
            "&self_check_tiles=true&problems=12",
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with multiple choice"),
            None,
            None,
        ),
        # a strip among those mixed limits the groups to 12
        (
            "/api/worksheets/word_problems.pdf?representation=mixed&representation_mix=strip"
            "&representation_mix=none&operations=multiply&max_groups=13",
            [],
            [],
            [],
            422,
            refused("max_groups: at most 12 with Strip Diagrams"),
            None,
            None,
        ),
    ],
)
def test_word_problems_pdf(
    url: str,
    picks: list[Operation] | list[TwoStepShape],
    drawn: list[int],
    chosen: list[object],
    status: int,
    expected_json: dict[str, Any] | None,
    pdf_data: dict[str, Any] | None,
    filename: str | None,
    client: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A request receives the PDF for its options, or the error identifying the invalid option.

    - A rejected request is compared with Ninja's JSON error, and has no PDF headers.
    - A PDF is compared on its filename, its cache header and the text the renderer draws for
      ``pdf_data``.
    """
    choices_returns(monkeypatch, picks)
    randint_returns(monkeypatch, drawn)
    reverse_shuffle(monkeypatch)
    sample_first(monkeypatch)
    choice_returns(monkeypatch, chosen)
    conventional_slot_of_returns(monkeypatch, REAL_CASE_SLOTS)

    response = client.get(url)

    assert response.status_code == status
    assert response.get("Content-Disposition") == (
        f'inline; filename="{filename}"' if not expected_json else None
    )
    assert response.get("Cache-Control") == ("public, max-age=86400" if not expected_json else None)
    if expected_json:
        assert response.json() == expected_json
    else:
        assert pdf_text(response.content) == pdf_text(
            render_word_problems(
                questions=pdf_data["questions"],
                representation=pdf_data["representation"],
                choices=pdf_data["choices"],
                hints=pdf_data["hints"],
                black_and_white=pdf_data["black_and_white"],
                work_box=pdf_data["work_box"],
                slot_of=pdf_data["slot_of"],
                answer_key=pdf_data["answer_key"],
                title=pdf_data["title"],
                label=pdf_data["label"],
                name_line=pdf_data["name_line"],
            )
        )
