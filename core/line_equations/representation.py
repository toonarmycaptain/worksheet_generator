"""
Writing a line's numbers, points and equations, both inline and as pieces for a PDF to draw, and
what a question about a line asks: a feature of the line, or its equation in a form.

A ``Fraction`` among the pieces is drawn as a stacked fraction, which an inline fraction such as
-3/4x can't show unambiguously; a string is drawn as text. Signs are written outside fractions,
with the minus sign rather than a hyphen, and a coefficient of 1 is left out: y = x - 2, not
y = 1x + -2.
"""

from fractions import Fraction
from typing import assert_never

from core.line_equations.data import (
    X_AXIS,
    Y_AXIS,
    Equation,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestionData,
    Relation,
    Stated,
    Statement,
    answer_of,
    choice_row,
)
from core.written_numbers import (
    MINUS,
    NumberStyle,
    Piece,
    Pieces,
    format_number,
    inline,
    merge_pieces,
    number_pieces,
)

UNDEFINED = "undefined"  # a vertical line's slope
_ONE = "\N{SUBSCRIPT ONE}"

SLOPE_AND_INTERCEPTS_NAME = "Slope and Intercepts"
WRITING_LINEAR_EQUATIONS_NAME = "Writing Linear Equations"
GRAPHING_LINEAR_EQUATIONS_NAME = "Graphing Linear Equations"

# What each choice is called on the web page; a form shows what it looks like
FORM_NAMES = {
    LineForm.SLOPE_INTERCEPT: "Slope-intercept form (y = mx + b)",
    LineForm.STANDARD: "Standard form (Ax + By = C)",
    LineForm.POINT_SLOPE: f"Point-slope form (y {MINUS} y{_ONE} = m(x {MINUS} x{_ONE}))",
    LineForm.POINT_AND_SLOPE: "A point and the slope",
    LineForm.TWO_POINTS: "Two points",
    LineForm.VERTICAL: "Vertical lines (x = a)",
    LineForm.HORIZONTAL: "Horizontal lines (y = b)",
    LineForm.TABLE: "A table",
    LineForm.GRAPH: "A graph",
    LineForm.SLOPE_AND_INTERCEPT: "The slope and y-intercept",
    LineForm.INTERCEPTS: "The x- and y-intercepts",
}
# What each thing graphing lines asks is called on the web page
GRAPHING_ASKED_NAMES = {LineForm.GRAPH: "Graph the line", LineForm.TABLE: "Complete the table"}
FEATURE_NAMES = {
    LineFeature.SLOPE: "Slope",
    LineFeature.RATE_OF_CHANGE: "Rate of change",
    LineFeature.Y_INTERCEPT: "y-intercept",
    LineFeature.X_INTERCEPT: "x-intercept",
    LineFeature.ZERO: "Zero",
    LineFeature.SLOPE_AND_Y_INTERCEPT: "Slope and y-intercept",
}
# What each thing an equation is written from is called on the web page: a form, as above, or a
# relation
EQUATION_GIVEN_NAMES: dict[LineForm | Relation, str] = {
    **{form: FORM_NAMES[form] for form in LineForm if form in FORM_NAMES},
    Relation.PARALLEL: "A point and a parallel line",
    Relation.PERPENDICULAR: "A point and a perpendicular line",
}
NUMBER_STYLE_NAMES = {
    NumberStyle.FRACTION: "Fractions (5/2)",
    NumberStyle.DECIMAL: "Decimals (2.5)",
    NumberStyle.MIXED_NUMBER: "Mixed numbers (2 1/2)",
}

# What a question calls a line shown in a table
_TABLE_LINE = "the line through the points in this table"

# What each feature is called in a question
_FEATURE_WORDS = {
    LineFeature.SLOPE: "slope",
    LineFeature.RATE_OF_CHANGE: "rate of change",
    LineFeature.Y_INTERCEPT: "y-intercept",
    LineFeature.X_INTERCEPT: "x-intercept",
    LineFeature.ZERO: "zero",
    LineFeature.SLOPE_AND_Y_INTERCEPT: "slope and y-intercept",
}

# What a question asking for a vertical or horizontal line's equation adds for each statement
_STATEMENT_WORDS = {
    Statement.SLOPE: ", and give its slope:",
    Statement.X_AXIS: ", and say whether it is parallel or perpendicular to the x-axis:",
}
# The labels of the two blanks a question with two answers has: the slope and y-intercept, or a
# vertical or horizontal line's equation and its statement
_BLANK_LABELS = {
    Statement.SLOPE: ("Equation", "Slope"),
    Statement.X_AXIS: ("Equation", "Parallel or perpendicular"),
}
SLOPE_AND_INTERCEPT_LABELS = ("Slope", "y-intercept")

# What each form is called in a question that asks for an equation in it
_FORM_WORDS = {
    LineForm.SLOPE_INTERCEPT: "slope-intercept form",
    LineForm.STANDARD: "standard form",
    LineForm.POINT_SLOPE: "point-slope form",
}


def point_pieces(point: tuple[Fraction | int, Fraction | int], style: NumberStyle) -> Pieces:
    """Return ``point`` as an ordered pair, such as (5/2, 0), its numbers written in ``style``."""
    x, y = point
    return merge_pieces(("(", *number_pieces(x, style), ", ", *number_pieces(y, style), ")"))


def equation_pieces(
    line: Line,
    form: LineForm,
    *,
    numbers: NumberStyle = NumberStyle.FRACTION,
    function: str | None = None,
    point: tuple[int, int] | None = None,
    solved_for_y: bool = False,
) -> Pieces:
    """
    Return the equation of ``line`` in ``form``, its numbers written in ``numbers``:

    - slope-intercept: y = -3/4x + 2, or with ``function`` "f", f(x) = -3/4x + 2;
    - standard: 3x + 4y = 8, in whole numbers;
    - point-slope through ``point`` (-4, 5): y - 5 = -3/4(x + 4), or with ``solved_for_y``,
      y = -3/4(x + 4) + 5;
    - vertical: x = -4;
    - horizontal: y = 2.5, or f(x) = 2.5.

    A term whose number is 0 is left out, so a line through the origin is y = 3x, and a point
    on an axis gives y = 2(x - 3) in point-slope form. With a slope of 1, point-slope form has
    no brackets, y - 3 = x - 1, except solved for y: y = (x - 1) + 3.

    Raises ``ValueError`` for a form that isn't an equation (a point and slope, two points), for
    a vertical line in slope-intercept or point-slope form, for point-slope form without
    ``point``, and for a line that isn't vertical or horizontal in that form.
    """
    lhs = f"{function}(x)" if function else "y"
    match form:
        case (
            LineForm.POINT_AND_SLOPE
            | LineForm.TWO_POINTS
            | LineForm.TABLE
            | LineForm.GRAPH
            | LineForm.SLOPE_AND_INTERCEPT
            | LineForm.INTERCEPTS
        ):
            raise ValueError(f"A line given by {form} isn't an equation.")
        case LineForm.SLOPE_INTERCEPT:
            slope, intercept = _slope_and_intercept(line, form)
            if slope == 0:
                return merge_pieces((f"{lhs} = ", *number_pieces(intercept, numbers)))
            return merge_pieces(
                (f"{lhs} = ", *_coefficient(slope, numbers), "x", *_added(intercept, numbers))
            )
        case LineForm.STANDARD:
            return _standard(line)
        case LineForm.POINT_SLOPE:
            slope, _ = _slope_and_intercept(line, form)
            if point is None:
                raise ValueError("Point-slope form needs a point.")
            x, y = point
            if solved_for_y:
                inner: Pieces = ("(x", *_added(-x, numbers), ")") if x else ("x",)
                right_side = (*_coefficient(slope, numbers), *inner, *_added(y, numbers))
                return merge_pieces((f"{lhs} = ", *right_side))
            left = (lhs, *_added(-y, numbers))
            if x == 0 or slope == 1:
                right: Pieces = ("x", *_added(-x, numbers))
            else:
                right = ("(x", *_added(-x, numbers), ")")
            return merge_pieces((*left, " = ", *_coefficient(slope, numbers), *right))
        case LineForm.VERTICAL:
            if line.b != 0:
                raise ValueError(f"{line} isn't a vertical line.")
            return merge_pieces(("x = ", *number_pieces(Fraction(line.c, line.a), numbers)))
        case LineForm.HORIZONTAL:
            if line.a != 0:
                raise ValueError(f"{line} isn't a horizontal line.")
            return merge_pieces((f"{lhs} = ", *number_pieces(Fraction(line.c, line.b), numbers)))
        case _:
            assert_never(form)


def instruction(data: LineQuestionData) -> str:
    """
    Return what the question asks, such as "Find the slope of this line:", for its given form
    to follow, as ``given_pieces`` writes it.

    A line is a function when its equation is in function notation or its zero is asked:
    "Find the zero of this function:". Two points, a point and slope, and a table name the line
    by them: "Find the y-intercept of the line through these points:", "Find the slope of the
    line through the points in this table:". A graph is "this line", as an equation is. An
    intercept asked as a point adds "as an ordered pair". A question that asks for an equation
    is worded by ``_equation_instruction``, and one that asks to graph a line or complete a
    table by ``_graphing_instruction``.
    """
    if data.asked in (LineForm.GRAPH, LineForm.TABLE):
        return _graphing_instruction(data)
    if isinstance(data.asked, LineForm):
        return _equation_instruction(data, data.asked)
    function = data.function is not None or data.asked is LineFeature.ZERO
    match data.given:
        case LineForm.TWO_POINTS:
            noun = "linear function" if function else "line"
            subject = f"the {noun} through these points"
        case LineForm.POINT_AND_SLOPE:
            noun = "linear function" if function else "line"
            subject = f"the {noun} with this point and slope"
        case LineForm.TABLE:
            subject = "the linear function in this table" if function else _TABLE_LINE
        case _:
            subject = "this function" if function else "this line"
    shape = " as an ordered pair" if data.as_point else ""
    return f"Find the {_FEATURE_WORDS[data.asked]} of {subject}{shape}:"


def _graphing_instruction(data: LineQuestionData) -> str:
    """
    Return what a question that asks to graph a line or complete a table of it asks, for its
    given to follow: "Graph this equation:", "Graph the line through these points:", "Graph the
    line with these intercepts:", "Complete the table for this equation:", "Complete the table
    for this line:" for a graph. A graph or table to choose is asked as STAAR asks it: "Which
    graph represents this equation?", "Which table represents this line?".
    """
    match data.given:
        case LineForm.TWO_POINTS:
            subject = "the line through these points"
        case LineForm.POINT_AND_SLOPE:
            subject = "the line with this point and slope"
        case LineForm.SLOPE_AND_INTERCEPT:
            subject = "the line with this slope and y-intercept"
        case LineForm.INTERCEPTS:
            subject = "the line with these intercepts"
        case LineForm.GRAPH:
            subject = "this line"
        case _:
            subject = "this equation"
    if data.chosen:
        picture = "graph" if data.asked is LineForm.GRAPH else "table"
        return f"Which {picture} represents {subject}?"
    if data.asked is LineForm.TABLE:
        return f"Complete the table for {subject}:"
    return f"Graph {subject}:"


def _equation_instruction(data: LineQuestionData, form: LineForm) -> str:
    """
    Return what a question that asks for an equation in ``form`` asks, for its given to follow:
    "Write this equation in standard form:", "Write the equation of the line through these
    points in slope-intercept form:", or with a relation, "Write the equation of the line through
    (-3, -6) that is parallel to this line, in point-slope form:".

    x = a and y = b aren't named, since naming them gives the answer's shape away. Point-slope
    form from two points is written through the first point, so the question says so; from a
    table or a graph, through the point ``points`` holds, which the question names: "Write the
    equation of this line in point-slope form, using the point (-4, 5):". A line
    parallel or perpendicular to an axis has its point shown below instead: "Write the equation
    of the line through this point that is parallel to the x-axis:". A statement asked too adds
    its words: "Write the equation of the line through these points, and give its slope:".
    """
    words = _equation_words(data, form)
    if data.statement is None:
        return words
    return words.removesuffix(":") + _STATEMENT_WORDS[data.statement]


def _equation_words(data: LineQuestionData, form: LineForm) -> str:
    """Return what ``_equation_instruction`` asks, without a statement's words."""
    in_form = f" in {_FORM_WORDS[form]}" if form in _FORM_WORDS else ""
    if data.relation is not None:
        # an axis's line is vertical or horizontal, the other lines neither (see the generator)
        relation = "parallel" if data.relation is Relation.PARALLEL else "perpendicular"
        if data.reference in (X_AXIS, Y_AXIS):
            axis = "x-axis" if data.reference == X_AXIS else "y-axis"
            subject = f"the line through this point that is {relation} to the {axis}"
            return f"Write the equation of {subject}:"
        (point,) = data.points
        through = inline(point_pieces(point, data.numbers))
        return (
            f"Write the equation of the line through {through} that is {relation} to this "
            f"line,{in_form}:"
        )
    match data.given:
        case LineForm.TWO_POINTS:
            using = ", using the first point" if form is LineForm.POINT_SLOPE else ""
            return f"Write the equation of the line through these points{in_form}{using}:"
        case LineForm.POINT_AND_SLOPE:
            return f"Write the equation of the line with this point and slope{in_form}:"
        case LineForm.TABLE | LineForm.GRAPH:
            using = ""
            if form is LineForm.POINT_SLOPE:
                using = f", using the point {inline(point_pieces(data.points[0], data.numbers))}"
            subject = _TABLE_LINE if data.given is LineForm.TABLE else "this line"
            return f"Write the equation of {subject}{in_form}{using}:"
        case _:
            return f"Write this equation{in_form}:"


def given_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the line as the question shows it: its equation in the given form, its two points,
    "(-4, 5) and (4, -1)", its point and slope, "point (-4, 5), slope -3/4", where a vertical
    line's slope is "undefined", its slope and y-intercept, "slope -2/3, y-intercept 2", or its
    intercepts, "x-intercept 3, y-intercept 2".

    With a relation, it's the line the answer is parallel or perpendicular to, in the given form,
    or for an axis, the point the answer passes through: "(3, 7)". A table and a graph aren't
    written, so they have no pieces: ``table_cells`` gives a table's text, and the data holds a
    graph's grid and points.
    """
    if data.reference is not None:
        if data.reference in (X_AXIS, Y_AXIS):
            (point,) = data.points
            return point_pieces(point, data.numbers)
        return equation_pieces(data.reference, data.given, numbers=data.numbers)
    match data.given:
        case LineForm.TWO_POINTS:
            first, second = data.points
            return merge_pieces(
                (*point_pieces(first, data.numbers), " and ", *point_pieces(second, data.numbers))
            )
        case LineForm.POINT_AND_SLOPE:
            slope = data.answer.slope
            (point,) = data.points
            return merge_pieces(
                (
                    "point ",
                    *point_pieces(point, data.numbers),
                    ", slope ",
                    *((UNDEFINED,) if slope is None else number_pieces(slope, data.numbers)),
                )
            )
        case LineForm.SLOPE_AND_INTERCEPT:
            slope, intercept = _slope_and_intercept(data.answer, data.given)
            return merge_pieces(
                (
                    "slope ",
                    *number_pieces(slope, data.numbers),
                    ", y-intercept ",
                    *number_pieces(intercept, data.numbers),
                )
            )
        case LineForm.INTERCEPTS:
            x_intercept, y_intercept = data.answer.x_intercept, data.answer.y_intercept
            if x_intercept is None or y_intercept is None:
                raise ValueError(f"{data.answer} doesn't cross both axes.")
            return merge_pieces(
                (
                    "x-intercept ",
                    *number_pieces(x_intercept, data.numbers),
                    ", y-intercept ",
                    *number_pieces(y_intercept, data.numbers),
                )
            )
        case LineForm.TABLE | LineForm.GRAPH:
            return ()
        case _:
            return equation_pieces(
                data.answer,
                data.given,
                numbers=data.numbers,
                function=data.function,
                point=data.points[0] if data.points else None,
                solved_for_y=data.solved_for_y,
            )


def choice_table_cells(
    data: LineQuestionData, line: Line
) -> tuple[tuple[str | Pieces, ...], tuple[str | Pieces, ...]]:
    """
    Return a table of ``line`` to choose, at the question's x-values, as ``table_cells`` writes a
    table: each row as ``choice_row`` gives it, so a vertical line's table has its number in
    every row of x, with the x-values as its y-values.
    """
    rows = [choice_row(line, x) for x in data.table_xs]
    return (
        ("x", *(number_pieces(x, data.numbers) for x, _ in rows)),
        ("y", *(number_pieces(y, data.numbers) for _, y in rows)),
    )


def table_cells(
    data: LineQuestionData, filled: bool = False
) -> tuple[tuple[str | Pieces | None, ...], tuple[str | Pieces | None, ...]]:
    """
    Return a table's two lines, its x-values and its y-values, each headed by its variable:
    "x", then ("-4",), ("1",), and "y", then ("5",), ("1.5",), with minus signs. Each value is
    written in the question's number style, so a half is 1.5 or a stacked 3/2. A table to
    complete has ``None`` for each cell ``table_blanks`` leaves out, unless ``filled``, as the
    answer key fills them.
    """
    line = data.answer
    ys = [Fraction(line.c - line.a * x, line.b) for x in data.table_xs]
    blanks = data.table_blanks if data.table_blanks and not filled else (None,) * len(ys)
    return (
        (
            "x",
            *(
                None if blank == 0 else number_pieces(x, data.numbers)
                for x, blank in zip(data.table_xs, blanks, strict=True)
            ),
        ),
        (
            "y",
            *(
                None if blank == 1 else number_pieces(y, data.numbers)
                for y, blank in zip(ys, blanks, strict=True)
            ),
        ),
    )


def blank_labels(data: LineQuestionData) -> tuple[str, str] | None:
    """
    Return the labels of the two blanks a free-response question with two answers has: "Slope"
    and "y-intercept", "Equation" and "Slope", or "Equation" and "Parallel or perpendicular";
    or ``None`` for a question with one answer.
    """
    if data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT:
        return SLOPE_AND_INTERCEPT_LABELS
    if data.statement is not None:
        return _BLANK_LABELS[data.statement]
    return None


def answer_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the answer to ``data`` for the answer key, as ``choice_pieces`` writes it, except the
    slope and y-intercept, which are "slope -3/4, y-intercept 3", and a statement, which is
    "x = -4, slope undefined" or "y = 3, parallel to the x-axis".
    """
    answer = answer_of(data)
    if isinstance(answer, Stated):
        return _stated(answer, data.numbers, short=True)
    if data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT and isinstance(answer, tuple):
        slope, intercept = answer
        return merge_pieces(
            (
                "slope ",
                *number_pieces(slope, data.numbers),
                ", y-intercept ",
                *number_pieces(intercept, data.numbers),
            )
        )
    return choice_pieces(data, answer)


def choice_pieces(data: LineQuestionData, choice: LineAnswer) -> Pieces:
    """
    Return ``choice``, the answer to ``data`` or a wrong one, as a multiple-choice option shows
    it: a number in the question's style, "undefined" for ``None``, an ordered pair, such as
    (0, 2), an equation, as ``equation_pieces`` writes it, or for the slope and y-intercept, a
    statement: "The slope is -3/4, and the y-intercept is 3.", as for a vertical or horizontal
    line: "The equation of the line is x = -4, and the slope is undefined."

    Raises ``ValueError`` for a graph or table, which is drawn, not written.
    """
    if choice is None:
        return (UNDEFINED,)
    if isinstance(choice, Stated):
        return _stated(choice, data.numbers, short=False)
    if isinstance(choice, Equation) and choice.form in (LineForm.GRAPH, LineForm.TABLE):
        raise ValueError(f"A {choice.form} to choose is drawn, not written.")
    if isinstance(choice, Equation):
        return equation_pieces(choice.line, choice.form, numbers=data.numbers, point=choice.point)
    if not isinstance(choice, tuple):
        return number_pieces(choice, data.numbers)
    if data.asked is not LineFeature.SLOPE_AND_Y_INTERCEPT:
        return point_pieces(choice, data.numbers)
    slope, intercept = choice
    return merge_pieces(
        (
            "The slope is ",
            *number_pieces(slope, data.numbers),
            ", and the y-intercept is ",
            *number_pieces(intercept, data.numbers),
            ".",
        )
    )


def tile_answer_pieces(data: LineQuestionData) -> Pieces:
    """
    Return the answer to ``data`` as a self-check tile's box shows it: as ``answer_pieces``
    writes it, except the slope and y-intercept, which are labelled "m = -3/4, b = 3".
    """
    answer = answer_of(data)
    if data.asked is LineFeature.SLOPE_AND_Y_INTERCEPT and isinstance(answer, tuple):
        slope, intercept = answer
        return merge_pieces(
            (
                "m = ",
                *number_pieces(slope, data.numbers),
                ", b = ",
                *number_pieces(intercept, data.numbers),
            )
        )
    return answer_pieces(data)


def _stated(stated: Stated, numbers: NumberStyle, short: bool) -> Pieces:
    """
    Return a statement about a vertical or horizontal line: "The equation of the line is
    x = -4, and the slope is undefined.", "…, and the line is parallel to the x-axis.", or
    ``short``, "x = -4, slope undefined", "y = 3, parallel to the x-axis".
    """
    equation = equation_pieces(stated.equation.line, stated.equation.form, numbers=numbers)
    about = stated.about
    if isinstance(about, Relation):
        fact = f"{about} to the x-axis"
        long = f", and the line is {fact}."
    else:
        fact = f"slope {UNDEFINED if about is None else format_number(about, numbers)}"
        long = f", and the {fact.replace(' ', ' is ', 1)}."
    if short:
        return merge_pieces((*equation, f", {fact}"))
    return merge_pieces(("The equation of the line is ", *equation, long))


def _slope_and_intercept(line: Line, form: LineForm) -> tuple[Fraction, Fraction]:
    """Return the slope and y-intercept of ``line``, which can't be vertical in ``form``."""
    if line.slope is None or line.y_intercept is None:
        raise ValueError(f"A vertical line can't be written in {form} form.")
    return line.slope, line.y_intercept


def _coefficient(value: Fraction, numbers: NumberStyle) -> Pieces:
    """Return ``value`` as the coefficient of a variable: none for 1, and only a sign for -1."""
    if abs(value) == 1:
        return (MINUS,) if value < 0 else ()
    return number_pieces(value, numbers)


def _added(value: Fraction | int, numbers: NumberStyle) -> Pieces:
    """Return ``value`` added to a term, such as " + 2" or " - 3/4", or nothing for 0."""
    value = Fraction(value)
    if value == 0:
        return ()
    sign = f" {MINUS} " if value < 0 else " + "
    return (sign, *number_pieces(abs(value), numbers))


def _standard(line: Line) -> Pieces:
    """Return Ax + By = C, leaving out a term whose coefficient is 0."""
    pieces: list[Piece] = []
    for coefficient, variable in ((line.a, "x"), (line.b, "y")):
        if coefficient == 0:
            continue
        if pieces:
            pieces.append(f" {MINUS} " if coefficient < 0 else " + ")
        elif coefficient < 0:
            pieces.append(MINUS)
        size = abs(coefficient)
        pieces.append(variable if size == 1 else f"{size:,}{variable}")
    return merge_pieces((*pieces, " = ", *number_pieces(line.c, NumberStyle.FRACTION)))
