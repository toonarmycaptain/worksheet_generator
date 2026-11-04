"""
Answer sheets for the self-check tiles case: the questions, the tiles, the answer bank and the
pattern.

The case has 12 slots, lettered A to L in two rows of six (A to F on top, G to L below). A
student solves question n and places tile n in the slot holding its answer. Closing and
flipping the case swaps the two rows, and the tile backs then form a picture.

``slot_of`` is the single input from which the bank and the pattern are derived:
``slot_of[n - 1]`` is the slot (0 for A, up to 11 for L) holding question n's answer. A sheet
with fewer than 12 questions uses only the first tiles; slots that no question uses are blocked
out, represented as ``None``.

``slot_of`` comes from ``random_slot_of`` or ``conventional_slot_of``. The latter chooses slots
so the tile backs form a conventional picture: three 2 by 2 blocks, one per color, in which no
tile edge cuts through a colored shape.
"""

import itertools
import random
from collections.abc import Sequence
from dataclasses import dataclass

SLOTS = 12
SLOTS_PER_ROW = 6


@dataclass(frozen=True)
class TileQuestion:
    """
    A question as displayed on the self-check tiles sheet, independent of its question type.

    ``prompt`` is the text the student reads, ``answer`` is the text in the answer's bank box,
    and ``solution`` is the completed question for the answer key, such as "3 + 4 = 7". A
    ``BLANK`` in the prompt is drawn as an empty square.
    """

    prompt: str
    answer: str
    solution: str


# tile number -> (color, stem side, flare side), as printed on the case's tile backs
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

# A piece is a tile's shape without its color: (stem side, flare side).
type Piece = tuple[str, str]
PIECES: list[Piece] = sorted({(stem, flare) for _, stem, flare in TILES.values()})


def edge(piece: Piece, side: str) -> str:
    """
    Return how a piece's colored shape meets one side of its tile: ``full``, ``empty`` or a half.

    The stem's side and the flare's side are colored along their full length. The side opposite
    the stem touches the shape only at a corner, so it is white. The side opposite the flare is
    colored along the half the stem covers, such as ``left half``.
    """
    stem, flare = piece
    if side in (stem, flare):
        return "full"
    if side in ("left", "right"):
        return "empty"
    return f"{stem} half"


def fits_beside(left: Piece, right: Piece) -> bool:
    """Return whether two horizontally adjacent tiles meet without a cut edge, ignoring color."""
    return edge(left, "right") == edge(right, "left")


def fits_above(top: Piece, bottom: Piece) -> bool:
    """Return whether two vertically adjacent tiles meet without a cut edge, ignoring color."""
    return edge(top, "bottom") == edge(bottom, "top")


# Every arrangement of a color's four pieces in a 2 by 2 block, as (top left, top right, bottom
# left, bottom right), in which the shape continues across all four inner edges: 10 of the 24.
BLOCK_SHAPES: tuple[tuple[Piece, Piece, Piece, Piece], ...] = tuple(
    (top_left, top_right, bottom_left, bottom_right)
    for top_left, top_right, bottom_left, bottom_right in itertools.permutations(PIECES)
    if fits_beside(top_left, top_right)
    and fits_beside(bottom_left, bottom_right)
    and fits_above(top_left, bottom_left)
    and fits_above(top_right, bottom_right)
)


def random_slot_of(count: int) -> tuple[int, ...]:
    """Return a random, distinct slot for each of ``count`` questions."""
    slots = list(range(SLOTS))
    random.shuffle(slots)
    return tuple(slots[:count])


def conventional_slot_of(count: int) -> tuple[int, ...]:
    """
    Return slots for ``count`` questions whose tile backs form a conventional picture.

    The picture is a 2 by 2 block of each color side by side, in random color order, each block
    taking a random one of the ``BLOCK_SHAPES``: 6 * 10 ** 3 pictures in all. Only the first
    ``count`` tiles are placed, so a shorter sheet shows part of its picture.
    """
    top_row: list[int] = []
    bottom_row: list[int] = []
    for color in random.sample(COLORS, k=len(COLORS)):
        top_left, top_right, bottom_left, bottom_right = (
            TILE_OF[color, *piece] for piece in random.choice(BLOCK_SHAPES)
        )
        top_row += [top_left, top_right]
        bottom_row += [bottom_left, bottom_right]
    # The picture is viewed from the back, where the rows are swapped; see ``pattern``.
    tile_in_slot = bottom_row + top_row
    return tuple(tile_in_slot.index(tile) for tile in range(1, count + 1))


def answer_bank[Answer](
    answers: Sequence[Answer], slot_of: Sequence[int]
) -> tuple[Answer | None, ...]:
    """
    Return the answer in each slot, from A: slot ``slot_of[i]`` holds ``answers[i]``.

    A slot that no question uses is ``None``.
    """
    bank: list[Answer | None] = [None] * SLOTS
    for slot, answer in zip(slot_of, answers, strict=True):
        bank[slot] = answer
    return tuple(bank)


def pattern(slot_of: Sequence[int]) -> tuple[tuple[int | None, ...], ...]:
    """
    Return the tile numbers seen on the back of the closed case, in two rows of six.

    Tile n sits in slot ``slot_of[n - 1]``. Flipping the case swaps the rows but preserves the
    order along each row, so the first row returned is the case's bottom row (G to L). A slot
    that no question uses is ``None``.
    """
    tile_in_slot: list[int | None] = [None] * SLOTS
    for tile, slot in enumerate(slot_of, start=1):
        tile_in_slot[slot] = tile
    return (tuple(tile_in_slot[SLOTS_PER_ROW:]), tuple(tile_in_slot[:SLOTS_PER_ROW]))


def tile_outline(tile: int) -> tuple[tuple[float, float], ...]:
    """
    Return the corners of a tile's colored shape within a unit square, with y pointing down.

    The shape is a stem (half the tile's width, full height) with a flare: a triangle from the
    tile's centre to the far corner, against the stem's inner edge. The outline is defined for
    a left stem with the flare at the bottom, and mirrored for a right stem or a top flare.
    """
    _, stem, flare = TILES[tile]
    left_and_bottom = ((0, 0), (0.5, 0), (0.5, 0.5), (1, 1), (0, 1))
    return tuple(
        (1 - x if stem == "right" else x, 1 - y if flare == "top" else y)
        for x, y in left_and_bottom
    )
