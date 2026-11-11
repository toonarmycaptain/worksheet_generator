"""
Models of multiplication, and the models a word problem's own are chosen from.

A multiplication of equal groups is shown as an array, as equal jumps along a number line, as a
strip diagram, or as repeated addition. Three of a problem's choices are its own models, each of
a different kind, and three are wrong, each showing one mistake with the problem's numbers, as
the legacy multiplication sheet makes them.
"""

import random
from collections.abc import Iterable
from dataclasses import dataclass
from typing import assert_never

from core.basic_operations.data import BasicOperationQuestionData, Operation
from core.basic_operations.representation import EqualStripDiagram, StripDiagram
from core.question import MultipleChoice, Question, multiple_choice

# A multiplication-models sheet's title unless one is given
MULTIPLICATION_MODELS_NAME = "Multiplication Models multiple choice"
MULTIPLICATION_MODELS_INSTRUCTION = (
    "Each problem has 6 models. Exactly 3 match the story. The ? is the total."
)
# An array with a side longer than this lies on its side, with its shorter side as its rows, so
# that its rows fit and can be counted. Other arrays are drawn either way round.
LONGEST_TURNABLE_SIDE = 7


@dataclass(frozen=True)
class Array:
    """An array of dots: ``rows`` rows of ``columns`` dots each."""

    rows: int
    columns: int


@dataclass(frozen=True)
class EqualJumpLine:
    """
    A number line from 0 with ``jumps`` equal jumps of ``size``. Its ticks are labelled 0, then
    each landing, with the last, the total, as "?".
    """

    jumps: int
    size: int


@dataclass(frozen=True)
class RepeatedAddition:
    """An addition of ``addends`` with its total to find, as in 4 + 4 + 4 = ?."""

    addends: tuple[int, ...]


# A model of multiplication. Its strip diagram is equal groups, or two parts for a wrong one.
type MultiplicationModel = (
    Array | EqualJumpLine | EqualStripDiagram | StripDiagram | RepeatedAddition
)
# A word problem as presented: three of its models chosen from six
type MultiplicationModelsQuestion = Question[
    BasicOperationQuestionData, MultipleChoice[MultiplicationModel]
]


def multiplication_model_choices(
    data: BasicOperationQuestionData,
) -> MultipleChoice[MultiplicationModel]:
    """
    Return the models to choose from for a multiplication: three of its own, each of a different
    kind, and three wrong ones from ``wrong_multiplication_models``.

    One of its four models is left out, drawn at random, and a wrong model of its kind is drawn,
    as is one of each of two of its other three kinds. So a kind shown twice is right once and
    wrong once, and how often a kind is shown says nothing about whether it's right. An array is
    drawn either way round, as ``_turned`` gives it.

    A multiplication needs at least 2 groups of at least 2, and any other operation raises
    ``ValueError``. 2 groups of 2 has one wrong model of each kind, 3 groups of 2, so a sheet of
    these choices leaves it out.
    """
    if data.operation is not Operation.MULTIPLY or min(data.operands) < 2:
        raise ValueError("Models show a multiplication of at least 2 groups of at least 2.")
    wrong_models = wrong_multiplication_models(*data.operands)
    left_out = random.choice(tuple(wrong_models))
    own = [model for model in wrong_models if model != left_out]
    wrong = [random.choice(wrong_models[model]) for model in [left_out, *random.sample(own, 2)]]
    return multiple_choice(tuple(map(_turned, own)), tuple(map(_turned, wrong)))


def wrong_multiplication_models(
    groups: int, size: int
) -> dict[MultiplicationModel, tuple[MultiplicationModel, ...]]:
    """
    Return each of the four models of ``groups`` groups of ``size``, with every wrong model of
    its kind, each showing one mistake with the problem's numbers:

    - an array: a row or a column too many or too few, or ``groups`` rows of ``groups``;
    - a number line: ``groups`` jumps of ``groups``, or ``size`` jumps of ``size``. Its jumps are
      numbered and its ticks labelled, so both its numbers show, and both are the story's. When
      ``groups`` and ``size`` are the same, those are its own line, so it has a jump too many or
      too few instead;
    - a strip diagram or repeated addition: a group too many or too few, ``groups`` groups of
      ``groups``, ``size`` groups of ``size``, or the two numbers as two parts, unless they're the
      same, when that would be 2 equal groups.

    None is the problem's own model, or its own turned round (``size`` groups of ``groups``), or
    has fewer than 2 groups or groups of fewer than 2. An array turned round looks the same, so
    each array is listed once.
    """
    more_or_fewer = [(groups + 1, size), (groups - 1, size)]
    same = [(groups, groups), (size, size)]
    arrays = [*more_or_fewer, (groups, size + 1), (groups, size - 1), (groups, groups)]
    lines = same if groups != size else more_or_fewer
    equal_groups = _kept([*more_or_fewer, *same], groups, size)
    two_parts = groups != size
    return {
        Array(groups, size): tuple(
            Array(*pair) for pair in _kept(arrays, groups, size, turns_alike=True)
        ),
        EqualJumpLine(groups, size): tuple(
            EqualJumpLine(*pair) for pair in _kept(lines, groups, size)
        ),
        EqualStripDiagram(groups, size, None): (
            *(EqualStripDiagram(*pair, None) for pair in equal_groups),
            *([StripDiagram((groups, size), None)] if two_parts else []),
        ),
        RepeatedAddition((size,) * groups): (
            *(
                RepeatedAddition((other_size,) * other_groups)
                for other_groups, other_size in equal_groups
            ),
            *([RepeatedAddition((groups, size))] if two_parts else []),
        ),
    }


def _kept(
    pairs: Iterable[tuple[int, int]], groups: int, size: int, turns_alike: bool = False
) -> list[tuple[int, int]]:
    """
    Return ``pairs`` of a number of groups and a size, in order, leaving out any with fewer than
    2 groups or groups of fewer than 2, any that is ``groups`` groups of ``size`` or its turn,
    and any repeat. With ``turns_alike``, a pair and its turn are repeats, as an array and its turn
    look the same.
    """
    own = {(groups, size), (size, groups)}
    kept: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for pair in pairs:
        looks = (min(pair), max(pair)) if turns_alike else pair
        if min(pair) >= 2 and pair not in own and looks not in seen:
            seen.add(looks)
            kept.append(pair)
    return kept


def _turned(model: MultiplicationModel) -> MultiplicationModel:
    """
    Return ``model``, turned round at random if it's an array. An array with a side longer than
    ``LONGEST_TURNABLE_SIDE`` lies on its side instead, with its shorter side as its rows.
    """
    if not isinstance(model, Array):
        return model
    shorter, longer = sorted((model.rows, model.columns))
    if longer > LONGEST_TURNABLE_SIDE:
        return Array(shorter, longer)
    return random.choice((model, Array(model.columns, model.rows)))


def model_description(model: MultiplicationModel) -> str:
    """
    Return what ``model`` shows, as an answer key gives a wrong model's mistake: "array has 5 rows
    of 6", or "adds 4 + 6".
    """
    match model:
        case Array(rows, columns):
            return f"array has {rows} rows of {columns}"
        case EqualJumpLine(jumps, size):
            return f"number line shows {jumps} jumps of {size}"
        case EqualStripDiagram(groups, size):
            return f"tape shows {groups} parts of {size}"
        case StripDiagram((first, second)):
            return f"tape has parts {first} and {second}"
        case RepeatedAddition(addends) if len(set(addends)) == 1:
            return f"adds {addends[0]} a total of {len(addends)} times"
        case RepeatedAddition(addends):
            return "adds " + " + ".join(str(addend) for addend in addends)
        case _:
            assert_never(model)
