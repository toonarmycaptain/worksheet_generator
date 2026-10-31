"""Answer sheets for the self-check tiles answer case: the tiles, the answer bank and the pattern.

The case has 12 slots, lettered A to L in two rows of six (A to F on top, G to L below). A
student solves question n and puts tile n in the slot of its answer. Closing and flipping the
case swaps the two rows, and the tile backs then make a picture. ``slot_of`` is the one input:
``slot_of[n - 1]`` is the slot (0 for A, up to 11 for L) holding question n's answer. The bank
and the pattern both follow from it. A sheet with fewer than 12 questions uses only the first
tiles, and the slots nothing points to are blocked out, shown as ``None``.
"""

import random
from collections.abc import Sequence

SLOTS = 12
SLOTS_PER_ROW = 6

# tile number -> (color, side of the stem, side of the flare), read off the case's tile backs
TILES: dict[int, tuple[str, str, str]] = {
    1: ("yellow", "left", "bottom"),
    2: ("blue", "left", "bottom"),
    3: ("red", "right", "bottom"),
    4: ("yellow", "right", "bottom"),
    5: ("red", "right", "top"),
    6: ("blue", "right", "bottom"),
    7: ("yellow", "right", "top"),
    8: ("blue", "left", "top"),
    9: ("red", "left", "bottom"),
    10: ("yellow", "left", "top"),
    11: ("red", "left", "top"),
    12: ("blue", "right", "top"),
}


def random_slot_of(count: int) -> tuple[int, ...]:
    """A random slot for each of ``count`` questions: no slot is used twice."""
    slots = list(range(SLOTS))
    random.shuffle(slots)
    return tuple(slots[:count])


def answer_bank(answers: Sequence[int], slot_of: Sequence[int]) -> tuple[int | None, ...]:
    """The answer in each slot, A first: slot ``slot_of[n]`` holds question n's answer.

    A slot that no question uses is ``None``.
    """
    bank: list[int | None] = [None] * SLOTS
    for slot, answer in zip(slot_of, answers, strict=True):
        bank[slot] = answer
    return tuple(bank)


def pattern(slot_of: Sequence[int]) -> tuple[tuple[int | None, ...], ...]:
    """The tile numbers seen from the back of the closed case, in two rows of six.

    Tile n sits in slot ``slot_of[n - 1]``. Flipping the case swaps the rows and keeps the
    order along each row, so the first row here is the case's bottom row (G to L). A slot that
    no question uses is ``None``.
    """
    tile_in_slot: list[int | None] = [None] * SLOTS
    for tile, slot in enumerate(slot_of, start=1):
        tile_in_slot[slot] = tile
    return (tuple(tile_in_slot[SLOTS_PER_ROW:]), tuple(tile_in_slot[:SLOTS_PER_ROW]))


def tile_outline(tile: int) -> tuple[tuple[float, float], ...]:
    """The corners of a tile's colored shape in a unit square, with y pointing down.

    The shape is a stem (half the tile's width, full height) with a flare: a triangle from the
    tile's centre to the far corner, against the stem's inner edge. It starts as a left stem
    with the flare at the bottom, then mirrors for a right stem or a flare at the top.
    """
    _, stem, flare = TILES[tile]
    left_and_bottom = ((0, 0), (0.5, 0), (0.5, 0.5), (1, 1), (0, 1))
    return tuple(
        (1 - x if stem == "right" else x, 1 - y if flare == "top" else y)
        for x, y in left_and_bottom
    )
