"""
Random generation of questions about a line: its slope or an intercept, from an equation, a point
and slope, or two points; or its equation in a form, from those or from a parallel or
perpendicular line and a point.

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
from itertools import combinations, product
from math import gcd
from typing import Literal

from core.line_equations.data import (
    EQUATION_FORMS,
    EQUATION_GIVENS,
    X_AXIS,
    Y_AXIS,
    Line,
    LineAnswer,
    LineFeature,
    LineForm,
    LineQuestion,
    LineQuestionData,
    NumberStyle,
    Point,
    Relation,
    answer_of,
    line_answer,
    line_from,
)
from core.line_equations.representation import terminates
from core.line_equations.wrong_answers import wrong_answers
from core.question import FreeResponse, Question, multiple_choice

DEFAULT_LARGEST_COORDINATE = 10  # STAAR's grids mostly run to ±9 or ±10
DEFAULT_LARGEST_DENOMINATOR = 5
FUNCTION_NAMES = ("f", "g", "h")

# Which way a line runs
type Slant = Literal["sloped", "horizontal", "vertical"]

# How a line through two points runs, each as likely as it is frequent here: one time in forty
# horizontal and one in forty vertical, so about one in twenty is either, among the slants the
# forms given and the feature asked allow
TWO_POINT_SLANTS: tuple[Slant, ...] = ("sloped",) * 38 + ("horizontal", "vertical")
# Whether a sloped line passes through the origin: one time in twenty
THROUGH_ORIGIN = (True,) + (False,) * 19
# Whether the one point an equation is written from is where the line crosses the x-axis, as in
# A.2 2019 Q10 ("crosses the x-axis at 36"): one time in ten, which gives y = m(x - r) in
# point-slope form
X_AXIS_POINT = (True,) + (False,) * 9
# The forms a line a parallel or perpendicular line is found from is written in, each as likely
REFERENCE_FORMS = (LineForm.SLOPE_INTERCEPT, LineForm.STANDARD)

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
# The points each form shows; the other forms show none, and a relation shows the one point the
# line asked for passes through
_POINTS_SHOWN = {LineForm.POINT_SLOPE: 1, LineForm.POINT_AND_SLOPE: 1, LineForm.TWO_POINTS: 2}
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
_SHOWS_POINT = (LineForm.POINT_AND_SLOPE, LineForm.TWO_POINTS, *Relation)


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
      intercept;
    - with ``whole_intercepts``, both intercepts are whole numbers. Without it, they are any
      numbers the other rules allow, whole ones included;
    - a sloped line passes through the origin as ``THROUGH_ORIGIN`` has it, one time in twenty;
    - x = a and y = b show vertical and horizontal lines. A line through two points is
      vertical only while x = a is among ``givens``, and horizontal only while y = b is, as
      ``TWO_POINT_SLANTS`` has it, when the feature asked allows it. The other forms show lines
      that are neither;
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
    ``FUNCTION_NAMES``.

    Raises ``ValueError`` if ``givens`` or ``features`` is empty, if no pair can be asked, if
    ``largest_coordinate`` or
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
) -> list[LineQuestion]:
    """
    Generate ``count`` questions that each ask for the equation of a line in a form from
    ``forms``, from a line given in a way from ``givens``: a form, or a relation, which shows a
    line the answer is parallel or perpendicular to and a point the answer passes through.

    Each question takes the next pair of a given and a form from a shuffled deck of the pairs
    that can be asked, as ``generate_line_questions`` does. ``can_write`` says which can.

    Each line meets the rules ``generate_line_questions`` lists, with these differences:
    - a line whose equation is asked as x = a is vertical, as y = b horizontal, and in any other
      form neither, so two points or a point and slope give a vertical or horizontal line only
      when x = a or y = b is asked;
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
    intercepts all terminate, and so do those of the line it's found from. With a non-zero
    ``wrong_answer_count``, each question is multiple choice among its answer and that many wrong
    answers, made by ``wrong_answers``.

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
        )

    return _questions(count, pairs, build, wrong_answer_count)


def _questions[P](
    count: int,
    pairs: Sequence[P],
    build: Callable[[P, set[Line], set[LineAnswer]], LineQuestionData | None],
    wrong_answer_count: int,
) -> list[LineQuestion]:
    """
    Return ``count`` questions, each built by ``build`` from the next of ``pairs`` dealt from a
    shuffled deck, with the lines and answers already on the sheet, which it mustn't repeat.

    When ``build`` returns ``None`` for the pair dealt, because none of its lines has a new
    answer, the first other pair it returns a question for is used instead; the caller has
    counted that there is one. With a non-zero ``wrong_answer_count``, each question is multiple
    choice among its answer and that many wrong answers.
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
            choices = multiple_choice((answer,), wrong_answers(data, wrong_answer_count))
            questions.append(Question(data, choices))
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
    slant, shown = _slant(given, asked, givens), _POINTS_SHOWN.get(given, 0)
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
    return LineQuestionData(line, given, asked, points, as_point, numbers, function)


def _equation_data(
    given: LineForm | Relation,
    form: LineForm,
    *,
    largest_coordinate: int,
    largest_denominator: int,
    whole_intercepts: bool,
    number_styles: Sequence[NumberStyle],
    used: set[Line],
) -> LineQuestionData | None:
    """
    Draw a question's number style, point-slope style and shares, and return its data with a
    line that meets the rules ``generate_equation_questions`` lists and isn't in ``used``, and
    the line it's found from, if it has a relation. Returns ``None`` when no new line does.
    """
    numbers = random.choice(number_styles)
    solved_for_y = given is LineForm.POINT_SLOPE and random.choice((False, True))
    relation = given if isinstance(given, Relation) else None
    slant, shown = _FORM_SLANTS.get(form, "sloped"), _points_shown(given)
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
    return LineQuestionData(
        line,
        shown_form,
        form,
        points,
        numbers=numbers,
        reference=reference,
        relation=relation,
        solved_for_y=solved_for_y,
    )


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

    def shape(form: LineForm) -> tuple[Slant, int]:
        return _FORM_SLANTS.get(form, "sloped"), _points_shown(form)

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

    def shape(given: LineForm | Relation, form: LineForm) -> tuple[Slant, int, Relation | None]:
        relation = given if isinstance(given, Relation) else None
        return _FORM_SLANTS.get(form, "sloped"), _points_shown(given), relation

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
    are asked of two points, a point and slope, or a relation, never of another equation. Slope-
    intercept and standard forms are asked of any given but themselves. A point and slope and two
    points aren't equations, so they can't be asked.
    """
    match form:
        case LineForm.POINT_SLOPE | LineForm.VERTICAL | LineForm.HORIZONTAL:
            return given in _SHOWS_POINT
        case LineForm.SLOPE_INTERCEPT | LineForm.STANDARD:
            return given != form
        case _:
            return False


def _points_shown(given: LineForm | Relation) -> int:
    """Return how many points a line given as ``given`` shows: a relation shows one."""
    return 1 if isinstance(given, Relation) else _POINTS_SHOWN.get(given, 0)


def _slant(given: LineForm, asked: LineFeature, givens: Sequence[LineForm]) -> Slant:
    """
    Return which way the question's line runs, drawn for two points from ``TWO_POINT_SLANTS``:
    vertical only while x = a is among ``givens``, horizontal only while y = b is, and only when
    the line has the feature ``asked``.
    """
    match given:
        case LineForm.VERTICAL:
            return "vertical"
        case LineForm.HORIZONTAL:
            return "horizontal"
        case LineForm.TWO_POINTS:
            return random.choice(
                [
                    slant
                    for slant in TWO_POINT_SLANTS
                    if asked in _FEATURES_OF[slant]
                    and (slant == "sloped" or _FORM_OF[slant] in givens)
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
    slant: Slant, shown: int, rules: _Rules, limit: int, key: Callable[[Line], K]
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


def _lines(slant: Slant, shown: int, rules: _Rules) -> Iterator[Line]:
    """
    Yield the lines running as ``slant`` says that meet ``rules`` with ``shown`` points, ignoring
    ``rules.x_axis_point``, a share.
    """
    if slant != "sloped":
        yield from (_level(slant, number) for number in _level_numbers(slant, shown, rules))
        return
    for slope in _slopes(rules):
        references = _reference_intercepts(slope, rules)
        for intercept in _y_intercepts(slope, rules):
            if not _has_reference(intercept, references, rules.relation):
                continue
            line = line_from(-slope, Fraction(1), intercept)
            if not shown or len(_points_on(line, rules.largest_coordinate)) >= shown:
                yield line


def _line(slant: Slant, shown: int, rules: _Rules) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a line running as ``slant`` says that meets ``rules``, and ``shown`` points on it, or
    ``None`` if no line does.
    """
    if slant == "sloped":
        return _sloped_line(shown, rules)
    return _level_line(slant, shown, rules)


def _sloped_line(shown: int, rules: _Rules) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a line that isn't vertical or horizontal, and ``shown`` points on it, drawn at random
    from those on it within the coordinates allowed.

    The slope is drawn first, then the y-intercept. A slope or y-intercept that leaves too few
    points to show, or with a relation, no line to be parallel or perpendicular to, is set aside
    and another drawn, until none is left, giving ``None``. With ``rules.x_axis_point``, the one
    point shown is where the line crosses the x-axis.
    """
    slopes = _slopes(rules)
    while slopes:
        slope = random.choice(slopes)
        references = _reference_intercepts(slope, rules)
        intercepts = _y_intercepts(slope, rules) if references != [] else []
        while intercepts:
            intercept = random.choice(intercepts)
            if not _has_reference(intercept, references, rules.relation):
                intercepts.remove(intercept)
                continue
            line = line_from(-slope, Fraction(1), intercept)
            if not shown:
                return line, ()
            if rules.x_axis_point:
                points = _x_axis_points(line)
            else:
                points = _points_on(line, rules.largest_coordinate)
            if len(points) >= shown:
                return line, tuple(random.sample(points, shown))
            intercepts.remove(intercept)
        slopes.remove(slope)
    return None


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
    slant: Literal["horizontal", "vertical"], shown: int, rules: _Rules
) -> tuple[Line, tuple[Point, ...]] | None:
    """
    Return a horizontal line, y = b, or a vertical one, x = a, its number drawn from those that
    meet ``rules``, and ``shown`` points on it, or ``None`` if no number does. A line with points
    shown has a whole number other than 0, so its points have whole-number coordinates and lie
    off the axes.
    """
    candidates = _level_numbers(slant, shown, rules)
    if not candidates:
        return None
    number = random.choice(candidates)
    line = _level(slant, number)
    if not shown:
        return line, ()
    largest = rules.largest_coordinate
    others = [other for other in range(-largest, largest + 1) if other != 0]
    if slant == "vertical":
        points = [(int(number), y) for y in others]
    else:
        points = [(x, int(number)) for x in others]
    return line, tuple(random.sample(points, shown))


def _level_numbers(
    slant: Literal["horizontal", "vertical"], shown: int, rules: _Rules
) -> list[Fraction]:
    """
    Return the numbers a horizontal or vertical line can have under ``rules``, in order. With
    points shown, the number is whole and not 0, so the points lie off the axes.
    """
    largest = rules.largest_coordinate
    # with points shown, only whole numbers, which saves listing every fraction
    denominators = range(1, rules.largest_denominator + 1) if not shown else (1,)
    numbers = sorted(
        {
            Fraction(numerator, denominator)
            for denominator in denominators
            for numerator in range(-largest * denominator, largest * denominator + 1)
        }
    )
    return [
        number
        for number in numbers
        if _meets(_level(slant, number), rules) and not (shown and number == 0)
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


def _y_intercepts(slope: Fraction, rules: _Rules) -> list[Fraction]:
    """
    Return the y-intercepts that a line with ``slope`` can have under ``rules``.

    Each is a whole number of the slope's denominator's parts, so that the line has points with
    whole-number coordinates: for a slope of 3/4, the y-intercept is a number of quarters. It is
    0 for a line through the origin, and never 0 otherwise.
    """
    parts = slope.denominator
    largest = rules.largest_coordinate * parts
    return [
        Fraction(numerator, parts)
        for numerator in range(-largest, largest + 1)
        if (rules.origin is None or (numerator == 0) == rules.origin)
        and _meets(line_from(-slope, Fraction(1), Fraction(numerator, parts)), rules)
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
