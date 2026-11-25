"""
Tests for the fraction pictures: area models, models in a row, groups of objects, number lines and
fraction walls, each drawn on its own.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/fractions_pdf_expecteds.txt``. To regenerate sections after an intended change,
uncomment the ``write_section`` lines in the tests and run them.
"""

from collections.abc import Callable, Sequence
from fractions import Fraction
from io import BytesIO

import pytest
from reportlab.pdfgen.canvas import Canvas

from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    EQUILATERAL_TRIANGLE,
    HALF_HEXAGON,
    REGULAR_HEXAGON,
    RHOMBUS,
    AreaModel,
    Circle,
    ConcaveOctagon,
    CutShape,
    FractionWall,
    Grid,
    RadialPartition,
    Rectangle,
    RegularPolygon,
    SlicedCircle,
    Strip,
    TriangleGrid,
    equal_sizes,
    lattice_triangles,
    quartered_by_diagonals,
    rectangle,
    striped,
    tiled,
    uneven_sizes,
)
from core.fraction_models.number_lines import (
    FractionLine,
    LengthUnit,
    LinePoint,
    Mark,
    TickLabels,
)
from core.fraction_models.object_groups import ObjectGroup
from render.pdf.graphics.fractions import (
    COLOUR_FRACTIONS,
    GREY_FRACTIONS,
    FractionColours,
    draw_area_model,
    draw_fraction_line,
    draw_fraction_wall,
    draw_models_in_a_row,
    draw_object_group,
    fraction_line_height,
    fraction_wall_height,
    row_height,
)
from tests.helpers import GOLDENS, pdf_text, read_sections

EXPECTED = GOLDENS / "fractions_pdf_expecteds.txt"
HALF = Fraction(1, 2)
# a rectangle of two squares, one over the other, cut corner to corner and between the squares
TWO_SQUARES = CutShape(
    rectangle(1, 2),
    (
        ((0, 0), (HALF, 1), (0, 1)),
        ((0, 0), (1, 0), (1, 1), (HALF, 1)),
        ((0, 1), (HALF, 1), (1, 2), (0, 2)),
        ((HALF, 1), (1, 1), (1, 2)),
    ),
)


def _drawn(draw: Callable[[Canvas], None]) -> str:
    """Return the decoded PDF of one page with ``draw`` drawn on it."""
    out = BytesIO()
    pdf = Canvas(out)
    draw(pdf)
    pdf.save()
    return pdf_text(out.getvalue())


@pytest.mark.parametrize(
    ("case_name", "model", "width", "height", "colours"),
    [
        (
            "strip_fourths",
            AreaModel(Strip(equal_sizes(4)), frozenset({0, 1, 2})),
            200,
            30,
            COLOUR_FRACTIONS,
        ),
        (
            "strip_uneven_one_left_out",
            AreaModel(Strip(uneven_sizes(3)), frozenset({0}), frozenset({2})),
            200,
            30,
            GREY_FRACTIONS,
        ),
        (
            "grid_2_by_4_one_left_out",
            AreaModel(Grid(2, 4), frozenset({0, 1}), frozenset({7})),
            160,
            80,
            COLOUR_FRACTIONS,
        ),
        (
            "circle_uncut",
            AreaModel(RadialPartition(Circle(), equal_sizes(1)), frozenset({0})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "circle_eighths_one_left_out",
            AreaModel(
                RadialPartition(Circle(), equal_sizes(8)), frozenset({0, 1, 2}), frozenset({7})
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "square_uncut",
            AreaModel(RadialPartition(RegularPolygon(4), equal_sizes(1))),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # cut from the middle of the top: 4 small squares
        (
            "square_four_squares",
            AreaModel(
                RadialPartition(RegularPolygon(4), equal_sizes(4), Fraction(1, 8)),
                frozenset({1, 3}),
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "four_pointed_star_eighths",
            AreaModel(
                RadialPartition(ConcaveOctagon(), equal_sizes(8)), frozenset({0, 2, 3, 4, 6, 7})
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # 4 of the hexagon's 6 triangles, where they'd be in the whole
        (
            "hexagon_four_of_six",
            AreaModel(
                RadialPartition(RegularPolygon(6, on_corner=True), equal_sizes(6)),
                frozenset({2}),
                frozenset({4, 5}),
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "triangle_sixths",
            AreaModel(RadialPartition(RegularPolygon(3), equal_sizes(6)), frozenset({0})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "pentagon_tenths",
            AreaModel(RadialPartition(RegularPolygon(5), equal_sizes(10)), frozenset({0, 3})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # cut to its sides' middles, flat at the top
        (
            "octagon_apothems",
            AreaModel(
                RadialPartition(RegularPolygon(8), equal_sizes(8), Fraction(1, 16)),
                frozenset({0, 2}),
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "square_on_corner",
            AreaModel(RadialPartition(RegularPolygon(4, on_corner=True), equal_sizes(4))),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # upside down, cut to its sides' middles into 3 kites
        (
            "triangle_on_corner_kites",
            AreaModel(
                RadialPartition(RegularPolygon(3, on_corner=True), equal_sizes(3), Fraction(1, 6)),
                frozenset({0}),
            ),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # fills its box, one part left out
        (
            "rectangle_eighths",
            AreaModel(RadialPartition(Rectangle(), equal_sizes(8)), frozenset({0}), frozenset({5})),
            160,
            80,
            COLOUR_FRACTIONS,
        ),
        (
            "concave_octagon_sharp",
            AreaModel(
                RadialPartition(ConcaveOctagon(Fraction(1, 4)), equal_sizes(4), Fraction(1, 8)),
                frozenset({1}),
            ),
            100,
            100,
            GREY_FRACTIONS,
        ),
        (
            "sliced_circle_down",
            AreaModel(SlicedCircle(4), frozenset({0})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "sliced_circle_across_one_left_out",
            AreaModel(SlicedCircle(4, horizontal=True), frozenset({3}), frozenset({0})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "triangle_grid_one_left_out",
            AreaModel(TriangleGrid(2), frozenset({0}), frozenset({2})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "cut_rectangle_one_left_out",
            AreaModel(tiled(TWO_SQUARES, 2, 1), frozenset({0}), frozenset({7})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # on the triangle lattice
        (
            "rhombus_quartered",
            AreaModel(quartered_by_diagonals(RHOMBUS), frozenset({0})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "half_hexagon_triangles_one_left_out",
            AreaModel(lattice_triangles(HALF_HEXAGON), frozenset({1}), frozenset({2})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "triangle_striped",
            AreaModel(striped(EQUILATERAL_TRIANGLE, 3, 1), frozenset({2})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        (
            "hexagon_striped",
            AreaModel(striped(REGULAR_HEXAGON, 3), frozenset({1})),
            100,
            100,
            COLOUR_FRACTIONS,
        ),
        # wholes drawn as objects: a pepperoni on each slice, and the crust
        (
            "pizza_in_6_two_shaded",
            AreaModel(
                RadialPartition(Circle(), equal_sizes(6)), frozenset({0, 1}), look=DrawnObject.PIZZA
            ),
            120,
            120,
            COLOUR_FRACTIONS,
        ),
        (
            "pizza_uncut",
            AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.PIZZA),
            120,
            120,
            COLOUR_FRACTIONS,
        ),
        (
            # too many slices for pepperoni
            "pizza_in_16",
            AreaModel(RadialPartition(Circle(), equal_sizes(16)), look=DrawnObject.PIZZA),
            120,
            120,
            GREY_FRACTIONS,
        ),
        (
            "sandwich_in_4_squares",
            AreaModel(
                RadialPartition(RegularPolygon(4), equal_sizes(4), Fraction(1, 8)),
                look=DrawnObject.SANDWICH,
            ),
            110,
            110,
            COLOUR_FRACTIONS,
        ),
        (
            "square_cake_3_by_3",
            AreaModel(Grid(3, 3), look=DrawnObject.SQUARE_CAKE),
            110,
            110,
            COLOUR_FRACTIONS,
        ),
        (
            # a square left out has no square drawn in it
            "chocolate_bar_2_by_4_one_left_out",
            AreaModel(Grid(2, 4), frozenset({0}), frozenset({7}), look=DrawnObject.CHOCOLATE_BAR),
            200,
            80,
            COLOUR_FRACTIONS,
        ),
        (
            "chocolate_bar_wrapped",
            AreaModel(Grid(1, 1), look=DrawnObject.CHOCOLATE_BAR),
            200,
            64,
            COLOUR_FRACTIONS,
        ),
        (
            # in the middle of a box wider than it needs
            "round_cake",
            AreaModel(RadialPartition(Circle(), equal_sizes(1)), look=DrawnObject.ROUND_CAKE),
            200,
            91,
            COLOUR_FRACTIONS,
        ),
    ],
)
def test_area_model_draws_the_expected_text(
    case_name: str,
    model: AreaModel,
    width: float,
    height: float,
    colours: FractionColours,
) -> None:
    """The decoded PDF matches this case's section of ``fractions_pdf_expecteds.txt``."""
    actual = _drawn(lambda pdf: draw_area_model(pdf, 100, 700, model, width, height, colours))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("case_name", "models", "labels", "scales"),
    [
        (
            "row_labelled",
            [
                AreaModel(Strip(uneven_sizes(5)), frozenset({0})),
                AreaModel(Strip(equal_sizes(5)), frozenset({0})),
            ],
            ["Model R", "Model T"],
            None,
        ),
        (
            "row_different_sizes",
            [
                AreaModel(RadialPartition(Circle(), equal_sizes(4)), frozenset({0})),
                AreaModel(RadialPartition(Circle(), equal_sizes(4)), frozenset({0})),
            ],
            None,
            [1, 0.6],
        ),
    ],
)
def test_models_in_a_row_draw_the_expected_text(
    case_name: str,
    models: Sequence[AreaModel],
    labels: Sequence[str] | None,
    scales: Sequence[float] | None,
) -> None:
    """The decoded PDF matches this case's section of ``fractions_pdf_expecteds.txt``."""
    actual = _drawn(
        lambda pdf: draw_models_in_a_row(
            pdf, 100, 700, 300, 80, models, COLOUR_FRACTIONS, labels, scales
        )
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("case_name", "group", "width", "height"),
    [
        (
            "baseballs_three_of_eight",
            ObjectGroup(DrawnObject.BASEBALL, 8, 4, frozenset({0, 1, 2})),
            200,
            90,
        ),
        # the last row is shorter
        (
            "stars_seven_in_rows_of_four",
            ObjectGroup(DrawnObject.STAR, 7, 4, frozenset({6})),
            200,
            90,
        ),
    ],
)
def test_object_group_draws_the_expected_text(
    case_name: str, group: ObjectGroup, width: float, height: float
) -> None:
    """The decoded PDF matches this case's section of ``fractions_pdf_expecteds.txt``."""
    actual = _drawn(
        lambda pdf: draw_object_group(pdf, 100, 700, group, width, height, COLOUR_FRACTIONS)
    )

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("case_name", "line", "width", "colours"),
    [
        ("sixths_dot", FractionLine(6, points=(LinePoint(5),)), 400, COLOUR_FRACTIONS),
        (
            "eighths_lettered",
            FractionLine(8, points=(LinePoint(1, "A"), LinePoint(3, "B"), LinePoint(6, "D"))),
            400,
            COLOUR_FRACTIONS,
        ),
        (
            "fourths_every_tick_star",
            FractionLine(4, labels=TickLabels.EVERY_TICK, points=(LinePoint(3, mark=Mark.STAR),)),
            400,
            COLOUR_FRACTIONS,
        ),
        (
            "eighths_arrow_yard",
            FractionLine(8, unit=LengthUnit.YARD, points=(LinePoint(2, "A"),), arrow_to=2),
            400,
            COLOUR_FRACTIONS,
        ),
        (
            "fourths_jumps_foot",
            FractionLine(4, unit=LengthUnit.FOOT, points=(LinePoint(2, "H"),), jumps=2),
            400,
            GREY_FRACTIONS,
        ),
        ("thirds_bar", FractionLine(3, bar_to=1), 400, COLOUR_FRACTIONS),
        # wholes past 1, every tick labelled, the unit plural
        (
            "halves_two_wholes_miles",
            FractionLine(2, wholes=2, labels=TickLabels.EVERY_TICK, unit=LengthUnit.MILE),
            400,
            COLOUR_FRACTIONS,
        ),
        # one part: every tick is a whole
        ("empty_line", FractionLine(1, labels=TickLabels.EVERY_TICK), 200, COLOUR_FRACTIONS),
        # labels shrink to fit between close ticks
        (
            "twelfths_every_tick_narrow",
            FractionLine(12, labels=TickLabels.EVERY_TICK),
            200,
            COLOUR_FRACTIONS,
        ),
    ],
)
def test_fraction_line_draws_the_expected_text(
    case_name: str, line: FractionLine, width: float, colours: FractionColours
) -> None:
    """The decoded PDF matches this case's section of ``fractions_pdf_expecteds.txt``."""
    actual = _drawn(lambda pdf: draw_fraction_line(pdf, 100, 700, line, width, colours))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("case_name", "wall", "width"),
    [
        ("wall_labelled", FractionWall((1, 2, 3, 4, 6, 8)), 400),
        ("wall_unlabelled", FractionWall((1, 2, 4), labelled=False), 400),
        # the labels shrink to fit narrow parts
        ("wall_twelfths_narrow", FractionWall((1, 12)), 150),
    ],
)
def test_fraction_wall_draws_the_expected_text(
    case_name: str, wall: FractionWall, width: float
) -> None:
    """The decoded PDF matches this case's section of ``fractions_pdf_expecteds.txt``."""
    actual = _drawn(lambda pdf: draw_fraction_wall(pdf, 100, 700, wall, width))

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("line", "height"),
    [
        # stars' room above, whole numbers' below
        (FractionLine(4), 26.5),
        (FractionLine(4, points=(LinePoint(1, "A"),)), 41.5),
        (FractionLine(4, arrow_to=1), 35),
        # jumps and a letter above, fractions below
        (FractionLine(4, labels=TickLabels.EVERY_TICK, points=(LinePoint(2, "H"),), jumps=2), 59),
    ],
)
def test_fraction_line_height(line: FractionLine, height: float) -> None:
    """A line's picture has room for what's above the line and the numbers under it."""
    assert fraction_line_height(line) == height


def test_fraction_wall_and_row_heights() -> None:
    """A wall is a row for each denominator; a row of models has room for labels if it has them."""
    heights = (
        fraction_wall_height(FractionWall((1, 2, 4))),
        row_height(70, True),
        row_height(70, False),
    )
    assert heights == (72, 88, 70)
