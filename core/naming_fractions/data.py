"""
Data for naming fractions questions: what fraction of a picture is shaded, shading a fraction of
one, and stories of sharing a group or a whole equally.
"""

from dataclasses import dataclass
from enum import StrEnum

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import AreaModel
from core.fraction_models.object_groups import ObjectGroup
from core.question import FreeResponse, MultipleChoice, Question, QuestionData
from core.written_numbers import UnreducedFraction

# A picture of a fraction: a whole cut into parts, or a group of objects, some of them shaded
type Picture = AreaModel | ObjectGroup


class QuestionType(StrEnum):
    """A kind of naming fractions question. Values are stable identifiers for the API and
    storage."""

    NAME = "name"  # what fraction of a picture is shaded
    SHADE = "shade"  # shade a fraction of a picture
    SHARE = "share"  # a group, or a whole already cut, shared equally
    DRAW_SHARES = "draw_shares"  # a whole, uncut, shared equally: draw the cuts


class Representation(StrEnum):
    """The pictures a question names or shades. Values are stable identifiers for the API and
    storage."""

    STRIP = "strip"
    GRID = "grid"  # a rectangle cut into rows and columns
    CIRCLE = "circle"  # cut from its centre
    OTHER_SHAPE = "other_shape"  # see ``core.fraction_models.splits``
    GROUP = "group"  # of objects


class Asked(StrEnum):
    """What a sharing story asks for. Values are stable identifiers for the API and storage."""

    EACH = "each"  # what each person gets
    TOGETHER = "together"  # what some of the people get together
    LEFT = "left"  # what's left after one person takes a share


@dataclass(frozen=True)
class People:
    """
    The ``count`` people a story's share is among: with ``names`` for them all, listed by name;
    with one name, that person and the rest by ``noun``, "Ana and three friends"; or with no
    names, by ``noun``, "Four friends". ``noun`` is (singular, plural).
    """

    count: int
    noun: tuple[str, str]
    names: tuple[str, ...] = ()


@dataclass(frozen=True)
class NameQuestionData(QuestionData[UnreducedFraction]):
    """
    Asks what fraction of ``picture`` is shaded, or with ``unshaded``, what fraction is not:
    ``answer``, as written, over the picture's parts.
    """

    picture: Picture
    unshaded: bool
    answer: UnreducedFraction


@dataclass(frozen=True)
class ShadeQuestionData(QuestionData[Picture]):
    """
    Asks to shade ``fraction`` of ``picture``, which has nothing shaded. With ``divide``, the
    picture is an uncut whole, and the question asks to divide it into the fraction's
    denominator of equal parts first. ``answer`` is the picture with the fraction shaded, one of
    many right ones: any parts of an equal split will do.
    """

    fraction: UnreducedFraction
    picture: Picture
    divide: bool
    answer: Picture


@dataclass(frozen=True)
class ShareQuestionData(QuestionData[UnreducedFraction]):
    """
    A story of ``people`` sharing equally ``total`` objects of ``kind``, or with ``whole``, one
    whole cut into ``total`` equal parts: ``story`` is the bank's story, and ``asked`` what it
    asks for, about ``together`` people when that's what's asked. ``picture`` shows the group or
    the cut whole, with nothing shaded, or is ``None`` when it would have too many parts to
    count. ``answer`` is over the total, as the parts are counted: 8 shared by 4 is 2/8 each.
    """

    story: int  # its position in the bank
    people: People
    kind: DrawnObject | None  # the objects shared, or None for a whole
    total: int
    asked: Asked
    together: int
    picture: Picture | None
    answer: UnreducedFraction


@dataclass(frozen=True)
class DrawSharesQuestionData(QuestionData[UnreducedFraction]):
    """
    A story of ``people`` sharing the whole in ``picture``, uncut, equally: the student draws the
    cuts, then says what fraction ``asked`` for, about ``together`` people when that's what's
    asked: ``answer``, over the number of people.
    """

    story: int  # its position in the bank
    people: People
    picture: AreaModel
    asked: Asked
    together: int
    answer: UnreducedFraction


# Each kind of question as presented. A shade question's options are pictures, and the others'
# fractions; with them, the shares are still drawn by hand.
type NameQuestion = Question[NameQuestionData, FreeResponse | MultipleChoice[UnreducedFraction]]
type ShadeQuestion = Question[ShadeQuestionData, FreeResponse | MultipleChoice[Picture]]
type ShareQuestion = Question[ShareQuestionData, FreeResponse | MultipleChoice[UnreducedFraction]]
type DrawSharesQuestion = Question[
    DrawSharesQuestionData, FreeResponse | MultipleChoice[UnreducedFraction]
]

type NamingFractionsQuestionData = (
    NameQuestionData | ShadeQuestionData | ShareQuestionData | DrawSharesQuestionData
)
# Any question on a naming fractions sheet
type NamingFractionsQuestion = NameQuestion | ShadeQuestion | ShareQuestion | DrawSharesQuestion
