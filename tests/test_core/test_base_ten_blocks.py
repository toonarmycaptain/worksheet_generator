"""
Tests for base-ten blocks sheets: each question's wording and blocks, how many questions the
limits allow, and generating a sheet.

The generator tests script ``random``: ``randint`` returns the numbers listed, each within its
draw's bounds, ``sample`` gives any extra questions to the last types, and ``shuffle`` reverses.
"""

import pytest

from core.base_ten_blocks import (
    BlocksQuestionData,
    BlocksQuestionType,
    blocks_answer_label,
    blocks_prompt,
    blocks_question_diagram,
    blocks_solution,
    blocks_tile_question,
    count_possible_blocks_questions,
    generate_blocks_questions,
)
from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.regrouping import Regrouping
from core.basic_operations.representation import BlocksDiagram
from core.placevalue.data import PlaceValueQuestionData
from core.placevalue.representation import BaseTenBlocks
from core.self_check_tiles import TileQuestion
from tests.data import BLOCKS, STANDARD
from tests.helpers import randint_returns, reverse_shuffle, sample_last

WRITE_NUMBER, ADD, SUBTRACT = BlocksQuestionType  # in the enum's order
NEVER, MIXED, ALWAYS = Regrouping  # in the enum's order


@pytest.mark.parametrize(
    ("data", "prompt", "diagram", "answer_label", "solution", "tile_answer"),
    [
        # a number to write, by itself
        (
            PlaceValueQuestionData(347, BLOCKS, STANDARD),
            "Write the number shown by the blocks.",
            BlocksDiagram((BaseTenBlocks(3, 4, 7),), None),
            "=",
            "347",
            "347",
        ),
        # both numbers of a sum, to combine
        (
            BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
            "Combine the blocks. Regroup if you can, then write the sum.",
            BlocksDiagram((BaseTenBlocks(2, 4, 7), BaseTenBlocks(3, 1, 8)), None),
            "Sum =",
            "247 + 318 = 565",
            "565",
        ),
        # the first number of a difference, with the second to cross out, which its label says
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
            "Cross out blocks to subtract. Break a hundred or ten if needed; write the difference.",
            BlocksDiagram((BaseTenBlocks(5, 7, 2),), 145),
            "572 \N{MINUS SIGN} 145 =",
            "572 \N{MINUS SIGN} 145 = 427",
            "427",
        ),
    ],
)
def test_each_question_s_wording_and_blocks(
    data: BlocksQuestionData,
    prompt: str,
    diagram: BlocksDiagram,
    answer_label: str,
    solution: str,
    tile_answer: str,
) -> None:
    """
    Each type of question has the legacy sheet's prompt, its blocks, the label before its answer
    box and its line in the answer key. Its tile question has the prompt, the answer and the
    line in the key.
    """
    assert (
        blocks_prompt(data),
        blocks_question_diagram(data),
        blocks_answer_label(data),
        blocks_solution(data),
    ) == (prompt, diagram, answer_label, solution)
    assert blocks_tile_question(data) == TileQuestion(prompt, tile_answer, solution)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
            "Base-ten blocks show only addition and subtraction.",
        ),
        (
            BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4),
            "Base-ten blocks show only addition and subtraction.",
        ),
    ],
)
def test_blocks_prompt_errors(data: BlocksQuestionData, message: str) -> None:
    """Multiplication and division raise ``ValueError`` rather than getting a prompt."""
    with pytest.raises(ValueError) as error:
        blocks_prompt(data)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("types", "smallest", "largest", "regrouping", "distinct_answers", "up_to", "expected"),
    [
        # Write the number: every number from the smallest to 599, the most drawn as blocks
        ([WRITE_NUMBER], 100, 999, MIXED, False, 20, 20),
        ([WRITE_NUMBER], 200, 210, MIXED, False, 20, 11),
        ([WRITE_NUMBER], 100, 150, MIXED, True, 60, 51),  # each number is its own answer
        ([WRITE_NUMBER], 590, 999, MIXED, False, 20, 10),  # 590 to 599
        # 1 + 1, 1 + 2, 1 + 3, 2 + 1, 2 + 2 and 3 + 1, with the sums 2, 3 and 4
        ([ADD], 1, 4, MIXED, False, 20, 6),
        ([ADD], 1, 4, MIXED, True, 20, 3),
        # 2 - 1, 3 - 1, 3 - 2, 4 - 1, 4 - 2 and 4 - 3, with the differences 1, 2 and 3
        ([SUBTRACT], 1, 4, MIXED, False, 20, 6),
        ([SUBTRACT], 1, 4, MIXED, True, 20, 3),
        # up to 10, a sum regroups only when it is 10: 1 + 9 to 9 + 1
        ([ADD], 1, 10, ALWAYS, False, 20, 9),
        ([ADD], 1, 10, ALWAYS, True, 20, 1),
        # the other 36 of the 45 sums up to 10, with the answers 2 to 9
        ([ADD], 1, 10, NEVER, False, 50, 36),
        ([ADD], 1, 10, NEVER, True, 20, 8),
        # up to 10, a difference regroups only when it starts at 10: 10 - 1 to 10 - 9
        ([SUBTRACT], 1, 10, ALWAYS, False, 20, 9),
        ([SUBTRACT], 1, 10, ALWAYS, True, 20, 9),
        # the other 36 of the 45 differences, with the answers 1 to 8
        ([SUBTRACT], 1, 10, NEVER, False, 50, 36),
        ([SUBTRACT], 1, 10, NEVER, True, 20, 8),
        # Every number is at least the smallest, the answer too: a difference of at least 298
        # starts at 596 or more, and stops at 599. 596 - 298, 597 - 298 or 299, and so on.
        ([SUBTRACT], 298, 999, MIXED, False, 20, 10),
        ([SUBTRACT], 298, 999, MIXED, True, 20, 4),  # 298 to 301
        # none at all
        ([], 100, 999, MIXED, False, 20, 0),  # no types of question
        ([ADD], 500, 999, MIXED, False, 20, 0),  # 500 + 500 is past 999
        ([SUBTRACT], 300, 999, MIXED, False, 20, 0),  # 600 - 300 starts past 599
        ([ADD], 1, 9, ALWAYS, False, 20, 0),  # nothing under 10 carries
        # Shared evenly: 4 numbers to write allow 8 questions, 4 of each. 3 of each type allow
        # 9, but a tenth would give one of them a fourth.
        ([WRITE_NUMBER, ADD], 1, 4, MIXED, False, 20, 8),
        ([WRITE_NUMBER, ADD, SUBTRACT], 1, 3, MIXED, False, 20, 9),
        # 12 questions take only 4 of the 10 numbers from 1 to 10
        ([WRITE_NUMBER, ADD, SUBTRACT], 1, 10, MIXED, False, 12, 12),
        # With distinct answers, the type with the fewest is made first. The 3 sums 2 to 4,
        # then the 4 numbers to write: 2 of each, but not 5 questions, which the 4 numbers to
        # write might have to cover.
        ([WRITE_NUMBER, ADD], 1, 4, MIXED, True, 20, 4),
        # the one sum that regroups, 10, then any of the 9 differences
        ([ADD, SUBTRACT], 1, 10, ALWAYS, True, 20, 2),
        # 9 sums, 9 differences, then 10 numbers to write: 3, 3 and 4
        ([WRITE_NUMBER, ADD, SUBTRACT], 1, 10, MIXED, True, 20, 10),
        # capped
        ([WRITE_NUMBER, ADD, SUBTRACT], 100, 999, MIXED, True, 12, 12),
    ],
)
def test_count_possible_blocks_questions(
    types: list[BlocksQuestionType],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
    distinct_answers: bool,
    up_to: int,
    expected: int,
) -> None:
    """
    The questions are shared evenly, so each type needs enough distinct questions for the larger
    share. With distinct answers, each type, from the one with the fewest answers, needs enough
    for its share and the shares before it, with the extra questions dealt first.
    """
    possible = count_possible_blocks_questions(
        types,
        smallest=smallest,
        largest=largest,
        regrouping=regrouping,
        distinct_answers=distinct_answers,
        up_to=up_to,
    )
    assert possible == expected


@pytest.mark.parametrize(
    (
        "count",
        "types",
        "smallest",
        "largest",
        "regrouping",
        "distinct_answers",
        "drawn",
        "bounds",
        "expected",
    ),
    [
        # The defaults: two of each, numbers from 100 to 599, the most drawn as blocks. A
        # subtraction starts at 200 or more, and takes away 100 to 499, to leave at least 100.
        (
            6,
            [WRITE_NUMBER, ADD, SUBTRACT],
            100,
            999,
            MIXED,
            False,
            [347, 102, 247, 318, 150, 420, 572, 145, 300, 150],
            [
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (200, 599),
                (100, 499),
                (200, 599),
                (100, 499),
            ],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (300, 150), 150),
                BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
                BasicOperationQuestionData(Operation.ADD, (150, 420), 570),
                BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                PlaceValueQuestionData(102, BLOCKS, STANDARD),
                PlaceValueQuestionData(347, BLOCKS, STANDARD),
            ],
        ),
        # 4 among 3 types: the extra question goes to the one sample picks
        (
            4,
            [WRITE_NUMBER, ADD, SUBTRACT],
            100,
            999,
            MIXED,
            False,
            [347, 247, 318, 572, 145, 300, 150],
            [(100, 599), (100, 599), (100, 599), (200, 599), (100, 499), (200, 599), (100, 499)],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (300, 150), 150),
                BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
                BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                PlaceValueQuestionData(347, BLOCKS, STANDARD),
            ],
        ),
        # a sum past the largest number is redrawn, and so is a difference under the smallest
        (
            2,
            [ADD, SUBTRACT],
            100,
            999,
            MIXED,
            False,
            [599, 500, 247, 318, 250, 200, 572, 145],
            [
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (200, 599),
                (100, 499),
                (200, 599),
                (100, 499),
            ],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (572, 145), 427),
                BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
            ],
        ),
        # always: 120 + 130 and 450 - 120 don't regroup, so they're redrawn
        (
            2,
            [ADD, SUBTRACT],
            100,
            999,
            ALWAYS,
            False,
            [120, 130, 125, 136, 450, 120, 452, 138],
            [
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (200, 599),
                (100, 499),
                (200, 599),
                (100, 499),
            ],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (452, 138), 314),
                BasicOperationQuestionData(Operation.ADD, (125, 136), 261),
            ],
        ),
        # never: 125 + 136 and 452 - 138 regroup, so they're redrawn
        (
            2,
            [ADD, SUBTRACT],
            100,
            999,
            NEVER,
            False,
            [125, 136, 120, 130, 452, 138, 450, 120],
            [
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (200, 599),
                (100, 499),
                (200, 599),
                (100, 499),
            ],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (450, 120), 330),
                BasicOperationQuestionData(Operation.ADD, (120, 130), 250),
            ],
        ),
        # no question repeats: the second 347 and the second 247 + 318 are redrawn
        (
            4,
            [WRITE_NUMBER, ADD],
            100,
            999,
            MIXED,
            False,
            [347, 347, 102, 247, 318, 247, 318, 150, 420],
            [
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
                (100, 599),
            ],
            [
                BasicOperationQuestionData(Operation.ADD, (150, 420), 570),
                BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                PlaceValueQuestionData(102, BLOCKS, STANDARD),
                PlaceValueQuestionData(347, BLOCKS, STANDARD),
            ],
        ),
        # with distinct answers, 100 + 150 is redrawn: 250 is the number to write
        (
            2,
            [WRITE_NUMBER, ADD],
            100,
            999,
            MIXED,
            True,
            [250, 100, 150, 247, 318],
            [(100, 599), (100, 599), (100, 599), (100, 599), (100, 599)],
            [
                BasicOperationQuestionData(Operation.ADD, (247, 318), 565),
                PlaceValueQuestionData(250, BLOCKS, STANDARD),
            ],
        ),
        # The limits reach every draw. With 1 to 50, an operand of a sum is at most 49, a
        # difference starts at 2 or more and takes away at most 49.
        (
            3,
            [WRITE_NUMBER, ADD, SUBTRACT],
            1,
            50,
            MIXED,
            False,
            [7, 23, 5, 31, 9],
            [(1, 50), (1, 49), (1, 49), (2, 50), (1, 49)],
            [
                BasicOperationQuestionData(Operation.SUBTRACT, (31, 9), 22),
                BasicOperationQuestionData(Operation.ADD, (23, 5), 28),
                PlaceValueQuestionData(7, BLOCKS, STANDARD),
            ],
        ),
    ],
)
def test_blocks_questions_from_scripted_draws(
    count: int,
    types: list[BlocksQuestionType],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
    distinct_answers: bool,
    drawn: list[int],
    bounds: list[tuple[int, int]],
    expected: list[BlocksQuestionData],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The questions are shared evenly among the types, and each one's numbers are drawn, and
    redrawn until they meet the limits and the regrouping and repeat no question.

    Every scripted draw must be made, within ``bounds``. The questions come out reversed, as
    ``shuffle`` reverses them, and are free response, with no wrong answers.
    """
    drawn_from = randint_returns(monkeypatch, drawn)
    sample_last(monkeypatch)
    reverse_shuffle(monkeypatch)

    questions = generate_blocks_questions(
        count,
        types,
        smallest=smallest,
        largest=largest,
        regrouping=regrouping,
        distinct_answers=distinct_answers,
    )

    assert drawn_from == bounds
    assert [(question.data, question.wrong_answers) for question in questions] == [
        (data, ()) for data in expected
    ]


@pytest.mark.parametrize(
    ("count", "types", "smallest", "largest", "regrouping"),
    [
        # the most the defaults allow, 20
        (20, [WRITE_NUMBER, ADD, SUBTRACT], 100, 999, MIXED),
        (12, [WRITE_NUMBER, ADD, SUBTRACT], 100, 999, ALWAYS),
        (12, [WRITE_NUMBER, ADD, SUBTRACT], 100, 999, NEVER),
        # every answer used, so the last questions are found by redrawing
        (11, [WRITE_NUMBER], 200, 210, MIXED),
        (4, [SUBTRACT], 298, 999, MIXED),
        # the 8 sums 2 to 9 and the 8 differences 1 to 8 share their answers
        (8, [ADD, SUBTRACT], 1, 10, NEVER),
        # every answer from 1 to 10
        (10, [WRITE_NUMBER, ADD, SUBTRACT], 1, 10, MIXED),
    ],
)
def test_random_blocks_questions_have_distinct_answers(
    count: int,
    types: list[BlocksQuestionType],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
) -> None:
    """A sheet of the most questions the limits allow is produced with no answer repeated."""
    questions = generate_blocks_questions(
        count,
        types,
        smallest=smallest,
        largest=largest,
        regrouping=regrouping,
        distinct_answers=True,
    )
    assert len({question.data.answer for question in questions}) == count


@pytest.mark.parametrize(
    ("count", "types", "smallest", "largest", "regrouping", "distinct_answers", "message"),
    [
        (1, [], 100, 999, MIXED, False, "A sheet needs at least one type of question."),
        (
            12,
            [WRITE_NUMBER],
            200,
            210,
            MIXED,
            False,
            "Cannot make 12 different questions: only 11 possible.",
        ),
        (
            2,
            [ADD],
            1,
            10,
            ALWAYS,
            True,
            "Cannot make 2 questions with different answers: only 1 possible.",
        ),
        (
            2,
            [WRITE_NUMBER, ADD],
            500,
            999,
            MIXED,
            False,
            "Cannot make 2 different questions: only 0 possible.",
        ),
    ],
)
def test_blocks_sheet_errors(
    count: int,
    types: list[BlocksQuestionType],
    smallest: int,
    largest: int,
    regrouping: Regrouping,
    distinct_answers: bool,
    message: str,
) -> None:
    """
    A sheet with no types of question, or more questions than the limits allow, raises
    ``ValueError`` saying why.

    Without that check, generation would loop forever looking for a question or an answer that
    does not exist.
    """
    with pytest.raises(ValueError) as error:
        generate_blocks_questions(
            count,
            types,
            smallest=smallest,
            largest=largest,
            regrouping=regrouping,
            distinct_answers=distinct_answers,
        )
    assert str(error.value) == message
