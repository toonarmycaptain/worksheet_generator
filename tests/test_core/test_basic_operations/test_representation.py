"""The wording of basic-operation questions: a missing-number equation, how the self-check tiles
sheet shows a question, and a word problem's strip diagram, number line jumps, hint, instruction
and sheet title. Also the equations and the strip diagrams a problem's own is chosen from, and
what each problem shows."""

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.basic_operations.representation import (
    EqualStripDiagram,
    Prompt,
    Representation,
    StripDiagram,
    basic_operation_tile_question,
    equation_choices,
    hint,
    instruction,
    missing_number_equation,
    missing_number_tile_question,
    number_line_jumps,
    operations_name,
    prompt_texts,
    strip_choices,
    strip_diagram,
    word_problems_title,
)
from core.question import BLANK, MultipleChoice
from core.self_check_tiles import TileQuestion
from tests.helpers import reverse_shuffle


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
        (ADD, StripDiagram((47, 25), None)),
        # subtraction: the whole and the left part are shown, and the right part is to find
        (SUBTRACT, StripDiagram((25, None), 72)),
        # multiplication: 3 equal parts of 4 are shown, and the whole is to find
        (MULTIPLY, EqualStripDiagram(3, 4, None)),
        # division: the whole is split into 3 equal parts, and their size is to find
        (DIVIDE, EqualStripDiagram(3, None, 12)),
    ],
)
def test_strip_diagram(
    data: BasicOperationQuestionData, expected: StripDiagram | EqualStripDiagram
) -> None:
    assert strip_diagram(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # Addition: the wrong strips subtract, multiply and divide its numbers, with the smaller
        # number as the groups. Subtracting makes the larger number the whole.
        (
            BasicOperationQuestionData(Operation.ADD, (9, 4), 13),
            MultipleChoice(
                (
                    EqualStripDiagram(4, None, 9),
                    EqualStripDiagram(4, 9, None),
                    StripDiagram((4, None), 9),
                    StripDiagram((9, 4), None),
                ),
                frozenset({3}),
            ),
        ),
        # adding keeps the numbers' order, and the smaller is the groups when it's first too
        (
            BasicOperationQuestionData(Operation.ADD, (4, 9), 13),
            MultipleChoice(
                (
                    EqualStripDiagram(4, None, 9),
                    EqualStripDiagram(4, 9, None),
                    StripDiagram((4, None), 9),
                    StripDiagram((4, 9), None),
                ),
                frozenset({3}),
            ),
        ),
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (13, 4), 9),
            MultipleChoice(
                (
                    EqualStripDiagram(4, None, 13),
                    EqualStripDiagram(4, 13, None),
                    StripDiagram((13, 4), None),
                    StripDiagram((4, None), 13),
                ),
                frozenset({3}),
            ),
        ),
        # Multiplication's groups are its own, its first operand. Sharing 4 into 3 equal groups
        # is impossible, and is a choice anyway.
        (
            MULTIPLY,
            MultipleChoice(
                (
                    EqualStripDiagram(3, None, 4),
                    StripDiagram((3, None), 4),
                    StripDiagram((3, 4), None),
                    EqualStripDiagram(3, 4, None),
                ),
                frozenset({3}),
            ),
        ),
        # even when its first operand is the larger
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (5, 2), 10),
            MultipleChoice(
                (
                    EqualStripDiagram(5, None, 2),
                    StripDiagram((2, None), 5),
                    StripDiagram((5, 2), None),
                    EqualStripDiagram(5, 2, None),
                ),
                frozenset({3}),
            ),
        ),
        # division's groups are its own, its second operand
        (
            DIVIDE,
            MultipleChoice(
                (
                    EqualStripDiagram(3, 12, None),
                    StripDiagram((3, None), 12),
                    StripDiagram((12, 3), None),
                    EqualStripDiagram(3, None, 12),
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_strip_choices(
    data: BasicOperationQuestionData,
    expected: MultipleChoice[StripDiagram | EqualStripDiagram],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A problem's own strip diagram is one choice, and the strips of the other three operations on
    its numbers are the wrong ones. ``shuffle`` reverses, so the wrong strips come in the reverse
    of ``Operation``'s order, and the problem's own is last.
    """
    reverse_shuffle(monkeypatch)
    assert strip_choices(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # Addition: the wrong equations subtract, multiply and divide its numbers, with the
        # smaller number as the groups. Subtracting and dividing put the larger number first.
        (
            BasicOperationQuestionData(Operation.ADD, (9, 4), 13),
            MultipleChoice(
                (
                    f"9 \N{DIVISION SIGN} 4 = {BLANK}",
                    f"4 \N{MULTIPLICATION SIGN} 9 = {BLANK}",
                    f"9 \N{MINUS SIGN} 4 = {BLANK}",
                    f"9 + 4 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
        # adding keeps the numbers' order, and the smaller is the groups when it's first too
        (
            BasicOperationQuestionData(Operation.ADD, (4, 9), 13),
            MultipleChoice(
                (
                    f"9 \N{DIVISION SIGN} 4 = {BLANK}",
                    f"4 \N{MULTIPLICATION SIGN} 9 = {BLANK}",
                    f"9 \N{MINUS SIGN} 4 = {BLANK}",
                    f"4 + 9 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (13, 4), 9),
            MultipleChoice(
                (
                    f"13 \N{DIVISION SIGN} 4 = {BLANK}",
                    f"4 \N{MULTIPLICATION SIGN} 13 = {BLANK}",
                    f"13 + 4 = {BLANK}",
                    f"13 \N{MINUS SIGN} 4 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
        # multiplication's groups are its own, its first operand, and 4 ÷ 3 needn't be even
        (
            MULTIPLY,
            MultipleChoice(
                (
                    f"4 \N{DIVISION SIGN} 3 = {BLANK}",
                    f"4 \N{MINUS SIGN} 3 = {BLANK}",
                    f"3 + 4 = {BLANK}",
                    f"3 \N{MULTIPLICATION SIGN} 4 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
        # Even when its first operand is the larger: dividing shares 2 into 5 groups, as on the
        # strip. Subtracting still takes the smaller from the larger.
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (5, 2), 10),
            MultipleChoice(
                (
                    f"2 \N{DIVISION SIGN} 5 = {BLANK}",
                    f"5 \N{MINUS SIGN} 2 = {BLANK}",
                    f"5 + 2 = {BLANK}",
                    f"5 \N{MULTIPLICATION SIGN} 2 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
        # division's groups are its own, its second operand
        (
            DIVIDE,
            MultipleChoice(
                (
                    f"3 \N{MULTIPLICATION SIGN} 12 = {BLANK}",
                    f"12 \N{MINUS SIGN} 3 = {BLANK}",
                    f"12 + 3 = {BLANK}",
                    f"12 \N{DIVISION SIGN} 3 = {BLANK}",
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_equation_choices(
    data: BasicOperationQuestionData, expected: MultipleChoice[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A problem's own equation is one choice, and the equations of the other three operations on its
    numbers are the wrong ones, each the equation of that operation's strip in ``strip_choices``.
    ``shuffle`` reverses, so the wrong equations come in the reverse of ``Operation``'s order, and
    the problem's own is last.
    """
    reverse_shuffle(monkeypatch)
    assert equation_choices(data) == expected


@pytest.mark.parametrize(
    ("data", "prompt", "expected"),
    [
        (
            BasicOperationQuestionData(
                Operation.ADD,
                (47, 5),
                52,
                "Maria had 47 cards and found 5 more. How many cards does Maria have now?",
            ),
            Prompt.WORD_PROBLEM,
            ("Maria had 47 cards and found 5 more. How many cards does Maria have now?",),
        ),
        (
            BasicOperationQuestionData(
                Operation.ADD,
                (47, 5),
                52,
                "Maria had 47 cards and found 5 more. How many cards does Maria have now?",
            ),
            Prompt.EQUATION,
            ("47 + 5 = ?",),
        ),
        # the wording, then the equation
        (
            BasicOperationQuestionData(
                Operation.ADD,
                (47, 5),
                52,
                "Maria had 47 cards and found 5 more. How many cards does Maria have now?",
            ),
            Prompt.BOTH,
            (
                "Maria had 47 cards and found 5 more. How many cards does Maria have now?",
                "47 + 5 = ?",
            ),
        ),
        (DIVIDE, Prompt.EQUATION, ("12 \N{DIVISION SIGN} 3 = ?",)),
        # a problem with no wording shows its equation
        (DIVIDE, Prompt.WORD_PROBLEM, ("12 \N{DIVISION SIGN} 3 = ?",)),
    ],
)
def test_prompt_texts(
    data: BasicOperationQuestionData, prompt: Prompt, expected: tuple[str, ...]
) -> None:
    assert prompt_texts(data, prompt) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # addition jumps forward, by each place of the second operand
        (BasicOperationQuestionData(Operation.ADD, (47, 25), 72), (20, 5)),
        # subtraction jumps backward
        (BasicOperationQuestionData(Operation.SUBTRACT, (72, 25), 47), (-20, -5)),
        # three places, three jumps
        (BasicOperationQuestionData(Operation.SUBTRACT, (347, 125), 222), (-100, -20, -5)),
        # a place of 0 has no jump
        (BasicOperationQuestionData(Operation.ADD, (35, 804), 839), (800, 4)),
        (BasicOperationQuestionData(Operation.ADD, (81, 70), 151), (70,)),
    ],
)
def test_number_line_jumps(data: BasicOperationQuestionData, expected: tuple[int, ...]) -> None:
    assert number_line_jumps(data) == expected


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (MULTIPLY, "A number line shows only addition and subtraction, not multiplication."),
        (DIVIDE, "A number line shows only addition and subtraction, not division."),
    ],
)
def test_number_line_jumps_errors(data: BasicOperationQuestionData, message: str) -> None:
    with pytest.raises(ValueError) as error:
        number_line_jumps(data)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("data", "representation", "expected"),
    [
        (ADD, Representation.STRIP, "Both parts are shown. Add the parts to find the whole."),
        (
            SUBTRACT,
            Representation.STRIP,
            "The whole and one part are shown. Subtract to find the missing part.",
        ),
        (
            MULTIPLY,
            Representation.STRIP,
            "Equal groups are shown. Multiply the group size by the number of groups.",
        ),
        (
            DIVIDE,
            Representation.STRIP,
            "The whole is split into equal groups. Divide to find the amount in each group.",
        ),
        # text only has no hints
        (ADD, Representation.NONE, None),
        (DIVIDE, Representation.NONE, None),
        (
            ADD,
            Representation.NUMBER_LINE,
            "Jump forward to add. Fill in each box; the last box is your answer.",
        ),
        (
            SUBTRACT,
            Representation.NUMBER_LINE,
            "Jump backward to subtract. Fill in each box; the last box is your answer.",
        ),
        (ADD, Representation.BLOCKS, "Combine the blocks to find the total."),
        # the amount to cross out, the second number
        (SUBTRACT, Representation.BLOCKS, "Cross out 25 to subtract."),
        # equation multiple choice has no hints
        (ADD, Representation.EQUATION_CHOICE, None),
        (DIVIDE, Representation.EQUATION_CHOICE, None),
    ],
)
def test_hint(
    data: BasicOperationQuestionData, representation: Representation, expected: str | None
) -> None:
    assert hint(data, representation) == expected


@pytest.mark.parametrize(
    ("representation", "operations", "work_box", "expected"),
    [
        (
            Representation.STRIP,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.ADD],
            True,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.SUBTRACT],
            True,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.MULTIPLY, Operation.DIVIDE],
            True,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.MULTIPLY],
            True,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.DIVIDE],
            True,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # one of each kind is enough for both
        (
            Representation.STRIP,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            True,
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            True,
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # text only: the same for any operations
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            "Read each problem. Show your work in the box.",
        ),
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            True,
            "Read each problem. Show your work in the box.",
        ),
        # without the work boxes, no box to mention
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            "Read each problem and solve it.",
        ),
        # number line: the same for addition, subtraction or both
        (
            Representation.NUMBER_LINE,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            "Use the number line. Start at the first number and jump by hundreds, tens, and ones.",
        ),
        (
            Representation.NUMBER_LINE,
            [Operation.SUBTRACT],
            True,
            "Use the number line. Start at the first number and jump by hundreds, tens, and ones.",
        ),
        # base-ten blocks: the same for addition, subtraction or both
        (
            Representation.BLOCKS,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            "Use the base-ten blocks to help you solve each problem.",
        ),
        (
            Representation.BLOCKS,
            [Operation.ADD],
            True,
            "Use the base-ten blocks to help you solve each problem.",
        ),
        # equation multiple choice: the same for any operations
        (
            Representation.EQUATION_CHOICE,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            f"Choose the equation that matches each problem. The {BLANK} shows what to find.",
        ),
        (
            Representation.EQUATION_CHOICE,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            f"Choose the equation that matches each problem. The {BLANK} shows what to find.",
        ),
    ],
)
def test_instruction(
    representation: Representation, operations: list[Operation], work_box: bool, expected: str
) -> None:
    assert instruction(representation, operations, work_box) == expected


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
    ("representation", "expected"),
    [
        (Representation.STRIP, "Word Problems — Strip Diagrams"),
        # text only: no representation to name
        (Representation.NONE, "Word Problems"),
        (Representation.NUMBER_LINE, "Word Problems — Number Lines"),
        (Representation.BLOCKS, "Word Problems — Base-Ten Blocks"),
        (Representation.EQUATION_CHOICE, "Word Problems — Equation multiple choice"),
    ],
)
def test_word_problems_title(representation: Representation, expected: str) -> None:
    assert word_problems_title(representation) == expected
