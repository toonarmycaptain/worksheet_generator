"""
Random generation of fractions on a number line questions: naming and marking points, distance
stories, dividing a line and comparing two distances, written, as multiple choice, or with
distinct answers for a self-check tiles sheet.

Each kind of question has its possible answers, as written, worked out from the sheet's
denominators, and each question is made from one of them: a question draws its answer first,
with each denominator equally likely, then a line or story that has it.
"""

import random
from collections import defaultdict
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import combinations

from core.fraction_models.answers import (
    LESS,
    MORE,
    WRONG_OPTIONS,
    Asked,
    NameAnswer,
    answer_capacity,
    name_answers,
    pick_answer,
    pick_distinct_answers,
    wrong_fractions,
)
from core.fraction_models.area_models import uneven_sizes
from core.fraction_models.number_lines import (
    LINE_LIMITS,
    FractionLine,
    LinePicture,
    LinePoint,
    Mark,
)
from core.fraction_number_lines.data import (
    GREATER_THAN,
    LESS_THAN,
    NONE_OF_THESE,
    Compared,
    CompareQuestion,
    CompareQuestionData,
    Comparison,
    DistanceAsked,
    DistanceQuestion,
    DistanceQuestionData,
    DivideQuestion,
    DivideQuestionData,
    FractionNumberLinesQuestion,
    MarkPointQuestion,
    MarkPointQuestionData,
    NamePointQuestion,
    NamePointQuestionData,
    QuestionType,
)
from core.fraction_number_lines.stories import DISTANCE_STORIES, DistanceStory
from core.names import NAMES, NameDealer
from core.question import FreeResponse, MultipleChoice, Question, multiple_choice
from core.written_numbers import FractionStyle, UnreducedFraction

# The kinds of question a self-check tiles sheet can ask: a divided line has no single answer
TILE_TYPES = (QuestionType.NAME, QuestionType.MARK, QuestionType.DISTANCE, QuestionType.COMPARE)
DISTANCE_PARTS = (2, 4, 8)  # halves, fourths and eighths: the only parts a distance story uses
# Lines a wrong distance choice can be cut into, besides the right line's parts: thirds and
# tenths aren't distances a story uses
WRONG_LINE_PARTS = (2, 3, 4, 6, 8, 10)
COLUMN_LINE_PARTS = LINE_LIMITS.in_a_choice  # the most parts a line in one of two columns shows
BANK_LINE_PARTS = 8  # the most parts a line in a tiles answer bank shows
DIVIDE_MOST_PARTS = 12  # the most equal parts a student is asked to divide a line into
# A wrong lettered point between ticks: only on lines of up to OFF_TICK_MOST_PARTS parts, where a
# letter fits between two ticks; at least OFF_TICK_CLEARANCE of a part from every tick, so it
# doesn't look as if it's on one; about OFF_TICK_SHARE of wrong points where a line has both kinds
OFF_TICK_MOST_PARTS = 8
OFF_TICK_CLEARANCE = Fraction(1, 4)
OFF_TICK_SHARE = 1 / 3
LETTER_SPACING = Fraction(1, 12)  # of a line, the least between two lettered points
NONE_SHARE = 0.1  # of multiple-choice name and mark questions, those ending in "None of these"
NONE_RIGHT_SHARE = 0.25  # of those, the ones where it's right
STAR_SHARE = 0.2  # of points drawn, those drawn as a star, not a dot
WHOLE_SHARE = 0.1  # of mark and divide answers with a whole among them, those that are the whole
# Of distance stories that give the distance, those on a line cut into other parts: 1/2 mile on
# a line in fourths, where the point is at 2/4
OTHER_PARTS_SHARE = 0.2
JUMPS_SHARE = 0.5  # of distances drawn, those shown as jumps, one for each part, not an arrow
HOW_FAR_SHARE = 0.5  # of written distance stories, those asking how far, not to mark the point
# Of wrong-answer choices that can make the answer the choice built from the numbers the choices
# repeat most, or not, those that do (see ``wrong_fractions``): measured so that, over default
# sheets, that choice is the answer about one time in four, as often as a guess. Lines to choose
# from reach that only by never choosing it while another choice of lines avoids it.
NAME_ON_TOP_SHARE = 0.5
DISTANCE_ON_TOP_SHARE = 0.0
# Of tiles sheets with only two compare questions, those where they ask "more or less", not who
MORE_LESS_PAIR_SHARE = 0.5

# What a compare question asks, for each thing a question about two people can ask
_COMPARED = {
    Asked.GREATER: Compared.FARTHER,
    Asked.SMALLER: Compared.SHORTER,
    Asked.MORE_OR_LESS: Compared.MORE_OR_LESS,
}

# Two distances on one line, as written, the shorter first
type _Pair = tuple[UnreducedFraction, UnreducedFraction]
# A question's type and answer: a fraction, or a compare question's distances, with what it must
# ask on a tiles sheet
type _Picked = tuple[QuestionType, UnreducedFraction | tuple[_Pair, NameAnswer | None]]


@dataclass(frozen=True)
class _Tables:
    """Every answer each kind of question can have on a sheet, and every pair of distances a
    compare question can have."""

    name: tuple[UnreducedFraction, ...]
    mark: tuple[UnreducedFraction, ...]
    distance: tuple[UnreducedFraction, ...]
    divide: tuple[UnreducedFraction, ...]
    compare: tuple[_Pair, ...]

    def of(self, question_type: QuestionType) -> tuple[UnreducedFraction, ...]:
        """Return the answers of ``question_type``, which isn't compare."""
        match question_type:
            case QuestionType.NAME:
                return self.name
            case QuestionType.MARK:
                return self.mark
            case QuestionType.DISTANCE:
                return self.distance
            case _:
                return self.divide

    def has(self, question_type: QuestionType) -> bool:
        """Return whether a question of ``question_type`` can be made."""
        if question_type is QuestionType.COMPARE:
            return bool(self.compare)
        return bool(self.of(question_type))


def generate_fraction_number_lines_questions(
    count: int,
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
    *,
    styles: Sequence[FractionStyle] = (FractionStyle.STACKED,),
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[FractionNumberLinesQuestion]:
    """
    Generate ``count`` questions, shared evenly among ``question_types``, then shuffled, each
    with fractions written in one of ``styles``.

    Every line's parts are one of ``denominators``, as long as the line can show them easily: a
    line in a column shows at most ``COLUMN_LINE_PARTS``, a line to divide at most
    ``DIVIDE_MOST_PARTS``. Distance stories, and comparisons of two distances, use only halves,
    fourths and eighths. Each question is written, or with ``multiple_choice``, has lettered
    choices: four fractions, four points on the line, four lines or four comparisons, a name or
    mark question now and then ending in "None of these". A question doesn't repeat an answer of
    its kind already on the sheet while it has others.

    With ``distinct_answers``, as the self-check tiles case needs, no two answers are the same:
    fractions as written, and a mark question asks to find the line with a point at its
    fraction, whose value no other answer on the sheet has. Distance stories ask how far.
    Dividing a line is left out, having no single answer. Compare questions are answered by
    names, which come in pairs of questions about the same two names, one answered by each, or
    with an odd number of them, once in a trio round three names; with four or more, one pair
    asks "more or less" instead. A single compare question gives its place to another type, and
    a type that has run out of answers gives its place to the next type that hasn't.

    Raises ``ValueError`` if ``question_types``, ``denominators`` or ``styles`` is empty, if
    both ``multiple_choice`` and ``distinct_answers`` are given, if a type has no possible
    question (see ``unaskable_types``), or if ``distinct_answers`` asks for more questions than
    ``count_possible_answers`` allows, for a sheet of nothing but dividing lines, or for a lone
    compare question.
    """
    if not (question_types and denominators and styles):
        raise ValueError("A question type, a denominator and a style are needed.")
    if multiple_choice and distinct_answers:
        raise ValueError("Multiple-choice questions have no answers to keep distinct.")
    tables = _tables(denominators, distinct_answers)
    kinds = [each for each in question_types if each in TILE_TYPES or not distinct_answers]
    if not kinds:
        raise ValueError("A self-check tiles sheet can't divide lines: no question has an answer.")
    stuck = [each for each in kinds if not tables.has(each)]
    if stuck:
        raise ValueError(f"No question of type {', '.join(stuck)} fits these settings.")
    names = NameDealer(NAMES)
    if distinct_answers:
        picked = _distinct_answers(count, kinds, tables, names)
    else:
        types = [kinds[index % len(kinds)] for index in range(count)]
        random.shuffle(types)
        picked = _answers(types, tables)
    questions: list[FractionNumberLinesQuestion] = []
    for question_type, answer in picked:
        style = random.choice(styles)
        if isinstance(answer, UnreducedFraction):
            questions.append(
                _question(
                    question_type,
                    replace(answer, style=style),
                    names,
                    multiple_choice,
                    distinct_answers,
                )
            )
        else:
            pair, spec = answer
            styled = (replace(pair[0], style=style), replace(pair[1], style=style))
            questions.append(_compare_question(styled, spec, names, multiple_choice))
    return questions


def unaskable_types(
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
    distinct_answers: bool = False,
) -> list[QuestionType]:
    """
    Return the types among ``question_types`` that no question can be made of with these
    denominators: naming or marking a point needs a denominator up to ``COLUMN_LINE_PARTS``, or
    with ``distinct_answers``, marking one up to ``BANK_LINE_PARTS``; dividing a line needs one
    up to ``DIVIDE_MOST_PARTS``; a distance story needs 2, 4 or 8; comparing two distances
    needs 4 or 8. With ``distinct_answers``, dividing a line is left out, not unaskable.
    """
    tables = _tables(denominators, distinct_answers)
    return [
        each
        for each in question_types
        if (each in TILE_TYPES or not distinct_answers) and not tables.has(each)
    ]


def count_possible_answers(
    question_types: Sequence[QuestionType],
    denominators: Sequence[int],
) -> int:
    """
    Return the most questions ``distinct_answers`` allows for ``question_types``: the different
    answers they can have, as written, where a line to find for a mark question, which takes a
    value of its own, counts once for its value, in place of the written answers with that value.
    Compare questions, answered by names, add one for each name in ``NAMES``, more than a sheet
    of tiles needs.
    """
    tables = _tables(denominators, distinct=True)
    kinds = [each for each in question_types if each in TILE_TYPES]
    fraction_kinds = [each for each in kinds if each is not QuestionType.COMPARE]
    capacity = answer_capacity(
        fraction_kinds, _by_type(fraction_kinds, tables), {QuestionType.MARK}
    )
    return capacity + (len(NAMES) if QuestionType.COMPARE in kinds else 0)


# --- possible answers


def _tables(denominators: Sequence[int], distinct: bool) -> _Tables:
    """Return every answer each kind of question can have with these settings."""
    mark_most = BANK_LINE_PARTS if distinct else COLUMN_LINE_PARTS
    distance_parts = [parts for parts in denominators if parts in DISTANCE_PARTS]
    return _Tables(
        name=_fractions(denominators, COLUMN_LINE_PARTS, whole=False),
        mark=_fractions(denominators, mark_most, whole=True),
        distance=_fractions(distance_parts, max(DISTANCE_PARTS), whole=False),
        divide=() if distinct else _fractions(denominators, DIVIDE_MOST_PARTS, whole=True),
        compare=tuple(
            (UnreducedFraction(shorter, parts), UnreducedFraction(longer, parts))
            for parts in distance_parts
            for shorter, longer in combinations(range(1, parts), 2)
        ),
    )


def _fractions(
    denominators: Sequence[int], most_parts: int, whole: bool
) -> tuple[UnreducedFraction, ...]:
    """Return every fraction from the first part of a line up to its last tick but one, or with
    ``whole``, up to its end, over each of ``denominators`` up to ``most_parts``."""
    return tuple(
        UnreducedFraction(numerator, parts)
        for parts in denominators
        if parts <= most_parts
        for numerator in range(1, parts + int(whole))
    )


def _by_type(
    question_types: Sequence[QuestionType], tables: _Tables
) -> dict[QuestionType, Collection[UnreducedFraction]]:
    """Return each of ``question_types``, which aren't compare, with the answers it can have."""
    return {question_type: tables.of(question_type) for question_type in question_types}


# --- choosing the answers


def _answers(types: Sequence[QuestionType], tables: _Tables) -> list[_Picked]:
    """Return an answer for each of ``types``, from those its type hasn't used while it has any:
    for a compare question, the pair of distances."""
    used: dict[QuestionType, set[UnreducedFraction]] = defaultdict(set)
    used_pairs: set[_Pair] = set()
    picked: list[_Picked] = []
    for question_type in types:
        if question_type is QuestionType.COMPARE:
            pair = _pick_pair(tables.compare, used_pairs)
            picked.append((question_type, (pair, None)))
            continue
        possible = tables.of(question_type)
        unused = [answer for answer in possible if answer not in used[question_type]]
        answer = pick_answer(unused or possible, WHOLE_SHARE)
        used[question_type].add(answer)
        picked.append((question_type, answer))
    return picked


def _pick_pair(pairs: Sequence[_Pair], used: set[_Pair]) -> _Pair:
    """Return one of ``pairs`` not in ``used`` while there are any, its parts drawn first, each
    with even chance, and add it to ``used``."""
    unused = [pair for pair in pairs if pair not in used] or list(pairs)
    by_parts: dict[int, list[_Pair]] = defaultdict(list)
    for pair in unused:
        by_parts[pair[0].denominator].append(pair)
    pair = random.choice(by_parts[random.choice(sorted(by_parts))])
    used.add(pair)
    return pair


def _distinct_answers(
    count: int, kinds: Sequence[QuestionType], tables: _Tables, names: NameDealer
) -> list[_Picked]:
    """
    Return the question types and answers of a tiles sheet, as
    ``generate_fraction_number_lines_questions`` describes: the compare questions, at least two
    or none, take their even share, or with too few fraction answers, every place left.
    """
    fraction_kinds = [each for each in kinds if each is not QuestionType.COMPARE]
    capacity = answer_capacity(
        fraction_kinds, _by_type(fraction_kinds, tables), {QuestionType.MARK}
    )
    share = [kinds[index % len(kinds)] for index in range(count)]
    compares = share.count(QuestionType.COMPARE)
    if compares == 1 and fraction_kinds:
        compares = 0
    if count - compares > capacity:
        if QuestionType.COMPARE not in kinds:
            raise ValueError(f"At most {capacity} different answers, not {count}.")
        compares = max(count - capacity, 2)
    if compares == 1:
        raise ValueError("Compare questions on a tiles sheet come at least two at a time.")
    fraction_slots = [
        fraction_kinds[index % len(fraction_kinds)] for index in range(count - compares)
    ]
    slots = fraction_slots + [QuestionType.COMPARE] * compares
    random.shuffle(slots)
    fractions = iter(
        pick_distinct_answers(
            [slot for slot in slots if slot is not QuestionType.COMPARE],
            fraction_kinds,
            _by_type(fraction_kinds, tables),
            {QuestionType.MARK},
            WHOLE_SHARE,
        )
    )
    specs = iter(_compare_specs(compares, names))
    used_pairs: set[_Pair] = set()
    picked: list[_Picked] = []
    for slot in slots:
        if slot is QuestionType.COMPARE:
            pair = _pick_pair(tables.compare, used_pairs)
            picked.append((slot, (pair, next(specs))))
        else:
            picked.append(next(fractions))
    return picked


def _compare_specs(count: int, names: NameDealer) -> list[NameAnswer]:
    """Return what each of ``count`` compare questions on a tiles sheet asks, as
    ``name_answers`` pairs them: "farther" asks for the greater distance."""
    return name_answers(count, names, MORE_LESS_PAIR_SHARE)


# --- making the questions


def _question(
    question_type: QuestionType,
    answer: UnreducedFraction,
    names: NameDealer,
    choices: bool,
    tiles: bool,
) -> FractionNumberLinesQuestion:
    """Make a question of ``question_type`` with ``answer``, in its style."""
    match question_type:
        case QuestionType.NAME:
            return _name_question(answer, choices)
        case QuestionType.MARK:
            return _mark_question(answer, choices)
        case QuestionType.DISTANCE:
            return _distance_question(answer, names.take(1)[0], choices, tiles)
        case _:
            return _divide_question(answer, choices)


def _mark() -> Mark:
    """Return how a point is drawn: a dot, or now and then a star."""
    return Mark.STAR if random.random() < STAR_SHARE else Mark.DOT


def _name_question(answer: UnreducedFraction, choices: bool) -> NamePointQuestion:
    """Make a question asking what fraction a point shows, as ``answer``."""
    parts, tick = answer.denominator, answer.numerator
    line = FractionLine(parts, points=(LinePoint(tick, mark=_mark()),))
    data = NamePointQuestionData(line, answer)
    if not choices:
        return Question(data, FreeResponse())
    # 1 over the point's place always; then two of: 1 over the parts, the place over itself, the
    # ticks counted instead of the parts, counted from the right end, counting the 0 tick as the
    # first, and one part too few
    first = [(1, tick)]
    rest = [(1, parts), (tick, tick), (tick, parts + 1), (parts - tick, parts)]
    rest += [(tick + 1, parts), (tick, parts - 1)]
    wrong = wrong_fractions(answer, first, rest, NAME_ON_TOP_SHARE)
    return Question(data, _choices(answer, wrong))


def _choices[Option](right: Option, wrong: Sequence[Option]) -> MultipleChoice[Option | str]:
    """
    Return ``right`` and ``wrong`` as choices, shuffled. Now and then the last is "None of
    these", and in a quarter of those it's right, ``right`` left out; otherwise it takes the
    place of the last wrong choice.
    """
    if random.random() >= NONE_SHARE:
        return multiple_choice((right,), tuple(wrong))
    if random.random() < NONE_RIGHT_SHARE:
        shuffled = multiple_choice((), tuple(wrong))
        return MultipleChoice((*shuffled.options, NONE_OF_THESE), frozenset({len(wrong)}))
    shuffled = multiple_choice((right,), tuple(wrong[:-1]))
    return MultipleChoice((*shuffled.options, NONE_OF_THESE), shuffled.correct_indexes)


def _mark_question(answer: UnreducedFraction, choices: bool) -> MarkPointQuestion:
    """Make a question asking to mark ``answer`` on a line, or with ``choices``, which of four
    lettered points shows it."""
    parts, tick = answer.denominator, answer.numerator
    line = FractionLine(parts)
    data = MarkPointQuestionData(answer, line, FractionLine(parts, points=(LinePoint(tick),)))
    if not choices:
        return Question(data, FreeResponse())
    return Question(data, _choices(answer.value, _wrong_points(answer)))


def _wrong_points(answer: UnreducedFraction) -> tuple[Fraction, ...]:
    """
    Return ``WRONG_OPTIONS`` points on a line cut into ``answer``'s parts, by how far along the
    line each is, for "Which point shows 3/8?": on ticks, one either side (2/8 counts the 0 tick
    as the first), counted from the right end (5/8), and one part (1/8); between ticks, where the
    same top number would be with one part fewer or more (1/2 for 1/3 on thirds), then halfway
    between two ticks, nearest the answer first; then any other tick, nearest first.

    How many are left of the answer is drawn first, each count with even chance among those the
    line allows, so the answer isn't most often the third point from the left. The first is on a
    tick, so the answer is never the only lettered point on one; each after it is between ticks
    ``OFF_TICK_SHARE`` of the time while both kinds are left, and as often as a line of halves or
    thirds needs, which has too few ticks for four letters. Every point is ``LETTER_SPACING``
    from the others, so their letters fit.
    """
    parts, tick = answer.denominator, answer.numerator
    on_ticks = list(
        dict.fromkeys(
            Fraction(each, parts)
            for each in (tick - 1, tick + 1, parts - tick, 1)
            if 1 <= each <= parts and each != tick
        )
    )
    on_ticks = random.sample(on_ticks, len(on_ticks))
    between: list[Fraction] = []
    if parts <= OFF_TICK_MOST_PARTS:
        near = [Fraction(tick, other) for other in (parts - 1, parts + 1)]
        near = [value for value in near if value <= 1 and _clear_of_ticks(value, parts)]
        halfway = sorted(
            (Fraction(2 * each + 1, 2 * parts) for each in range(parts)),
            key=lambda value: abs(value - answer.value),
        )
        between = random.sample(near, len(near)) + halfway
    every_tick = sorted(
        (Fraction(each, parts) for each in range(1, parts + 1)),
        key=lambda value: abs(value - answer.value),
    )
    # each count of points left of the answer in a random order, then any count, which any line
    # allows, having at least three other ticks or places between them
    splits = [*random.sample(range(WRONG_OPTIONS + 1), WRONG_OPTIONS + 1), None]
    return next(
        chosen
        for left in splits
        if (chosen := _chosen_points(answer.value, left, on_ticks, between, every_tick)) is not None
    )


def _chosen_points(
    value: Fraction,
    left: int | None,
    on_ticks: Sequence[Fraction],
    between: Sequence[Fraction],
    every_tick: Sequence[Fraction],
) -> tuple[Fraction, ...] | None:
    """
    Return ``WRONG_OPTIONS`` points for ``_wrong_points`` from its lists, ``left`` of them left
    of ``value`` and the rest right of it, or any number with ``left`` ``None``, or ``None`` if
    the lists don't have them.
    """
    pools = {"on": list(on_ticks), "between": list(between), "any": list(every_tick)}
    needed = None if left is None else {True: left, False: WRONG_OPTIONS - left}
    chosen = [value]
    for index in range(WRONG_OPTIONS):
        if index == 0:
            order = ("on", "any", "between")
        elif pools["between"] and (not pools["on"] or random.random() < OFF_TICK_SHARE):
            order = ("between", "on", "any")
        else:
            order = ("on", "between", "any")
        found = next(
            (
                (name, each)
                for name in order
                for each in pools[name]
                if (needed is None or needed[each < value] > 0) and _apart(each, chosen)
            ),
            None,
        )
        if found is None:
            return None
        name, point = found
        pools[name].remove(point)
        chosen.append(point)
        if needed is not None:
            needed[point < value] -= 1
    return tuple(chosen[1:])


def _clear_of_ticks(value: Fraction, parts: int) -> bool:
    """Return whether ``value`` along a line of ``parts`` parts is at least
    ``OFF_TICK_CLEARANCE`` of a part from every tick."""
    place = value * parts
    return abs(place - round(place)) >= OFF_TICK_CLEARANCE


def _apart(value: Fraction, chosen: Sequence[Fraction]) -> bool:
    """Return whether ``value`` is at least ``LETTER_SPACING`` from each of ``chosen``."""
    return all(abs(value - each) >= LETTER_SPACING for each in chosen)


def _distance_question(
    answer: UnreducedFraction, name: str, choices: bool, tiles: bool
) -> DistanceQuestion:
    """
    Make a story of ``name`` going ``answer`` of a unit from a start: asking how far a point is,
    to mark it, or with ``choices``, which of four lines shows it. On a tiles sheet it asks how
    far.
    """
    index = random.choice(range(len(DISTANCE_STORIES)))
    story = DISTANCE_STORIES[index]
    unit = random.choice(story.units)
    if tiles:
        asked = DistanceAsked.HOW_FAR
    elif choices:
        asked = DistanceAsked.MARK
    else:
        asked = DistanceAsked.HOW_FAR if random.random() < HOW_FAR_SHARE else DistanceAsked.MARK
    parts = answer.denominator
    other_parts = [each for each in DISTANCE_PARTS if each > parts and each % parts == 0]
    if asked is DistanceAsked.MARK and other_parts and random.random() < OTHER_PARTS_SHARE:
        parts = random.choice(other_parts)
    tick = answer.numerator * parts // answer.denominator
    jumps = random.random() < JUMPS_SHARE
    mark = _mark()
    letter = name[0]
    start = _start(story)

    def shown(line_parts: int, line_tick: int) -> FractionLine:
        """A line of the story's, with the point, the distance to it and the mover over it."""
        mover = (LinePicture(line_tick, story.mover),) if story.mover is not None else ()
        return FractionLine(
            line_parts,
            unit=unit,
            points=(LinePoint(line_tick, letter, mark),),
            jumps=line_tick if jumps else 0,
            arrow_to=None if jumps else line_tick,
            pictures=start + mover,
        )

    if asked is DistanceAsked.HOW_FAR:
        line = shown(parts, tick)
    else:
        line = FractionLine(parts, unit=unit, pictures=start)
    written = UnreducedFraction(tick, parts, answer.style)
    data = DistanceQuestionData(index, name, unit, asked, answer, line, written)
    if not choices:
        return Question(data, FreeResponse())
    # another point on the same line, and the same top number on a line of other parts, always;
    # then the other point on that other line, another of those first two kinds, a line in
    # thirds or tenths, counted from the right, or one part
    same_line = [each for each in ((tick - 1, parts), (tick + 1, parts)) if 1 <= each[0] <= parts]
    on_line = random.choice(same_line)
    same_top = [(tick, other) for other in WRONG_LINE_PARTS if other != parts and tick < other]
    same_top = [each for each in same_top if Fraction(*each) != Fraction(*on_line)] or same_top
    on_top = random.choice(same_top)
    # the other point on the other line, which makes the four a grid of two lines' parts by two
    # points, none of them built from the numbers the rest repeat most
    cross = (on_line[0], on_top[1])
    first = [on_line, on_top]
    rest = [cross, *same_line, *same_top, (parts - tick, parts), (1, parts), (1, 3), (2, 3)]
    rest = [each for each in [*rest, (tick, 10)] if each[0] <= each[1]]
    wrong = wrong_fractions(written, first, rest, DISTANCE_ON_TOP_SHARE)
    lines = tuple(shown(each.denominator, each.numerator) for each in wrong)
    return Question(data, multiple_choice((shown(parts, tick),), lines))


def _divide_question(answer: UnreducedFraction, choices: bool) -> DivideQuestion:
    """
    Make a question asking to divide a line into ``answer``'s parts and mark it, or with
    ``choices``, which of four divided lines does: always one cut into the right number of
    unequal parts, then two of: one part fewer (as many ticks as parts), one part more, and the
    right parts with the point counted from the right end.
    """
    parts, tick = answer.denominator, answer.numerator
    right = FractionLine(parts, points=(LinePoint(tick),))
    data = DivideQuestionData(answer, FractionLine(1), right)
    if not choices:
        return Question(data, FreeResponse())
    fewer = parts - 1 if parts > 2 else parts + 2
    sizes = random.sample(uneven_sizes(parts), parts)
    other = parts - tick if 1 <= parts - tick != tick else (tick - 1 if tick > 1 else tick + 1)
    unequal = FractionLine(parts, sizes=tuple(sizes), points=(LinePoint(tick),))
    rest = [
        FractionLine(fewer, points=(LinePoint(min(tick, fewer)),)),
        FractionLine(parts + 1, points=(LinePoint(tick),)),
        FractionLine(parts, points=(LinePoint(other),)),
    ]
    wrong = (unequal, *random.sample(rest, WRONG_OPTIONS - 1))
    return Question(data, multiple_choice((right,), wrong))


def _compare_question(
    pair: _Pair, spec: NameAnswer | None, names: NameDealer, choices: bool
) -> CompareQuestion:
    """
    Make a story of two people going the distances ``pair``, on one line, asking who went
    farther, a shorter distance, or whether the first went more or less than the second: as
    ``spec`` says, on a tiles sheet, else at random.
    """
    index = random.choice(range(len(DISTANCE_STORIES)))
    story = DISTANCE_STORIES[index]
    unit = random.choice(story.units)
    shorter, longer = pair
    if spec is None:
        first, second = names.take(2)
        compared = random.choice(list(Compared))
        distances = (shorter, longer) if random.random() < 0.5 else (longer, shorter)
        answer = _compare_answer((first, second), distances, compared)
    else:
        (first, second), answer = spec.names, spec.answer
        compared = _COMPARED[spec.asked]
        first_longer = (compared is Compared.FARTHER and answer == first) or (
            compared is Compared.SHORTER and answer == second
        )
        first_longer = first_longer or (compared is Compared.MORE_OR_LESS and answer == MORE)
        distances = (longer, shorter) if first_longer else (shorter, longer)
    line = FractionLine(shorter.denominator, unit=unit, pictures=_start(story))
    data = CompareQuestionData(index, (first, second), unit, distances, compared, line, answer)
    if not choices:
        return Question(data, FreeResponse())
    if compared is Compared.MORE_OR_LESS:
        options = [
            Comparison(word, distances[0], symbol, distances[1])
            for word in (MORE, LESS)
            for symbol in (GREATER_THAN, LESS_THAN)
        ]
    else:
        options = [
            Comparison(word, own, symbol, other)
            for word, own, other in (
                (first, distances[0], distances[1]),
                (second, distances[1], distances[0]),
            )
            for symbol in (GREATER_THAN, LESS_THAN)
        ]
    right = next(each for each in options if each.word == answer and _true(each))
    return Question(
        data, multiple_choice((right,), tuple(each for each in options if each != right))
    )


def _start(story: DistanceStory) -> tuple[LinePicture, ...]:
    """Return the picture of what ``story``'s distances start from, at 0, if it has one."""
    return (LinePicture(0, story.start),) if story.start is not None else ()


def _compare_answer(names: tuple[str, str], distances: _Pair, compared: Compared) -> str:
    """Return the answer to ``compared`` about ``names`` going ``distances``, in order."""
    first_longer = distances[0].value > distances[1].value
    match compared:
        case Compared.FARTHER:
            return names[0] if first_longer else names[1]
        case Compared.SHORTER:
            return names[1] if first_longer else names[0]
        case _:
            return MORE if first_longer else LESS


def _true(comparison: Comparison) -> bool:
    """Return whether ``comparison``'s symbol is right about its fractions."""
    if comparison.symbol == GREATER_THAN:
        return comparison.left.value > comparison.right.value
    return comparison.left.value < comparison.right.value
