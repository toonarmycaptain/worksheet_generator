"""
Small objects that pictures share, to count, to make a set, or to go with a story, each drawn
in code as an outline in a square.
"""

from collections.abc import Callable
from math import cos, hypot, pi, sin

from reportlab.lib.colors import Color, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from core.drawn_objects import DrawnObject
from render.pdf.graphics.common import OUTLINE_COLOUR, Point, draw_cake_from_the_side, draw_polygon
from render.pdf.page import BOLD_FONT

OBJECT_LINE_WIDTH = 1
# Objects drawn facing left, which a picture of something going right draws mirrored
FACING_LEFT = frozenset({DrawnObject.ANT, DrawnObject.FISH})
# Where an object's number goes, in a square of side 1 from its bottom-left corner: the middle of
# the number, and the most its digits' height and width can take. Objects not listed take the
# square's middle.
_NUMBER_SPOT = (0.5, 0.5, 0.3, 0.5)
_NUMBER_SPOTS: dict[DrawnObject, tuple[float, float, float, float]] = {
    DrawnObject.ANT: (0.73, 0.5, 0.16, 0.26),
    DrawnObject.APPLE: (0.5, 0.42, 0.3, 0.5),
    DrawnObject.BAG: (0.5, 0.36, 0.3, 0.5),
    DrawnObject.BALLOON: (0.5, 0.64, 0.26, 0.4),
    DrawnObject.BANANA: (0.5, 0.27, 0.09, 0.14),
    DrawnObject.BASEBALL: (0.5, 0.5, 0.3, 0.3),
    DrawnObject.BELL: (0.5, 0.44, 0.2, 0.3),
    DrawnObject.BIRD: (0.46, 0.44, 0.16, 0.26),
    DrawnObject.BLOCK: (0.39, 0.39, 0.36, 0.5),
    DrawnObject.BOOK: (0.57, 0.4, 0.3, 0.44),
    DrawnObject.BUS: (0.5, 0.33, 0.14, 0.4),
    DrawnObject.CANDY_BAR: (0.58, 0.54, 0.08, 0.16),
    DrawnObject.CAR: (0.51, 0.585, 0.16, 0.3),
    DrawnObject.CAT: (0.5, 0.17, 0.1, 0.24),
    DrawnObject.CHAIR: (0.24, 0.72, 0.1, 0.07),
    DrawnObject.COUNTER: (0.5, 0.5, 0.36, 0.56),
    DrawnObject.CUPCAKE: (0.5, 0.25, 0.18, 0.4),
    DrawnObject.DOG: (0.5, 0.7, 0.12, 0.22),
    DrawnObject.DRUM: (0.5, 0.4, 0.14, 0.24),
    DrawnObject.DUCK: (0.45, 0.35, 0.08, 0.16),
    DrawnObject.FISH: (0.5, 0.5, 0.24, 0.3),
    DrawnObject.FLOWER: (0.5, 0.68, 0.12, 0.15),
    DrawnObject.FROG: (0.52, 0.44, 0.1, 0.16),
    DrawnObject.GIFT: (0.28, 0.34, 0.24, 0.22),
    DrawnObject.GRANOLA_BAR: (0.5, 0.5, 0.15, 0.32),
    DrawnObject.GUITAR: (0.27, 0.37, 0.1, 0.14),
    DrawnObject.HOUSE: (0.5, 0.42, 0.17, 0.5),
    DrawnObject.JERSEY: (0.5, 0.36, 0.3, 0.46),
    DrawnObject.MARACA: (0.34, 0.4, 0.12, 0.16),
    DrawnObject.MUSICAL_TRIANGLE: (0.42, 0.42, 0.14, 0.2),
    DrawnObject.RABBIT: (0.5, 0.17, 0.09, 0.2),
    DrawnObject.SNAIL: (0.4, 0.46, 0.14, 0.22),
    DrawnObject.SQUARE_GIFT: (0.33, 0.34, 0.2, 0.13),
    DrawnObject.STAR: (0.5, 0.45, 0.2, 0.22),
    DrawnObject.TALL_GIFT: (0.38, 0.34, 0.14, 0.07),
    DrawnObject.TENT: (0.5, 0.64, 0.12, 0.2),
    DrawnObject.TROPHY: (0.5, 0.72, 0.2, 0.36),
    DrawnObject.TRUCK: (0.33, 0.5, 0.26, 0.44),
    DrawnObject.TURTLE: (0.48, 0.5, 0.12, 0.2),
    DrawnObject.XYLOPHONE: (0.42, 0.52, 0.14, 0.24),
}


def draw_object(
    pdf: Canvas,
    kind: DrawnObject,
    x: float,
    top: float,
    size: float,
    number: int | None = None,
    fill: Color | None = None,
    mirrored: bool = False,
) -> None:
    """
    Draw an object of ``kind`` as an outline in a square ``size`` wide with its top-left corner at
    (``x``, ``top``), filled with ``fill``, or white, and with ``number`` written on it, if any.
    Small details, such as eyes and wheels, are always dark. With ``mirrored``, it's drawn
    flipped left to right, its number too, so a mirrored object takes no number.
    """
    pdf.saveState()
    if mirrored:
        pdf.translate(x + size, top - size)
        pdf.scale(-size, size)
    else:
        pdf.translate(x, top - size)
        pdf.scale(size, size)  # draw in a square of side 1
    pdf.setLineWidth(OBJECT_LINE_WIDTH / size)
    pdf.setLineJoin(1)  # round
    pdf.setLineCap(1)  # round
    pdf.setStrokeColor(OUTLINE_COLOUR)
    colour = white if fill is None else fill
    pdf.setFillColor(colour)
    _OBJECT_DRAWERS[kind](pdf, colour)
    if number is not None:
        middle_x, middle_y, height, width = _NUMBER_SPOTS.get(kind, _NUMBER_SPOT)
        text = f"{number:,}"
        font_size = min(height / 0.72, width / stringWidth(text, BOLD_FONT, 1))  # 0.72: a digit
        pdf.setFillColor("black")
        pdf.setFont(BOLD_FONT, font_size)
        pdf.drawCentredString(middle_x, middle_y - font_size * 0.36, text)
    pdf.restoreState()


def _draw_curve(
    pdf: Canvas, start: tuple[float, float], *curves: tuple[float, ...], closed: bool = False
) -> None:
    """
    Draw a path from ``start`` through ``curves``, each a cubic Bézier curve's two control points
    and end, six numbers; filled and closed if ``closed``, else an open line.
    """
    path = pdf.beginPath()
    path.moveTo(*start)
    for curve in curves:
        path.curveTo(*curve)
    if closed:
        path.close()
    pdf.drawPath(path, stroke=1, fill=int(closed))


def _draw_lines(pdf: Canvas, *lines: tuple[float, float, float, float]) -> None:
    """Draw each of ``lines``, from (x1, y1) to (x2, y2)."""
    pdf.lines(lines)


def _draw_dark(pdf: Canvas, *dots: tuple[float, float, float]) -> None:
    """Draw dark dots, each at (x, y) with a radius, such as eyes. Leaves the fill dark."""
    pdf.setFillColor(OUTLINE_COLOUR)
    for dot_x, dot_y, radius in dots:
        pdf.circle(dot_x, dot_y, radius, stroke=0, fill=1)


def _tilt(pdf: Canvas) -> None:
    """Turn the square of side 1 a twelfth of a turn anticlockwise round its middle, for a long
    object drawn lying flat."""
    pdf.translate(0.5, 0.5)
    pdf.rotate(30)
    pdf.translate(-0.5, -0.5)


def _draw_ant(pdf: Canvas, fill: Color) -> None:
    """Draw an ant seen from above, facing left: three legs and an antenna each side, then its
    head, middle and back."""
    for side in (1, -1):  # above the body, then below
        for hip, knee, foot in (
            ((0.42, 0.5), (0.34, 0.64), (0.24, 0.74)),
            ((0.44, 0.5), (0.45, 0.68), (0.44, 0.84)),
            ((0.46, 0.5), (0.56, 0.64), (0.66, 0.78)),
        ):
            leg = pdf.beginPath()
            leg.moveTo(hip[0], 0.5 + side * (hip[1] - 0.5))
            leg.lineTo(knee[0], 0.5 + side * (knee[1] - 0.5))
            leg.lineTo(foot[0], 0.5 + side * (foot[1] - 0.5))
            pdf.drawPath(leg, stroke=1, fill=0)
        _draw_lines(pdf, (0.18, 0.5 + side * 0.06, 0.06, 0.5 + side * 0.2))
    pdf.ellipse(0.52, 0.36, 0.94, 0.64, stroke=1, fill=1)
    pdf.ellipse(0.32, 0.42, 0.55, 0.58, stroke=1, fill=1)
    pdf.circle(0.22, 0.5, 0.09, stroke=1, fill=1)


def _draw_apple(pdf: Canvas, fill: Color) -> None:
    """Draw an apple: two rounded sides meeting in a dip at the top, a stem and a leaf."""
    _draw_curve(
        pdf,
        (0.5, 0.74),
        (0.62, 0.86, 0.92, 0.8, 0.9, 0.5),
        (0.88, 0.2, 0.7, 0.04, 0.5, 0.1),
        (0.3, 0.04, 0.12, 0.2, 0.1, 0.5),
        (0.08, 0.8, 0.38, 0.86, 0.5, 0.74),
        closed=True,
    )
    _draw_lines(pdf, (0.5, 0.74, 0.54, 0.94))
    _draw_curve(
        pdf,
        (0.54, 0.86),
        (0.6, 0.98, 0.72, 0.96, 0.78, 0.92),
        (0.7, 0.84, 0.6, 0.82, 0.54, 0.86),
        closed=True,
    )


def _draw_bag(pdf: Canvas, fill: Color) -> None:
    """Draw a shopping bag: a bag a little narrower at the top, and a handle."""
    _draw_curve(pdf, (0.36, 0.66), (0.36, 0.94, 0.64, 0.94, 0.64, 0.66))
    draw_polygon(pdf, [(0.16, 0.06), (0.84, 0.06), (0.8, 0.66), (0.2, 0.66)])


def _draw_balloon(pdf: Canvas, fill: Color) -> None:
    """Draw a balloon on a wavy string, with its knot."""
    _draw_curve(pdf, (0.5, 0.3), (0.42, 0.2, 0.58, 0.12, 0.5, 0.02))
    pdf.ellipse(0.24, 0.32, 0.76, 0.96, stroke=1, fill=1)
    draw_polygon(pdf, [(0.45, 0.27), (0.55, 0.27), (0.5, 0.33)])


def _draw_baseball(pdf: Canvas, fill: Color) -> None:
    """Draw a baseball: a circle with a curved seam on each side."""
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)
    for edge, inner in ((0.28, 0.42), (0.72, 0.58)):  # each seam bows in towards the middle
        _draw_curve(pdf, (edge, 0.881), (inner, 0.68, inner, 0.32, edge, 0.119))


def _draw_basketball(pdf: Canvas, fill: Color) -> None:
    """Draw a basketball: a circle with lines across and down it, and a curve each side."""
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)
    _draw_lines(pdf, (0.06, 0.5, 0.94, 0.5), (0.5, 0.06, 0.5, 0.94))
    for edge, inner in ((0.22, 0.36), (0.78, 0.64)):
        _draw_curve(pdf, (edge, 0.84), (inner, 0.66, inner, 0.34, edge, 0.16))


def _draw_bird(pdf: Canvas, fill: Color) -> None:
    """Draw a bird facing right: tail, legs, body, head, beak, wing and eye."""
    draw_polygon(pdf, [(0.26, 0.5), (0.04, 0.64), (0.08, 0.4)])
    _draw_lines(pdf, (0.42, 0.28, 0.4, 0.08), (0.52, 0.28, 0.54, 0.08))
    pdf.ellipse(0.18, 0.24, 0.76, 0.66, stroke=1, fill=1)
    pdf.circle(0.72, 0.64, 0.15, stroke=1, fill=1)
    draw_polygon(pdf, [(0.86, 0.68), (0.99, 0.63), (0.86, 0.58)])
    _draw_curve(
        pdf,
        (0.32, 0.5),
        (0.4, 0.64, 0.58, 0.62, 0.6, 0.48),
        (0.5, 0.5, 0.4, 0.44, 0.32, 0.5),
        closed=True,
    )
    _draw_dark(pdf, (0.75, 0.68, 0.025))


def _draw_toy_block(pdf: Canvas, fill: Color) -> None:
    """Draw a cube: its front, top and right side."""
    pdf.rect(0.08, 0.08, 0.62, 0.62, stroke=1, fill=1)
    draw_polygon(pdf, [(0.08, 0.7), (0.3, 0.92), (0.92, 0.92), (0.7, 0.7)])
    draw_polygon(pdf, [(0.7, 0.08), (0.92, 0.3), (0.92, 0.92), (0.7, 0.7)])


def _draw_book(pdf: Canvas, fill: Color) -> None:
    """Draw a closed book: its cover, a line by its spine, and a box for its title."""
    pdf.rect(0.18, 0.06, 0.66, 0.88, stroke=1, fill=1)
    _draw_lines(pdf, (0.3, 0.06, 0.3, 0.94))
    pdf.rect(0.42, 0.62, 0.3, 0.14, stroke=1, fill=0)


def _draw_gift_box(pdf: Canvas, width: float) -> None:
    """Draw a present ``width`` wide, in the middle of the square: a box with a lid, a ribbon
    round it and a bow on top."""
    for side in (1, -1):  # the bow's two loops
        _draw_curve(
            pdf,
            (0.5, 0.78),
            (0.5 - side * 0.2, 0.98, 0.5 - side * 0.3, 0.8, 0.5, 0.78),
            closed=True,
        )
    left = 0.5 - width / 2
    pdf.rect(left, 0.06, width, 0.56, stroke=1, fill=1)
    pdf.rect(left - 0.06, 0.62, width + 0.12, 0.16, stroke=1, fill=1)
    _draw_lines(pdf, (0.44, 0.06, 0.44, 0.78), (0.56, 0.06, 0.56, 0.78))


def _draw_gift(pdf: Canvas, fill: Color) -> None:
    """Draw a present wider than it's high."""
    _draw_gift_box(pdf, 0.76)


def _draw_square_gift(pdf: Canvas, fill: Color) -> None:
    """Draw a present as high as it's wide, with its lid."""
    _draw_gift_box(pdf, 0.56)


def _draw_tall_gift(pdf: Canvas, fill: Color) -> None:
    """Draw a present higher than it's wide."""
    _draw_gift_box(pdf, 0.36)


def _draw_bus(pdf: Canvas, fill: Color) -> None:
    """Draw a bus facing right: a long body with a row of windows, and two wheels."""
    pdf.roundRect(0.03, 0.18, 0.94, 0.62, 0.06, stroke=1, fill=1)
    for left in (0.09, 0.29, 0.49, 0.69):
        pdf.rect(left, 0.5, 0.16, 0.2, stroke=1, fill=0)
    _draw_lines(pdf, (0.03, 0.42, 0.97, 0.42))
    _draw_dark(pdf, (0.24, 0.18, 0.09), (0.76, 0.18, 0.09))


def _draw_button(pdf: Canvas, fill: Color) -> None:
    """Draw a button: a circle with a rim and four holes."""
    pdf.circle(0.5, 0.5, 0.42, stroke=1, fill=1)
    pdf.circle(0.5, 0.5, 0.33, stroke=1, fill=0)
    pdf.setFillColor(white)
    for hole_x, hole_y in ((0.42, 0.58), (0.58, 0.58), (0.42, 0.42), (0.58, 0.42)):
        pdf.circle(hole_x, hole_y, 0.045, stroke=1, fill=1)


def _draw_car(pdf: Canvas, fill: Color) -> None:
    """Draw a car facing right: a cabin on a body, and two wheels."""
    draw_polygon(pdf, [(0.22, 0.46), (0.34, 0.72), (0.68, 0.72), (0.82, 0.46)])
    pdf.roundRect(0.04, 0.2, 0.92, 0.28, 0.08, stroke=1, fill=1)
    _draw_dark(pdf, (0.27, 0.2, 0.1), (0.73, 0.2, 0.1))


def _draw_cat(pdf: Canvas, fill: Color) -> None:
    """Draw a cat's face: pointed ears, a round head, eyes, nose, mouth and whiskers."""
    draw_polygon(pdf, [(0.18, 0.6), (0.2, 0.96), (0.44, 0.78)])
    draw_polygon(pdf, [(0.82, 0.6), (0.8, 0.96), (0.56, 0.78)])
    pdf.ellipse(0.14, 0.08, 0.86, 0.8, stroke=1, fill=1)
    for side in (1, -1):
        _draw_curve(
            pdf,
            (0.5, 0.32),
            (0.5 - side * 0.02, 0.24, 0.5 - side * 0.08, 0.24, 0.5 - side * 0.1, 0.27),
        )
        _draw_lines(
            pdf,
            (0.5 - side * 0.14, 0.34, 0.5 - side * 0.44, 0.38),
            (0.5 - side * 0.14, 0.31, 0.5 - side * 0.44, 0.26),
        )
    _draw_dark(pdf, (0.37, 0.5, 0.045), (0.63, 0.5, 0.045))
    draw_polygon(pdf, [(0.45, 0.38), (0.55, 0.38), (0.5, 0.32)])


def _draw_chair(pdf: Canvas, fill: Color) -> None:
    """Draw a chair from the side, facing right: two legs, a back and a seat."""
    pdf.rect(0.2, 0.05, 0.07, 0.36, stroke=1, fill=1)
    pdf.rect(0.73, 0.05, 0.07, 0.36, stroke=1, fill=1)
    pdf.rect(0.2, 0.47, 0.08, 0.48, stroke=1, fill=1)
    pdf.rect(0.18, 0.4, 0.64, 0.08, stroke=1, fill=1)


def _draw_cookie(pdf: Canvas, fill: Color) -> None:
    """Draw a chocolate chip cookie."""
    pdf.circle(0.5, 0.5, 0.42, stroke=1, fill=1)
    _draw_dark(
        pdf,
        *(
            (chip_x, chip_y, 0.04)
            for chip_x, chip_y in (
                (0.36, 0.64),
                (0.6, 0.7),
                (0.7, 0.46),
                (0.42, 0.36),
                (0.54, 0.52),
                (0.28, 0.46),
                (0.58, 0.26),
            )
        ),
    )


def _draw_counter(pdf: Canvas, fill: Color) -> None:
    """Draw a counter: a plain circle."""
    pdf.circle(0.5, 0.5, 0.42, stroke=1, fill=1)


def _draw_crayon(pdf: Canvas, fill: Color) -> None:
    """Draw a crayon lying tilted: its body with two wrapper lines, a cone, and its point."""
    pdf.saveState()
    _tilt(pdf)
    pdf.rect(0.1, 0.39, 0.58, 0.22, stroke=1, fill=1)
    _draw_lines(pdf, (0.22, 0.39, 0.22, 0.61), (0.56, 0.39, 0.56, 0.61))
    draw_polygon(pdf, [(0.68, 0.39), (0.84, 0.45), (0.84, 0.55), (0.68, 0.61)])
    draw_polygon(pdf, [(0.84, 0.45), (0.94, 0.5), (0.84, 0.55)])
    pdf.restoreState()


def _draw_cupcake(pdf: Canvas, fill: Color) -> None:
    """Draw a cupcake: a pleated wrapper, frosting and a cherry."""
    draw_polygon(pdf, [(0.24, 0.06), (0.76, 0.06), (0.84, 0.44), (0.16, 0.44)])
    _draw_lines(pdf, (0.37, 0.06, 0.33, 0.44), (0.5, 0.06, 0.5, 0.44), (0.63, 0.06, 0.67, 0.44))
    _draw_curve(
        pdf,
        (0.1, 0.44),
        (0.0, 0.6, 0.2, 0.72, 0.3, 0.68),
        (0.32, 0.88, 0.68, 0.88, 0.7, 0.68),
        (0.8, 0.72, 1.0, 0.6, 0.9, 0.44),
        closed=True,
    )
    pdf.circle(0.5, 0.87, 0.065, stroke=1, fill=1)


def _draw_dog(pdf: Canvas, fill: Color) -> None:
    """Draw a dog's face: a head, floppy ears, eyes, a snout with a nose, and a mouth."""
    pdf.ellipse(0.2, 0.1, 0.8, 0.84, stroke=1, fill=1)
    for side in (1, -1):
        _draw_curve(
            pdf,
            (0.5 - side * 0.2, 0.8),
            (0.5 - side * 0.42, 0.86, 0.5 - side * 0.48, 0.5, 0.5 - side * 0.38, 0.36),
            (0.5 - side * 0.3, 0.34, 0.5 - side * 0.24, 0.5, 0.5 - side * 0.2, 0.62),
            closed=True,
        )
    pdf.ellipse(0.35, 0.16, 0.65, 0.42, stroke=1, fill=1)
    _draw_lines(pdf, (0.5, 0.33, 0.5, 0.22))
    _draw_dark(pdf, (0.4, 0.56, 0.04), (0.6, 0.56, 0.04))
    pdf.ellipse(0.44, 0.31, 0.56, 0.39, stroke=0, fill=1)


def _draw_fish(pdf: Canvas, fill: Color) -> None:
    """Draw a fish facing left: a tail, an oval body, a gill and an eye."""
    draw_polygon(pdf, [(0.72, 0.5), (0.96, 0.74), (0.96, 0.26)])
    pdf.ellipse(0.06, 0.26, 0.8, 0.74, stroke=1, fill=1)
    _draw_curve(pdf, (0.36, 0.66), (0.42, 0.56, 0.42, 0.44, 0.36, 0.34))
    _draw_dark(pdf, (0.24, 0.56, 0.035))


def _draw_flower(pdf: Canvas, fill: Color) -> None:
    """Draw a flower: a stem with a leaf, six round petals and a middle."""
    _draw_lines(pdf, (0.5, 0.04, 0.5, 0.52))
    _draw_curve(
        pdf,
        (0.5, 0.2),
        (0.6, 0.32, 0.74, 0.3, 0.8, 0.26),
        (0.72, 0.17, 0.58, 0.15, 0.5, 0.2),
        closed=True,
    )
    for index in range(6):
        angle = pi / 2 + index * pi / 3
        pdf.circle(0.5 + 0.17 * cos(angle), 0.68 + 0.17 * sin(angle), 0.11, stroke=1, fill=1)
    pdf.setFillColor(white)
    pdf.circle(0.5, 0.68, 0.09, stroke=1, fill=1)


def _draw_american_football(pdf: Canvas, fill: Color) -> None:
    """Draw an American football lying tilted: a pointed oval with laces."""
    pdf.saveState()
    _tilt(pdf)
    _draw_curve(
        pdf,
        (0.06, 0.5),
        (0.24, 0.8, 0.76, 0.8, 0.94, 0.5),
        (0.76, 0.2, 0.24, 0.2, 0.06, 0.5),
        closed=True,
    )
    _draw_lines(pdf, (0.36, 0.56, 0.64, 0.56), *((x, 0.52, x, 0.6) for x in (0.4, 0.47, 0.53, 0.6)))
    pdf.restoreState()


def _draw_granola_bar(pdf: Canvas, fill: Color) -> None:
    """Draw a wrapped granola bar: a bar with crimped ends and a label."""
    for side in (1, -1):  # each crimped end, its zigzag outside the bar
        inner, outer, middle = 0.5 - side * 0.38, 0.5 - side * 0.46, 0.5 - side * 0.43
        zigzag = [(outer if step % 2 == 0 else middle, 0.3 + step * 0.05) for step in range(9)]
        draw_polygon(pdf, [(inner, 0.3), *zigzag, (inner, 0.7)])
    pdf.roundRect(0.12, 0.3, 0.76, 0.4, 0.04, stroke=1, fill=1)
    pdf.rect(0.32, 0.4, 0.36, 0.2, stroke=1, fill=0)


def _draw_house(pdf: Canvas, fill: Color) -> None:
    """Draw a house: a roof over a wall with a door."""
    draw_polygon(pdf, [(0.06, 0.55), (0.94, 0.55), (0.5, 0.94)])
    pdf.rect(0.16, 0.06, 0.68, 0.49, stroke=1, fill=1)
    pdf.rect(0.43, 0.06, 0.14, 0.22, stroke=1, fill=0)


def _draw_jersey(pdf: Canvas, fill: Color) -> None:
    """Draw a jersey: a shirt with short sleeves and a round neck."""
    jersey = pdf.beginPath()
    jersey.moveTo(0.38, 0.92)
    for point in (
        (0.15, 0.85),  # left shoulder
        (0.02, 0.66),  # the end of the left sleeve
        (0.14, 0.58),
        (0.22, 0.66),  # left armpit
        (0.22, 0.06),
        (0.78, 0.06),
        (0.78, 0.66),
        (0.86, 0.58),
        (0.98, 0.66),
        (0.85, 0.85),
        (0.62, 0.92),
    ):
        jersey.lineTo(*point)
    jersey.curveTo(0.58, 0.8, 0.42, 0.8, 0.38, 0.92)  # the neck
    jersey.close()
    pdf.drawPath(jersey, stroke=1, fill=1)


def _draw_leaf(pdf: Canvas, fill: Color) -> None:
    """Draw a leaf pointing up and right: its blade, a vein down its middle, and its stem."""
    _draw_lines(pdf, (0.12, 0.14, 0.04, 0.04))
    _draw_curve(
        pdf,
        (0.12, 0.14),
        (0.1, 0.7, 0.5, 0.94, 0.9, 0.9),
        (0.88, 0.48, 0.56, 0.1, 0.12, 0.14),
        closed=True,
    )
    _draw_lines(pdf, (0.12, 0.14, 0.84, 0.84))


def _draw_pencil(pdf: Canvas, fill: Color) -> None:
    """Draw a pencil lying tilted: an eraser, its metal band, the body, the sharpened wood and
    the lead."""
    pdf.saveState()
    _tilt(pdf)
    pdf.roundRect(0.03, 0.42, 0.12, 0.16, 0.03, stroke=1, fill=1)
    pdf.rect(0.13, 0.42, 0.07, 0.16, stroke=1, fill=1)
    pdf.rect(0.2, 0.42, 0.54, 0.16, stroke=1, fill=1)
    _draw_lines(pdf, (0.2, 0.5, 0.74, 0.5))
    draw_polygon(pdf, [(0.74, 0.42), (0.92, 0.5), (0.74, 0.58)])
    pdf.setFillColor(OUTLINE_COLOUR)
    draw_polygon(pdf, [(0.86, 0.4733), (0.92, 0.5), (0.86, 0.5267)])
    pdf.restoreState()


def _draw_rabbit(pdf: Canvas, fill: Color) -> None:
    """Draw a rabbit's face: two long ears, a round head, eyes, a nose and whiskers."""
    for left in (0.28, 0.56):
        pdf.ellipse(left, 0.5, left + 0.16, 0.98, stroke=1, fill=1)
        pdf.ellipse(left + 0.04, 0.62, left + 0.12, 0.92, stroke=1, fill=0)
    pdf.circle(0.5, 0.36, 0.3, stroke=1, fill=1)
    for side in (1, -1):
        _draw_lines(
            pdf,
            (0.5 - side * 0.08, 0.28, 0.5 - side * 0.38, 0.32),
            (0.5 - side * 0.08, 0.26, 0.5 - side * 0.38, 0.2),
        )
    _draw_dark(pdf, (0.4, 0.42, 0.035), (0.6, 0.42, 0.035))
    draw_polygon(pdf, [(0.46, 0.32), (0.54, 0.32), (0.5, 0.27)])


def _draw_football(pdf: Canvas, fill: Color) -> None:
    """
    Draw a football in the pattern it's stitched in: a dark pentagon in the middle, five white
    hexagons round it, and the near parts of the five dark pentagons beyond, cut off by the edge.
    Each of the middle pentagon's corners leads out to the inner corner of the pentagon in line
    with it, and a seam joins each of those pentagons to the next, closing the hexagons.
    """
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)

    def pentagon(middle_x: float, middle_y: float, radius: float, turn: float) -> list[Point]:
        return [
            (
                middle_x + radius * cos(turn + index * 2 * pi / 5),
                middle_y + radius * sin(turn + index * 2 * pi / 5),
            )
            for index in range(5)
        ]

    middle = pentagon(0.5, 0.5, 0.13, pi / 2)  # a corner at the top
    outer = []
    for index in range(5):  # in line with each corner, its first corner pointing in
        angle = pi / 2 + index * 2 * pi / 5
        outer.append(pentagon(0.5 + 0.39 * cos(angle), 0.5 + 0.39 * sin(angle), 0.12, angle + pi))
    pdf.saveState()
    edge = pdf.beginPath()
    edge.circle(0.5, 0.5, 0.44)
    pdf.clipPath(edge, stroke=0, fill=0)
    seams = [(*middle[index], *outer[index][0]) for index in range(5)]
    # each outer pentagon's corner turned towards the next, joined to that one's turned back
    seams += [(*outer[index][4], *outer[(index + 1) % 5][1]) for index in range(5)]
    _draw_lines(pdf, *seams)
    pdf.setFillColor(OUTLINE_COLOUR)
    for each in outer:
        draw_polygon(pdf, each)
    pdf.restoreState()
    pdf.setFillColor(OUTLINE_COLOUR)
    draw_polygon(pdf, middle)
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=0)


def _draw_star(pdf: Canvas, fill: Color) -> None:
    """Draw a five-pointed star, point up."""
    points = []
    for index in range(10):
        radius = 0.5 if index % 2 == 0 else 0.19  # each point, then the corner between two
        angle = pi / 2 + index * pi / 5
        points.append((0.5 + radius * cos(angle), 0.47 + radius * sin(angle)))
    draw_polygon(pdf, points)


def _draw_tent(pdf: Canvas, fill: Color) -> None:
    """Draw a tent: a triangle with a dark doorway, and a flag on its pole."""
    _draw_lines(pdf, (0.5, 0.86, 0.5, 0.97))
    draw_polygon(pdf, [(0.5, 0.97), (0.63, 0.93), (0.5, 0.89)])
    draw_polygon(pdf, [(0.04, 0.1), (0.96, 0.1), (0.5, 0.86)])
    pdf.setFillColor(OUTLINE_COLOUR)
    draw_polygon(pdf, [(0.38, 0.1), (0.62, 0.1), (0.5, 0.48)])


def _draw_tree(pdf: Canvas, fill: Color) -> None:
    """Draw a pine tree: a trunk and three tiers of branches."""
    pdf.rect(0.44, 0.04, 0.12, 0.18, stroke=1, fill=1)
    for low, half_width, high in ((0.22, 0.36, 0.62), (0.44, 0.3, 0.8), (0.64, 0.22, 0.96)):
        draw_polygon(pdf, [(0.5 - half_width, low), (0.5 + half_width, low), (0.5, high)])


def _draw_trophy(pdf: Canvas, fill: Color) -> None:
    """Draw a trophy: a cup with two handles on a stem, a step and a base."""
    for side in (1, -1):
        _draw_curve(
            pdf,
            (0.5 - side * 0.22, 0.86),
            (0.5 - side * 0.44, 0.86, 0.5 - side * 0.42, 0.56, 0.5 - side * 0.16, 0.56),
        )
    pdf.rect(0.26, 0.04, 0.48, 0.1, stroke=1, fill=1)
    pdf.rect(0.34, 0.14, 0.32, 0.12, stroke=1, fill=1)
    pdf.rect(0.46, 0.26, 0.08, 0.2, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.24, 0.92),
        (0.4, 0.92, 0.6, 0.92, 0.76, 0.92),
        (0.76, 0.6, 0.62, 0.44, 0.5, 0.44),
        (0.38, 0.44, 0.24, 0.6, 0.24, 0.92),
        closed=True,
    )


def _draw_truck(pdf: Canvas, fill: Color) -> None:
    """Draw a truck facing right: a box, a cab with a window, and three wheels."""
    pdf.rect(0.04, 0.22, 0.58, 0.56, stroke=1, fill=1)
    draw_polygon(pdf, [(0.62, 0.22), (0.95, 0.22), (0.95, 0.46), (0.86, 0.6), (0.62, 0.6)])
    pdf.rect(0.68, 0.42, 0.15, 0.12, stroke=1, fill=0)
    _draw_dark(pdf, (0.2, 0.2, 0.09), (0.46, 0.2, 0.09), (0.8, 0.2, 0.09))


def _draw_turtle(pdf: Canvas, fill: Color) -> None:
    """Draw a turtle from the side, facing right: legs, a tail and a head under a domed shell
    with a pattern, and an eye."""
    pdf.roundRect(0.24, 0.14, 0.1, 0.18, 0.03, stroke=1, fill=1)
    pdf.roundRect(0.62, 0.14, 0.1, 0.18, 0.03, stroke=1, fill=1)
    draw_polygon(pdf, [(0.14, 0.3), (0.03, 0.25), (0.14, 0.24)])
    pdf.ellipse(0.76, 0.24, 0.97, 0.42, stroke=1, fill=1)
    _draw_curve(pdf, (0.12, 0.26), (0.14, 0.8, 0.82, 0.8, 0.84, 0.26), closed=True)
    draw_polygon(
        pdf, [(0.38, 0.4), (0.58, 0.4), (0.64, 0.5), (0.58, 0.6), (0.38, 0.6), (0.32, 0.5)]
    )
    _draw_dark(pdf, (0.9, 0.36, 0.02))


def _draw_ball(pdf: Canvas, fill: Color) -> None:
    """Draw a plain ball: a circle with a curved stripe round it."""
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)
    pdf.saveState()
    edge = pdf.beginPath()
    edge.circle(0.5, 0.5, 0.44)
    pdf.clipPath(edge, stroke=0, fill=0)
    _draw_curve(pdf, (0.02, 0.62), (0.32, 0.42, 0.68, 0.42, 0.98, 0.62))
    _draw_curve(pdf, (0.02, 0.4), (0.32, 0.2, 0.68, 0.2, 0.98, 0.4))
    pdf.restoreState()


def _draw_chocolate_bar(pdf: Canvas, fill: Color) -> None:
    """Draw a chocolate bar standing up, its wrapper torn open at the top to show the
    chocolate's squares."""
    pdf.rect(0.25, 0.46, 0.5, 0.48, stroke=1, fill=1)
    _draw_lines(pdf, (0.5, 0.56, 0.5, 0.94), (0.25, 0.75, 0.75, 0.75))
    torn = [(0.8 - step * 0.075, 0.56 if step % 2 == 0 else 0.5) for step in range(9)]
    draw_polygon(pdf, [(0.2, 0.06), (0.8, 0.06), *torn])
    pdf.rect(0.3, 0.2, 0.4, 0.16, stroke=1, fill=0)


def _draw_hard_candy(pdf: Canvas, fill: Color) -> None:
    """Draw a wrapped hard candy: a round sweet with the wrapper twisted at each end."""
    for side in (1, -1):
        edge = 0.5 - side * 0.44
        draw_polygon(pdf, [(0.5 - side * 0.18, 0.5), (edge, 0.68), (edge, 0.32)])
        _draw_lines(pdf, (0.5 - side * 0.2, 0.5, 0.5 - side * 0.36, 0.6))
        _draw_lines(pdf, (0.5 - side * 0.2, 0.5, 0.5 - side * 0.36, 0.4))
    pdf.ellipse(0.27, 0.34, 0.73, 0.66, stroke=1, fill=1)


def _draw_lollipop(pdf: Canvas, fill: Color) -> None:
    """Draw a lollipop: a round candy with a swirl, on a stick."""
    _draw_lines(pdf, (0.5, 0.04, 0.5, 0.4))
    pdf.circle(0.5, 0.66, 0.3, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.5, 0.66),
        (0.58, 0.68, 0.58, 0.78, 0.5, 0.78),
        (0.38, 0.78, 0.36, 0.6, 0.5, 0.56),
        (0.66, 0.52, 0.72, 0.72, 0.62, 0.84),
    )


def _draw_teddy_bear(pdf: Canvas, fill: Color) -> None:
    """Draw a teddy bear sitting: ears, arms and legs behind a round body and head, a muzzle,
    eyes and a nose."""
    for middle_x in (0.3, 0.7):
        pdf.circle(middle_x, 0.88, 0.08, stroke=1, fill=1)
    for left in (0.1, 0.66):
        pdf.ellipse(left, 0.34, left + 0.24, 0.56, stroke=1, fill=1)
    for left in (0.2, 0.56):
        pdf.ellipse(left, 0.03, left + 0.24, 0.23, stroke=1, fill=1)
    pdf.ellipse(0.27, 0.1, 0.73, 0.62, stroke=1, fill=1)
    pdf.circle(0.5, 0.74, 0.18, stroke=1, fill=1)
    pdf.ellipse(0.41, 0.62, 0.59, 0.74, stroke=1, fill=1)
    _draw_dark(pdf, (0.43, 0.79, 0.025), (0.57, 0.79, 0.025), (0.5, 0.71, 0.03))


def _draw_stick(pdf: Canvas, start: Point, end: Point, width: float) -> None:
    """Draw a stick ``width`` thick from ``start`` to ``end``, as a long, thin outline."""
    (start_x, start_y), (end_x, end_y) = start, end
    length = hypot(end_x - start_x, end_y - start_y)
    across_x = (start_y - end_y) / length * width / 2
    across_y = (end_x - start_x) / length * width / 2
    draw_polygon(
        pdf,
        [
            (start_x + across_x, start_y + across_y),
            (end_x + across_x, end_y + across_y),
            (end_x - across_x, end_y - across_y),
            (start_x - across_x, start_y - across_y),
        ],
    )


def _draw_candy_bar(pdf: Canvas, fill: Color) -> None:
    """Draw a candy bar lying tilted: the bar, showing where its wrapper is torn open, and the
    wrapper, with a label and a crimped end."""
    pdf.saveState()
    _tilt(pdf)
    pdf.roundRect(0.06, 0.4, 0.34, 0.2, 0.06, stroke=1, fill=1)
    crimped = [(0.94 if step % 2 == 0 else 0.9, 0.37 + step * 0.0325) for step in range(9)]
    draw_polygon(pdf, [(0.84, 0.37), *crimped, (0.84, 0.63)])
    torn = [(0.3 if step % 2 == 0 else 0.35, 0.63 - step * 0.0325) for step in range(9)]
    draw_polygon(pdf, [(0.84, 0.37), (0.84, 0.63), *torn])
    pdf.rect(0.47, 0.44, 0.26, 0.12, stroke=1, fill=0)
    pdf.restoreState()


def _draw_banana(pdf: Canvas, fill: Color) -> None:
    """Draw a banana lying curved like a smile: a short dark stem at the right, a ridge along it,
    and a dark tip capping its blunt left end."""
    pdf.setFillColor(OUTLINE_COLOUR)
    draw_polygon(pdf, [(0.77, 0.55), (0.83, 0.51), (0.873, 0.585), (0.833, 0.615)])
    pdf.setFillColor(fill)
    _draw_curve(
        pdf,
        (0.15, 0.565),
        (0.135, 0.535, 0.13, 0.5, 0.135, 0.47),  # the blunt end
        (0.2, 0.31, 0.36, 0.21, 0.52, 0.21),  # the outer edge
        (0.68, 0.21, 0.8, 0.32, 0.83, 0.5),  # up to the stem
        (0.81, 0.52, 0.79, 0.535, 0.77, 0.55),
        (0.7, 0.43, 0.6, 0.39, 0.48, 0.39),  # the inner edge, back
        (0.34, 0.39, 0.22, 0.48, 0.15, 0.565),
        closed=True,
    )
    _draw_curve(pdf, (0.16, 0.535), (0.3, 0.34, 0.6, 0.28, 0.79, 0.535))  # the ridge
    pdf.setFillColor(OUTLINE_COLOUR)
    _draw_curve(  # the tip
        pdf,
        (0.142, 0.545),
        (0.11, 0.54, 0.105, 0.5, 0.135, 0.49),
        (0.13, 0.51, 0.135, 0.53, 0.142, 0.545),
        closed=True,
    )


def _draw_duck(pdf: Canvas, fill: Color) -> None:
    """Draw a duck swimming, facing right: its body with its tail turned up, its head, a flat
    bill, a wing and an eye."""
    _draw_curve(
        pdf,
        (0.06, 0.6),  # the tail's tip
        (0.08, 0.4, 0.1, 0.18, 0.4, 0.16),  # under the tail and along the bottom
        (0.66, 0.14, 0.84, 0.26, 0.78, 0.46),  # round the breast to the neck
        (0.6, 0.46, 0.3, 0.42, 0.06, 0.6),  # and along the back
        closed=True,
    )
    _draw_curve(
        pdf,
        (0.8, 0.65),
        (0.9, 0.67, 0.98, 0.64, 0.97, 0.59),
        (0.94, 0.55, 0.86, 0.56, 0.8, 0.58),
        closed=True,
    )
    pdf.circle(0.7, 0.64, 0.14, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.28, 0.36),
        (0.38, 0.46, 0.56, 0.42, 0.62, 0.32),
        (0.5, 0.26, 0.36, 0.28, 0.28, 0.36),
        closed=True,
    )
    _draw_dark(pdf, (0.73, 0.68, 0.025))


def _draw_frog(pdf: Canvas, fill: Color) -> None:
    """Draw a frog sitting, from the side, facing right: a back foot, its body, its folded back
    leg over it, a front leg, a bulging eye and a mouth."""
    pdf.ellipse(0.1, 0.08, 0.46, 0.17, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.12, 0.2),  # the bottom of its back
        (0.06, 0.42, 0.3, 0.62, 0.5, 0.62),  # up its back
        (0.7, 0.64, 0.88, 0.56, 0.93, 0.42),  # over its head to its snout
        (0.95, 0.3, 0.78, 0.18, 0.62, 0.18),  # under its chin
        closed=True,
    )
    pdf.ellipse(0.14, 0.14, 0.5, 0.42, stroke=1, fill=1)
    _draw_lines(pdf, (0.68, 0.24, 0.7, 0.1), (0.63, 0.1, 0.78, 0.1))
    pdf.circle(0.72, 0.6, 0.09, stroke=1, fill=1)
    _draw_curve(pdf, (0.93, 0.42), (0.86, 0.38, 0.78, 0.38, 0.72, 0.41))
    _draw_dark(pdf, (0.74, 0.62, 0.035))


def _draw_snail(pdf: Canvas, fill: Color) -> None:
    """Draw a snail from the side, facing right: its body along the ground, rising to its head,
    two eye stalks, and a round shell with a spiral on its back."""
    body = pdf.beginPath()
    body.moveTo(0.04, 0.12)
    body.lineTo(0.8, 0.12)
    body.curveTo(0.9, 0.12, 0.94, 0.2, 0.92, 0.32)  # the front of its head
    body.curveTo(0.9, 0.46, 0.76, 0.48, 0.72, 0.38)  # over its head to its neck
    body.lineTo(0.7, 0.24)
    body.lineTo(0.14, 0.24)
    body.curveTo(0.08, 0.24, 0.04, 0.18, 0.04, 0.12)  # its tail
    body.close()
    pdf.drawPath(body, stroke=1, fill=1)
    _draw_lines(pdf, (0.82, 0.44, 0.79, 0.62), (0.88, 0.42, 0.92, 0.6))
    pdf.circle(0.4, 0.46, 0.28, stroke=1, fill=1)
    turns = 3.5 * pi  # a spiral of one and three quarter turns, out from the shell's middle
    spiral = pdf.beginPath()
    for step in range(57):
        angle = turns * step / 56
        radius = 0.025 + 0.2 * angle / turns
        point = (0.4 + radius * cos(angle), 0.46 + radius * sin(angle))
        if step == 0:
            spiral.moveTo(*point)
        else:
            spiral.lineTo(*point)
    pdf.drawPath(spiral, stroke=1, fill=0)
    _draw_dark(pdf, (0.79, 0.63, 0.025), (0.92, 0.61, 0.025))


def _draw_bell(pdf: Canvas, fill: Color) -> None:
    """Draw a hand bell: a handle with a knob, the bell flaring out to its rim, and the clapper
    under it."""
    _draw_dark(pdf, (0.5, 0.1, 0.06))
    pdf.setFillColor(fill)
    pdf.rect(0.45, 0.68, 0.1, 0.16, stroke=1, fill=1)
    pdf.circle(0.5, 0.88, 0.06, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.12, 0.18),
        (0.3, 0.24, 0.22, 0.74, 0.5, 0.74),
        (0.78, 0.74, 0.7, 0.24, 0.88, 0.18),
        closed=True,
    )
    pdf.roundRect(0.1, 0.13, 0.8, 0.07, 0.035, stroke=1, fill=1)


def _draw_drum(pdf: Canvas, fill: Color) -> None:
    """Draw a drum from the side: its body with a cord zigzagging round it, its top, and two
    drumsticks resting on it."""
    body = pdf.beginPath()
    body.moveTo(0.12, 0.68)
    body.lineTo(0.12, 0.24)
    body.curveTo(0.12, 0.11, 0.88, 0.11, 0.88, 0.24)
    body.lineTo(0.88, 0.68)
    body.close()
    pdf.drawPath(body, stroke=1, fill=1)
    cord = pdf.beginPath()
    cord.moveTo(0.16, 0.63)
    for point in ((0.27, 0.2), (0.38, 0.59), (0.5, 0.17), (0.62, 0.59), (0.73, 0.2), (0.84, 0.63)):
        cord.lineTo(*point)
    pdf.drawPath(cord, stroke=1, fill=0)
    pdf.ellipse(0.12, 0.58, 0.88, 0.78, stroke=1, fill=1)
    for tip_x, end_x in ((0.36, 0.1), (0.64, 0.9)):
        _draw_stick(pdf, (tip_x, 0.7), (end_x, 0.95), 0.035)
        pdf.circle(tip_x, 0.7, 0.03, stroke=1, fill=1)


def _draw_guitar(pdf: Canvas, fill: Color) -> None:
    """Draw a guitar lying tilted: its neck and head, its body narrowing at the waist, a bridge,
    a dark sound hole, and strings."""
    pdf.saveState()
    _tilt(pdf)
    pdf.rect(0.62, 0.465, 0.26, 0.07, stroke=1, fill=1)
    pdf.roundRect(0.87, 0.43, 0.1, 0.14, 0.02, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.04, 0.5),
        (0.04, 0.62, 0.12, 0.7, 0.22, 0.7),  # the wide end's top
        (0.32, 0.7, 0.33, 0.62, 0.38, 0.62),  # into the waist
        (0.43, 0.62, 0.45, 0.66, 0.52, 0.66),
        (0.6, 0.66, 0.64, 0.58, 0.64, 0.5),  # round the narrow end
        (0.64, 0.42, 0.6, 0.34, 0.52, 0.34),
        (0.45, 0.34, 0.43, 0.38, 0.38, 0.38),
        (0.33, 0.38, 0.32, 0.3, 0.22, 0.3),
        (0.12, 0.3, 0.04, 0.38, 0.04, 0.5),
        closed=True,
    )
    pdf.rect(0.13, 0.44, 0.04, 0.12, stroke=1, fill=0)
    _draw_dark(pdf, (0.42, 0.5, 0.065))
    _draw_lines(pdf, *((0.15, string_y, 0.9, string_y) for string_y in (0.48, 0.5, 0.52)))
    pdf.restoreState()


def _draw_maraca(pdf: Canvas, fill: Color) -> None:
    """Draw a maraca lying tilted: a handle, and an oval head with a band round it."""
    pdf.saveState()
    _tilt(pdf)
    pdf.roundRect(0.5, 0.455, 0.44, 0.09, 0.04, stroke=1, fill=1)
    pdf.ellipse(0.06, 0.28, 0.58, 0.72, stroke=1, fill=1)
    for edge in (0.26, 0.38):  # each side of the band bows towards the handle
        _draw_curve(pdf, (edge, 0.714), (edge + 0.04, 0.6, edge + 0.04, 0.4, edge, 0.286))
    pdf.restoreState()


def _draw_musical_triangle(pdf: Canvas, fill: Color) -> None:
    """Draw a musical triangle: a bar bent into a triangle, open at its bottom-left corner, hung
    from a string, with its beater beside it."""
    _draw_lines(pdf, (0.42, 0.84, 0.42, 0.97))
    draw_polygon(
        pdf,
        [  # round the outside from the open corner, then back round the inside
            (0.103, 0.259),
            (0.42, 0.84),
            (0.78, 0.18),
            (0.146, 0.18),
            (0.21, 0.23),
            (0.696, 0.23),
            (0.42, 0.736),
            (0.177, 0.291),
        ],
    )
    _draw_stick(pdf, (0.66, 0.58), (0.94, 0.9), 0.03)


def _draw_tambourine(pdf: Canvas, fill: Color) -> None:
    """Draw a tambourine: a round frame with six jingles in it, round a drum skin."""
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)
    pdf.circle(0.5, 0.5, 0.33, stroke=1, fill=1)
    pdf.setFillColor(white)
    for index in range(6):
        angle = pi / 2 + index * pi / 3
        pdf.circle(0.5 + 0.385 * cos(angle), 0.5 + 0.385 * sin(angle), 0.04, stroke=1, fill=1)


def _draw_xylophone(pdf: Canvas, fill: Color) -> None:
    """Draw a xylophone from above: two rails, six bars across them, each shorter than the one
    before and pinned to the rails, and a mallet."""
    _draw_lines(pdf, (0.04, 0.787, 0.8, 0.604), (0.04, 0.253, 0.8, 0.436))
    pins = []
    for index in range(6):
        middle, length = 0.11 + index * 0.125, 0.62 - index * 0.06
        pdf.rect(middle - 0.05, 0.52 - length / 2, 0.1, length, stroke=1, fill=1)
        pins += [(middle, 0.52 + side * (length / 2 - 0.06), 0.012) for side in (1, -1)]
    _draw_dark(pdf, *pins)
    pdf.setFillColor(fill)
    _draw_stick(pdf, (0.9, 0.56), (0.96, 0.08), 0.03)
    pdf.circle(0.89, 0.62, 0.06, stroke=1, fill=1)


def _draw_pizza(pdf: Canvas, fill: Color) -> None:
    """Draw a pizza from above: its crust round the edge, cut into 6 slices, with pepperoni."""
    pdf.circle(0.5, 0.5, 0.44, stroke=1, fill=1)
    pdf.circle(0.5, 0.5, 0.36, stroke=1, fill=0)
    for turn in range(3):
        angle = pi * turn / 3 + pi / 2
        _draw_lines(
            pdf,
            (
                0.5 + 0.44 * cos(angle),
                0.5 + 0.44 * sin(angle),
                0.5 - 0.44 * cos(angle),
                0.5 - 0.44 * sin(angle),
            ),
        )
    _draw_dark(
        pdf,
        *(
            (0.5 + 0.22 * cos(angle), 0.5 + 0.22 * sin(angle), 0.045)
            for angle in (pi * (turn / 3 + 1 / 6) + pi / 2 for turn in range(6))
        ),
    )


def _draw_round_cake(pdf: Canvas, fill: Color) -> None:
    """Draw a round cake from the side, as ``draw_cake_from_the_side`` draws it, with a candle."""
    draw_cake_from_the_side(pdf, 0.1, 0.72, 0.8, 0.62)
    pdf.rect(0.46, 0.6, 0.08, 0.2, stroke=1, fill=1)
    _draw_curve(
        pdf,
        (0.5, 0.82),
        (0.44, 0.88, 0.5, 0.94, 0.5, 0.97),
        (0.5, 0.94, 0.56, 0.88, 0.5, 0.82),
        closed=True,
    )


def _draw_sandwich(pdf: Canvas, fill: Color) -> None:
    """Draw a square sandwich from above: its crust round the edge, cut corner to corner."""
    pdf.rect(0.1, 0.1, 0.8, 0.8, stroke=1, fill=1)
    pdf.rect(0.18, 0.18, 0.64, 0.64, stroke=1, fill=0)
    _draw_lines(pdf, (0.1, 0.9, 0.9, 0.1))


def _draw_square_cake(pdf: Canvas, fill: Color) -> None:
    """Draw a square cake from above: a bead of icing round its edge and a cherry on top."""
    pdf.rect(0.08, 0.08, 0.84, 0.84, stroke=1, fill=1)
    beads = [0.17 + 0.0825 * step for step in range(9)]
    for along in beads:
        for bead_x, bead_y in ((along, 0.17), (along, 0.83), (0.17, along), (0.83, along)):
            pdf.circle(bead_x, bead_y, 0.035, stroke=1, fill=0)
    pdf.circle(0.5, 0.5, 0.08, stroke=1, fill=0)


_OBJECT_DRAWERS: dict[DrawnObject, Callable[[Canvas, Color], None]] = {
    DrawnObject.AMERICAN_FOOTBALL: _draw_american_football,
    DrawnObject.ANT: _draw_ant,
    DrawnObject.APPLE: _draw_apple,
    DrawnObject.BAG: _draw_bag,
    DrawnObject.BALL: _draw_ball,
    DrawnObject.BALLOON: _draw_balloon,
    DrawnObject.BANANA: _draw_banana,
    DrawnObject.BASEBALL: _draw_baseball,
    DrawnObject.BASKETBALL: _draw_basketball,
    DrawnObject.BELL: _draw_bell,
    DrawnObject.BIRD: _draw_bird,
    DrawnObject.BLOCK: _draw_toy_block,
    DrawnObject.BOOK: _draw_book,
    DrawnObject.BUS: _draw_bus,
    DrawnObject.BUTTON: _draw_button,
    DrawnObject.CANDY_BAR: _draw_candy_bar,
    DrawnObject.CAR: _draw_car,
    DrawnObject.CAT: _draw_cat,
    DrawnObject.CHAIR: _draw_chair,
    DrawnObject.CHOCOLATE_BAR: _draw_chocolate_bar,
    DrawnObject.COOKIE: _draw_cookie,
    DrawnObject.COUNTER: _draw_counter,
    DrawnObject.CRAYON: _draw_crayon,
    DrawnObject.CUPCAKE: _draw_cupcake,
    DrawnObject.DOG: _draw_dog,
    DrawnObject.DRUM: _draw_drum,
    DrawnObject.DUCK: _draw_duck,
    DrawnObject.FISH: _draw_fish,
    DrawnObject.FLOWER: _draw_flower,
    DrawnObject.FOOTBALL: _draw_football,
    DrawnObject.FROG: _draw_frog,
    DrawnObject.GIFT: _draw_gift,
    DrawnObject.GRANOLA_BAR: _draw_granola_bar,
    DrawnObject.GUITAR: _draw_guitar,
    DrawnObject.HARD_CANDY: _draw_hard_candy,
    DrawnObject.HOUSE: _draw_house,
    DrawnObject.JERSEY: _draw_jersey,
    DrawnObject.LEAF: _draw_leaf,
    DrawnObject.LOLLIPOP: _draw_lollipop,
    DrawnObject.MARACA: _draw_maraca,
    DrawnObject.MUSICAL_TRIANGLE: _draw_musical_triangle,
    DrawnObject.PENCIL: _draw_pencil,
    DrawnObject.PIZZA: _draw_pizza,
    DrawnObject.RABBIT: _draw_rabbit,
    DrawnObject.SNAIL: _draw_snail,
    DrawnObject.ROUND_CAKE: _draw_round_cake,
    DrawnObject.SANDWICH: _draw_sandwich,
    DrawnObject.SQUARE_CAKE: _draw_square_cake,
    DrawnObject.SQUARE_GIFT: _draw_square_gift,
    DrawnObject.STAR: _draw_star,
    DrawnObject.TALL_GIFT: _draw_tall_gift,
    DrawnObject.TAMBOURINE: _draw_tambourine,
    DrawnObject.TEDDY_BEAR: _draw_teddy_bear,
    DrawnObject.TENT: _draw_tent,
    DrawnObject.TREE: _draw_tree,
    DrawnObject.TROPHY: _draw_trophy,
    DrawnObject.TRUCK: _draw_truck,
    DrawnObject.TURTLE: _draw_turtle,
    DrawnObject.XYLOPHONE: _draw_xylophone,
}
