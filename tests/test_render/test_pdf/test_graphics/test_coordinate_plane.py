"""
Tests for the coordinate grid drawing, on its own: the grid, and what is plotted on it, among
them the segments and rays with open or closed ends that the domain and range sheet will plot.

Each case's output is stored as text decoded from the PDF, in one file with a section per case:
``goldens/coordinate_plane_pdf_expecteds.txt``. To regenerate sections after an intended
change, uncomment the ``write_section`` lines in ``test_pdf_draws_the_expected_text`` and run it.
"""

from collections.abc import Callable
from io import BytesIO

import pytest
from reportlab.pdfgen.canvas import Canvas

from render.pdf.graphics.coordinate_plane import (
    Plane,
    draw_coordinate_plane,
    draw_line,
    draw_point,
    draw_ray,
    draw_segment,
    plane_height,
)
from tests.helpers import GOLDENS, pdf_text, read_sections

EXPECTED = GOLDENS / "coordinate_plane_pdf_expecteds.txt"


def _segments_and_rays(pdf: Canvas, plane: Plane) -> None:
    """A segment closed at both ends, one open at its end, a ray from an open end, and one from
    a closed end."""
    draw_segment(pdf, plane, (-4, -3), (-1, 2))
    draw_segment(pdf, plane, (0, -4), (3, -4), end_closed=False)
    draw_ray(pdf, plane, (1, 1), (2, 3), closed=False)
    draw_ray(pdf, plane, (-2, 4), (-4, 4))


def _line_and_points(pdf: Canvas, plane: Plane) -> None:
    """A line across the grid, and two points on it, one labelled."""
    draw_line(pdf, plane, 1, 2, 2)
    draw_point(pdf, plane, (2, 0), "(2, 0)", (1, 2))
    draw_point(pdf, plane, (-2, 2))


@pytest.mark.parametrize(
    ("case_name", "largest_x", "largest_y", "step", "plot"),
    [
        ("segments_and_rays", 5, 5, 1, _segments_and_rays),
        ("line_and_points", 5, 3, 1, _line_and_points),
        # every second number fits at 20, counting by 2
        ("counting_by_2", 20, 10, 2, _line_and_points),
    ],
)
def test_pdf_draws_the_expected_text(
    case_name: str,
    largest_x: int,
    largest_y: int,
    step: int,
    plot: Callable[[Canvas, Plane], None],
) -> None:
    """The decoded PDF matches this case's section of ``coordinate_plane_pdf_expecteds.txt``."""
    out = BytesIO()
    pdf = Canvas(out)
    plane = draw_coordinate_plane(pdf, 100, 700, 200, largest_x, largest_y, step)
    plot(pdf, plane)
    pdf.save()

    actual = pdf_text(out.getvalue())

    # to regenerate, uncomment:
    # from tests.helpers import write_section
    # write_section(EXPECTED, case_name, actual)
    assert actual == read_sections(EXPECTED).get(case_name)


@pytest.mark.parametrize(
    ("width", "largest_x", "largest_y", "height"),
    [(200, 10, 10, 200), (200, 10, 5, 100), (200, 20, 6, 60)],
)
def test_plane_height(width: float, largest_x: int, largest_y: int, height: float) -> None:
    """One square per unit both ways, so the height follows the y-range."""
    assert plane_height(width, largest_x, largest_y) == height


def test_plane_puts_points_on_the_page() -> None:
    """The origin is the grid's middle, and each unit is the width over the x-range."""
    plane = Plane(left=100, bottom=500, unit=10, largest_x=10, largest_y=5)
    assert (plane.at(0, 0), plane.at(-10, -5), plane.at(10, 5)) == (
        (200, 550),
        (100, 500),
        (300, 600),
    )
