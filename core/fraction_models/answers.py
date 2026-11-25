"""
Choosing a fraction sheet's answers: drawing one from those a question can have, keeping a
self-check tiles sheet's answers distinct when some of them are pictures, and wrong fractions for
multiple choice built from the answer's own numbers.
"""

import random
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence, Set
from fractions import Fraction
from itertools import combinations

from core.written_numbers import UnreducedFraction

WRONG_OPTIONS = 3  # beside the correct option, in a multiple-choice question


def pick_answer(answers: Sequence[UnreducedFraction], whole_share: float) -> UnreducedFraction:
    """
    Return one of ``answers``, its denominator drawn first, each with even chance, then a
    numerator. A whole, such as 4/4, is drawn only ``whole_share`` of the time while there are
    others, so that a picture all shaded doesn't come up as often as one half shaded.
    """
    by_denominator: dict[int, list[UnreducedFraction]] = defaultdict(list)
    for answer in answers:
        by_denominator[answer.denominator].append(answer)
    drawn = by_denominator[random.choice(sorted(by_denominator))]
    wholes = [answer for answer in drawn if answer.numerator == answer.denominator]
    parts = [answer for answer in drawn if answer.numerator != answer.denominator]
    if wholes and parts:
        return random.choice(wholes if random.random() < whole_share else parts)
    return random.choice(drawn)


# --- distinct answers for a self-check tiles sheet


def answer_capacity[Kind](
    kinds: Sequence[Kind],
    answers: Mapping[Kind, Collection[UnreducedFraction]],
    pictured: Set[Kind],
) -> int:
    """
    Return the most questions of ``kinds`` a tiles sheet can have with distinct answers, each
    kind able to have ``answers[kind]``: the different answers they can have, as written, where
    a kind among ``pictured``, whose answer the bank shows as a picture, counts once for each
    value, in place of the written answers with that value.
    """
    return _capacity(
        _written_by_value(kinds, answers, pictured), _picture_values(kinds, answers, pictured)
    )


def pick_distinct_answers[Kind](
    slots: Sequence[Kind],
    kinds: Sequence[Kind],
    answers: Mapping[Kind, Collection[UnreducedFraction]],
    pictured: Set[Kind],
    whole_share: float,
) -> list[tuple[Kind, UnreducedFraction]]:
    """
    Return a distinct answer for each of ``slots``, each the kind of question it's for, trying
    the slot's own kind first, then the others in ``kinds`` order, so that a kind that has run out
    of answers gives its place to the next kind that hasn't. Each kind can have
    ``answers[kind]``, drawn as ``pick_answer`` draws them, with ``whole_share``.

    Written answers are distinct as written, so 2/8 and 1/4 can both be answers. A kind among
    ``pictured`` has its answer shown in the bank as a picture, whose value no other answer may
    have: a picture of 3/4 can't sit in a bank beside 6/8. Every written answer lowers the
    sheet's capacity (see ``_capacity``) by one, but a picture's value lowers it by all the
    written answers with that value, so a picture takes a value only while enough capacity is
    left for the slots after it. That keeps a slot always fillable, so the sheet is complete
    whenever ``answer_capacity`` allows its length.

    Raises ``ValueError`` if there are more slots than ``answer_capacity`` allows.
    """
    written = _written_by_value(kinds, answers, pictured)
    pictures = _picture_values(kinds, answers, pictured)
    if len(slots) > _capacity(written, pictures):
        raise ValueError(
            f"At most {_capacity(written, pictures)} different answers, not {len(slots)}."
        )
    used: set[UnreducedFraction] = set()
    taken: set[Fraction] = set()
    picked: list[tuple[Kind, UnreducedFraction]] = []
    for slot, own in enumerate(slots):
        left_after = len(slots) - slot - 1
        start = kinds.index(own)
        for kind in (*kinds[start:], *kinds[:start]):
            if kind in pictured:
                capacity = _capacity(written, pictures, used, taken)
                values_used = {answer.value for answer in used}
                own_values = {answer.value for answer in answers[kind]}
                fitting = sorted(
                    value
                    for value in own_values - taken - values_used
                    if capacity - max(len(written.get(value, ())), 1) >= left_after
                )
                if fitting:
                    value = random.choice(fitting)
                    taken.add(value)
                    forms = [answer for answer in answers[kind] if answer.value == value]
                    picked.append((kind, random.choice(forms)))
                    break
            else:
                fitting_answers = [
                    answer
                    for answer in answers[kind]
                    if answer not in used and answer.value not in taken
                ]
                if fitting_answers:
                    answer = pick_answer(fitting_answers, whole_share)
                    used.add(answer)
                    picked.append((kind, answer))
                    break
    return picked


def _written_by_value[Kind](
    kinds: Sequence[Kind],
    answers: Mapping[Kind, Collection[UnreducedFraction]],
    pictured: Set[Kind],
) -> dict[Fraction, set[UnreducedFraction]]:
    """Return the written answers of ``kinds``, grouped by their values."""
    found: dict[Fraction, set[UnreducedFraction]] = defaultdict(set)
    for kind in set(kinds) - pictured:
        for answer in answers[kind]:
            found[answer.value].add(answer)
    return found


def _picture_values[Kind](
    kinds: Sequence[Kind],
    answers: Mapping[Kind, Collection[UnreducedFraction]],
    pictured: Set[Kind],
) -> set[Fraction]:
    """Return the values a picture answer can have among ``kinds``."""
    return {answer.value for kind in set(kinds) & pictured for answer in answers[kind]}


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


# --- wrong fractions for multiple choice


def wrong_fractions(
    answer: UnreducedFraction,
    first: Sequence[tuple[int, int]],
    rest: Sequence[tuple[int, int]],
    on_top_share: float,
) -> tuple[UnreducedFraction, ...]:
    """
    Return ``WRONG_OPTIONS`` wrong fractions in ``answer``'s style, each (numerator, denominator):
    those of ``first`` that are wrong, then a random choice of ``rest``'s, each value different
    from the answer's and from the others'. If those run short, fractions over the answer's
    denominator fill in.

    A wrong answer is often built from the answer's own numbers, which can make the answer the
    one choice built from the numbers the choices repeat most, a guess that needs no maths. So
    when the ways to choose from ``rest`` can put the answer alone at the top that way or not,
    it's put there ``on_top_share`` of the time, a share measured for each kind of question so
    that the guess is right about as often as any guess. A whole, such as 4/4, has its
    denominator twice, so it's always at the top.
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
    if on_top and (not others_top or random.random() < on_top_share):
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
