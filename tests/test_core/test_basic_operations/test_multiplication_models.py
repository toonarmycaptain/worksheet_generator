"""
The models of multiplication: every wrong model of each kind, the six models a problem's own three
are chosen from, and what each model shows.
"""

import pytest

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.multiplication_models import (
    Array,
    EqualJumpLine,
    MultiplicationModel,
    RepeatedAddition,
    model_description,
    multiplication_model_choices,
    wrong_multiplication_models,
)
from core.basic_operations.representation import EqualStripDiagram, StripDiagram
from core.question import MultipleChoice
from tests.helpers import choice_returns, reverse_shuffle, sample_first


@pytest.mark.parametrize(
    ("groups", "size", "expected"),
    [
        # A row or column too many or too few, or 3 rows of 3; 3 jumps of 3 or 4 of 4; a group
        # too many or too few, 3 groups of 3 or 4 of 4, or 3 and 4 as two parts. 4 groups of 4,
        # the size's own and a group too many, is listed once.
        (
            3,
            4,
            {
                Array(3, 4): (Array(4, 4), Array(2, 4), Array(3, 5), Array(3, 3)),
                EqualJumpLine(3, 4): (EqualJumpLine(3, 3), EqualJumpLine(4, 4)),
                EqualStripDiagram(3, 4, None): (
                    EqualStripDiagram(4, 4, None),
                    EqualStripDiagram(2, 4, None),
                    EqualStripDiagram(3, 3, None),
                    StripDiagram((3, 4), None),
                ),
                RepeatedAddition((4, 4, 4)): (
                    RepeatedAddition((4, 4, 4, 4)),
                    RepeatedAddition((4, 4)),
                    RepeatedAddition((3, 3, 3)),
                    RepeatedAddition((3, 4)),
                ),
            },
        ),
        # A square: 4 groups of 4 is its own, so the number line has a jump too many or too few
        # instead, and there are no two parts. An array with a row too many looks the same as one
        # with a column too many, so it's listed once, as is one too few.
        (
            4,
            4,
            {
                Array(4, 4): (Array(5, 4), Array(3, 4)),
                EqualJumpLine(4, 4): (EqualJumpLine(5, 4), EqualJumpLine(3, 4)),
                EqualStripDiagram(4, 4, None): (
                    EqualStripDiagram(5, 4, None),
                    EqualStripDiagram(3, 4, None),
                ),
                RepeatedAddition((4, 4, 4, 4)): (
                    RepeatedAddition((4, 4, 4, 4, 4)),
                    RepeatedAddition((4, 4, 4)),
                ),
            },
        ),
        # 2 groups: one group too few would be 1 group
        (
            2,
            5,
            {
                Array(2, 5): (Array(3, 5), Array(2, 6), Array(2, 4), Array(2, 2)),
                EqualJumpLine(2, 5): (EqualJumpLine(2, 2), EqualJumpLine(5, 5)),
                EqualStripDiagram(2, 5, None): (
                    EqualStripDiagram(3, 5, None),
                    EqualStripDiagram(2, 2, None),
                    EqualStripDiagram(5, 5, None),
                    StripDiagram((2, 5), None),
                ),
                RepeatedAddition((5, 5)): (
                    RepeatedAddition((5, 5, 5)),
                    RepeatedAddition((2, 2)),
                    RepeatedAddition((5, 5, 5, 5, 5)),
                    RepeatedAddition((2, 5)),
                ),
            },
        ),
        # groups of 2: an array with a column too few would have columns of 1
        (
            5,
            2,
            {
                Array(5, 2): (Array(6, 2), Array(4, 2), Array(5, 3), Array(5, 5)),
                EqualJumpLine(5, 2): (EqualJumpLine(5, 5), EqualJumpLine(2, 2)),
                EqualStripDiagram(5, 2, None): (
                    EqualStripDiagram(6, 2, None),
                    EqualStripDiagram(4, 2, None),
                    EqualStripDiagram(5, 5, None),
                    EqualStripDiagram(2, 2, None),
                    StripDiagram((5, 2), None),
                ),
                RepeatedAddition((2, 2, 2, 2, 2)): (
                    RepeatedAddition((2, 2, 2, 2, 2, 2)),
                    RepeatedAddition((2, 2, 2, 2)),
                    RepeatedAddition((5, 5, 5, 5, 5)),
                    RepeatedAddition((2, 2)),
                    RepeatedAddition((5, 2)),
                ),
            },
        ),
        # 2 groups of 2, which a sheet leaves out: every mistake but a group too many gives back
        # its own model, or 1 group
        (
            2,
            2,
            {
                Array(2, 2): (Array(3, 2),),
                EqualJumpLine(2, 2): (EqualJumpLine(3, 2),),
                EqualStripDiagram(2, 2, None): (EqualStripDiagram(3, 2, None),),
                RepeatedAddition((2, 2)): (RepeatedAddition((2, 2, 2)),),
            },
        ),
    ],
)
def test_wrong_multiplication_models(
    groups: int,
    size: int,
    expected: dict[MultiplicationModel, tuple[MultiplicationModel, ...]],
) -> None:
    """
    Each of the four models of the problem, with every wrong model of its kind: none is its own
    model or its turn, has fewer than 2 groups or groups of fewer than 2, or repeats another, an
    array and its turn counting as the same.
    """
    assert wrong_multiplication_models(groups, size) == expected


@pytest.mark.parametrize(
    ("data", "picks", "expected"),
    [
        # The array is left out, so the wrong models are an array, a number line and a strip.
        # The wrong array, 2 rows of 4, is drawn turned round.
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
            [
                Array(3, 4),
                Array(2, 4),
                EqualJumpLine(4, 4),
                StripDiagram((3, 4), None),
                Array(4, 2),
            ],
            MultipleChoice(
                (
                    StripDiagram((3, 4), None),
                    EqualJumpLine(4, 4),
                    Array(4, 2),
                    RepeatedAddition((4, 4, 4)),
                    EqualStripDiagram(3, 4, None),
                    EqualJumpLine(3, 4),
                ),
                frozenset({3, 4, 5}),
            ),
        ),
        # The repeated addition is left out, so the wrong models are a repeated addition, an
        # array and a number line. The problem's own array is drawn as it is, and the wrong one,
        # 3 rows of 5, turned round.
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (3, 4), 12),
            [
                RepeatedAddition((4, 4, 4)),
                RepeatedAddition((3, 4)),
                Array(3, 5),
                EqualJumpLine(3, 3),
                Array(3, 4),
                Array(5, 3),
            ],
            MultipleChoice(
                (
                    EqualJumpLine(3, 3),
                    Array(5, 3),
                    RepeatedAddition((3, 4)),
                    EqualStripDiagram(3, 4, None),
                    EqualJumpLine(3, 4),
                    Array(3, 4),
                ),
                frozenset({3, 4, 5}),
            ),
        ),
        # The number line is left out, so the wrong models are a number line, an array and a
        # strip. The problem's own array, with a side of 8, lies on its side with no draw, and
        # the wrong one, with a side of 7, is drawn either way round, here as it is, 7 rows of 3.
        (
            BasicOperationQuestionData(Operation.MULTIPLY, (8, 3), 24),
            [
                EqualJumpLine(8, 3),
                EqualJumpLine(3, 3),
                Array(7, 3),
                EqualStripDiagram(9, 3, None),
                Array(7, 3),
            ],
            MultipleChoice(
                (
                    EqualStripDiagram(9, 3, None),
                    Array(7, 3),
                    EqualJumpLine(3, 3),
                    RepeatedAddition((3, 3, 3, 3, 3, 3, 3, 3)),
                    EqualStripDiagram(8, 3, None),
                    Array(3, 8),
                ),
                frozenset({3, 4, 5}),
            ),
        ),
    ],
)
def test_multiplication_model_choices(
    data: BasicOperationQuestionData,
    picks: list[MultiplicationModel],
    expected: MultipleChoice[MultiplicationModel],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Three of the problem's four models are choices, and the one left out has a wrong model of its
    kind, as do two of the other three. Each wrong model is one of its kind's from
    ``wrong_multiplication_models``. An array is drawn either way round, unless it has a side
    longer than 7, when it lies on its side.

    ``choice`` returns ``picks``, each from the items it's offered, in the order drawn: the model
    left out, the wrong model of each kind, then each array's way round, the problem's own first.
    ``sample`` takes the first two of the other three kinds, and ``shuffle`` reverses, so the
    wrong models come last drawn first, and the problem's own three are last.
    """
    choice_returns(monkeypatch, picks)
    sample_first(monkeypatch)
    reverse_shuffle(monkeypatch)
    assert multiplication_model_choices(data) == expected


@pytest.mark.parametrize(
    "data",
    [
        BasicOperationQuestionData(Operation.DIVIDE, (12, 3), 4),
        BasicOperationQuestionData(Operation.MULTIPLY, (1, 5), 5),
        BasicOperationQuestionData(Operation.MULTIPLY, (5, 1), 5),
    ],
)
def test_multiplication_model_choices_errors(data: BasicOperationQuestionData) -> None:
    with pytest.raises(ValueError) as error:
        multiplication_model_choices(data)
    assert str(error.value) == "Models show a multiplication of at least 2 groups of at least 2."


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        (Array(5, 6), "array has 5 rows of 6"),
        (EqualJumpLine(4, 6), "number line shows 4 jumps of 6"),
        (EqualStripDiagram(4, 6, None), "tape shows 4 parts of 6"),
        (StripDiagram((4, 6), None), "tape has parts 4 and 6"),
        (RepeatedAddition((6, 6, 6, 6)), "adds 6 a total of 4 times"),
        (RepeatedAddition((4, 6)), "adds 4 + 6"),
    ],
)
def test_model_description(model: MultiplicationModel, expected: str) -> None:
    assert model_description(model) == expected
