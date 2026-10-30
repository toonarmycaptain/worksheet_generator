"""Shared test setup."""

import random
from collections.abc import MutableSequence, Sequence
from typing import Any

import pytest
import reportlab.rl_config

# Fixed PDF timestamp and document id, so the same seed gives the same bytes.
# The golden tests (CLI and web) depend on it.
reportlab.rl_config.invariant = 1


@pytest.fixture
def randint_ranges(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    """Record the ``(low, high)`` of each ``random.randint`` call, which then returns ``low``.

    Only for one question at a time: always drawing ``low`` repeats the same operands, which
    a sheet of several questions would keep rejecting.
    """
    asked: list[tuple[int, int]] = []

    def record(low: int, high: int) -> int:
        asked.append((low, high))
        return low

    monkeypatch.setattr(random, "randint", record)
    return asked


@pytest.fixture
def predictable_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the core's choosing and shuffling exact.

    ``random.sample`` takes the first ``k`` items in order, and ``random.shuffle``
    reverses the list. A test using this knows exactly which wrong answers and which
    option order the core produces.
    """

    def first_items(population: Sequence[Any], k: int) -> list[Any]:
        return list(population[:k])

    def reverse(items: MutableSequence[Any]) -> None:
        items.reverse()

    monkeypatch.setattr(random, "sample", first_items)
    monkeypatch.setattr(random, "shuffle", reverse)
