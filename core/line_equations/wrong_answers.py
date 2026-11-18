"""
Wrong answers to questions about a line, from the mistakes STAAR's wrong options model.

The first three of each list make a balanced set of four with the answer, so no sign or shape
gives the answer away: a slope of -3/4 comes with -4/3, 3/4 and 4/3 (the reciprocal, the sign
and both), and an equation with each of two slopes beside each of two intercepts. Where a
mistake gives the answer itself or a choice already made, as the reciprocal of a slope of 1
does, the next mistake fills in, then nearby numbers.
"""

from collections.abc import Iterable, Iterator, Sequence
from fractions import Fraction
from itertools import count

from core.line_equations.data import (
    Equation,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    NumberStyle,
    Point,
    Relation,
    answer_of,
    line_from,
)
from core.line_equations.representation import terminates


def wrong_answers(data: LineQuestionData, count: int) -> tuple[LineAnswer, ...]:
    """
    Return ``count`` different wrong answers to ``data``, in the order of the
    mistakes ``_mistakes`` lists. In a decimal question, a wrong answer whose decimal doesn't
    terminate is passed over, since it can't be written like the others. So is an equation of
    the answer's line, such as point-slope form through another of its points, which is right.
    """
    answer = answer_of(data)
    chosen: list[LineAnswer] = []
    for choice in _mistakes(data):
        right = isinstance(choice, Equation) and choice.line == data.answer
        if right or choice == answer or choice in chosen:
            continue
        if _writable(choice, data.numbers):
            chosen.append(choice)
            if len(chosen) == count:
                break
    return tuple(chosen)


def _mistakes(data: LineQuestionData) -> Iterator[LineAnswer]:
    """
    Yield wrong answers to ``data``, the commonest mistakes first, then nearby numbers without
    end:

    - slope or rate of change: the reciprocal, the sign, both; the y- and x-intercepts for it.
      A vertical line's undefined slope: 0, and its number and the opposite as the slope. A
      horizontal line's slope of 0: undefined, and its number and the opposite;
    - y-intercept: the x-intercept for it, the sign, the x-intercept's opposite, the slope;
    - x-intercept or zero: the y-intercept for it, the sign, the y-intercept's opposite, the
      slope;
    - an intercept as a point, (0, b): x and y exchanged, (b, 0), and the other intercept, (0, a)
      and (a, 0); then the sign;
    - slope and y-intercept: the reciprocal slope, the x-intercept for the y-intercept, both;
      then the sign of each;
    - an equation: as ``_equation_mistakes`` lists them.
    """
    asked = data.asked
    if isinstance(asked, LineForm):
        yield from _equation_mistakes(data, asked)
        return
    line = data.answer
    slope, b, a = line.slope, line.y_intercept, line.x_intercept
    match asked:
        case LineFeature.SLOPE | LineFeature.RATE_OF_CHANGE if slope is None:
            yield from _numbers(Fraction(0), a, _opposite(a))
            yield from _nearby(Fraction(0))
        case LineFeature.SLOPE | LineFeature.RATE_OF_CHANGE if slope == 0:
            yield None
            yield from _numbers(b, _opposite(b))
            yield from _nearby(Fraction(0))
        case LineFeature.SLOPE | LineFeature.RATE_OF_CHANGE if slope is not None:
            yield from _numbers(1 / slope, -slope, -1 / slope, b, a)
            yield from _nearby(slope)
        case LineFeature.Y_INTERCEPT if b is not None and not data.as_point:
            yield from _numbers(a, -b, _opposite(a), slope, _opposite(slope))
            yield from _nearby(b)
        case LineFeature.X_INTERCEPT | LineFeature.ZERO if a is not None and not data.as_point:
            yield from _numbers(b, -a, _opposite(b), slope, _opposite(slope))
            yield from _nearby(a)
        case LineFeature.Y_INTERCEPT | LineFeature.X_INTERCEPT:
            yield from _point_mistakes(answer_of(data), b, a, asked)
        case LineFeature.SLOPE_AND_Y_INTERCEPT if slope is not None and b is not None:
            yield from _pair_mistakes(slope, b, a)
        case _:
            raise ValueError(f"{line} has no {asked} to ask.")


def _equation_mistakes(data: LineQuestionData, form: LineForm) -> Iterator[LineAnswer]:
    """
    Yield wrong equations in ``form`` for ``data``, the commonest mistakes first, then nearby
    ones without end. Each of two slopes goes with each of two y-intercepts or points, so the
    first three make a balanced set with the answer: each slope, and each intercept or point, is
    in two of the four, and no sign of an intercept or constant marks the answer out.

    The slopes, when a point is shown: for a parallel line, the perpendicular slope, -1/m, then
    the reciprocal and the sign. For a perpendicular line, -1/r for a line with slope r, the
    slope only inverted, 1/r, then only negated, -r, then r itself. Otherwise, the reciprocal,
    the sign, then both. Rewriting an equation, with no point shown: the slope's sign, as in
    reading -A/B as A/B, then the reciprocal and both.

    - Slope-intercept form: each slope with the answer's y-intercept and, through a point
      (x₁, y₁) shown, y₁ + m·x₁, the sign slip in b = y₁ - m·x₁, or with no point, -b; then the
      x-intercept for b, then nearby numbers.
    - Standard form: through a point shown, each wrong line goes through it or through
      (-x₁, -y₁), which turns C into -C, as in STAAR's 8x + 3y = 45 against 8x - 3y = -51 (A.2
      2021 Q19); then x and y exchanged, then points above and below it. A line through a point
      keeps whole coefficients as small as the answer's. With no point, each slope goes with b
      and -b, then the x-intercept for b, and the reciprocal is left out, since with the same
      y-intercept its coefficients grow, which would give the answer away. A line through the
      origin takes the y-intercepts slope-intercept form does, 0 and y₁ + m·x₁, so C = 0 is in
      two of the four.
    - Point-slope form: through the point shown, or with its signs flipped, as in
      y + 5 = m(x - 4) for (4, 5); then x and y exchanged, then points above and below it.
    - x = a and y = b: as ``_level_mistakes`` lists them.

    STAAR's wrong lines through the point itself (the reciprocal through it, A.2 2019 Q6) give
    the answer the only intercept of its sign about half the time, so they aren't used.
    """
    line = data.answer
    slope = line.slope
    if slope is None or slope == 0:
        yield from _level_mistakes(data, form)
        return
    b, a = line.y_intercept, line.x_intercept
    assert b is not None and a is not None  # the line is sloped
    if not data.points:
        reciprocals = [1 / slope, -1 / slope] if form is LineForm.SLOPE_INTERCEPT else []
        slopes = [slope, *_distinct([-slope, *reciprocals], slope)]
        intercepts = [b, *_distinct([-b, a], b)]
        for some, more in _grid(slopes, intercepts):
            yield from (_written(each, intercept, form) for each in some for intercept in more)
        yield from (_written(slope, b + step, form) for step in _steps())
        return
    slopes = [slope, *_distinct(_wrong_slopes(slope, data.relation), slope)]
    x, y = data.points[0]
    # through the origin, standard form's C is 0, which only lines through it share
    if form is LineForm.SLOPE_INTERCEPT or (form is LineForm.STANDARD and b == 0):
        intercepts = [b, *_distinct([y + slope * x, -b, a], b)]
        for some, more in _grid(slopes, intercepts):
            yield from (_written(each, intercept, form) for each in some for intercept in more)
        yield from (_written(slope, b + step, form) for step in _steps())
        return
    # a point on the line, such as (-x₁, -y₁) on a line through the origin, gives the answer's
    # line, so the next one takes its place in the balanced set
    others = [point for point in ((-x, -y), (y, x)) if _through(slope, point, form).line != line]
    points: list[Point] = [(x, y), *others]
    nearby: Iterable[Point] = ((x, y + step) for step in _steps())
    for some, others in _grid(slopes, points):
        yield from (_through(each, point, form) for each in some for point in others)
    yield from (_through(slope, point, form) for point in nearby)


def _grid[T](slopes: list[Fraction], others: list[T]) -> Iterator[tuple[list[Fraction], list[T]]]:
    """
    Yield the groups of slopes and points or intercepts to pair, in order: the first two of
    each, which give the balanced set; the other slopes with the first two of ``others``; then
    every slope with the rest of ``others``.
    """
    yield slopes[:2], others[:2]
    yield slopes[2:], others[:2]
    yield slopes, others[2:]


def _wrong_slopes(slope: Fraction, relation: Relation | None) -> list[Fraction]:
    """
    Return the wrong slopes for a line with ``slope`` through a point, in the order
    ``_equation_mistakes`` lists them.
    """
    match relation:
        case Relation.PARALLEL:
            return [-1 / slope, 1 / slope, -slope]
        case Relation.PERPENDICULAR:
            return [-slope, 1 / slope, -1 / slope]
        case _:
            return [1 / slope, -slope, -1 / slope]


def _level_mistakes(data: LineQuestionData, form: LineForm) -> Iterator[LineAnswer]:
    """
    Yield wrong equations for a vertical or horizontal line through the point (h, k) shown: for
    y = k, x = k, then y = h and x = h; for x = h, y = h, then x = k and y = k; then nearby lines
    in ``form``. x = and y = confused and the point's other coordinate used are STAAR's two
    commonest mistakes here.
    """
    h, k = data.points[0]
    own, other = (k, h) if form is LineForm.HORIZONTAL else (h, k)
    swapped = LineForm.VERTICAL if form is LineForm.HORIZONTAL else LineForm.HORIZONTAL
    for each in (form, swapped):
        yield from (Equation(_level(each, number), each) for number in (own, other))
    yield from (Equation(_level(form, own + step), form) for step in _steps())


def _level(form: LineForm, number: int) -> Line:
    """Return x = ``number`` for the vertical form, or y = ``number``."""
    if form is LineForm.VERTICAL:
        return line_from(Fraction(1), Fraction(0), Fraction(number))
    return line_from(Fraction(0), Fraction(1), Fraction(number))


def _written(slope: Fraction, intercept: Fraction, form: LineForm) -> Equation:
    """Return the line with ``slope`` and ``intercept``, in ``form``."""
    return Equation(line_from(-slope, Fraction(1), intercept), form)


def _through(slope: Fraction, point: Point, form: LineForm) -> Equation:
    """
    Return the line with ``slope`` through ``point``, in ``form``, which in point-slope form is
    written through ``point``.
    """
    x, y = point
    line = line_from(-slope, Fraction(1), y - slope * x)
    return Equation(line, form, point if form is LineForm.POINT_SLOPE else None)


def _distinct(values: Sequence[Fraction], answer: Fraction) -> list[Fraction]:
    """Return ``values`` without ``answer`` or repeats, in order."""
    return list(dict.fromkeys(value for value in values if value != answer))


def _point_mistakes(
    answer: LineAnswer, b: Fraction | None, a: Fraction | None, asked: LineFeature
) -> Iterator[LineAnswer]:
    """
    Yield wrong ordered pairs for an intercept ``answer``, (0, b) or (a, 0), ending with nearby
    points on the same axis, so a point off it never gives the answer away.
    """
    if not isinstance(answer, tuple):
        raise ValueError(f"{answer} isn't an ordered pair.")
    x, y = answer
    yield (y, x)
    for value in (b, a):
        if value is not None:
            yield (Fraction(0), value)
            yield (value, Fraction(0))
    yield (-x, -y)
    yield (-y, -x)
    for step in _steps():
        yield (x, y + step) if asked is LineFeature.Y_INTERCEPT else (x + step, y)


def _pair_mistakes(slope: Fraction, b: Fraction, a: Fraction | None) -> Iterator[LineAnswer]:
    """Yield wrong slopes and y-intercepts for a line with ``slope`` and intercepts ``b``, ``a``."""
    reciprocal = 1 / slope if slope else None
    if reciprocal is not None:
        yield (reciprocal, b)
    if a is not None:
        yield (slope, a)
        if reciprocal is not None:
            yield (reciprocal, a)
    yield (-slope, b)
    yield (slope, -b)
    yield (-slope, -b)
    for step in _steps():
        yield (slope, b + step)


def _numbers(*values: Fraction | None) -> Iterator[LineAnswer]:
    """Yield each of ``values`` that is a number; ``None`` stands for a mistake that has none."""
    yield from (value for value in values if value is not None)


def _opposite(value: Fraction | None) -> Fraction | None:
    return None if value is None else -value


def _nearby(value: Fraction) -> Iterator[LineAnswer]:
    """Yield the numbers 1, 2, 3 and so on above and below ``value``, nearest first."""
    for step in _steps():
        yield value + step


def _steps() -> Iterator[int]:
    """Yield 1, -1, 2, -2 and so on."""
    for size in count(1):
        yield size
        yield -size


def _writable(choice: LineAnswer, numbers: NumberStyle) -> bool:
    """
    Return whether ``choice`` can be written in ``numbers``: in decimals, only if they end. An
    equation shows its slope and y-intercept in slope-intercept form, its slope in point-slope
    form, its number as x = a or y = b, and only whole numbers in standard form.
    """
    if numbers is not NumberStyle.DECIMAL or choice is None:
        return True
    if isinstance(choice, Equation):
        line = choice.line
        shown = {
            LineForm.SLOPE_INTERCEPT: (line.slope, line.y_intercept),
            LineForm.POINT_SLOPE: (line.slope,),
            LineForm.VERTICAL: (line.x_intercept,),
            LineForm.HORIZONTAL: (line.y_intercept,),
        }.get(choice.form, ())
        return all(terminates(value) for value in shown if value is not None)
    values = choice if isinstance(choice, tuple) else (choice,)
    return all(terminates(value) for value in values)
