"""The wording of basic-operation questions: a missing-number equation, how the self-check tiles
sheet shows a question, two-step ones included, and a word problem's strip diagram, two-step
strip diagram, number line jumps, hint, instruction and sheet title. Also the equations, the
number lines and the strip diagrams a problem's own is chosen from, two-step strip diagrams
included, and what each problem shows."""

from collections.abc import Callable

import pytest

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    TwoStepQuestionData,
    Unknown,
)
from core.basic_operations.representation import (
    EqualStripDiagram,
    Prompt,
    Representation,
    Response,
    StripDiagram,
    TwoJumpLine,
    TwoStepStripDiagram,
    WordProblemKind,
    basic_operation_tile_question,
    equation_choices,
    has_fair_equation_choices,
    hint,
    instruction,
    missing_number_equation,
    missing_number_tile_question,
    number_line_choices,
    number_line_jumps,
    operations_name,
    prompt_texts,
    strip_choices,
    strip_diagram,
    two_step_equation_choices,
    two_step_strip,
    two_step_strip_choices,
    two_step_tile_question,
    word_problem_kinds,
    word_problems_title,
)
from core.question import BLANK, MultipleChoice
from core.self_check_tiles import TileQuestion
from tests.helpers import choice_indexes, choice_returns, reverse_shuffle


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

# one two-step problem of each shape that one bar shows
ADD_ADD = TwoStepQuestionData(  # (4 + 6) + 7
    (
        BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
        BasicOperationQuestionData(Operation.ADD, (10, 7), 17),
    ),
    Unknown.FIRST,
    17,
)
SUBTRACT_SUBTRACT = TwoStepQuestionData(  # (25 - 5) - 8
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (25, 5), 20),
        BasicOperationQuestionData(Operation.SUBTRACT, (20, 8), 12),
    ),
    Unknown.FIRST,
    12,
)
SUBTRACT_DIVIDE = TwoStepQuestionData(  # (24 - 6) shared into 3 groups
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
        BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
    ),
    Unknown.FIRST,
    6,
)
MULTIPLY_ADD = TwoStepQuestionData(  # (3 groups of 5) + 4
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
        BasicOperationQuestionData(Operation.ADD, (15, 4), 19),
    ),
    Unknown.FIRST,
    19,
)
MULTIPLY_SUBTRACT = TwoStepQuestionData(  # 45 - (3 groups of 5)
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 5), 15),
        BasicOperationQuestionData(Operation.SUBTRACT, (45, 15), 30),
    ),
    Unknown.SECOND,
    30,
)


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
        # with no wording, the prompt has the first step in brackets
        (
            MULTIPLY_SUBTRACT,
            TileQuestion(
                "45 \N{MINUS SIGN} (3 \N{MULTIPLICATION SIGN} 5) = ?",
                "30",
                "3 \N{MULTIPLICATION SIGN} 5 = 15,  45 \N{MINUS SIGN} 15 = 30",
            ),
        ),
        # a word problem: the prompt is its wording, and the key has each step
        (
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                    BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                ),
                Unknown.FIRST,
                6,
                "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                "How many cards are in each group?",
            ),
            TileQuestion(
                "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                "How many cards are in each group?",
                "6",
                "24 \N{MINUS SIGN} 6 = 18,  18 \N{DIVISION SIGN} 3 = 6",
            ),
        ),
    ],
)
def test_two_step_tile_question(data: TwoStepQuestionData, expected: TileQuestion) -> None:
    assert two_step_tile_question(data) == expected


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
        # adding three numbers: the parts in the order they're added, and the whole to find
        (ADD_ADD, TwoStepStripDiagram((4, 6, 7), None)),
        # taking two from a whole: the parts taken, then the part to find
        (SUBTRACT_SUBTRACT, TwoStepStripDiagram((5, 8, None), 25)),
        # what's left after the part is taken, shared into 3 equal parts to find
        (SUBTRACT_DIVIDE, TwoStepStripDiagram((6, None, None, None), 24)),
        # 3 equal parts of 5, then the part added, and the whole to find
        (MULTIPLY_ADD, TwoStepStripDiagram((5, 5, 5, 4), None)),
        # 3 equal parts of 5 taken from the whole, then the part to find
        (MULTIPLY_SUBTRACT, TwoStepStripDiagram((5, 5, 5, None), 45)),
    ],
)
def test_two_step_strip(data: TwoStepQuestionData, expected: TwoStepStripDiagram) -> None:
    assert two_step_strip(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # adding three parts: each part as the whole, with the whole to find the first part
        (
            ADD_ADD,
            MultipleChoice(
                (
                    TwoStepStripDiagram((None, 4, 6), 7),
                    TwoStepStripDiagram((None, 4, 7), 6),
                    TwoStepStripDiagram((None, 6, 7), 4),
                    TwoStepStripDiagram((4, 6, 7), None),
                ),
                frozenset({3}),
            ),
        ),
        # Taking two from a whole: each part taken as the whole, with the whole the first part,
        # and the whole as a part, with the whole to find. A part larger than its whole is
        # impossible, and a choice anyway.
        (
            SUBTRACT_SUBTRACT,
            MultipleChoice(
                (
                    TwoStepStripDiagram((25, 5, None), 8),
                    TwoStepStripDiagram((25, 8, None), 5),
                    TwoStepStripDiagram((25, 5, 8), None),
                    TwoStepStripDiagram((5, 8, None), 25),
                ),
                frozenset({3}),
            ),
        ),
        # Equal parts: one too many, the equal parts forgotten, and the unknown as the whole
        (
            SUBTRACT_DIVIDE,
            MultipleChoice(
                (
                    TwoStepStripDiagram((6, None, None, None, None), 24),
                    TwoStepStripDiagram((6, None), 24),
                    TwoStepStripDiagram((24, 6), None),
                    TwoStepStripDiagram((6, None, None, None), 24),
                ),
                frozenset({3}),
            ),
        ),
        # the whole is already the unknown, so the other part is the whole instead
        (
            MULTIPLY_ADD,
            MultipleChoice(
                (
                    TwoStepStripDiagram((5, 5, 5, 5, 4), None),
                    TwoStepStripDiagram((5, 4), None),
                    TwoStepStripDiagram((None, 5, 5, 5), 4),
                    TwoStepStripDiagram((5, 5, 5, 4), None),
                ),
                frozenset({3}),
            ),
        ),
        (
            MULTIPLY_SUBTRACT,
            MultipleChoice(
                (
                    TwoStepStripDiagram((5, 5, 5, 5, None), 45),
                    TwoStepStripDiagram((5, None), 45),
                    TwoStepStripDiagram((45, 5, 5, 5), None),
                    TwoStepStripDiagram((5, 5, 5, None), 45),
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_two_step_strip_choices(
    data: TwoStepQuestionData,
    expected: MultipleChoice[TwoStepStripDiagram],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A problem's own strip diagram is one choice, and three wrong strips are the others.
    ``shuffle`` reverses, so the wrong strips come last first, and the problem's own is last.
    """
    reverse_shuffle(monkeypatch)
    assert two_step_strip_choices(data) == expected


@pytest.mark.parametrize(
    ("make", "data", "message"),
    [
        # adding, then taking away: the part taken away isn't in the bar
        (
            two_step_strip,
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.ADD, (4, 6), 10),
                    BasicOperationQuestionData(Operation.SUBTRACT, (10, 3), 7),
                ),
                Unknown.FIRST,
                7,
            ),
            "One strip diagram shows only some shapes of two-step problem.",
        ),
        # sharing, then sharing again: equal parts of equal parts
        (
            two_step_strip_choices,
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.DIVIDE, (24, 2), 12),
                    BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4),
                ),
                Unknown.FIRST,
                4,
            ),
            "One strip diagram shows only some shapes of two-step problem.",
        ),
    ],
)
def test_two_step_strip_errors(
    make: Callable[[TwoStepQuestionData], object], data: TwoStepQuestionData, message: str
) -> None:
    """A shape that one bar can't show raises ``ValueError``, for its strip and its choices."""
    with pytest.raises(ValueError) as error:
        make(data)
    assert str(error.value) == message


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


# (24 - 6) + 5, and 4 shared into (12 shared into 6 groups) groups
SUBTRACT_ADD = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
        BasicOperationQuestionData(Operation.ADD, (18, 5), 23),
    ),
    Unknown.FIRST,
    23,
)
DIVIDE_INTO_DIVIDE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.DIVIDE, (12, 6), 2),
        BasicOperationQuestionData(Operation.DIVIDE, (4, 2), 2),
    ),
    Unknown.SECOND,
    2,
)
# one operation twice: (45 - 12) - 8, (30 shared into 5 groups) shared into 3, (12 + 8) + 5,
# (2 groups of 3) groups of 16, and 5 groups of (3 groups of 2)
SUBTRACT_TWICE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.SUBTRACT, (45, 12), 33),
        BasicOperationQuestionData(Operation.SUBTRACT, (33, 8), 25),
    ),
    Unknown.FIRST,
    25,
)
DIVIDE_TWICE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.DIVIDE, (30, 5), 6),
        BasicOperationQuestionData(Operation.DIVIDE, (6, 3), 2),
    ),
    Unknown.FIRST,
    2,
)
ADD_TWICE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.ADD, (12, 8), 20),
        BasicOperationQuestionData(Operation.ADD, (20, 5), 25),
    ),
    Unknown.FIRST,
    25,
)
MULTIPLY_TWICE = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (2, 3), 6),
        BasicOperationQuestionData(Operation.MULTIPLY, (6, 16), 96),
    ),
    Unknown.FIRST,
    96,
)
MULTIPLY_INTO_MULTIPLY = TwoStepQuestionData(
    (
        BasicOperationQuestionData(Operation.MULTIPLY, (3, 2), 6),
        BasicOperationQuestionData(Operation.MULTIPLY, (5, 6), 30),
    ),
    Unknown.SECOND,
    30,
)


@pytest.mark.parametrize(
    ("data", "operations", "picks", "mistake_pairs", "expected"),
    [
        # Taking away, then sharing: each mistake pair has fair sets. The first sign and the
        # brackets here, with + as the first sign.
        (
            SUBTRACT_DIVIDE,
            list(Operation),
            [1, 0],
            3,
            MultipleChoice(
                (
                    "24 + (6 \N{DIVISION SIGN} 3) = s",
                    "24 \N{MINUS SIGN} (6 \N{DIVISION SIGN} 3) = s",
                    "(24 + 6) \N{DIVISION SIGN} 3 = s",
                    "(24 \N{MINUS SIGN} 6) \N{DIVISION SIGN} 3 = s",
                ),
                frozenset({3}),
            ),
        ),
        # both signs, the first + and the second +
        (
            SUBTRACT_DIVIDE,
            list(Operation),
            [0, 0],
            3,
            MultipleChoice(
                (
                    "(24 + 6) + 3 = s",
                    "(24 \N{MINUS SIGN} 6) + 3 = s",
                    "(24 + 6) \N{DIVISION SIGN} 3 = s",
                    "(24 \N{MINUS SIGN} 6) \N{DIVISION SIGN} 3 = s",
                ),
                frozenset({3}),
            ),
        ),
        # only the ticked operations' signs: the second sign and the brackets
        (
            SUBTRACT_DIVIDE,
            [Operation.SUBTRACT, Operation.DIVIDE],
            [2, 0],
            3,
            MultipleChoice(
                (
                    "24 \N{MINUS SIGN} (6 \N{MINUS SIGN} 3) = s",
                    "24 \N{MINUS SIGN} (6 \N{DIVISION SIGN} 3) = s",
                    "(24 \N{MINUS SIGN} 6) \N{MINUS SIGN} 3 = s",
                    "(24 \N{MINUS SIGN} 6) \N{DIVISION SIGN} 3 = s",
                ),
                frozenset({3}),
            ),
        ),
        # Only the signs: moving the brackets with a sign changed gives two wrong equations of the
        # same value, (24 + 6) + 5 and 24 + (6 + 5), or (24 - 6) - 5 and 24 - (6 + 5).
        (
            SUBTRACT_ADD,
            [Operation.ADD, Operation.SUBTRACT],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "(24 + 6) \N{MINUS SIGN} 5 = s",
                    "(24 \N{MINUS SIGN} 6) \N{MINUS SIGN} 5 = s",
                    "(24 + 6) + 5 = s",
                    "(24 \N{MINUS SIGN} 6) + 5 = s",
                ),
                frozenset({3}),
            ),
        ),
        # In the story's order 4 - 6 is ruled out at a glance, and moving the brackets gives the
        # answer, so every choice has 6 + 4 the other way round.
        (
            ADD_ADD,
            [Operation.ADD, Operation.SUBTRACT],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "(6 \N{MINUS SIGN} 4) \N{MINUS SIGN} 7 = s",
                    "(6 + 4) \N{MINUS SIGN} 7 = s",
                    "(6 \N{MINUS SIGN} 4) + 7 = s",
                    "(6 + 4) + 7 = s",
                ),
                frozenset({3}),
            ),
        ),
        # with multiplication ticked, 4 x 6 keeps the story's order; the brackets still can't move
        (
            ADD_ADD,
            [Operation.ADD, Operation.MULTIPLY],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "(4 \N{MULTIPLICATION SIGN} 6) \N{MULTIPLICATION SIGN} 7 = s",
                    "(4 + 6) \N{MULTIPLICATION SIGN} 7 = s",
                    "(4 \N{MULTIPLICATION SIGN} 6) + 7 = s",
                    "(4 + 6) + 7 = s",
                ),
                frozenset({3}),
            ),
        ),
        # Taking away equal groups, with the brackets on the last two numbers: moving them puts
        # them on the first two.
        (
            MULTIPLY_SUBTRACT,
            list(Operation),
            [1, 0],
            3,
            MultipleChoice(
                (
                    "(45 + 3) \N{MULTIPLICATION SIGN} 5 = s",
                    "(45 \N{MINUS SIGN} 3) \N{MULTIPLICATION SIGN} 5 = s",
                    "45 + (3 \N{MULTIPLICATION SIGN} 5) = s",
                    "45 \N{MINUS SIGN} (3 \N{MULTIPLICATION SIGN} 5) = s",
                ),
                frozenset({3}),
            ),
        ),
        # With only - and x, 3 - 5 is ruled out at a glance, so every choice has 5 x 3 the other
        # way round. Changing the first sign as well as moving the brackets gives two wrong
        # equations of the same value, 45 x (5 x 3) and (45 x 5) x 3.
        (
            MULTIPLY_SUBTRACT,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            [1, 0],
            2,
            MultipleChoice(
                (
                    "(45 \N{MINUS SIGN} 5) \N{MINUS SIGN} 3 = s",
                    "(45 \N{MINUS SIGN} 5) \N{MULTIPLICATION SIGN} 3 = s",
                    "45 \N{MINUS SIGN} (5 \N{MINUS SIGN} 3) = s",
                    "45 \N{MINUS SIGN} (5 \N{MULTIPLICATION SIGN} 3) = s",
                ),
                frozenset({3}),
            ),
        ),
        # 4 ÷ 2 and 4 - 2 are both 2, so the first sign can't be -, and moving the brackets gives
        # 4 ÷ 12, ruled out at a glance: only the signs
        (
            DIVIDE_INTO_DIVIDE,
            list(Operation),
            [0, 0],
            1,
            MultipleChoice(
                (
                    "4 + (12 + 6) = s",
                    "4 \N{DIVISION SIGN} (12 + 6) = s",
                    "4 + (12 \N{DIVISION SIGN} 6) = s",
                    "4 \N{DIVISION SIGN} (12 \N{DIVISION SIGN} 6) = s",
                ),
                frozenset({3}),
            ),
        ),
        # Subtraction alone: the brackets moved, and the step outside them the other way round.
        (
            SUBTRACT_TWICE,
            [Operation.SUBTRACT],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "(12 \N{MINUS SIGN} 8) \N{MINUS SIGN} 45 = s",
                    "8 \N{MINUS SIGN} (45 \N{MINUS SIGN} 12) = s",
                    "45 \N{MINUS SIGN} (12 \N{MINUS SIGN} 8) = s",
                    "(45 \N{MINUS SIGN} 12) \N{MINUS SIGN} 8 = s",
                ),
                frozenset({3}),
            ),
        ),
        # and division alone
        (
            DIVIDE_TWICE,
            [Operation.DIVIDE],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "(5 \N{DIVISION SIGN} 3) \N{DIVISION SIGN} 30 = s",
                    "3 \N{DIVISION SIGN} (30 \N{DIVISION SIGN} 5) = s",
                    "30 \N{DIVISION SIGN} (5 \N{DIVISION SIGN} 3) = s",
                    "(30 \N{DIVISION SIGN} 5) \N{DIVISION SIGN} 3 = s",
                ),
                frozenset({3}),
            ),
        ),
        # Addition alone: 12 copied as 21, and a step left out. Only 12 can be reversed, so the
        # step left can only be 12 + 8: left with 8 + 5, both mistakes would look like one.
        (
            ADD_TWICE,
            [Operation.ADD],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "21 + 8 = s",
                    "12 + 8 = s",
                    "(21 + 8) + 5 = s",
                    "(12 + 8) + 5 = s",
                ),
                frozenset({3}),
            ),
        ),
        # And multiplication alone, where only 16 can be reversed, so the step left is 3 x 16. The
        # signs changed to + aren't offered, as these give a fair set.
        (
            MULTIPLY_TWICE,
            [Operation.MULTIPLY],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "3 \N{MULTIPLICATION SIGN} 61 = s",
                    "3 \N{MULTIPLICATION SIGN} 16 = s",
                    "(2 \N{MULTIPLICATION SIGN} 3) \N{MULTIPLICATION SIGN} 61 = s",
                    "(2 \N{MULTIPLICATION SIGN} 3) \N{MULTIPLICATION SIGN} 16 = s",
                ),
                frozenset({3}),
            ),
        ),
        # With no number to reverse, multiplication alone changes the first sign and the second
        # to +.
        (
            MULTIPLY_INTO_MULTIPLY,
            [Operation.MULTIPLY],
            [0, 0],
            1,
            MultipleChoice(
                (
                    "5 + (3 + 2) = s",
                    "5 \N{MULTIPLICATION SIGN} (3 + 2) = s",
                    "5 + (3 \N{MULTIPLICATION SIGN} 2) = s",
                    "5 \N{MULTIPLICATION SIGN} (3 \N{MULTIPLICATION SIGN} 2) = s",
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_two_step_equation_choices(
    data: TwoStepQuestionData,
    operations: list[Operation],
    picks: list[int],
    mistake_pairs: int,
    expected: MultipleChoice[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    The wrong equations cross two mistakes: the right one, one with each mistake, and one with
    both. ``choice`` picks the pair of mistakes, among the ``mistake_pairs`` with a fair set (with
    two or more operations ticked, the first sign and the second, the first sign and the
    brackets, the second sign and the brackets; with one, its only pair, or with multiplication
    alone, the signs changed to + if its digit reversed and step left out give none), and then a
    set, and
    ``shuffle`` reverses, so the choices come both mistakes, the second, the first, then the
    right one. A changed sign is the next of the ticked operations in ``Operation``'s order.
    """
    offered = choice_indexes(monkeypatch, picks)
    reverse_shuffle(monkeypatch)
    assert two_step_equation_choices(data, "s", operations) == expected
    assert len(offered[0]) == mistake_pairs


@pytest.mark.parametrize(
    ("data", "operations", "message"),
    [
        # 4 ÷ 2 and 4 - 2 are both 2, and 4 ÷ 12 is ruled out at a glance
        (
            DIVIDE_INTO_DIVIDE,
            [Operation.SUBTRACT, Operation.DIVIDE],
            "No fair wrong equations for 4 \N{DIVISION SIGN} (12 \N{DIVISION SIGN} 6).",
        ),
        # subtraction alone: both its mistakes move the brackets, which gives 5 - 8, ruled out at
        # a glance
        (
            SUBTRACT_SUBTRACT,
            [Operation.SUBTRACT],
            "No fair wrong equations for (25 \N{MINUS SIGN} 5) \N{MINUS SIGN} 8.",
        ),
        # division alone: likewise 4 ÷ 12
        (
            DIVIDE_INTO_DIVIDE,
            [Operation.DIVIDE],
            "No fair wrong equations for 4 \N{DIVISION SIGN} (12 \N{DIVISION SIGN} 6).",
        ),
        # addition alone: no number to reverse, in either order of 4 + 6
        (
            ADD_ADD,
            [Operation.ADD],
            "No fair wrong equations for (4 + 6) + 7.",
        ),
        # nor when reversing a number copies another: 12 and 21
        (
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.ADD, (12, 21), 33),
                    BasicOperationQuestionData(Operation.ADD, (33, 5), 38),
                ),
                Unknown.FIRST,
                38,
            ),
            [Operation.ADD],
            "No fair wrong equations for (12 + 21) + 5.",
        ),
    ],
)
def test_two_step_equation_choices_errors(
    data: TwoStepQuestionData, operations: list[Operation], message: str
) -> None:
    with pytest.raises(ValueError) as error:
        two_step_equation_choices(data, "s", operations)
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("data", "operations", "expected"),
    [
        (SUBTRACT_DIVIDE, [Operation.SUBTRACT, Operation.DIVIDE], True),
        # one operation, as above
        (SUBTRACT_SUBTRACT, [Operation.SUBTRACT], False),
        (SUBTRACT_TWICE, [Operation.SUBTRACT], True),
        (ADD_ADD, [Operation.ADD], False),
        (MULTIPLY_TWICE, [Operation.MULTIPLY], True),
        (MULTIPLY_INTO_MULTIPLY, [Operation.MULTIPLY], True),
        # with only - and ÷ there's none, as above, and with all four there is
        (DIVIDE_INTO_DIVIDE, [Operation.SUBTRACT, Operation.DIVIDE], False),
        (DIVIDE_INTO_DIVIDE, list(Operation), True),
        # only with 6 + 4 the other way round
        (ADD_ADD, [Operation.ADD, Operation.SUBTRACT], True),
    ],
)
def test_has_fair_equation_choices(
    data: TwoStepQuestionData, operations: list[Operation], expected: bool
) -> None:
    assert has_fair_equation_choices(data, operations) is expected


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
        # two steps: the first in brackets, where its answer is carried
        (
            SUBTRACT_DIVIDE,
            Prompt.EQUATION,
            ("(24 \N{MINUS SIGN} 6) \N{DIVISION SIGN} 3 = ?",),
        ),
        (
            MULTIPLY_SUBTRACT,
            Prompt.EQUATION,
            ("45 \N{MINUS SIGN} (3 \N{MULTIPLICATION SIGN} 5) = ?",),
        ),
        (
            TwoStepQuestionData(
                (
                    BasicOperationQuestionData(Operation.SUBTRACT, (24, 6), 18),
                    BasicOperationQuestionData(Operation.DIVIDE, (18, 3), 6),
                ),
                Unknown.FIRST,
                6,
                "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                "How many cards are in each group?",
            ),
            Prompt.BOTH,
            (
                "Maria had 24 cards and used 6. Maria put the rest into 3 equal groups. "
                "How many cards are in each group?",
                "(24 \N{MINUS SIGN} 6) \N{DIVISION SIGN} 3 = ?",
            ),
        ),
        (ADD_ADD, Prompt.WORD_PROBLEM, ("(4 + 6) + 7 = ?",)),
    ],
)
def test_prompt_texts(
    data: BasicOperationQuestionData | TwoStepQuestionData,
    prompt: Prompt,
    expected: tuple[str, ...],
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
    ("data", "side", "expected"),
    [
        # Addition, with the wrong landing drawn above the answer: the misread 25 is 52, the wrong
        # landing 10 above, and the wrong way subtracts.
        (
            ADD,
            1,
            MultipleChoice(
                (
                    TwoJumpLine(47, 52, 99),
                    TwoJumpLine(47, 25, 82),
                    TwoJumpLine(47, -25, 22),
                    TwoJumpLine(47, 25, 72),
                ),
                frozenset({3}),
            ),
        ),
        # subtraction jumps back, and its wrong way forward
        (
            SUBTRACT,
            1,
            MultipleChoice(
                (
                    TwoJumpLine(72, -52, 20),
                    TwoJumpLine(72, -25, 57),
                    TwoJumpLine(72, 25, 97),
                    TwoJumpLine(72, -25, 47),
                ),
                frozenset({3}),
            ),
        ),
        # 30 is misread as 3
        (
            BasicOperationQuestionData(Operation.ADD, (45, 30), 75),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(45, 3, 48),
                    TwoJumpLine(45, 30, 85),
                    TwoJumpLine(45, -30, 15),
                    TwoJumpLine(45, 30, 75),
                ),
                frozenset({3}),
            ),
        ),
        # with hundreds, the tens and ones are swapped
        (
            BasicOperationQuestionData(Operation.ADD, (347, 125), 472),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(347, 152, 499),
                    TwoJumpLine(347, 125, 482),
                    TwoJumpLine(347, -125, 222),
                    TwoJumpLine(347, 125, 472),
                ),
                frozenset({3}),
            ),
        ),
        # 33 swapped is 33, so it's misread as double, 66
        (
            BasicOperationQuestionData(Operation.ADD, (50, 33), 83),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(50, 66, 116),
                    TwoJumpLine(50, 33, 93),
                    TwoJumpLine(50, -33, 17),
                    TwoJumpLine(50, 33, 83),
                ),
                frozenset({3}),
            ),
        ),
        # 34 as 43 would land 9 from the answer, between the wrong landing's two spots, so it's
        # misread as double, 68
        (
            BasicOperationQuestionData(Operation.ADD, (50, 34), 84),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(50, 68, 118),
                    TwoJumpLine(50, 34, 94),
                    TwoJumpLine(50, -34, 16),
                    TwoJumpLine(50, 34, 84),
                ),
                frozenset({3}),
            ),
        ),
        # A second number of 10 or less steps 1: 10 above, 25, would be behind the first number,
        # its - 5 pointing back. 5 as 50 lands under 0, so it's misread as double, 10.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (20, 5), 15),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(20, -10, 10),
                    TwoJumpLine(20, -5, 16),
                    TwoJumpLine(20, 5, 25),
                    TwoJumpLine(20, -5, 15),
                ),
                frozenset({3}),
            ),
        ),
        # 10 isn't over 10, so the step is 1; 10 is misread as 1
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (50, 10), 40),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(50, -1, 49),
                    TwoJumpLine(50, -10, 41),
                    TwoJumpLine(50, 10, 60),
                    TwoJumpLine(50, -10, 40),
                ),
                frozenset({3}),
            ),
        ),
        # 1 above, 5, is the first number, so the wrong landing is 1 below, whichever side is
        # drawn. Every misreading of 1 lands under 0 or beside the answer, so the first number is
        # misread, 5 as 50.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (5, 1), 4),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(50, -1, 49),
                    TwoJumpLine(5, -1, 3),
                    TwoJumpLine(5, 1, 6),
                    TwoJumpLine(5, -1, 4),
                ),
                frozenset({3}),
            ),
        ),
        # The answer, 5, leaves no room 10 below, so the step is 1, even with 25. 25 as 52, and
        # double, 50, land under 0, so it's misread as 10 less, 15.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (30, 25), 5),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(30, -15, 15),
                    TwoJumpLine(30, -25, 6),
                    TwoJumpLine(30, 25, 55),
                    TwoJumpLine(30, -25, 5),
                ),
                frozenset({3}),
            ),
        ),
        # The answer is the second number, so doubling either number lands on 0 or on the wrong
        # way's 75, and no misreading clears both landing spots. The first to land somewhere new
        # would be 10 less, 15, but it lands on 35, where the wrong landing is, so one less, 24.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (50, 25), 25),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(50, -24, 26),
                    TwoJumpLine(50, -25, 35),
                    TwoJumpLine(50, 25, 75),
                    TwoJumpLine(50, -25, 25),
                ),
                frozenset({3}),
            ),
        ),
        # 2 - 1 has no wrong landing past its first number and above 0, so it lands 10 above,
        # pointing back. Every misreading of 1 lands on or under 0, so the first number is
        # misread, 2 as 20.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (2, 1), 1),
            1,
            MultipleChoice(
                (
                    TwoJumpLine(20, -1, 19),
                    TwoJumpLine(2, -1, 11),
                    TwoJumpLine(2, 1, 3),
                    TwoJumpLine(2, -1, 1),
                ),
                frozenset({3}),
            ),
        ),
        # with the wrong landing drawn below the answer, 10 below
        (
            ADD,
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(47, 52, 99),
                    TwoJumpLine(47, 25, 62),
                    TwoJumpLine(47, -25, 22),
                    TwoJumpLine(47, 25, 72),
                ),
                frozenset({3}),
            ),
        ),
        (
            SUBTRACT,
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(72, -52, 20),
                    TwoJumpLine(72, -25, 37),
                    TwoJumpLine(72, 25, 97),
                    TwoJumpLine(72, -25, 47),
                ),
                frozenset({3}),
            ),
        ),
        # 10 below, 40, would be behind the first number, its + 3 pointing back, so the step is 1
        (
            BasicOperationQuestionData(Operation.ADD, (47, 3), 50),
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(47, 30, 77),
                    TwoJumpLine(47, 3, 49),
                    TwoJumpLine(47, -3, 44),
                    TwoJumpLine(47, 3, 50),
                ),
                frozenset({3}),
            ),
        ),
        # 1 below, 47, is the first number, so the wrong landing is 1 above, whichever side is
        # drawn
        (
            BasicOperationQuestionData(Operation.ADD, (47, 1), 48),
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(47, 10, 57),
                    TwoJumpLine(47, 1, 49),
                    TwoJumpLine(47, -1, 46),
                    TwoJumpLine(47, 1, 48),
                ),
                frozenset({3}),
            ),
        ),
        # The answer, 8, leaves no room 10 below, so the step is 1, even with 12. 12 as 21, and
        # double, 24, land under 0, so it's misread as 10 less, 2.
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (20, 12), 8),
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(20, -2, 18),
                    TwoJumpLine(20, -12, 7),
                    TwoJumpLine(20, 12, 32),
                    TwoJumpLine(20, -12, 8),
                ),
                frozenset({3}),
            ),
        ),
        # with the wrong landing on 15, 10 less lands somewhere new, on 35
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (50, 25), 25),
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(50, -15, 35),
                    TwoJumpLine(50, -25, 15),
                    TwoJumpLine(50, 25, 75),
                    TwoJumpLine(50, -25, 25),
                ),
                frozenset({3}),
            ),
        ),
        # 2 - 1 has the same lines either way
        (
            BasicOperationQuestionData(Operation.SUBTRACT, (2, 1), 1),
            -1,
            MultipleChoice(
                (
                    TwoJumpLine(20, -1, 19),
                    TwoJumpLine(2, -1, 11),
                    TwoJumpLine(2, 1, 3),
                    TwoJumpLine(2, -1, 1),
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_number_line_choices(
    data: BasicOperationQuestionData,
    side: int,
    expected: MultipleChoice[TwoJumpLine],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A problem's own line is one choice, and the wrong lines are its second jump going the wrong
    way, its right jumps landing on a wrong number, and one of its numbers misread. Every line
    lands somewhere different, above 0 and not on the first number, and the wrong landing points
    the way its sign says, but for 2 - 1's. ``choice`` returns ``side``, the side of the answer
    the wrong landing tries first: 1 above, -1 below. ``shuffle`` reverses, so the wrong lines
    come misread, wrong landing, wrong way, and the problem's own is last.
    """
    choice_returns(monkeypatch, [side])
    reverse_shuffle(monkeypatch)
    assert number_line_choices(data) == expected


@pytest.mark.parametrize(
    ("data", "message"),
    [
        # the wrong way would go below 0, or to 0
        (
            BasicOperationQuestionData(Operation.ADD, (25, 47), 72),
            "A number line from 0 needs an addition's larger number first.",
        ),
        (
            BasicOperationQuestionData(Operation.ADD, (25, 25), 50),
            "A number line from 0 needs an addition's larger number first.",
        ),
        (MULTIPLY, "A number line shows only addition and subtraction, not multiplication."),
        (DIVIDE, "A number line shows only addition and subtraction, not division."),
    ],
)
def test_number_line_choices_errors(data: BasicOperationQuestionData, message: str) -> None:
    with pytest.raises(ValueError) as error:
        number_line_choices(data)
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
        (ADD, Representation.EQUATION, None),
        (DIVIDE, Representation.EQUATION, None),
        # a strip diagram has a hint for each shape of two-step problem
        (ADD_ADD, Representation.STRIP, "All three parts are shown. Add them to find the whole."),
        (
            SUBTRACT_SUBTRACT,
            Representation.STRIP,
            "The whole and two parts are shown. Subtract both parts to find the missing part.",
        ),
        (
            SUBTRACT_DIVIDE,
            Representation.STRIP,
            "Subtract the part that's shown from the whole, then divide the rest into the equal "
            "parts.",
        ),
        (
            MULTIPLY_ADD,
            Representation.STRIP,
            "Multiply to find the equal parts together, then add the other part to find the whole.",
        ),
        (
            MULTIPLY_SUBTRACT,
            Representation.STRIP,
            "Multiply to find the equal parts together, then subtract them from the whole to find "
            "the missing part.",
        ),
        # text only still has none, nor do equations
        (SUBTRACT_DIVIDE, Representation.NONE, None),
        (SUBTRACT_DIVIDE, Representation.EQUATION, None),
    ],
)
def test_hint(
    data: BasicOperationQuestionData | TwoStepQuestionData,
    representation: Representation,
    expected: str | None,
) -> None:
    assert hint(data, representation) == expected


@pytest.mark.parametrize(
    ("representation", "operations", "work_box", "choices", "two_steps", "expected"),
    [
        (
            Representation.STRIP,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            False,
            False,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.ADD],
            True,
            False,
            False,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.SUBTRACT],
            True,
            False,
            False,
            "Use the strip diagram (bar model): two parts make a whole. The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.MULTIPLY, Operation.DIVIDE],
            True,
            False,
            False,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.MULTIPLY],
            True,
            False,
            False,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.DIVIDE],
            True,
            False,
            False,
            "Use the strip diagram (bar model): equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # one of each kind is enough for both
        (
            Representation.STRIP,
            [Operation.SUBTRACT, Operation.MULTIPLY],
            True,
            False,
            False,
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        (
            Representation.STRIP,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            True,
            False,
            False,
            "Use the strip diagram (bar model): parts or equal groups make a whole. "
            "The ? shows what to find.",
        ),
        # text only: the same for any operations
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            False,
            False,
            "Read each problem. Show your work in the box.",
        ),
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            True,
            False,
            False,
            "Read each problem. Show your work in the box.",
        ),
        # without the work boxes, no box to mention
        (
            Representation.NONE,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            False,
            False,
            "Read each problem and solve it.",
        ),
        # number line: the same for addition, subtraction or both
        (
            Representation.NUMBER_LINE,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            False,
            False,
            "Use the number line. Start at the first number and jump by hundreds, tens, and ones.",
        ),
        (
            Representation.NUMBER_LINE,
            [Operation.SUBTRACT],
            True,
            False,
            False,
            "Use the number line. Start at the first number and jump by hundreds, tens, and ones.",
        ),
        # number lines to choose from: from 0, with both numbers as jumps
        (
            Representation.NUMBER_LINE,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            True,
            False,
            "Each number line starts at 0 and shows both numbers as jumps. Circle the correct one.",
        ),
        (
            Representation.NUMBER_LINE,
            [Operation.SUBTRACT],
            False,
            True,
            False,
            "Each number line starts at 0 and shows both numbers as jumps. Circle the correct one.",
        ),
        # base-ten blocks: the same for addition, subtraction or both
        (
            Representation.BLOCKS,
            [Operation.ADD, Operation.SUBTRACT],
            True,
            False,
            False,
            "Use the base-ten blocks to help you solve each problem.",
        ),
        (
            Representation.BLOCKS,
            [Operation.ADD],
            True,
            False,
            False,
            "Use the base-ten blocks to help you solve each problem.",
        ),
        # equation multiple choice: the same for any operations
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            True,
            False,
            f"Choose the equation that matches each problem. The {BLANK} shows what to find.",
        ),
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            True,
            False,
            f"Choose the equation that matches each problem. The {BLANK} shows what to find.",
        ),
        # equations, written: the same for any operations
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            False,
            False,
            f"Write an equation for each problem, with a {BLANK} for what to find. Solve it.",
        ),
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT, Operation.MULTIPLY, Operation.DIVIDE],
            False,
            False,
            False,
            f"Write an equation for each problem, with a {BLANK} for what to find. Solve it.",
        ),
        # two steps: equations to choose from have a letter for what to find
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            True,
            True,
            "Choose the equation that matches each problem. The letter stands for the number to "
            "find.",
        ),
        # written equations still ask for a square
        (
            Representation.EQUATION,
            [Operation.ADD, Operation.SUBTRACT],
            False,
            False,
            True,
            f"Write an equation for each problem, with a {BLANK} for what to find. Solve it.",
        ),
    ],
)
def test_instruction(
    representation: Representation,
    operations: list[Operation],
    work_box: bool,
    choices: bool,
    two_steps: bool,
    expected: str,
) -> None:
    assert instruction(representation, operations, work_box, choices, two_steps) == expected


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
    ("representation", "choices", "expected"),
    [
        (Representation.STRIP, False, "Word Problems — Strip Diagrams"),
        # text only: no representation to name
        (Representation.NONE, False, "Word Problems"),
        (Representation.NUMBER_LINE, False, "Word Problems — Number Lines"),
        (Representation.BLOCKS, False, "Word Problems — Base-Ten Blocks"),
        (Representation.EQUATION, False, "Word Problems — Equations"),
        # chosen from lettered ones: the name in CHOICE_NAMES
        (Representation.NUMBER_LINE, True, "Word Problems — Number Line multiple choice"),
        (Representation.EQUATION, True, "Word Problems — Equation multiple choice"),
    ],
)
def test_word_problems_title(representation: Representation, choices: bool, expected: str) -> None:
    assert word_problems_title(representation, choices) == expected


@pytest.mark.parametrize(
    ("representations", "responses", "two_steps", "expected"),
    [
        # each representation written, in Representation's order
        (
            [Representation.EQUATION, Representation.STRIP, Representation.BLOCKS],
            [Response.FREE_RESPONSE],
            False,
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                (Representation.BLOCKS, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.FREE_RESPONSE),
            ],
        ),
        # only number lines and equations are chosen
        (
            list(Representation),
            [Response.MULTIPLE_CHOICE],
            False,
            [
                (Representation.NUMBER_LINE, Response.MULTIPLE_CHOICE),
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
            ],
        ),
        # both ways: each representation written, then chosen where it can be
        (
            [Representation.NUMBER_LINE, Representation.STRIP],
            list(Response),
            False,
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                (Representation.NUMBER_LINE, Response.FREE_RESPONSE),
                (Representation.NUMBER_LINE, Response.MULTIPLE_CHOICE),
            ],
        ),
        # two steps: no number lines or blocks, and only equations chosen
        (
            list(Representation),
            list(Response),
            True,
            [
                (Representation.STRIP, Response.FREE_RESPONSE),
                (Representation.NONE, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.FREE_RESPONSE),
                (Representation.EQUATION, Response.MULTIPLE_CHOICE),
            ],
        ),
        # none: blocks aren't chosen
        ([Representation.BLOCKS], [Response.MULTIPLE_CHOICE], False, []),
    ],
)
def test_word_problem_kinds(
    representations: list[Representation],
    responses: list[Response],
    two_steps: bool,
    expected: list[WordProblemKind],
) -> None:
    assert word_problem_kinds(representations, responses, two_steps) == expected
