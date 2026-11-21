"""Tests for a whole number's factors and factor pairs, and whether it is prime or composite."""

import pytest

from core.prime_composite.factors import Primality, factor_pairs, factors, primality

PRIME, COMPOSITE, NEITHER = Primality


@pytest.mark.parametrize(
    ("number", "expected_factors", "expected_pairs", "expected_primality"),
    [
        # 1 has one factor, which pairs with itself
        (1, (1,), ((1, 1),), NEITHER),
        (2, (1, 2), ((1, 2),), PRIME),
        # a square's root pairs with itself, and is listed once
        (4, (1, 2, 4), ((1, 4), (2, 2)), COMPOSITE),
        (9, (1, 3, 9), ((1, 9), (3, 3)), COMPOSITE),
        (37, (1, 37), ((1, 37),), PRIME),
        # odd composites that look prime
        (51, (1, 3, 17, 51), ((1, 51), (3, 17)), COMPOSITE),
        (91, (1, 7, 13, 91), ((1, 91), (7, 13)), COMPOSITE),
        # STAAR's numbers whose factor pairs are asked for
        (
            132,
            (1, 2, 3, 4, 6, 11, 12, 22, 33, 44, 66, 132),
            ((1, 132), (2, 66), (3, 44), (4, 33), (6, 22), (11, 12)),
            COMPOSITE,
        ),
        (
            184,
            (1, 2, 4, 8, 23, 46, 92, 184),
            ((1, 184), (2, 92), (4, 46), (8, 23)),
            COMPOSITE,
        ),
    ],
)
def test_factors(
    number: int,
    expected_factors: tuple[int, ...],
    expected_pairs: tuple[tuple[int, int], ...],
    expected_primality: Primality,
) -> None:
    assert (factors(number), factor_pairs(number), primality(number)) == (
        expected_factors,
        expected_pairs,
        expected_primality,
    )
