"""
The fractions a self-check tiles sheet's comparing questions are about, in groups.

Each group's fractions share a numerator or a denominator, and each answers one of the group's
questions while the others offer it, so that every fraction a question offers is in the bank as
another question's answer, and no tile can be matched to its question without comparing. Pairs
and threes come with Compare ticked; with Greatest and least alone, groups of four or more.

Groups are built directly, one at a time, each kept only if the fractions left can still fill
the rest of the sheet, so a sheet is never drawn again for failing to fit.
"""

import random
from collections.abc import Iterator, Sequence, Set
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, islice

from core.comparing_fractions.data import Representation, Shared
from core.comparing_fractions.pictures import can_show, largest_showable
from core.written_numbers import UnreducedFraction

SAMPLED_DENOMINATORS = 12  # the most denominators a tiles sheet draws its fractions from
LISTED_TOPS = 23  # past a denominator of 24, the numerators listed over it, besides the whole
PAIRS_AND_THREES = 2  # the fewest fractions in a group with Compare ticked
GREATEST_GROUP = (4, 7)  # the fewest and most fractions in a group of Greatest and least alone
# Of a kind of group that doesn't decide whether a sheet fits, the sets of fractions tried from
# each group of fractions that share a number, at most
OTHER_KIND_TRIES = 20

type Group = tuple[UnreducedFraction, ...]


@dataclass(frozen=True)
class Pool:
    """
    The fractions a tiles sheet's groups come from, as two lists of fractions that share a
    number: ``by_denominator``, one for each denominator, and ``by_numerator``, one for each
    numerator, each with the fractions a ticked representation can show together. A list is
    empty when its kind of sharing isn't ``shared``.
    """

    shared: tuple[Shared, ...]
    by_denominator: tuple[Group, ...]
    by_numerator: tuple[Group, ...]

    def partition(self) -> tuple[Group, ...]:
        """Return the lists whose fractions don't overlap that decide whether a sheet fits: by
        denominator when that's shared, else by numerator."""
        return self.by_denominator if Shared.DENOMINATOR in self.shared else self.by_numerator

    def of(self, kind: Shared) -> tuple[Group, ...]:
        """Return the lists of fractions sharing ``kind`` of number."""
        return self.by_denominator if kind is Shared.DENOMINATOR else self.by_numerator


def tops(parts: int) -> list[int]:
    """Return the numerators a tiles sheet lists over ``parts``: every one up to the whole, or
    past 24 parts, 1 to ``LISTED_TOPS`` and the whole."""
    if parts <= LISTED_TOPS + 1:
        return list(range(1, parts + 1))
    return [*range(1, LISTED_TOPS + 1), parts]


def make_pool(
    reps: Sequence[Representation],
    shared: Sequence[Shared],
    denominators: Sequence[int],
    sample: bool,
) -> Pool:
    """
    Return the fractions a tiles sheet's groups can come from, over the ``denominators`` some
    of ``reps`` can show, at most ``SAMPLED_DENOMINATORS`` of them: drawn at random with
    ``sample``, else the smallest, so that the possible counts are the same every time. A
    fraction over a denominator past that many is still in the sheet's other questions.
    """
    usable = [
        parts
        for parts in denominators
        if Representation.NONE in reps or any(largest_showable(rep, [parts]) for rep in reps)
    ]
    if len(usable) > SAMPLED_DENOMINATORS:
        if sample:
            usable = sorted(random.sample(usable, SAMPLED_DENOMINATORS))
        else:
            usable = usable[:SAMPLED_DENOMINATORS]
    by_denominator: tuple[Group, ...] = ()
    if Shared.DENOMINATOR in shared:
        by_denominator = tuple(
            tuple(UnreducedFraction(top, parts) for top in tops(parts))
            for parts in usable
            if any(can_show(rep, [parts]) for rep in reps)
        )
    by_numerator: tuple[Group, ...] = ()
    if Shared.NUMERATOR in shared:
        numerators = sorted({top for parts in usable for top in tops(parts)})
        groups = []
        for top in numerators:
            over = [parts for parts in usable if top in tops(parts)]
            shown = (
                over
                if Representation.NONE in reps
                else max((largest_showable(rep, over) for rep in reps), key=len)
            )
            groups.append(
                tuple(sorted((UnreducedFraction(top, parts) for parts in shown), key=_value))
            )
        by_numerator = tuple(groups)
    return Pool(tuple(shared), by_denominator, by_numerator)


def _value(fraction: UnreducedFraction) -> Fraction:
    """Return a fraction's value, to sort by."""
    return fraction.value


def capacity(pool: Pool, fewest: int) -> int:
    """Return the most fractions groups of at least ``fewest`` can take from ``pool``."""
    return sum(size for size in _sizes(pool, None) if size >= fewest)


def fills(
    pool: Pool, total: int, fewest: int, unused: Set[UnreducedFraction] | None = None
) -> bool:
    """
    Return whether groups of at least ``fewest`` fractions can take exactly ``total`` of
    ``pool``'s fractions, or of those ``unused``: each list in its partition gives any number
    from ``fewest`` up to all its fractions, or none. With pairs and threes, any number from 2
    up is pairs and threes; with groups of four to seven, any number from 4 up.
    """
    sums = {0}
    for size in _sizes(pool, unused):
        if size >= fewest:
            sums |= {
                each + taken
                for each in sums
                for taken in range(fewest, size + 1)
                if each + taken <= total
            }
    return total in sums


def _sizes(pool: Pool, unused: Set[UnreducedFraction] | None) -> list[int]:
    """Return how many fractions are left in each list of ``pool``'s partition."""
    return [
        sum(1 for each in group if unused is None or each in unused) for group in pool.partition()
    ]


def plan_groups(pool: Pool, total: int, fewest: int, want_three: bool) -> list[Group]:
    """
    Return groups of fractions from ``pool``, each sorted from the least, taking ``total`` in
    all: pairs and threes with ``fewest`` 2, else groups of four to seven. Each group shares a
    numerator or a denominator, with even chance when both are shared; with ``want_three``,
    the first group that can be a three is one.

    Each group is kept only if the fractions left can still fill the rest, which the partition's
    own kind of group always can when ``fills`` allows ``total``, so the sheet is complete.

    Raises ``ValueError`` if ``fills`` doesn't allow ``total``.
    """
    if not fills(pool, total, fewest):
        raise ValueError(f"No groups of at least {fewest} fractions make {total}.")
    unused = {each for group in (*pool.by_denominator, *pool.by_numerator) for each in group}
    groups: list[Group] = []
    left = total
    while left:  # each group takes at least two, so this ends
        prefer_three = want_three and not any(len(group) == 3 for group in groups)
        sizes = _group_sizes(left, fewest, prefer_three)
        kinds = random.sample(pool.shared, len(pool.shared))
        found = next(
            group
            for kind in kinds
            for group in _candidates(pool, kind, unused, sizes)
            if fills(pool, left - len(group), fewest, unused - set(group))
        )
        groups.append(found)
        unused -= set(found)
        left -= len(found)
    return groups


def _group_sizes(left: int, fewest: int, prefer_three: bool) -> list[int]:
    """Return the sizes the next group can have with ``left`` fractions still to take, so that
    what remains can still be groups: in a random order, or a three first."""
    if fewest == PAIRS_AND_THREES:
        if left in (2, 3):
            return [left]
        if left == 4:
            return [2]
        return [3, 2] if prefer_three else random.sample([2, 3], 2)
    least, most = GREATEST_GROUP
    sizes = [
        size
        for size in range(least, min(most, left) + 1)
        if left - size == 0 or left - size >= least
    ]
    return random.sample(sizes, len(sizes))


def _candidates(
    pool: Pool, kind: Shared, unused: Set[UnreducedFraction], sizes: Sequence[int]
) -> Iterator[Group]:
    """
    Yield groups of ``sizes`` from ``pool``'s lists sharing ``kind``, from fractions ``unused``,
    the lists in a random order: one set from each list of the partition's own kind, where any
    set of a size is as good as another, else up to ``OTHER_KIND_TRIES`` sets of each size.
    """
    own_kind = pool.of(kind) is pool.partition()
    lists = list(pool.of(kind))
    for group in random.sample(lists, len(lists)):
        members = [each for each in group if each in unused]
        random.shuffle(members)
        for size in sizes:
            if len(members) < size:
                continue
            if own_kind:
                yield tuple(sorted(members[:size], key=_value))
            else:
                for chosen in islice(combinations(members, size), OTHER_KIND_TRIES):
                    yield tuple(sorted(chosen, key=_value))
