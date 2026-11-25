"""
What a naming fractions question shows: its question as written maths, the answer key's entry,
the names of the wholes its pictures show, and on a self-check tiles sheet, its tile question.
"""

from typing import assert_never

from core.drawn_objects import OBJECT_NAMES
from core.fraction_models.area_models import (
    HALF_HEXAGON,
    PARALLELOGRAM,
    REGULAR_HEXAGON,
    RHOMBUS,
    AreaModel,
    Circle,
    ConcaveOctagon,
    CutShape,
    Grid,
    Lattice,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Split,
    Strip,
    TriangleGrid,
)
from core.fraction_models.object_groups import ObjectGroup
from core.naming_fractions.data import (
    Asked,
    DrawSharesQuestionData,
    NameQuestionData,
    NamingFractionsQuestionData,
    People,
    Picture,
    QuestionType,
    Representation,
    ShadeQuestionData,
    ShareQuestionData,
)
from core.naming_fractions.stories import GROUP_STORIES, WHOLE_STORIES
from core.self_check_tiles import TileQuestion
from core.written_numbers import Pieces, inline

NAMING_FRACTIONS_NAME = "Naming Fractions"
QUESTION_TYPE_NAMES = {
    QuestionType.NAME: "Name the fraction",
    QuestionType.SHADE: "Shade the fraction",
    QuestionType.SHARE: "Share equally",
    QuestionType.DRAW_SHARES: "Draw the shares",
}
REPRESENTATION_NAMES = {
    Representation.STRIP: "Strips",
    Representation.GRID: "Grids",
    Representation.CIRCLE: "Circles",
    Representation.OTHER_SHAPE: "Other shapes",
    Representation.GROUP: "Groups of objects",
}
CIRCLE_SHARE = "Circle each person's share."  # under a written sharing story's picture
NUMBER_WORDS = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
# The names of regular polygons, by their sides
POLYGON_NAMES = {3: "triangle", 4: "square", 5: "pentagon", 6: "hexagon", 8: "octagon"}

# A naming fractions question's answer as a tiles bank shows it: written, or a picture
type TileAnswer = Pieces | Picture


def question(data: NamingFractionsQuestionData, choices: bool, tiles: bool = False) -> Pieces:
    """
    Return the question as written maths, worded for lettered choices with ``choices``, for a
    self-check tiles sheet with ``tiles``, else for a written answer. Pictures are drawn below
    it, not described in it.
    """
    match data:
        case NameQuestionData():
            shaded = "NOT shaded" if data.unshaded else "shaded"
            if isinstance(data.picture, ObjectGroup):
                return (f"What fraction of the {_objects(data.picture)} are {shaded}?",)
            return (f"What fraction of the {whole_name(data.picture.split)} is {shaded}?",)
        case ShadeQuestionData():
            fraction = data.fraction
            if tiles:
                return ("Find the picture that shows ", fraction, ".")
            if choices:
                return ("Which model shows ", fraction, " shaded?")
            if data.divide and isinstance(data.answer, AreaModel):
                name = whole_name(data.answer.split)
                return (
                    f"Divide the {name} into {fraction.denominator} equal parts. Shade "
                    f"{fraction.numerator} of them.",
                )
            if isinstance(data.picture, ObjectGroup):
                return ("Shade ", fraction, f" of the {_objects(data.picture)}.")
            return ("Shade ", fraction, f" of the {whole_name(data.picture.split)}.")
        case ShareQuestionData():
            sentences = [_share_setup(data), _asked(data, data.people, data.asked, data.together)]
            if data.picture is not None and not choices and not tiles:
                sentences.append(CIRCLE_SHARE)
            return (" ".join(filter(None, sentences)),)
        case DrawSharesQuestionData():
            story = WHOLE_STORIES[data.story]
            setup = _capitalised(story.setup.format(people=_people(data.people)))
            asked = _asked(data, data.people, data.asked, data.together)
            return (f"{setup} Draw lines to show the shares. {asked}",)
        case _:
            assert_never(data)


def solution(data: NamingFractionsQuestionData) -> Pieces:
    """Return the answer key's entry: the answer, and how the picture or story shows it."""
    match data:
        case NameQuestionData():
            count, total = data.answer.numerator, data.answer.denominator
            things = _objects(data.picture) if isinstance(data.picture, ObjectGroup) else "parts"
            verb = "is" if count == 1 else "are"
            shaded = "not shaded" if data.unshaded else "shaded"
            return (data.answer, f": {count} of the {total} {things} {verb} {shaded}")
        case ShadeQuestionData():
            count, total = data.fraction.numerator, data.fraction.denominator
            if data.divide:
                how = f"{total} equal parts, {_any(count, total)} of them shaded"
            elif isinstance(data.picture, ObjectGroup):
                how = f"{_any(count, total)} of the {total} {_objects(data.picture)} shaded"
            else:
                how = f"{_any(count, total)} of the {total} parts shaded"
            return (data.fraction, f": {how}")
        case ShareQuestionData():
            return (data.answer, f": {_share_working(data)}")
        case DrawSharesQuestionData():
            people = data.people.count
            cut = f"cut into {people} equal parts"
            if data.asked is Asked.TOGETHER:
                return (data.answer, f": {cut}; {data.together} people get {data.together} of them")
            return (data.answer, f": {cut}, one for each person")
        case _:
            assert_never(data)


def tile_answer(data: NamingFractionsQuestionData) -> TileAnswer:
    """Return the answer as a tiles bank shows it: the picture for a shade question, else the
    fraction."""
    if isinstance(data, ShadeQuestionData):
        return data.answer
    return (data.answer,)


def naming_fractions_tile_question(data: NamingFractionsQuestionData) -> TileQuestion[TileAnswer]:
    """
    Convert a question's data to a ``TileQuestion``: the prompt is the question, written inline,
    the answer as the bank shows it, and the solution the answer key's entry, inline.
    """
    return TileQuestion(
        prompt=inline(question(data, choices=False, tiles=True)),
        answer=tile_answer(data),
        solution=inline(solution(data)),
    )


def whole_name(split: Split) -> str:
    """
    Return the name of the whole that ``split`` cuts, as a question calls it: "strip",
    "rectangle", "circle", a polygon's name, or "figure" for a shape with no everyday name.
    """
    match split:
        case Strip():
            return "strip"
        case Grid():
            return "rectangle"
        case SlicedCircle():
            return "circle"
        case TriangleGrid():
            return "triangle"
        case RadialPartition():
            outline = split.outline
            match outline:
                case Circle():
                    return "circle"
                case Rectangle():
                    return "rectangle"
                case RegularPolygon():
                    return POLYGON_NAMES.get(outline.sides, "figure")
                case ConcaveOctagon():
                    return "figure"
                case _:
                    assert_never(outline)
        case CutShape():
            return _cut_shape_name(split)
        case _:
            assert_never(split)


def _cut_shape_name(cut: CutShape) -> str:
    """Return the name of a cut shape's whole."""
    named = {
        RHOMBUS: "rhombus",
        PARALLELOGRAM: "parallelogram",
        HALF_HEXAGON: "trapezoid",
        REGULAR_HEXAGON: "hexagon",
    }
    outline = cut.outline
    if outline in named:
        return named[outline]
    corners = outline.corners
    if len(corners) == 3:
        return "triangle"
    if len(corners) == 4 and outline.lattice is Lattice.SQUARE:
        xs = {x for x, _ in corners}
        ys = {y for _, y in corners}
        if len(xs) == 2 and len(ys) == 2:
            return "square" if max(xs) - min(xs) == max(ys) - min(ys) else "rectangle"
    return "figure"


def _objects(group: ObjectGroup) -> str:
    """Return the plural name of a group's objects."""
    return OBJECT_NAMES[group.kind][1]


def _any(count: int, total: int) -> str:
    """Return "any 3", or "all 4" when every part is meant."""
    return f"all {count}" if count == total else f"any {count}"


def _word(number: int) -> str:
    """Return a number as a word up to nine, else in digits."""
    return NUMBER_WORDS[number] if number < len(NUMBER_WORDS) else str(number)


def _capitalised(text: str) -> str:
    """Return ``text`` with its first letter a capital."""
    return text[:1].upper() + text[1:]


def _people(people: People) -> str:
    """
    Return the people as a story names them: "Ana, Ben and Chen", "Ana and three friends",
    "Ana and one friend", or "four friends".
    """
    singular, plural = people.noun
    if len(people.names) == people.count:
        return _listed(people.names)
    if people.names:
        others = people.count - 1
        return f"{people.names[0]} and {_word(others)} {singular if others == 1 else plural}"
    return f"{_word(people.count)} {plural}"


def _person(people: People) -> str:
    """Return how a question calls one of the people: "friend", or "person" when they're named."""
    return "person" if people.names else people.noun[0]


def _listed(items: tuple[str, ...]) -> str:
    """Return items as a list in a sentence: "A", "A and B", "A, B and C"."""
    return " and ".join(filter(None, (", ".join(items[:-1]), items[-1])))


def _thing(data: ShareQuestionData | DrawSharesQuestionData) -> str:
    """Return what's shared, as the question asks about it: "the baseballs", "the pizza"."""
    if isinstance(data, ShareQuestionData) and data.kind is not None:
        return f"the {OBJECT_NAMES[data.kind][1]}"
    return f"the {WHOLE_STORIES[data.story].whole}"


def _verb(data: ShareQuestionData | DrawSharesQuestionData) -> str:
    """Return what each person does with a share: "get", or a whole story's verb, "paint"."""
    if isinstance(data, ShareQuestionData) and data.kind is not None:
        return "get"
    return WHOLE_STORIES[data.story].verb


def _share_setup(data: ShareQuestionData) -> str:
    """Return a sharing story's sentences before its question."""
    people = _people(data.people)
    if data.kind is not None:
        setup = GROUP_STORIES[data.story].setup.format(
            people=people, total=data.total, objects=OBJECT_NAMES[data.kind][1]
        )
        return _capitalised(setup)
    story = WHOLE_STORIES[data.story]
    return f"{_capitalised(story.setup.format(people=people))} {story.cut.format(total=data.total)}"


def _asked(
    data: ShareQuestionData | DrawSharesQuestionData, people: People, asked: Asked, together: int
) -> str:
    """Return a sharing story's question: what each person gets, some get together, or is left."""
    thing, verb = _thing(data), _verb(data)
    match asked:
        case Asked.EACH:
            return f"What fraction of {thing} does each {_person(people)} {verb}?"
        case Asked.TOGETHER:
            if len(people.names) == people.count:
                who = _listed(people.names[:together])
            elif people.names:
                who = f"{_word(together)} of them"
            else:
                who = f"{_word(together)} of the {people.noun[1]}"
            return f"What fraction of {thing} do {who} {verb} together?"
        case Asked.LEFT:
            first = people.names[0] if people.names else f"One {people.noun[0]}"
            return f"{first} takes a share first. What fraction of {thing} is left?"
        case _:
            assert_never(asked)


def _share_working(data: ShareQuestionData) -> str:
    """Return how a sharing story's answer comes: "each person gets 2 of the 8 baseballs"."""
    total, people = data.total, data.people.count
    share = total // people
    things = OBJECT_NAMES[data.kind][1] if data.kind is not None else "parts"
    match data.asked:
        case Asked.EACH:
            return f"{total} {things} shared by {people} is {share} each, {share} of the {total}"
        case Asked.TOGETHER:
            return (
                f"{share} each, so {data.together} people get {data.together * share} of the "
                f"{total} {things}"
            )
        case Asked.LEFT:
            return f"one share is {share} of the {total} {things}, leaving {total - share}"
        case _:
            assert_never(data.asked)
