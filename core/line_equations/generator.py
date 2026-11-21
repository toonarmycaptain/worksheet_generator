"""
Random generation of questions about a line: its slope or an intercept, from an equation, a point
and slope, two points, a table or a graph; or its equation in a form, from those or from a
parallel or perpendicular line and a point.

Each line is built from its answer, never drawn and then rejected: a slope, then a y-intercept
that gives the line points with whole-number coordinates; or the number of a vertical or
horizontal line. Each is drawn from a list of the numbers that meet the options, so nothing
loops, and options that leave too few lines are refused before anything is drawn, as
``count_possible_lines`` counts them.
"""

import random
from collections import Counter
from collections.abc import Callable, Hashable, Iterator, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import chain, combinations, islice, pairwise, product
from math import ceil, gcd
from typing import Literal

from core.line_equations.data import (
    EQUATION_FORMS,
    EQUATION_GIVENS,
    FEATURE_GIVENS,
    GRAPHING_ASKED,
    GRAPHING_GIVENS,
    X_AXIS,
    Y_AXIS,
    Equation,
    Grid,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestion,
    LineQuestionData,
    Point,
    Relation,
    Statement,
    answer_of,
    choice_row,
    line_answer,
    line_from,
)
from core.line_equations.wrong_answers import mistake_sets, wrong_answers, wrong_lines
from core.question import FreeResponse, Question, multiple_choice
from core.written_numbers import NumberStyle, terminates

DEFAULT_LARGEST_COORDINATE = 10  # STAAR's grids mostly run to ±9 or ±10
DEFAULT_LARGEST_DENOMINATOR = 5
FUNCTION_NAMES = ("f", "g", "h")

# Which way a line runs
type Slant = Literal["sloped", "horizontal", "vertical"]

# How a line shown by its points (two points, a graph or a table) runs, each as likely as it is
# frequent here: one time in forty horizontal and one in forty vertical, so about one in twenty
# is either, among the slants the forms given and the feature asked allow. A table is never of
# a vertical line, which isn't a function.
SHOWN_SLANTS: tuple[Slant, ...] = ("sloped",) * 38 + ("horizontal", "vertical")
TABLE_ROWS = (4, 5, 6)  # how many rows a table has, each as likely, as many as its line allows
# The fewest rows four tables to choose can share, as in STAAR's tables of 3 to 6 pairs: fewer
# than a given table's, since a steep line's table and its reciprocal's share few rows
CHOICE_TABLE_ROWS = 3
# Whether a table's x-values go up in equal steps (of 2 or 5, or of the gap between the rows its
# line allows): one time in four. Otherwise they're unevenly spaced, as in most of STAAR's.
EVEN_TABLES = (True, False, False, False)
EVEN_STEPS = (2, 5)
# Whether a table has a row at x = 0: one time in five, whatever is asked. When the x-intercept
# or zero is asked, the row where y = 0 is allowed as often, and left out otherwise.
ZERO_ROWS = (True,) + (False,) * 4
# Whether two points come with a blank grid beside them to work on, while that's allowed: even
# chance, as in STAAR (2 of 5 A.3(A) items, 2 of 3 in 8.5(I))
BLANK_GRIDS = (True, False)
GRID_LINES = 12  # a grid has at most this many gridlines beyond the axis, each way
# Which cell of a row a table to complete leaves out, each as likely: 0 for x, 1 for y
TABLE_BLANKS = (0, 1)
# Whether a sloped line passes through the origin: one time in twenty
THROUGH_ORIGIN = (True,) + (False,) * 19
# Whether the one point an equation is written from is where the line crosses the x-axis, as in
# A.2 2019 Q10 ("crosses the x-axis at 36"): one time in ten, which gives y = m(x - r) in
# point-slope form
X_AXIS_POINT = (True,) + (False,) * 9
# The forms a line a parallel or perpendicular line is found from is written in, each as likely
REFERENCE_FORMS = (LineForm.SLOPE_INTERCEPT, LineForm.STANDARD)
# Whether a vertical or horizontal line's equation asks for a statement too, while statements are
# allowed: even chance, as in STAAR (3 of 6 A.2(G) items)
STATEMENT_SHARE = (False, True)
# How many more wrong lines a table to choose looks through for one whose table agrees with the
# answer's in a row, once it has its other wrong lines
SHARED_ROW_SEARCH = 40

# The features a line of each slant has. A vertical line's slope is undefined, and it isn't a
# function, so it has no rate of change or zero; a horizontal line never crosses the x-axis.
_FEATURES_OF: dict[Slant, tuple[LineFeature, ...]] = {
    "sloped": tuple(LineFeature),
    "horizontal": (
        LineFeature.SLOPE,
        LineFeature.RATE_OF_CHANGE,
        LineFeature.Y_INTERCEPT,
        LineFeature.SLOPE_AND_Y_INTERCEPT,
    ),
    "vertical": (LineFeature.SLOPE, LineFeature.X_INTERCEPT),
}
# What a question shows of its line besides an equation: that many points with whole-number
# coordinates off the axes, a table, or a graph through two marked points
type Shown = Literal[0, 1, 2, "table", "graph"]
# What each form shows; the other forms show nothing more, and a relation shows the one point
# the line asked for passes through
_SHOWN: dict[LineForm, Shown] = {
    LineForm.POINT_SLOPE: 1,
    LineForm.POINT_AND_SLOPE: 1,
    LineForm.TWO_POINTS: 2,
    LineForm.TABLE: "table",
    LineForm.GRAPH: "graph",
}
# The kind of answer each feature has: features of one kind give the same number for a line
_ANSWER_KINDS = {
    LineFeature.SLOPE: LineFeature.SLOPE,
    LineFeature.RATE_OF_CHANGE: LineFeature.SLOPE,
    LineFeature.Y_INTERCEPT: LineFeature.Y_INTERCEPT,
    LineFeature.X_INTERCEPT: LineFeature.X_INTERCEPT,
    LineFeature.ZERO: LineFeature.X_INTERCEPT,
    LineFeature.SLOPE_AND_Y_INTERCEPT: LineFeature.SLOPE_AND_Y_INTERCEPT,
}
# Which way each form's line runs when no share is drawn; the other forms' lines are sloped. An
# equation asked in a form is of a line that runs this way too.
_FORM_SLANTS: dict[LineForm, Slant] = {
    LineForm.VERTICAL: "vertical",
    LineForm.HORIZONTAL: "horizontal",
}
# The form that shows a line of each slant but "sloped"; two points give a line of that slant only
# while its form is ticked
_FORM_OF: dict[Slant, LineForm] = {
    "vertical": LineForm.VERTICAL,
    "horizontal": LineForm.HORIZONTAL,
}
# The forms that show a point, so an equation can be written through it in point-slope form
_SHOWS_POINT = (
    LineForm.POINT_AND_SLOPE,
    LineForm.TWO_POINTS,
    LineForm.TABLE,
    LineForm.GRAPH,
    *Relation,
)
# The givens a table to complete is made from: an equation, or a graph
_TABLED_FROM = (
    LineForm.SLOPE_INTERCEPT,
    LineForm.STANDARD,
    LineForm.POINT_SLOPE,
    LineForm.HORIZONTAL,
    LineForm.GRAPH,
)
# The intercepts each given shows, which must be on gridlines to plot
_ON_GRIDLINES = {
    LineForm.SLOPE_AND_INTERCEPT: frozenset({LineFeature.Y_INTERCEPT}),
    LineForm.INTERCEPTS: frozenset({LineFeature.Y_INTERCEPT, LineFeature.X_INTERCEPT}),
}
# The features a table's row where y = 0 would show
_X_INTERCEPT_FEATURES = (LineFeature.X_INTERCEPT, LineFeature.ZERO)


@dataclass(frozen=True)
class _Rules:
    """
    What one question's line must meet: the options, whether its intercepts are whole, its
    numbers decimals and, if it's sloped, whether it passes through the origin (``None`` for
    either), and the lines already on the sheet, ``used``, which it mustn't repeat. With
    different answers, its answer to ``asked``, as a point if ``as_point``, mustn't be one of
    those ``taken``.

    With a ``relation``, a sloped line must have a line it is parallel or perpendicular to that
    meets the same rules, apart from ``used``, ``taken`` and ``origin``. With ``x_axis_point``,
    its one point shown is where it crosses the x-axis, which must be a whole number other than 0.

    With ``on_grid``, the line is graphed on a grid, so it passes through two places the grid's
    gridlines cross, inside its edge, and any points shown are such places. The intercepts in
    ``on_gridlines`` must be on a gridline, so they can be plotted. With ``table``, the line
    also has rows enough for a table, as ``_fits_table`` says.
    """

    largest_coordinate: int
    largest_denominator: int
    whole: bool
    decimal: bool
    origin: bool | None
    used: set[Line]
    asked: LineFeature = LineFeature.SLOPE
    as_point: bool = False
    taken: set[LineAnswer] | frozenset[LineAnswer] = frozenset()
    relation: Relation | None = None
    x_axis_point: bool = False
    on_grid: bool = False
    on_gridlines: frozenset[LineFeature] = frozenset()
    table: bool = False


def generate_line_questions(
    count: int,
    givens: Sequence[LineForm],
    features: Sequence[LineFeature],
    *,
    largest_coordinate: int = DEFAULT_LARGEST_COORDINATE,
    largest_denominator: int = DEFAULT_LARGEST_DENOMINATOR,
    whole_intercepts: bool = False,
    number_styles: Sequence[NumberStyle] = (NumberStyle.FRACTION, NumberStyle.DECIMAL),
    as_point_choices: Sequence[bool] = (False, True),
    wrong_answer_count: int = 0,
    distinct_answers: bool = False,
    blank_grids: bool = False,
) -> list[LineQuestion]:
    """
    Generate ``count`` questions about lines, each asking a feature from ``features`` of a line
    shown in a form from ``givens``.

    Each question takes the next pair of a form and a feature from a shuffled deck of the pairs
    that can be asked, so no pair repeats on a sheet until all of them have been used. A pair
    can't be asked when the form shows the feature (a point and slope, the slope), or when its
    line can't have the feature (x = a, the y-intercept).

    Each line meets these rules:
    - each coordinate shown, and each intercept, is from -``largest_coordinate`` to
      ``largest_coordinate``;
    - a slope's numerator is at most ``largest_coordinate``, and the slope and intercepts have
      denominators of at most ``largest_denominator``;
    - points shown have whole-number coordinates and lie on neither axis, so none is an
      intercept. A graph's two marked points are also where its gridlines cross, inside its
      edge, as ``_marked_points`` finds them;
    - a table has rows as ``_table_xs`` picks them: whole-number x-values, each y-value a whole
      number or a half, all from -``largest_coordinate`` to ``largest_coordinate``;
    - with ``whole_intercepts``, both intercepts are whole numbers. Without it, they are any
      numbers the other rules allow, whole ones included;
    - a sloped line passes through the origin as ``THROUGH_ORIGIN`` has it, one time in twenty;
    - x = a and y = b show vertical and horizontal lines. A line through two points or on a
      graph is vertical only while x = a is among ``givens``, and a line through two points, on
      a graph or in a table horizontal only while y = b is, as ``SHOWN_SLANTS`` has it, when the
      feature asked allows it. The other forms show lines that are neither;
    - no line repeats on a sheet. The shares drawn for a question (through the origin, a
      vertical or horizontal line through two points, and decimals when fractions are allowed
      too) give way when their lines are used up, so a question can always take any line its
      form can show. A pair whose lines are used up gives way to another, but
      ``count_possible_lines`` counts lines enough for each pair's share of the deck.
    A slope is drawn first, so each slope the rules allow is as likely as any other, then a
    y-intercept among those the rules allow with that slope.

    Each question's number style is drawn from ``number_styles``; a decimal question's slope and
    intercepts all terminate. An x- or y-intercept is asked as an ordered pair or a number as
    drawn from ``as_point_choices``: ``(False, True)``, with even chance, by default. An
    equation in slope-intercept form is in function notation with even chance, named from
    ``FUNCTION_NAMES``. A graph and a table are set out as ``_shown_data`` says; with
    ``blank_grids``, two points come with a blank grid beside them as ``BLANK_GRIDS`` has it.

    Raises ``ValueError`` if ``givens`` or ``features`` is empty, if ``givens`` has a form not in
    ``FEATURE_GIVENS``, if no pair can be asked, if ``largest_coordinate`` or
    ``largest_denominator`` is less than 1, if ``number_styles`` is empty or has mixed
    numbers, if ``as_point_choices`` is empty, if both ``wrong_answer_count`` and
    ``distinct_answers`` are given, or if ``count`` is more than ``count_possible_lines`` allows.

    With a non-zero ``wrong_answer_count``, each question is multiple choice among its answer and
    that many wrong answers, made by ``wrong_answers``. With ``distinct_answers``, as the
    self-check tiles case needs, no two questions have the same answer either: a question whose
    pair has no new line with a new answer takes the first other pair that has one.
    """
    if not as_point_choices:
        raise ValueError("Intercepts need asking as numbers, points or both.")
    if wrong_answer_count and distinct_answers:
        raise ValueError("Multiple-choice questions don't need different answers.")
    if not givens:
        raise ValueError("At least one form to show is needed.")
    if not features:
        raise ValueError("At least one feature to ask is needed.")
    for given in givens:
        if given not in FEATURE_GIVENS:
            raise ValueError(f"A line's features aren't asked of {given}.")
    _check_numbers(largest_coordinate, largest_denominator, number_styles)
    pairs = [pair for pair in product(givens, features) if can_ask(*pair)]
    if not pairs:
        raise ValueError("None of the forms given can show a line with the features asked.")
    possible = count_possible_lines(
        givens,
        features,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        distinct_answers=distinct_answers,
        limit=count,
    )
    if count > possible:
        different = "answers" if distinct_answers else "lines"
        raise ValueError(
            f"Cannot make {count} questions with different {different}: only {possible} possible."
        )

    def build(
        pair: tuple[LineForm, LineFeature], used: set[Line], taken: set[LineAnswer]
    ) -> LineQuestionData | None:
        given, asked = pair
        return _question_data(
            given,
            asked,
            givens,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=whole_intercepts,
            number_styles=number_styles,
            as_point_choices=as_point_choices,
            used=used,
            taken=taken if distinct_answers else None,
            blank_grids=blank_grids,
        )

    return _questions(count, pairs, build, wrong_answer_count)


def generate_equation_questions(
    count: int,
    givens: Sequence[LineForm | Relation],
    forms: Sequence[LineForm],
    *,
    largest_coordinate: int = DEFAULT_LARGEST_COORDINATE,
    largest_denominator: int = DEFAULT_LARGEST_DENOMINATOR,
    whole_intercepts: bool = False,
    number_styles: Sequence[NumberStyle] = (NumberStyle.FRACTION, NumberStyle.DECIMAL),
    wrong_answer_count: int = 0,
    blank_grids: bool = False,
    statements: bool = False,
) -> list[LineQuestion]:
    """
    Generate ``count`` questions that each ask for the equation of a line in a form from
    ``forms``, from a line given in a way from ``givens``: a form, or a relation, which shows a
    line the answer is parallel or perpendicular to and a point the answer passes through.

    Each question takes the next pair of a given and a form from a shuffled deck of the pairs
    that can be asked, as ``generate_line_questions`` does. ``can_write`` says which can.

    Each line meets the rules ``generate_line_questions`` lists, with these differences:
    - a line whose equation is asked as x = a is vertical, as y = b horizontal, and in any other
      form neither, so two points, a point and slope, a table or a graph give a vertical or
      horizontal line only when x = a or y = b is asked;
    - an equation in point-slope form from a table is written through its row ``points`` holds,
      and from a graph through its first marked point;
    - when the line is given by one point and doesn't pass through the origin, that point is
      where it crosses the x-axis one time in ten (``X_AXIS_POINT``), when it crosses at a whole
      number. The share gives way as the others do;
    - a line found from a parallel or perpendicular line is sloped, and that line is sloped too,
      meets the same rules apart from passing through the origin, and is drawn at random among
      those that do. It is written in slope-intercept or standard form, as drawn from
      ``REFERENCE_FORMS``. A vertical or horizontal line is found from the x- or y-axis instead;
    - a given equation in point-slope form is written y = m(x - x₁) + y₁ with even chance. No
      equation is in function notation.
    No line repeats, so no answer does, and the self-check tiles case needs nothing more.

    Each question's number style is drawn from ``number_styles``; a decimal question's slope and
    intercepts all terminate, and so do those of the line it's found from. A graph and a table
    are set out, and two points given a blank grid with ``blank_grids``, as
    ``generate_line_questions`` does. With ``statements``, a question asking for x = a or y = b
    asks for a statement too, as ``STATEMENT_SHARE`` has it: the line's slope, unless a point and
    the slope give it, or how it runs against the x-axis, unless it's found from an axis, each
    as likely. With a non-zero ``wrong_answer_count``, each question is multiple choice among
    its answer and that many wrong answers, made by ``wrong_answers``, from a set of mistakes
    drawn with even chance when the question has two (``mistake_sets``).

    Raises ``ValueError`` if ``givens`` or ``forms`` is empty or has a given not in
    ``EQUATION_GIVENS`` or a form not in ``EQUATION_FORMS``, if no pair can be asked, if
    ``largest_coordinate`` or ``largest_denominator`` is less than 1, if ``number_styles`` is
    empty or has mixed numbers, or if ``count`` is more than ``count_possible_equations`` allows.
    """
    if not givens:
        raise ValueError("At least one given is needed.")
    if not forms:
        raise ValueError("At least one form to write is needed.")
    for given in givens:
        if given not in EQUATION_GIVENS:
            raise ValueError(f"A line's equation isn't written from {given}.")
    for form in forms:
        if form not in EQUATION_FORMS:
            raise ValueError(f"Equations aren't written in {form} form.")
    _check_numbers(largest_coordinate, largest_denominator, number_styles)
    pairs = [pair for pair in product(givens, forms) if can_write(*pair)]
    if not pairs:
        raise ValueError("None of the givens can be written in the forms asked.")
    possible = count_possible_equations(
        givens,
        forms,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        limit=count,
    )
    if count > possible:
        raise ValueError(
            f"Cannot make {count} questions with different lines: only {possible} possible."
        )

    def build(
        pair: tuple[LineForm | Relation, LineForm], used: set[Line], _: set[LineAnswer]
    ) -> LineQuestionData | None:
        given, form = pair
        return _equation_data(
            given,
            form,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=whole_intercepts,
            number_styles=number_styles,
            used=used,
            blank_grids=blank_grids,
            statements=statements,
        )

    return _questions(count, pairs, build, wrong_answer_count)


def generate_graphing_questions(
    count: int,
    givens: Sequence[LineForm],
    asked: Sequence[LineForm],
    *,
    largest_coordinate: int = DEFAULT_LARGEST_COORDINATE,
    largest_denominator: int = DEFAULT_LARGEST_DENOMINATOR,
    whole_intercepts: bool = False,
    number_styles: Sequence[NumberStyle] = (NumberStyle.FRACTION, NumberStyle.DECIMAL),
    wrong_answer_count: int = 0,
    distinct_answers: bool = False,
) -> list[LineQuestion]:
    """
    Generate ``count`` questions that each ask to graph a line on a blank grid, or to complete a
    table of it, from the line given in a form from ``givens``: an equation, a point and slope,
    two points, the slope and y-intercept, the intercepts, or for a table, a graph.

    Each question takes the next pair of a given and what is asked from a shuffled deck of the
    pairs that can be asked, as ``generate_line_questions`` does. ``can_graph`` says which can.

    Each line meets the rules ``generate_line_questions`` lists, with these differences:
    - a line to graph passes through two places where the grid's gridlines cross, inside its
      edge, and the points given are such places, so they can be plotted; the grid is fitted to
      it as ``_graph_grid`` says, and ``key_points`` holds the two points the answer key marks,
      the points given first, then those nearest the origin where gridlines cross;
    - the intercepts given, and the y-intercept given with the slope, are on gridlines, and a
      line given by its intercepts doesn't pass through the origin, which would leave it
      unknown;
    - two points give a vertical or horizontal line as ``SHOWN_SLANTS`` has it, while x = a or
      y = b is among ``givens``; a graph a table is completed from is never vertical;
    - a table to complete has rows as ``_table_xs`` picks them, set out across or down the page
      with even chance, and leaves out x or y in each row, as ``_table_blanks`` says;
    - a given equation in point-slope form is written y = m(x - x₁) + y₁ with even chance. No
      equation is in function notation.

    Each question's number style is drawn from ``number_styles``.

    With a non-zero ``wrong_answer_count``, each question is multiple choice: the student
    chooses the line's graph or table from it and that many wrong ones, as ``_graph_choices``
    makes them. With ``distinct_answers``, as the self-check tiles case needs, the student finds
    the graph or table in the answer bank: no line repeats, so no answer does, and a table has no
    blanks. Either way the question is ``chosen``.

    Raises ``ValueError`` if ``givens`` or ``asked`` is empty or has a given not in
    ``GRAPHING_GIVENS`` or an ask not in ``GRAPHING_ASKED``, if no pair can be asked, if
    ``largest_coordinate`` or ``largest_denominator`` is less than 1, if ``number_styles`` is
    empty or has mixed numbers, if both ``wrong_answer_count`` and ``distinct_answers`` are
    given, or if ``count`` is more than ``count_possible_graphs`` allows.
    """
    if wrong_answer_count and distinct_answers:
        raise ValueError("Multiple-choice questions don't need different answers.")
    if not givens:
        raise ValueError("At least one given is needed.")
    if not asked:
        raise ValueError("At least one thing to ask is needed.")
    for given in givens:
        if given not in GRAPHING_GIVENS:
            raise ValueError(f"A line isn't graphed from {given}.")
    for form in asked:
        if form not in GRAPHING_ASKED:
            raise ValueError(f"Graphing lines doesn't ask for {form}.")
    _check_numbers(largest_coordinate, largest_denominator, number_styles)
    pairs = [pair for pair in product(givens, asked) if can_graph(*pair)]
    if not pairs:
        raise ValueError("None of the givens can be graphed or tabled as asked.")
    possible = count_possible_graphs(
        givens,
        asked,
        largest_coordinate=largest_coordinate,
        largest_denominator=largest_denominator,
        whole_intercepts=whole_intercepts,
        number_styles=number_styles,
        limit=count,
    )
    if count > possible:
        raise ValueError(
            f"Cannot make {count} questions with different lines: only {possible} possible."
        )

    def build(
        pair: tuple[LineForm, LineForm], used: set[Line], _: set[LineAnswer]
    ) -> LineQuestionData | None:
        given, form = pair
        return _graphing_data(
            given,
            form,
            givens,
            largest_coordinate=largest_coordinate,
            largest_denominator=largest_denominator,
            whole_intercepts=whole_intercepts,
            number_styles=number_styles,
            used=used,
            chosen=bool(wrong_answer_count) or distinct_answers,
        )

    def choose(data: LineQuestionData, wrong: int) -> _Choices:
        return _graph_choices(data, wrong, largest_coordinate)

    return _questions(count, pairs, build, wrong_answer_count, choose)


def can_graph(given: LineForm, asked: LineForm) -> bool:
    """
    Return whether a line given as ``given`` can be asked ``asked``: graphed from any given but
    a graph, or tabled from an equation or a graph, never x = a, which isn't a function.
    """
    match asked:
        case LineForm.GRAPH:
            return given in GRAPHING_GIVENS and given is not LineForm.GRAPH
        case LineForm.TABLE:
            return given in _TABLED_FROM
        case _:
            return False


def count_possible_graphs(
    givens: Sequence[LineForm],
    asked: Sequence[LineForm],
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    limit: int,
) -> int:
    """
    Return how many questions ``generate_graphing_questions`` can always make with these options
    without repeating a line, counting no further than ``limit``, as ``count_possible_lines``
    counts them: a pair's lines are those its given shows that meet the rules every question
    keeps, on a grid or with a table's rows as it asks.
    """
    pairs = [(given, form) for given, form in product(givens, asked) if can_graph(given, form)]
    rules = _Rules(
        largest_coordinate,
        largest_denominator,
        whole_intercepts,
        decimal=NumberStyle.FRACTION not in number_styles,
        origin=None,
        used=set(),
    )
    lines = {
        pair: frozenset(
            _distinct(
                _FORM_SLANTS.get(pair[0], "sloped"),
                _shown(pair[0]),
                _graphing_rules(rules, *pair),
                limit,
                _line_itself,
            )
        )
        for pair in pairs
    }
    return _dealt_count([lines[pair] for pair in pairs], limit)


def _graphing_rules(rules: _Rules, given: LineForm, asked: LineForm) -> _Rules:
    """
    Return ``rules`` for a line given as ``given`` and asked ``asked``: on a grid to graph it,
    with rows for a table, and with the intercepts given on gridlines and, for the intercepts,
    off the origin.
    """
    origin = False if given is LineForm.INTERCEPTS else rules.origin
    return replace(
        rules,
        origin=origin,
        on_grid=asked is LineForm.GRAPH,
        on_gridlines=_ON_GRIDLINES.get(given, frozenset()),
        table=asked is LineForm.TABLE,
    )


def _graphing_data(
    given: LineForm,
    asked: LineForm,
    givens: Sequence[LineForm],
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    used: set[Line],
    chosen: bool,
) -> LineQuestionData | None:
    """
    Draw a question's number style, point-slope style and shares, and return its data with a
    line that meets the rules ``generate_graphing_questions`` lists and isn't in ``used``, its
    grid or table set out, a table to fill in with its blanks, unless the question is
    ``chosen``. Returns ``None`` when no new line does.
    """
    numbers = random.choice(number_styles)
    solved_for_y = given is LineForm.POINT_SLOPE and random.choice((False, True))
    slant, shown = _graphing_slant(given, asked, givens), _shown(given)
    origin = (
        slant == "sloped" and given is not LineForm.INTERCEPTS and random.choice(THROUGH_ORIGIN)
    )
    rules = _graphing_rules(
        _Rules(
            largest_coordinate,
            largest_denominator,
            whole_intercepts,
            numbers is NumberStyle.DECIMAL,
            origin,
            used,
        ),
        given,
        asked,
    )
    form_slant = _FORM_SLANTS.get(given, "sloped")
    form_rules = _graphing_rules(_form_rules(rules, number_styles), given, asked)
    found = _line(slant, shown, rules) or _line(form_slant, shown, form_rules)
    if not found:
        return None
    line, points = found
    if numbers is NumberStyle.DECIMAL and not _terminating(line):
        numbers = NumberStyle.FRACTION  # the decimals' lines were used up
    data = LineQuestionData(
        line, given, asked, points, numbers=numbers, solved_for_y=solved_for_y, chosen=chosen
    )
    data = _shown_data(data, largest_coordinate, blank_grids=False)
    if asked is LineForm.GRAPH:
        key_points = _key_points(line, points, largest_coordinate)
        grid = _graph_grid(line, key_points, largest_coordinate)
        return replace(data, grid=grid, key_points=key_points)
    table_xs = _table_xs(line, None, asked, largest_coordinate)
    return replace(
        data,
        table_xs=table_xs,
        table_across=random.choice((False, True)),
        table_blanks=() if chosen else _table_blanks(line, table_xs),
    )


def _graphing_slant(given: LineForm, asked: LineForm, givens: Sequence[LineForm]) -> Slant:
    """
    Return which way a line to graph or table runs: as x = a or y = b says; for two points, or
    a graph to table, drawn from ``SHOWN_SLANTS`` while x = a or y = b is among ``givens``, a
    table never vertical; otherwise sloped.
    """
    match given:
        case LineForm.VERTICAL:
            return "vertical"
        case LineForm.HORIZONTAL:
            return "horizontal"
        case LineForm.TWO_POINTS | LineForm.GRAPH:
            return random.choice(
                [
                    slant
                    for slant in SHOWN_SLANTS
                    if (slant == "sloped" or _FORM_OF[slant] in givens)
                    and not (slant == "vertical" and asked is LineForm.TABLE)
                ]
            )
        case _:
            return "sloped"


def _key_points(line: Line, points: Sequence[Point], largest: int) -> tuple[Point, Point]:
    """
    Return the two points an answer key marks on ``line`` graphed for coordinates from
    -``largest`` to ``largest``: ``points``, those given, first, then where it crosses the
    y-axis and the x-axis, when that's where gridlines cross, as students plot from an equation
    or its intercepts, then the other places gridlines cross on it, inside the grid's edge,
    nearest the origin first.
    """
    step, inner = _axis_step(largest), _inner(largest)
    if line.b == 0:
        x = Fraction(line.c, line.a)
        crossings = [(int(x), y) for y in range(-inner, inner + 1, step) if y % step == 0]
    else:
        crossings = [
            (x, int(y))
            for x in range(-inner, inner + 1)
            if x % step == 0
            and (y := _y_at(line, x)).denominator == 1
            and y % step == 0
            and abs(y) <= inner
        ]
    crossings.sort(key=lambda point: (abs(point[0]) + abs(point[1]), point))
    on_axes = [point for axis in (0, 1) for point in crossings if point[axis] == 0]
    first, second, *_ = dict.fromkeys([*points, *on_axes, *crossings])
    return first, second


def _table_blanks(line: Line, table_xs: Sequence[int]) -> tuple[int, ...]:
    """
    Return each row's column a table to complete leaves out, as ``TABLE_BLANKS`` has it: 0 for
    x, 1 for y, with at least one of each, as input-output tables leave them out, except for a
    horizontal line, whose x can't be found from its y, so leaves out y in every row.
    """
    if line.a == 0:
        return (1,) * len(table_xs)
    blanks = [random.choice(TABLE_BLANKS) for _ in table_xs]
    if len(set(blanks)) == 1:
        flipped = random.choice(range(len(blanks)))
        blanks[flipped] = 1 - blanks[flipped]
    return tuple(blanks)


# A question's data, set out for its choices, and its wrong answers
type _Choices = tuple[LineQuestionData, tuple[LineAnswer, ...]]


def _choices(data: LineQuestionData, count: int) -> _Choices:
    """
    Return ``data`` and ``count`` wrong answers to it, from a set of mistakes drawn with even
    chance when it has two, as ``mistake_sets`` counts them.
    """
    sets = mistake_sets(data)
    mistakes = random.choice(range(sets)) if sets > 1 else 0
    return data, wrong_answers(data, count, mistakes)


def _questions[P](
    count: int,
    pairs: Sequence[P],
    build: Callable[[P, set[Line], set[LineAnswer]], LineQuestionData | None],
    wrong_answer_count: int,
    choose: Callable[[LineQuestionData, int], _Choices] = _choices,
) -> list[LineQuestion]:
    """
    Return ``count`` questions, each built by ``build`` from the next of ``pairs`` dealt from a
    shuffled deck, with the lines and answers already on the sheet, which it mustn't repeat.

    When ``build`` returns ``None`` for the pair dealt, because none of its lines has a new
    answer, the first other pair it returns a question for is used instead; the caller has
    counted that there is one. With a non-zero ``wrong_answer_count``, each question is multiple
    choice among its answer and that many wrong answers, which ``choose`` makes, setting the
    question out for them.
    """
    taken: set[LineAnswer] = set()
    deck: list[P] = []
    used: set[Line] = set()
    questions: list[LineQuestion] = []
    for _ in range(count):
        if not deck:
            deck = list(pairs)
            random.shuffle(deck)
        drawn = deck.pop()
        for pair in (drawn, *(pair for pair in pairs if pair != drawn)):
            data = build(pair, used, taken)
            if data:
                break
        else:  # never reached: the caller counted the lines or answers
            raise ValueError("No new line meets these options.")
        used.add(data.answer)
        answer = answer_of(data)
        taken.add(answer)
        if wrong_answer_count:
            data, wrong = choose(data, wrong_answer_count)
            questions.append(Question(data, multiple_choice((answer,), wrong)))
        else:
            questions.append(Question(data, FreeResponse()))
    return questions


def _question_data(
    given: LineForm,
    asked: LineFeature,
    givens: Sequence[LineForm],
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    as_point_choices: Sequence[bool],
    used: set[Line],
    taken: set[LineAnswer] | None,
    blank_grids: bool,
) -> LineQuestionData | None:
    """
    Draw a question's number style, shape of answer, notation and shares, and return its data
    with a line that meets the rules ``generate_line_questions`` lists and isn't in ``used``.

    With ``taken``, the answers already on the sheet, its answer must be a new one too. Returns
    ``None`` when no new line has a new answer.
    """
    numbers = random.choice(number_styles)
    as_point = False
    if asked in (LineFeature.X_INTERCEPT, LineFeature.Y_INTERCEPT):
        as_point = random.choice(as_point_choices)
    function = None
    if given is LineForm.SLOPE_INTERCEPT and random.choice((False, True)):
        function = random.choice(FUNCTION_NAMES)
    slant, shown = _slant(given, asked, givens), _shown(given)
    origin = slant == "sloped" and random.choice(THROUGH_ORIGIN)
    rules = _Rules(
        largest_coordinate,
        largest_denominator,
        whole_intercepts,
        numbers is NumberStyle.DECIMAL,
        origin,
        used,
        asked,
        as_point,
        frozenset() if taken is None else taken,
    )
    form_slant, form_rules = _FORM_SLANTS.get(given, "sloped"), _form_rules(rules, number_styles)
    found = _line(slant, shown, rules) or _line(form_slant, shown, form_rules)
    if not found:
        return None
    line, points = found
    if numbers is NumberStyle.DECIMAL and not _terminating(line):
        numbers = NumberStyle.FRACTION  # the decimals' lines were used up
    data = LineQuestionData(line, given, asked, points, as_point, numbers, function)
    return _shown_data(data, largest_coordinate, blank_grids)


def _equation_data(
    given: LineForm | Relation,
    form: LineForm,
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    used: set[Line],
    blank_grids: bool,
    statements: bool,
) -> LineQuestionData | None:
    """
    Draw a question's number style, point-slope style and shares, and return its data with a
    line that meets the rules ``generate_equation_questions`` lists and isn't in ``used``, and
    the line it's found from, if it has a relation, and with ``statements``, the statement a
    vertical or horizontal line's equation asks for too, if any, as ``_statement`` draws it.
    Returns ``None`` when no new line does.
    """
    numbers = random.choice(number_styles)
    solved_for_y = given is LineForm.POINT_SLOPE and random.choice((False, True))
    relation = given if isinstance(given, Relation) else None
    slant, shown = _FORM_SLANTS.get(form, "sloped"), _shown(given)
    origin = slant == "sloped" and random.choice(THROUGH_ORIGIN)
    # a line through the origin crosses the x-axis at 0, which a point shown mustn't be
    x_axis_point = slant == "sloped" and shown == 1 and not origin and random.choice(X_AXIS_POINT)
    rules = _Rules(
        largest_coordinate,
        largest_denominator,
        whole_intercepts,
        numbers is NumberStyle.DECIMAL,
        origin,
        used,
        relation=relation,
        x_axis_point=x_axis_point,
    )
    found = _line(slant, shown, rules)
    if not found:
        rules = replace(_form_rules(rules, number_styles), x_axis_point=False)
        found = _line(slant, shown, rules)
    if not found:
        return None
    line, points = found
    reference = _reference(line, rules)
    shown_form = given
    if reference in (X_AXIS, Y_AXIS):
        shown_form = LineForm.HORIZONTAL if reference == X_AXIS else LineForm.VERTICAL
    elif reference:
        shown_form = random.choice(REFERENCE_FORMS)
    assert isinstance(shown_form, LineForm)  # a relation always has a reference
    lines = (line,) if reference is None else (line, reference)
    if numbers is NumberStyle.DECIMAL and not all(_terminating(each) for each in lines):
        numbers = NumberStyle.FRACTION  # the decimals' lines were used up
    data = LineQuestionData(
        line,
        shown_form,
        form,
        points,
        numbers=numbers,
        reference=reference,
        relation=relation,
        solved_for_y=solved_for_y,
    )
    if statements and form in (LineForm.VERTICAL, LineForm.HORIZONTAL):
        data = replace(data, statement=_statement(data))
    return _shown_data(data, largest_coordinate, blank_grids)


def _statement(data: LineQuestionData) -> Statement | None:
    """
    Return the statement a question asking for x = a or y = b asks for too, as
    ``STATEMENT_SHARE`` has it, or ``None``: the slope, unless a point and the slope give it
    away, or how the line runs against the x-axis, unless it's found from an axis, which gives
    that away, each as likely.
    """
    allowed = [
        statement
        for statement in Statement
        if not (statement is Statement.SLOPE and data.given is LineForm.POINT_AND_SLOPE)
        and not (statement is Statement.X_AXIS and data.reference is not None)
    ]
    if not allowed or not random.choice(STATEMENT_SHARE):
        return None
    return random.choice(allowed)


def _shown_data(data: LineQuestionData, largest: int, blank_grids: bool) -> LineQuestionData:
    """
    Return ``data`` with how its table, graph or blank grid is set out, drawn at random:

    - a table: its rows, as ``_table_xs`` picks them, set out across or down the page with even
      chance;
    - a graph: its grid, fitted to the line as ``_graph_grid`` says, and its marked points
      labelled with their coordinates when an intercept isn't on a gridline, so it can only be
      worked out from them, and otherwise with even chance;
    - two points, with ``blank_grids``: a blank grid beside them, fitted the same way, as
      ``BLANK_GRIDS`` has it, when both points lie where gridlines cross.
    """
    line, points = data.answer, data.points
    match data.given:
        case LineForm.TABLE:
            table_xs = _table_xs(line, points[0], data.asked, largest)
            return replace(data, table_xs=table_xs, table_across=random.choice((False, True)))
        case LineForm.GRAPH:
            grid = _graph_grid(line, points, largest)
            labelled = not _on_gridlines(line, grid.step) or random.choice((False, True))
            return replace(data, grid=grid, labelled=labelled)
        case LineForm.TWO_POINTS if blank_grids:
            step = _axis_step(largest)
            crossing = all(x % step == 0 and y % step == 0 for x, y in points)
            if crossing and random.choice(BLANK_GRIDS):
                return replace(data, grid=_graph_grid(line, points, largest))
            return data
        case _:
            return data


def count_possible_lines(
    givens: Sequence[LineForm],
    features: Sequence[LineFeature],
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    distinct_answers: bool = False,
    limit: int,
) -> int:
    """
    Return how many questions ``generate_line_questions`` can always make with these options
    without repeating a line, or with ``distinct_answers``, an answer, counting no further than
    ``limit``.

    Without ``distinct_answers``, that's as many as the deck can deal while every pair has a new
    line for each time it's dealt, as ``_dealt_count`` counts them. A pair's lines are those its
    form shows under the rules every question keeps: the coordinates, denominators and whole
    intercepts, and decimals when they're the only style. Shares drawn per question give way
    when their lines run out, so they don't count.

    With ``distinct_answers``, a question needs a new line with a new answer. A pair whose
    lines have no new answer gives way to another, so the count rests on the pair with the most
    different answers among its form's lines (every vertical line's slope is the one answer
    "undefined"), an intercept counted as a number, since as points there are as many. When
    every feature asked has the same kind of answer, such as the slope and the rate of change,
    each earlier question rules out at most one of that pair's answers, so each answer can be a
    question. Otherwise an earlier question can rule out two, its own answer and, through its
    line, another feature's, so only half can.
    """
    pairs = [(given, asked) for given, asked in product(givens, features) if can_ask(given, asked)]
    rules = _Rules(
        largest_coordinate,
        largest_denominator,
        whole_intercepts,
        decimal=NumberStyle.FRACTION not in number_styles,
        origin=None,
        used=set(),
    )

    def shape(form: LineForm) -> tuple[Slant, Shown]:
        return _FORM_SLANTS.get(form, "sloped"), _shown(form)

    if distinct_answers:
        one_kind = len({_ANSWER_KINDS[asked] for _, asked in pairs}) == 1
        reach = limit if one_kind else 2 * limit - 1
        most = max(
            (
                len(_distinct(*shape(form), rules, reach, _answer_key(asked)))
                for form, asked in pairs
            ),
            default=0,
        )
        return most if one_kind else min((most + 1) // 2, limit)
    lines = {
        form: frozenset(_distinct(*shape(form), rules, limit, _line_itself))
        for form in {given for given, _ in pairs}
    }
    return _dealt_count([lines[given] for given, _ in pairs], limit)


def count_possible_equations(
    givens: Sequence[LineForm | Relation],
    forms: Sequence[LineForm],
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    limit: int,
) -> int:
    """
    Return how many questions ``generate_equation_questions`` can always make with these options
    without repeating a line, counting no further than ``limit``.

    As ``count_possible_lines`` counts them: as many as the deck can deal while every pair has a
    new line for each time it's dealt, under the rules every question keeps. A pair's lines run
    as the form asked says, show the points its given shows and, with a relation, have a line
    they're parallel or perpendicular to. Shares drawn per question give way when their lines run
    out, so they don't count.
    """
    pairs = [(given, form) for given, form in product(givens, forms) if can_write(given, form)]
    rules = _Rules(
        largest_coordinate,
        largest_denominator,
        whole_intercepts,
        decimal=NumberStyle.FRACTION not in number_styles,
        origin=None,
        used=set(),
    )

    def shape(given: LineForm | Relation, form: LineForm) -> tuple[Slant, Shown, Relation | None]:
        relation = given if isinstance(given, Relation) else None
        return _FORM_SLANTS.get(form, "sloped"), _shown(given), relation

    lines = {
        (slant, shown, relation): frozenset(
            _distinct(slant, shown, replace(rules, relation=relation), limit, _line_itself)
        )
        for slant, shown, relation in {shape(*pair) for pair in pairs}
    }
    return _dealt_count([lines[shape(*pair)] for pair in pairs], limit)


def _dealt_count(pair_lines: Sequence[frozenset[Line]], limit: int) -> int:
    """
    Return how many questions, up to ``limit``, the shuffled deck of pairs can deal with a new
    line for each, where ``pair_lines`` holds each pair's lines, at most ``limit`` of them.

    The deck deals every pair once a round, then deals the next round in a new order. A group of
    g of the p pairs with l lines among them has lines for l // g rounds of p questions, and as
    its pairs may come first in the next round, for l % g questions more: (l // g) * p + l % g
    in all. The fewest any group allows is counted. The group of every pair then has a line for
    each question, so a pair whose lines another pair took can give way to one with lines left.

    Pairs with the same lines are grouped together, since one more of them adds questions but no
    lines, and a group with a pair of ``limit`` lines allows any number, so only groups of pairs
    with fewer are counted.
    """
    pairs_with = Counter(pair_lines)
    few = [lines for lines in pairs_with if len(lines) < limit]
    groups = [
        (sum(pairs_with[lines] for lines in group), len(frozenset[Line]().union(*group)))
        for size in range(1, len(few) + 1)
        for group in combinations(few, size)
    ]
    dealt = (lines // pairs * len(pair_lines) + lines % pairs for pairs, lines in groups)
    return min([limit, *dealt]) if pair_lines else 0


def _check_numbers(
    largest_coordinate: int, largest_denominator: int, number_styles: Sequence[NumberStyle]
) -> None:
    """Raise ``ValueError`` for number options no line can meet, as the generators list them."""
    if largest_coordinate < 1:
        raise ValueError(f"The largest coordinate must be at least 1, not {largest_coordinate}.")
    if largest_denominator < 1:
        raise ValueError(f"The largest denominator must be at least 1, not {largest_denominator}.")
    if not number_styles:
        raise ValueError("At least one number style is needed.")
    if NumberStyle.MIXED_NUMBER in number_styles:
        raise ValueError("Lines are written with fractions or decimals, not mixed numbers.")


def can_ask(given: LineForm, asked: LineFeature) -> bool:
    """Return whether a line shown in the form ``given`` can be asked the feature ``asked``."""
    if given is LineForm.POINT_AND_SLOPE:
        return asked not in (
            LineFeature.SLOPE,
            LineFeature.RATE_OF_CHANGE,
            LineFeature.SLOPE_AND_Y_INTERCEPT,
        )
    if given is LineForm.VERTICAL:
        return asked in _FEATURES_OF["vertical"]
    if given is LineForm.HORIZONTAL:
        return asked in _FEATURES_OF["horizontal"]
    return True


def can_write(given: LineForm | Relation, form: LineForm) -> bool:
    """
    Return whether the equation of a line given as ``given`` can be asked in ``form``.

    Point-slope form, x = a and y = b need a point shown to write the equation through, so they
    are asked of two points, a point and slope, a table, a graph or a relation, never of another
    equation; x = a never of a table, which never shows a vertical line. Slope-intercept and
    standard forms are asked of any given but themselves. A point and slope, two points, a table
    and a graph aren't equations, so they can't be asked.
    """
    match form:
        case LineForm.VERTICAL if given is LineForm.TABLE:
            return False
        case LineForm.POINT_SLOPE | LineForm.VERTICAL | LineForm.HORIZONTAL:
            return given in _SHOWS_POINT
        case LineForm.SLOPE_INTERCEPT | LineForm.STANDARD:
            return given != form
        case _:
            return False


def _shown(given: LineForm | Relation) -> Shown:
    """Return what a line given as ``given`` shows besides an equation: a relation, one point."""
    return 1 if isinstance(given, Relation) else _SHOWN.get(given, 0)


def _slant(given: LineForm, asked: LineFeature, givens: Sequence[LineForm]) -> Slant:
    """
    Return which way the question's line runs, drawn for two points, a graph or a table from
    ``SHOWN_SLANTS``: vertical only while x = a is among ``givens`` and never in a table,
    horizontal only while y = b is, and only when the line has the feature ``asked``.
    """
    match given:
        case LineForm.VERTICAL:
            return "vertical"
        case LineForm.HORIZONTAL:
            return "horizontal"
        case LineForm.TWO_POINTS | LineForm.GRAPH | LineForm.TABLE:
            return random.choice(
                [
                    slant
                    for slant in SHOWN_SLANTS
                    if asked in _FEATURES_OF[slant]
                    and (slant == "sloped" or _FORM_OF[slant] in givens)
                    and not (slant == "vertical" and given is LineForm.TABLE)
                ]
            )
        case _:
            return "sloped"


def _form_rules(rules: _Rules, number_styles: Sequence[NumberStyle]) -> _Rules:
    """Return ``rules`` without a question's shares: either side of the origin, and decimals only
    when they're the only style."""
    return replace(
        rules,
        origin=None,
        decimal=rules.decimal and NumberStyle.FRACTION not in number_styles,
    )


def _terminating(line: Line) -> bool:
    """Return whether the slope and intercepts of ``line`` all have decimals that terminate."""
    numbers = (line.slope, line.y_intercept, line.x_intercept)
    return all(terminates(number) for number in numbers if number is not None)


def _answer_key(asked: LineFeature) -> Callable[[Line], Hashable]:
    """Return a function giving a line's answer to ``asked``, an intercept as a number."""
    return lambda line: line_answer(line, asked, False)


def _line_itself(line: Line) -> Line:
    """Return ``line``, for collecting lines rather than answers."""
    return line


def _distinct[K: Hashable](
    slant: Slant, shown: Shown, rules: _Rules, limit: int, key: Callable[[Line], K]
) -> set[K]:
    """
    Return the different ``key`` values the lines running as ``slant`` says that meet ``rules``
    with ``shown`` points have, collecting no more than ``limit``.
    """
    seen: set[K] = set()
    for line in _lines(slant, shown, rules):
        seen.add(key(line))
        if len(seen) >= limit:
            break
    return seen


def _lines(slant: Slant, shown: Shown, rules: _Rules) -> Iterator[Line]:
    """
    Yield the lines running as ``slant`` says that meet ``rules`` and can show what ``shown``
    says, ignoring ``rules.x_axis_point``, a share.
    """
    if slant != "sloped":
        yield from (_level(slant, number) for number in _level_numbers(slant, shown, rules))
        return
    step = _axis_step(rules.largest_coordinate) if _gridded(shown, rules) else 1
    for slope in _shown_slopes(shown, rules):
        references = _reference_intercepts(slope, rules)
        for intercept in _y_intercepts(slope, rules, step):
            if not _has_reference(intercept, references, rules.relation):
                continue
            line = line_from(-slope, Fraction(1), intercept)
            if _fits(line, shown, rules):
                yield line


def _line(slant: Slant, shown: Shown, rules: _Rules) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a line running as ``slant`` says that meets ``rules``, and the points on it that
    ``shown`` asks for, as ``_picked`` counts them, or ``None`` if no line does.
    """
    if slant == "sloped":
        return _sloped_line(shown, rules)
    return _level_line(slant, shown, rules)


def _sloped_line(shown: Shown, rules: _Rules) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a line that isn't vertical or horizontal, and the points on it that ``shown`` asks
    for, drawn at random from those ``_candidates`` finds.

    The slope is drawn first, then the y-intercept. A slope or y-intercept that leaves too
    little to show, or with a relation, no line to be parallel or perpendicular to, is set aside
    and another drawn, until none is left, giving ``None``. With ``rules.x_axis_point``, the one
    point shown is where the line crosses the x-axis. A graph's line has y-intercepts that put
    it through where gridlines cross, as ``_y_intercepts`` lists them.
    """
    step = _axis_step(rules.largest_coordinate) if _gridded(shown, rules) else 1
    slopes = _shown_slopes(shown, rules)
    while slopes:
        slope = random.choice(slopes)
        references = _reference_intercepts(slope, rules)
        intercepts = _y_intercepts(slope, rules, step) if references != [] else []
        while intercepts:
            intercept = random.choice(intercepts)
            if not _has_reference(intercept, references, rules.relation):
                intercepts.remove(intercept)
                continue
            line = line_from(-slope, Fraction(1), intercept)
            if not shown and _fits(line, shown, rules):
                return line, ()
            if rules.x_axis_point:
                points = _x_axis_points(line)
            elif shown and _fits(line, shown, rules):
                points = _candidates(line, shown, rules)
            else:
                points = []
            if points and len(points) >= _picked(shown):
                return line, tuple(random.sample(points, _picked(shown)))
            intercepts.remove(intercept)
        slopes.remove(slope)
    return None


def _shown_slopes(shown: Shown, rules: _Rules) -> list[Fraction]:
    """
    Return the slopes ``rules`` allow for a line that shows what ``shown`` says. A graph's line
    rises or falls by its numerator's gridlines over its denominator's, so it needs both within
    the grid to pass through two places gridlines cross.
    """
    slopes = _slopes(rules)
    if not _gridded(shown, rules):
        return slopes
    largest = rules.largest_coordinate
    room = 2 * _inner(largest) // _axis_step(largest)
    return [slope for slope in slopes if abs(slope.numerator) <= room and slope.denominator <= room]


def _picked(shown: Shown) -> int:
    """Return how many points a question showing ``shown`` holds in its data: a table, one row."""
    match shown:
        case "table":
            return 1
        case "graph":
            return 2
        case _:
            return shown


def _gridded(shown: Shown, rules: _Rules) -> bool:
    """Return whether a question's line is on a grid: a graph shown, or a line to graph."""
    return shown == "graph" or rules.on_grid


def _fits(line: Line, shown: Shown, rules: _Rules) -> bool:
    """
    Return whether ``line``, which isn't vertical, can show what ``shown`` says within the
    largest coordinate: that many points off the axes, two marked points on a graph, or a table
    as ``_fits_table`` says, one of its rows with a whole y-value for ``points`` to hold. With
    ``rules.on_grid``, it also passes through two places gridlines cross, and its points shown
    are such places; with ``rules.table``, it also fits a table.
    """
    largest = rules.largest_coordinate
    if rules.on_grid and len(_marked_points(line, largest)) < 2:
        return False
    if rules.table and not _fits_table(line, largest):
        return False
    match shown:
        case 0:
            return True
        case "table":
            return _fits_table(line, largest) and bool(_points_on(line, largest))
        case _:
            return len(_candidates(line, shown, rules)) >= _picked(shown)


def _fits_table(line: Line, largest: int) -> bool:
    """
    Return whether ``line``, which isn't vertical, has rows for a table: at least the fewest
    ``TABLE_ROWS`` allows, off the axes, within the largest coordinate.
    """
    off_axes = [x for x in _table_rows(line, largest) if x and _y_at(line, x)]
    return len(off_axes) >= min(TABLE_ROWS)


def _candidates(line: Line, shown: Shown, rules: _Rules) -> list[Point]:
    """
    Return the points on ``line``, which isn't vertical, that a question showing ``shown`` can
    hold in its data: on a grid, as ``_marked_points`` finds them; otherwise those with
    whole-number coordinates off the axes, which for a table are its rows that ``points`` can
    hold.
    """
    if _gridded(shown, rules):
        return _marked_points(line, rules.largest_coordinate)
    return _points_on(line, rules.largest_coordinate)


def _reference_intercepts(slope: Fraction, rules: _Rules) -> list[Fraction] | None:
    """
    Return the y-intercepts a line can have that a line with ``slope`` is parallel or
    perpendicular to, as ``rules.relation`` says, or ``None`` without a relation.

    That line meets ``rules`` apart from ``used``, ``taken`` and ``origin``. A perpendicular
    line's slope, -1/``slope``, must be one the rules allow, or there are none.
    """
    if rules.relation is None:
        return None
    shown = replace(rules, used=set(), taken=frozenset(), origin=None, relation=None)
    if rules.relation is Relation.PARALLEL:
        return _y_intercepts(slope, shown)
    perpendicular = -1 / slope
    return _y_intercepts(perpendicular, shown) if perpendicular in _slopes(shown) else []


def _has_reference(
    intercept: Fraction, references: list[Fraction] | None, relation: Relation | None
) -> bool:
    """
    Return whether a line with the y-intercept ``intercept`` has a line among those with the
    y-intercepts ``references`` to be parallel or perpendicular to, as ``relation`` says: any,
    or for a parallel line, any but itself. ``None`` for ``references`` means no relation.
    """
    if references is None:
        return True
    if relation is Relation.PARALLEL:
        return any(reference != intercept for reference in references)
    return bool(references)


def _reference(line: Line, rules: _Rules) -> Line | None:
    """
    Return a line that ``line`` is parallel or perpendicular to, as ``rules.relation`` says,
    drawn at random from those ``_reference_intercepts`` allows, or the axis a vertical or
    horizontal line is parallel or perpendicular to. Returns ``None`` without a relation.
    """
    if rules.relation is None:
        return None
    parallel = rules.relation is Relation.PARALLEL
    if line.slope is None or line.slope == 0:
        return X_AXIS if parallel == (line.slope == 0) else Y_AXIS
    references = _reference_intercepts(line.slope, rules) or []
    slope = line.slope if parallel else -1 / line.slope
    intercepts = [b for b in references if not (parallel and b == line.y_intercept)]
    return line_from(-slope, Fraction(1), random.choice(intercepts))


def _x_axis_points(line: Line) -> list[Point]:
    """Return where ``line`` crosses the x-axis, if that's a whole number other than 0."""
    a = line.x_intercept
    return [(int(a), 0)] if a is not None and a.denominator == 1 and a != 0 else []


def _level_line(
    slant: Literal["horizontal", "vertical"], shown: Shown, rules: _Rules
) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a horizontal line, y = b, or a vertical one, x = a, its number drawn from those that
    meet ``rules``, and the points on it that ``shown`` asks for, or ``None`` if no number does.
    A line with points shown has a whole number other than 0, so its points have whole-number
    coordinates and lie off the axes; on a graph, they are where gridlines cross, inside its
    edge.
    """
    candidates = _level_numbers(slant, shown, rules)
    if not candidates:
        return None
    number = random.choice(candidates)
    line = _level(slant, number)
    if not shown:
        return line, ()
    largest = rules.largest_coordinate
    gridded = _gridded(shown, rules)
    step, inner = (_axis_step(largest), _inner(largest)) if gridded else (1, largest)
    others = [other for other in range(-inner, inner + 1) if other != 0 and other % step == 0]
    if slant == "vertical":
        points = [(int(number), y) for y in others]
    else:
        points = [(x, int(number)) for x in others]
    return line, tuple(random.sample(points, _picked(shown)))


def _level_numbers(
    slant: Literal["horizontal", "vertical"], shown: Shown, rules: _Rules
) -> list[Fraction]:
    """
    Return the numbers a horizontal or vertical line can have under ``rules``, in order. With
    points shown, or on a grid, the number is whole and not 0, so the points lie off the axes;
    on a grid, it is also a gridline inside its edge. With ``rules.table``, a horizontal line
    has rows for a table, as ``_fits_table`` says.
    """
    largest = rules.largest_coordinate
    gridded = _gridded(shown, rules)
    whole = bool(shown) or gridded
    # with points shown, only whole numbers, which saves listing every fraction
    denominators = range(1, rules.largest_denominator + 1) if not whole else (1,)
    numbers = sorted(
        {
            Fraction(numerator, denominator)
            for denominator in denominators
            for numerator in range(-largest * denominator, largest * denominator + 1)
        }
    )
    step, inner = _axis_step(largest), _inner(largest)
    return [
        number
        for number in numbers
        if _meets(_level(slant, number), rules)
        and not (whole and number == 0)
        and (not gridded or (number % step == 0 and abs(number) <= inner))
        and not (rules.table and not _fits_table(_level(slant, number), largest))
    ]


def _level(slant: Literal["horizontal", "vertical"], number: Fraction) -> Line:
    """Return the line x = ``number`` if ``slant`` is vertical, or y = ``number``."""
    if slant == "vertical":
        return line_from(Fraction(1), Fraction(0), number)
    return line_from(Fraction(0), Fraction(1), number)


def _slopes(rules: _Rules) -> list[Fraction]:
    """
    Return the slopes ``rules`` allow: numerators up to the largest coordinate, denominators up
    to the largest denominator, and only decimals that terminate in a decimal question.
    """
    largest = rules.largest_coordinate
    return [
        Fraction(numerator, denominator)
        for denominator in range(1, rules.largest_denominator + 1)
        if not rules.decimal or terminates(Fraction(1, denominator))
        for numerator in range(-largest, largest + 1)
        if numerator != 0 and gcd(numerator, denominator) == 1
    ]


def _y_intercepts(slope: Fraction, rules: _Rules, step: int = 1) -> list[Fraction]:
    """
    Return the y-intercepts that a line with ``slope`` can have under ``rules``.

    Each is a whole number of the slope's denominator's parts, so that the line has points with
    whole-number coordinates: for a slope of 3/4, the y-intercept is a number of quarters. With
    a ``step``, it's a whole number of ``step`` of those parts, so that the line passes through
    points whose coordinates are both multiples of ``step``, where a grid's gridlines cross. It
    is 0 for a line through the origin, and never 0 otherwise.
    """
    parts = slope.denominator
    largest = rules.largest_coordinate * parts // step
    return [
        Fraction(step * numerator, parts)
        for numerator in range(-largest, largest + 1)
        if (rules.origin is None or (numerator == 0) == rules.origin)
        and _meets(line_from(-slope, Fraction(1), Fraction(step * numerator, parts)), rules)
    ]


def _meets(line: Line, rules: _Rules) -> bool:
    """Return whether ``line`` meets ``rules``, as ``generate_line_questions`` lists them."""
    intercepts = [value for value in (line.y_intercept, line.x_intercept) if value is not None]
    numbers = intercepts if line.slope is None else [line.slope, *intercepts]
    return (
        line not in rules.used
        and not (rules.taken and line_answer(line, rules.asked, rules.as_point) in rules.taken)
        and all(abs(value) <= rules.largest_coordinate for value in intercepts)
        and all(value.denominator <= rules.largest_denominator for value in numbers)
        and not (rules.whole and any(value.denominator != 1 for value in intercepts))
        and not (rules.decimal and not all(terminates(value) for value in numbers))
        and _intercepts_on_gridlines(line, rules)
    )


def _intercepts_on_gridlines(line: Line, rules: _Rules) -> bool:
    """Return whether ``line`` has each intercept in ``rules.on_gridlines``, on a gridline."""
    if not rules.on_gridlines:
        return True
    step = _axis_step(rules.largest_coordinate)
    values = {LineFeature.Y_INTERCEPT: line.y_intercept, LineFeature.X_INTERCEPT: line.x_intercept}
    return all(
        (value := values[feature]) is not None and value % step == 0
        for feature in rules.on_gridlines
    )


def _points_on(line: Line, largest: int) -> list[Point]:
    """
    Return the points on ``line``, which isn't vertical, with whole-number coordinates from
    -``largest`` to ``largest`` that lie on neither axis.
    """
    points = []
    for x in range(-largest, largest + 1):
        y, remainder = divmod(line.c - line.a * x, line.b)
        if x != 0 and y != 0 and remainder == 0 and abs(y) <= largest:
            points.append((x, y))
    return points


def _y_at(line: Line, x: int) -> Fraction:
    """Return the y-value of ``line``, which isn't vertical, at ``x``."""
    return Fraction(line.c - line.a * x, line.b)


def _table_rows(line: Line, largest: int) -> list[int]:
    """
    Return the x-values a table of ``line``, which isn't vertical, can have rows at, in order:
    whole numbers from -``largest`` to ``largest`` where its y-value is a whole number or a half
    in that range too.
    """
    return [
        x
        for x in range(-largest, largest + 1)
        if (y := _y_at(line, x)).denominator <= 2 and abs(y) <= largest
    ]


def _table_xs(
    line: Line, point: Point | None, asked: LineFeature | LineForm, largest: int
) -> tuple[int, ...]:
    """
    Return the x-values of a table of ``line``'s rows, in order, among those ``_table_rows``
    allows, one of them ``point``'s, if given.

    It has as many rows as drawn from ``TABLE_ROWS``, or as the line allows. A row at x = 0
    comes as ``ZERO_ROWS`` has it, and when the x-intercept or zero is asked, the row where
    y = 0 is allowed as often. The x-values go up in equal steps as ``EVEN_TABLES`` has it, by 2
    or 5, or by the gap between the rows the line allows, when the rows allow a run of that
    length; otherwise they're drawn at random from those allowed.
    """
    rows = _table_rows(line, largest)
    crossing = [x for x in rows if _y_at(line, x) == 0]
    if asked in _X_INTERCEPT_FEATURES and crossing and not random.choice(ZERO_ROWS):
        rows = [x for x in rows if x not in crossing]
    zero = 0 in rows and random.choice(ZERO_ROWS)
    allowed = [x for x in rows if x != 0 or zero]
    required = {point[0]} if point else set()
    if zero:
        required.add(0)
    return _picked_xs(allowed, required, min(random.choice(TABLE_ROWS), len(allowed)))


def _picked_xs(allowed: list[int], required: set[int], size: int) -> tuple[int, ...]:
    """
    Return ``size`` x-values among ``allowed``, in order, with all of ``required``: in equal
    steps as ``EVEN_TABLES`` has it, when ``_even_runs`` finds a run, otherwise at random.
    """
    if random.choice(EVEN_TABLES):
        runs = _even_runs(allowed, required, size)
        if runs:
            return random.choice(runs)
    others = [x for x in allowed if x not in required]
    return tuple(sorted([*required, *random.sample(others, size - len(required))]))


def _graph_choices(data: LineQuestionData, count: int, largest: int) -> _Choices:
    """
    Return ``data`` set out for a graph or table of its line to choose, and ``count`` wrong
    graphs or tables, each the line of a mistake as an ``Equation`` in the form asked. The
    mistakes come from a set of ``wrong_lines`` drawn with even chance when the line has two
    (``mistake_sets``).

    A wrong graph crosses the y-axis inside the grid, or the x-axis for a vertical line, and the
    four graphs share one grid, fitted to them all as ``_fitted_grid`` says. The four tables
    share their x-values, as ``_table_lines`` picks them.
    """
    sets = mistake_sets(data)
    mistakes = random.choice(range(sets)) if sets > 1 else 0
    candidates = (line for line in wrong_lines(data, mistakes) if line != data.answer)
    if data.asked is LineForm.GRAPH:
        lines = _graph_lines(candidates, count, largest)
        intercepts = [line.y_intercept for line in (data.answer, *lines)]
        grid = _fitted_grid([abs(value) for value in intercepts if value is not None], largest)
        data = replace(data, grid=grid, key_points=())
    else:
        lines, table_xs = _table_lines(data.answer, candidates, count, largest)
        data = replace(data, table_xs=table_xs, table_blanks=())
    form = data.asked
    assert isinstance(form, LineForm)  # a graph or a table
    return data, tuple(Equation(line, form) for line in lines)


def _graph_lines(candidates: Iterator[Line], count: int, largest: int) -> list[Line]:
    """
    Return the first ``count`` different lines among ``candidates`` that cross the y-axis from
    -``largest`` to ``largest``, or for a vertical line, the x-axis.
    """
    lines: list[Line] = []
    for line in candidates:
        crossing = line.x_intercept if line.b == 0 else line.y_intercept
        if line not in lines and crossing is not None and abs(crossing) <= largest:
            lines.append(line)
            if len(lines) == count:
                break
    return lines


def _table_lines(
    answer: Line, candidates: Iterator[Line], count: int, largest: int
) -> tuple[list[Line], tuple[int, ...]]:
    """
    Return ``count`` wrong lines for a table of ``answer`` to choose, and the x-values all the
    tables share, in order.

    The lines are the first different ones among ``candidates`` whose tables can have rows at
    ``CHOICE_TABLE_ROWS`` or more of the x-values that the answer's table and those taken before
    them allow, as ``_choice_rows`` finds them. The last is the first such line, within
    ``SHARED_ROW_SEARCH`` more, whose table, or another wrong line's, agrees with the answer's
    in a row, so checking one row isn't enough; failing that, the first such line moved through
    a row of the answer's table, as ``_moved_to_row`` moves it, so the slopes stay as they were;
    failing that, the first such line. The x-values hold a shared row, and are picked as a
    table's are, as many as drawn from ``TABLE_ROWS`` or as allowed.

    A horizontal line y = b whose b is a half has no shared row: its wrong tables are of x = b,
    y = -b and x = -b, and only x = b's could share one, (b, b), at a whole-number x.
    """
    fewest = CHOICE_TABLE_ROWS
    allowed = set(_choice_rows(answer, largest))
    lines: list[Line] = []
    for line in candidates:
        rows = allowed & set(_choice_rows(line, largest))
        if line in lines or len(rows) < fewest:
            continue
        if len(lines) < count - 1:
            lines.append(line)
            allowed = rows
            continue
        # the last wrong line: the first that shares a row, or failing that, the first that fits
        # moved through a row of the answer's table
        last = None
        for later in islice(chain((line,), candidates), SHARED_ROW_SEARCH):
            later_rows = allowed & set(_choice_rows(later, largest))
            fits = later not in lines and len(later_rows) >= fewest
            if fits and _shared_rows(answer, [*lines, later], later_rows):
                last = (later, later_rows)
                break
        last = last or _moved_to_row(answer, line, lines, allowed, largest) or (line, rows)
        lines.append(last[0])
        allowed = last[1]
        break
    shared = _shared_rows(answer, lines, allowed)
    required = {random.choice(shared)} if shared else set()
    ordered = sorted(allowed)
    return lines, _picked_xs(ordered, required, min(random.choice(TABLE_ROWS), len(ordered)))


def _moved_to_row(
    answer: Line, line: Line, lines: Sequence[Line], allowed: set[int], largest: int
) -> tuple[Line, set[int]] | None:
    """
    Return a line through a row of the answer's table, the row nearest the middle of
    ``allowed`` first, with the x-values its table and the others' share: with ``line``'s slope,
    or when that's the answer's, the answer's slope's opposite, so the slopes stay balanced. It
    must share ``CHOICE_TABLE_ROWS`` or more of them and not be one of ``lines``. Returns
    ``None`` when no such line does, or when ``answer`` is horizontal, whose wrong tables are
    of vertical and horizontal lines.
    """
    if answer.a == 0 or answer.slope is None or line.slope is None:
        return None
    slope = line.slope if line.slope != answer.slope else -answer.slope
    middle = sum(allowed) / len(allowed) if allowed else 0
    for x in sorted(allowed, key=lambda value: (abs(value - middle), value)):
        moved = line_from(-slope, Fraction(1), _y_at(answer, x) - slope * x)
        rows = allowed & set(_choice_rows(moved, largest))
        if moved not in lines and moved != answer and len(rows) >= CHOICE_TABLE_ROWS:
            return moved, rows
    return None


def _choice_rows(line: Line, largest: int) -> list[int]:
    """
    Return the x-values a table to choose can have rows at for ``line``: as ``_table_rows`` finds
    them, or for a vertical line x = c, whose table has c in every row with the x-values as its
    y-values, every whole number from -``largest`` to ``largest``, when c is a whole number or a
    half in that range.
    """
    if line.b != 0:
        return _table_rows(line, largest)
    c = Fraction(line.c, line.a)
    return list(range(-largest, largest + 1)) if c.denominator <= 2 and abs(c) <= largest else []


def _shared_rows(answer: Line, lines: Sequence[Line], xs: set[int]) -> list[int]:
    """
    Return the x-values among ``xs``, in order, where a table of one of ``lines`` has the same
    row as the table of ``answer``, as ``choice_row`` gives them.
    """
    return [
        x for x in sorted(xs) if any(choice_row(line, x) == choice_row(answer, x) for line in lines)
    ]


def _even_runs(allowed: list[int], required: set[int], size: int) -> list[tuple[int, ...]]:
    """
    Return every run of ``size`` x-values among ``allowed`` that go up in equal steps of 2 or 5,
    or of the gap between the ``allowed`` values when that's another number, and hold all of
    ``required``.
    """
    gap = gcd(*(later - earlier for earlier, later in pairwise(allowed)))
    steps = [*EVEN_STEPS, *([gap] if gap > 1 and gap not in EVEN_STEPS else [])]
    present = set(allowed)
    runs = []
    for step in steps:
        for start in allowed:
            run = tuple(start + index * step for index in range(size))
            if present.issuperset(run) and required.issubset(run):
                runs.append(run)
    return runs


def _axis_step(largest: int) -> int:
    """
    Return how far apart a grid's gridlines are for coordinates from -``largest`` to
    ``largest``: 1, 2, 5, 10, 20, 50 and so on, the smallest that leaves ``GRID_LINES`` or fewer
    beyond each axis.
    """
    scale = 1
    while True:
        for multiplier in (1, 2, 5):
            if largest <= GRID_LINES * multiplier * scale:
                return multiplier * scale
        scale *= 10


def _inner(largest: int) -> int:
    """
    Return how far from the axes a graph's marked points can be: within -``largest`` to
    ``largest``, and at least a gridline inside the edge of the grid, which runs to the first
    gridline at or past ``largest``.
    """
    step = _axis_step(largest)
    return min(largest, ceil(largest / step) * step - step)


def _marked_points(line: Line, largest: int) -> list[Point]:
    """
    Return the points on ``line``, which isn't vertical, that a graph for coordinates from
    -``largest`` to ``largest`` can mark: where its gridlines cross, off the axes and inside its
    edge, as ``_inner`` says.
    """
    step = _axis_step(largest)
    return [(x, y) for x, y in _points_on(line, _inner(largest)) if x % step == 0 and y % step == 0]


def _graph_grid(line: Line, points: Sequence[Point], largest: int) -> Grid:
    """
    Return the grid a graph of ``line`` through ``points`` is drawn on, or the blank grid beside
    two points, for coordinates from -``largest`` to ``largest``.

    x runs to the first gridline at or past ``largest``, so every grid on a sheet has the same
    squares. y runs two gridlines past the points and the y-intercept, leaving room for the
    points' labels, and at least half as far as x, so the grid's height gives nothing away, and
    no further than x.
    """
    heights = [Fraction(abs(y)) for _, y in points]
    if line.y_intercept is not None:
        heights.append(abs(line.y_intercept))
    return _fitted_grid(heights, largest)


def _fitted_grid(heights: Sequence[Fraction], largest: int) -> Grid:
    """
    Return a grid for coordinates from -``largest`` to ``largest`` whose x runs to the first
    gridline at or past ``largest``, and whose y runs two gridlines past the largest of
    ``heights``, at least half as far as x and no further.
    """
    step = _axis_step(largest)
    largest_x = ceil(largest / step) * step
    needed = max(Fraction(largest, 2), max(heights, default=Fraction(0)) + 2 * step)
    return Grid(largest_x, min(largest_x, ceil(needed / step) * step), step)


def _on_gridlines(line: Line, step: int) -> bool:
    """Return whether ``line`` crosses each axis it crosses on a gridline ``step`` apart."""
    intercepts = (line.y_intercept, line.x_intercept)
    return all(value % step == 0 for value in intercepts if value is not None)
