"""
Tests for the drawn objects, each drawn on its own: plain, and some filled in or numbered.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/objects_pdf_expecteds.txt``. To regenerate sections after an intended change, uncomment
the ``write_section`` lines in ``test_object_draws_the_expected_text`` and run it.
"""

from io import BytesIO

import pytest
from reportlab.lib.colors import Color
from reportlab.pdfgen.canvas import Canvas

from core.drawn_objects import DrawnObject
from render.pdf.graphics.fractions import COLOUR_FRACTIONS, GREY_FRACTIONS
from render.pdf.graphics.objects import draw_object
from tests.helpers import GOLDENS, pdf_text, read_sections

EXPECTED = GOLDENS / "objects_pdf_expecteds.txt"
BLUE, GREY = COLOUR_FRACTIONS.shaded, GREY_FRACTIONS.shaded


@pytest.mark.parametrize(
    ("case_name", "kind", "number", "fill"),
    [
        ("american_football", DrawnObject.AMERICAN_FOOTBALL, None, None),
        ("ant", DrawnObject.ANT, None, None),
        ("apple", DrawnObject.APPLE, None, None),
        ("bag", DrawnObject.BAG, None, None),
        ("ball", DrawnObject.BALL, None, None),
        ("balloon", DrawnObject.BALLOON, None, None),
        ("banana", DrawnObject.BANANA, None, None),
        ("baseball", DrawnObject.BASEBALL, None, None),
        ("basketball", DrawnObject.BASKETBALL, None, None),
        ("bell", DrawnObject.BELL, None, None),
        ("bird", DrawnObject.BIRD, None, None),
        ("block", DrawnObject.BLOCK, None, None),
        ("book", DrawnObject.BOOK, None, None),
        ("bus", DrawnObject.BUS, None, None),
        ("button", DrawnObject.BUTTON, None, None),
        ("candy_bar", DrawnObject.CANDY_BAR, None, None),
        ("car", DrawnObject.CAR, None, None),
        ("cat", DrawnObject.CAT, None, None),
        ("chair", DrawnObject.CHAIR, None, None),
        ("chocolate_bar", DrawnObject.CHOCOLATE_BAR, None, None),
        ("cookie", DrawnObject.COOKIE, None, None),
        ("counter", DrawnObject.COUNTER, None, None),
        ("crayon", DrawnObject.CRAYON, None, None),
        ("cupcake", DrawnObject.CUPCAKE, None, None),
        ("dog", DrawnObject.DOG, None, None),
        ("drum", DrawnObject.DRUM, None, None),
        ("duck", DrawnObject.DUCK, None, None),
        ("fish", DrawnObject.FISH, None, None),
        ("flower", DrawnObject.FLOWER, None, None),
        ("football", DrawnObject.FOOTBALL, None, None),
        ("gift", DrawnObject.GIFT, None, None),
        ("granola_bar", DrawnObject.GRANOLA_BAR, None, None),
        ("guitar", DrawnObject.GUITAR, None, None),
        ("hard_candy", DrawnObject.HARD_CANDY, None, None),
        ("house", DrawnObject.HOUSE, None, None),
        ("jersey", DrawnObject.JERSEY, None, None),
        ("leaf", DrawnObject.LEAF, None, None),
        ("lollipop", DrawnObject.LOLLIPOP, None, None),
        ("maraca", DrawnObject.MARACA, None, None),
        ("musical_triangle", DrawnObject.MUSICAL_TRIANGLE, None, None),
        ("pencil", DrawnObject.PENCIL, None, None),
        ("rabbit", DrawnObject.RABBIT, None, None),
        ("square_gift", DrawnObject.SQUARE_GIFT, None, None),
        ("star", DrawnObject.STAR, None, None),
        ("tall_gift", DrawnObject.TALL_GIFT, None, None),
        ("tambourine", DrawnObject.TAMBOURINE, None, None),
        ("teddy_bear", DrawnObject.TEDDY_BEAR, None, None),
        ("tent", DrawnObject.TENT, None, None),
        ("tree", DrawnObject.TREE, None, None),
        ("trophy", DrawnObject.TROPHY, None, None),
        ("truck", DrawnObject.TRUCK, None, None),
        ("turtle", DrawnObject.TURTLE, None, None),
        ("xylophone", DrawnObject.XYLOPHONE, None, None),
        # filled in; the eyes, wheels and details stay dark
        ("cat_filled", DrawnObject.CAT, None, BLUE),
        ("truck_filled_grey", DrawnObject.TRUCK, None, GREY),
        # numbered: where each kind's number goes, shrunk to fit; a basketball's in the middle
        ("jersey_numbered", DrawnObject.JERSEY, 52, None),
        ("house_numbered_filled", DrawnObject.HOUSE, 4137, BLUE),
        ("basketball_numbered", DrawnObject.BASKETBALL, 7, None),
        ("candy_bar_numbered_filled", DrawnObject.CANDY_BAR, 3, BLUE),
        ("xylophone_filled_grey", DrawnObject.XYLOPHONE, None, GREY),
    ],
)
def test_object_draws_the_expected_text(
    case_name: str, kind: DrawnObject, number: int | None, fill: Color | None
) -> None:
    """The decoded PDF matches this case's section of ``objects_pdf_expecteds.txt``."""
    out = BytesIO()
    pdf = Canvas(out)
    draw_object(pdf, kind, 100, 700, 40, number=number, fill=fill)
    pdf.save()

    actual = pdf_text(out.getvalue())

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)
