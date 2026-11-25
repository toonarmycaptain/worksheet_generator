"""
What a fractions on a number line question shows: its question as written maths, its choices as
written maths, the answer key's entry, and on a self-check tiles sheet, its tile question.
"""

from typing import assert_never

from core.fraction_models.number_lines import UNIT_NAMES, FractionLine, LengthUnit, Mark
from core.fraction_number_lines.data import (
    GREATER_THAN,
    LESS_THAN,
    Compared,
    CompareQuestionData,
    Comparison,
    DistanceAsked,
    DistanceQuestionData,
    DivideQuestionData,
    FractionNumberLinesQuestionData,
    MarkPointQuestionData,
    NamePointQuestionData,
    QuestionType,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES, DistanceStory
from core.self_check_tiles import TileQuestion
from core.written_numbers import Pieces, inline, merge_pieces

FRACTION_NUMBER_LINES_NAME = "Fractions on a Number Line"
QUESTION_TYPE_NAMES = {
    QuestionType.NAME: "Name the point",
    QuestionType.MARK: "Mark the point",
    QuestionType.DISTANCE: "Distance stories",
    QuestionType.DIVIDE: "Divide the line",
    QuestionType.COMPARE: "Compare distances",
}
# What a whole cut into that many equal parts makes, as "Divide the number line into fourths" says
PART_NAMES = {
    2: "halves",
    3: "thirds",
    4: "fourths",
    5: "fifths",
    6: "sixths",
    7: "sevenths",
    8: "eighths",
    9: "ninths",
    10: "tenths",
    11: "elevenths",
    12: "twelfths",
}

# A question's answer as a tiles bank shows it: written, or a line to find
type TileAnswer = Pieces | FractionLine


def question(data: FractionNumberLinesQuestionData, choices: bool, tiles: bool = False) -> Pieces:
    """
    Return the question as written maths, worded for lettered choices with ``choices``, for a
    self-check tiles sheet with ``tiles``, else for a written answer. Lines are drawn below it,
    not described in it.
    """
    match data:
        case NamePointQuestionData():
            marked = "star" if data.line.points[0].mark is Mark.STAR else "point"
            return (f"What fraction does the {marked} show?",)
        case MarkPointQuestionData():
            if tiles:
                return ("Find the number line with a point at ", data.fraction, ".")
            if choices:
                return ("Which point shows ", data.fraction, "?")
            return ("Mark and label ", data.fraction, " on the number line.")
        case DistanceQuestionData():
            return _distance_question(data, choices)
        case DivideQuestionData():
            parts = _part_name(data.fraction.denominator)
            if choices:
                return (
                    f"Which number line is divided into {parts} with ",
                    data.fraction,
                    " marked?",
                )
            return (f"Divide the number line into {parts}. Mark and label ", data.fraction, ".")
        case CompareQuestionData():
            return _compare_question(data)
        case _:
            assert_never(data)


def solution(data: FractionNumberLinesQuestionData) -> Pieces:
    """Return the answer key's entry: the answer, and how the line shows it."""
    match data:
        case NamePointQuestionData():
            count, total = data.answer.numerator, data.answer.denominator
            return (data.answer, f": {count} of the {total} equal parts from 0")
        case MarkPointQuestionData():
            count, total = data.fraction.numerator, data.fraction.denominator
            return (data.fraction, f": {count} of the {total} equal parts from 0")
        case DistanceQuestionData():
            letter, unit = data.name[0], _unit(data.unit)
            count, total = data.answer.numerator, data.answer.denominator
            parts = f"{count} of the {total} equal parts from 0"
            if data.asked is DistanceAsked.HOW_FAR:
                return (data.answer, f" {unit}: point {letter} is {parts}")
            if data.answer == data.distance:
                return (f"Point {letter} at ", data.answer, f": {parts}")
            return merge_pieces(
                (
                    f"Point {letter} at ",
                    data.answer,
                    f": {parts}, which is ",
                    data.distance,
                    f" {unit}",
                )
            )
        case DivideQuestionData():
            count, total = data.fraction.numerator, data.fraction.denominator
            return (f"{total} equal parts; ", data.fraction, f" is {count} of them from 0")
        case CompareQuestionData():
            return (f"{data.answer}: ", *_true_comparison(data))
        case _:
            assert_never(data)


def answer_unit(data: FractionNumberLinesQuestionData) -> str | None:
    """Return the unit written after a written answer's line, "mile", for a question asking how
    far, else ``None``."""
    if isinstance(data, DistanceQuestionData) and data.asked is DistanceAsked.HOW_FAR:
        return _unit(data.unit)
    return None


def comparison_pieces(comparison: Comparison) -> Pieces:
    """Return a comparison as a choice writes it: "Ben, 5/8 > 3/8"."""
    return (
        f"{comparison.word}, ",
        comparison.left,
        f" {comparison.symbol} ",
        comparison.right,
    )


def tile_answer(data: FractionNumberLinesQuestionData) -> TileAnswer:
    """Return the answer as a tiles bank shows it: the line with the point for a mark question,
    the name or word for a compare question, else the fraction, without its unit."""
    match data:
        case MarkPointQuestionData():
            return data.answer
        case CompareQuestionData():
            return (data.answer,)
        case NamePointQuestionData() | DistanceQuestionData():
            return (data.answer,)
        case DivideQuestionData():
            raise ValueError("A line to divide has no single answer for a tile.")
        case _:
            assert_never(data)


def fraction_number_lines_tile_question(
    data: FractionNumberLinesQuestionData,
) -> TileQuestion[TileAnswer]:
    """
    Convert a question's data to a ``TileQuestion``: the prompt is the question, written inline,
    the answer as the bank shows it, and the solution the answer key's entry, inline.
    """
    return TileQuestion(
        prompt=inline(question(data, choices=False, tiles=True)),
        answer=tile_answer(data),
        solution=inline(solution(data)),
    )


def _part_name(parts: int) -> str:
    """Return what ``parts`` equal parts make, "fourths", or "13 equal parts" past twelfths."""
    return PART_NAMES.get(parts, f"{parts} equal parts")


def _unit(unit: LengthUnit) -> str:
    """Return a unit's name as a fraction of it takes it, singular: "3/4 mile"."""
    return UNIT_NAMES[unit][0]


def _who(story: DistanceStory, name: str) -> str:
    """Return who goes the distance: "Ana", or "Ana's frog"."""
    return f"{name}'s {story.thing}" if story.thing else name


def _second(story: DistanceStory, name: str) -> str:
    """Return the second of two who go a distance, after the first: "Ben", or "Ben's"."""
    return f"{name}'s" if story.thing else name


def _origin(story: DistanceStory) -> str:
    """Return where the distance is from, after a space, " from home", or nothing."""
    return f" {story.origin}" if story.origin else ""


def _distance_question(data: DistanceQuestionData, choices: bool) -> Pieces:
    """Return a distance story's question: how far, mark the point, or which line shows it."""
    story = DISTANCE_STORIES[data.story]
    who, letter = _who(story, data.name), data.name[0]
    where = f"where {who} {story.stopped}"
    if data.asked is DistanceAsked.HOW_FAR:
        return (f"Point {letter} shows {where}. How far{_origin(story)} did {who} {story.go}?",)
    setup = (
        f"{story.scene}{who} {story.went} ",
        data.distance,
        f" {_unit(data.unit)}{_origin(story)}.",
    )
    if choices:
        return merge_pieces((*setup, f" Which number line shows {where}?"))
    return merge_pieces((*setup, f" Mark point {letter} to show {where}."))


def _compare_question(data: CompareQuestionData) -> Pieces:
    """Return a story of two distances: the distances, marking both points, and its question."""
    story = DISTANCE_STORIES[data.story]
    first, second = data.names
    unit = _unit(data.unit)
    went_again = story.went_again or story.went
    match data.compared:
        case Compared.FARTHER:
            asked = f"{_whose(story)} {went_again} farther?"
        case Compared.SHORTER:
            asked = f"{_whose(story)} {went_again} a shorter distance?"
        case Compared.MORE_OR_LESS:
            asked = (
                f"Did {_who(story, first)} {story.go} more or less than {_second(story, second)}?"
            )
        case _:
            assert_never(data.compared)
    return merge_pieces(
        (
            f"{story.scene}{_who(story, first)} {story.went} ",
            data.distances[0],
            f" {unit}{_origin(story)}, and {_second(story, second)} {went_again} ",
            data.distances[1],
            f" {unit}. Mark point {first[0]} for {first} and point {second[0]} for {second}. "
            f"{asked}",
        )
    )


def _whose(story: DistanceStory) -> str:
    """Return how a question asks which of two went farther: "Who", or "Whose frog"."""
    return f"Whose {story.thing}" if story.thing else "Who"


def _true_comparison(data: CompareQuestionData) -> Pieces:
    """Return the comparison that answers a compare question: the answer's distance first, then
    the other's, or for "more or less", the first person's, then the second's."""
    first, second = data.distances
    if data.compared is Compared.MORE_OR_LESS:
        left, right = first, second
    else:
        left, right = (first, second) if data.answer == data.names[0] else (second, first)
    symbol = GREATER_THAN if left.value > right.value else LESS_THAN
    return (left, f" {symbol} ", right)
