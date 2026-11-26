"""
Tests for what a comparing fractions question shows: its question, the work under its pictures
and its answer key entry as written maths, its answer line, its choices and reasons as written
maths, and its tile question.

The stories are taken from the end of each bank, where tests' stories stay as new ones go on at
the top: the pizza (last) and the book (third from last) of the wholes; the worm (last), the frog
(third from last) and the walk home (fourth from last) of the lengths; the blocks (last) of the
groups.
"""

import pytest

from core.comparing_fractions.data import (
    ALL_OF_THESE,
    CANT_TELL,
    LESS,
    MORE,
    SAME,
    BiggerNumber,
    CompareQuestionData,
    ComparingFractionsQuestionData,
    Comparison,
    DrawAsked,
    DrawQuestionData,
    EveryQuestionData,
    ExplainForm,
    ExplainQuestionData,
    Explanation,
    GreatestQuestionData,
    LessGreaterForm,
    LessGreaterQuestionData,
    PartSize,
    PartsOf,
    Pick,
    Picture,
    Reason,
    SameCount,
    StoryChoice,
    StoryForm,
    StoryKind,
    StoryReason,
    Verdict,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.representation import (
    answer_line,
    choice_pieces,
    comparing_fractions_tile_question,
    comparison_pieces,
    explanation_pieces,
    question,
    reason_text,
    solution,
    story_choice_pieces,
    tile_answer,
    work,
    writing_lines,
)
from core.comparing_fractions.stories import GROUP_STORIES, LENGTH_STORIES, WHOLE_STORIES
from core.drawn_objects import DrawnObject
from core.fraction_models.area_models import (
    AreaModel,
    Circle,
    FractionWall,
    Grid,
    RadialPartition,
    RegularPolygon,
    Strip,
    equal_sizes,
)
from core.fraction_models.number_lines import FractionLine, LengthUnit
from core.fraction_models.object_groups import ObjectGroup
from core.question import CIRCLE
from core.self_check_tiles import TileQuestion
from core.written_numbers import Pieces, UnreducedFraction

PIZZA, BOOK = len(WHOLE_STORIES) - 1, len(WHOLE_STORIES) - 3
WORM, FROG, WALK = len(LENGTH_STORIES) - 1, len(LENGTH_STORIES) - 3, len(LENGTH_STORIES) - 4
BLOCKS = len(GROUP_STORIES) - 1
WHOLE, LENGTH, GROUP = StoryKind
WHO, SENTENCE = WordAsked
CIRCLE_WORDS, WRITE, PAIR, WHY = ExplainForm
DIVIDE, CIRCLE_EVERY, WRITE_ONE, NOT_A_WAY, SHOWS = LessGreaterForm
SYMBOL, GREATER, LESS_ONE = DrawAsked
REASONS, WHO_SYMBOL, PLAIN = StoryForm
TO_COMPARE = f"  {CIRCLE}  "  # the circle between two fractions to write the symbol in
GAP = "        "  # between two fractions to circle
SYMBOLS = "  ( >   <   = )  "  # the symbols to circle
STORY = "Ana and Ben each have a pizza. The pizzas are the same size. Ana eats "


def _f(numerator: int, denominator: int) -> UnreducedFraction:
    """Return a fraction as written."""
    return UnreducedFraction(numerator, denominator)


def _strip(parts: int, shaded: int = 0) -> AreaModel:
    """Return a strip of ``parts`` equal parts, the first ``shaded`` of them shaded."""
    return AreaModel(Strip(equal_sizes(parts)), frozenset(range(shaded)))


TWO_THIRDS, TWO_FOURTHS = _f(2, 3), _f(2, 4)
THIRD, FOURTH = _f(1, 3), _f(1, 4)
AREA = (_strip(3, 2), _strip(4, 2))
LINES = (FractionLine(3, jumps=2), FractionLine(4, jumps=2))
GROUPS = (
    ObjectGroup(DrawnObject.BLOCK, 3, 4, frozenset({0, 1})),
    ObjectGroup(DrawnObject.BLOCK, 4, 4, frozenset({0, 1})),
)
WALL = FractionWall((1, 3, 4), labelled=False)
FIVE_SIXTHS_EXPLAINED = Explanation(Comparison(_f(5, 6), ">", _f(5, 8)), PartSize(6, 8, True))
SIX_EIGHTHS_EXPLAINED = Explanation(
    Comparison(_f(6, 8), "<", _f(8, 8)), PartsOf(_f(6, 8), _f(8, 8), False)
)


def _word(
    kind: StoryKind,
    story: int,
    pair: tuple[UnreducedFraction, UnreducedFraction] = (THIRD, FOURTH),
    answer: str = "Ana",
    *,
    unit: LengthUnit | None = None,
    sizes: tuple[str, str] | None = None,
    greater: bool = True,
    more_or_less: bool = False,
    asked: WordAsked = WHO,
    form: StoryForm | None = None,
) -> WordQuestionData:
    """Return a word problem of Ana and Ben."""
    return WordQuestionData(
        kind,
        story,
        ("Ana", "Ben"),
        pair,
        unit,
        sizes,
        greater,
        more_or_less,
        asked,
        form,
        (),
        answer,
    )


def _greatest(
    fractions: tuple[UnreducedFraction, ...],
    greatest: bool,
    pictures: tuple[Picture, ...] = (),
    wall: FractionWall | None = None,
) -> GreatestQuestionData:
    """Return a greatest or least question, its answer worked out."""
    pick = max if greatest else min
    answer = pick(fractions, key=lambda each: each.value)
    return GreatestQuestionData(fractions, greatest, pictures, wall, answer)


@pytest.mark.parametrize(
    ("data", "choices", "tiles", "expected_question", "expected_work"),
    [
        # compare, written: the symbol in a circle between the fractions
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, False, ">"),
            False,
            False,
            ("Write >, <, or =.",),
            (TWO_THIRDS, TO_COMPARE, TWO_FOURTHS),
        ),
        # with pictures, the fractions too, on blanks
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), AREA, None, False, ">"),
            False,
            False,
            ("Write the fraction each model shows. Then write >, <, or =.",),
            (f"________{TO_COMPARE}________",),
        ),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), LINES, None, False, ">"),
            False,
            False,
            ("Write the fraction each number line shows. Then write >, <, or =.",),
            (f"________{TO_COMPARE}________",),
        ),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), WALL, False, ">"),
            False,
            False,
            ("Use the fraction strips. Write >, <, or =.",),
            (TWO_THIRDS, TO_COMPARE, TWO_FOURTHS),
        ),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), GROUPS, None, False, ">"),
            True,
            False,
            ("The groups show two fractions. Which comparison is true?",),
            (),
        ),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), WALL, False, ">"),
            True,
            False,
            ("Use the fraction strips. Which comparison is true?",),
            (),
        ),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, True, ">"),
            True,
            False,
            ("Which comparison is true?",),
            (),
        ),
        # every fraction greater, or less
        (
            EveryQuestionData(_f(3, 8), True, (_f(3, 4), _f(5, 8), _f(1, 8)), (_f(3, 4), _f(5, 8))),
            False,
            False,
            ("Circle every fraction greater than ", _f(3, 8), "."),
            (_f(3, 4), GAP, _f(5, 8), GAP, _f(1, 8)),
        ),
        (
            EveryQuestionData(_f(3, 8), False, (_f(3, 4), _f(5, 8), _f(1, 8)), (_f(1, 8),)),
            True,
            False,
            ("Which fraction is less than ", _f(3, 8), "?"),
            (),
        ),
        (
            EveryQuestionData(
                _f(3, 8), True, (_f(3, 4), _f(5, 8), _f(3, 6)), (_f(3, 4), _f(5, 8), _f(3, 6))
            ),
            False,
            True,
            (
                "Which of these are greater than ",
                _f(3, 8),
                ": ",
                _f(3, 4),
                ", ",
                _f(5, 8),
                ", ",
                _f(3, 6),
                "?",
            ),
            (),
        ),
        # explain: the symbol and the words to circle
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, CIRCLE_WORDS, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            False,
            ("Circle the symbol and the words that make the sentence true.",),
            (_f(5, 6), SYMBOLS, _f(5, 8), " because ( sixths / eighths ) are larger parts."),
        ),
        (
            ExplainQuestionData(
                (_f(6, 8), _f(8, 8)), (), None, False, CIRCLE_WORDS, SIX_EIGHTHS_EXPLAINED
            ),
            False,
            False,
            ("Circle the symbol and the words that make the sentence true.",),
            (
                _f(6, 8),
                SYMBOLS,
                _f(8, 8),
                " because 6 out of 8 equal parts is ( more than / less than ) 8 out of 8 equal "
                "parts.",
            ),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), WALL, False, CIRCLE_WORDS, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            False,
            (
                "Use the fraction strips. Circle the symbol and the words that make the sentence "
                "true.",
            ),
            (_f(5, 6), SYMBOLS, _f(5, 8), " because ( sixths / eighths ) are larger parts."),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), AREA, None, False, PAIR, FIVE_SIXTHS_EXPLAINED
            ),
            True,
            False,
            ("The models show two fractions. Which comparison and explanation are true?",),
            (),
        ),
        # word problems: who, with the comparison to write
        (
            _word(WHOLE, PIZZA),
            False,
            False,
            (
                STORY,
                THIRD,
                " of a pizza. Ben eats ",
                FOURTH,
                " of a pizza. Who eats more pizza? ________",
            ),
            ("Write >, <, or =:  ", THIRD, TO_COMPARE, FOURTH),
        ),
        # the sentence, its reasons the numerator's: 1 part, not parts
        (
            _word(WHOLE, PIZZA, asked=SENTENCE),
            False,
            False,
            (
                STORY,
                THIRD,
                " of a pizza. Ben eats ",
                FOURTH,
                " of a pizza. Circle the words that make the sentence true.",
            ),
            (
                "Ana eats ( more than / less than / the same amount as ) Ben because ( thirds are "
                "larger than fourths / fourths are larger than thirds / both have 1 part ).",
            ),
        ),
        # a shared denominator's reasons count the parts
        (
            _word(WHOLE, PIZZA, (_f(3, 8), _f(1, 8)), asked=SENTENCE),
            False,
            False,
            (
                STORY,
                _f(3, 8),
                " of a pizza. Ben eats ",
                _f(1, 8),
                " of a pizza. Circle the words that make the sentence true.",
            ),
            (
                "Ana eats ( more than / less than / the same amount as ) Ben because ( 3 eighths "
                "is more than 1 eighth / 1 eighth is more than 3 eighths / both are eighths ).",
            ),
        ),
        (
            _word(WHOLE, PIZZA, form=REASONS),
            True,
            False,
            (
                STORY,
                THIRD,
                " of a pizza. Ben eats ",
                FOURTH,
                " of a pizza. Which statement is true?",
            ),
            (),
        ),
        # brief choices follow the question itself
        (
            _word(WHOLE, PIZZA, form=WHO_SYMBOL, greater=False),
            True,
            False,
            (STORY, THIRD, " of a pizza. Ben eats ", FOURTH, " of a pizza. Who eats less pizza?"),
            (),
        ),
        (
            _word(WHOLE, PIZZA, answer=MORE, more_or_less=True),
            False,
            True,
            (
                STORY,
                THIRD,
                " of a pizza. Ben eats ",
                FOURTH,
                " of a pizza. Does Ana eat more or less pizza than Ben?",
            ),
            (),
        ),
        # wholes of different sizes
        (
            _word(WHOLE, PIZZA, (_f(5, 8), _f(3, 8)), CANT_TELL, sizes=("small", "large")),
            False,
            False,
            (
                "Ana and Ben each have a pizza. One pizza is small and the other is large. Ana "
                "eats ",
                _f(5, 8),
                " of the small pizza. Ben eats ",
                _f(3, 8),
                " of the large pizza. Who eats more pizza? ________",
            ),
            ("Write >, <, or =:  ", _f(5, 8), TO_COMPARE, _f(3, 8)),
        ),
        # one whole: no "same size", "of the book"
        (
            _word(WHOLE, BOOK, greater=False),
            False,
            True,
            (
                "Ana and Ben are reading the same book. Ana reads ",
                THIRD,
                " of the book. Ben reads ",
                FOURTH,
                " of the book. Who reads less of the book?",
            ),
            (),
        ),
        # lengths: a thing of each person's, or the person
        (
            _word(LENGTH, WORM, unit=LengthUnit.INCH, greater=False),
            False,
            False,
            (
                "Ana and Ben each measure a worm. Ana's worm is ",
                THIRD,
                " inch long. Ben's worm is ",
                FOURTH,
                " inch long. Whose worm is shorter? ________",
            ),
            ("Write >, <, or =:  ", THIRD, TO_COMPARE, FOURTH),
        ),
        (
            _word(LENGTH, WORM, unit=LengthUnit.INCH, asked=SENTENCE),
            False,
            False,
            (
                "Ana and Ben each measure a worm. Ana's worm is ",
                THIRD,
                " inch long. Ben's worm is ",
                FOURTH,
                " inch long. Circle the words that make the sentence true.",
            ),
            (
                "Ana's worm is ( longer than / shorter than / the same length as ) Ben's because "
                "( thirds are larger than fourths / fourths are larger than thirds / both have 1 "
                "part ).",
            ),
        ),
        (
            _word(LENGTH, FROG, answer=MORE, unit=LengthUnit.FOOT, more_or_less=True),
            False,
            True,
            (
                "Ana and Ben each have a frog in a jumping contest. Ana's frog jumps ",
                THIRD,
                " foot. Ben's frog jumps ",
                FOURTH,
                " foot. Does Ana's frog jump more or less than Ben's?",
            ),
            (),
        ),
        (
            _word(LENGTH, WALK, unit=LengthUnit.MILE),
            False,
            True,
            (
                "Ana and Ben each walk home from school. Ana walks ",
                THIRD,
                " mile. Ben walks ",
                FOURTH,
                " mile. Who walks farther?",
            ),
            (),
        ),
        (
            _word(LENGTH, WALK, answer=LESS, unit=LengthUnit.MILE, more_or_less=True),
            False,
            True,
            (
                "Ana and Ben each walk home from school. Ana walks ",
                THIRD,
                " mile. Ben walks ",
                FOURTH,
                " mile. Does Ana walk more or less than Ben?",
            ),
            (),
        ),
        (
            _word(LENGTH, WALK, unit=LengthUnit.MILE, asked=SENTENCE),
            False,
            False,
            (
                "Ana and Ben each walk home from school. Ana walks ",
                THIRD,
                " mile. Ben walks ",
                FOURTH,
                " mile. Circle the words that make the sentence true.",
            ),
            (
                "Ana walks ( farther than / a shorter distance than / the same distance as ) Ben "
                "because ( thirds are larger than fourths / fourths are larger than thirds / both "
                "have 1 part ).",
            ),
        ),
        # groups: counts, not fractions
        (
            _word(GROUP, BLOCKS, (TWO_THIRDS, TWO_FOURTHS), greater=False),
            False,
            False,
            (
                "Ana and Ben are painting blocks. Ana has 3 blocks and paints 2 of them. Ben has 4 "
                "blocks and paints 2 of them. Who paints a smaller fraction of their blocks? "
                "________",
            ),
            ("Write >, <, or =:  ", TWO_THIRDS, TO_COMPARE, TWO_FOURTHS),
        ),
        # less or greater than a model, each blank named
        (
            LessGreaterQuestionData(
                _f(4, 6), False, DIVIDE, _strip(6, 4), _strip(1), (), (_f(1, 6),)
            ),
            False,
            False,
            (
                "Divide and shade each blank strip to show a different fraction less than ",
                _f(4, 6),
                ".",
            ),
            (),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6),
                True,
                DIVIDE,
                AreaModel(Grid(2, 3)),
                AreaModel(Grid(1, 1)),
                (),
                (_f(5, 6),),
            ),
            False,
            False,
            (
                "Divide and shade each blank rectangle to show a different fraction greater than ",
                _f(4, 6),
                ".",
            ),
            (),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6),
                True,
                NOT_A_WAY,
                AreaModel(RadialPartition(Circle(), equal_sizes(6))),
                AreaModel(RadialPartition(Circle(), equal_sizes(1))),
                (),
                (_f(4, 8),),
            ),
            True,
            False,
            (
                "The model shows ",
                _f(4, 6),
                ". Which is NOT a way to show a fraction greater than ",
                _f(4, 6),
                "?",
            ),
            (),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6), False, SHOWS, _strip(6, 4), _strip(1), (), (_f(3, 6),)
            ),
            True,
            False,
            (
                "The model shows ",
                _f(4, 6),
                ". Which model shows a fraction less than ",
                _f(4, 6),
                "?",
            ),
            (),
        ),
        # circle every model, or write a way of each kind there is
        (
            LessGreaterQuestionData(
                _f(4, 6),
                False,
                CIRCLE_EVERY,
                _strip(6, 4),
                _strip(1),
                (_strip(6, 3), _strip(6, 5), _strip(8, 4), _strip(4, 4)),
                (_f(3, 6), _f(4, 8)),
            ),
            False,
            False,
            (
                "The model shows ",
                _f(4, 6),
                ". Circle every model that shows a fraction less than ",
                _f(4, 6),
                ".",
            ),
            (),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6), True, WRITE_ONE, _strip(6, 4), _strip(1), (), (_f(5, 6), _f(4, 5))
            ),
            False,
            False,
            ("The model shows ", _f(4, 6), ". Write a fraction greater than ", _f(4, 6), "."),
            ("Same denominator: ________        Same numerator: ________",),
        ),
        (
            LessGreaterQuestionData(
                _f(1, 6), False, WRITE_ONE, _strip(6, 1), _strip(1), (), (_f(1, 7), _f(1, 8))
            ),
            False,
            False,
            ("The model shows ", _f(1, 6), ". Write a fraction less than ", _f(1, 6), "."),
            ("Same numerator: ________",),
        ),
        # draw and compare
        (
            DrawQuestionData(
                (TWO_THIRDS, TWO_FOURTHS),
                (AreaModel(RadialPartition(RegularPolygon(6), equal_sizes(1))),) * 2,
                SYMBOL,
                ">",
            ),
            False,
            False,
            (
                "Divide and shade the shapes to show ",
                TWO_THIRDS,
                " and ",
                TWO_FOURTHS,
                ". Then write >, <, or =.",
            ),
            (TWO_THIRDS, TO_COMPARE, TWO_FOURTHS),
        ),
        (
            DrawQuestionData(
                (TWO_THIRDS, TWO_FOURTHS),
                (AreaModel(RadialPartition(Circle(), equal_sizes(1))),) * 2,
                SYMBOL,
                ">",
            ),
            True,
            False,
            (
                "Divide and shade the circles to show ",
                TWO_THIRDS,
                " and ",
                TWO_FOURTHS,
                ". Which comparison is true?",
            ),
            (),
        ),
        (
            DrawQuestionData(
                (TWO_THIRDS, TWO_FOURTHS), (FractionLine(1), FractionLine(1)), SYMBOL, ">"
            ),
            False,
            False,
            (
                "Mark ",
                TWO_THIRDS,
                " on the first number line and ",
                TWO_FOURTHS,
                " on the second. Then write >, <, or =.",
            ),
            (TWO_THIRDS, TO_COMPARE, TWO_FOURTHS),
        ),
        # which fraction is greater, or less, after drawing
        (
            DrawQuestionData(
                (TWO_THIRDS, TWO_FOURTHS),
                (AreaModel(RadialPartition(Circle(), equal_sizes(1))),) * 2,
                GREATER,
                ">",
            ),
            False,
            False,
            (
                "Divide and shade the circles to show ",
                TWO_THIRDS,
                " and ",
                TWO_FOURTHS,
                ". Which fraction is greater?",
            ),
            (),
        ),
        (
            DrawQuestionData((TWO_THIRDS, TWO_FOURTHS), (FractionLine(1),) * 2, LESS_ONE, ">"),
            True,
            False,
            (
                "Mark ",
                TWO_THIRDS,
                " on the first number line and ",
                TWO_FOURTHS,
                " on the second. Which fraction is less?",
            ),
            (),
        ),
        # explain: write and explain, or which reason explains a true comparison
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, WRITE, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            False,
            ("Write >, <, or =. Then explain how you know.",),
            (_f(5, 6), TO_COMPARE, _f(5, 8)),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), WALL, False, WRITE, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            False,
            ("Use the fraction strips. Write >, <, or =. Then explain how you know.",),
            (_f(5, 6), TO_COMPARE, _f(5, 8)),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), AREA, None, False, WHY, FIVE_SIXTHS_EXPLAINED
            ),
            True,
            False,
            ("The models show two fractions. ", _f(5, 6), " > ", _f(5, 8), ". Which explains why?"),
            (),
        ),
        # the greatest or least
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True),
            False,
            False,
            ("Circle the greatest fraction.",),
            (_f(2, 3), GAP, _f(2, 6), GAP, _f(2, 8)),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), False, wall=WALL),
            False,
            False,
            ("Use the fraction strips. Circle the least fraction.",),
            (_f(2, 3), GAP, _f(2, 6), GAP, _f(2, 8)),
        ),
        (
            _greatest((TWO_THIRDS, TWO_FOURTHS), True, AREA),
            False,
            False,
            ("Each model shows a fraction. Which fraction is greater?",),
            (),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True, (*LINES, FractionLine(8, jumps=2))),
            False,
            False,
            ("Each number line shows a fraction. Which fraction is the greatest?",),
            (),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), False, (*AREA, _strip(8, 2))),
            True,
            False,
            ("Which model shows the least fraction?",),
            (),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True),
            True,
            False,
            ("Which fraction is the greatest?",),
            (),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), False, wall=WALL),
            True,
            False,
            ("Use the fraction strips. Which fraction is the least?",),
            (),
        ),
        # on tiles: two, "Which is greater?", or three or four, "Which is the greatest?"
        (
            _greatest((_f(3, 6), _f(3, 8)), True),
            False,
            True,
            ("Which is greater, ", _f(3, 6), " or ", _f(3, 8), "?"),
            (),
        ),
        (
            _greatest((_f(3, 8), _f(3, 6)), False, wall=WALL),
            False,
            True,
            ("Use the fraction strips. Which is less, ", _f(3, 8), " or ", _f(3, 6), "?"),
            (),
        ),
        (
            _greatest((_f(3, 4), _f(3, 6), _f(3, 8)), True),
            False,
            True,
            ("Which is the greatest: ", _f(3, 4), ", ", _f(3, 6), ", or ", _f(3, 8), "?"),
            (),
        ),
        (
            _greatest((_f(1, 8), _f(2, 8), _f(5, 8), _f(7, 8)), False),
            False,
            True,
            (
                "Which is the least: ",
                _f(1, 8),
                ", ",
                _f(2, 8),
                ", ",
                _f(5, 8),
                ", or ",
                _f(7, 8),
                "?",
            ),
            (),
        ),
        (
            _greatest((TWO_THIRDS, TWO_FOURTHS), False, GROUPS),
            False,
            True,
            ("Each group shows a fraction. Which fraction is less?",),
            (),
        ),
    ],
)
def test_question_and_work(
    data: ComparingFractionsQuestionData,
    choices: bool,
    tiles: bool,
    expected_question: Pieces,
    expected_work: Pieces,
) -> None:
    assert (question(data, choices, tiles), work(data, choices, tiles)) == (
        expected_question,
        expected_work,
    )


@pytest.mark.parametrize(
    ("data", "choices", "tiles", "expected"),
    [
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True, (*AREA, _strip(8, 2))),
            False,
            False,
            True,
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True, (*AREA, _strip(8, 2))),
            True,
            False,
            False,
        ),
        (_greatest((TWO_THIRDS, TWO_FOURTHS), True, AREA), False, True, False),
        (_greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True), False, False, False),
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), AREA, None, False, ">"),
            False,
            False,
            False,
        ),
        # the fraction that's greater (or less) of two drawn, written
        (
            DrawQuestionData((TWO_THIRDS, TWO_FOURTHS), (FractionLine(1),) * 2, GREATER, ">"),
            False,
            False,
            True,
        ),
        (
            DrawQuestionData((TWO_THIRDS, TWO_FOURTHS), (FractionLine(1),) * 2, GREATER, ">"),
            True,
            False,
            False,
        ),
        (
            DrawQuestionData((TWO_THIRDS, TWO_FOURTHS), (FractionLine(1),) * 2, SYMBOL, ">"),
            False,
            False,
            False,
        ),
    ],
)
def test_answer_line(
    data: ComparingFractionsQuestionData, choices: bool, tiles: bool, expected: bool
) -> None:
    """Only a written greatest or least question with pictures, or a written question asking
    which of two drawn fractions is greater (or less), has its answer on a line."""
    assert answer_line(data, choices, tiles) is expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # a comparison, with its reason
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, False, ">"),
            (TWO_THIRDS, " > ", TWO_FOURTHS, ": thirds are larger than fourths"),
        ),
        (
            DrawQuestionData((_f(3, 8), _f(5, 8)), (FractionLine(1), FractionLine(1)), SYMBOL, "<"),
            (
                _f(3, 8),
                " < ",
                _f(5, 8),
                ": 3 out of 8 equal parts is less than 5 out of 8 equal parts",
            ),
        ),
        (
            CompareQuestionData((_f(3, 8), _f(3, 8)), (), None, False, "="),
            (_f(3, 8), " = ", _f(3, 8), ": the same fraction"),
        ),
        # every one greater (or less): all, none, one or two
        (
            EveryQuestionData(
                _f(3, 8), True, (_f(3, 4), _f(5, 8), _f(3, 6)), (_f(3, 4), _f(5, 8), _f(3, 6))
            ),
            (_f(3, 4), ", ", _f(5, 8), ", and ", _f(3, 6), " are all greater than ", _f(3, 8)),
        ),
        (
            EveryQuestionData(_f(2, 6), False, (_f(5, 6), _f(4, 6), _f(6, 6)), ()),
            ("None of them is less than ", _f(2, 6)),
        ),
        (
            EveryQuestionData(_f(3, 8), True, (_f(3, 4), _f(5, 8), _f(1, 8)), (_f(5, 8),)),
            (_f(5, 8), " is greater than ", _f(3, 8)),
        ),
        (
            EveryQuestionData(_f(3, 8), True, (_f(3, 4), _f(5, 8), _f(1, 8)), (_f(3, 4), _f(5, 8))),
            (_f(3, 4), " and ", _f(5, 8), " are greater than ", _f(3, 8)),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, CIRCLE_WORDS, FIVE_SIXTHS_EXPLAINED
            ),
            (_f(5, 6), " > ", _f(5, 8), ", because sixths are larger than eighths"),
        ),
        # word problems: who, more or less, the same, can't tell, or the words to circle
        (_word(WHOLE, PIZZA), ("Ana: ", THIRD, " > ", FOURTH)),
        (_word(WHOLE, PIZZA, answer="Ben", greater=False), ("Ben: ", FOURTH, " < ", THIRD)),
        (_word(WHOLE, PIZZA, answer=MORE, more_or_less=True), ("more: ", THIRD, " > ", FOURTH)),
        (
            _word(WHOLE, PIZZA, (_f(3, 8), _f(3, 8)), SAME),
            ("The same: ", _f(3, 8), " = ", _f(3, 8)),
        ),
        (
            _word(WHOLE, PIZZA, (_f(5, 8), _f(3, 8)), CANT_TELL, sizes=("small", "large")),
            ("Can't tell: the pizzas are different sizes; ", _f(5, 8), " > ", _f(3, 8)),
        ),
        (
            _word(WHOLE, PIZZA, asked=SENTENCE),
            ("more than, because thirds are larger than fourths",),
        ),
        (
            _word(WHOLE, PIZZA, (_f(3, 8), _f(5, 8)), "Ben", asked=SENTENCE),
            ("less than, because 5 eighths is more than 3 eighths",),
        ),
        (
            _word(LENGTH, WORM, unit=LengthUnit.INCH, asked=SENTENCE),
            ("longer than, because thirds are larger than fourths",),
        ),
        # less or greater: some ways, or the one that isn't
        (
            LessGreaterQuestionData(
                _f(4, 6), False, DIVIDE, _strip(6, 4), _strip(1), (), (_f(1, 6), _f(2, 6), _f(4, 8))
            ),
            ("For example: ", _f(1, 6), ", ", _f(2, 6), ", ", _f(4, 8)),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6), False, NOT_A_WAY, _strip(6, 4), _strip(1), (), (_f(5, 6),)
            ),
            (_f(5, 6), " is not less than ", _f(4, 6)),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6), False, SHOWS, _strip(6, 4), _strip(1), (), (_f(3, 6),)
            ),
            (_f(3, 6), " is less than ", _f(4, 6)),
        ),
        # circle every model: one, two or three of them
        (
            LessGreaterQuestionData(
                _f(4, 6), False, CIRCLE_EVERY, _strip(6, 4), _strip(1), (), (_f(3, 6),)
            ),
            (_f(3, 6), " is less than ", _f(4, 6)),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6), False, CIRCLE_EVERY, _strip(6, 4), _strip(1), (), (_f(3, 6), _f(4, 8))
            ),
            (_f(3, 6), " and ", _f(4, 8), " are less than ", _f(4, 6)),
        ),
        (
            LessGreaterQuestionData(
                _f(4, 6),
                False,
                CIRCLE_EVERY,
                _strip(6, 4),
                _strip(1),
                (),
                (_f(1, 6), _f(3, 6), _f(4, 8)),
            ),
            (_f(1, 6), ", ", _f(3, 6), ", and ", _f(4, 8), " are less than ", _f(4, 6)),
        ),
        # write a way: every one of each kind
        (
            LessGreaterQuestionData(
                _f(4, 6),
                False,
                WRITE_ONE,
                _strip(6, 4),
                _strip(1),
                (),
                (_f(1, 6), _f(2, 6), _f(3, 6), _f(4, 7), _f(4, 8)),
            ),
            (
                "Same denominator: ",
                _f(1, 6),
                ", ",
                _f(2, 6),
                " or ",
                _f(3, 6),
                "; same numerator: ",
                _f(4, 7),
                " or ",
                _f(4, 8),
            ),
        ),
        (
            LessGreaterQuestionData(
                _f(1, 6), False, WRITE_ONE, _strip(6, 1), _strip(1), (), (_f(1, 7), _f(1, 8))
            ),
            ("Same numerator: ", _f(1, 7), " or ", _f(1, 8)),
        ),
        # which of two drawn is greater (or less)
        (
            DrawQuestionData((TWO_THIRDS, TWO_FOURTHS), (FractionLine(1),) * 2, GREATER, ">"),
            (TWO_THIRDS, ": thirds are larger parts"),
        ),
        (
            DrawQuestionData((_f(5, 8), _f(3, 8)), (FractionLine(1),) * 2, LESS_ONE, ">"),
            (_f(3, 8), ": fewer eighths"),
        ),
        # the greatest or least: the parts' sizes, or how many of the same parts
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), True),
            (_f(2, 3), ": thirds are the largest parts"),
        ),
        (
            _greatest((_f(2, 3), _f(2, 6), _f(2, 8)), False),
            (_f(2, 8), ": eighths are the smallest parts"),
        ),
        (_greatest((_f(1, 8), _f(7, 8), _f(3, 8)), True), (_f(7, 8), ": the most eighths")),
        (_greatest((_f(1, 8), _f(7, 8), _f(3, 8)), False), (_f(1, 8), ": the fewest eighths")),
        (_greatest((_f(3, 6), _f(3, 8)), True), (_f(3, 6), ": sixths are larger parts")),
        (_greatest((_f(3, 6), _f(3, 8)), False), (_f(3, 8), ": eighths are smaller parts")),
        (_greatest((_f(5, 8), _f(3, 8)), True), (_f(5, 8), ": more eighths")),
        (_greatest((_f(5, 8), _f(3, 8)), False), (_f(3, 8), ": fewer eighths")),
    ],
)
def test_solution(data: ComparingFractionsQuestionData, expected: Pieces) -> None:
    assert solution(data) == expected


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (PartSize(6, 8, larger=True), "sixths are larger than eighths"),
        (PartSize(6, 8, larger=False), "sixths are smaller than eighths"),
        (
            PartsOf(_f(5, 8), _f(3, 8), True),
            "5 out of 8 equal parts is more than 3 out of 8 equal parts",
        ),
        (
            PartsOf(_f(3, 8), _f(5, 8), False),
            "3 out of 8 equal parts is less than 5 out of 8 equal parts",
        ),
        (BiggerNumber(8, 6, greater=True), "8 is greater than 6"),
        (BiggerNumber(3, 4, greater=False), "3 is less than 4"),
        (SameCount(2, total=False, pictured=True), "each model has 2 parts shaded"),
        (SameCount(2, total=False, pictured=False), "both fractions have a numerator of 2"),
        (SameCount(8, total=True, pictured=True), "each model has 8 equal parts"),
        (SameCount(8, total=True, pictured=False), "both fractions have 8 equal parts"),
    ],
)
def test_reason_text(reason: Reason, expected: str) -> None:
    assert reason_text(reason) == expected


@pytest.mark.parametrize(
    ("comparison", "in_words", "expected"),
    [
        (Comparison(THIRD, ">", FOURTH), False, (THIRD, " > ", FOURTH)),
        (Comparison(THIRD, ">", FOURTH), True, (THIRD, " is greater than ", FOURTH)),
        (Comparison(FOURTH, "<", THIRD), True, (FOURTH, " is less than ", THIRD)),
        (Comparison(THIRD, "=", FOURTH), True, (THIRD, " is equal to ", FOURTH)),
    ],
)
def test_comparison_pieces(comparison: Comparison, in_words: bool, expected: Pieces) -> None:
    assert comparison_pieces(comparison, in_words) == expected


def test_explanation_pieces() -> None:
    assert explanation_pieces(SIX_EIGHTHS_EXPLAINED, in_words=True) == (
        _f(6, 8),
        " is less than ",
        _f(8, 8),
        ", because 6 out of 8 equal parts is less than 8 out of 8 equal parts",
    )


@pytest.mark.parametrize(
    ("data", "choice", "expected"),
    [
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.AHEAD, "Ana", StoryReason.NONE),
            ("Ana eats more pizza.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.AHEAD, "Ana", StoryReason.FRACTION, Comparison(THIRD, ">", FOURTH)),
            ("Ana eats more pizza, because ", THIRD, " is greater than ", FOURTH, "."),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(
                Verdict.AHEAD, "Ana", StoryReason.PART_SIZE, Comparison(THIRD, ">", FOURTH)
            ),
            ("Ana eats more pizza, because thirds are larger than fourths.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(
                Verdict.AHEAD, "Ben", StoryReason.DENOMINATOR, Comparison(FOURTH, ">", THIRD)
            ),
            ("Ben eats more pizza, because a denominator of 4 is larger than a denominator of 3.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
            ("They eat the same amount, because the pizzas are the same size.",),
        ),
        (
            _word(WHOLE, BOOK),
            StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
            ("They read the same amount, because it is the same book.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.SAME, None, StoryReason.SAME_NUMERATOR),
            ("They eat the same amount, because both fractions have a numerator of 1.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.SAME, None, StoryReason.EQUAL, Comparison(THIRD, "=", FOURTH)),
            ("They eat the same amount, because ", THIRD, " is equal to ", FOURTH, "."),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
            ("There is not enough information to tell.",),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(
                Verdict.AHEAD, "Kayla", StoryReason.FRACTION, Comparison(THIRD, ">", FOURTH), True
            ),
            ("Kayla, because ", THIRD, " > ", FOURTH),
        ),
        (
            _word(LENGTH, WORM, unit=LengthUnit.INCH),
            StoryChoice(Verdict.AHEAD, "Ana", StoryReason.NONE),
            ("Ana's worm is longer.",),
        ),
        (
            _word(LENGTH, WALK, unit=LengthUnit.MILE),
            StoryChoice(Verdict.SAME, None, StoryReason.NONE),
            ("They walk the same distance.",),
        ),
        (
            _word(LENGTH, WORM, unit=LengthUnit.INCH),
            StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
            ("The worms are the same length, because both are measured in inches.",),
        ),
        (
            _word(GROUP, BLOCKS, (_f(3, 8), _f(5, 8))),
            StoryChoice(Verdict.AHEAD, "Ben", StoryReason.NONE),
            ("A greater fraction of Ben's blocks are painted.",),
        ),
        (
            _word(GROUP, BLOCKS, (_f(3, 8), _f(5, 8))),
            StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
            ("The same fraction of each person's blocks are painted, because each has 8 blocks.",),
        ),
    ],
)
def test_story_choice_pieces(data: WordQuestionData, choice: StoryChoice, expected: Pieces) -> None:
    assert story_choice_pieces(data, choice) == expected


def test_story_choice_pieces_error() -> None:
    choice = StoryChoice(Verdict.AHEAD, "Ana", StoryReason.FRACTION)
    with pytest.raises(ValueError) as error:
        story_choice_pieces(_word(WHOLE, PIZZA), choice)
    assert str(error.value) == "A fraction reason needs a comparison."


@pytest.mark.parametrize(
    ("data", "option", "expected"),
    [
        (
            CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, True, ">"),
            Comparison(TWO_THIRDS, ">", TWO_FOURTHS),
            (TWO_THIRDS, " is greater than ", TWO_FOURTHS),
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, CIRCLE_WORDS, FIVE_SIXTHS_EXPLAINED
            ),
            FIVE_SIXTHS_EXPLAINED,
            (_f(5, 6), " > ", _f(5, 8), ", because sixths are larger than eighths"),
        ),
        (
            _word(WHOLE, PIZZA),
            StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
            ("There is not enough information to tell.",),
        ),
        (_greatest((THIRD, FOURTH), True), THIRD, (THIRD,)),
        (
            EveryQuestionData(_f(3, 8), True, (_f(3, 4),), (_f(3, 4),)),
            ALL_OF_THESE,
            (ALL_OF_THESE,),
        ),
        (_greatest((TWO_THIRDS, TWO_FOURTHS), True, AREA), AREA[0], None),  # a picture
    ],
)
def test_choice_pieces(
    data: ComparingFractionsQuestionData, option: object, expected: Pieces | None
) -> None:
    assert choice_pieces(data, option) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (_greatest((_f(3, 6), _f(3, 8)), True), (_f(3, 6),)),
        (_word(WHOLE, PIZZA, answer=LESS, more_or_less=True), (LESS,)),
        (
            EveryQuestionData(
                _f(3, 8), True, (_f(3, 4), _f(5, 8), _f(3, 6)), (_f(3, 4), _f(5, 8), _f(3, 6))
            ),
            ("all of them",),
        ),
        (EveryQuestionData(_f(2, 6), False, (_f(5, 6), _f(4, 6), _f(6, 6)), ()), ("none of them",)),
    ],
)
def test_tile_answer(data: ComparingFractionsQuestionData, expected: Pieces) -> None:
    assert tile_answer(data) == expected


def test_tile_answer_error() -> None:
    data = CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, False, ">")
    with pytest.raises(ValueError) as error:
        tile_answer(data)
    assert str(error.value) == "A CompareQuestionData has no single answer for a tile."


def test_comparing_fractions_tile_question() -> None:
    assert comparing_fractions_tile_question(_greatest((_f(3, 6), _f(3, 8)), True)) == TileQuestion(
        prompt="Which is greater, 3/6 or 3/8?",
        answer=(_f(3, 6),),
        solution="3/6: sixths are larger parts",
    )


def test_a_length_story_needs_a_unit() -> None:
    data = _word(LENGTH, WORM)
    with pytest.raises(ValueError) as error:
        question(data, choices=False)
    assert str(error.value) == "A length story has a unit."


@pytest.mark.parametrize(
    ("data", "choices", "expected"),
    [
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, WRITE, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            2,
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, WRITE, FIVE_SIXTHS_EXPLAINED
            ),
            True,
            0,
        ),
        (
            ExplainQuestionData(
                (_f(5, 6), _f(5, 8)), (), None, False, CIRCLE_WORDS, FIVE_SIXTHS_EXPLAINED
            ),
            False,
            0,
        ),
        (CompareQuestionData((TWO_THIRDS, TWO_FOURTHS), (), None, False, ">"), False, 0),
    ],
)
def test_writing_lines(data: ComparingFractionsQuestionData, choices: bool, expected: int) -> None:
    """Only a written question to explain in words has lines to write on."""
    assert writing_lines(data, choices) == expected


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        (PartSize(6, 8, larger=True), ("Sixths are larger than eighths.",)),
        (BiggerNumber(8, 6, greater=True), ("8 is greater than 6.",)),
        (
            Pick(TWO_FOURTHS, Comparison(TWO_THIRDS, ">", TWO_FOURTHS)),
            (TWO_FOURTHS, ", because ", TWO_THIRDS, " > ", TWO_FOURTHS),
        ),
    ],
)
def test_reason_and_pick_choices(option: object, expected: Pieces) -> None:
    """A reason to choose is a sentence; a fraction picked comes with its comparison."""
    data = ExplainQuestionData((_f(5, 6), _f(5, 8)), (), None, False, WHY, FIVE_SIXTHS_EXPLAINED)
    assert choice_pieces(data, option) == expected
