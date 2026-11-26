"""Tests for the comparing fractions stories' banks: every story reads as sentences, in every
form, and the banks are as large as asked."""

import re

from core.comparing_fractions.data import (
    SAME,
    Comparison,
    StoryChoice,
    StoryForm,
    StoryKind,
    StoryReason,
    Verdict,
    WordAsked,
    WordQuestionData,
)
from core.comparing_fractions.pictures import GROUP_KINDS
from core.comparing_fractions.questions import asks_more_or_less
from core.comparing_fractions.representation import question, solution, story_choice_pieces, work
from core.comparing_fractions.stories import GROUP_STORIES, LENGTH_STORIES, WHOLE_STORIES
from core.written_numbers import UnreducedFraction, inline

THIRD, FOURTH = UnreducedFraction(1, 3), UnreducedFraction(1, 4)
THREE_EIGHTHS, FIVE_EIGHTHS = UnreducedFraction(3, 8), UnreducedFraction(5, 8)
# A sentence starts with a capital and ends with a full stop or a question mark, its words one
# space apart; a sentence to circle words in ends with its last bracket
SENTENCES = re.compile(r"(?:[A-Z][^.?]*[a-z0-9')][.?] ?)+")
BLANK_LINE = " ________"  # the answer line a written question ends with
STATEMENTS = (
    StoryChoice(Verdict.AHEAD, "Ana", StoryReason.NONE),
    StoryChoice(Verdict.AHEAD, "Ana", StoryReason.FRACTION, Comparison(THIRD, ">", FOURTH)),
    StoryChoice(Verdict.AHEAD, "Ana", StoryReason.PART_SIZE, Comparison(THIRD, ">", FOURTH)),
    StoryChoice(Verdict.AHEAD, "Ben", StoryReason.DENOMINATOR, Comparison(FOURTH, ">", THIRD)),
    StoryChoice(Verdict.SAME, None, StoryReason.NONE),
    StoryChoice(Verdict.SAME, None, StoryReason.SAME_WHOLE),
    StoryChoice(Verdict.SAME, None, StoryReason.SAME_NUMERATOR),
    StoryChoice(Verdict.SAME, None, StoryReason.EQUAL, Comparison(THIRD, "=", FOURTH)),
    StoryChoice(Verdict.CANT_TELL, None, StoryReason.NONE),
)


def _story(
    kind: StoryKind,
    index: int,
    pair: tuple[UnreducedFraction, UnreducedFraction],
    *,
    sizes: tuple[str, str] | None = None,
    greater: bool = True,
    more_or_less: bool = False,
    asked: WordAsked = WordAsked.WHO,
    form: StoryForm | None = None,
) -> WordQuestionData:
    """Return a word problem of Ana and Ben from story ``index`` of ``kind``'s bank."""
    unit = LENGTH_STORIES[index].units[0] if kind is StoryKind.LENGTH else None
    return WordQuestionData(
        kind,
        index,
        ("Ana", "Ben"),
        pair,
        unit,
        sizes,
        greater,
        more_or_less,
        asked,
        form,
        (),
        SAME,
    )


def _texts(kind: StoryKind, index: int) -> list[str]:
    """Return every text a story makes: each question, its sentence to circle, its key and its
    statements."""
    data = [
        _story(kind, index, (THIRD, FOURTH)),
        _story(kind, index, (THIRD, FOURTH), greater=False),
        *(_story(kind, index, (THIRD, FOURTH), form=form) for form in StoryForm),
    ]
    if kind is not StoryKind.GROUP:
        data += [
            _story(kind, index, pair, asked=WordAsked.SENTENCE)
            for pair in ((THIRD, FOURTH), (THREE_EIGHTHS, FIVE_EIGHTHS))
        ]
    if asks_more_or_less(kind, index):
        data.append(_story(kind, index, (THIRD, FOURTH), more_or_less=True))
    if kind is StoryKind.WHOLE and WHOLE_STORIES[index].sizes:
        data.append(_story(kind, index, (FIVE_EIGHTHS, THREE_EIGHTHS), sizes=("small", "large")))
    texts = []
    for each in data:
        texts.append(inline(question(each, choices=each.form is not None)).removesuffix(BLANK_LINE))
        texts.append(inline(question(each, choices=False, tiles=True)))
        if each.asked is WordAsked.SENTENCE:
            texts += [inline(work(each, choices=False)), f"{inline(solution(each))}."]
    texts += [inline(story_choice_pieces(data[0], statement)) for statement in STATEMENTS]
    return texts


def test_every_story_reads_as_sentences() -> None:
    """
    Each story, asking who has more or less, more or less than the other, as multiple choice,
    with wholes of different sizes, its sentence to circle, its key and every kind of statement,
    makes sentences with single spaces: an empty amount, thing or "same size" leaves no gap.
    """
    wrong = [
        text
        for kind, bank in (
            (StoryKind.WHOLE, WHOLE_STORIES),
            (StoryKind.LENGTH, LENGTH_STORIES),
            (StoryKind.GROUP, GROUP_STORIES),
        )
        for index in range(len(bank))
        for text in _texts(kind, index)
        if "  " in text or not SENTENCES.fullmatch(text[0].upper() + text[1:])
    ]
    assert wrong == []


def test_the_banks() -> None:
    """
    At least 26 stories, 10 of wholes, 8 of lengths and 8 of groups. A whole drawn as an object
    has a representation to draw it in, every length story has a unit, and a group's objects are
    among those a group shows.
    """
    broken = [
        f"{story.whole} has a look but no representation"
        for story in WHOLE_STORIES
        if story.look is not None and story.representation is None
    ]
    broken += [f"{story.setup} has no unit" for story in LENGTH_STORIES if not story.units]
    broken += [
        f"{story.kind} isn't drawn in groups"
        for story in GROUP_STORIES
        if story.kind not in GROUP_KINDS
    ]
    sizes = (len(WHOLE_STORIES), len(LENGTH_STORIES), len(GROUP_STORIES))
    assert (broken, all(size >= least for size, least in zip(sizes, (10, 8, 8), strict=True))) == (
        [],
        True,
    )
