"""
The reason bank for "Who is correct?" questions: what a student might say to show that a number
is prime, composite or neither, rightly or wrongly.

A reason's ``text`` takes these slots:
- ``{n}``: the number it is about;
- ``{a}`` and ``{b}``: a factor pair of the number other than 1 and itself.

Some texts appear twice, about different numbers: "{n} is prime because it is odd" is the wrong
answer for 51, and the right answer for a wrong reason for 37. A new reason is one more entry in
``REASONS``.
"""

from collections.abc import Callable
from dataclasses import dataclass

from core.prime_composite.factors import Primality, is_composite, is_prime


@dataclass(frozen=True)
class Reason:
    """
    A student's claim that a number is prime, composite or neither, with a reason, about any
    number that ``about`` accepts. ``says`` is what the claim says the number is.

    ``sound`` is whether the claim is correct: its answer is right and its reason proves it. A
    claim with the right answer and a reason that doesn't prove it has a ``flaw``, saying why
    not with a counterexample.
    """

    text: str  # "{n} is prime because it is odd"
    says: Primality
    about: Callable[[int], bool]
    sound: bool
    flaw: str = ""  # "Being odd doesn't make a number prime: 9 is odd and composite."


def _odd_composite(number: int) -> bool:
    return number % 2 == 1 and is_composite(number)


def _odd_prime(number: int) -> bool:
    return number % 2 == 1 and is_prime(number)


REASONS = (
    # correct
    Reason("{n} is prime because its only factors are 1 and {n}", Primality.PRIME, is_prime, True),
    Reason("{n} is prime because it has only two factors", Primality.PRIME, is_prime, True),
    Reason(
        "{n} is composite because {a} \N{MULTIPLICATION SIGN} {b} = {n}",
        Primality.COMPOSITE,
        is_composite,
        True,
    ),
    Reason(
        "{n} is composite because it has more than two factors",
        Primality.COMPOSITE,
        is_composite,
        True,
    ),
    Reason(
        "{n} is composite because it is even and greater than 2",
        Primality.COMPOSITE,
        lambda number: number % 2 == 0 and number > 2,
        True,
    ),
    Reason(
        "1 is neither prime nor composite because it has only one factor",
        Primality.NEITHER,
        lambda number: number == 1,
        True,
    ),
    # the wrong answer
    Reason("{n} is prime because it is odd", Primality.PRIME, _odd_composite, False),
    Reason("{n} is prime because it has only two factors", Primality.PRIME, is_composite, False),
    Reason(
        "{n} is prime because neither 2 nor 5 is a factor of {n}",
        Primality.PRIME,
        lambda number: _odd_composite(number) and number % 5 != 0,
        False,
    ),
    Reason(
        "2 is composite because all even numbers are composite",
        Primality.COMPOSITE,
        lambda number: number == 2,
        False,
    ),
    Reason(
        "{n} is composite because it has the factors 1 and {n}",
        Primality.COMPOSITE,
        is_prime,
        False,
    ),
    Reason(
        "1 is prime because it has only one factor",
        Primality.PRIME,
        lambda number: number == 1,
        False,
    ),
    Reason(
        "1 is composite because it is a factor of every number",
        Primality.COMPOSITE,
        lambda number: number == 1,
        False,
    ),
    # the right answer for a wrong reason
    Reason(
        "{n} is composite because it is odd",
        Primality.COMPOSITE,
        _odd_composite,
        False,
        "Being odd doesn't make a number composite: 7 is odd and prime.",
    ),
    Reason(
        "{n} is prime because it is odd",
        Primality.PRIME,
        _odd_prime,
        False,
        "Being odd doesn't make a number prime: 9 is odd and composite.",
    ),
    Reason(
        "{n} is prime because neither 2 nor 5 is a factor of {n}",
        Primality.PRIME,
        lambda number: _odd_prime(number) and number != 5,
        False,
        "Neither 2 nor 5 is a factor of 21, but 21 is composite: 3 \N{MULTIPLICATION SIGN} 7 = 21.",
    ),
)
