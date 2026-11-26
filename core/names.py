"""
Given names for the people in questions, shared by every question bank.

New names go at the end. Tests script ``random`` to take names from the start of ``NAMES``, so
their wording stays the same.
"""

import random
from collections.abc import Sequence

NAMES = (
    "Maria",
    "Jamal",
    "Priya",
    "Liam",
    "Sofia",
    "Chen",
    "Aisha",
    "Diego",
    "Emma",
    "Noah",
    "Zoe",
    "Omar",
    "Ava",
    "Kai",
    "Lucia",
    "Malik",
    "Hana",
    "Leo",
    "Nina",
    "Theo",
    "Rosa",
    "Sam",
    "Ivy",
    "Dev",
    "Mateo",
    "Grace",
    "Ravi",
    "Elena",
    "Jonah",
    "Mia",
    "Tariq",
    "Lily",
    "Jaylen",
    "Seth",
    "Elly",
    "Ulysses",
    "Maggie",
    "Palmer",
    "Brenda",
    "Carla",
)


class NameDealer:
    """Hands out ``names``, such as ``NAMES``, none twice on a sheet while any are left."""

    def __init__(self, names: Sequence[str]) -> None:
        self._names = tuple(names)
        self._left = random.sample(self._names, len(self._names))

    def take(self, count: int) -> tuple[str, ...]:
        """Return ``count`` names with different first letters, so that each can letter a point
        or be told apart by its initial."""
        taken: list[str] = []
        for name in [*self._left, *self._names]:
            if len(taken) == count:
                break
            if name[0] not in {each[0] for each in taken}:
                taken.append(name)
        for name in taken:
            if name in self._left:
                self._left.remove(name)
        if not self._left:
            self._left = random.sample(self._names, len(self._names))
        return tuple(taken)
