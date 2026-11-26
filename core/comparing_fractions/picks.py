"""
Choosing what a comparing fractions question compares: two to four fractions sharing a numerator
or a denominator, and a representation that can show them all.

Every choice is made directly from the candidates that fit, so a question is never drawn again
for failing to fit.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

from core.comparing_fractions.data import Representation, Shared
from core.comparing_fractions.pictures import can_show
from core.fraction_models.area_models import WALL_LIMITS
from core.written_numbers import FractionStyle, UnreducedFraction

# Denominators past this aren't listed with every set of fractions they can make: a sheet's
# sets are drawn from them directly instead, where repeats are rare anyway
LISTED_MOST = 12


@dataclass(frozen=True)
class Need:
    """
    What a question's fractions must be: ``size`` of them, all different; with ``equal``, two
    that are the same, a fraction compared with itself, short of a whole; with ``least_top``,
    numerators of at least that when they share a denominator, as a reason that reads
    numerators as part sizes needs (no parts are called "ones").
    """

    size: int = 2
    equal: bool = False
    least_top: int = 1


def showing(rep: Representation, denominators: Sequence[int]) -> list[int]:
    """Return the denominators of ``denominators`` that ``rep`` can show alone; a wall shows
    any it has a row for."""
    if rep is Representation.WALL:
        return [each for each in denominators if each <= WALL_LIMITS.alone]
    return [each for each in denominators if can_show(rep, [each])]


def can_pick(rep: Representation, shared: Shared, denominators: Sequence[int], need: Need) -> bool:
    """Return whether ``pick`` can find fractions for ``need`` sharing ``shared`` that ``rep``
    shows."""
    return bool(_options(rep, shared, denominators, need))


def pick(
    rep: Representation,
    shared: Shared,
    denominators: Sequence[int],
    need: Need,
    style: FractionStyle,
    used: set[frozenset[UnreducedFraction]],
) -> tuple[UnreducedFraction, ...]:
    """
    Return fractions for ``need``, in a random order, written in ``style``, sharing ``shared``,
    that ``rep`` shows, from ``denominators``: a set not in ``used`` while there are others,
    which is then added to it. ``can_pick`` must allow it.
    """
    options = _options(rep, shared, denominators, need)
    if not options:
        raise ValueError(f"No fractions fit {need} for {rep} sharing a {shared}.")
    keys = sorted(options)
    key = random.choice(keys)
    found = _sets(key, options[key], need)
    fresh = [each for each in found if frozenset(each) not in used] or found
    chosen = list(random.choice(fresh))
    used.add(frozenset(chosen))
    random.shuffle(chosen)
    return tuple(UnreducedFraction(each.numerator, each.denominator, style) for each in chosen)


# A way of choosing a set: a denominator shared, (denominator,), or the denominators of a set
# sharing a numerator
type _Key = tuple[int, ...]


def _options(
    rep: Representation, shared: Shared, denominators: Sequence[int], need: Need
) -> dict[_Key, Shared]:
    """Return the keys a set can be chosen by: each denominator that has enough numerators, or
    each set of denominators that ``rep`` shows together, for a shared numerator."""
    shown = showing(rep, denominators)
    if not shown:
        return {}
    if shared is Shared.DENOMINATOR or need.equal:
        if rep is Representation.WALL:  # a wall shows only different denominators
            return {}
        size = 1 if need.equal else need.size
        return {
            (parts,): Shared.DENOMINATOR
            for parts in shown
            if parts - need.least_top + 1 >= size and (not need.equal or parts >= 2)
        }
    if len(shown) < need.size:
        return {}
    if rep in (Representation.OTHER_SHAPE, Representation.WALL) or max(shown) <= LISTED_MOST:
        return {
            group: Shared.NUMERATOR
            for group in combinations(shown, need.size)
            if can_show(rep, group)
        }
    # too many to list: any of them shows with any other, so the key is drawn when picked
    return {tuple(shown): Shared.NUMERATOR}


def _sets(key: _Key, shared: Shared, need: Need) -> list[tuple[UnreducedFraction, ...]]:
    """Return the sets ``key`` gives, or for a long key, a few drawn at random."""
    if need.equal:
        parts = key[0]
        return [
            (UnreducedFraction(top, parts), UnreducedFraction(top, parts))
            for top in range(1, parts)
        ]
    if shared is Shared.DENOMINATOR:
        parts = key[0]
        tops = range(need.least_top, parts + 1)
        if parts <= LISTED_MOST:
            return [
                tuple(UnreducedFraction(top, parts) for top in group)
                for group in combinations(tops, need.size)
            ]
        return [tuple(UnreducedFraction(top, parts) for top in random.sample(tops, need.size))]
    if len(key) > need.size:  # every denominator shown: draw the set
        key = tuple(sorted(random.sample(key, need.size)))
    return [tuple(UnreducedFraction(top, parts) for parts in key) for top in range(1, min(key) + 1)]
