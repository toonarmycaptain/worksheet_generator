"""
The context bank for input-output tables: real situations that relate two quantities.

In every context, the larger quantity is the smaller one plus a number, n, or the smaller one
times n. ``CONTEXTS`` holds the contexts under that operation, ``Operation.ADD`` or
``Operation.MULTIPLY``. A table can take either quantity as its input, so each context serves
two operations: addition or subtraction, or multiplication or division.

A context's text takes these slots:
- ``{name}``: a person's name, from ``core.names``, in the ``title``, the ``rule`` or a noun;
- ``{n}``: the rule's number, in the ``rule``;
- ``{n:point|points}``: any word in the ``rule`` that agrees with n, singular first. Addition
  contexts use it wherever n meets a noun, since their n can be 1; multiplication's n starts at
  2.

The headings take no slots. A new context is one more entry in its tuple; the tests use contexts
of their own, so it changes none of them.
"""

from dataclasses import dataclass

from core.basic_operations.data import Operation


@dataclass(frozen=True)
class TableContext:
    """A real situation relating a smaller quantity to a larger one, worded for a table."""

    title: str  # "Packages of Socks", above the table
    smaller: str  # "Number of Packages", heading the smaller quantity's column or row
    larger: str  # "Number of Socks"
    smaller_noun: str  # "the number of packages", naming the smaller quantity in a sentence
    larger_noun: str  # "the number of socks"
    rule: str  # "There are {n} socks in each package.", stating how the two are related


CONTEXTS: dict[Operation, tuple[TableContext, ...]] = {
    Operation.ADD: (
        TableContext(
            title="Book Sale",
            smaller="Sale Price ($)",
            larger="Regular Price ($)",
            smaller_noun="the sale price",
            larger_noun="the regular price",
            rule="The sale price of each book is ${n} less than the regular price.",
        ),
        TableContext(
            title="Muffins and Cookies",
            smaller="Number of Muffins",
            larger="Number of Cookies",
            smaller_noun="the number of muffins",
            larger_noun="the number of cookies",
            rule="Each day, a bakery makes {n} more {n:cookie|cookies} than muffins.",
        ),
        TableContext(
            title="Canoes and Paddleboats",
            smaller="Number of Paddleboats",
            larger="Number of Canoes",
            smaller_noun="the number of paddleboats",
            larger_noun="the number of canoes",
            rule="Each week, campers rent {n} more {n:canoe|canoes} than paddleboats.",
        ),
        TableContext(
            title="Test Scores",
            smaller="Score Before Bonus",
            larger="Score After Bonus",
            smaller_noun="the score before the bonus",
            larger_noun="the score after the bonus",
            rule="A teacher adds {n} bonus {n:point|points} to each test score.",
        ),
        TableContext(
            title="Weights in Ounces",
            smaller="Working Scale",
            larger="Broken Scale",
            smaller_noun="the weight on the working scale",
            larger_noun="the weight on the broken scale",
            rule="A broken scale always shows {n} more {n:ounce|ounces} than a working scale.",
        ),
        TableContext(
            title="Temperatures",
            smaller="Morning (°F)",
            larger="Afternoon (°F)",
            smaller_noun="the morning temperature",
            larger_noun="the afternoon temperature",
            rule="Each afternoon is {n} {n:degree|degrees} warmer than that morning.",
        ),
        TableContext(
            title="{name}'s Orders",
            smaller="Items Ordered",
            larger="Items Sent",
            smaller_noun="the number of items ordered",
            larger_noun="the number of items sent",
            rule="{name} sends {n} free {n:gift|gifts} with each order.",
        ),
        TableContext(
            title="Toy Prices",
            smaller="Price Paid ($)",
            larger="Selling Price ($)",
            smaller_noun="the price the store paid",
            larger_noun="the selling price",
            rule="A toy store sells each toy for ${n} more than it paid for the toy.",
        ),
        TableContext(
            title="Garden Plants",
            smaller="Tomato Plants",
            larger="Spinach Plants",
            smaller_noun="the number of tomato plants",
            larger_noun="the number of spinach plants",
            rule="Each garden has {n} more spinach {n:plant|plants} than tomato plants.",
        ),
        TableContext(
            title="Classroom Chairs",
            smaller="Number of Students",
            larger="Number of Chairs",
            smaller_noun="the number of students",
            larger_noun="the number of chairs",
            rule="Each classroom has {n} more {n:chair|chairs} than students.",
        ),
    ),
    Operation.MULTIPLY: (
        TableContext(
            title="Packages of Socks",
            smaller="Number of Packages",
            larger="Number of Socks",
            smaller_noun="the number of packages",
            larger_noun="the number of socks",
            rule="There are {n} socks in each package.",
        ),
        TableContext(
            title="Oranges",
            smaller="Number of Bags",
            larger="Number of Oranges",
            smaller_noun="the number of bags",
            larger_noun="the number of oranges",
            rule="There are {n} oranges in each bag.",
        ),
        TableContext(
            title="{name}'s Reading",
            smaller="Number of Months",
            larger="Books Read",
            smaller_noun="the number of months",
            larger_noun="the number of books {name} reads",
            rule="{name} reads {n} books every month.",
        ),
        TableContext(
            title="Amusement Park Rides",
            smaller="Number of Rides",
            larger="Number of Tickets",
            smaller_noun="the number of rides",
            larger_noun="the number of tickets",
            rule="Each ride at an amusement park costs {n} tickets.",
        ),
        TableContext(
            title="Pet Store Fish",
            smaller="Number of Aquariums",
            larger="Number of Fish",
            smaller_noun="the number of aquariums",
            larger_noun="the number of fish",
            rule="Each aquarium at a pet store has {n} fish.",
        ),
        TableContext(
            title="Boxes of Crayons",
            smaller="Number of Boxes",
            larger="Number of Crayons",
            smaller_noun="the number of boxes",
            larger_noun="the number of crayons",
            rule="There are {n} crayons in each box.",
        ),
        TableContext(
            title="Cafeteria Tables",
            smaller="Number of Tables",
            larger="Number of Chairs",
            smaller_noun="the number of tables",
            larger_noun="the number of chairs",
            rule="Each table in the cafeteria has {n} chairs.",
        ),
        TableContext(
            title="{name}'s Dog Walking",
            smaller="Dogs Walked",
            larger="Dollars Earned",
            smaller_noun="the number of dogs {name} walks",
            larger_noun="the number of dollars {name} earns",
            rule="{name} earns ${n} for walking each dog.",
        ),
        TableContext(
            title="Soccer Teams",
            smaller="Number of Teams",
            larger="Number of Players",
            smaller_noun="the number of teams",
            larger_noun="the number of players",
            rule="Each soccer team has {n} players.",
        ),
        TableContext(
            title="Flowers in Vases",
            smaller="Number of Vases",
            larger="Number of Flowers",
            smaller_noun="the number of vases",
            larger_noun="the number of flowers",
            rule="Each vase holds {n} flowers.",
        ),
        TableContext(
            title="Burritos Made",
            smaller="Pounds of Meat",
            larger="Number of Burritos",
            smaller_noun="the number of pounds of meat",
            larger_noun="the number of burritos",
            rule="A chef makes {n} burritos with every pound of meat.",
        ),
        TableContext(
            title="Sticker Packs",
            smaller="Number of Packs",
            larger="Number of Stickers",
            smaller_noun="the number of packs",
            larger_noun="the number of stickers",
            rule="Each pack of stickers has {n} stickers.",
        ),
        TableContext(
            title="Garden Rows",
            smaller="Number of Rows",
            larger="Number of Plants",
            smaller_noun="the number of rows",
            larger_noun="the number of plants",
            rule="A garden has {n} plants in each row.",
        ),
        TableContext(
            title="{name}'s Savings",
            smaller="Number of Weeks",
            larger="Dollars Saved",
            smaller_noun="the number of weeks",
            larger_noun="the number of dollars {name} saves",
            rule="{name} saves ${n} every week.",
        ),
        TableContext(
            title="Bracelets Sold",
            smaller="Number of Dollars",
            larger="Number of Bracelets",
            smaller_noun="the number of dollars",
            larger_noun="the number of bracelets {name} sells",
            rule="{name} sells {n} bracelets for 1 dollar.",
        ),
    ),
}
