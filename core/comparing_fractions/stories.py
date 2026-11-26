"""
The stories comparing fractions word problems tell: two people each with a fraction of a whole
the same size, a length, or a fraction of a group of objects.

New stories go at the top of each bank. Tests script ``random`` to take stories from the end of
a bank, so their wording stays the same.
"""

from dataclasses import dataclass

from core.comparing_fractions.data import Representation
from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import LengthUnit


@dataclass(frozen=True)
class WholeStory:
    """
    A story of two people each with a whole of one kind, such as a pizza. ``setup`` has slots
    for the two names, ``{first}`` and ``{second}``, and ``same_size`` says the wholes are the
    same size, or is empty when ``setup`` already makes them one whole ("the same book"). Each
    person ``verb``s a fraction "of" ``article`` ``whole``: "Ana eats 3/8 of a pizza." The
    question asks who ``verb``s more ``amount``: "Who eats more pizza?", "Who reads more of the
    book?", or with no amount, "Who paints more?"; ``base`` is the verb after "does": "Does Ana
    eat more or less pizza than Ben?".

    With ``sizes``, the wholes can be different sizes, "a small pizza" and "a large pizza", so
    there's no telling who has more. ``wholes`` is the plural. The two wholes are drawn as
    ``representation``, if any, as ``look`` or as plain shapes.
    """

    setup: str
    same_size: str
    verb: str
    base: str
    article: str
    whole: str
    wholes: str
    amount: str
    sizes: bool
    representation: Representation | None = None
    look: DrawnObject | None = None


@dataclass(frozen=True)
class LengthStory:
    """
    A story of two people each with a length in one of ``units``. ``setup`` has slots for the
    two names, ``{first}`` and ``{second}``. Each length is a ``thing`` of the person's, "Ana's
    worm", or with no thing, the person: "Ana walks 3/4 mile." It ``verb``s a fraction of a
    unit, then ``tail``: "Ana's worm is 1/2 foot long." The question asks whose is ``longer`` or
    ``shorter``: "Whose worm is longer?", "Who walks a shorter distance?". Both can be ``same``,
    "the same length", where ``plural_verb`` and ``things`` are the plurals: "The worms are the
    same length."
    """

    setup: str
    thing: str | None
    things: str | None
    verb: str
    plural_verb: str
    tail: str
    longer: str
    shorter: str
    same: str
    units: tuple[LengthUnit, ...]


@dataclass(frozen=True)
class GroupStory:
    """A story of two people each with a group of objects of ``kind``, ``verb``ing some of them:
    "Kayla has 6 blocks and paints 3 of them." ``setup`` has slots for the two names, ``{first}``
    and ``{second}``; ``base`` is the verb after "they": "They paint the same fraction"; ``done``
    describes the objects: "A greater fraction of Kayla's blocks are painted."""

    setup: str
    kind: DrawnObject
    verb: str
    base: str
    done: str


WHOLE_STORIES = (
    WholeStory(
        "{first} and {second} each paint a poster.",
        "The posters are the same size.",
        "paints",
        "paint",
        "a",
        "poster",
        "posters",
        "",
        sizes=True,
        representation=Representation.GRID,
    ),
    WholeStory(
        "{first} and {second} each have a bottle of water.",
        "The bottles are the same size.",
        "drinks",
        "drink",
        "a",
        "bottle of water",
        "bottles",
        "water",
        sizes=True,
    ),
    WholeStory(
        "{first} and {second} are doing the same puzzle.",
        "",
        "finishes",
        "finish",
        "the",
        "puzzle",
        "puzzles",
        "of the puzzle",
        sizes=False,
    ),
    WholeStory(
        "{first} and {second} each have a chocolate bar.",
        "The chocolate bars are the same size.",
        "eats",
        "eat",
        "a",
        "chocolate bar",
        "chocolate bars",
        "chocolate",
        sizes=True,
        representation=Representation.GRID,
        look=DrawnObject.CHOCOLATE_BAR,
    ),
    WholeStory(
        "{first} and {second} each have a cake.",
        "The cakes are the same size.",
        "eats",
        "eat",
        "a",
        "cake",
        "cakes",
        "cake",
        sizes=True,
        representation=Representation.GRID,
        look=DrawnObject.SQUARE_CAKE,
    ),
    WholeStory(
        "{first} and {second} each color a banner.",
        "The banners are the same size.",
        "colors",
        "color",
        "a",
        "banner",
        "banners",
        "",
        sizes=True,
        representation=Representation.STRIP,
    ),
    WholeStory(
        "{first} and {second} each have a pan of brownies.",
        "The pans are the same size.",
        "eats",
        "eat",
        "a",
        "pan of brownies",
        "pans of brownies",
        "brownies",
        sizes=True,
        representation=Representation.GRID,
    ),
    WholeStory(
        "{first} and {second} each plant a garden.",
        "The gardens are the same size.",
        "plants",
        "plant",
        "a",
        "garden",
        "gardens",
        "",
        sizes=True,
        representation=Representation.GRID,
    ),
    WholeStory(
        "{first} and {second} each paint a wall.",
        "The walls are the same size.",
        "paints",
        "paint",
        "a",
        "wall",
        "walls",
        "",
        sizes=True,
        representation=Representation.GRID,
    ),
    WholeStory(
        "{first} and {second} each have a milkshake.",
        "The milkshakes are the same size.",
        "drinks",
        "drink",
        "a",
        "milkshake",
        "milkshakes",
        "milkshake",
        sizes=True,
    ),
    WholeStory(
        "{first} and {second} are reading the same book.",
        "",
        "reads",
        "read",
        "the",
        "book",
        "books",
        "of the book",
        sizes=False,
    ),
    WholeStory(
        "{first} and {second} each have a pie.",
        "The pies are the same size.",
        "eats",
        "eat",
        "a",
        "pie",
        "pies",
        "pie",
        sizes=True,
        representation=Representation.CIRCLE,
    ),
    WholeStory(
        "{first} and {second} each have a pizza.",
        "The pizzas are the same size.",
        "eats",
        "eat",
        "a",
        "pizza",
        "pizzas",
        "pizza",
        sizes=True,
        representation=Representation.CIRCLE,
        look=DrawnObject.PIZZA,
    ),
)

LENGTH_STORIES = (
    LengthStory(
        "{first} and {second} each make a paper chain.",
        "paper chain",
        "paper chains",
        "is",
        "are",
        " long",
        "longer",
        "shorter",
        "the same length",
        (LengthUnit.YARD, LengthUnit.METER),
    ),
    LengthStory(
        "{first} and {second} each run on a track.",
        None,
        None,
        "runs",
        "run",
        "",
        "farther",
        "a shorter distance",
        "the same distance",
        (LengthUnit.MILE, LengthUnit.KILOMETER),
    ),
    LengthStory(
        "{first} and {second} each have a piece of yarn.",
        "yarn",
        "pieces of yarn",
        "is",
        "are",
        " long",
        "longer",
        "shorter",
        "the same length",
        (LengthUnit.FOOT, LengthUnit.YARD, LengthUnit.METER),
    ),
    LengthStory(
        "{first} and {second} each have a pencil.",
        "pencil",
        "pencils",
        "is",
        "are",
        " long",
        "longer",
        "shorter",
        "the same length",
        (LengthUnit.FOOT,),
    ),
    LengthStory(
        "{first} and {second} each watch a snail crawl.",
        "snail",
        "snails",
        "crawls",
        "crawl",
        "",
        "farther",
        "a shorter distance",
        "the same distance",
        (LengthUnit.INCH, LengthUnit.FOOT, LengthUnit.CENTIMETER),
    ),
    LengthStory(
        "{first} and {second} each walk home from school.",
        None,
        None,
        "walks",
        "walk",
        "",
        "farther",
        "a shorter distance",
        "the same distance",
        (LengthUnit.MILE, LengthUnit.KILOMETER),
    ),
    LengthStory(
        "{first} and {second} each have a frog in a jumping contest.",
        "frog",
        "frogs",
        "jumps",
        "jump",
        "",
        "farther",
        "a shorter distance",
        "the same distance",
        (LengthUnit.FOOT, LengthUnit.YARD, LengthUnit.METER),
    ),
    LengthStory(
        "{first} and {second} each cut a piece of ribbon.",
        "ribbon",
        "ribbons",
        "is",
        "are",
        " long",
        "longer",
        "shorter",
        "the same length",
        (LengthUnit.FOOT, LengthUnit.YARD, LengthUnit.METER),
    ),
    LengthStory(
        "{first} and {second} each measure a worm.",
        "worm",
        "worms",
        "is",
        "are",
        " long",
        "longer",
        "shorter",
        "the same length",
        (LengthUnit.INCH, LengthUnit.FOOT, LengthUnit.CENTIMETER),
    ),
)

GROUP_STORIES = (
    GroupStory(
        "{first} and {second} are decorating cookies.",
        DrawnObject.COOKIE,
        "decorates",
        "decorate",
        "decorated",
    ),
    GroupStory(
        "{first} and {second} are coloring fish on a page.",
        DrawnObject.FISH,
        "colors",
        "color",
        "colored",
    ),
    GroupStory(
        "{first} and {second} are painting leaves for an art project.",
        DrawnObject.LEAF,
        "paints",
        "paint",
        "painted",
    ),
    GroupStory(
        "{first} and {second} are wrapping gifts.", DrawnObject.GIFT, "wraps", "wrap", "wrapped"
    ),
    GroupStory(
        "{first} and {second} are filling balloons with water.",
        DrawnObject.BALLOON,
        "fills",
        "fill",
        "filled",
    ),
    GroupStory(
        "{first} and {second} are frosting cupcakes.",
        DrawnObject.CUPCAKE,
        "frosts",
        "frost",
        "frosted",
    ),
    GroupStory(
        "{first} and {second} are coloring flowers on a page.",
        DrawnObject.FLOWER,
        "colors",
        "color",
        "colored",
    ),
    GroupStory(
        "{first} and {second} are coloring stars on a page.",
        DrawnObject.STAR,
        "colors",
        "color",
        "colored",
    ),
    GroupStory(
        "{first} and {second} are painting blocks.", DrawnObject.BLOCK, "paints", "paint", "painted"
    ),
)
