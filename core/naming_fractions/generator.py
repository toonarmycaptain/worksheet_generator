"""
Random generation of naming fractions questions: naming and shading fractions of pictures, and
stories of sharing equally, written, as multiple choice, or with distinct answers for a
self-check tiles sheet.

Each kind of question has its possible answers, as written, worked out from the sheet's
denominators and pictures, and each question is made from one of them: a question draws its
answer first, with each denominator equally likely, then a picture or story that has it.
"""

import random
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction
from itertools import combinations
from math import ceil

from core.drawn_objects import DrawnObject, ObjectUse, objects_for
from core.fraction_models.area_models import (
    BANK_PICTURE_PARTS,
    CIRCLE_LIMITS,
    GRID_LIMITS,
    STRIP_LIMITS,
    AreaModel,
    Circle,
    Grid,
    PartLimits,
    RadialPartition,
    RegularPolygon,
    Split,
    Strip,
    equal_sizes,
    rectangle,
    striped,
    uneven_sizes,
)
from core.fraction_models.object_groups import GROUP_LIMITS, ObjectGroup
from core.fraction_models.splits import other_shape_splits
from core.names import NAMES
from core.naming_fractions.data import (
    Asked,
    DrawSharesQuestion,
    DrawSharesQuestionData,
    NameQuestion,
    NameQuestionData,
    NamingFractionsQuestion,
    People,
    Picture,
    QuestionType,
    Representation,
    ShadeQuestion,
    ShadeQuestionData,
    ShareQuestion,
    ShareQuestionData,
)
from core.naming_fractions.stories import GROUP_STORIES, WHOLE_STORIES, WholeStory
from core.question import FreeResponse, Question, multiple_choice
from core.written_numbers import FractionStyle, UnreducedFraction

WRONG_OPTIONS = 3  # beside the correct option, in a multiple-choice question
UNSHADED_SHARE = 0.2  # of name questions, those asking what fraction is NOT shaded
# Of wrong-answer choices that can make the answer the choice built from the numbers the choices
# repeat most, or not, those that do, for each kind of question: measured so that, over default
# sheets, that choice is the answer about one time in four, as often as a guess, when one choice
# is alone at the top
ANSWER_ON_TOP_SHARES = {
    QuestionType.NAME: 0.6,
    QuestionType.SHARE: 1.0,  # always, and still about one time in eight: its wrong answers allow
    QuestionType.DRAW_SHARES: 0.35,
}
WHOLE_SHARE = 0.1  # of answers with a whole among them, those that are the whole, such as 4/4
SPREAD_SHARE = 0.5  # of pictures, those with their shaded parts scattered, not side by side
DIVIDE_SHARE = 1 / 3  # of written shade questions on a plain shape, those that come uncut
DIVIDE_MOST_PARTS = 12  # the most equal parts a student is asked to divide a shape into
FEWEST_PEOPLE = 2  # sharing among
MOST_PEOPLE = 8
NAMED_PERSON_SHARE = 0.25  # of stories, those about "Ana and three friends"
LISTED_SHARE = 0.4  # of stories of 2 or 3 people, those naming them all
WHOLE_STORY_SHARE = 0.4  # of sharing questions, those about a whole, when one can show it
GROUP_ROW = 8  # the most objects in a row of a group
WHOLE_GRID_ROWS = 4  # the most rows of a whole cut as a grid, such as a wall
# Objects a group shows when it's named or shaded: all but the musical triangle, whose name
# would read as the shape
GROUP_KINDS = tuple(kind for kind in DrawnObject if kind is not DrawnObject.MUSICAL_TRIANGLE)
SHARED_KINDS = objects_for(ObjectUse.SHARING)


class _Room(Enum):
    """How large a picture to name or shade is drawn, which limits how many parts it shows. A
    story's picture is as wide as the page's text, so ``_whole_splits`` uses the alone limits."""

    COLUMN = "column"  # in one of two columns, or one of four choices in two rows
    BANK = "bank"  # in a box of a tiles answer bank


def _most(limits: PartLimits, room: _Room) -> int:
    """Return the most parts a picture with ``limits`` shows in ``room``."""
    if room is _Room.BANK:
        return min(limits.in_a_choice, BANK_PICTURE_PARTS)
    return limits.in_a_choice


@dataclass(frozen=True)
class _ShareWay:
    """How a sharing story gets its answer: among ``people``, asking ``asked``, about
    ``together`` people when it asks what some get together."""

    people: int
    asked: Asked
    together: int = 1


# Each possible answer, as written, with the ways a question can have it: the representations
# that can show it, or the ways a story can
type _Answers[Way] = Mapping[UnreducedFraction, Sequence[Way]]


@dataclass(frozen=True)
class _Tables:
    """Every answer each kind of question can have on a sheet, with the ways it can come up."""

    name: _Answers[Representation]
    shade: _Answers[Representation]
    share: _Answers[_ShareWay]
    draw: _Answers[_ShareWay]

    def of(self, question_type: QuestionType) -> _Answers[Representation] | _Answers[_ShareWay]:
        """Return the answers of ``question_type``."""
        match question_type:
            case QuestionType.NAME:
                return self.name
            case QuestionType.SHADE:
                return self.shade
            case QuestionType.SHARE:
                return self.share
            case _:
                return self.draw


def generate_naming_fractions_questions(
    count: int,
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
    *,
    styles: Sequence[FractionStyle] = (FractionStyle.STACKED,),
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[NamingFractionsQuestion]:
    """
    Generate ``count`` questions, shared evenly among ``question_types``, then shuffled, each
    with fractions written in one of ``styles``.

    Every fraction's denominator is one of ``denominators``, and every picture a question names
    or shades, and every story's picture, is one of ``representations``, as long as it can show
    the parts easily: a picture is capped by what it can draw, and a story whose group has too
    many objects to count has no picture. Each is written, or with ``multiple_choice``, has
    lettered choices: four fractions, or for a shade question four pictures; the shares to draw
    are still drawn, with fractions to choose from. A question doesn't repeat an answer of its
    kind already on the sheet while it has others.

    With ``distinct_answers``, as the self-check tiles case needs, no two answers are the same as
    written, and a shade question asks to find the picture that shows its fraction, whose value
    no other answer on the sheet has: a picture of 3/4 can't sit in a bank beside 6/8. A type
    that has run out of answers gives its place to the next type that hasn't.

    Raises ``ValueError`` if ``question_types``, ``representations``, ``denominators`` or
    ``styles`` is empty, if both ``multiple_choice`` and ``distinct_answers`` are given, if a
    type has no possible answer (see ``unaskable_types``), or if ``distinct_answers`` asks for
    more questions than ``count_possible_answers`` allows.
    """
    if not (question_types and representations and denominators and styles):
        raise ValueError("A question type, a representation, a denominator and a style are needed.")
    if multiple_choice and distinct_answers:
        raise ValueError("Multiple-choice questions have no answers to keep distinct.")
    tables = _tables(representations, denominators, distinct_answers)
    stuck = [each for each in question_types if not tables.of(each)]
    if stuck:
        raise ValueError(f"No question of type {', '.join(stuck)} fits these settings.")
    types = [question_types[index % len(question_types)] for index in range(count)]
    random.shuffle(types)
    if distinct_answers:
        picked = _distinct_answers(types, question_types, tables)
    else:
        picked = _answers(types, tables)
    return [
        _question(
            question_type,
            replace(answer, style=random.choice(styles)),
            tables,
            representations,
            multiple_choice,
            distinct_answers,
        )
        for question_type, answer in picked
    ]


def unaskable_types(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
    distinct_answers: bool = False,
) -> list[QuestionType]:
    """
    Return the types among ``question_types`` that no question can be made of with these
    pictures and denominators: naming or shading needs a picture that can show a denominator,
    sharing needs a denominator with a factor from 2 to 8 and a story to tell with the pictures,
    and drawing the shares needs a denominator from 2 to 8 and a whole to cut, which a group of
    objects isn't. With ``distinct_answers``, a picture to shade must fit a tiles answer bank.
    """
    tables = _tables(representations, denominators, distinct_answers)
    return [each for each in question_types if not tables.of(each)]


def count_possible_answers(
    question_types: Sequence[QuestionType],
    representations: Sequence[Representation],
    denominators: Sequence[int],
) -> int:
    """
    Return the most questions ``distinct_answers`` allows for ``question_types``: the different
    answers they can have, as written, where a picture to shade, which takes a value of its own,
    counts once for its value, in place of the written answers with that value.
    """
    tables = _tables(representations, denominators, distinct=True)
    return _capacity(
        _written_by_value(question_types, tables), _picture_values(question_types, tables)
    )


# --- possible answers


def _tables(
    representations: Sequence[Representation], denominators: Sequence[int], distinct: bool
) -> _Tables:
    """Return every answer each kind of question can have with these settings."""
    reps = tuple(representations)
    name: dict[UnreducedFraction, list[Representation]] = {}
    shade: dict[UnreducedFraction, list[Representation]] = {}
    share: dict[UnreducedFraction, list[_ShareWay]] = defaultdict(list)
    draw: dict[UnreducedFraction, list[_ShareWay]] = defaultdict(list)
    shade_room = _Room.BANK if distinct else _Room.COLUMN
    for parts in denominators:
        for table, room in ((name, _Room.COLUMN), (shade, shade_room)):
            showing = [rep for rep in reps if _can_show(rep, parts, room)]
            if showing:
                for shaded in range(1, parts + 1):
                    table[UnreducedFraction(shaded, parts)] = showing
        if _group_stories_fit(reps) or _precut_stories(reps, parts):
            for people in range(FEWEST_PEOPLE, min(MOST_PEOPLE, parts) + 1):
                if parts % people == 0:
                    for answer, way in _share_ways(parts, people, parts // people):
                        share[answer].append(way)
        if FEWEST_PEOPLE <= parts <= MOST_PEOPLE and _drawn_stories(reps):
            for answer, way in _share_ways(parts, parts, 1, left=False):
                draw[answer].append(way)
    return _Tables(name, shade, dict(share), dict(draw))


def _share_ways(
    total: int, people: int, share: int, left: bool = True
) -> list[tuple[UnreducedFraction, _ShareWay]]:
    """
    Return each answer of ``total`` shared among ``people``, ``share`` each, with how it's asked:
    each person's share, what 2 or more of them get together, and with ``left``, what's left
    after one takes a share.
    """
    ways = [(UnreducedFraction(share, total), _ShareWay(people, Asked.EACH))]
    ways += [
        (UnreducedFraction(together * share, total), _ShareWay(people, Asked.TOGETHER, together))
        for together in range(2, people)
    ]
    if left:
        ways.append((UnreducedFraction(total - share, total), _ShareWay(people, Asked.LEFT)))
    return ways


def _can_show(rep: Representation, parts: int, room: _Room) -> bool:
    """Return whether ``rep`` can show ``parts`` equal parts in ``room``."""
    if rep is Representation.GROUP:
        return parts <= _most(GROUP_LIMITS, room)
    return bool(_equal_splits(rep, parts, room))


def _equal_splits(rep: Representation, parts: int, room: _Room) -> list[Split]:
    """Return the ways ``rep``, which isn't a group, shows ``parts`` equal parts in ``room``."""
    match rep:
        case Representation.STRIP:
            return [Strip(equal_sizes(parts))] if parts <= _most(STRIP_LIMITS, room) else []
        case Representation.GRID:
            if parts > _most(GRID_LIMITS, room):
                return []
            return [
                Grid(rows, parts // rows)
                for rows in range(2, parts // 2 + 1)
                if parts % rows == 0 and parts // rows >= 2
            ]
        case Representation.CIRCLE:
            if parts > _most(CIRCLE_LIMITS, room):
                return []
            return [RadialPartition(Circle(), equal_sizes(parts))]
        case _:
            splits = other_shape_splits(parts, in_a_choice=True)
            return list(splits) if room is not _Room.BANK or parts <= BANK_PICTURE_PARTS else []


def _group_stories_fit(reps: Sequence[Representation]) -> bool:
    """Return whether a story can share a group of objects: when groups are among ``reps``."""
    return Representation.GROUP in reps


def _precut_stories(reps: Sequence[Representation], parts: int) -> list[WholeStory]:
    """Return the stories of a whole that comes cut into ``parts`` and that ``reps`` show."""
    return [
        story
        for story in WHOLE_STORIES
        if story.precut and story.representation in reps and _whole_splits(story, parts)
    ]


def _drawn_stories(reps: Sequence[Representation]) -> list[WholeStory]:
    """Return the stories of a whole, uncut, that ``reps`` show."""
    return [story for story in WHOLE_STORIES if story.representation in reps]


def _whole_splits(story: WholeStory, parts: int) -> list[Split]:
    """
    Return the ways ``story``'s whole is cut into ``parts`` equal parts, drawn as wide as the
    page's text: 1 is the whole, uncut. A round cake, seen from the side, never comes cut: its
    story isn't ``precut``.
    """
    match story.representation:
        case Representation.STRIP:
            return [Strip(equal_sizes(parts))] if parts <= STRIP_LIMITS.alone else []
        case Representation.GRID:
            if parts > GRID_LIMITS.alone:
                return []
            return [
                Grid(rows, parts // rows)
                for rows in range(1, WHOLE_GRID_ROWS + 1)
                if parts % rows == 0 and parts // rows >= rows
            ]
        case Representation.CIRCLE:
            return (
                [RadialPartition(Circle(), equal_sizes(parts))]
                if parts <= CIRCLE_LIMITS.alone
                else []
            )
        case _:  # a square sandwich: cut corner to corner or across, then both
            square = RegularPolygon(4)
            if parts in (1, 8):
                return [RadialPartition(square, equal_sizes(parts))]
            if parts in (2, 4):
                return [
                    RadialPartition(square, equal_sizes(parts)),
                    RadialPartition(square, equal_sizes(parts), Fraction(1, 8)),
                ]
            return []


# --- choosing the answers


def _answers(
    types: Sequence[QuestionType], tables: _Tables
) -> list[tuple[QuestionType, UnreducedFraction]]:
    """Return an answer for each of ``types``, from those its type hasn't used while it has any."""
    used: dict[QuestionType, set[UnreducedFraction]] = defaultdict(set)
    picked = []
    for question_type in types:
        possible = list(tables.of(question_type))
        unused = [answer for answer in possible if answer not in used[question_type]]
        answer = _pick(unused or possible)
        used[question_type].add(answer)
        picked.append((question_type, answer))
    return picked


def _pick(answers: Sequence[UnreducedFraction]) -> UnreducedFraction:
    """
    Return one of ``answers``, its denominator drawn first, each with even chance, then a
    numerator. A whole, such as 4/4, is drawn only one time in ``1 / WHOLE_SHARE`` while there are
    others, so that a picture all shaded doesn't come up as often as one half shaded.
    """
    by_denominator: dict[int, list[UnreducedFraction]] = defaultdict(list)
    for answer in answers:
        by_denominator[answer.denominator].append(answer)
    drawn = by_denominator[random.choice(sorted(by_denominator))]
    wholes = [answer for answer in drawn if answer.numerator == answer.denominator]
    parts = [answer for answer in drawn if answer.numerator != answer.denominator]
    if wholes and parts:
        return random.choice(wholes if random.random() < WHOLE_SHARE else parts)
    return random.choice(drawn)


def _written_by_value(
    question_types: Sequence[QuestionType], tables: _Tables
) -> dict[Fraction, set[UnreducedFraction]]:
    """Return the written answers of ``question_types``, grouped by their values."""
    found: dict[Fraction, set[UnreducedFraction]] = defaultdict(set)
    for question_type in set(question_types) - {QuestionType.SHADE}:
        for answer in tables.of(question_type):
            found[answer.value].add(answer)
    return found


def _picture_values(question_types: Sequence[QuestionType], tables: _Tables) -> set[Fraction]:
    """Return the values a picture to shade can have, if shading is among ``question_types``."""
    if QuestionType.SHADE not in question_types:
        return set()
    return {answer.value for answer in tables.shade}


def _capacity(
    written: Mapping[Fraction, Set[UnreducedFraction]],
    pictures: Set[Fraction],
    used: Set[UnreducedFraction] = frozenset(),
    taken: Set[Fraction] = frozenset(),
) -> int:
    """
    Return how many more distinct answers a sheet can take, once it has used the written answers
    ``used`` and the picture values ``taken``: for each value, its written answers left if it has
    used one, none if a picture has it, else the more of its written answers and a picture.
    """
    values_used = {answer.value for answer in used}
    total = 0
    for value in written.keys() | pictures:
        forms = written.get(value, frozenset())
        if value in taken:
            continue
        if value in values_used:
            total += len(forms - used)
        else:
            total += max(len(forms), int(value in pictures))
    return total


def _distinct_answers(
    types: Sequence[QuestionType], question_types: Sequence[QuestionType], tables: _Tables
) -> list[tuple[QuestionType, UnreducedFraction]]:
    """
    Return a distinct answer for each of ``types``, as ``generate_naming_fractions_questions``
    describes, trying each slot's own type first, then the others in ``question_types`` order.

    Every written answer lowers the sheet's capacity (see ``_capacity``) by one, but a picture's
    value lowers it by all the written answers with that value, so a picture takes a value only
    while enough capacity is left for the slots after it. That keeps a slot always fillable, so
    the sheet is complete whenever ``count_possible_answers`` allows its length.
    """
    written = _written_by_value(question_types, tables)
    pictures = _picture_values(question_types, tables)
    if len(types) > _capacity(written, pictures):
        raise ValueError(
            f"At most {_capacity(written, pictures)} different answers, not {len(types)}."
        )
    used: set[UnreducedFraction] = set()
    taken: set[Fraction] = set()
    picked: list[tuple[QuestionType, UnreducedFraction]] = []
    for slot, own in enumerate(types):
        left_after = len(types) - slot - 1
        start = question_types.index(own)
        for question_type in (*question_types[start:], *question_types[:start]):
            if question_type is QuestionType.SHADE:
                capacity = _capacity(written, pictures, used, taken)
                values_used = {answer.value for answer in used}
                fitting = sorted(
                    value
                    for value in pictures - taken - values_used
                    if capacity - max(len(written.get(value, ())), 1) >= left_after
                )
                if fitting:
                    value = random.choice(fitting)
                    taken.add(value)
                    forms = [answer for answer in tables.shade if answer.value == value]
                    picked.append((question_type, random.choice(forms)))
                    break
            else:
                fitting_answers = [
                    answer
                    for answer in tables.of(question_type)
                    if answer not in used and answer.value not in taken
                ]
                if fitting_answers:
                    answer = _pick(fitting_answers)
                    used.add(answer)
                    picked.append((question_type, answer))
                    break
    return picked


# --- making the questions


def _question(
    question_type: QuestionType,
    answer: UnreducedFraction,
    tables: _Tables,
    reps: Sequence[Representation],
    choices: bool,
    tiles: bool,
) -> NamingFractionsQuestion:
    """Make a question of ``question_type`` with ``answer``, in its style."""
    match question_type:
        case QuestionType.NAME:
            return _name_question(answer, tables.name[answer], choices)
        case QuestionType.SHADE:
            return _shade_question(answer, tables.shade[answer], choices, tiles)
        case QuestionType.SHARE:
            return _share_question(answer, random.choice(tables.share[answer]), reps, choices)
        case _:
            return _draw_question(answer, random.choice(tables.draw[answer]), reps, choices)


def _name_question(
    answer: UnreducedFraction, reps: Sequence[Representation], choices: bool
) -> NameQuestion:
    """Make a question asking what fraction of a picture is shaded, or not, as ``answer``."""
    parts, asked = answer.denominator, answer.numerator
    unshaded = asked < parts and random.random() < UNSHADED_SHARE
    picture = _picture(
        random.choice(reps), parts, parts - asked if unshaded else asked, _Room.COLUMN
    )
    data = NameQuestionData(picture, unshaded, answer)
    if not choices:
        return Question(data, FreeResponse())
    other = parts - asked
    # the other parts over the whole always, then two of: the other parts over the asked ones,
    # 1 over the asked parts, the asked over the others, a part too many or too few, and flipped
    rest = [(other, asked), (1, asked), (asked, other), (asked, parts + 1), (asked, parts - 1)]
    wrong = _wrong_fractions(QuestionType.NAME, answer, [(other, parts)], [*rest, (parts, asked)])
    return Question(data, multiple_choice((answer,), wrong))


def _shade_question(
    answer: UnreducedFraction, reps: Sequence[Representation], choices: bool, tiles: bool
) -> ShadeQuestion:
    """Make a question asking to shade ``answer`` of a picture."""
    parts, shaded = answer.denominator, answer.numerator
    rep = random.choice(reps)
    room = _Room.BANK if tiles else _Room.COLUMN
    divide = (
        not (choices or tiles)
        and rep is not Representation.GROUP
        and parts <= DIVIDE_MOST_PARTS
        and random.random() < DIVIDE_SHARE
    )
    if divide:
        whole, cut = _uncut(rep, parts)
        data = ShadeQuestionData(
            answer, AreaModel(whole), True, AreaModel(cut, _shade(parts, shaded))
        )
        return Question(data, FreeResponse())
    shown = _picture(rep, parts, shaded, room)
    data = ShadeQuestionData(answer, _without_shading(shown), False, shown)
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, multiple_choice((shown,), _wrong_pictures(shown, rep, answer)))


def _share_question(
    answer: UnreducedFraction, way: _ShareWay, reps: Sequence[Representation], choices: bool
) -> ShareQuestion:
    """Make a story of a group, or a whole cut into parts, shared equally, with ``answer``."""
    total = answer.denominator
    wholes = _precut_stories(reps, total)
    if wholes and (not _group_stories_fit(reps) or random.random() < WHOLE_STORY_SHARE):
        story = random.choice(wholes)
        index = WHOLE_STORIES.index(story)
        picture: Picture | None = AreaModel(
            random.choice(_whole_splits(story, total)), look=story.look
        )
        kind = None
        nouns = story.nouns
    else:
        index = random.choice(range(len(GROUP_STORIES)))
        kind = random.choice(SHARED_KINDS)
        picture = ObjectGroup(kind, total, _per_row(total)) if total <= GROUP_LIMITS.alone else None
        nouns = GROUP_STORIES[index].nouns
    people = _people(way.people, nouns)
    data = ShareQuestionData(index, people, kind, total, way.asked, way.together, picture, answer)
    if not choices:
        return Question(data, FreeResponse())
    share, count, together = total // way.people, way.people, way.together
    match way.asked:
        case Asked.EACH:
            first = [(count, total)]  # the people over the total
            rest = [(share, share), (share, 1), (total + count, total), (share, count)]
            rest += [(count, count), (1, total), (1, count)]
            if len(people.names) == 1:  # "Ana and three friends", counted without Ana
                first.append((count - 1, total))
        case Asked.TOGETHER:
            first = [(together, total)]  # the people over the total
            rest = [(together, count), (share, total), (total - together * share, total)]
            rest += [(together * share, count)]
        case _:
            first = [(share, total)]  # the share, not what's left
            rest = [(count - 1, count), (1, count), (count - 1, total), (total - share, share)]
    return Question(
        data, multiple_choice((answer,), _wrong_fractions(QuestionType.SHARE, answer, first, rest))
    )


def _draw_question(
    answer: UnreducedFraction, way: _ShareWay, reps: Sequence[Representation], choices: bool
) -> DrawSharesQuestion:
    """Make a story of a whole, uncut, shared equally, for the student to cut, with ``answer``,
    and with ``choices``, four fractions to choose from."""
    story = random.choice(_drawn_stories(reps))
    picture = AreaModel(_whole_splits(story, 1)[0], look=story.look)
    data = DrawSharesQuestionData(
        WHOLE_STORIES.index(story),
        _people(way.people, story.nouns),
        picture,
        way.asked,
        way.together,
        answer,
    )
    if not choices:
        return Question(data, FreeResponse())
    count, together = way.people, way.together
    # the cuts counted instead of the parts, as a strip cut in 4 has 3 cuts, or "Ana and three
    # friends" counted without Ana
    first = [(answer.numerator, count - 1)]
    if way.asked is Asked.EACH:
        # flipped, what's left after one share, one part too many, and the whole
        rest = [(count, 1), (count - 1, count), (1, count + 1), (count, count)]
    else:
        # one share, what the others get, one part too many, flipped, and 1 over the people asked
        rest = [(1, count), (count - together, count), (together, count + 1), (count, together)]
        rest.append((1, together))
    wrong = _wrong_fractions(QuestionType.DRAW_SHARES, answer, first, rest)
    return Question(data, multiple_choice((answer,), wrong))


def _people(count: int, nouns: Sequence[tuple[str, str]]) -> People:
    """Return ``count`` people, described in one of the ways ``People`` allows."""
    noun = random.choice(nouns)
    roll = random.random()
    if roll < NAMED_PERSON_SHARE:
        return People(count, noun, (random.choice(NAMES),))
    if count <= 3 and roll < NAMED_PERSON_SHARE + LISTED_SHARE:
        return People(count, noun, tuple(random.sample(NAMES, count)))
    return People(count, noun)


# --- pictures


def _picture(
    rep: Representation, parts: int, shaded: int, room: _Room, kind: DrawnObject | None = None
) -> Picture:
    """Return a picture of ``parts`` equal parts in ``rep``, ``shaded`` of them shaded, a group
    of ``kind``, or of a random object."""
    if rep is Representation.GROUP:
        kind = kind or random.choice(GROUP_KINDS)
        return ObjectGroup(kind, parts, _per_row(parts), _shade(parts, shaded))
    return AreaModel(random.choice(_equal_splits(rep, parts, room)), _shade(parts, shaded))


def _shade(parts: int, shaded: int) -> frozenset[int]:
    """Return which of ``parts`` to shade, ``shaded`` of them, scattered or side by side."""
    if random.random() < SPREAD_SHARE:
        return frozenset(random.sample(range(parts), shaded))
    start = random.choice(range(parts - shaded + 1))
    return frozenset(range(start, start + shaded))


def _without_shading(picture: Picture) -> Picture:
    """Return ``picture`` with nothing shaded."""
    return replace(picture, shaded=frozenset())


def _per_row(count: int) -> int:
    """Return how many of ``count`` objects go in a row: one row of up to 5, else two rows or
    more, of up to ``GROUP_ROW``."""
    rows = 1 if count <= 5 else max(2, ceil(count / GROUP_ROW))
    return ceil(count / rows)


def _uncut(rep: Representation, parts: int) -> tuple[Split, Split]:
    """Return a plain whole for ``rep``, uncut, and one way of cutting it into ``parts`` equal
    parts: a strip, a rectangle, a circle or a square."""
    match rep:
        case Representation.STRIP:
            return Strip(equal_sizes(1)), Strip(equal_sizes(parts))
        case Representation.GRID:
            return Grid(1, 1), Grid(1, parts)
        case Representation.CIRCLE:
            return (
                RadialPartition(Circle(), equal_sizes(1)),
                RadialPartition(Circle(), equal_sizes(parts)),
            )
        case _:
            return RadialPartition(RegularPolygon(4), equal_sizes(1)), striped(
                rectangle(1, 1), parts
            )


def _unequal_split(rep: Representation, parts: int) -> Split | None:
    """Return ``rep`` cut into ``parts`` clearly unequal parts, in a random order, or ``None``
    when it can't be: a grid or a group."""
    sizes = list(uneven_sizes(parts))
    random.shuffle(sizes)
    match rep:
        case Representation.STRIP:
            return Strip(tuple(sizes))
        case Representation.CIRCLE:
            return RadialPartition(Circle(), tuple(sizes))
        case Representation.OTHER_SHAPE:
            outline = random.choice((RegularPolygon(4), RegularPolygon(6, on_corner=True)))
            return RadialPartition(outline, tuple(sizes))
        case _:
            return None


# --- wrong answers


def _wrong_fractions(
    question_type: QuestionType,
    answer: UnreducedFraction,
    first: Sequence[tuple[int, int]],
    rest: Sequence[tuple[int, int]],
) -> tuple[UnreducedFraction, ...]:
    """
    Return ``WRONG_OPTIONS`` wrong fractions in ``answer``'s style: those of ``first`` that are
    wrong, then a random choice of ``rest``'s, each value different from the answer's and from
    the others'. If those run short, fractions over the answer's denominator fill in.

    A wrong answer is often built from the answer's own numbers, which can make the answer the
    one choice built from the numbers the choices repeat most, a guess that needs no maths. So
    when the ways to choose from ``rest`` can put the answer alone at the top that way or not, it's
    put there ``question_type``'s share of the time in ``ANSWER_ON_TOP_SHARES``, so that the guess
    is right about as often as any guess. A whole, such as 4/4, has its denominator twice, so it's
    always at the top.
    """
    forced = _valid_fractions(answer, first)[:WRONG_OPTIONS]
    others = _valid_fractions(answer, rest, {each.value for each in forced})
    needed = WRONG_OPTIONS - len(forced)
    if len(others) < needed:
        parts = answer.denominator
        fill = [(numerator, parts) for numerator in range(1, parts + 2)]
        fill += [(numerator, parts + 1) for numerator in range(1, parts + 2)]
        taken = {each.value for each in (*forced, *others)}
        others += _valid_fractions(answer, fill, taken)[: needed - len(others)]
    ways = [(*forced, *chosen) for chosen in combinations(others, needed)]
    tops = {way: _top(answer, way) for way in ways}
    on_top = [way for way in ways if tops[way] == 0]  # the answer
    wrong_top = [way for way in ways if tops[way] is not None and tops[way] != 0]
    tied = [way for way in ways if tops[way] is None]
    others_top = wrong_top + tied
    if on_top and (not others_top or random.random() < ANSWER_ON_TOP_SHARES[question_type]):
        return random.choice(on_top)
    return random.choice(others_top)


def _valid_fractions(
    answer: UnreducedFraction,
    candidates: Sequence[tuple[int, int]],
    taken: Set[Fraction] = frozenset(),
) -> list[UnreducedFraction]:
    """Return ``candidates`` as fractions in ``answer``'s style, leaving out any with a number
    below 1, or a value already among the answer's and ``taken``, and repeats."""
    values = {answer.value, *taken}
    found = []
    for numerator, denominator in candidates:
        if numerator < 1 or denominator < 1:
            continue
        fraction = UnreducedFraction(numerator, denominator, answer.style)
        if fraction.value not in values:
            found.append(fraction)
            values.add(fraction.value)
    return found


def _top(answer: UnreducedFraction, wrong: Sequence[UnreducedFraction]) -> int | None:
    """
    Return which of the choices, the answer first and then ``wrong``, is alone the one built from
    the numbers the choices repeat most, by its position, or ``None`` when two or more tie.
    """
    options = (answer, *wrong)
    counts = Counter(number for each in options for number in (each.numerator, each.denominator))
    scores = [counts[each.numerator] + counts[each.denominator] for each in options]
    return scores.index(max(scores)) if scores.count(max(scores)) == 1 else None


def _wrong_pictures(
    shown: Picture, rep: Representation, answer: UnreducedFraction
) -> tuple[Picture, ...]:
    """
    Return ``WRONG_OPTIONS`` pictures for "Which model shows 3/4 shaded?" that don't show
    ``answer``, in ``rep``, a group of the same objects as ``shown``: the shaded and unshaded
    parts swapped; the unshaded parts counted as the whole, as in 3 shaded beside 4 more; the
    same parts shaded of a whole cut unequally; the same number shaded of another number of parts;
    and one part more or less shaded.
    """
    parts, shaded = answer.denominator, answer.numerator
    kind = shown.kind if isinstance(shown, ObjectGroup) else None
    first = [(parts, parts - shaded, True)]
    rest = [(shaded + parts, shaded, True), (parts, shaded, False)]
    rest += [(other, shaded, True) for other in (2 * parts, parts + 1, parts - 1)]
    rest += [(parts, shaded + 1, True), (parts, shaded - 1, True)]
    found: list[Picture] = []
    values = {answer.value}

    def add(candidates: Sequence[tuple[int, int, bool]]) -> None:
        for whole, count, equal in candidates:
            if len(found) == WRONG_OPTIONS or not 1 <= count <= whole:
                continue
            if equal:
                value = Fraction(count, whole)
                if value in values or not _can_show(rep, whole, _Room.COLUMN):
                    continue
                values.add(value)
                found.append(_picture(rep, whole, count, _Room.COLUMN, kind))
            elif 2 <= whole <= _most(CIRCLE_LIMITS, _Room.COLUMN):
                split = _unequal_split(rep, whole)
                if split is not None:
                    found.append(AreaModel(split, _shade(whole, count)))

    add(first)
    add(random.sample(rest, len(rest)))
    add([(parts, count, True) for count in range(1, parts + 1)])
    add([(whole, count, True) for whole in range(2, parts + 3) for count in range(1, whole + 1)])
    return tuple(found)
