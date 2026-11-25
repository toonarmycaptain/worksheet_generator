"""
Small objects that pictures show, to count, to make a set, or to go with a story: their kinds,
their names for a question's wording ("How many trucks?"), and what stories they suit.
"""

from enum import StrEnum


class DrawnObject(StrEnum):
    """An object a picture can show. Values are stable identifiers for the API and storage."""

    AMERICAN_FOOTBALL = "american_football"  # oval, with laces
    ANT = "ant"
    APPLE = "apple"
    BAG = "bag"  # a shopping bag with a handle
    BALL = "ball"  # plain, with a curved stripe
    BALLOON = "balloon"
    BANANA = "banana"
    BASEBALL = "baseball"
    BASKETBALL = "basketball"
    BELL = "bell"  # a hand bell
    BIRD = "bird"
    BLOCK = "block"  # a cube
    BOOK = "book"
    BUS = "bus"
    BUTTON = "button"
    CANDY_BAR = "candy_bar"  # lying tilted, its wrapper torn open at one end
    CAR = "car"
    CAT = "cat"  # its face
    CHAIR = "chair"
    CHOCOLATE_BAR = "chocolate_bar"  # standing up, its wrapper torn open to show its squares
    COOKIE = "cookie"
    COUNTER = "counter"  # a plain circle
    CRAYON = "crayon"
    CUPCAKE = "cupcake"
    DOG = "dog"  # its face
    DRUM = "drum"  # with two drumsticks
    DUCK = "duck"
    FISH = "fish"
    FLOWER = "flower"
    FOOTBALL = "football"  # round, of pentagons and hexagons
    FROG = "frog"  # from the side, facing right
    GIFT = "gift"  # a present, with a ribbon and bow, wider than it's high
    GRANOLA_BAR = "granola_bar"
    GUITAR = "guitar"
    HARD_CANDY = "hard_candy"  # a wrapped sweet
    HOUSE = "house"
    JERSEY = "jersey"
    LEAF = "leaf"
    LOLLIPOP = "lollipop"
    MARACA = "maraca"
    MUSICAL_TRIANGLE = "musical_triangle"  # hung from a string, with its beater
    PENCIL = "pencil"
    PIZZA = "pizza"  # from above
    RABBIT = "rabbit"  # its face
    ROUND_CAKE = "round_cake"  # from the side, its top an oval
    SANDWICH = "sandwich"  # a square sandwich from above
    SNAIL = "snail"  # from the side, facing right
    SQUARE_CAKE = "square_cake"  # from above, with icing round its edge
    SQUARE_GIFT = "square_gift"  # a gift as high as it's wide
    STAR = "star"
    TALL_GIFT = "tall_gift"  # a gift higher than it's wide
    TAMBOURINE = "tambourine"
    TEDDY_BEAR = "teddy_bear"
    TENT = "tent"
    TREE = "tree"
    TROPHY = "trophy"
    TRUCK = "truck"
    TURTLE = "turtle"
    XYLOPHONE = "xylophone"  # with a mallet


# Each object's name, singular and plural
OBJECT_NAMES: dict[DrawnObject, tuple[str, str]] = {
    DrawnObject.AMERICAN_FOOTBALL: ("American football", "American footballs"),
    DrawnObject.ANT: ("ant", "ants"),
    DrawnObject.APPLE: ("apple", "apples"),
    DrawnObject.BAG: ("bag", "bags"),
    DrawnObject.BALL: ("ball", "balls"),
    DrawnObject.BALLOON: ("balloon", "balloons"),
    DrawnObject.BANANA: ("banana", "bananas"),
    DrawnObject.BASEBALL: ("baseball", "baseballs"),
    DrawnObject.BASKETBALL: ("basketball", "basketballs"),
    DrawnObject.BELL: ("bell", "bells"),
    DrawnObject.BIRD: ("bird", "birds"),
    DrawnObject.BLOCK: ("block", "blocks"),
    DrawnObject.BOOK: ("book", "books"),
    DrawnObject.BUS: ("bus", "buses"),
    DrawnObject.BUTTON: ("button", "buttons"),
    DrawnObject.CANDY_BAR: ("candy bar", "candy bars"),
    DrawnObject.CAR: ("car", "cars"),
    DrawnObject.CAT: ("cat", "cats"),
    DrawnObject.CHAIR: ("chair", "chairs"),
    DrawnObject.CHOCOLATE_BAR: ("chocolate bar", "chocolate bars"),
    DrawnObject.COOKIE: ("cookie", "cookies"),
    DrawnObject.COUNTER: ("counter", "counters"),
    DrawnObject.CRAYON: ("crayon", "crayons"),
    DrawnObject.CUPCAKE: ("cupcake", "cupcakes"),
    DrawnObject.DOG: ("dog", "dogs"),
    DrawnObject.DRUM: ("drum", "drums"),
    DrawnObject.DUCK: ("duck", "ducks"),
    DrawnObject.FISH: ("fish", "fish"),
    DrawnObject.FLOWER: ("flower", "flowers"),
    DrawnObject.FOOTBALL: ("football", "footballs"),
    DrawnObject.FROG: ("frog", "frogs"),
    DrawnObject.GIFT: ("gift", "gifts"),
    DrawnObject.GRANOLA_BAR: ("granola bar", "granola bars"),
    DrawnObject.GUITAR: ("guitar", "guitars"),
    DrawnObject.HARD_CANDY: ("hard candy", "hard candies"),
    DrawnObject.HOUSE: ("house", "houses"),
    DrawnObject.JERSEY: ("jersey", "jerseys"),
    DrawnObject.LEAF: ("leaf", "leaves"),
    DrawnObject.LOLLIPOP: ("lollipop", "lollipops"),
    DrawnObject.MARACA: ("maraca", "maracas"),
    DrawnObject.MUSICAL_TRIANGLE: ("triangle", "triangles"),
    DrawnObject.PENCIL: ("pencil", "pencils"),
    DrawnObject.PIZZA: ("pizza", "pizzas"),
    DrawnObject.RABBIT: ("rabbit", "rabbits"),
    DrawnObject.ROUND_CAKE: ("cake", "cakes"),
    DrawnObject.SANDWICH: ("sandwich", "sandwiches"),
    DrawnObject.SNAIL: ("snail", "snails"),
    DrawnObject.SQUARE_CAKE: ("cake", "cakes"),
    DrawnObject.SQUARE_GIFT: ("gift", "gifts"),
    DrawnObject.STAR: ("star", "stars"),
    DrawnObject.TALL_GIFT: ("gift", "gifts"),
    DrawnObject.TAMBOURINE: ("tambourine", "tambourines"),
    DrawnObject.TEDDY_BEAR: ("teddy bear", "teddy bears"),
    DrawnObject.TENT: ("tent", "tents"),
    DrawnObject.TREE: ("tree", "trees"),
    DrawnObject.TROPHY: ("trophy", "trophies"),
    DrawnObject.TRUCK: ("truck", "trucks"),
    DrawnObject.TURTLE: ("turtle", "turtles"),
    DrawnObject.XYLOPHONE: ("xylophone", "xylophones"),
}

# Other names some objects go by, singular and plural, for a story to use instead
OTHER_NAMES: dict[DrawnObject, tuple[tuple[str, str], ...]] = {
    DrawnObject.HARD_CANDY: (("lolly", "lollies"),),
}


class ObjectUse(StrEnum):
    """What a story can do with an object. Values are stable identifiers for the API and
    storage."""

    SHARING = "sharing"  # a group of them shared out among people
    CUTTING = "cutting"  # one of them cut into equal parts and shared


# What each object suits, for objects that stories use: houses and animals aren't shared out
OBJECT_USES: dict[DrawnObject, frozenset[ObjectUse]] = {
    DrawnObject.APPLE: frozenset({ObjectUse.SHARING}),
    DrawnObject.BALL: frozenset({ObjectUse.SHARING}),
    DrawnObject.BALLOON: frozenset({ObjectUse.SHARING}),
    DrawnObject.BANANA: frozenset({ObjectUse.SHARING}),
    DrawnObject.BASEBALL: frozenset({ObjectUse.SHARING}),
    DrawnObject.BASKETBALL: frozenset({ObjectUse.SHARING}),
    DrawnObject.BLOCK: frozenset({ObjectUse.SHARING}),
    DrawnObject.BOOK: frozenset({ObjectUse.SHARING}),
    DrawnObject.BUTTON: frozenset({ObjectUse.SHARING}),
    DrawnObject.CANDY_BAR: frozenset({ObjectUse.SHARING}),
    DrawnObject.CHOCOLATE_BAR: frozenset({ObjectUse.SHARING, ObjectUse.CUTTING}),
    DrawnObject.COOKIE: frozenset({ObjectUse.SHARING}),
    DrawnObject.CRAYON: frozenset({ObjectUse.SHARING}),
    DrawnObject.CUPCAKE: frozenset({ObjectUse.SHARING}),
    DrawnObject.FOOTBALL: frozenset({ObjectUse.SHARING}),
    DrawnObject.GIFT: frozenset({ObjectUse.SHARING}),
    DrawnObject.GRANOLA_BAR: frozenset({ObjectUse.SHARING}),
    DrawnObject.HARD_CANDY: frozenset({ObjectUse.SHARING}),
    DrawnObject.LOLLIPOP: frozenset({ObjectUse.SHARING}),
    DrawnObject.PENCIL: frozenset({ObjectUse.SHARING}),
    DrawnObject.PIZZA: frozenset({ObjectUse.CUTTING}),
    DrawnObject.ROUND_CAKE: frozenset({ObjectUse.CUTTING}),
    DrawnObject.SANDWICH: frozenset({ObjectUse.CUTTING}),
    DrawnObject.SQUARE_CAKE: frozenset({ObjectUse.CUTTING}),
    DrawnObject.TEDDY_BEAR: frozenset({ObjectUse.SHARING}),
    DrawnObject.TROPHY: frozenset({ObjectUse.SHARING}),
}


def objects_for(use: ObjectUse) -> tuple[DrawnObject, ...]:
    """Return the objects that suit ``use``, in the order of ``DrawnObject``."""
    return tuple(kind for kind in DrawnObject if use in OBJECT_USES.get(kind, frozenset()))
