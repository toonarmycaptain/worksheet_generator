"""
Making each kind of comparing fractions question from the fractions chosen for it: its pictures,
its answer, and as multiple choice, its options.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass

from core.comparing_fractions.choices import (
    bare_comparisons,
    either_way,
    explanation,
    explanation_choices,
    less_greater_choices,
    less_greater_shows_choices,
    less_greater_ways,
    pick_choices,
    pictured_comparisons,
    reason_choices,
    story_choices,
    symbol,
    true_comparison,
)
from core.comparing_fractions.data import (
    ALL_OF_THESE,
    CANT_TELL,
    LESS,
    MORE,
    SAME,
    CompareQuestion,
    CompareQuestionData,
    DrawAsked,
    DrawQuestion,
    DrawQuestionData,
    EveryQuestion,
    EveryQuestionData,
    ExplainForm,
    ExplainQuestion,
    ExplainQuestionData,
    GreatestQuestion,
    GreatestQuestionData,
    LessGreaterForm,
    LessGreaterQuestion,
    LessGreaterQuestionData,
    Picture,
    Representation,
    Shared,
    StoryForm,
    StoryKind,
    WordAsked,
    WordQuestion,
    WordQuestionData,
)
from core.comparing_fractions.picks import Need, can_pick, pick
from core.comparing_fractions.pictures import (
    blank,
    blank_like,
    can_draw_like,
    like,
    model_options,
    show,
    wall,
)
from core.comparing_fractions.stories import GROUP_STORIES, LENGTH_STORIES, WHOLE_STORIES
from core.fraction_models.answers import WRONG_OPTIONS, Asked, NameAnswer
from core.fraction_models.area_models import WALL_LIMITS, AreaModel, FractionWall
from core.fraction_models.number_lines import FractionLine, LengthUnit
from core.names import NameDealer
from core.question import FreeResponse, MultipleChoice, Question, multiple_choice
from core.written_numbers import FractionStyle, UnreducedFraction

IN_WORDS_SHARE = 0.25  # of multiple-choice comparisons, those written in words
EQUAL_SHARE = 0.1  # of compare questions and word problems, those comparing a fraction with itself
# Of word problems about wholes that can be different sizes, those that are: about 1 word problem
# in 10, with a third of the stories about wholes
CANT_TELL_SHARE = 0.3
WORD_PICTURE_SHARE = 1 / 3  # of word problems that can be drawn, those that are
SENTENCE_SHARE = 0.5  # of written word problems that can be a sentence to circle, those that are
EVERY_ALL_SHARE = 0.5  # of multiple-choice "which is greater than" questions, those all right
EVERY_TOPS_TRIED = 30  # numerators tried for a target over each denominator: 1 to this

type Pair = tuple[UnreducedFraction, UnreducedFraction]


def shown(
    rep: Representation,
    fractions: Sequence[UnreducedFraction],
    denominators: Sequence[int],
    extra: Sequence[UnreducedFraction] = (),
) -> tuple[tuple[Picture, ...], FractionWall | None]:
    """Return the pictures of ``fractions`` in ``rep``, or a wall with rows for them and for
    ``extra``, or neither."""
    if rep is Representation.NONE:
        return (), None
    if rep is Representation.WALL:
        needed = {each.denominator for each in (*fractions, *extra)}
        return (), wall(needed, denominators)
    return show(rep, fractions), None


def compare_question(
    pair: Pair,
    rep: Representation,
    shared: Sequence[Shared],
    denominators: Sequence[int],
    choices: bool,
) -> CompareQuestion:
    """
    Make a question comparing ``pair`` with >, < or =, shown in ``rep``: with ``choices``,
    "Which comparison is true?". Beside pictures, the wrong comparisons misread them; written or
    beside a wall, they're four different pairs (see ``bare_comparisons``), which the wall has
    rows for.
    """
    answer = symbol(*pair)
    in_words = choices and random.random() < IN_WORDS_SHARE
    if not choices:
        pictures, fraction_wall = shown(rep, pair, denominators)
        data = CompareQuestionData(pair, pictures, fraction_wall, False, answer)
        return Question(data, FreeResponse())
    right = true_comparison(pair)
    if rep in (Representation.NONE, Representation.WALL):
        usable = denominators
        if rep is Representation.WALL:
            usable = [each for each in denominators if each <= WALL_LIMITS.alone]
        wrong = bare_comparisons(pair, shared, usable)
        extra = [fraction for each in wrong for fraction in (each.left, each.right)]
        pictures, fraction_wall = shown(rep, pair, denominators, extra)
    else:
        pictures, fraction_wall = shown(rep, pair, denominators)
        wrong = pictured_comparisons(pair, pictures)
    data = CompareQuestionData(pair, pictures, fraction_wall, in_words, answer)
    return Question(data, multiple_choice((right,), tuple(either_way(each) for each in wrong)))


def every_question(
    shared: Sequence[Shared],
    denominators: Sequence[int],
    style: FractionStyle,
    used: set[frozenset[UnreducedFraction]],
    choices: bool,
    all_or_none: bool | None = None,
) -> EveryQuestion | None:
    """
    Make a question asking which of three fractions are greater (or less) than another, each
    sharing a numerator or a denominator with it as ``shared`` allows, or ``None`` if the
    denominators allow none. With ``all_or_none``, for a tiles sheet, all three are, or with
    ``False``, none; with ``choices``, all three are ``EVERY_ALL_SHARE`` of the time, else
    exactly one, beside "All of these"; written, one to three of them are. Its four fractions
    aren't a set in ``used`` while there are others, and are added to it.
    """
    if all_or_none is not None:
        counts = [3 if all_or_none else 0]
    elif choices:
        counts = [3 if random.random() < EVERY_ALL_SHARE else 1]
    else:
        counts = random.sample([1, 2, 3], 3)
    chosen: tuple[int, UnreducedFraction, bool, tuple[UnreducedFraction, ...]] | None = None
    for count in counts:
        found = _every_fractions(shared, denominators, count, style, used)
        if found is not None and (chosen is None or found[3]):
            chosen = (count, *found[:3])
            if found[3]:
                break
    if chosen is None:
        return None
    count, target, greater, offered = chosen
    used.add(frozenset((target, *offered)))
    answer = tuple(each for each in offered if (each.value > target.value) == greater)
    data = EveryQuestionData(target, greater, offered, answer)
    if not choices:
        return Question(data, FreeResponse())
    options: tuple[UnreducedFraction | str, ...] = (*offered, ALL_OF_THESE)
    right = len(offered) if count == 3 else offered.index(answer[0])
    return Question(data, MultipleChoice(options, frozenset({right})))


def _every_fractions(
    shared: Sequence[Shared],
    denominators: Sequence[int],
    count: int,
    style: FractionStyle,
    used: set[frozenset[UnreducedFraction]],
) -> tuple[UnreducedFraction, bool, tuple[UnreducedFraction, ...], bool] | None:
    """Return a target, whether the question asks for greater, three fractions in a random
    order, ``count`` of them on the asked side of the target, and whether they're a set not in
    ``used``: the first such set, else the first found, or ``None``."""
    fallback = None
    for parts in random.sample(list(denominators), len(denominators)):
        tried = min(parts, EVERY_TOPS_TRIED)
        for top in random.sample(range(1, tried + 1), tried):
            target = UnreducedFraction(top, parts, style)
            others = sharing(target, shared, denominators)
            for greater in random.sample([True, False], 2):
                asked = [each for each in others if (each.value > target.value) == greater]
                other_side = [each for each in others if (each.value > target.value) != greater]
                if len(asked) >= count and len(other_side) >= WRONG_OPTIONS - count:
                    offered = random.sample(asked, count) + random.sample(
                        other_side, WRONG_OPTIONS - count
                    )
                    random.shuffle(offered)
                    if frozenset((target, *offered)) not in used:
                        return target, greater, tuple(offered), True
                    fallback = fallback or (target, greater, tuple(offered), False)
    return fallback


def can_ask_every(shared: Sequence[Shared], denominators: Sequence[int]) -> bool:
    """Return whether ``every_question`` can be asked with all three fractions on one side of the
    target, as its "all of them" and "none of them" tiles need: a target with three fractions
    sharing a number with it on one side, among the numerators it tries."""
    for parts in denominators:
        for top in range(1, min(parts, EVERY_TOPS_TRIED) + 1):
            target = UnreducedFraction(top, parts)
            others = sharing(target, shared, denominators)
            greater = sum(1 for each in others if each.value > target.value)
            if max(greater, len(others) - greater) >= WRONG_OPTIONS:
                return True
    return False


def sharing(
    target: UnreducedFraction, shared: Sequence[Shared], denominators: Sequence[int]
) -> list[UnreducedFraction]:
    """Return the fractions that share ``target``'s numerator or denominator, as ``shared``
    allows, from ``denominators``, with values other than its own, up to a whole."""
    found: dict[object, UnreducedFraction] = {}
    style = target.style
    if Shared.DENOMINATOR in shared:
        for top in range(1, target.denominator + 1):
            if top != target.numerator:
                fraction = UnreducedFraction(top, target.denominator, style)
                found[fraction.value] = fraction
    if Shared.NUMERATOR in shared:
        for parts in denominators:
            if parts != target.denominator and parts >= target.numerator:
                fraction = UnreducedFraction(target.numerator, parts, style)
                found.setdefault(fraction.value, fraction)
    return list(found.values())


def explain_question(
    pair: Pair, rep: Representation, denominators: Sequence[int], choices: bool
) -> ExplainQuestion:
    """Make a question comparing ``pair`` and saying why, shown in ``rep``, in one of its forms
    with even chance: written, circle the words or write and explain; with ``choices``, choose a
    comparison with its explanation, or the reason for the true comparison."""
    pictures, fraction_wall = shown(rep, pair, denominators)
    answer = explanation(pair, bool(pictures))
    in_words = choices and random.random() < IN_WORDS_SHARE
    if choices:
        form = random.choice((ExplainForm.PAIR, ExplainForm.WHY))
    else:
        form = random.choice((ExplainForm.CIRCLE, ExplainForm.WRITE))
    data = ExplainQuestionData(pair, pictures, fraction_wall, in_words, form, answer)
    if form is ExplainForm.PAIR:
        return Question(data, multiple_choice((answer,), explanation_choices(answer, pictures)))
    if form is ExplainForm.WHY:
        modelled = bool(pictures) and not any(isinstance(each, FractionLine) for each in pictures)
        wrong = reason_choices(answer, modelled)
        return Question(data, multiple_choice((answer.reason,), wrong))
    return Question(data, FreeResponse())


def word_question(
    kind: StoryKind,
    story: int,
    names: tuple[str, str],
    pair: Pair,
    *,
    unit: LengthUnit | None,
    sizes: tuple[str, str] | None,
    greater: bool,
    more_or_less: bool,
    asked: WordAsked,
    rep: Representation,
    form: StoryForm | None,
) -> WordQuestion:
    """
    Make a word problem of ``names`` having ``pair``, in order, from ``kind``'s bank's story
    ``story``, asking who has the greater share (or smaller), or whether the first has more or
    less: its two wholes, lengths or groups drawn in ``rep``, unless it's no picture; with
    ``form``, multiple choice in that form.
    """
    first, second = names
    left, right = pair
    winner = None if left.value == right.value else (first if left.value > right.value else second)
    loser = None if winner is None else (second if winner == first else first)
    if sizes is not None:
        answer = CANT_TELL
    elif more_or_less:
        answer = MORE if left.value > right.value else LESS
    elif winner is None:
        answer = SAME
    else:
        answer = winner if greater else (loser or second)
    pictures: tuple[Picture, ...] = ()
    if rep is not Representation.NONE:
        pictures = _story_pictures(kind, story, rep, pair, unit)
    data = WordQuestionData(
        kind,
        story,
        names,
        pair,
        unit,
        sizes,
        greater,
        more_or_less,
        asked,
        form,
        pictures,
        answer,
    )
    if form is None:
        return Question(data, FreeResponse())
    right_choice, wrong = story_choices(form, names, pair, answer, winner, sizes is None, greater)
    return Question(data, multiple_choice((right_choice,), wrong))


def _story_pictures(
    kind: StoryKind, story: int, rep: Representation, pair: Pair, unit: LengthUnit | None
) -> tuple[Picture, ...]:
    """Return a word problem's two wholes, in ``rep``, lengths or groups, drawn: a length that
    moves as jumps from 0, one that's measured as a shaded bar."""
    match kind:
        case StoryKind.WHOLE:
            return show(rep, pair, look=WHOLE_STORIES[story].look)
        case StoryKind.LENGTH:
            length = LENGTH_STORIES[story]
            marking = "bar" if length.tail else "jumps"
            return show(Representation.LINE, pair, unit=unit, marking=marking)
        case _:
            return show(Representation.GROUP, pair, kind=GROUP_STORIES[story].kind)


def less_greater_question(
    fraction: UnreducedFraction,
    greater: bool,
    rep: Representation,
    shared: Sequence[Shared],
    choices: bool,
) -> LessGreaterQuestion:
    """
    Make a question showing ``fraction`` shaded in ``rep``, about ways to show a fraction less
    (or greater), in one of the forms that fit, with even chance: written, divide and shade
    three blank wholes (three ways in the key), circle every model of four that's a way, or
    write a way; with ``choices``, which is NOT a way, or which model shows one, each drawn as
    the model is. ``less_greater_fits`` must allow it.
    """
    ways, nots = less_greater_ways(fraction, greater, shared)
    drawn = [_drawn_ways(each, ways, nots) for each in model_options(rep, fraction)]
    if choices:
        forms = {
            LessGreaterForm.NOT_A_WAY: [
                each for each in drawn if len(each[1]) >= WRONG_OPTIONS and each[2]
            ],
            LessGreaterForm.SHOWS: [
                each for each in drawn if each[1] and len(each[2]) >= WRONG_OPTIONS
            ],
        }
    else:
        forms = {
            LessGreaterForm.DIVIDE: drawn,
            LessGreaterForm.CIRCLE: [
                each for each in drawn if each[1] and each[2] and len(each[1]) + len(each[2]) > 3
            ],
            LessGreaterForm.WRITE: drawn,
        }
    form = random.choice([each for each, fitting in forms.items() if fitting])
    model, drawn_ways, drawn_nots = random.choice(forms[form])
    blank_model = blank_like(model)
    if form is LessGreaterForm.NOT_A_WAY or form is LessGreaterForm.SHOWS:
        if form is LessGreaterForm.NOT_A_WAY:
            right, wrong = less_greater_choices(fraction, drawn_ways, drawn_nots, greater)
        else:
            right, wrong = less_greater_shows_choices(fraction, drawn_ways, drawn_nots, greater)
        data = LessGreaterQuestionData(fraction, greater, form, model, blank_model, (), (right,))
        pictures = tuple(like(model, each) for each in wrong)
        return Question(data, multiple_choice((like(model, right),), pictures))
    if form is LessGreaterForm.CIRCLE:
        counts = [
            count
            for count in range(1, 4)
            if count <= len(drawn_ways) and 4 - count <= len(drawn_nots)
        ]
        count = random.choice(counts)
        circled = random.sample(drawn_ways, count) + random.sample(drawn_nots, 4 - count)
        random.shuffle(circled)
        answer = tuple(each for each in circled if each in drawn_ways)
        pictures = tuple(like(model, each) for each in circled)
        data = LessGreaterQuestionData(
            fraction, greater, form, model, blank_model, pictures, answer
        )
        return Question(data, FreeResponse())
    if form is LessGreaterForm.WRITE:
        data = LessGreaterQuestionData(fraction, greater, form, model, blank_model, (), tuple(ways))
        return Question(data, FreeResponse())
    examples = tuple(sorted(random.sample(ways, WRONG_OPTIONS), key=lambda each: each.value))
    data = LessGreaterQuestionData(fraction, greater, form, model, blank_model, (), examples)
    return Question(data, FreeResponse())


def less_greater_fits(
    fraction: UnreducedFraction,
    greater: bool,
    rep: Representation,
    shared: Sequence[Shared],
    choices: bool,
) -> bool:
    """Return whether ``less_greater_question`` can show ``fraction`` in ``rep``: written, three
    ways to show a fraction less (or greater); with ``choices``, three ways and one that isn't,
    or one way and three that aren't, that can be drawn as one of the models of ``fraction``
    is."""
    ways, nots = less_greater_ways(fraction, greater, shared)
    if not choices:
        return len(ways) >= WRONG_OPTIONS
    return any(
        (len(drawn_ways) >= WRONG_OPTIONS and drawn_nots)
        or (drawn_ways and len(drawn_nots) >= WRONG_OPTIONS)
        for _, drawn_ways, drawn_nots in (
            _drawn_ways(model, ways, nots) for model in model_options(rep, fraction)
        )
    )


def _drawn_ways(
    model: AreaModel, ways: Sequence[UnreducedFraction], nots: Sequence[UnreducedFraction]
) -> tuple[AreaModel, list[UnreducedFraction], list[UnreducedFraction]]:
    """Return ``model`` with those of ``ways`` and of ``nots`` that can be drawn as it is."""
    return (
        model,
        [each for each in ways if can_draw_like(model, each.denominator)],
        [each for each in nots if can_draw_like(model, each.denominator)],
    )


def draw_question(pair: Pair, rep: Representation, choices: bool) -> DrawQuestion:
    """Make a question asking to divide and shade two blank wholes, or mark two number lines, in
    ``rep`` to show ``pair``, then write >, < or =, or with even chance, say which fraction is
    greater, or less, evenly: with ``choices``, which comparison is true, or which fraction,
    picked with a comparison."""
    whole = blank(rep, [each.denominator for each in pair])
    if random.random() < 0.5:
        asked = DrawAsked.SYMBOL
    else:
        asked = random.choice((DrawAsked.GREATER, DrawAsked.LESS))
    data = DrawQuestionData(pair, (whole, whole), asked, symbol(*pair))
    if not choices:
        return Question(data, FreeResponse())
    if asked is DrawAsked.SYMBOL:
        wrong = tuple(either_way(each) for each in pictured_comparisons(pair, (whole,)))
        return Question(data, multiple_choice((true_comparison(pair),), wrong))
    right, wrong_picks = pick_choices(pair, asked is DrawAsked.GREATER)
    return Question(data, multiple_choice((right,), wrong_picks))


def greatest_question(
    fractions: Sequence[UnreducedFraction],
    rep: Representation,
    denominators: Sequence[int],
    greatest: bool,
    choices: bool,
) -> GreatestQuestion:
    """Make a question asking which of ``fractions`` is the greatest, or the least, shown in
    ``rep``: with ``choices``, the fractions are lettered, or the pictures are."""
    pictures, fraction_wall = shown(rep, fractions, denominators)
    pick = max if greatest else min
    answer = pick(fractions, key=lambda each: each.value)
    data = GreatestQuestionData(tuple(fractions), greatest, pictures, fraction_wall, answer)
    if not choices:
        return Question(data, FreeResponse())
    right = frozenset({list(fractions).index(answer)})
    if pictures:
        return Question(data, MultipleChoice(pictures, right))
    return Question(data, MultipleChoice(tuple(fractions), right))


# --- choosing a word problem's story


@dataclass(frozen=True)
class StorySettings:
    """A sheet's settings that a word problem's story must fit: its ticked ``reps``, what its
    fractions may share, and its ``denominators``."""

    reps: tuple[Representation, ...]
    shared: tuple[Shared, ...]
    denominators: tuple[int, ...]


def story_rep(kind: StoryKind, story: int) -> Representation | None:
    """Return how a story's two wholes, lengths or groups are drawn, if they can be."""
    match kind:
        case StoryKind.WHOLE:
            return WHOLE_STORIES[story].representation
        case StoryKind.LENGTH:
            return Representation.LINE
        case _:
            return Representation.GROUP


def asks_more_or_less(kind: StoryKind, story: int) -> bool:
    """Return whether a story can ask "Does Ana eat more or less than Ben?": a whole's, or a
    length that's travelled, "Does Ana's frog jump more or less than Ben's?"."""
    return kind is StoryKind.WHOLE or (kind is StoryKind.LENGTH and not LENGTH_STORIES[story].tail)


def story_ways(
    settings: StorySettings, need: Need, more_or_less: bool = False
) -> list[tuple[StoryKind, int, Representation]]:
    """
    Return each way a story can be told with these settings, as (kind, position,
    representation): with no picture ticked, any story, unpictured (``Representation.NONE``),
    and pictured as well when its representation is ticked and can show fractions for ``need``;
    with no picture unticked, only pictured ones. With ``more_or_less``, only stories that can
    ask it.
    """
    ways: list[tuple[StoryKind, int, Representation]] = []
    banks = (
        (StoryKind.WHOLE, len(WHOLE_STORIES)),
        (StoryKind.LENGTH, len(LENGTH_STORIES)),
        (StoryKind.GROUP, len(GROUP_STORIES)),
    )
    unpictured = Representation.NONE in settings.reps and any(
        can_pick(Representation.NONE, kind, settings.denominators, need) for kind in settings.shared
    )
    for kind, size in banks:
        for story in range(size):
            if more_or_less and not asks_more_or_less(kind, story):
                continue
            if unpictured:
                ways.append((kind, story, Representation.NONE))
            rep = story_rep(kind, story)
            if (
                rep is not None
                and rep in settings.reps
                and any(
                    can_pick(rep, shared, settings.denominators, need) for shared in settings.shared
                )
            ):
                ways.append((kind, story, rep))
    return ways


def make_word_question(
    settings: StorySettings,
    style: FractionStyle,
    names: NameDealer,
    used: set[frozenset[UnreducedFraction]],
    choices: bool,
    spec: NameAnswer | None = None,
) -> WordQuestion:
    """
    Make a word problem: its kind of story drawn first, each kind with even chance, then a story,
    then whether it's pictured (``WORD_PICTURE_SHARE`` of the time, unless no picture is
    unticked), then its fractions, sharing a numerator or a denominator with even chance. About
    ``EQUAL_SHARE`` compare a fraction with itself; about ``CANT_TELL_SHARE`` of the wholes that
    can be different sizes are, the smaller whole with the greater fraction, so there's no
    telling who has more. A written problem asks who, or a sentence to circle,
    ``SENTENCE_SHARE`` of the time when it can; multiple choice is in one of the forms, evenly.

    With ``spec``, for a tiles sheet, the problem is about its names and has its answer, a name
    or "more" or "less", never equal or different sizes.
    """
    more_or_less = spec is not None and spec.asked is Asked.MORE_OR_LESS
    equal = spec is None and random.random() < EQUAL_SHARE
    need = Need(equal=equal)
    # a fraction with itself fits wherever two different fractions do, so equal leaves ways
    ways = story_ways(settings, need, more_or_less)
    kinds = sorted({kind for kind, _, _ in ways})
    kind = random.choice(kinds)
    stories = sorted({story for each, story, _ in ways if each is kind})
    story = random.choice(stories)
    reps = [rep for each, place, rep in ways if (each, place) == (kind, story)]
    if len(reps) == 2:  # unpictured first, then pictured
        rep = reps[1] if random.random() < WORD_PICTURE_SHARE else reps[0]
    else:
        rep = reps[0]
    fitting = [
        shared for shared in settings.shared if can_pick(rep, shared, settings.denominators, need)
    ]
    picked = pick(rep, random.choice(fitting), settings.denominators, need, style, used)
    low, high = sorted(picked, key=lambda each: each.value)
    pair = (low, high)
    if spec is not None:
        first, second = spec.names
        first_greater = (
            (spec.asked is Asked.GREATER and spec.answer == first)
            or (spec.asked is Asked.SMALLER and spec.answer == second)
            or (spec.asked is Asked.MORE_OR_LESS and spec.answer == MORE)
        )
        pair = (high, low) if first_greater else (low, high)
        greater = spec.asked is not Asked.SMALLER
    else:
        first, second = names.take(2)
        greater = random.random() < 0.5
    unit = random.choice(LENGTH_STORIES[story].units) if kind is StoryKind.LENGTH else None
    sizes: tuple[str, str] | None = None
    if (
        spec is None
        and kind is StoryKind.WHOLE
        and WHOLE_STORIES[story].sizes
        and pair[0].value != pair[1].value
        and random.random() < CANT_TELL_SHARE
    ):
        sizes = ("small", "large") if pair[0].value > pair[1].value else ("large", "small")
    different = pair[0].value != pair[1].value
    sentence = (
        not choices and spec is None and kind is not StoryKind.GROUP and different and sizes is None
    )
    asked = WordAsked.SENTENCE if sentence and random.random() < SENTENCE_SHARE else WordAsked.WHO
    form = None
    if choices:
        forms = [StoryForm.REASONS, StoryForm.PLAIN]
        if different and sizes is None:
            forms.append(StoryForm.WHO_SYMBOL)
        form = random.choice(forms)
    return word_question(
        kind,
        story,
        (first, second),
        pair,
        unit=unit,
        sizes=sizes,
        greater=greater,
        more_or_less=more_or_less,
        asked=asked,
        rep=rep,
        form=form,
    )
