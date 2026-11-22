"""
Tests for the choices of data-set questions: displays and lists of counts, statements of an
error, displays that don't all match, and word problems' numbers.

The tests script ``random``: ``sample`` returns the picks listed, ``choice`` returns the picks
listed and records what it was offered, ``randint`` and ``random`` return the values listed,
and ``shuffle`` reverses. So a question's options come out in reverse order of how they're
made: for a display or a list, both mistakes, the second alone, the first alone, then the right
one.

A pair of mistakes is drawn last first: of the pairs of the kinds drawn, the one made from the
last mistake of the first kind and the last of the second that changes other counts, unless its
choices don't fit or look alike.
"""

from dataclasses import replace

import pytest

from core.discrete_data.data import (
    CategoricalData,
    CategoricalDataProblemData,
    CategoricalProblemType,
    DataDisplay,
    DisplayChoice,
    DisplayMistake,
    ErrorChoice,
    EveryTick,
    FindErrorQuestionData,
    NumericalData,
    NumericalDataProblemData,
    NumericalProblemType,
    Off,
    OneEach,
    ReadCountsQuestionData,
    RoundDown,
    ShownDisplay,
    SummarizeDataQuestionData,
    Swap,
    WrongScale,
)
from core.discrete_data.wrong_answers import (
    count_choices,
    display_choices,
    doesnt_match_choices,
    error_choices,
    number_choices,
    wrong_display,
)
from core.question import MultipleChoice
from tests.data import CLASSES, FRUIT
from tests.helpers import (
    choice_returns,
    randint_returns,
    random_returns,
    reverse_shuffle,
    sample_first,
    sample_returns,
)

TABLE, TALLY_TABLE, PICTOGRAPH, BAR_GRAPH, DOT_PLOT, LIST, NUMBER_LINE_DOT_PLOT = (
    DataDisplay  # enum order
)
type MistakeKinds = tuple[type[DisplayMistake], type[DisplayMistake]]

# A survey with a scale of 2: bananas' 5 and grapes' 9 fall between steps
FRUIT_DATA = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes", "pears"),
    counts=(12, 5, 9, 4),
    scale=2,
    person="Ana",
)
# the same with every count on a step, so nothing falls between them
EVEN_FRUIT_DATA = replace(FRUIT_DATA, counts=(12, 6, 8, 4))
# 18 three times, 20 twice, 21 and 23 once, and 19 and 22 not at all
CLASSES_DATA = NumericalData(
    topic=CLASSES,
    values=(18, 20, 18, 21, 20, 18, 23),
    ticks=(18, 19, 20, 21, 22, 23),
    person="Eve",
)
# counts in sixes, as displays that don't all match have them
MATCH_DATA = CategoricalData(
    topic=FRUIT,
    categories=("apples", "bananas", "grapes"),
    counts=(6, 12, 18),
    scale=6,
    person="Ana",
)

FRUIT_ANSWER = DisplayChoice((12, 5, 9, 4), 2, ())
LINE_ANSWER = DisplayChoice((3, 0, 2, 1, 0, 1), 1, ())
TO_BAR_GRAPH = SummarizeDataQuestionData(FRUIT_DATA, TABLE, BAR_GRAPH, (0, 1, 2, 3), (12, 5, 9, 4))
TO_LINE = SummarizeDataQuestionData(
    CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, (0, 1, 2, 3, 4, 5), (3, 0, 2, 1, 0, 1)
)


@pytest.mark.parametrize(
    ("data", "kinds", "expected"),
    [
        # Grapes and pears switched, and bananas' 5 shown as 7: each count and the scale is
        # right in two of the four, or in all four.
        (
            TO_BAR_GRAPH,
            [(Swap, Off), (Swap, Swap), (Off, Off), (Swap, WrongScale), (Swap, RoundDown)],
            MultipleChoice(
                (
                    DisplayChoice((12, 7, 4, 9), 2, (Swap(2, 3), Off(1, 7))),
                    DisplayChoice((12, 7, 9, 4), 2, (Off(1, 7),)),
                    DisplayChoice((12, 5, 4, 9), 2, (Swap(2, 3),)),
                    FRUIT_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        (
            TO_BAR_GRAPH,
            [(Swap, Swap), (Swap, Off), (Off, Off), (Swap, WrongScale), (Swap, RoundDown)],
            MultipleChoice(
                (
                    DisplayChoice((5, 12, 4, 9), 2, (Swap(2, 3), Swap(0, 1))),
                    DisplayChoice((5, 12, 9, 4), 2, (Swap(0, 1),)),
                    DisplayChoice((12, 5, 4, 9), 2, (Swap(2, 3),)),
                    FRUIT_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # pears' 4 shown as 6, and grapes' 9 as 11
        (
            TO_BAR_GRAPH,
            [(Off, Off), (Swap, Off), (Swap, Swap), (Swap, WrongScale), (Swap, RoundDown)],
            MultipleChoice(
                (
                    DisplayChoice((12, 5, 11, 6), 2, (Off(3, 6), Off(2, 11))),
                    DisplayChoice((12, 5, 11, 4), 2, (Off(2, 11),)),
                    DisplayChoice((12, 5, 9, 6), 2, (Off(3, 6),)),
                    FRUIT_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # a scale of 10: the same bars, read five times too high
        (
            TO_BAR_GRAPH,
            [(Swap, WrongScale), (Swap, Off), (Swap, Swap), (Off, Off), (Swap, RoundDown)],
            MultipleChoice(
                (
                    DisplayChoice((60, 25, 20, 45), 10, (Swap(2, 3), WrongScale(10))),
                    DisplayChoice((60, 25, 45, 20), 10, (WrongScale(10),)),
                    DisplayChoice((12, 5, 4, 9), 2, (Swap(2, 3),)),
                    FRUIT_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # bananas' 5 and grapes' 9 taken at the step below
        (
            TO_BAR_GRAPH,
            [(Swap, RoundDown), (Swap, Off), (Swap, Swap), (Off, Off), (Swap, WrongScale)],
            MultipleChoice(
                (
                    DisplayChoice((12, 4, 4, 8), 2, (Swap(2, 3), RoundDown())),
                    DisplayChoice((12, 4, 8, 4), 2, (RoundDown(),)),
                    DisplayChoice((12, 5, 4, 9), 2, (Swap(2, 3),)),
                    FRUIT_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # with every count on a step, nothing rounds down, so the next kinds are drawn
        (
            replace(TO_BAR_GRAPH, dataset=EVEN_FRUIT_DATA, answer=(12, 6, 8, 4)),
            [(Swap, RoundDown), (Swap, Swap), (Swap, Off), (Off, Off), (Swap, WrongScale)],
            MultipleChoice(
                (
                    DisplayChoice((6, 12, 4, 8), 2, (Swap(2, 3), Swap(0, 1))),
                    DisplayChoice((6, 12, 8, 4), 2, (Swap(0, 1),)),
                    DisplayChoice((12, 6, 4, 8), 2, (Swap(2, 3),)),
                    DisplayChoice((12, 6, 8, 4), 2, ()),
                ),
                frozenset({3}),
            ),
        ),
        # On a number line: the Xs for 22 and 23 switched, and 21's 1 X shown as 2. Only
        # numbers whose counts differ are switched.
        (
            TO_LINE,
            [(Swap, Off), (Swap, Swap), (Off, Off), (OneEach, Off), (EveryTick, Off)],
            MultipleChoice(
                (
                    DisplayChoice((3, 0, 2, 2, 1, 0), 1, (Swap(4, 5), Off(3, 2))),
                    DisplayChoice((3, 0, 2, 2, 0, 1), 1, (Off(3, 2),)),
                    DisplayChoice((3, 0, 2, 1, 1, 0), 1, (Swap(4, 5),)),
                    LINE_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # One X for each number, and 23 left out. 23 shown with 2 Xs is drawn first, but one X
        # each would hide it.
        (
            TO_LINE,
            [(OneEach, Off), (Swap, Off), (Swap, Swap), (Off, Off), (EveryTick, Off)],
            MultipleChoice(
                (
                    DisplayChoice((1, 0, 1, 1, 0, 0), 1, (OneEach(), Off(5, 0))),
                    DisplayChoice((3, 0, 2, 1, 0, 0), 1, (Off(5, 0),)),
                    DisplayChoice((1, 0, 1, 1, 0, 1), 1, (OneEach(),)),
                    LINE_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
        # One X above every number, and 23 shown with 2 Xs: every number keeps its 1 X where
        # it has one, so the off count must be at one of those, 21 or 23.
        (
            TO_LINE,
            [(EveryTick, Off), (Swap, Off), (Swap, Swap), (Off, Off), (OneEach, Off)],
            MultipleChoice(
                (
                    DisplayChoice((1, 1, 1, 1, 1, 2), 1, (EveryTick(), Off(5, 2))),
                    DisplayChoice((3, 0, 2, 1, 0, 2), 1, (Off(5, 2),)),
                    DisplayChoice((1, 1, 1, 1, 1, 1), 1, (EveryTick(),)),
                    LINE_ANSWER,
                ),
                frozenset({3}),
            ),
        ),
    ],
)
def test_display_choices(
    data: SummarizeDataQuestionData,
    kinds: list[MistakeKinds],
    expected: MultipleChoice[DisplayChoice],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A display's four choices: the right one, each of two mistakes alone, and both, the pair's
    kinds drawn first (``kinds``, in the order drawn).
    """
    sample_returns(monkeypatch, [kinds])
    reverse_shuffle(monkeypatch)

    assert display_choices(data) == expected


def test_count_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    A list of counts read from a pictograph is chosen the same way: grapes and pears switched,
    and the key read as 10, not 2. A list shows no scale, so only its counts must differ.
    """
    sample_returns(
        monkeypatch,
        [[(Swap, WrongScale), (Swap, Off), (Swap, Swap), (Off, Off), (Swap, RoundDown)]],
    )
    reverse_shuffle(monkeypatch)

    choices = count_choices(ReadCountsQuestionData(FRUIT_DATA, PICTOGRAPH, (12, 5, 9, 4)))

    assert choices == MultipleChoice(
        (
            DisplayChoice((60, 25, 20, 45), 10, (Swap(2, 3), WrongScale(10))),
            DisplayChoice((60, 25, 45, 20), 10, (WrongScale(10),)),
            DisplayChoice((12, 5, 4, 9), 2, (Swap(2, 3),)),
            FRUIT_ANSWER,
        ),
        frozenset({3}),
    )


@pytest.mark.parametrize(
    ("data", "randoms", "picks", "expected", "offered"),
    [
        # Bananas' 5 shown as 7. The other category is grapes, picked from those whose counts
        # stay above 0 a step either way: all but bananas. Bananas' wrong count is 6, a step
        # from 5 but not the 7 shown; grapes' are 10 and 8.
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, None, 1, 7, 5),
            [],
            [2],
            MultipleChoice(
                (
                    ErrorChoice(PICTOGRAPH, 2, 8),
                    ErrorChoice(PICTOGRAPH, 2, 10),
                    ErrorChoice(PICTOGRAPH, 1, 6),
                    ErrorChoice(PICTOGRAPH, 1, 5),
                ),
                frozenset({3}),
            ),
            [[0, 2, 3]],
        ),
        # With a second display, each display and each category is named twice. Each wrong
        # count is a step from the right one, up for a draw under 0.5 and down otherwise.
        (
            FindErrorQuestionData(FRUIT_DATA, TABLE, PICTOGRAPH, BAR_GRAPH, 1, 7, 5),
            [0.4, 0.6, 0.4],
            [3],
            MultipleChoice(
                (
                    ErrorChoice(BAR_GRAPH, 3, 5),
                    ErrorChoice(BAR_GRAPH, 1, 4),
                    ErrorChoice(PICTOGRAPH, 3, 5),
                    ErrorChoice(PICTOGRAPH, 1, 5),
                ),
                frozenset({3}),
            ),
            [[0, 2, 3]],
        ),
        # On a number line, a number with no Xs isn't named, as both ways would give 1.
        (
            FindErrorQuestionData(CLASSES_DATA, LIST, NUMBER_LINE_DOT_PLOT, None, 0, 2, 3),
            [],
            [3],
            MultipleChoice(
                (
                    ErrorChoice(NUMBER_LINE_DOT_PLOT, 3, 0),
                    ErrorChoice(NUMBER_LINE_DOT_PLOT, 3, 2),
                    ErrorChoice(NUMBER_LINE_DOT_PLOT, 0, 4),
                    ErrorChoice(NUMBER_LINE_DOT_PLOT, 0, 3),
                ),
                frozenset({3}),
            ),
            [[2, 3, 5]],
        ),
    ],
)
def test_error_choices(
    data: FindErrorQuestionData,
    randoms: list[float],
    picks: list[int],
    expected: MultipleChoice[ErrorChoice],
    offered: list[list[int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Four statements of an error: the right one, and others naming a count no display shows
    there, so none is ruled out by its display alone. ``offered`` is the other categories the
    draw could name.
    """
    random_returns(monkeypatch, randoms)
    offers = choice_returns(monkeypatch, picks)
    reverse_shuffle(monkeypatch)

    assert (error_choices(data), offers) == (expected, offered)


@pytest.mark.parametrize(
    ("display", "scale", "picks", "kinds"),
    [
        # A pictograph keyed 12 can be keyed 2 or 10 and still show whole symbols, not 1 or 5;
        # rounding down would leave apples' 6 at 0.
        (
            PICTOGRAPH,
            12,
            [WrongScale, DisplayChoice((5, 10, 15), 10, (WrongScale(10),))],
            [Swap, Off, WrongScale],
        ),
        # a tally table has no scale to misread, and its counts go a mark or two off
        (TALLY_TABLE, 6, [Off, DisplayChoice((6, 12, 17), 6, (Off(2, 17),))], [Swap, Off]),
    ],
)
def test_wrong_display(
    display: DataDisplay,
    scale: int,
    picks: list[object],
    kinds: list[type[DisplayMistake]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A display with one mistake, its kind drawn first from ``kinds``, those that fit the display
    and change what it shows, then the mistake.
    """
    offers = choice_returns(monkeypatch, picks)

    shown = wrong_display(MATCH_DATA, display, scale)

    assert (shown, offers[0]) == (picks[1], kinds)


SHOWN = (
    ShownDisplay(BAR_GRAPH, 6, DisplayChoice((6, 12, 18), 6, (Swap(0, 1),))),
    ShownDisplay(PICTOGRAPH, 12, DisplayChoice((6, 12, 18), 12, ())),
    ShownDisplay(DOT_PLOT, 6, DisplayChoice((6, 12, 18), 6, ())),
    ShownDisplay(BAR_GRAPH, 3, DisplayChoice((6, 12, 18), 3, ())),
)


@pytest.mark.parametrize(
    ("wrong", "expected"),
    [
        (0, MultipleChoice((SHOWN[3], SHOWN[2], SHOWN[1], SHOWN[0]), frozenset({3}))),
        (2, MultipleChoice((SHOWN[3], SHOWN[1], SHOWN[0], SHOWN[2]), frozenset({3}))),
    ],
)
def test_doesnt_match_choices(
    wrong: int, expected: MultipleChoice[ShownDisplay], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The displays shuffled, the one at ``wrong`` the answer."""
    reverse_shuffle(monkeypatch)

    assert doesnt_match_choices(SHOWN, wrong) == expected


@pytest.mark.parametrize(
    ("data", "drawn", "expected", "bounds"),
    [
        # Apples' 12 less bananas' 5. Its mistakes: adding (17), one category alone (12 or 5),
        # and a step off (8 or 6). The answer's place by size is drawn first, here third
        # smallest: two numbers below it, one above.
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 1), 7),
            [2],
            MultipleChoice((17, 6, 5, 7), frozenset({3})),
            [(0, 3)],
        ),
        # the smallest: three above
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 1), 7),
            [0],
            MultipleChoice((8, 12, 17, 7), frozenset({3})),
            [(0, 3)],
        ),
        # the largest: the two mistakes below, padded with the nearest number not taken, 4
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (0, 1), 7),
            [3],
            MultipleChoice((4, 6, 5, 7), frozenset({3})),
            [(0, 3)],
        ),
        # An answer of 1 has only 0 below it, so it's at most second smallest.
        (
            CategoricalDataProblemData(FRUIT_DATA, CategoricalProblemType.MORE, (1, 3), 1),
            [1],
            MultipleChoice((5, 9, 0, 1), frozenset({3})),
            [(0, 1)],
        ),
        # A missing number's mistakes: the listed numbers' total, 138, and a tick or two off.
        (
            NumericalDataProblemData(CLASSES_DATA, NumericalProblemType.MISSING_VALUE, (), 19, 157),
            [1],
            MultipleChoice((20, 138, 18, 19), frozenset({3})),
            [(0, 3)],
        ),
    ],
)
def test_number_choices(
    data: CategoricalDataProblemData | NumericalDataProblemData,
    drawn: list[int],
    expected: MultipleChoice[int],
    bounds: list[tuple[int, int]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    A problem's answer and three wrong numbers from its mistakes. ``bounds`` is the range the
    answer's place by size was drawn from.
    """
    calls = randint_returns(monkeypatch, drawn)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)

    assert (number_choices(data), calls) == (expected, bounds)
