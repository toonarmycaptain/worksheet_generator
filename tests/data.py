"""Test data shared by more than one test module."""

from core.discrete_data.topics import FriendsTopic, NumberListTopic, SurveyTopic
from core.placevalue.data import PlaceValueForm

STANDARD, EXPANDED, UNIT, EXPANDED_NOTATION, WORD, BLOCKS = PlaceValueForm  # in the enum's order

TIMES = "\N{MULTIPLICATION SIGN}"
MINUS = "\N{MINUS SIGN}"

# Data-set topics and names standing in for the banks', which grow, so that a new topic or name
# doesn't change what a test expects
FRUIT = SurveyTopic(
    title="Favorite Fruit",
    category_header="Fruit",
    favorite="fruit",
    categories=("apples", "bananas", "grapes", "pears", "plums"),
)
CANS = FriendsTopic(
    title="Cans Collected",
    unit="cans",
    unit_singular="can",
    verb="collect",
    verb_past="collected",
    intro="Four friends collected cans for a food drive.",
)
CLASSES = NumberListTopic(
    title="Students in Each Class",
    axis_title="Number of Students",
    ticks=range(15, 31),
    unit="classes",
    unit_singular="class",
    phrase="have {amount}",
    amount_singular="student",
    amount_plural="students",
    intro="The list shows how many students are in each class at {person}'s school.",
)
COINS = NumberListTopic(
    title="Coins in a Piggy Bank",
    axis_title="Value of Coin (cents)",
    ticks=range(0, 31, 5),
    unit="coins",
    unit_singular="coin",
    phrase="are worth {amount}",
    amount_singular="cent",
    amount_plural="cents",
    intro="{person} emptied a piggy bank. The list shows the value of each coin in cents.",
    possible_values=(5, 10, 25),
)
NAMES = ("Ana", "Ben", "Cy", "Dot", "Eve")

# the complex pattern's slots when a test makes ``random.shuffle`` reverse its list: L to A
REVERSED_SLOTS = (11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
# the slots of a real case (tile 1 in H, tile 2 in J, tile 3 in K, ...): three clean blocks
REAL_CASE_SLOTS = (7, 9, 10, 6, 4, 8, 0, 3, 11, 1, 5, 2)
