"""
Random generation of comparing fractions questions: comparing two fractions with a symbol, with
or without a reason, word problems, ways of showing a fraction less or greater than a model's,
drawing two fractions to compare, and the greatest or least of three or four, written, as
multiple choice, or with distinct answers for a self-check tiles sheet.

Every comparison is of fractions that share a numerator or a denominator, each chosen directly
from the candidates that fit the sheet's settings, so a question is never drawn again for
failing to fit.
"""

import random
from collections.abc import Sequence
from dataclasses import replace
from functools import cache

from core.comparing_fractions.data import (
    ComparingFractionsQuestion,
    GreatestQuestion,
    Representation,
    Shared,
)
from core.comparing_fractions.data import QuestionType as Type
from core.comparing_fractions.picks import Need, can_pick, pick
from core.comparing_fractions.pictures import AREA_REPRESENTATIONS, can_show
from core.comparing_fractions.questions import (
    EQUAL_SHARE,
    StorySettings,
    can_ask_every,
    compare_question,
    draw_question,
    every_question,
    explain_question,
    greatest_question,
    less_greater_fits,
    less_greater_question,
    make_word_question,
    story_ways,
)
from core.comparing_fractions.tiles import (
    GREATEST_GROUP,
    PAIRS_AND_THREES,
    Group,
    Pool,
    capacity,
    fills,
    make_pool,
    plan_groups,
)
from core.fraction_models.answers import name_answers
from core.names import NAMES, NameDealer
from core.written_numbers import FractionStyle, UnreducedFraction

# The kinds of question a self-check tiles sheet can ask: the rest have no single written answer
TILE_TYPES = (Type.COMPARE, Type.WORD, Type.GREATEST)
EVERY_SHARE = 0.1  # of compare questions, when no picture is ticked, those asking "greater than"
GREATER_SHARE = 0.5  # of less or greater questions, those asking for a fraction greater
FOUR_SHARE = 0.5  # of greatest and least questions that can have four fractions, those that do
DRAW_MOST_PARTS = 12  # the most equal parts a student is asked to divide a whole or a line into
# Of tiles sheets with Compare ticked, those with a pair of "Which of these are greater than"
# questions, one answered "all of them" and one "none of them"
EVERY_PAIR_SHARE = 0.5
# Of tiles sheets with only two word problems, those where they ask "more or less", not who
MORE_LESS_PAIR_SHARE = 0.5
# The representations a whole or a line to divide can be drawn in
DRAW_REPRESENTATIONS = (*AREA_REPRESENTATIONS, Representation.LINE)


def generate_comparing_fractions_questions(
    count: int,
    question_types: Sequence[Type],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    *,
    styles: Sequence[FractionStyle] = (FractionStyle.STACKED,),
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[ComparingFractionsQuestion]:
    """
    Generate ``count`` questions, shared evenly among ``question_types``, then shuffled, each
    with fractions written in one of ``styles``.

    Each question's fractions share a numerator or a denominator, as ``shared`` allows, with
    even chance when both are, over ``denominators``, and each is shown in one of
    ``representations`` that can show them, or written with no picture. Written, each asks for
    its answer; with ``multiple_choice``, it has lettered choices whose wrong ones are common
    mistakes. A question's set of fractions isn't repeated on the sheet while there are others.

    With ``distinct_answers``, as the self-check tiles case needs, no two answers are the same:
    fractions as written, names, and "more", "less", "all of them" and "none of them". Compare,
    word problems, and greatest and least are asked; the rest, having no single written answer,
    are left out. Compare questions ask "Which is greater, 3/6 or 3/8?" in groups of two or
    three fractions sharing a number, where each fraction answers one question and the others
    offer it, with a three's third question asking for the greatest when Greatest and least is
    ticked; Greatest and least alone comes in groups of four to seven. Word problems are answered
    by names in pairs, or once in a trio, as ``name_answers`` gives them. A type that can't fill
    its share gives its places to word problems.

    Raises ``ValueError`` if ``question_types``, ``representations``, ``shared``,
    ``denominators`` or ``styles`` is empty, if both ``multiple_choice`` and
    ``distinct_answers`` are given, if ``distinct_answers`` is given with none of the types a
    tiles sheet asks, if a type has no possible question (see
    ``unaskable_types``), or if ``distinct_answers`` asks for a count that
    ``count_possible_answers`` or ``tile_count_fits`` doesn't allow.
    """
    if not (question_types and representations and shared and denominators and styles):
        raise ValueError(
            "A question type, a representation, a kind of sharing, a denominator "
            "and a style are needed."
        )
    if multiple_choice and distinct_answers:
        raise ValueError("Multiple-choice questions have no answers to keep distinct.")
    if distinct_answers and not any(each in TILE_TYPES for each in question_types):
        raise ValueError("A self-check tiles sheet asks none of these types: none has one answer.")
    stuck = unaskable_types(
        question_types,
        representations,
        shared,
        denominators,
        multiple_choice=multiple_choice,
        distinct_answers=distinct_answers,
    )
    if stuck:
        raise ValueError(f"No question of type {', '.join(stuck)} fits these settings.")
    names = NameDealer(NAMES)
    settings = StorySettings(tuple(representations), tuple(shared), tuple(denominators))
    if distinct_answers:
        return _tiles_sheet(count, question_types, settings, styles, names)
    types = [question_types[index % len(question_types)] for index in range(count)]
    random.shuffle(types)
    used: set[frozenset[UnreducedFraction]] = set()
    return [
        _question(each, settings, random.choice(styles), names, used, multiple_choice)
        for each in types
    ]


def unaskable_types(
    question_types: Sequence[Type],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    *,
    multiple_choice: bool = False,
    distinct_answers: bool = False,
) -> list[Type]:
    """
    Return the types among ``question_types`` that no question can be made of with these
    settings: no ticked representation shows two fractions sharing a ticked kind of number (three
    for greatest and least), no story can be told, no area representation is ticked for less or
    greater, or none of strips, grids, circles, other shapes and number lines with a denominator
    up to ``DRAW_MOST_PARTS`` for draw and compare.

    With ``distinct_answers``, the types that aren't asked on a tiles sheet are left out, not
    unaskable; compare needs a group of two fractions, or the all-or-none pair; greatest and
    least needs a three with Compare ticked, else a group of four.
    """
    settings = StorySettings(tuple(representations), tuple(shared), tuple(denominators))
    if distinct_answers:
        pool = make_pool(representations, shared, denominators, sample=False)
        return [
            each
            for each in question_types
            if each in TILE_TYPES and not _tile_askable(each, question_types, settings, pool)
        ]
    return [each for each in question_types if not _askable(each, settings, multiple_choice)]


def count_possible_answers(
    question_types: Sequence[Type],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
) -> int:
    """
    Return the most questions ``distinct_answers`` allows for ``question_types``: the fractions
    the groups can take, as written, and two for the all-or-none pair when Compare can ask it.
    Word problems, answered by names, add one for each name in ``NAMES``, more than a sheet of
    tiles needs. Not every smaller count can be made: see ``tile_count_fits``.
    """
    kinds = [each for each in question_types if each in TILE_TYPES]
    pool = make_pool(representations, shared, denominators, sample=False)
    fraction = 0
    if Type.COMPARE in kinds:
        every = _every_possible(representations, shared, denominators)
        fraction = capacity(pool, PAIRS_AND_THREES) + (2 if every else 0)
    elif Type.GREATEST in kinds:
        fraction = capacity(pool, GREATEST_GROUP[0])
    return fraction + (len(NAMES) if Type.WORD in kinds else 0)


def tile_count_fits(
    count: int,
    question_types: Sequence[Type],
    representations: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
) -> bool:
    """
    Return whether a tiles sheet of ``count`` questions of ``question_types`` can be made, up to
    ``count_possible_answers``: the fraction questions, after word problems take their share,
    must split into groups, at least two or none at a time, and at least four with Greatest and
    least alone; word problems come at least two at a time. For example, with only halves and
    thirds sharing a numerator, pairs alone can't make 3 compare questions.
    """
    kinds = [each for each in question_types if each in TILE_TYPES]
    pool = make_pool(representations, shared, denominators, sample=False)
    every = Type.COMPARE in kinds and _every_possible(representations, shared, denominators)
    return _fraction_slots(count, kinds, pool, every) is not None


# --- which types can be asked


def _fits(
    reps: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    need: Need,
) -> bool:
    """Return whether one of ``reps`` shows fractions for ``need`` sharing a ticked number."""
    return any(can_pick(rep, kind, denominators, need) for kind in shared for rep in reps)


def _askable(question_type: Type, settings: StorySettings, choices: bool) -> bool:
    """Return whether a question of ``question_type`` can be made with ``settings``."""
    reps, shared, denominators = settings.reps, settings.shared, settings.denominators
    match question_type:
        case Type.COMPARE:
            return _fits(reps, shared, denominators, Need())
        case Type.EXPLAIN:
            return _fits(reps, shared, denominators, _explain_need(choices))
        case Type.WORD:
            return bool(story_ways(settings, Need()))
        case Type.LESS_GREATER:
            return any(
                _less_greater_candidates(settings, greater, choices) for greater in (True, False)
            )
        case Type.DRAW:
            return _fits(_draw_reps(reps), shared, _draw_denominators(denominators), Need())
        case _:
            return _fits(reps, shared, denominators, Need(size=3))


def _tile_askable(
    question_type: Type, question_types: Sequence[Type], settings: StorySettings, pool: Pool
) -> bool:
    """Return whether a tiles sheet can ask ``question_type`` with ``settings``."""
    match question_type:
        case Type.COMPARE:
            return capacity(pool, PAIRS_AND_THREES) >= PAIRS_AND_THREES or _every_possible(
                settings.reps, settings.shared, settings.denominators
            )
        case Type.GREATEST if Type.COMPARE in question_types:
            return any(len(group) >= 3 for group in (*pool.by_denominator, *pool.by_numerator))
        case Type.GREATEST:
            return capacity(pool, GREATEST_GROUP[0]) >= GREATEST_GROUP[0]
        case _:
            return bool(story_ways(settings, Need()))


def _every_possible(
    reps: Sequence[Representation], shared: Sequence[Shared], denominators: Sequence[int]
) -> bool:
    """Return whether "Which of these are greater than 3/8?" can be asked with all three on one
    side: it has no picture, so it needs no picture ticked."""
    return Representation.NONE in reps and can_ask_every(shared, denominators)


def _explain_need(choices: bool) -> Need:
    """Return what an explain question's fractions must be: with ``choices``, numerators of 2
    or more when they share a denominator, for the mistake that reads them as part sizes."""
    return Need(least_top=2) if choices else Need()


def _draw_reps(reps: Sequence[Representation]) -> list[Representation]:
    """Return the ticked representations a whole or a line to divide can be drawn in."""
    return [rep for rep in reps if rep in DRAW_REPRESENTATIONS]


def _draw_denominators(denominators: Sequence[int]) -> list[int]:
    """Return the denominators a student is asked to divide a whole or a line into."""
    return [parts for parts in denominators if parts <= DRAW_MOST_PARTS]


def _less_greater_candidates(
    settings: StorySettings, greater: bool, choices: bool
) -> tuple[tuple[Representation, UnreducedFraction], ...]:
    """Return each area representation ticked and fraction short of a whole it shows alone
    that a less (or greater) question can be about."""
    return _less_greater_table(settings, greater, choices)


@cache
def _less_greater_table(
    settings: StorySettings, greater: bool, choices: bool
) -> tuple[tuple[Representation, UnreducedFraction], ...]:
    """``_less_greater_candidates``, worked out once for each set of settings."""
    return tuple(
        (rep, UnreducedFraction(top, parts))
        for rep in settings.reps
        if rep in AREA_REPRESENTATIONS
        for parts in settings.denominators
        if can_show(rep, [parts])
        for top in range(1, parts)
        if less_greater_fits(
            UnreducedFraction(top, parts),
            greater,
            rep,
            settings.shared,
            choices,
        )
    )


# --- making the questions


def _choose(
    reps: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    need: Need,
) -> tuple[Representation, Shared]:
    """Return a representation and a kind of sharing for ``need``: the kind first, with even
    chance among those some representation fits, then one of those representations."""
    fitting = {
        kind: [rep for rep in reps if can_pick(rep, kind, denominators, need)] for kind in shared
    }
    kind = random.choice([each for each in shared if fitting[each]])
    return random.choice(fitting[kind]), kind


def _question(
    question_type: Type,
    settings: StorySettings,
    style: FractionStyle,
    names: NameDealer,
    used: set[frozenset[UnreducedFraction]],
    choices: bool,
) -> ComparingFractionsQuestion:
    """Make a question of ``question_type``, its fractions written in ``style``."""
    reps, shared, denominators = settings.reps, settings.shared, settings.denominators
    match question_type:
        case Type.COMPARE:
            if Representation.NONE in reps and random.random() < EVERY_SHARE:
                every = every_question(shared, denominators, style, used, choices)
                if every is not None:
                    return every
            need = Need(equal=random.random() < EQUAL_SHARE)
            if not _fits(reps, shared, denominators, need):
                need = Need()
            rep, kind = _choose(reps, shared, denominators, need)
            pair = pick(rep, kind, denominators, need, style, used)
            return compare_question((pair[0], pair[1]), rep, shared, denominators, choices)
        case Type.EXPLAIN:
            need = _explain_need(choices)
            rep, kind = _choose(reps, shared, denominators, need)
            pair = pick(rep, kind, denominators, need, style, used)
            return explain_question((pair[0], pair[1]), rep, denominators, choices)
        case Type.WORD:
            return make_word_question(settings, style, names, used, choices)
        case Type.LESS_GREATER:
            first = random.random() < GREATER_SHARE
            greater = first if _less_greater_candidates(settings, first, choices) else not first
            candidates = _less_greater_candidates(settings, greater, choices)
            rep = random.choice(list(dict.fromkeys(rep for rep, _ in candidates)))
            of_rep = [fraction for each, fraction in candidates if each is rep]
            parts = random.choice(sorted({each.denominator for each in of_rep}))
            fraction = random.choice([each for each in of_rep if each.denominator == parts])
            return less_greater_question(
                replace(fraction, style=style), greater, rep, shared, choices
            )
        case Type.DRAW:
            small = _draw_denominators(denominators)
            rep, kind = _choose(_draw_reps(reps), shared, small, Need())
            pair = pick(rep, kind, small, Need(), style, used)
            return draw_question((pair[0], pair[1]), rep, choices)
        case _:
            four = random.random() < FOUR_SHARE and _fits(reps, shared, denominators, Need(size=4))
            need = Need(size=4 if four else 3)
            rep, kind = _choose(reps, shared, denominators, need)
            fractions = pick(rep, kind, denominators, need, style, used)
            return greatest_question(fractions, rep, denominators, random.random() < 0.5, choices)


# --- a self-check tiles sheet


def _fraction_slots(count: int, kinds: Sequence[Type], pool: Pool, every: bool) -> int | None:
    """
    Return how many of a tiles sheet's ``count`` questions are about fractions, not word
    problems: their even share among ``kinds``, or one more when word problems' share is one,
    since names come at least two at a time, or fewer when word problems are ticked and the
    fractions can't fill it, down to none. Return ``None`` if no number can be made.
    """
    word = Type.WORD in kinds
    if not any(each in kinds for each in (Type.COMPARE, Type.GREATEST)):
        return 0 if count != 1 else None
    share = [kinds[index % len(kinds)] for index in range(count)]
    fraction = count - share.count(Type.WORD)
    order = [fraction]
    if word:
        order = ([fraction + 1] if count - fraction == 1 else []) + list(range(fraction, -1, -1))
    fewest = PAIRS_AND_THREES if Type.COMPARE in kinds else GREATEST_GROUP[0]
    return next(
        (each for each in order if count - each != 1 and _fraction_fits(pool, each, fewest, every)),
        None,
    )


def _fraction_fits(pool: Pool, total: int, fewest: int, every: bool) -> bool:
    """Return whether ``total`` fraction questions can be made: in groups, or with the
    all-or-none pair as two of them when ``every``."""
    if total == 0 or fills(pool, total, fewest):
        return True
    return every and total >= 2 and (total == 2 or fills(pool, total - 2, fewest))


def _tiles_sheet(
    count: int,
    question_types: Sequence[Type],
    settings: StorySettings,
    styles: Sequence[FractionStyle],
    names: NameDealer,
) -> list[ComparingFractionsQuestion]:
    """
    Return a tiles sheet's questions, as ``generate_comparing_fractions_questions`` describes,
    shuffled. The fractions come from a sample of the denominators when there are many, or from
    the smallest if the sample can't fill the sheet. The all-or-none pair comes on
    ``EVERY_PAIR_SHARE`` of sheets that can have it, and on any sheet that needs it to fill.
    """
    reps, shared, denominators = settings.reps, settings.shared, settings.denominators
    kinds = [each for each in question_types if each in TILE_TYPES]
    every = Type.COMPARE in kinds and _every_possible(reps, shared, denominators)
    pool = make_pool(reps, shared, denominators, sample=True)
    fraction = _fraction_slots(count, kinds, pool, every)
    if fraction is None:
        pool = make_pool(reps, shared, denominators, sample=False)
        fraction = _fraction_slots(count, kinds, pool, every)
    if fraction is None:
        raise ValueError(f"A tiles sheet of these types can't have {count} questions.")
    fewest = PAIRS_AND_THREES if Type.COMPARE in kinds else GREATEST_GROUP[0]
    grouped = fills(pool, fraction, fewest)
    use_every = (
        every
        and fraction >= 2
        and (fraction == 2 or fills(pool, fraction - 2, fewest))
        and (not grouped or random.random() < EVERY_PAIR_SHARE)
    )
    want_three = Type.GREATEST in kinds and Type.COMPARE in kinds
    groups = plan_groups(pool, fraction - 2 * use_every, fewest, want_three)
    questions: list[ComparingFractionsQuestion] = []
    for group in groups:
        style = random.choice(styles)
        styled = tuple(replace(each, style=style) for each in group)
        questions += _group_questions(styled, Type.GREATEST in kinds, fewest, settings)
    if use_every:
        style = random.choice(styles)
        used_every: set[frozenset[UnreducedFraction]] = set()
        for all_or_none in (True, False):
            every_one = every_question(shared, denominators, style, used_every, False, all_or_none)
            if every_one is None:
                raise ValueError("No fractions fit an all-or-none question.")
            questions.append(every_one)
    words = count - fraction
    if words:
        used: set[frozenset[UnreducedFraction]] = set()
        more_or_less = bool(story_ways(settings, Need(), more_or_less=True))
        specs = name_answers(words, names, MORE_LESS_PAIR_SHARE, more_or_less)
        for spec in specs:
            style = random.choice(styles)
            questions.append(make_word_question(settings, style, names, used, False, spec))
    random.shuffle(questions)
    return questions


def _group_questions(
    group: Group, greatest: bool, fewest: int, settings: StorySettings
) -> list[GreatestQuestion]:
    """
    Return the questions about ``group``, sorted from the least, each answered by one of its
    fractions and offering others: a pair asks which is greater and which is less, one with a
    picture and one without when both can be; a three a, b, c asks the greater of a and b, the
    less of a and c, and the greatest of all three, or with ``greatest`` false, the greater of
    b and c. A group of four or more is asked as ``_greatest_sets`` gives.
    """
    sets: list[tuple[tuple[int, ...], bool]]
    if fewest == PAIRS_AND_THREES and len(group) == 2:
        sets = [((0, 1), True), ((0, 1), False)]
    elif fewest == PAIRS_AND_THREES:
        sets = [((0, 1), True), ((0, 2), False), ((0, 1, 2) if greatest else (1, 2), True)]
    else:
        sets = _greatest_sets(len(group))
    offered = [
        tuple(random.sample([group[index] for index in each], len(each))) for each, _ in sets
    ]
    reps = [_tile_reps(each, settings.reps) for each in offered]
    chosen = [random.choice(each) for each in reps]
    if len(group) == 2 and fewest == PAIRS_AND_THREES:
        chosen = _one_pictured(reps) or chosen
    return [
        greatest_question(fractions, rep, settings.denominators, asks_greatest, False)
        for fractions, rep, (_, asks_greatest) in zip(offered, chosen, sets, strict=True)
    ]


def _greatest_sets(size: int) -> list[tuple[tuple[int, ...], bool]]:
    """
    Return the questions about a group of ``size`` fractions, four or more, as the positions of
    the fractions each offers, from the least, and whether it asks for the greatest: the least
    and the greatest of the two least and two greatest (all four of a four), the least of the
    second, third and fourth, the greatest of the three below the second greatest, and each
    fraction between the third and the third greatest as the greatest of itself and the two
    below it. Each fraction answers one question and is offered by at least one other.
    """
    last = size - 1
    ends = (0, 1, last - 1, last)
    sets = [(ends, False), (ends, True), ((1, 2, 3), False), ((last - 3, last - 2, last - 1), True)]
    sets += [((index - 2, index - 1, index), True) for index in range(2, last - 1)]
    return sets


def _tile_reps(
    fractions: Sequence[UnreducedFraction], reps: Sequence[Representation]
) -> list[Representation]:
    """Return the ticked representations that show ``fractions`` together, no picture
    included when it's ticked."""
    return [rep for rep in reps if can_show(rep, [each.denominator for each in fractions])]


def _one_pictured(reps: Sequence[Sequence[Representation]]) -> list[Representation] | None:
    """Return a representation for each of a pair's two questions, one with no picture and the
    other with a picture, in a random order, or ``None`` if both can't be."""
    pictured = [[rep for rep in each if rep is not Representation.NONE] for each in reps]
    if not all(Representation.NONE in each for each in reps) or not all(pictured):
        return None
    first_pictured = random.random() < 0.5
    return [
        random.choice(pictured[0]) if first_pictured else Representation.NONE,
        Representation.NONE if first_pictured else random.choice(pictured[1]),
    ]
