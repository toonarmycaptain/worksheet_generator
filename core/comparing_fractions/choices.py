"""
Multiple-choice options for comparing fractions questions: true and mistaken comparisons,
explanations, word problem statements, and ways of shading a fraction.

Each wrong option comes from a common mistake: the symbol the wrong way round, a larger
denominator taken for a larger fraction, the same numerator or the same denominator taken for
equal fractions, a picture read by its unshaded parts, jumps or ticks counted for parts, and
numerators read as the sizes of parts. Exactly one option is true.
"""

import random
from collections.abc import Sequence
from fractions import Fraction
from itertools import combinations

from core.comparing_fractions.data import (
    CANT_TELL,
    EQUAL_TO,
    GREATER_THAN,
    LESS_THAN,
    SAME,
    BiggerNumber,
    Comparison,
    Explanation,
    PartSize,
    PartsOf,
    Pick,
    Picture,
    Reason,
    SameCount,
    Shared,
    StoryChoice,
    StoryForm,
    StoryReason,
    Verdict,
)
from core.fraction_models.answers import WRONG_OPTIONS
from core.fraction_models.number_lines import FractionLine
from core.written_numbers import UnreducedFraction

type Pair = tuple[UnreducedFraction, UnreducedFraction]

WRONG_PAIR_DENOMINATORS = 12  # the most denominators wrong comparisons' pairs are drawn from
# Of wrong comparisons without pictures, those that show another pair twice, not the answer's
DOUBLED_PAIR_SHARE = 0.5
# The mistakes made about one kind of pair: sharing a numerator, or a denominator
_MISTAKE_FAMILIES = (
    ("larger_denominator", "same_numerator"),
    ("same_denominator", "larger_numerator"),
)
# Each symbol as it reads with its two sides swapped
_MIRRORED = {GREATER_THAN: LESS_THAN, LESS_THAN: GREATER_THAN, EQUAL_TO: EQUAL_TO}
LESS_GREATER_PARTS = 12  # the most parts of a way to shade, unless the model has more
# Of "Which is NOT a way?" questions, those whose answer may stand out by its shaded parts
STANDOUT_SHARE = 0.25


def symbol(left: UnreducedFraction, right: UnreducedFraction) -> str:
    """Return the symbol that makes ``left`` compared with ``right`` true."""
    if left.value == right.value:
        return EQUAL_TO
    return GREATER_THAN if left.value > right.value else LESS_THAN


def is_true(comparison: Comparison) -> bool:
    """Return whether ``comparison`` is true."""
    return symbol(comparison.left, comparison.right) == comparison.symbol


def either_way(comparison: Comparison) -> Comparison:
    """Return ``comparison`` as written, or with even chance the other way round, its symbol
    mirrored, which says the same: 3/6 > 1/6, or 1/6 < 3/6. Choices written either way round
    leave no order that only the right one has. A fraction compared with itself stays as
    written, since turning 3/4 > 3/4 round would make it 3/4 < 3/4, another choice."""
    if comparison.left == comparison.right or random.random() < 0.5:
        return comparison
    return Comparison(comparison.right, _MIRRORED[comparison.symbol], comparison.left)


def true_comparison(pair: Pair) -> Comparison:
    """Return ``pair`` compared truly, written either way round at random: 3/6 > 1/6, or
    1/6 < 3/6."""
    left, right = pair if random.random() < 0.5 else (pair[1], pair[0])
    return Comparison(left, symbol(left, right), right)


def _false_symbol(left: UnreducedFraction, right: UnreducedFraction) -> str:
    """Return a symbol that makes ``left`` compared with ``right`` false: the other of > and <,
    or for equal fractions, one of them at random."""
    match symbol(left, right):
        case "=":
            return random.choice((GREATER_THAN, LESS_THAN))
        case ">":
            return LESS_THAN
        case _:
            return GREATER_THAN


def _styled(numerator: int, denominator: int, like: UnreducedFraction) -> UnreducedFraction:
    """Return numerator over denominator written in ``like``'s style."""
    return UnreducedFraction(numerator, denominator, like.style)


# --- comparisons


def pictured_comparisons(pair: Pair, pictures: Sequence[Picture]) -> tuple[Comparison, ...]:
    """
    Return the wrong options for "Which comparison is true?" about ``pair`` shown by
    ``pictures``, one each, or by wholes the student divides and shades: the symbol the wrong way
    round, "=" (unless the fractions are equal, when both > and < are wrong), and one picture
    misread: an area model or group read by its unshaded parts (3/6 > 5/6 when 1/6 is shaded), a
    number line's jumps counted as if each were a whole (2 jumps and 1, "1/2 > 1/1"), or its
    ticks counted instead of its parts (5/7 for 5/6).
    """
    left, right = pair
    wrong = [Comparison(left, _false_symbol(left, right), right)]
    if left.value != right.value:
        wrong.append(Comparison(left, EQUAL_TO, right))
    else:
        flipped = GREATER_THAN if wrong[0].symbol == LESS_THAN else LESS_THAN
        wrong.append(Comparison(left, flipped, right))
    misread_left, misread_right = _misread(pair, pictures)
    wrong.append(
        Comparison(misread_left, _false_symbol(misread_left, misread_right), misread_right)
    )
    return tuple(wrong)


def _misread(pair: Pair, pictures: Sequence[Picture]) -> Pair:
    """Return ``pair`` as a student might misread its pictures, as ``pictured_comparisons``
    describes, different from ``pair`` itself and with two different values: the unshaded parts
    read when that gives a new fraction, else a ticks misread."""
    left, right = pair
    lines = [each for each in pictures if isinstance(each, FractionLine)]
    if lines and all(line.jumps for line in lines):
        return _styled(1, left.numerator, left), _styled(1, right.numerator, right)
    sides = [0, 1]
    random.shuffle(sides)
    if not lines:
        for side in sides:
            shown, other = pair[side], pair[1 - side]
            unshaded = _styled(shown.denominator - shown.numerator, shown.denominator, shown)
            # a whole has no unshaded parts, a half's are the same fraction, and a fraction read
            # as the other one would be compared with itself
            if unshaded.numerator > 0 and unshaded.value not in (shown.value, other.value):
                return (unshaded, right) if side == 0 else (left, unshaded)
    # counting the ticks lowers a fraction, so it can't make both sides the other's value
    side = next(
        each
        for each in sides
        if Fraction(pair[each].numerator, pair[each].denominator + 1) != pair[1 - each].value
    )
    shown = pair[side]
    ticks = _styled(shown.numerator, shown.denominator + 1, shown)
    return (ticks, right) if side == 0 else (left, ticks)


def bare_comparisons(
    pair: Pair, shared: Sequence[Shared], denominators: Sequence[int]
) -> tuple[Comparison, ...]:
    """
    Return the wrong options for "Which comparison is true?" about ``pair``, written or beside a
    fraction wall, each wrong in its own way: the answer's pair with the symbol the wrong way
    round (2/6 > 2/4); then two of: a larger denominator taken for a larger fraction
    (2/3 < 2/8), the same numerator taken for equal (2/3 = 2/4), the same denominator taken for
    equal (1/8 = 2/8), and a larger numerator taken for a smaller fraction (5/8 < 3/8), using
    only the kinds of pair in ``shared``, from ``denominators``, or from
    ``WRONG_PAIR_DENOMINATORS`` of them drawn at random when there are more. When those run out,
    as with few denominators, any kind of pair fills in, from them and the next denominators up.

    One pair is always shown twice, so a student can't take the answer to be one of the two
    choices that share their fractions: the answer's pair, or ``DOUBLED_PAIR_SHARE`` of the time,
    another pair with two mistakes about it (2/3 = 2/4 and 2/3 > 2/4) in place of the answer's.
    """
    left, right = pair
    used = {frozenset((left, right))}
    pool = sorted(set(denominators))
    if len(pool) > WRONG_PAIR_DENOMINATORS:
        pool = sorted(random.sample(pool, WRONG_PAIR_DENOMINATORS))
    kinds: list[str] = []
    if Shared.NUMERATOR in shared:
        kinds += ["larger_denominator", "same_numerator"]
    if Shared.DENOMINATOR in shared:
        kinds += ["same_denominator", "larger_numerator"]
    random.shuffle(kinds)
    wrong: list[Comparison] = []
    if left.value != right.value and random.random() < DOUBLED_PAIR_SHARE:
        families = [each for each in _MISTAKE_FAMILIES if each[0] in kinds]
        first, second = random.choice(families)
        found = _other_pair(first, pool, used, left)
        if found is not None:
            used.add(frozenset(found))
            wrong += [_mistake(first, found), _mistake(second, found)]
    if not wrong:
        wrong.append(
            Comparison(right, symbol(left, right), left)
            if left.value != right.value
            else Comparison(left, _false_symbol(left, right), right)
        )
    for kind in kinds:
        if len(wrong) == WRONG_OPTIONS:
            break
        found = _other_pair(kind, pool, used, left)
        if found is not None:
            used.add(frozenset(found))
            wrong.append(_mistake(kind, found))
    filler = sorted({*pool, left.denominator + 1, right.denominator + 2})
    for kind in ("same_denominator", "larger_numerator", "larger_denominator", "same_numerator"):
        if len(wrong) == WRONG_OPTIONS:
            break
        found = _other_pair(kind, filler, used, left)
        if found is not None:
            used.add(frozenset(found))
            wrong.append(_mistake(kind, found))
    return tuple(wrong)


def _other_pair(
    kind: str,
    denominators: Sequence[int],
    used: set[frozenset[UnreducedFraction]],
    like: UnreducedFraction,
) -> Pair | None:
    """Return a pair for ``kind`` of mistake from ``denominators``, the smaller first, sharing a
    numerator or a denominator as the mistake needs and not in ``used``, or ``None``."""
    pairs: list[Pair]
    if kind in ("larger_denominator", "same_numerator"):
        pairs = [
            (_styled(top, larger, like), _styled(top, smaller, like))
            for smaller, larger in combinations(sorted(set(denominators)), 2)
            for top in range(1, min(smaller, 12) + 1)
        ]
    else:
        pairs = [
            (_styled(low, parts, like), _styled(high, parts, like))
            for parts in sorted(set(denominators))
            if parts <= 24
            for low, high in combinations(range(1, parts + 1), 2)
        ]
    fresh = [each for each in pairs if frozenset(each) not in used]
    return random.choice(fresh) if fresh else None


def _mistake(kind: str, pair: Pair) -> Comparison:
    """Return ``pair``, the smaller first, compared as ``kind`` of mistake would."""
    smaller, larger = pair
    match kind:
        case "larger_denominator":  # 2/8 > 2/3: the larger denominator taken for the larger
            return Comparison(smaller, GREATER_THAN, larger)
        case "larger_numerator":  # 5/8 < 3/8: written the wrong way round
            return Comparison(larger, LESS_THAN, smaller)
        case _:  # 2/3 = 2/4, 1/8 = 2/8
            return Comparison(smaller, EQUAL_TO, larger)


# --- explanations


def explanation(pair: Pair, pictured: bool) -> Explanation:
    """
    Return the true comparison of ``pair``, either way round, with its reason: for the same
    numerator, which parts are larger, "sixths are larger than eighths"; for the same
    denominator, how many parts, "6 out of 8 parts is less than 8 out of 8 parts".
    """
    comparison = true_comparison(pair)
    return Explanation(comparison, right_reason(comparison))


def right_reason(comparison: Comparison) -> Reason:
    """Return the reason ``comparison``, true or not, would have if its symbol were right."""
    left, right = comparison.left, comparison.right
    if left.numerator == right.numerator:
        return PartSize(*_part_sizes(comparison), larger=True)
    return PartsOf(left, right, comparison.symbol == GREATER_THAN)


def _part_sizes(comparison: Comparison) -> tuple[int, int]:
    """Return the denominators of a comparison of fractions with the same numerator, the one
    its symbol makes the greater fraction first: its parts are the larger."""
    left, right = comparison.left.denominator, comparison.right.denominator
    return (left, right) if comparison.symbol == GREATER_THAN else (right, left)


def explanation_choices(
    answer: Explanation, pictures: Sequence[Picture]
) -> tuple[Explanation, ...]:
    """
    Return the wrong options for "Which comparison and explanation are true?" about ``answer``'s
    fractions, as half of them do: the grid of the true or the wrong-way-round symbol with the
    right reason or a mistaken one (for the same numerator, "eighths are larger than sixths";
    for the same denominator, numerators read as part sizes, "sixths are smaller than eighths",
    which needs numerators of 2 or more). The other half mix mistakes: the wrong way round with
    its reason, "=" because the fractions have the same number of parts shaded or in all, a
    larger denominator taken for a larger fraction ("2/3 < 2/4, because 3 is less than 4"), the
    picture's unshaded parts compared with a true-sounding reason, and the grid's mistaken
    reason.
    """
    comparison = answer.comparison
    left, right = comparison.left, comparison.right
    flipped = Comparison(left, _false_symbol(left, right), right)
    same_numerator = left.numerator == right.numerator
    mistaken = _mistaken_reason(comparison)
    if mistaken is not None and random.random() < 0.5:
        flipped_mistaken = _mistaken_reason(flipped)
        if flipped_mistaken is not None:
            return (
                Explanation(comparison, mistaken),
                Explanation(flipped, right_reason(flipped)),
                Explanation(flipped, flipped_mistaken),
            )
    pool: list[Explanation] = [Explanation(flipped, right_reason(flipped))]
    pictured = bool(pictures) and not any(isinstance(each, FractionLine) for each in pictures)
    if same_numerator:
        pool.append(
            Explanation(
                Comparison(left, EQUAL_TO, right), SameCount(left.numerator, False, pictured)
            )
        )
        larger_den, smaller_den = sorted((left.denominator, right.denominator), reverse=True)
        # the larger denominator taken for the larger fraction, the denominators compared
        larger, smaller = _larger_denominator_first(left, right)
        bigger = Comparison(larger, GREATER_THAN, smaller)
        pool.append(Explanation(bigger, BiggerNumber(larger_den, smaller_den, greater=True)))
    else:
        pool.append(
            Explanation(
                Comparison(left, EQUAL_TO, right), SameCount(left.denominator, True, pictured)
            )
        )
    if pictured:
        unshaded = _unshaded_explanation(comparison)
        if unshaded is not None:
            pool.append(unshaded)
    if mistaken is not None:
        pool.append(Explanation(comparison, mistaken))
    random.shuffle(pool)
    return tuple(pool[:WRONG_OPTIONS])


def _larger_denominator_first(
    left: UnreducedFraction, right: UnreducedFraction
) -> tuple[UnreducedFraction, UnreducedFraction]:
    """Return ``left`` and ``right`` with the larger denominator first."""
    return (left, right) if left.denominator > right.denominator else (right, left)


def _mistaken_reason(comparison: Comparison) -> Reason | None:
    """
    Return the grid's mistaken reason for ``comparison``, to go with its symbol: for the same
    numerator, the other parts called larger, "eighths are larger than sixths"; for the same
    denominator, the numerators read as part sizes, "sixths are smaller than eighths" with <, or
    ``None`` when a numerator is 1, which names no parts.
    """
    left, right = comparison.left, comparison.right
    greater = comparison.symbol == GREATER_THAN
    if left.numerator == right.numerator:
        larger, smaller = _part_sizes(comparison)
        return PartSize(smaller, larger, larger=True)
    if min(left.numerator, right.numerator) < 2:
        return None
    return PartSize(left.numerator, right.numerator, larger=greater)


def _unshaded_explanation(comparison: Comparison) -> Explanation | None:
    """
    Return the pictures read by their unshaded parts, compared with ``comparison``'s symbol, with
    a reason that sounds true: "1/3 > 6/8, because thirds are larger than eighths", or ``None``
    when a picture is all shaded. ``comparison`` is true, of two different fractions, so the
    unshaded parts compare the other way and the misread is false.
    """
    left, right = comparison.left, comparison.right
    if left.numerator == left.denominator or right.numerator == right.denominator:
        return None
    unshaded_left = _styled(left.denominator - left.numerator, left.denominator, left)
    unshaded_right = _styled(right.denominator - right.numerator, right.denominator, right)
    misread = Comparison(unshaded_left, comparison.symbol, unshaded_right)
    if left.numerator == right.numerator:
        return Explanation(misread, right_reason(comparison))
    return Explanation(
        misread, PartsOf(unshaded_left, unshaded_right, comparison.symbol == GREATER_THAN)
    )


# --- word problems


def story_choices(
    form: StoryForm,
    names: tuple[str, str],
    fractions: Pair,
    answer: str,
    winner: str | None,
    same_size: bool,
    greater: bool,
) -> tuple[StoryChoice, tuple[StoryChoice, ...]]:
    """
    Return the right statement and three wrong ones about ``names`` having ``fractions``, written
    in ``form``. ``winner`` is who has the greater fraction, or ``None`` when they're equal;
    ``answer`` is the question's answer, a name, "the same" or "can't tell" (the wholes not
    ``same_size``). ``greater`` says whether the who-and-symbol form asks who has more.

    Statements with reasons: the right one with its true reason, the other person with a larger
    denominator taken for a larger fraction or the fractions the wrong way round, "the same"
    because it's the same kind of whole, because both numerators are the same, or because the
    fractions are equal, and "not enough information". Who and symbol: each person with each
    symbol. Plain statements: each person ahead, the same, and "not enough information".
    """
    first, second = names
    loser = None if winner is None else (second if winner == first else first)
    same_numerator = fractions[0].numerator == fractions[1].numerator
    of = dict(zip(names, fractions, strict=True))
    if form is StoryForm.WHO_SYMBOL:
        options = [
            StoryChoice(
                Verdict.AHEAD,
                name,
                StoryReason.FRACTION,
                Comparison(fractions[0], mark, fractions[1]),
                brief=True,
            )
            for name in names
            for mark in (GREATER_THAN, LESS_THAN)
        ]
        wanted = winner if greater else loser
        right = next(
            each
            for each in options
            if each.who == wanted and each.claim is not None and is_true(each.claim)
        )
        return right, tuple(each for each in options if each != right)
    cant_tell = StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE)
    if form is StoryForm.PLAIN:
        plain = [StoryChoice(Verdict.AHEAD, name, StoryReason.NONE) for name in names]
        plain += [StoryChoice(Verdict.SAME, None, StoryReason.NONE), cant_tell]
        right = next(each for each in plain if _plain_right(each, answer, winner))
        return right, tuple(each for each in plain if each != right)
    if winner is not None and same_size:
        reason = (
            StoryReason.PART_SIZE
            if same_numerator and random.random() < 0.5
            else StoryReason.FRACTION
        )
        right = StoryChoice(
            Verdict.AHEAD, winner, reason, Comparison(of[winner], GREATER_THAN, of[loser or first])
        )
    elif winner is None:
        right = StoryChoice(
            Verdict.SAME, None, StoryReason.EQUAL, Comparison(fractions[0], EQUAL_TO, fractions[1])
        )
    else:
        right = cant_tell
    pool: list[StoryChoice] = []
    if winner is not None and loser is not None:
        backwards = Comparison(of[loser], GREATER_THAN, of[winner])
        if same_numerator:
            pool.append(StoryChoice(Verdict.AHEAD, loser, StoryReason.DENOMINATOR, backwards))
        else:
            pool.append(StoryChoice(Verdict.AHEAD, loser, StoryReason.FRACTION, backwards))
        same_reason = StoryReason.SAME_NUMERATOR if same_numerator else StoryReason.SAME_WHOLE
        pool.append(StoryChoice(Verdict.SAME, None, same_reason))
        pool.append(
            StoryChoice(
                Verdict.SAME,
                None,
                StoryReason.EQUAL,
                Comparison(fractions[0], EQUAL_TO, fractions[1]),
            )
        )
        if right is cant_tell:
            # the greater fraction taken for more, though the wholes are different sizes
            pool.append(
                StoryChoice(
                    Verdict.AHEAD,
                    winner,
                    StoryReason.FRACTION,
                    Comparison(of[winner], GREATER_THAN, of[loser]),
                )
            )
        else:
            pool.append(cant_tell)
    else:
        for name in names:
            pool.append(StoryChoice(Verdict.AHEAD, name, StoryReason.NONE))
        pool.append(cant_tell)
    pool = [each for each in pool if each != right]
    first_pick = pool[:1]
    rest = pool[1:]
    random.shuffle(rest)
    return right, tuple((first_pick + rest)[:WRONG_OPTIONS])


def _plain_right(choice: StoryChoice, answer: str, winner: str | None) -> bool:
    """Return whether a plain statement is the right one, for ``answer``."""
    match choice.verdict:
        case Verdict.AHEAD:
            return answer not in (SAME, CANT_TELL) and choice.who == winner
        case Verdict.SAME:
            return answer == SAME
        case _:
            return answer == CANT_TELL


# --- ways of shading less or greater than a model


def less_greater_ways(
    fraction: UnreducedFraction,
    greater: bool,
    shared: Sequence[Shared],
) -> tuple[list[UnreducedFraction], list[UnreducedFraction]]:
    """
    Return the ways of dividing and shading a whole, each as (shaded parts, parts) written as a
    fraction, that show a fraction less than ``fraction``, or greater with ``greater``, and those
    that don't, sharing its numerator or denominator as ``shared`` allows: the same parts with
    fewer or more shaded, or the same number shaded of more or fewer parts, from 2 parts up to
    ``LESS_GREATER_PARTS``, or up to ``fraction``'s own parts when it has more.

    Those that don't: the same number shaded of fewer parts for "less" (4 of 4 for 4/6), more
    shaded of the same parts (5 of 6), and the same fraction (4 of 6); for "greater" the reverse.
    """
    count, parts = fraction.numerator, fraction.denominator
    most = max(LESS_GREATER_PARTS, parts)
    other_parts = [each for each in range(2, most + 1) if each != parts]
    ways: list[UnreducedFraction] = []
    nots: list[UnreducedFraction] = [_styled(count, parts, fraction)]
    if Shared.DENOMINATOR in shared:
        for shaded in range(1, parts + 1):
            if shaded == count:
                continue
            way = _styled(shaded, parts, fraction)
            (ways if (way.value > fraction.value) == greater else nots).append(way)
    if Shared.NUMERATOR in shared:
        for other in other_parts:
            if other < count:
                continue
            way = _styled(count, other, fraction)
            (ways if (way.value > fraction.value) == greater else nots).append(way)
    return ways, nots


def less_greater_choices(
    fraction: UnreducedFraction,
    ways: Sequence[UnreducedFraction],
    nots: Sequence[UnreducedFraction],
    greater: bool,
) -> tuple[UnreducedFraction, tuple[UnreducedFraction, ...]]:
    """
    Return the way that isn't one, the right answer to "Which is NOT a way to show a fraction
    less than 4/6?", and three ways that are, the wrong answers.

    Picking the picture with the most parts shaded (for "greater", the fewest) would find the
    answer without comparing whenever it alone has that many, as 5 of 6 does beside ways of 2 of
    6, 3 of 6 and 4 of 8. So ``1 - STANDOUT_SHARE`` of the time, when it can be, the answer has
    a way beside it with as many shaded parts or more (fewer): 4 of 5 beside 4 of 8. The answer
    is then never ``fraction`` itself, whose picture is the model's twin, so that picking the twin
    doesn't find the answer often either. The rest of the time all four are drawn at random.
    """

    def matched(way: UnreducedFraction, answer: UnreducedFraction) -> bool:
        """Whether ``way`` has as many shaded parts as ``answer`` or more (for "greater",
        as few or fewer)."""
        if greater:
            return way.numerator <= answer.numerator
        return way.numerator >= answer.numerator

    hidden = [
        each
        for each in nots
        if each.value != fraction.value and any(matched(way, each) for way in ways)
    ]
    if not hidden or random.random() < STANDOUT_SHARE:
        return random.choice(list(nots)), tuple(random.sample(list(ways), WRONG_OPTIONS))
    answer = random.choice(hidden)
    beside = random.choice([way for way in ways if matched(way, answer)])
    rest = random.sample([way for way in ways if way != beside], WRONG_OPTIONS - 1)
    return answer, (beside, *rest)


def less_greater_shows_choices(
    fraction: UnreducedFraction,
    ways: Sequence[UnreducedFraction],
    nots: Sequence[UnreducedFraction],
    greater: bool,
) -> tuple[UnreducedFraction, tuple[UnreducedFraction, ...]]:
    """
    Return a way, the right answer to "Which model shows a fraction less than 4/6?", and three
    that aren't, the wrong answers.

    Picking the picture with the fewest parts shaded (for "greater", the most) would find the
    answer without comparing whenever it alone has that few, as 2 of 6 does beside 4 of 4, 5 of
    6 and 4 of 6. So ``1 - STANDOUT_SHARE`` of the time, when it can be, the answer has one that
    isn't beside it with as few shaded parts or fewer (more): 4 of 8 beside 4 of 5, which isn't
    the model's twin when another can be. The rest of the time all four are drawn at random.
    """

    def matched(way: UnreducedFraction, other: UnreducedFraction) -> bool:
        """Whether ``other`` has as few shaded parts as ``way`` or fewer (for "greater", as
        many or more)."""
        if greater:
            return other.numerator >= way.numerator
        return other.numerator <= way.numerator

    hidden = [each for each in ways if any(matched(each, other) for other in nots)]
    if not hidden or random.random() < STANDOUT_SHARE:
        return random.choice(list(ways)), tuple(random.sample(list(nots), WRONG_OPTIONS))
    answer = random.choice(hidden)
    beside_ones = [other for other in nots if matched(answer, other)]
    beside = random.choice(
        [other for other in beside_ones if other.value != fraction.value] or beside_ones
    )
    rest = random.sample([other for other in nots if other != beside], WRONG_OPTIONS - 1)
    return answer, (beside, *rest)


# --- "5/6 > 5/8. Which explains why?"


def reason_choices(answer: Explanation, pictured: bool) -> tuple[Reason, ...]:
    """
    Return the wrong reasons for ``answer``'s true comparison, ``pictured`` with models or not:
    for the same numerator, the other parts called larger ("eighths are larger than sixths"),
    the same number of parts shaded, and the larger denominator taken for the larger fraction
    ("8 is greater than 6"); for the same denominator, the numerators read as part sizes
    ("sixths are smaller than eighths", which needs numerators of 2 or more), the same number of
    equal parts, and the parts counted the wrong way round.
    """
    comparison = answer.comparison
    left, right = comparison.left, comparison.right
    if left.numerator == right.numerator:
        larger, smaller = _part_sizes(comparison)
        return (
            PartSize(smaller, larger, larger=True),
            SameCount(left.numerator, total=False, pictured=pictured),
            BiggerNumber(smaller, larger, greater=True),
        )
    greater = comparison.symbol == GREATER_THAN
    return (
        PartSize(left.numerator, right.numerator, larger=greater),
        SameCount(left.denominator, total=True, pictured=pictured),
        PartsOf(left, right, greater=not greater),
    )


# --- "Which fraction is greater?" after drawing two


def pick_choices(pair: Pair, greater: bool) -> tuple[Pick, tuple[Pick, ...]]:
    """Return the right choice for which of ``pair``, two different fractions, is greater (or
    less), and the three wrong ones: each fraction picked because ``pair`` compares one way or
    the other, "2/3, because 2/3 > 2/4"."""
    options = [
        Pick(fraction, Comparison(pair[0], mark, pair[1]))
        for fraction in pair
        for mark in (GREATER_THAN, LESS_THAN)
    ]
    pick = max if greater else min
    wanted = pick(pair, key=lambda each: each.value)
    right = next(each for each in options if each.fraction == wanted and is_true(each.claim))
    return right, tuple(each for each in options if each != right)
