"""Answer sheets for the self-check tiles answer case: the tiles, the answer bank and the pattern.

The case has 12 slots, lettered A to L in two rows of six (A to F on top, G to L below). A
student solves question n and puts tile n in the slot of its answer. Closing and flipping the
case swaps the two rows, and the tile backs then make a picture. ``slot_of`` is the one input:
``slot_of[n - 1]`` is the slot (0 for A, up to 11 for L) holding question n's answer. The bank
and the pattern both follow from it. A sheet with fewer than 12 questions uses only the first
tiles, and the slots nothing points to are blocked out, shown as ``None``.

``slot_of`` comes from ``random_slot_of`` or from ``conventional_slot_of``. The second picks the
slots so the tile backs make a conventional picture: three 2 by 2 blocks, one per color, in which
no tile edge cuts a colored shape.
"""

import itertools
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
COLORS = ("yellow", "blue", "red")
TILE_OF = {piece: tile for tile, piece in TILES.items()}  # (color, stem, flare) -> tile number

# a piece is a tile's (stem side, flare side), color aside
type Piece = tuple[str, str]
PIECES: list[Piece] = sorted({(stem, flare) for _, stem, flare in TILES.values()})


def edge(piece: Piece, side: str) -> str:
    """How a piece's colored shape meets one edge of its tile: ``full``, ``empty`` or a half.

    The stem's edge and the flare's edge are colored along their whole length. The edge opposite
    the stem only touches the shape at a corner, so it is white. The edge opposite the flare is
    colored for the half that the stem covers.
    """
    stem, flare = piece
    if side in (stem, flare):
        return "full"
    if side in ("left", "right"):
        return "empty"
    return f"{stem} half"


def fits_beside(left: Piece, right: Piece) -> bool:
    """Whether two tiles side by side show no cut edge where they touch, color aside."""
    return edge(left, "right") == edge(right, "left")


def fits_above(top: Piece, bottom: Piece) -> bool:
    """Whether two tiles one above the other show no cut edge where they touch, color aside."""
    return edge(top, "bottom") == edge(bottom, "top")


# every way to lay a color's four pieces in a 2 by 2 block, as (top left, top right, bottom left,
# bottom right), so that the shape runs on across all four touching edges: 10 of the 24
BLOCK_SHAPES: tuple[tuple[Piece, Piece, Piece, Piece], ...] = tuple(
    (top_left, top_right, bottom_left, bottom_right)
    for top_left, top_right, bottom_left, bottom_right in itertools.permutations(PIECES)
    if fits_beside(top_left, top_right)
    and fits_beside(bottom_left, bottom_right)
    and fits_above(top_left, bottom_left)
    and fits_above(top_right, bottom_right)
)


def random_slot_of(count: int) -> tuple[int, ...]:
    """A random slot for each of ``count`` questions: no slot is used twice."""
    slots = list(range(SLOTS))
    random.shuffle(slots)
    return tuple(slots[:count])


def conventional_slot_of(count: int) -> tuple[int, ...]:
    """The slots of ``count`` questions that make a conventional picture on the back.

    The picture is a 2 by 2 block of each color side by side, in a random color order, and each
    block takes a random one of the ``BLOCK_SHAPES``: 6 * 10 ** 3 pictures in all. Only the
    first ``count`` tiles are placed, so a shorter sheet shows part of its picture.
    """
    top_row: list[int] = []
    bottom_row: list[int] = []
    for color in random.sample(COLORS, k=len(COLORS)):
        top_left, top_right, bottom_left, bottom_right = (
            TILE_OF[color, *piece] for piece in random.choice(BLOCK_SHAPES)
        )
        top_row += [top_left, top_right]
        bottom_row += [bottom_left, bottom_right]
    # the picture is seen from the back, where the rows are swapped: see ``pattern``
    tile_in_slot = bottom_row + top_row
    return tuple(tile_in_slot.index(tile) for tile in range(1, count + 1))


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
