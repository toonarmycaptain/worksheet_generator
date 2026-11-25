"""Tests for the distance stories' bank: every story reads as sentences, in every form."""

import re

from core.fraction_models.number_lines import FractionLine
from core.fraction_number_lines.data import (
    LESS,
    Compared,
    CompareQuestionData,
    DistanceAsked,
    DistanceQuestionData,
)
from core.fraction_number_lines.representation import question
from core.fraction_number_lines.stories import DISTANCE_STORIES
from core.written_numbers import UnreducedFraction, inline

THREE_EIGHTHS, FIVE_EIGHTHS = UnreducedFraction(3, 8), UnreducedFraction(5, 8)
# A sentence starts with a capital and ends with a full stop or a question mark, its words one
# space apart
SENTENCES = re.compile(r"(?:[A-Z][^.?]*[a-z0-9'][.?] ?)+")


def test_every_story_reads_as_sentences() -> None:
    """
    Each story, asking how far, to mark the point, which line, and each comparison, makes
    sentences with single spaces: an empty scene or origin leaves no gap, and the story's units,
    mover and start fit it.
    """
    wrong = []
    for index, story in enumerate(DISTANCE_STORIES):
        texts = [
            inline(
                question(
                    DistanceQuestionData(
                        index,
                        "Ana",
                        story.units[0],
                        asked,
                        THREE_EIGHTHS,
                        FractionLine(8),
                        THREE_EIGHTHS,
                    ),
                    choices,
                )
            )
            for asked in DistanceAsked
            for choices in (False, True)
        ]
        texts += [
            inline(
                question(
                    CompareQuestionData(
                        index,
                        ("Ana", "Ben"),
                        story.units[0],
                        (THREE_EIGHTHS, FIVE_EIGHTHS),
                        compared,
                        FractionLine(8),
                        LESS,
                    ),
                    False,
                )
            )
            for compared in Compared
        ]
        wrong += [text for text in texts if "  " in text or not SENTENCES.fullmatch(text)]
        if not story.units or (story.mover is not None and story.thing is None):
            wrong.append(f"story {index}: no units, or a mover that isn't the person's thing")
    assert wrong == []
