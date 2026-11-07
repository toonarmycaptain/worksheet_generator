"""Test data shared by more than one test module."""

from core.placevalue.data import PlaceValueForm

STANDARD, EXPANDED, UNIT, EXPANDED_NOTATION, WORD, BLOCKS = PlaceValueForm  # in the enum's order

TIMES = "\N{MULTIPLICATION SIGN}"

# the complex pattern's slots when a test makes ``random.shuffle`` reverse its list: L to A
REVERSED_SLOTS = (11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
# the slots of a real case (tile 1 in H, tile 2 in J, tile 3 in K, ...): three clean blocks
REAL_CASE_SLOTS = (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2)
