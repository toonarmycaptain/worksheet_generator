"""
What a comparing fractions question shows: its question as written maths, the work it has the
student write or circle under its pictures, its choices as written maths, the answer key's
entry, and on a self-check tiles sheet, its tile question.
"""

from typing import assert_never

from core.comparing_fractions.choices import right_reason, symbol
from core.comparing_fractions.data import (
    ALL_OF_THEM,
    CANT_TELL,
    EQUAL_TO,
    GREATER_THAN,
    LESS_THAN,
    NONE_OF_THEM,
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
    QuestionType,
    Reason,
    Representation,
    SameCount,
    Shared,
    StoryChoice,
    StoryForm,
    StoryKind,
    StoryReason,
    Verdict,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.stories import GROUP_STORIES, LENGTH_STORIES, WHOLE_STORIES
from core.drawn_objects import OBJECT_NAMES
from core.fraction_models.area_models import AreaModel, Circle, Grid, RadialPartition, Strip
from core.fraction_models.denominators import part_name
from core.fraction_models.number_lines import UNIT_NAMES, FractionLine
from core.fraction_models.object_groups import ObjectGroup
from core.question import CIRCLE
from core.self_check_tiles import TileQuestion
from core.written_numbers import Piece, Pieces, UnreducedFraction, inline, merge_pieces

COMPARING_FRACTIONS_NAME = "Comparing Fractions"
QUESTION_TYPE_NAMES = {
    QuestionType.COMPARE: "Compare",
    QuestionType.EXPLAIN: "Compare and explain",
    QuestionType.WORD: "Word problems",
    QuestionType.LESS_GREATER: "Less or greater than a model",
    QuestionType.DRAW: "Draw and compare",
    QuestionType.GREATEST: "Greatest and least",
}
REPRESENTATION_NAMES = {
    Representation.STRIP: "Strips",
    Representation.GRID: "Grids",
    Representation.CIRCLE: "Circles",
    Representation.OTHER_SHAPE: "Other shapes",
    Representation.GROUP: "Groups of objects",
    Representation.LINE: "Number lines",
    Representation.WALL: "Fraction strip charts",
    Representation.NONE: "No picture",
}
SHARED_NAMES = {Shared.NUMERATOR: "Same numerator", Shared.DENOMINATOR: "Same denominator"}

ANSWER_BLANK = "________"  # where a written answer goes in a question's text
SYMBOL_GAP = "  "  # either side of the circle to write a symbol in, or of a symbol
SYMBOL_WORDS = {GREATER_THAN: "is greater than", LESS_THAN: "is less than", EQUAL_TO: "is equal to"}
USE_WALL = "Use the fraction strips. "
WIDE_GAP = "        "  # between two blanks to write in on one line
EXPLAIN_LINES = 2  # lines to write an explanation on


def question(data: ComparingFractionsQuestionData, choices: bool, tiles: bool = False) -> Pieces:
    """
    Return the question as written maths, worded for lettered choices with ``choices``, for a
    self-check tiles sheet with ``tiles``, else for a written answer. Pictures, a wall and the
    work under them (see ``work``) come after it.
    """
    match data:
        case CompareQuestionData():
            return _compare_question(data, choices)
        case EveryQuestionData():
            word = _side(data.greater)
            if tiles:
                fractions = _listed(data.fractions, ", ")
                return merge_pieces(
                    (f"Which of these are {word} than ", data.target, ": ", *fractions, "?")
                )
            if choices:
                return (f"Which fraction is {word} than ", data.target, "?")
            return (f"Circle every fraction {word} than ", data.target, ".")
        case ExplainQuestionData():
            return _explain_question(data)
        case WordQuestionData():
            return _word_question(data, choices, tiles)
        case LessGreaterQuestionData():
            return _less_greater_question(data)
        case DrawQuestionData():
            return _draw_question(data, choices)
        case GreatestQuestionData():
            return _greatest_question(data, choices, tiles)
        case _:
            assert_never(data)


def work(data: ComparingFractionsQuestionData, choices: bool, tiles: bool = False) -> Pieces:
    """
    Return what a written question has the student fill in or circle under its pictures, if
    anything: the two fractions with a circle for the symbol, blanks for the fractions the
    pictures show, the fractions to circle, or the sentence with words to circle.
    """
    if choices or tiles:
        return ()
    match data:
        case CompareQuestionData():
            if data.pictures:
                return (f"{ANSWER_BLANK}{SYMBOL_GAP}{CIRCLE}{SYMBOL_GAP}{ANSWER_BLANK}",)
            return _to_compare(*data.fractions)
        case EveryQuestionData():
            return _spaced(data.fractions)
        case ExplainQuestionData():
            if data.form is ExplainForm.WRITE:
                return _to_compare(*data.fractions)
            return _explain_sentence(data)
        case WordQuestionData():
            if data.asked is WordAsked.SENTENCE:
                return _word_sentence(data)
            return ("Write >, <, or =:  ", *_to_compare(*data.fractions))
        case DrawQuestionData():
            return _to_compare(*data.fractions) if data.asked is DrawAsked.SYMBOL else ()
        case GreatestQuestionData():
            return () if data.pictures else _spaced(data.fractions)
        case LessGreaterQuestionData():
            if data.form is not LessGreaterForm.WRITE:
                return ()
            kinds = []
            if any(each.denominator == data.fraction.denominator for each in data.answer):
                kinds.append(f"Same denominator: {ANSWER_BLANK}")
            if any(each.numerator == data.fraction.numerator for each in data.answer):
                kinds.append(f"Same numerator: {ANSWER_BLANK}")
            return (WIDE_GAP.join(kinds),)
        case _:
            assert_never(data)


def answer_line(data: ComparingFractionsQuestionData, choices: bool, tiles: bool = False) -> bool:
    """Return whether a written question's answer goes on a line after everything else: the
    fraction that's the greatest or least of pictures, or of two drawn."""
    if choices or tiles:
        return False
    if isinstance(data, DrawQuestionData):
        return data.asked is not DrawAsked.SYMBOL
    return isinstance(data, GreatestQuestionData) and bool(data.pictures)


def writing_lines(data: ComparingFractionsQuestionData, choices: bool, tiles: bool = False) -> int:
    """Return how many lines as wide as the question a written question leaves to explain on:
    ``EXPLAIN_LINES`` for writing an explanation, else none."""
    if isinstance(data, ExplainQuestionData) and data.form is ExplainForm.WRITE:
        return 0 if choices or tiles else EXPLAIN_LINES
    return 0


def solution(data: ComparingFractionsQuestionData) -> Pieces:
    """Return the answer key's entry: the answer, and why, its fractions written as the question
    writes them."""
    match data:
        case DrawQuestionData() if data.asked is not DrawAsked.SYMBOL:
            greatest = data.asked is DrawAsked.GREATER
            pick = max if greatest else min
            answer = pick(data.fractions, key=lambda each: each.value)
            return (answer, f": {_greatest_reason(data.fractions, greatest, answer)}")
        case CompareQuestionData() | DrawQuestionData():
            left, right = data.fractions
            return _with_reason(Comparison(left, data.answer, right))
        case EveryQuestionData():
            return _every_solution(data)
        case ExplainQuestionData():
            return explanation_pieces(data.answer, in_words=False)
        case WordQuestionData():
            return _word_solution(data)
        case LessGreaterQuestionData():
            return _less_greater_solution(data)
        case GreatestQuestionData():
            return (
                data.answer,
                f": {_greatest_reason(data.fractions, data.greatest, data.answer)}",
            )
        case _:
            assert_never(data)


# --- choices


def comparison_pieces(comparison: Comparison, in_words: bool) -> Pieces:
    """Return a comparison as written maths, "3/6 > 1/6", or in words, "3/6 is greater than
    1/6"."""
    joined = f" {SYMBOL_WORDS[comparison.symbol]} " if in_words else f" {comparison.symbol} "
    return (comparison.left, joined, comparison.right)


def explanation_pieces(explanation: Explanation, in_words: bool) -> Pieces:
    """Return an explanation as a choice writes it: "5/6 > 5/8, because sixths are larger than
    eighths"."""
    return merge_pieces(
        (
            *comparison_pieces(explanation.comparison, in_words),
            f", because {reason_text(explanation.reason)}",
        )
    )


def reason_text(reason: Reason) -> str:
    """Return a reason, true or not, as a choice or the answer key writes it."""
    match reason:
        case PartSize():
            size = "larger" if reason.larger else "smaller"
            return f"{part_name(reason.first)} are {size} than {part_name(reason.second)}"
        case PartsOf():
            more = "more" if reason.greater else "less"
            first, second = reason.first, reason.second
            return (
                f"{first.numerator} out of {first.denominator} equal parts is {more} than "
                f"{second.numerator} out of {second.denominator} equal parts"
            )
        case BiggerNumber():
            return (
                f"{reason.first} is {'greater' if reason.greater else 'less'} than {reason.second}"
            )
        case SameCount():
            if reason.total:
                owner = "each model has" if reason.pictured else "both fractions have"
                return f"{owner} {reason.count} equal parts"
            if reason.pictured:
                return f"each model has {reason.count} parts shaded"
            return f"both fractions have a numerator of {reason.count}"
        case _:
            assert_never(reason)


def story_choice_pieces(data: WordQuestionData, choice: StoryChoice) -> Pieces:
    """Return a word problem's statement as its choice writes it: "Ana eats more pizza, because
    1/3 is greater than 1/4.", or briefly, "Kayla, because 3/6 > 3/8"."""
    claim = choice.claim
    if choice.brief and claim is not None and choice.who is not None:
        return (f"{choice.who}, because ", *comparison_pieces(claim, in_words=False))
    match choice.verdict:
        case Verdict.AHEAD:
            head = _ahead(data, choice.who or data.names[0])
        case Verdict.SAME:
            head = _same(data)
        case Verdict.CANT_TELL:
            return ("There is not enough information to tell.",)
        case _:
            assert_never(choice.verdict)
    match choice.reason:
        case StoryReason.NONE:
            return (f"{head}.",)
        case StoryReason.FRACTION | StoryReason.EQUAL if claim is not None:
            return merge_pieces(
                (f"{head}, because ", *comparison_pieces(claim, in_words=True), ".")
            )
        case StoryReason.PART_SIZE if claim is not None:
            larger, smaller = part_name(claim.left.denominator), part_name(claim.right.denominator)
            return (f"{head}, because {larger} are larger than {smaller}.",)
        case StoryReason.DENOMINATOR if claim is not None:
            first, second = claim.left.denominator, claim.right.denominator
            return (
                f"{head}, because a denominator of {first} is larger than a denominator of "
                f"{second}.",
            )
        case StoryReason.SAME_WHOLE:
            return (f"{head}, because {_same_whole(data)}.",)
        case StoryReason.SAME_NUMERATOR:
            top = data.fractions[0].numerator
            return (f"{head}, because both fractions have a numerator of {top}.",)
        case _:
            raise ValueError(f"A {choice.reason} reason needs a comparison.")


def choice_pieces(data: ComparingFractionsQuestionData, option: object) -> Pieces | None:
    """Return a written choice as written maths, or ``None`` for a picture to choose."""
    match option:
        case Comparison():
            return comparison_pieces(option, _in_words(data))
        case Explanation():
            return explanation_pieces(option, _in_words(data))
        case StoryChoice() if isinstance(data, WordQuestionData):
            return story_choice_pieces(data, option)
        case PartSize() | PartsOf() | BiggerNumber() | SameCount():
            text = reason_text(option)
            return (f"{text[0].upper()}{text[1:]}.",)
        case Pick():
            return (option.fraction, ", because ", *comparison_pieces(option.claim, False))
        case UnreducedFraction() | str():
            return (option,)
        case _:
            return None


def _in_words(data: ComparingFractionsQuestionData) -> bool:
    """Return whether a question writes its comparisons in words."""
    return isinstance(data, CompareQuestionData | ExplainQuestionData) and data.in_words


# --- tiles


def tile_answer(data: ComparingFractionsQuestionData) -> Pieces:
    """Return the answer as a tiles bank shows it: the fraction, the name or word, or "all of
    them" or "none of them"."""
    match data:
        case GreatestQuestionData():
            return (data.answer,)
        case WordQuestionData():
            return (data.answer,)
        case EveryQuestionData():
            return (ALL_OF_THEM if data.answer else NONE_OF_THEM,)
        case _:
            raise ValueError(f"A {type(data).__name__} has no single answer for a tile.")


def comparing_fractions_tile_question(data: ComparingFractionsQuestionData) -> TileQuestion[Pieces]:
    """
    Convert a question's data to a ``TileQuestion``: the prompt is the question, written inline,
    the answer as the bank shows it, and the solution the answer key's entry, inline.
    """
    return TileQuestion(
        prompt=inline(question(data, choices=False, tiles=True)),
        answer=tile_answer(data),
        solution=inline(solution(data)),
    )


# --- wording


def _side(greater: bool) -> str:
    """Return which side of a fraction is asked for: "greater" or "less"."""
    return "greater" if greater else "less"


def _noun(pictures: tuple[Picture, ...], plural: bool) -> str:
    """Return what a question's pictures are called: models, groups or number lines."""
    first = pictures[0]
    if isinstance(first, FractionLine):
        return "number lines" if plural else "number line"
    if isinstance(first, ObjectGroup):
        return "groups" if plural else "group"
    return "models" if plural else "model"


def _shown(pictures: tuple[Picture, ...], wall: bool) -> str:
    """Return what a multiple-choice question says before asking, about its pictures or wall:
    "The models show two fractions. ", "Use the fraction strips. ", or nothing."""
    if wall:
        return USE_WALL
    if pictures:
        return f"The {_noun(pictures, plural=True)} show two fractions. "
    return ""


def _to_compare(left: UnreducedFraction, right: UnreducedFraction) -> Pieces:
    """Return two fractions with a circle between them to write the symbol in."""
    return (left, f"{SYMBOL_GAP}{CIRCLE}{SYMBOL_GAP}", right)


def _spaced(fractions: tuple[UnreducedFraction, ...]) -> Pieces:
    """Return fractions to circle, spaced out in a row."""
    pieces: list[UnreducedFraction | str] = []
    for index, fraction in enumerate(fractions):
        if index:
            pieces.append("        ")
        pieces.append(fraction)
    return tuple(pieces)


def _listed(fractions: tuple[UnreducedFraction, ...], last: str) -> Pieces:
    """Return fractions as a list, "3/4, 5/8, 3/6", with ``last`` before the last of them:
    ", " or ", or "."""
    pieces: list[UnreducedFraction | str] = []
    for index, fraction in enumerate(fractions):
        if index:
            pieces.append(last if index == len(fractions) - 1 else ", ")
        pieces.append(fraction)
    return tuple(pieces)


def _compare_question(data: CompareQuestionData, choices: bool) -> Pieces:
    """Return a compare question: write the symbol, or which comparison is true."""
    if choices:
        return (f"{_shown(data.pictures, data.wall is not None)}Which comparison is true?",)
    if data.wall is not None:
        return (f"{USE_WALL}Write >, <, or =.",)
    if data.pictures:
        noun = _noun(data.pictures, plural=False)
        return (f"Write the fraction each {noun} shows. Then write >, <, or =.",)
    return ("Write >, <, or =.",)


def _explain_sentence(data: ExplainQuestionData) -> Pieces:
    """Return an explain question's sentence, with the symbol and words to circle."""
    left, right = data.fractions
    symbols = f"{SYMBOL_GAP}( >   <   = ){SYMBOL_GAP}"
    if left.numerator == right.numerator:
        first, second = part_name(left.denominator), part_name(right.denominator)
        return (left, symbols, right, f" because ( {first} / {second} ) are larger parts.")
    parts = left.denominator
    return (
        left,
        symbols,
        right,
        f" because {left.numerator} out of {parts} equal parts is ( more than / less than ) "
        f"{right.numerator} out of {parts} equal parts.",
    )


def _draw_question(data: DrawQuestionData, choices: bool) -> Pieces:
    """Return a draw and compare question: divide and shade, or mark two lines, then compare."""
    left, right = data.fractions
    if data.asked is DrawAsked.SYMBOL:
        then = "Which comparison is true?" if choices else "Then write >, <, or =."
    else:
        then = f"Which fraction is {'greater' if data.asked is DrawAsked.GREATER else 'less'}?"
    if isinstance(data.blanks[0], FractionLine):
        return (
            "Mark ",
            left,
            " on the first number line and ",
            right,
            f" on the second. {then}",
        )
    noun = _blank_noun(data.blanks[0])
    return (f"Divide and shade the {noun}s to show ", left, " and ", right, f". {then}")


def _blank_noun(picture: Picture) -> str:
    """Return what a whole left uncut is called: strip, rectangle, circle or shape."""
    if isinstance(picture, AreaModel):
        split = picture.split
        if isinstance(split, Strip):
            return "strip"
        if isinstance(split, Grid):
            return "rectangle"
        if isinstance(split, RadialPartition) and isinstance(split.outline, Circle):
            return "circle"
    return "shape"


def _greatest_question(data: GreatestQuestionData, choices: bool, tiles: bool) -> Pieces:
    """Return a greatest or least question: of two, "Which is greater, 3/6 or 3/8?"."""
    two = len(data.fractions) == 2
    if two:
        word = "greater" if data.greatest else "less"
    else:
        word = "the greatest" if data.greatest else "the least"
    prefix = USE_WALL if data.wall is not None else ""
    if data.pictures:
        noun = _noun(data.pictures, plural=False)
        if choices:
            return (f"Which {noun} shows {word} fraction?",)
        return (f"Each {noun} shows a fraction. Which fraction is {word}?",)
    if choices:
        return (f"{prefix}Which fraction is {word}?",)
    if tiles:
        if two:
            first, second = data.fractions
            return (f"{prefix}Which is {word}, ", first, " or ", second, "?")
        return merge_pieces((f"{prefix}Which is {word}: ", *_listed(data.fractions, ", or "), "?"))
    return (f"{prefix}Circle {word} fraction.",)


def _greatest_reason(
    fractions: tuple[UnreducedFraction, ...], greatest: bool, answer: UnreducedFraction
) -> str:
    """Return why ``answer`` is the greatest (or least) of ``fractions``: its parts are the
    largest or smallest, or it has the most or fewest of the same parts."""
    two = len(fractions) == 2
    if len({each.numerator for each in fractions}) == 1:
        if two:
            size = "larger" if greatest else "smaller"
        else:
            size = "the largest" if greatest else "the smallest"
        return f"{part_name(answer.denominator)} are {size} parts"
    if two:
        return f"{'more' if greatest else 'fewer'} {part_name(answer.denominator)}"
    return f"{'the most' if greatest else 'the fewest'} {part_name(answer.denominator)}"


def _with_reason(comparison: Comparison) -> Pieces:
    """Return a true comparison with its reason: "3/6 > 3/8: sixths are larger than eighths"."""
    pieces = comparison_pieces(comparison, in_words=False)
    if comparison.symbol == EQUAL_TO:
        return merge_pieces((*pieces, ": the same fraction"))
    return merge_pieces((*pieces, f": {reason_text(right_reason(comparison))}"))


def _every_solution(data: EveryQuestionData) -> Pieces:
    """Return which fractions are greater (or less) than the target."""
    word = _side(data.greater)
    if not data.answer:
        return (f"None of them is {word} than ", data.target)
    if len(data.answer) == len(data.fractions):
        listed = _listed(data.answer, ", and ")
        return merge_pieces((*listed, f" are all {word} than ", data.target))
    verb = "is" if len(data.answer) == 1 else "are"
    listed = _listed(data.answer, " and " if len(data.answer) == 2 else ", and ")
    return merge_pieces((*listed, f" {verb} {word} than ", data.target))


def _explain_question(data: ExplainQuestionData) -> Pieces:
    """Return a compare and explain question, as its form asks."""
    shown = _shown(data.pictures, data.wall is not None)
    match data.form:
        case ExplainForm.PAIR:
            return (f"{shown}Which comparison and explanation are true?",)
        case ExplainForm.WHY:
            comparison = data.answer.comparison
            return merge_pieces(
                (shown, *comparison_pieces(comparison, in_words=False), ". Which explains why?")
            )
        case ExplainForm.WRITE:
            prefix = USE_WALL if data.wall is not None else ""
            return (f"{prefix}Write >, <, or =. Then explain how you know.",)
        case ExplainForm.CIRCLE:
            prefix = USE_WALL if data.wall is not None else ""
            return (f"{prefix}Circle the symbol and the words that make the sentence true.",)
        case _:
            assert_never(data.form)


def _less_greater_question(data: LessGreaterQuestionData) -> Pieces:
    """Return a less or greater than a model question, as its form asks."""
    word, fraction = _side(data.greater), data.fraction
    model = ("The model shows ", fraction, ". ")
    match data.form:
        case LessGreaterForm.NOT_A_WAY:
            asked: Pieces = (f"Which is NOT a way to show a fraction {word} than ", fraction, "?")
        case LessGreaterForm.SHOWS:
            asked = (f"Which model shows a fraction {word} than ", fraction, "?")
        case LessGreaterForm.CIRCLE:
            asked = (f"Circle every model that shows a fraction {word} than ", fraction, ".")
        case LessGreaterForm.WRITE:
            asked = (f"Write a fraction {word} than ", fraction, ".")
        case LessGreaterForm.DIVIDE:
            noun = _blank_noun(data.blank)
            return (
                f"Divide and shade each blank {noun} to show a different fraction {word} than ",
                fraction,
                ".",
            )
        case _:
            assert_never(data.form)
    return merge_pieces((*model, *asked))


def _less_greater_solution(data: LessGreaterQuestionData) -> Pieces:
    """Return a less or greater than a model question's answer: some ways, the ways among the
    models, every way of each kind, or the one model that is or isn't a way."""
    word, fraction = _side(data.greater), data.fraction
    match data.form:
        case LessGreaterForm.NOT_A_WAY:
            return (data.answer[0], f" is not {word} than ", fraction)
        case LessGreaterForm.SHOWS:
            return (data.answer[0], f" is {word} than ", fraction)
        case LessGreaterForm.CIRCLE:
            verb = "is" if len(data.answer) == 1 else "are"
            listed = _listed(data.answer, " and " if len(data.answer) == 2 else ", and ")
            return merge_pieces((*listed, f" {verb} {word} than ", fraction))
        case LessGreaterForm.WRITE:
            same_parts = tuple(
                each for each in data.answer if each.denominator == fraction.denominator
            )
            same_top = tuple(each for each in data.answer if each.numerator == fraction.numerator)
            pieces: list[Piece] = []
            for name, found in (("denominator", same_parts), ("numerator", same_top)):
                if found:
                    start = "; same" if pieces else "Same"
                    pieces += [f"{start} {name}: ", *_listed(found, " or ")]
            return merge_pieces(pieces)
        case LessGreaterForm.DIVIDE:
            return merge_pieces(("For example: ", *_listed(data.answer, ", ")))
        case _:
            assert_never(data.form)


# --- word problems


def _amount(data: WordQuestionData) -> str:
    """Return what a whole story asks more of, after a space: " pizza", " of the book", or
    nothing."""
    amount = WHOLE_STORIES[data.story].amount
    return f" {amount}" if amount else ""


def _objects(data: WordQuestionData) -> str:
    """Return a group story's objects: "blocks"."""
    return OBJECT_NAMES[GROUP_STORIES[data.story].kind][1]


def _unit(data: WordQuestionData, plural: bool = False) -> str:
    """Return a length story's unit, singular as a fraction of it takes it: "3/4 mile"."""
    if data.unit is None:
        raise ValueError("A length story has a unit.")
    return UNIT_NAMES[data.unit][1 if plural else 0]


def _story(data: WordQuestionData) -> Pieces:
    """Return a word problem's story, up to its question."""
    first, second = data.names
    left, right = data.fractions
    match data.kind:
        case StoryKind.WHOLE:
            story = WHOLE_STORIES[data.story]
            setup = story.setup.format(first=first, second=second)
            if data.sizes is not None:
                small, large = data.sizes
                sizes = f" One {story.whole} is small and the other is large."
                return (
                    f"{setup}{sizes} {first} {story.verb} ",
                    left,
                    f" of the {small} {story.whole}. {second} {story.verb} ",
                    right,
                    f" of the {large} {story.whole}.",
                )
            same = f" {story.same_size}" if story.same_size else ""
            whole = f"{story.article} {story.whole}"
            return (
                f"{setup}{same} {first} {story.verb} ",
                left,
                f" of {whole}. {second} {story.verb} ",
                right,
                f" of {whole}.",
            )
        case StoryKind.LENGTH:
            length = LENGTH_STORIES[data.story]
            setup = length.setup.format(first=first, second=second)
            unit = _unit(data)
            return (
                f"{setup} {_whose(data, first)} {length.verb} ",
                left,
                f" {unit}{length.tail}. {_whose(data, second)} {length.verb} ",
                right,
                f" {unit}{length.tail}.",
            )
        case StoryKind.GROUP:
            group = GROUP_STORIES[data.story]
            setup = group.setup.format(first=first, second=second)
            objects = _objects(data)
            return (
                f"{setup} {first} has {left.denominator} {objects} and {group.verb} "
                f"{left.numerator} of them. {second} has {right.denominator} {objects} and "
                f"{group.verb} {right.numerator} of them.",
            )
        case _:
            assert_never(data.kind)


def _whose(data: WordQuestionData, name: str) -> str:
    """Return who has a length: "Ana", or "Ana's worm"."""
    thing = LENGTH_STORIES[data.story].thing
    return f"{name}'s {thing}" if thing else name


def _asked(data: WordQuestionData) -> str:
    """Return a word problem's question: who has more, or whether the first has more or less."""
    first, second = data.names
    match data.kind:
        case StoryKind.WHOLE:
            story = WHOLE_STORIES[data.story]
            if data.more_or_less:
                return f"Does {first} {story.base} more or less{_amount(data)} than {second}?"
            return f"Who {story.verb} {'more' if data.greater else 'less'}{_amount(data)}?"
        case StoryKind.LENGTH:
            length = LENGTH_STORIES[data.story]
            if data.more_or_less:
                other = f"{second}'s" if length.thing else second
                return f"Does {_whose(data, first)} {length.plural_verb} more or less than {other}?"
            who = f"Whose {length.thing}" if length.thing else "Who"
            return f"{who} {length.verb} {length.longer if data.greater else length.shorter}?"
        case StoryKind.GROUP:
            group = GROUP_STORIES[data.story]
            size = "greater" if data.greater else "smaller"
            return f"Who {group.verb} a {size} fraction of their {_objects(data)}?"
        case _:
            assert_never(data.kind)


def _word_question(data: WordQuestionData, choices: bool, tiles: bool) -> Pieces:
    """Return a word problem: its story, then what it asks."""
    story = _story(data)
    if tiles:
        return merge_pieces((*story, f" {_asked(data)}"))
    if choices:
        if data.form is StoryForm.WHO_SYMBOL:
            return merge_pieces((*story, f" {_asked(data)}"))
        return merge_pieces((*story, " Which statement is true?"))
    if data.asked is WordAsked.SENTENCE:
        return merge_pieces((*story, " Circle the words that make the sentence true."))
    return merge_pieces((*story, f" {_asked(data)} {ANSWER_BLANK}"))


def _ahead(data: WordQuestionData, who: str) -> str:
    """Return that ``who`` comes out ahead: "Ana eats more pizza", "Ana's worm is longer"."""
    match data.kind:
        case StoryKind.WHOLE:
            return f"{who} {WHOLE_STORIES[data.story].verb} more{_amount(data)}"
        case StoryKind.LENGTH:
            length = LENGTH_STORIES[data.story]
            return f"{_whose(data, who)} {length.verb} {length.longer}"
        case StoryKind.GROUP:
            return (
                f"A greater fraction of {who}'s {_objects(data)} are "
                f"{GROUP_STORIES[data.story].done}"
            )
        case _:
            assert_never(data.kind)


def _same(data: WordQuestionData) -> str:
    """Return that both have the same: "They eat the same amount", "The worms are the same
    length"."""
    match data.kind:
        case StoryKind.WHOLE:
            return f"They {WHOLE_STORIES[data.story].base} the same amount"
        case StoryKind.LENGTH:
            length = LENGTH_STORIES[data.story]
            who = f"The {length.things}" if length.things else "They"
            return f"{who} {length.plural_verb} {length.same}"
        case StoryKind.GROUP:
            return (
                f"The same fraction of each person's {_objects(data)} are "
                f"{GROUP_STORIES[data.story].done}"
            )
        case _:
            assert_never(data.kind)


def _same_whole(data: WordQuestionData) -> str:
    """Return the mistaken reason that both have the same because their wholes are alike: "the
    pizzas are the same size", "both are measured in feet", "each has 8 blocks"."""
    match data.kind:
        case StoryKind.WHOLE:
            story = WHOLE_STORIES[data.story]
            if story.same_size:
                return f"the {story.wholes} are the same size"
            return f"it is the same {story.whole}"
        case StoryKind.LENGTH:
            return f"both are measured in {_unit(data, plural=True)}"
        case StoryKind.GROUP:
            return f"each has {data.fractions[0].denominator} {_objects(data)}"
        case _:
            assert_never(data.kind)


def _relations(data: WordQuestionData) -> tuple[str, str, str]:
    """Return the three ways a sentence can compare the first person with the second: more, less
    and the same, or for lengths, longer, shorter and the same."""
    if data.kind is StoryKind.LENGTH:
        length = LENGTH_STORIES[data.story]
        return f"{length.longer} than", f"{length.shorter} than", f"{length.same} as"
    return "more than", "less than", "the same amount as"


def _sentence_reasons(data: WordQuestionData) -> tuple[str, str, str]:
    """Return the three reasons a sentence offers: the first's parts or count larger, the
    second's, or both the same: "sixths are larger than eighths", "both have 5 parts"."""
    left, right = data.fractions
    if left.numerator == right.numerator:
        first, second = part_name(left.denominator), part_name(right.denominator)
        return (
            f"{first} are larger than {second}",
            f"{second} are larger than {first}",
            f"both have {left.numerator} part{'' if left.numerator == 1 else 's'}",
        )
    parts = left.denominator
    first, second = _count_of(left.numerator, parts), _count_of(right.numerator, parts)
    return (
        f"{first} is more than {second}",
        f"{second} is more than {first}",
        f"both are {part_name(parts)}",
    )


def _count_of(count: int, parts: int) -> str:
    """Return a count of equal parts: "5 eighths", "1 eighth", "1 half"."""
    name = part_name(parts)
    if count == 1:
        name = "half" if parts == 2 else name[:-1]
    return f"{count} {name}"


def _word_sentence(data: WordQuestionData) -> Pieces:
    """Return a word problem's sentence with words to circle."""
    first, second = data.names
    more, less, same = _relations(data)
    reasons = " / ".join(_sentence_reasons(data))
    if data.kind is StoryKind.LENGTH:
        length = LENGTH_STORIES[data.story]
        other = f"{second}'s" if length.thing else second
        subject = f"{_whose(data, first)} {length.verb}"
    else:
        other = second
        subject = f"{first} {WHOLE_STORIES[data.story].verb}"
    return (f"{subject} ( {more} / {less} / {same} ) {other} because ( {reasons} ).",)


def _word_solution(data: WordQuestionData) -> Pieces:
    """Return a word problem's answer: who, or more or less, with the true comparison, or why
    it's the same or can't be told; for a sentence, the words to circle."""
    left, right = data.fractions
    in_order = comparison_pieces(Comparison(left, symbol(left, right), right), in_words=False)
    if data.answer == CANT_TELL:
        story = WHOLE_STORIES[data.story]
        return merge_pieces((f"Can't tell: the {story.wholes} are different sizes; ", *in_order))
    if data.answer == SAME:
        return merge_pieces(("The same: ", *in_order))
    if data.asked is WordAsked.SENTENCE and not data.more_or_less:
        more, less, _ = _relations(data)
        reasons = _sentence_reasons(data)
        ahead = left.value > right.value
        return (f"{more if ahead else less}, because {reasons[0 if ahead else 1]}",)
    if data.more_or_less:
        return merge_pieces((f"{data.answer}: ", *in_order))
    own, other = (left, right) if data.answer == data.names[0] else (right, left)
    true = Comparison(own, symbol(own, other), other)
    return merge_pieces((f"{data.answer}: ", *comparison_pieces(true, in_words=False)))
