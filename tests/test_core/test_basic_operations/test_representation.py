"""The wording of basic-operation questions: a missing-number equation, how the self-check tiles
sheet shows a question, and a word problem's strip diagram, hint, instruction and sheet title."""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.basic_operations.representation import (
    EqualStripDiagram,
    Picture,
    StripDiagram,
    StripUnknown,
    basic_operation_tile_question,
    hint,
    instruction,
    missing_number_equation,
    missing_number_tile_question,
    operations_name,
    strip_diagram,
    word_problems_title,
)
from core.question import BLANK
from core.self_check_tiles import TileQuestion


@pytest.mark.parametrize(
    ("data", "missing", "expected"),
    [
        (
            MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
            BLANK,
            f"{BLANK} ÷ 4 = 7",
        ),
        (
            MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4),
            BLANK,
            f"28 ÷ {BLANK} = 7",
        ),
        # with the answer in its place: the whole equation
        (MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28), 28, "28 ÷ 4 = 7"),
        (MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4), 4, "28 ÷ 4 = 7"),
    ],
)
def test_missing_number_equation(
    data: MissingNumberQuestionData, missing: int | str, expected: str
) -> None:
    assert missing_number_equation(data, missing) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            MissingNumberQuestionData(Operation.DIVIDE, Unknown.FIRST, 4, 7, 28),
            TileQuestion(f"{BLANK} ÷ 4 = 7", "28", "28 ÷ 4 = 7"),
        ),
        (
            MissingNumberQuestionData(Operation.DIVIDE, Unknown.SECOND, 28, 7, 4),
            TileQuestion(f"28 ÷ {BLANK} = 7", "4", "28 ÷ 4 = 7"),
        ),
    ],
)
def test_missing_number_tile_question(
    data: MissingNumberQuestionData, expected: TileQuestion
) -> None:
    """On the tiles sheet the prompt has the square, the bank shows the missing number, and the
    key has the whole equation."""
    assert missing_number_tile_question(data) == expected


ADD = BasicOperationQuestionData(Operation.ADD, (47, 25), 72)
SUBTRACT = BasicOperationQuestionData(Operation.SUBTRACT, (72, 25), 47)
MULTIPLY = BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12)  # 3 groups of 4
DIVIDE = BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4)  # 12 shared into 3 groups


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            BasicOperationQuestionData(Operation.ADD, (3, 4), 7),
            TileQuestion("3 + 4 = ?", "7", "3 + 4 = 7"),
        ),
        # a word problem: the prompt is its wording, and the key still has the equation
        (
            BasicOperationQuestionData(
                Operation.SUBTRACT,
                (72, 25),
                47,
                "Maria had 72 cards and used 25. How many are left?",
            ),
            TileQuestion(
                "Maria had 72 cards and used 25. How many are left?",
                "47",
                "72 \N{MINUS SIGN} 25 = 47",
            ),
        ),
    ],
)
def test_basic_operation_tile_question(
    data: BasicOperationQuestionData, expected: TileQuestion
) -> None:
    assert basic_operation_tile_question(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # addition: both parts are shown, and the whole is to find
        (ADD, StripDiagram((47, 25), 72, StripUnknown.WHOLE)),
        # subtraction: the whole and the left part are shown, and the right part is to find
        (SUBTRACT, StripDiagram((25, 47), 72, StripUnknown.RIGHT)),
        # multiplication: 3 equal parts of 4 are shown, and the whole is to find
        (MULTIPLY, EqualStripDiagram(3, 4, StripUnknown.WHOLE)),
        # division: the whole is split into 3 equal parts, and their size is to find
        (DIVIDE, EqualStripDiagram(3, 4, StripUnknown.SIZE)),
    ],
)
def test_strip_diagram(
    data: BasicOperationQuestionData, expected: StripDiagram | EqualStripDiagram
) -> None:
    assert strip_diagram(data) == expected


@pytest.mark.parametrize(
    ("strip", "whole"),
    [
        (EqualStripDiagram(3, 4, StripUnknown.WHOLE), 12),
        (EqualStripDiagram(6, 20, StripUnknown.SIZE), 120),
    ],
)
def test_equal_strip_diagram_whole(strip: EqualStripDiagram, whole: int) -> None:
    assert strip.whole == whole


@pytest.mark.parametrize(
    ("data", "picture", "expected"),
    [
        (ADD, Picture.STRIP, "Both parts are shown. Add the parts to find the whole."),
        (
            SUBTRACT,
            Picture.STRIP,
            "The whole and one part are shown. Subtract to find the missing part.",
        ),
        (
            MULTIPLY,
            Picture.STRIP,
            "Equal groups are shown. Multiply the group size by the number of groups.",
        ),
        (
            DIVIDE,
            Picture.STRIP,
            "The whole is split into equal groups. Divide to find the amount in each group.",
        ),
        # text only has no hints
        (ADD, Picture.NONE, None),
        (DIVIDE, Picture.NONE, None),
    ],
)
def test_hint(data: BasicOperationQuestionData, picture: Picture, expected: str | None) -> None:
    assert hint(data, picture) == expected


@pytest.mark.parametrize(
    ("picture", "operations", "expected"),
    [
        (
            Picture.STRIP,
            [Operation.ADD, Operation.SUBTRACT],
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.ADD],
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.SUBTRACT],
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.MULTIPLY, Operation.DIVIDE],
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.MULTIPLY],
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.DIVIDE],
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # one of each kind is enough for both
        (
            Picture.STRIP,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Picture.STRIP,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # text only: the same for any operations
        (
            Picture.NONE,
            [Operation.ADD, Operation.SUBTRACT],
            "Read each problem. Show your work in the box.",
        ),
        (
            Picture.NONE,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            "Read each problem. Show your work in the box.",
        ),
    ],
)
def test_instruction(picture: Picture, operations: list[Operation], expected: str) -> None:
    assert instruction(picture, operations) == expected


@pytest.mark.parametrize(
    ("operations", "expected"),
    [
        ([Operation.ADD], "Addition"),
        ([Operation.DIVIDE], "Division"),
        ([Operation.ADD, Operation.SUBTRACT], "Addition and Subtraction"),
        ([Operation.MULTIPLY, Operation.DIVIDE], "Multiplication and Division"),
        ([Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY], "Mixed Operations"),
        (list(Operation), "Mixed Operations"),
    ],
)
def test_operations_name(operations: list[Operation], expected: str) -> None:
    assert operations_name(operations) == expected


@pytest.mark.parametrize(
    ("picture", "expected"),
    [
        (Picture.STRIP, "Word Problems — Strip Diagrams"),
        # text only: no picture to name
        (Picture.NONE, "Word Problems"),
        (Picture.NUMBER_LINE, "Word Problems — Number Lines"),
        (Picture.BLOCKS, "Word Problems — Base-Ten Blocks"),
    ],
)
def test_word_problems_title(picture: Picture, expected: str) -> None:
    assert word_problems_title(picture) == expected
