"""
The distance stories fractions on a number line questions tell: someone, or something of
theirs, going a distance in a straight line from a start, such as "Javier rode a bike 3/4 mile
from home."

New stories go at the top of the bank. Tests script ``random`` to take stories from the end of
the bank, so their wording stays the same.
"""

from dataclasses import dataclass

from core.drawn_objects import DrawnObject
from core.fraction_models.number_lines import LengthUnit

INCH, FOOT, YARD, MILE, CENTIMETER, METER, KILOMETER = LengthUnit


@dataclass(frozen=True)
class DistanceStory:
    """
    A story of a distance gone from a start. The one going is a person, by name, or with
    ``thing``, something of the person's: "frog" in "Ana's frog". They ``went`` the distance,
    "rode a bike", and in a second clause ``went_again``, "rode", or ``went`` again if that's
    not given; a question asks how far they ``go``, "ride". ``origin`` is where from, "from
    home", or empty; ``stopped`` is what they did at the end, "stopped" or "landed"; ``scene``
    opens the first sentence, "At camp, ", or is empty.

    ``units`` are the units the distance fits. ``mover`` is drawn over the point, or is
    ``None`` when there's no drawing of it, as for a person; ``start`` is drawn at 0, or is
    ``None``.
    """

    went: str
    go: str
    origin: str
    units: tuple[LengthUnit, ...]
    start: DrawnObject | None = None
    thing: str | None = None
    mover: DrawnObject | None = None
    went_again: str | None = None
    stopped: str = "stopped"
    scene: str = ""


DISTANCE_STORIES = (
    DistanceStory(
        "walked",
        "walk",
        "from the house",
        (YARD, METER),
        DrawnObject.HOUSE,
        "cat",
        DrawnObject.CAT,
    ),
    DistanceStory("rolled", "roll", "", (FOOT, YARD, METER), thing="ball", mover=DrawnObject.BALL),
    DistanceStory(
        "rolled",
        "roll",
        "",
        (INCH, FOOT, CENTIMETER, METER),
        thing="toy car",
        mover=DrawnObject.CAR,
    ),
    DistanceStory("flew", "fly", "", (FOOT, YARD, METER), thing="paper airplane", stopped="landed"),
    DistanceStory("swam", "swim", "from the shore", (MILE, KILOMETER)),
    DistanceStory("swam", "swim", "", (YARD, METER), thing="duck", mover=DrawnObject.DUCK),
    DistanceStory(
        "hopped", "hop", "", (FOOT, YARD, METER), thing="rabbit", mover=DrawnObject.RABBIT
    ),
    DistanceStory(
        "ran", "run", "from the house", (YARD, METER), DrawnObject.HOUSE, "dog", DrawnObject.DOG
    ),
    DistanceStory(
        "walked",
        "walk",
        "from the tree",
        (FOOT, YARD, METER),
        DrawnObject.TREE,
        "turtle",
        DrawnObject.TURTLE,
    ),
    DistanceStory(
        "jumped", "jump", "", (FOOT, METER), thing="frog", mover=DrawnObject.FROG, stopped="landed"
    ),
    DistanceStory(
        "crawled",
        "crawl",
        "from its leaf",
        (INCH, FOOT, CENTIMETER),
        DrawnObject.LEAF,
        "snail",
        DrawnObject.SNAIL,
    ),
    DistanceStory(
        "crawled",
        "crawl",
        "from its house",
        (INCH, FOOT, YARD, CENTIMETER, METER),
        DrawnObject.HOUSE,
        "ant",
        DrawnObject.ANT,
    ),
    DistanceStory("ran", "run", "from the big tree", (MILE, KILOMETER), DrawnObject.TREE),
    DistanceStory(
        "hiked", "hike", "from the tent", (MILE, KILOMETER), DrawnObject.TENT, scene="At camp, "
    ),
    DistanceStory(
        "walked", "walk", "from the car", (MILE, KILOMETER), DrawnObject.CAR, scene="At the park, "
    ),
    DistanceStory(
        "walked",
        "walk",
        "from the bus",
        (MILE, KILOMETER),
        DrawnObject.BUS,
        scene="On a field trip, ",
    ),
    DistanceStory(
        "rode a bike", "ride", "from home", (MILE, KILOMETER), DrawnObject.HOUSE, went_again="rode"
    ),
)
