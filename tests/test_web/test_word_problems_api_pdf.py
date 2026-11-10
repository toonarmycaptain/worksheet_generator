"""
Tests for the word problems endpoint: its options reach the core and the renderer intact.

The tests script ``random``. ``choices`` returns the operations, or two-step shapes, listed as
picks, ``randint`` the operands listed, and ``shuffle`` reverses, so the complex tile pattern runs
from L to A, and an equation multiple choice sheet, whose operations are split evenly instead,
comes in the reverse of the ticked order. ``choice`` returns the draws listed as chosen: for each
two-step problem, the number its first step carries, then each step, and then each problem's
object. The wording takes the first two names and each operation's or shape's last template.
``conventional_slot_of`` gives the slots of a real case. The PDF must then match what the
renderer draws for the same questions. Disallowed options get Ninja's JSON error. The renderer's
output is tested in ``test_word_problems_worksheet``.
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
from core.basic_operations.representation import Representation
from tests.data import REAL_CASE_SLOTS
from tests.helpers import (
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
        # two steps only with strip diagrams or text only, and every shape adds or subtracts
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
            "/api/worksheets/word_problems.pdf?representation=equation_choice&steps=two",
            [],
            [],
            [],
            422,
            refused("steps: two steps not available with Equation multiple choice"),
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
            # with tiles, three different numbers within 10 make only the answers 6 to 10
            "/api/worksheets/word_problems.pdf?representation=none&steps=two&operations=add"
            "&max_number=10&self_check_tiles=true&problems=12",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 5 without repeated answers for that largest number. Lower "
                "problems to 5, or raise the largest number to 17."
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
            # is worded with its comparison. The hints are on, but it has none.
            "/api/worksheets/word_problems.pdf?representation=equation_choice&problems=2"
            "&answer_key=true&sheet=1ab2c3",
            [],
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
                "representation": Representation.EQUATION_CHOICE,
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
            # All four ticked, one of each: 4 shared into 2 is redrawn, as 4 - 2 is 2 too, and the
            # largest number caps the subtraction and addition, but not 6 groups of 20.
            "/api/worksheets/word_problems.pdf?representation=equation_choice&operations=add"
            "&operations=subtract&operations=multiply&operations=divide&problems=4"
            "&max_number=100&sheet=1ab2c3",
            [],
            [2, 2, 3, 4, 6, 20, 40, 90, 47, 25],
            [("card", "cards"), ("card", "cards"), ("card", "cards"), ("card", "cards")],
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
                "representation": Representation.EQUATION_CHOICE,
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
        # equation multiple choice has no tiles
        (
            "/api/worksheets/word_problems.pdf?representation=equation_choice"
            "&self_check_tiles=true",
            [],
            [],
            [],
            422,
            refused("self_check_tiles: not available with Equation multiple choice"),
            None,
            None,
        ),
        (
            # Split evenly, addition needs 3 of 6 problems, and a largest number of 3 allows 2
            # sums. Text only would allow 2 problems in all.
            "/api/worksheets/word_problems.pdf?representation=equation_choice&operations=add"
            "&operations=multiply&problems=6&max_number=3",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 4 without repeats for that choice of operations and largest "
                "number. Lower problems to 4, or raise the largest number to 4."
            ),
            None,
            None,
        ),
        (
            # a largest number of 99 caps the sum too, so 60 + 50 is redrawn
            "/api/worksheets/word_problems.pdf?representation=strip&operations=add&problems=1"
            "&max_number=99&sheet=1ab2c3",
            [Operation.ADD],
            [60, 50, 47, 25],
            [("card", "cards")],
            200,
            None,
            {
                "questions": [ADD],
                "representation": Representation.STRIP,
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
            # with multiplication too, raising the largest number helps only the addition
            "/api/worksheets/word_problems.pdf?operations=add&operations=multiply&problems=4"
            "&max_number=3",
            [],
            [],
            [],
            422,
            refused(
                "problems: at most 2 without repeats for that choice of operations and largest "
                "number. Lower problems to 2, or raise the largest number to 5."
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
