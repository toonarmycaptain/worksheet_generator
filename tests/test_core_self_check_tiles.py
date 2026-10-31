"""The self-check tiles core: the tile table, the answer bank, and the pattern the tiles make.

The pattern is checked against two arrangements read off a real case: each tile's slot, and the
tiles seen in the rows from the back after the flip.
"""

import pytest

from core.self_check_tiles import (
    BLOCK_SHAPES,
    TILES,
    answer_bank,
    conventional_slot_of,
    fits_above,
    fits_beside,
    pattern,
    random_slot_of,
    tile_outline,
)

# the four piece types: which side the stem is on, and which side the flare is
LB, LT, RB, RT = ("left", "bottom"), ("left", "top"), ("right", "bottom"), ("right", "top")
PIECE_TYPES = [LB, LT, RB, RT]
HEXAGON = (RB, LB, RT, LT)  # the shape of a clean block, as in the real case
RING = (LT, RT, LB, RB)


def test_the_tiles_are_numbered_1_to_12() -> None:
    assert list(TILES) == list(range(1, 13))


@pytest.mark.parametrize("color", ["yellow", "blue", "red"])
def test_each_color_has_one_tile_of_each_piece_type(color: str) -> None:
    """Every color has four tiles, and no two of them have the same stem and flare sides."""
    pieces = sorted(
        (stem, flare) for tile_color, stem, flare in TILES.values() if tile_color == color
    )
    assert pieces == PIECE_TYPES


@pytest.mark.parametrize(
    ("tile", "outline"),
    [
        (1, ((0, 0), (0.5, 0), (0.5, 0.5), (1, 1), (0, 1))),  # stem left, flare bottom
        (3, ((1, 0), (0.5, 0), (0.5, 0.5), (0, 1), (1, 1))),  # stem right, flare bottom
        (5, ((1, 1), (0.5, 1), (0.5, 0.5), (0, 0), (1, 0))),  # stem right, flare top
        (10, ((0, 1), (0.5, 1), (0.5, 0.5), (1, 0), (0, 0))),  # stem left, flare top
    ],
)
def test_tile_outline(tile: int, outline: tuple[tuple[float, float], ...]) -> None:
    """The outline is the left-stem, bottom-flare polygon, mirrored to the tile's sides."""
    assert tile_outline(tile) == outline


@pytest.mark.parametrize(
    ("slot_of", "bank"),
    [
        # each answer in the slot of its own number
        ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), (11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22)),
        # question 1's answer in slot L, question 12's in slot A
        ((11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0), (22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11)),
        # question 1 (answer 11) in C, question 2 (12) in A, question 3 (13) in E, and so on
        ((2, 0, 4, 9, 10, 7, 8, 1, 5, 3, 11, 6), (12, 18, 11, 20, 13, 19, 22, 16, 17, 14, 15, 21)),
        # four questions: answers 11 to 14 in F, A, L, G, and the other slots blocked out
        (
            (5, 0, 11, 6),
            (12, None, None, None, None, 11, 14, None, None, None, None, 13),
        ),
    ],
)
def test_answer_bank(slot_of: tuple[int, ...], bank: tuple[int | None, ...]) -> None:
    """Question n's answer (10 + n) sits in the slot ``slot_of[n - 1]``."""
    assert answer_bank(range(11, 11 + len(slot_of)), slot_of) == bank


@pytest.mark.parametrize(
    ("slot_of", "rows"),
    [
        # the case's front rows are tiles 1 to 6 over 7 to 12, and the flip swaps them
        (
            (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
            ((7, 8, 9, 10, 11, 12), (1, 2, 3, 4, 5, 6)),
        ),
        # tiles 3, 9 in G, H and 5, 11 in A, B: a clean red block at the left of the back
        (
            (2, 3, 6, 4, 0, 5, 8, 9, 7, 10, 1, 11),
            ((3, 9, 7, 8, 10, 12), (5, 11, 1, 2, 4, 6)),
        ),
        # a real case, a black one: tiles in A to F were 7 10 12 8 5 11 and in G to L 4 1 6 2 3 9
        (
            (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2),
            ((4, 1, 6, 2, 3, 9), (7, 10, 12, 8, 5, 11)),
        ),
        # another: A to F were 2 8 1 10 3 9 and G to L 12 6 7 4 5 11
        (
            (2, 0, 4, 9, 10, 7, 8, 1, 5, 3, 11, 6),
            ((12, 6, 7, 4, 5, 11), (2, 8, 1, 10, 3, 9)),
        ),
        # four questions: tiles 1 to 4 in F, A, L, G, and nothing in the other slots
        (
            (5, 0, 11, 6),
            ((4, None, None, None, None, 3), (2, None, None, None, None, 1)),
        ),
    ],
)
def test_pattern(slot_of: tuple[int, ...], rows: tuple[tuple[int | None, ...], ...]) -> None:
    """The pattern is the tiles of slots G to L over those of A to F."""
    assert pattern(slot_of) == rows


@pytest.mark.parametrize(
    ("count", "slot_of"),
    [
        (12, (11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)),
        (4, (11, 10, 9, 8)),
        (1, (11,)),
    ],
)
def test_random_slot_of_takes_the_first_of_the_shuffled_slots(
    count: int, slot_of: tuple[int, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the shuffle reversing its list, each question gets the next slot down from L."""
    monkeypatch.setattr("random.shuffle", lambda items: items.reverse())
    assert random_slot_of(count) == slot_of


@pytest.mark.parametrize("count", [1, 4, 12])
def test_random_slot_of_uses_no_slot_twice(count: int) -> None:
    slots = random_slot_of(count)
    assert len(set(slots)) == count
    assert set(slots) <= set(range(12))


@pytest.mark.parametrize(
    ("left", "right", "fits"),
    [
        (RB, LB, True),  # the two stems meet, so the color runs on
        (LB, RB, True),  # the two stems are on the outside, so the white runs on
        (RB, LT, True),  # the flare sides make no difference
        (RB, RB, False),  # a stem's edge against white
        (LB, LB, False),  # white against a stem's edge
    ],
)
def test_fits_beside(left: tuple[str, str], right: tuple[str, str], fits: bool) -> None:
    assert fits_beside(left, right) is fits


@pytest.mark.parametrize(
    ("top", "bottom", "fits"),
    [
        (LB, LT, True),  # a flare's edge against a flare's edge: the color runs on
        (LT, LB, True),  # two stem halves, on the same side, meet
        (LT, RB, False),  # the stem halves are on opposite sides
        (LB, RB, False),  # a flare's edge against a stem half
        (LT, RT, False),  # a stem half against a flare's edge
    ],
)
def test_fits_above(top: tuple[str, str], bottom: tuple[str, str], fits: bool) -> None:
    assert fits_above(top, bottom) is fits


def test_there_are_ten_block_shapes() -> None:
    assert len(BLOCK_SHAPES) == 10


def test_the_block_shapes() -> None:
    """Top left, top right, bottom left and bottom right of each of the ten seamless blocks."""
    assert set(BLOCK_SHAPES) == {
        (LB, RB, LT, RT),  # white hourglass
        (LB, RB, RT, LT),  # fork
        (RB, LB, LT, RT),  # arch
        (RB, LB, RT, LT),  # hexagon
        (RB, LT, RT, LB),  # arrow pointing left
        (LT, RT, LB, RB),  # ring
        (RT, LB, RB, LT),  # arrow pointing right
        (RT, LT, RB, LB),  # color hourglass
        (LB, RT, LT, RB),  # zigzag
        (LT, RB, LB, RT),  # its mirror image
    }


@pytest.mark.parametrize(
    ("colors", "shape", "count", "slot_of"),
    [
        # yellow, blue, red clean blocks, as on a real case: tiles in A to F were 7 10 12 8 5 11
        # and in G to L 4 1 6 2 3 9
        (
            ["yellow", "blue", "red"],
            HEXAGON,
            12,
            (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2),
        ),
        (["yellow", "blue", "red"], HEXAGON, 4, (7, 9, 10, 6)),
        (["yellow", "blue", "red"], HEXAGON, 1, (7,)),
        # rings, red first: A to F hold 9 3 1 4 2 6 and G to L 11 5 10 7 8 12
        (
            ["red", "yellow", "blue"],
            RING,
            12,
            (2, 4, 1, 3, 7, 5, 9, 10, 0, 8, 6, 11),
        ),
    ],
)
def test_conventional_slot_of_places_each_tile_by_its_color_and_piece(
    colors: list[str],
    shape: tuple[tuple[str, str], ...],
    count: int,
    slot_of: tuple[int, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the colors in the given order and every block the same shape, the slots follow."""
    monkeypatch.setattr("random.sample", lambda population, k: colors)
    monkeypatch.setattr("random.choice", lambda options: shape)
    assert conventional_slot_of(count) == slot_of


@pytest.mark.parametrize("count", [1, 4, 12])
def test_conventional_slot_of_uses_no_slot_twice(count: int) -> None:
    slots = conventional_slot_of(count)
    assert len(set(slots)) == count
    assert set(slots) <= set(range(12))
