"""A whole number's factors and factor pairs, and whether it is prime, composite or neither."""

from enum import StrEnum
from math import isqrt


class Primality(StrEnum):
    """
    Whether a whole number is prime, composite or neither, as 0 and 1 are. Values are stable
    identifiers for the API and storage.
    """

    PRIME = "prime"  # exactly two factors: 1 and itself
    COMPOSITE = "composite"  # more than two factors
    NEITHER = "neither"  # fewer than two factors: 1 has one


# A factor pair, smaller factor first: (4, 46) for 184
type FactorPair = tuple[int, int]


def factors(number: int) -> tuple[int, ...]:
    """Return the factors of a whole number from 1 up, in ascending order: (1, 3, 17, 51)."""
    pairs = factor_pairs(number)
    small = [pair[0] for pair in pairs]
    large = [pair[1] for pair in reversed(pairs) if pair[1] != pair[0]]
    return (*small, *large)


def factor_pairs(number: int) -> tuple[FactorPair, ...]:
    """
    Return the factor pairs of a whole number from 1 up, each smaller factor first, in ascending
    order of it: ((1, 184), (2, 92), (4, 46), (8, 23)). A square's root pairs with itself.
    """
    return tuple(
        (small, number // small) for small in range(1, isqrt(number) + 1) if number % small == 0
    )


def primality(number: int) -> Primality:
    """Return whether a whole number from 1 up is prime, composite or neither."""
    count = len(factors(number))
    if count == 2:
        return Primality.PRIME
    return Primality.COMPOSITE if count > 2 else Primality.NEITHER


def is_prime(number: int) -> bool:
    """Return whether a whole number from 1 up is prime."""
    return primality(number) is Primality.PRIME


def is_composite(number: int) -> bool:
    """Return whether a whole number from 1 up is composite."""
    return primality(number) is Primality.COMPOSITE
