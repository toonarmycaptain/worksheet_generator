"""
Small objects that pictures show, to count, to make a set, or to go with a story: their kinds,
and their names for a question's wording ("How many trucks?").
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
    RABBIT = "rabbit"  # its face
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
    DrawnObject.RABBIT: ("rabbit", "rabbits"),
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
