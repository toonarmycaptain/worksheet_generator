"""
Wording of basic-operation questions: each operation's symbol and name, the equations, and the
questions as the self-check tiles sheet shows them. Also the pictures drawn with word problems,
with their instructions, hints and diagram descriptions.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never

from core.basic_operations.data import (
    BasicOperationQuestionData,
    MissingNumberQuestionData,
    Operation,
    Unknown,
)
from core.question import BLANK
from core.self_check_tiles import TileQuestion

SYMBOLS = {
    Operation.ADD: "+",
    Operation.SUBTRACT: "\N{MINUS SIGN}",
    Operation.MULTIPLY: "\N{MULTIPLICATION SIGN}",
    Operation.DIVIDE: "\N{DIVISION SIGN}",
}

# What a sheet of each operation is called, so its title unless one is given
OPERATION_NAMES = {
    Operation.ADD: "Addition",
    Operation.SUBTRACT: "Subtraction",
    Operation.MULTIPLY: "Multiplication",
    Operation.DIVIDE: "Division",
}


def equation(data: BasicOperationQuestionData) -> str:
    first, second = data.operands
    return f"{first} {SYMBOLS[data.operation]} {second}"


def stem(data: BasicOperationQuestionData) -> str:
    """Return the question's text: its word-problem wording, or its equation followed by "= ?"."""
    if data.question_text is not None:
        return data.question_text
    return f"{equation(data)} = ?"


def basic_operation_tile_question(data: BasicOperationQuestionData) -> TileQuestion:
    """Convert the question to a ``TileQuestion`` for the self-check tiles sheet."""
    return TileQuestion(
        prompt=stem(data), answer=str(data.answer), solution=f"{equation(data)} = {data.answer}"
    )


def missing_number_equation(data: MissingNumberQuestionData, missing: int | str = BLANK) -> str:
    """
    Return the equation with ``missing`` in place of its missing operand.

    By default the gap is a ``BLANK`` (□ ÷ 4 = 7); passing the answer gives the completed
    equation (28 ÷ 4 = 7).
    """
    operands = (missing, data.known) if data.unknown is Unknown.FIRST else (data.known, missing)
    return f"{operands[0]} {SYMBOLS[data.operation]} {operands[1]} = {data.result}"


def missing_number_tile_question(data: MissingNumberQuestionData) -> TileQuestion:
    """Convert the equation to a ``TileQuestion``, with a square for the missing number."""
    return TileQuestion(
        prompt=missing_number_equation(data),
        answer=str(data.answer),
        solution=missing_number_equation(data, data.answer),
    )


class Picture(StrEnum):
    """
    The picture drawn with each word problem on a sheet. Values are stable identifiers for the
    API and storage.
    """

    STRIP = "strip"  # a part-part-whole strip diagram, or bar model
    NONE = "none"  # text only, with a box to show the work
    NUMBER_LINE = "number_line"  # jumps along an open number line
    BLOCKS = "blocks"  # base-ten blocks


# What each picture is called, in a sheet's title and on the web page
PICTURE_NAMES = {
    Picture.STRIP: "Strip Diagrams",
    Picture.NONE: "Text Only",
    Picture.NUMBER_LINE: "Number Lines",
    Picture.BLOCKS: "Base-Ten Blocks",
}

_STRIP_HINTS = {
    Operation.ADD: "Both parts are shown. Add the parts to find the whole.",
    Operation.SUBTRACT: "The whole and one part are shown. Subtract to find the missing part.",
}


class StripUnknown(StrEnum):
    """The value of a strip diagram that is unknown, and shown as "?"."""

    WHOLE = "whole"  # the total, labelled above the bar: an addition's sum
    RIGHT = "right"  # the right-hand part: a subtraction's difference


@dataclass(frozen=True)
class StripDiagram:
    """
    A part-part-whole strip diagram: a bar split into two ``parts``, which together make
    ``whole``.

    Every value is stored, the unknown one included, so that a renderer can size the parts in
    proportion. ``unknown`` identifies the value to show as "?". 47 + 25 is
    ``((47, 25), 72, WHOLE)``, and 72 - 25 is ``((25, 47), 72, RIGHT)``.
    """

    parts: tuple[int, int]
    whole: int
    unknown: StripUnknown


def strip_diagram(data: BasicOperationQuestionData) -> StripDiagram:
    """
    Return the strip diagram for an addition or subtraction question.

    Addition shows its operands as the parts and asks for the whole. Subtraction shows its first
    operand as the whole and its second as the left part, and asks for the right part.
    """
    first, second = data.operands
    match data.operation:
        case Operation.ADD:
            return StripDiagram((first, second), data.answer, StripUnknown.WHOLE)
        case Operation.SUBTRACT:
            return StripDiagram((second, data.answer), first, StripUnknown.RIGHT)
        case Operation.MULTIPLY | Operation.DIVIDE:
            raise NotImplementedError("Strip diagrams are built for + and - only.")
        case _:
            assert_never(data.operation)


def instruction(picture: Picture) -> str:
    """Return the instruction printed under a word-problem sheet's header, for its picture."""
    match picture:
        case Picture.STRIP:
            return (
                "Use the strip diagram (bar model): two parts make a whole. "
                "The ? shows what to find."
            )
        case Picture.NONE | Picture.NUMBER_LINE | Picture.BLOCKS:
            raise NotImplementedError(f"The {picture} picture is not built yet.")
        case _:
            assert_never(picture)


def hint(data: BasicOperationQuestionData, picture: Picture) -> str:
    """Return the hint printed under a word problem, for the picture drawn with it."""
    match picture:
        case Picture.STRIP:
            return _STRIP_HINTS[data.operation]
        case Picture.NONE | Picture.NUMBER_LINE | Picture.BLOCKS:
            raise NotImplementedError(f"The {picture} picture is not built yet.")
        case _:
            assert_never(picture)
